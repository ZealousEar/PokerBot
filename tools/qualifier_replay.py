"""Analyze qualifier hand-history JSON and optionally replay decision snapshots.

Histories are deliberately not committed to this repository. Supply one or
more ``--history`` files/directories, or place JSON/JSONL under
``histories/qualifier``. Analysis is engine-free. If histories contain captured
``game_state``/``state_before`` objects, ``--candidate`` replays them through
the official sandbox ``BotProcess`` and reports action agreement.

The official ``run_match`` history contains rich action events but not action-
request snapshots, so it is fully analyzable but cannot by itself reproduce a
bot's counterfactual decisions. Candidate replay therefore requires an
instrumented export containing those snapshots and fails clearly without one.

Supported containers include a raw list of hands, engine ``run_match`` output
(``hands`` plus ``chip_delta``), and nested ``matches``/``games``/``rounds``.
The original input is never modified.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import traceback
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.evaluation import (  # noqa: E402
    DEFAULT_ENGINE_DIR,
    BotArtifact,
    EvaluationError,
    MatchFailure,
    PrerequisiteError,
    append_jsonl,
    artifact_digest,
    default_output_dir,
    dump_json,
    git_provenance,
    load_engine,
    sha256_file,
    utc_now,
    validate_artifact,
)


SCHEMA_VERSION = "fullhouse-qualifier-replay-v1"
CONTAINER_KEYS = ("matches", "games", "rounds", "results", "data", "events")
ACTION_KEYS = ("action_log", "actions", "history")
STATE_KEYS = ("game_state", "state_before", "state")


def discover_history_files(paths: Sequence[Path], default_dir: Path) -> list[Path]:
    requested = list(paths) if paths else [default_dir]
    missing = [str(path) for path in requested if not path.expanduser().exists()]
    if missing:
        raise PrerequisiteError("history input does not exist: " + ", ".join(missing))
    discovered: set[Path] = set()
    for requested_path in requested:
        path = requested_path.expanduser().resolve()
        if path.is_file():
            if path.suffix.lower() not in {".json", ".jsonl"}:
                raise PrerequisiteError(f"history input must be JSON or JSONL: {path}")
            discovered.add(path)
        elif path.is_dir():
            discovered.update(item.resolve() for item in path.rglob("*.json") if item.is_file())
            discovered.update(item.resolve() for item in path.rglob("*.jsonl") if item.is_file())
    files = sorted(discovered)
    if not files:
        raise PrerequisiteError("no .json or .jsonl qualifier histories were found")
    return files


def load_history_file(path: Path) -> list[Any]:
    try:
        if path.suffix.lower() == ".jsonl":
            documents = []
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    documents.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise EvaluationError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            return documents
        return [json.loads(path.read_text(encoding="utf-8"))]
    except UnicodeDecodeError as exc:
        raise EvaluationError(f"{path}: history is not UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"{path}: invalid JSON: {exc}") from exc


def _looks_like_hand(value: Mapping[str, Any]) -> bool:
    return any(isinstance(value.get(key), list) for key in ACTION_KEYS) and any(
        key in value for key in ("hand_id", "hand_num", "community_cards", "board", "players")
    )


def extract_matches_and_hands(document: Any) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    matches: list[Mapping[str, Any]] = []
    hands: list[Mapping[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if not isinstance(value, Mapping):
            return
        contained_hands = value.get("hands")
        if isinstance(contained_hands, list):
            matches.append(value)
            for hand in contained_hands:
                if isinstance(hand, Mapping):
                    hands.append(hand)
            for key in CONTAINER_KEYS:
                nested = value.get(key)
                if nested is not None:
                    visit(nested)
            return
        if _looks_like_hand(value):
            hands.append(value)
            return
        traversed = False
        for key in CONTAINER_KEYS:
            nested = value.get(key)
            if nested is not None:
                traversed = True
                visit(nested)
        if not traversed:
            # A top-level mapping keyed by match id is also common.
            for nested in value.values():
                if isinstance(nested, (Mapping, list)):
                    visit(nested)

    visit(document)
    return matches, hands


def _seat_map(hand: Mapping[str, Any]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    players = hand.get("players")
    if not isinstance(players, list):
        return mapping
    for player in players:
        if not isinstance(player, Mapping):
            continue
        seat = player.get("seat")
        bot_id = player.get("bot_id") or player.get("id") or player.get("name")
        if isinstance(seat, int) and bot_id is not None:
            mapping[seat] = str(bot_id)
    return mapping


def _actions(hand: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    # Official engine hand results contain both a seat-only ``action_log`` and
    # richer ``events`` with bot_id/street. Prefer the latter so hero filtering
    # and per-street analysis survive busted-player seat compression.
    events = hand.get("events")
    if isinstance(events, list):
        event_actions = [
            entry
            for entry in events
            if isinstance(entry, Mapping) and str(entry.get("type", "")).lower() == "action"
        ]
        if event_actions:
            return event_actions
    for key in ACTION_KEYS:
        value = hand.get(key)
        if isinstance(value, list):
            return [entry for entry in value if isinstance(entry, Mapping)]
    return []


def _actor(entry: Mapping[str, Any], seats: Mapping[int, str]) -> str | None:
    direct = entry.get("bot_id") or entry.get("player_id") or entry.get("player")
    if direct is not None:
        return str(direct)
    seat = entry.get("seat")
    if isinstance(seat, int) and seat in seats:
        return seats[seat]
    return None


def _action_name(value: Any) -> str | None:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, Mapping):
        action = value.get("action")
        return str(action).lower() if action is not None else None
    return None


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _decision_records(hand: Mapping[str, Any], source: str, hand_index: int) -> list[dict[str, Any]]:
    candidates: list[Mapping[str, Any]] = []
    decisions = hand.get("decisions")
    if isinstance(decisions, list):
        candidates.extend(item for item in decisions if isinstance(item, Mapping))
    for key in (*ACTION_KEYS, "events"):
        entries = hand.get(key)
        if isinstance(entries, list):
            candidates.extend(item for item in entries if isinstance(item, Mapping))

    records = []
    for decision_index, item in enumerate(candidates):
        state = None
        for key in STATE_KEYS:
            if isinstance(item.get(key), Mapping):
                state = dict(item[key])
                break
        if state is None:
            continue
        actual = item.get("actual_action")
        if actual is None:
            actual = item.get("response")
        if actual is None:
            actual = item.get("decision")
        if actual is None and "action" in item:
            actual = {"action": item.get("action"), "amount": item.get("amount")}
        records.append(
            {
                "source": source,
                "hand_index": hand_index,
                "hand_id": hand.get("hand_id", hand.get("hand_num", hand_index)),
                "decision_index": decision_index,
                "state": state,
                "actual_action": actual,
            }
        )
    return records


def analyze_documents(
    documents: Sequence[tuple[str, Any]],
    *,
    hero_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    all_matches: list[tuple[str, Mapping[str, Any]]] = []
    all_hands: list[tuple[str, Mapping[str, Any]]] = []
    for source, document in documents:
        matches, hands = extract_matches_and_hands(document)
        all_matches.extend((source, match) for match in matches)
        all_hands.extend((source, hand) for hand in hands)
    if not all_hands:
        raise EvaluationError("history JSON contains no recognizable hands")

    action_counts: Counter[str] = Counter()
    street_action_counts: dict[str, Counter[str]] = {}
    actor_counts: Counter[str] = Counter()
    error_count = 0
    records: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for hand_index, (source, hand) in enumerate(all_hands):
        seats = _seat_map(hand)
        kept_actions = []
        for entry in _actions(hand):
            actor = _actor(entry, seats)
            action = _action_name(entry)
            if hero_id is not None and actor != hero_id:
                continue
            if action is None:
                continue
            street = str(entry.get("street", "unknown")).lower()
            action_counts[action] += 1
            street_action_counts.setdefault(street, Counter())[action] += 1
            if actor is not None:
                actor_counts[actor] += 1
            if entry.get("error"):
                error_count += 1
            kept_actions.append(
                {
                    "actor": actor,
                    "seat": entry.get("seat"),
                    "street": street,
                    "action": action,
                    "amount": entry.get("amount"),
                    "error": entry.get("error"),
                }
            )
        hand_record = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "hand",
            "source": source,
            "hand_index": hand_index,
            "hand_id": hand.get("hand_id", hand.get("hand_num", hand_index)),
            "community_cards": hand.get("community_cards", hand.get("board", [])),
            "actions": kept_actions,
            "action_count": len(kept_actions),
        }
        records.append(hand_record)
        decisions.extend(_decision_records(hand, source, hand_index))

    # Prefer match-level deltas, because summing both match and hand deltas
    # would double-count engine run_match histories.
    match_deltas: list[float] = []
    for _, match in all_matches:
        delta = match.get("chip_delta")
        if isinstance(delta, Mapping):
            if hero_id is not None:
                number = _numeric(delta.get(hero_id))
                if number is not None:
                    match_deltas.append(number)
            else:
                numbers = [_numeric(value) for value in delta.values()]
                match_deltas.extend(number for number in numbers if number is not None)
    if not match_deltas:
        for _, hand in all_hands:
            delta = hand.get("chip_delta")
            if isinstance(delta, Mapping):
                if hero_id is not None:
                    number = _numeric(delta.get(hero_id))
                    if number is not None:
                        match_deltas.append(number)
                else:
                    numbers = [_numeric(value) for value in delta.values()]
                    match_deltas.extend(number for number in numbers if number is not None)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "hero_id": hero_id,
        "match_count": len(all_matches),
        "hand_count": len(all_hands),
        "action_count": sum(action_counts.values()),
        "action_counts": dict(sorted(action_counts.items())),
        "street_action_counts": {
            street: dict(sorted(counts.items())) for street, counts in sorted(street_action_counts.items())
        },
        "actor_action_counts": dict(sorted(actor_counts.items())),
        "error_count": error_count,
        "decision_snapshot_count": len(decisions),
        "chip_delta_observations": match_deltas,
        "chip_delta_total": sum(match_deltas),
        "chip_delta_mean": sum(match_deltas) / len(match_deltas) if match_deltas else None,
    }
    return summary, records, decisions


def replay_decisions(
    decisions: Sequence[Mapping[str, Any]],
    act: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not decisions:
        raise EvaluationError(
            "--candidate requested replay, but histories contain no captured decision states"
        )
    records = []
    action_agreements = 0
    exact_agreements = 0
    replay_errors = 0
    for index, decision in enumerate(decisions):
        try:
            replayed = act(decision["state"])
        except Exception as exc:
            replayed = {"action": None, "error": f"{type(exc).__name__}: {exc}"}
        if not isinstance(replayed, Mapping):
            replayed = {"action": None, "error": f"non_mapping_response:{type(replayed).__name__}"}
        actual = decision.get("actual_action")
        actual_name = _action_name(actual)
        replay_name = _action_name(replayed)
        action_match = actual_name is not None and actual_name == replay_name
        exact_match = action_match
        if action_match and actual_name == "raise" and isinstance(actual, Mapping):
            exact_match = actual.get("amount") == replayed.get("amount")
        action_agreements += int(action_match)
        exact_agreements += int(exact_match)
        replay_errors += int(bool(replayed.get("error")))
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "decision_replay",
                "replay_index": index,
                "source": decision.get("source"),
                "hand_index": decision.get("hand_index"),
                "hand_id": decision.get("hand_id"),
                "decision_index": decision.get("decision_index"),
                "actual_action": actual,
                "replayed_action": dict(replayed),
                "action_match": action_match,
                "exact_match": exact_match,
            }
        )
    total = len(records)
    return {
        "decision_count": total,
        "action_agreements": action_agreements,
        "action_agreement_rate": action_agreements / total,
        "exact_agreements": exact_agreements,
        "exact_agreement_rate": exact_agreements / total,
        "replay_errors": replay_errors,
    }, records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", action="append", type=Path, default=[], help="JSON/JSONL file or directory; repeatable")
    parser.add_argument("--history-dir", type=Path, default=ROOT / "histories" / "qualifier", help="Default history directory when --history is omitted")
    parser.add_argument("--hero-id", help="Restrict action and chip-delta analysis to this bot id")
    parser.add_argument(
        "--candidate",
        help="Bot artifact for instrumented decision-state replay (official raw history is analysis-only)",
    )
    parser.add_argument("--engine-dir", type=Path, default=DEFAULT_ENGINE_DIR)
    parser.add_argument("--output-dir", type=Path, help="Artifact directory; defaults to evaluation_runs/<timestamp>-qualifier-replay")
    parser.add_argument("--allow-replay-errors", action="store_true", help="Return success while recording sandbox replay errors")
    return parser


def _resolve_candidate(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = (args.output_dir or default_output_dir("qualifier-replay")).expanduser().resolve()
    manifest_path = output_dir / "manifest.json"
    records_path = output_dir / "records.jsonl"
    summary_path = output_dir / "summary.json"
    try:
        files = discover_history_files(args.history, args.history_dir)
        if records_path.exists():
            raise EvaluationError(f"refusing to overwrite existing replay records: {records_path}")
        documents: list[tuple[str, Any]] = []
        for path in files:
            documents.extend((str(path), document) for document in load_history_file(path))
        analysis, hand_records, decisions = analyze_documents(documents, hero_id=args.hero_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "status": "running",
            "created_utc": utc_now(),
            "command": sys.argv,
            "git": git_provenance(),
            "inputs": [
                {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
                for path in files
            ],
            "hero_id": args.hero_id,
            "outputs": {"manifest": "manifest.json", "records": "records.jsonl", "summary": "summary.json"},
        }
        dump_json(manifest_path, manifest)
        for record in hand_records:
            append_jsonl(records_path, record)

        replay_summary = None
        if args.candidate:
            candidate = validate_artifact(BotArtifact("candidate", _resolve_candidate(args.candidate)))
            _, engine_info = load_engine(args.engine_dir)
            match_module = sys.modules.get("sandbox.match")
            bot_process_type = getattr(match_module, "BotProcess", None)
            if not callable(bot_process_type):
                raise PrerequisiteError("official sandbox.match does not expose BotProcess for replay")
            process = bot_process_type("qualifier_replay", str(candidate.path))
            try:
                process.warmup()
                replay_summary, replay_records = replay_decisions(decisions, process.act)
            finally:
                process.stop()
            for record in replay_records:
                append_jsonl(records_path, record)
            manifest["candidate"] = {
                "path": str(candidate.path),
                "sha256": artifact_digest(candidate.path),
            }
            manifest["engine"] = engine_info
            if replay_summary["replay_errors"] and not args.allow_replay_errors:
                raise MatchFailure(
                    f"sandbox replay produced {replay_summary['replay_errors']} errors"
                )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "created_utc": utc_now(),
            "analysis": analysis,
            "replay": replay_summary,
        }
        dump_json(summary_path, summary)
        manifest.update({"status": "complete", "completed_utc": utc_now()})
        dump_json(manifest_path, manifest)
        print(json.dumps({"summary": summary, "output_dir": str(output_dir)}, sort_keys=True))
        return 0
    except PrerequisiteError as exc:
        print(f"qualifier replay prerequisite failure: {exc}", file=sys.stderr)
        return 3
    except (EvaluationError, MatchFailure) as exc:
        if manifest_path.exists():
            try:
                current = json.loads(manifest_path.read_text(encoding="utf-8"))
                current.update(
                    {
                        "status": "failed",
                        "completed_utc": utc_now(),
                        "failure": {
                            "type": type(exc).__name__,
                            "message": str(exc),
                            "traceback": traceback.format_exc(),
                        },
                    }
                )
                dump_json(manifest_path, current)
            except Exception:
                pass
        print(f"qualifier replay failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
