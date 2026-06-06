#!/usr/bin/env python3
"""Quick 6-max evidence runner for finals-day v_final.zip.

Local-only tool. It does not modify src/, data/, submissions/, or ext/.
Uses ext/fullhouse-engine/sandbox/match.py::run_match with six bot paths.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "ext" / "fullhouse-engine"
SANDBOX = ENGINE / "sandbox"
REF_BOTS = ENGINE / "bots"
DEFAULT_OUT = ROOT / "consult" / "artifacts" / "2026-06-04-finals-ship" / "6max_evidence"
THORP_ZIP = ROOT / "submissions" / "v_final.zip"
EXPECTED_SHA_PREFIX = "b108eff5"

sys.path.insert(0, str(SANDBOX))
sys.path.insert(0, str(ENGINE))
import match as match_mod  # noqa: E402

VALID_ACTIONS = {"fold", "check", "call", "raise", "all_in"}
ACTION_RECORDS: List[Dict[str, Any]] = []


class RecordingBotProcess(match_mod.BotProcess):
    """In-memory instrumentation of runner responses; engine code remains frozen."""

    def act(self, game_state: dict) -> dict:  # type: ignore[override]
        raw = super().act(game_state)
        action = str(raw.get("action", "fold")).lower().strip() if isinstance(raw, dict) else "fold"
        amount_raw = raw.get("amount") if isinstance(raw, dict) else None
        try:
            amount_int = int(amount_raw or 0)
            amount_parse_error = False
        except (TypeError, ValueError):
            amount_int = 0
            amount_parse_error = True

        owed = int(game_state.get("amount_owed") or 0)
        can_check = bool(game_state.get("can_check"))
        min_raise_to = int(game_state.get("min_raise_to") or 0)
        your_stack = int(game_state.get("your_stack") or 0)
        your_bet = int(game_state.get("your_bet_this_street") or 0)
        current_bet = int(game_state.get("current_bet") or 0)

        invalid_name = action not in VALID_ACTIONS
        check_when_owed = action == "check" and not can_check
        raise_without_amount = action == "raise" and "amount" not in raw
        raise_below_min = action == "raise" and amount_int < min_raise_to
        raise_to_nonpositive = action == "raise" and amount_int <= your_bet
        fold_default = bool(isinstance(raw, dict) and raw.get("error")) or invalid_name

        ACTION_RECORDS.append({
            "bot_id": self.bot_id,
            "hand_id": game_state.get("hand_id"),
            "street": game_state.get("street"),
            "seat": game_state.get("seat_to_act"),
            "raw_action": action,
            "raw_amount": amount_raw,
            "runner_error": raw.get("error") if isinstance(raw, dict) else "non_dict_response",
            "invalid_name": invalid_name,
            "check_when_owed": check_when_owed,
            "raise_without_amount": raise_without_amount,
            "raise_below_min": raise_below_min,
            "raise_to_nonpositive": raise_to_nonpositive,
            "amount_parse_error": amount_parse_error,
            "fold_default": fold_default,
            "amount_owed": owed,
            "can_check": can_check,
            "min_raise_to": min_raise_to,
            "your_stack": your_stack,
            "your_bet_this_street": your_bet,
            "current_bet": current_bet,
        })
        return raw


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_extract_zip(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            name = member.filename
            if name.startswith(("/", "\\")):
                raise ValueError(f"unsafe absolute zip path: {name!r}")
            norm = os.path.normpath(str(dest / name))
            if not (norm == str(dest) or norm.startswith(str(dest) + os.sep)):
                raise ValueError(f"unsafe traversal zip path: {name!r}")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"unsafe symlink zip path: {name!r}")
        zf.extractall(dest)
    if not (dest / "bot.py").is_file():
        raise ValueError(f"{zip_path} did not extract to root bot.py")


def table_mixes() -> Dict[str, List[Tuple[str, Path]]]:
    return {
        "reference_field": [
            ("aggressor", REF_BOTS / "aggressor"),
            ("mathematician", REF_BOTS / "mathematician"),
            ("ref_bot_2", REF_BOTS / "ref_bot_2"),
            ("shark", REF_BOTS / "shark"),
            ("template", REF_BOTS / "template"),
        ],
        "aggro_collision": [
            ("aggressor_a", REF_BOTS / "aggressor"),
            ("aggressor_b", REF_BOTS / "aggressor"),
            ("aggressor_c", REF_BOTS / "aggressor"),
            ("shark", REF_BOTS / "shark"),
            ("ref_bot_2", REF_BOTS / "ref_bot_2"),
        ],
        "balanced_heavy": [
            ("shark_a", REF_BOTS / "shark"),
            ("shark_b", REF_BOTS / "shark"),
            ("ref_bot_2_a", REF_BOTS / "ref_bot_2"),
            ("ref_bot_2_b", REF_BOTS / "ref_bot_2"),
            ("template", REF_BOTS / "template"),
        ],
    }


def build_seated_paths(thorp_dir: Path, opponents: List[Tuple[str, Path]], thorp_seat: int, copy_root: Path) -> OrderedDict[str, str]:
    """Return six ordered bot paths with Thorp occupying thorp_seat.

    Duplicate reference bots are copied to temp dirs per the finals-lane instruction.
    """
    seats: List[Tuple[str, Path]] = []
    opp_iter = iter(opponents)
    for seat in range(6):
        if seat == thorp_seat:
            seats.append(("thorp", thorp_dir))
        else:
            seats.append(next(opp_iter))

    seen_source_counts: Counter[str] = Counter()
    out: OrderedDict[str, str] = OrderedDict()
    for bot_id, path in seats:
        if bot_id == "thorp":
            out[bot_id] = str(path)
            continue
        source_key = str(path.resolve())
        seen_source_counts[source_key] += 1
        if seen_source_counts[source_key] > 1:
            copy_path = copy_root / f"{bot_id}_{seen_source_counts[source_key]}"
            if copy_path.exists():
                shutil.rmtree(copy_path)
            shutil.copytree(path, copy_path, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            out[bot_id] = str(copy_path)
        else:
            out[bot_id] = str(path)
    return out


def classify_records(records: Iterable[Dict[str, Any]], bot_id: str) -> Dict[str, Any]:
    recs = [r for r in records if r.get("bot_id") == bot_id]
    runner_errors = Counter(str(r.get("runner_error")) for r in recs if r.get("runner_error"))
    illegal_names = sum(1 for r in recs if r.get("invalid_name"))
    protocol_coercions = {
        "check_when_owed": sum(1 for r in recs if r.get("check_when_owed")),
        "raise_without_amount": sum(1 for r in recs if r.get("raise_without_amount")),
        "raise_below_min": sum(1 for r in recs if r.get("raise_below_min")),
        "raise_to_nonpositive": sum(1 for r in recs if r.get("raise_to_nonpositive")),
        "amount_parse_error": sum(1 for r in recs if r.get("amount_parse_error")),
    }
    return {
        "decisions": len(recs),
        "runner_errors": dict(runner_errors),
        "timeouts": runner_errors.get("timeout", 0),
        "exceptions": runner_errors.get("exception", 0),
        "load_failed": runner_errors.get("load_failed", 0),
        "warmup_timeout": runner_errors.get("warmup_timeout", 0),
        "warmup_exception": runner_errors.get("warmup_exception", 0),
        "illegal_action_names": illegal_names,
        "fold_defaults": sum(1 for r in recs if r.get("fold_default")),
        "protocol_coercions": protocol_coercions,
    }


def summarize_busts(result: Dict[str, Any], bot_id: str) -> Dict[str, Any]:
    bust_hand = None
    bust_street = None
    for hand in result.get("hands", []):
        stacks = hand.get("final_stacks", {})
        if stacks.get(bot_id, 1) <= 0:
            bust_hand = hand.get("hand_num")
            bust_street = hand.get("street")
            break
    return {
        "busted": bust_hand is not None,
        "bust_hand": bust_hand,
        "bust_street": bust_street,
    }


def compact_result(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "match_id": result.get("match_id"),
        "seed": result.get("seed"),
        "n_hands": result.get("n_hands"),
        "duration_s": result.get("duration_s"),
        "bot_ids": result.get("bot_ids"),
        "final_stacks": result.get("final_stacks"),
        "chip_delta": result.get("chip_delta"),
        "bot_errors": result.get("bot_errors"),
    }


def run_one(mix_name: str, opponents: List[Tuple[str, Path]], thorp_dir: Path, thorp_seat: int, seed: int, hands: int, out_dir: Path) -> Dict[str, Any]:
    global ACTION_RECORDS
    ACTION_RECORDS = []
    match_mod.BotProcess = RecordingBotProcess  # monkeypatch in this process only
    match_id = f"{mix_name}_seat{thorp_seat}_seed{seed}"
    with tempfile.TemporaryDirectory(prefix=f"fh6_{mix_name}_") as tmp:
        copy_root = Path(tmp) / "dup_refs"
        copy_root.mkdir(parents=True, exist_ok=True)
        bot_paths = build_seated_paths(thorp_dir, opponents, thorp_seat, copy_root)
        started = time.time()
        result = match_mod.run_match(match_id, bot_paths, n_hands=hands, verbose=False, seed=seed)
        elapsed = round(time.time() - started, 2)

    metrics = classify_records(ACTION_RECORDS, "thorp")
    busts = summarize_busts(result, "thorp")
    row = {
        "mix": mix_name,
        "thorp_seat": thorp_seat,
        "seed": seed,
        "hands_requested": hands,
        "hands_played": result.get("n_hands"),
        "duration_s": result.get("duration_s", elapsed),
        "thorp_delta": result.get("chip_delta", {}).get("thorp"),
        "thorp_final_stack": result.get("final_stacks", {}).get("thorp"),
        **metrics,
        **busts,
        "bot_errors_all": result.get("bot_errors", {}),
        "bot_ids": result.get("bot_ids", []),
        "chip_delta_all": result.get("chip_delta", {}),
    }

    raw_path = out_dir / f"{match_id}.json"
    raw_path.write_text(json.dumps({
        "row": row,
        "compact_result": compact_result(result),
        "thorp_action_records": [r for r in ACTION_RECORDS if r.get("bot_id") == "thorp"],
        "all_action_error_records": [r for r in ACTION_RECORDS if r.get("runner_error") or r.get("invalid_name")],
    }, indent=2, sort_keys=True), encoding="utf-8")
    return row


def aggregate(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["mix"]].append(row)

    summaries: List[Dict[str, Any]] = []
    for mix, mix_rows in grouped.items():
        n = len(mix_rows)
        total_delta = sum(int(r.get("thorp_delta") or 0) for r in mix_rows)
        total_hands = sum(int(r.get("hands_played") or 0) for r in mix_rows)
        total_decisions = sum(int(r.get("decisions") or 0) for r in mix_rows)
        total_fold_defaults = sum(int(r.get("fold_defaults") or 0) for r in mix_rows)
        total_illegal = sum(int(r.get("illegal_action_names") or 0) for r in mix_rows)
        total_timeouts = sum(int(r.get("timeouts") or 0) for r in mix_rows)
        total_exceptions = sum(int(r.get("exceptions") or 0) for r in mix_rows)
        busts = sum(1 for r in mix_rows if r.get("busted"))
        runner_errors = Counter()
        coercions = Counter()
        for r in mix_rows:
            runner_errors.update(r.get("runner_errors", {}))
            coercions.update(r.get("protocol_coercions", {}))
        summaries.append({
            "mix": mix,
            "matches": n,
            "hands_total": total_hands,
            "thorp_delta_sum": total_delta,
            "thorp_delta_avg_per_match": round(total_delta / n, 2) if n else 0.0,
            "thorp_chip_per_100_hands": round(total_delta * 100.0 / total_hands, 2) if total_hands else 0.0,
            "thorp_decisions": total_decisions,
            "fold_defaults": total_fold_defaults,
            "illegal_action_names": total_illegal,
            "timeouts": total_timeouts,
            "exceptions": total_exceptions,
            "runner_errors": dict(runner_errors),
            "protocol_coercions": dict(coercions),
            "busts": busts,
            "bust_rate": round(busts / n, 4) if n else 0.0,
            "bust_streets": dict(Counter(str(r.get("bust_street")) for r in mix_rows if r.get("busted"))),
            "seats": sorted(int(r["thorp_seat"]) for r in mix_rows),
            "seeds": sorted(int(r["seed"]) for r in mix_rows),
        })
    return summaries


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, sha: str, rows: List[Dict[str, Any]], summaries: List[Dict[str, Any]], hands: int, seed_base: int) -> None:
    lines = []
    lines.append("# Finals 6-max evidence: v_final.zip")
    lines.append("")
    lines.append(f"- zip: `{THORP_ZIP.relative_to(ROOT)}`")
    lines.append(f"- sha256: `{sha}`")
    lines.append(f"- expected prefix: `{EXPECTED_SHA_PREFIX}`; match: `{sha.startswith(EXPECTED_SHA_PREFIX)}`")
    lines.append(f"- engine primitive: `ext/fullhouse-engine/sandbox/match.py::run_match`")
    lines.append(f"- hands per match: `{hands}`; seat rotations: `0..5`; paired seeds: `{seed_base}..{seed_base + 5}`")
    lines.append(f"- mode: local subprocess runner under `{sys.executable}`")
    lines.append("")
    lines.append("## Per-mix summary")
    lines.append("")
    lines.append("| mix | matches | hands | Thorp delta sum | avg/match | chip/100 | decisions | fold-defaults | illegal names | timeouts | exceptions | busts | bust streets |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for s in summaries:
        lines.append(
            f"| {s['mix']} | {s['matches']} | {s['hands_total']} | {s['thorp_delta_sum']} | "
            f"{s['thorp_delta_avg_per_match']} | {s['thorp_chip_per_100_hands']} | {s['thorp_decisions']} | "
            f"{s['fold_defaults']} | {s['illegal_action_names']} | {s['timeouts']} | {s['exceptions']} | "
            f"{s['busts']} | `{json.dumps(s['bust_streets'], sort_keys=True)}` |"
        )
    lines.append("")
    lines.append("## Per-seat rows")
    lines.append("")
    lines.append("| mix | seat | seed | hands | delta | final stack | decisions | fold-defaults | illegal names | timeouts | exceptions | busted | bust street |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for r in rows:
        lines.append(
            f"| {r['mix']} | {r['thorp_seat']} | {r['seed']} | {r['hands_played']} | "
            f"{r['thorp_delta']} | {r['thorp_final_stack']} | {r['decisions']} | {r['fold_defaults']} | "
            f"{r['illegal_action_names']} | {r['timeouts']} | {r['exceptions']} | {r['busted']} | {r['bust_street']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run finals-day 6-max evidence for submissions/v_final.zip")
    p.add_argument("--hands", type=int, default=800)
    p.add_argument("--seed-base", type=int, default=42)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--mix", choices=sorted(table_mixes().keys()), action="append", help="Limit to a mix; repeatable")
    p.add_argument("--seat", type=int, choices=range(6), action="append", help="Limit to a Thorp seat; repeatable")
    p.add_argument("--fail-on-sha-mismatch", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.out_dir / "raw_matches"
    raw_dir.mkdir(parents=True, exist_ok=True)

    sha = sha256_file(THORP_ZIP)
    if args.fail_on_sha_mismatch and not sha.startswith(EXPECTED_SHA_PREFIX):
        raise SystemExit(f"sha mismatch: {sha} does not start with {EXPECTED_SHA_PREFIX}")

    mixes = table_mixes()
    selected_mixes = args.mix or list(mixes.keys())
    selected_seats = args.seat or list(range(6))

    started = time.time()
    rows: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="fh6_thorp_") as tmp:
        thorp_dir = Path(tmp) / "thorp"
        thorp_dir.mkdir(parents=True, exist_ok=True)
        safe_extract_zip(THORP_ZIP, thorp_dir)
        for mix_name in selected_mixes:
            opponents = mixes[mix_name]
            for seat in selected_seats:
                seed = args.seed_base + seat
                print(f"[quick_6max_eval] running mix={mix_name} thorp_seat={seat} seed={seed} hands={args.hands}", flush=True)
                row = run_one(mix_name, opponents, thorp_dir, seat, seed, args.hands, raw_dir)
                rows.append(row)
                print(
                    f"[quick_6max_eval] done mix={mix_name} seat={seat}: "
                    f"delta={row['thorp_delta']} decisions={row['decisions']} "
                    f"fold_defaults={row['fold_defaults']} errors={row['runner_errors']} busted={row['busted']}",
                    flush=True,
                )

    summaries = aggregate(rows)
    elapsed = round(time.time() - started, 2)
    manifest = {
        "created_at_epoch": time.time(),
        "duration_s": elapsed,
        "python": sys.executable,
        "v_final_zip": str(THORP_ZIP),
        "sha256": sha,
        "sha_prefix_expected": EXPECTED_SHA_PREFIX,
        "sha_prefix_match": sha.startswith(EXPECTED_SHA_PREFIX),
        "hands": args.hands,
        "seed_base": args.seed_base,
        "rows": rows,
        "summaries": summaries,
    }
    (args.out_dir / "summary.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.out_dir / "per_match.csv", rows, [
        "mix", "thorp_seat", "seed", "hands_played", "duration_s", "thorp_delta", "thorp_final_stack",
        "decisions", "fold_defaults", "illegal_action_names", "timeouts", "exceptions", "busted", "bust_hand", "bust_street",
    ])
    write_csv(args.out_dir / "per_mix.csv", summaries, [
        "mix", "matches", "hands_total", "thorp_delta_sum", "thorp_delta_avg_per_match", "thorp_chip_per_100_hands",
        "thorp_decisions", "fold_defaults", "illegal_action_names", "timeouts", "exceptions", "busts", "bust_rate", "bust_streets",
    ])
    write_markdown(args.out_dir / "REPORT.md", sha, rows, summaries, args.hands, args.seed_base)

    print(f"[quick_6max_eval] wrote {args.out_dir / 'REPORT.md'}")
    print(json.dumps({"duration_s": elapsed, "summaries": summaries}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
