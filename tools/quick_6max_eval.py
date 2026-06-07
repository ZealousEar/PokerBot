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
import random
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
SYNTHETIC_MIX_STYLES = {"adaptive_overfold_pressure": "adaptive_overfold_exploiter"}
MIX_CHOICES = ("adaptive_overfold_pressure", "aggro_collision", "balanced_heavy", "reference_field")

sys.path.insert(0, str(SANDBOX))
sys.path.insert(0, str(ENGINE))
import match as match_mod  # noqa: E402
from engine.game import BIG_BLIND, STARTING_STACK  # noqa: E402
try:  # noqa: E402
    import synthetic_opponents  # type: ignore  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover - import path differs under package imports
    from tools import synthetic_opponents  # type: ignore  # noqa: E402

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


def table_mixes(synthetic_paths: Dict[str, Path] | None = None) -> Dict[str, List[Tuple[str, Path]]]:
    mixes: Dict[str, List[Tuple[str, Path]]] = {
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
    if synthetic_paths:
        adaptive = synthetic_paths.get("adaptive_overfold_exploiter")
        if adaptive is not None:
            mixes["adaptive_overfold_pressure"] = [
                (f"adaptive_overfold_{idx}", adaptive) for idx in range(1, 6)
            ]
    return mixes


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


def bb100(chips: int | float, hands: int | float) -> float:
    return round((float(chips) / BIG_BLIND) / (float(hands) / 100.0), 4) if hands else 0.0


def pressure_kind(street: str, first_aggression_on_street: bool, bot_id: str, flop_pressure_bots: set[str]) -> str:
    if street == "flop" and first_aggression_on_street:
        return "flop_cbet_or_probe"
    if street == "turn" and first_aggression_on_street and bot_id in flop_pressure_bots:
        return "turn_barrel"
    if street == "turn" and first_aggression_on_street:
        return "turn_probe"
    return "postflop_raise_pressure"


def pressure_bleed_diagnostics(result: Dict[str, Any], mix_name: str, seed: int, thorp_seat: int, hero_id: str = "thorp") -> List[Dict[str, Any]]:
    """Rows where Thorp folds flop/turn after non-Thorp pressure in 6-max.

    This mirrors the HU gauntlet's mechanism-matched metric and uses engine
    `events`, not raw win-rate or runner response logs.
    """
    rows: List[Dict[str, Any]] = []
    prev_stack = STARTING_STACK
    for hand in result.get("hands", []):
        final_stack = int((hand.get("final_stacks") or {}).get(hero_id, prev_stack))
        hero_delta = final_stack - prev_stack
        prev_stack = final_stack
        street_aggression_seen: Dict[str, bool] = {}
        flop_pressure_bots: set[str] = set()
        last_pressure: Dict[str, Any] | None = None
        for index, event in enumerate(hand.get("events") or []):
            if event.get("type") != "action":
                continue
            street = str(event.get("street") or "")
            bot_id = str(event.get("bot_id") or "")
            action = str(event.get("action") or "")
            if street in {"flop", "turn"} and bot_id != hero_id and action in {"raise", "all_in"}:
                first = not street_aggression_seen.get(street, False)
                street_aggression_seen[street] = True
                kind = pressure_kind(street, first, bot_id, flop_pressure_bots)
                if street == "flop":
                    flop_pressure_bots.add(bot_id)
                last_pressure = {
                    "street": street,
                    "pressure_kind": kind,
                    "pressure_bot": bot_id,
                    "pressure_action": action,
                    "pressure_amount": int(event.get("amount") or 0),
                    "pressure_pot_after": int(event.get("pot_after") or event.get("pot") or 0),
                    "pressure_event_index": index,
                }
                continue
            if street in {"flop", "turn"} and bot_id == hero_id and action == "fold" and last_pressure and last_pressure["street"] == street:
                rows.append({
                    "mix": mix_name,
                    "seed": seed,
                    "thorp_seat": thorp_seat,
                    "hand_num": hand.get("hand_num"),
                    "hand_id": hand.get("hand_id"),
                    **last_pressure,
                    "fold_event_index": index,
                    "fold_pot": int(event.get("pot") or 0),
                    "hero_delta": hero_delta,
                    "hero_chip_loss": max(0, -hero_delta),
                    "final_street": hand.get("street"),
                    "final_pot": hand.get("pot"),
                    "showdown": hand.get("showdown"),
                    "community_cards": " ".join(hand.get("community_cards") or []),
                    "action_log": json.dumps(hand.get("action_log") or [], sort_keys=True),
                })
                break
    return rows


def summarize_pressure_bleed(rows: List[Dict[str, Any]], hands: int) -> Dict[str, Any]:
    by_street = Counter(str(row.get("street")) for row in rows)
    by_kind = Counter(str(row.get("pressure_kind")) for row in rows)
    chip_loss = sum(int(row.get("hero_chip_loss") or 0) for row in rows)
    net_delta = sum(int(row.get("hero_delta") or 0) for row in rows)
    surrendered_pot = sum(int(row.get("pressure_pot_after") or 0) for row in rows)
    return {
        "postflop_pressure_fold_count": len(rows),
        "postflop_pressure_fold_loss_chips": chip_loss,
        "postflop_pressure_fold_net_delta_chips": net_delta,
        "postflop_pressure_fold_loss_bb100": bb100(-chip_loss, hands),
        "pressure_pot_after_surrendered_chips": surrendered_pot,
        "pressure_pot_after_surrendered_bb100": bb100(-surrendered_pot, hands),
        "by_street": dict(by_street),
        "by_pressure_kind": dict(by_kind),
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

    pressure_rows = pressure_bleed_diagnostics(result, mix_name, seed, thorp_seat)
    pressure_summary = summarize_pressure_bleed(pressure_rows, int(result.get("n_hands") or 0))
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
        "pressure_bleed": pressure_summary,
        "pressure_fold_count": pressure_summary["postflop_pressure_fold_count"],
        "pressure_fold_loss_chips": pressure_summary["postflop_pressure_fold_loss_chips"],
        "pressure_fold_net_delta_chips": pressure_summary["postflop_pressure_fold_net_delta_chips"],
        "pressure_fold_loss_bb100": pressure_summary["postflop_pressure_fold_loss_bb100"],
        "pressure_pot_after_surrendered_chips": pressure_summary["pressure_pot_after_surrendered_chips"],
        "pressure_pot_after_surrendered_bb100": pressure_summary["pressure_pot_after_surrendered_bb100"],
        "pressure_by_street": pressure_summary["by_street"],
        "pressure_by_kind": pressure_summary["by_pressure_kind"],
        "_pressure_bleed_hands": pressure_rows,
        **metrics,
        **busts,
        "bot_errors_all": result.get("bot_errors", {}),
        "bot_ids": result.get("bot_ids", []),
        "chip_delta_all": result.get("chip_delta", {}),
    }

    raw_row = dict(row)
    raw_row.pop("_pressure_bleed_hands", None)
    raw_path = out_dir / f"{match_id}.json"
    raw_path.write_text(json.dumps({
        "row": raw_row,
        "compact_result": compact_result(result),
        "pressure_bleed_hands": pressure_rows,
        "thorp_action_records": [r for r in ACTION_RECORDS if r.get("bot_id") == "thorp"],
        "all_action_error_records": [r for r in ACTION_RECORDS if r.get("runner_error") or r.get("invalid_name")],
    }, indent=2, sort_keys=True), encoding="utf-8")
    return row


def bootstrap_bb100_ci(rows: List[Dict[str, Any]], seed: int, draws: int = 2000) -> Dict[str, float]:
    if not rows:
        return {"mean": 0.0, "low": 0.0, "high": 0.0, "half_width": 0.0}
    rnd = random.Random(seed)
    vals: List[float] = []
    n = len(rows)
    for _ in range(draws):
        sample = [rows[rnd.randrange(n)] for _ in range(n)]
        chips = sum(int(r.get("thorp_delta") or 0) for r in sample)
        hands = sum(int(r.get("hands_played") or 0) for r in sample)
        vals.append(bb100(chips, hands))
    vals.sort()
    low = vals[int(0.025 * (draws - 1))]
    high = vals[int(0.975 * (draws - 1))]
    mean = sum(vals) / len(vals)
    return {
        "mean": round(mean, 4),
        "low": round(low, 4),
        "high": round(high, 4),
        "half_width": round((high - low) / 2.0, 4),
    }


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
        total_pressure_fold_count = sum(int(r.get("pressure_fold_count") or 0) for r in mix_rows)
        total_pressure_fold_loss = sum(int(r.get("pressure_fold_loss_chips") or 0) for r in mix_rows)
        total_pressure_fold_net = sum(int(r.get("pressure_fold_net_delta_chips") or 0) for r in mix_rows)
        total_pressure_pot_surrendered = sum(int(r.get("pressure_pot_after_surrendered_chips") or 0) for r in mix_rows)
        runner_errors = Counter()
        coercions = Counter()
        pressure_streets = Counter()
        pressure_kinds = Counter()
        for r in mix_rows:
            runner_errors.update(r.get("runner_errors", {}))
            coercions.update(r.get("protocol_coercions", {}))
            pressure_streets.update(r.get("pressure_by_street", {}))
            pressure_kinds.update(r.get("pressure_by_kind", {}))
        ci_seed = sum(ord(ch) for ch in mix) ^ total_hands ^ n
        summaries.append({
            "mix": mix,
            "matches": n,
            "hands_total": total_hands,
            "thorp_delta_sum": total_delta,
            "thorp_delta_avg_per_match": round(total_delta / n, 2) if n else 0.0,
            "thorp_chip_per_100_hands": round(total_delta * 100.0 / total_hands, 2) if total_hands else 0.0,
            "thorp_bb100": bb100(total_delta, total_hands),
            "thorp_bb100_ci": bootstrap_bb100_ci(mix_rows, ci_seed),
            "pressure_fold_count": total_pressure_fold_count,
            "pressure_fold_loss_chips": total_pressure_fold_loss,
            "pressure_fold_net_delta_chips": total_pressure_fold_net,
            "pressure_fold_loss_bb100": bb100(-total_pressure_fold_loss, total_hands),
            "pressure_pot_after_surrendered_chips": total_pressure_pot_surrendered,
            "pressure_pot_after_surrendered_bb100": bb100(-total_pressure_pot_surrendered, total_hands),
            "pressure_by_street": dict(pressure_streets),
            "pressure_by_kind": dict(pressure_kinds),
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


def write_pressure_bleed_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fields = [
        "mix", "seed", "thorp_seat", "hand_num", "hand_id", "street",
        "pressure_kind", "pressure_bot", "pressure_action", "pressure_amount",
        "pressure_pot_after", "pressure_event_index", "fold_event_index",
        "fold_pot", "hero_delta", "hero_chip_loss", "final_street",
        "final_pot", "showdown", "community_cards", "action_log",
    ]
    write_csv(path, rows, fields)


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
    lines.append("| mix | matches | hands | Thorp delta sum | avg/match | chip/100 | bb/100 | bb/100 CI | pressure folds | pressure loss chips | pressure loss bb/100 | decisions | fold-defaults | illegal names | timeouts | exceptions | busts | bust streets |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for s in summaries:
        lines.append(
            f"| {s['mix']} | {s['matches']} | {s['hands_total']} | {s['thorp_delta_sum']} | "
            f"{s['thorp_delta_avg_per_match']} | {s['thorp_chip_per_100_hands']} | {s['thorp_bb100']} | "
            f"`{json.dumps(s['thorp_bb100_ci'], sort_keys=True)}` | "
            f"{s['pressure_fold_count']} | {s['pressure_fold_loss_chips']} | {s['pressure_fold_loss_bb100']} | "
            f"{s['thorp_decisions']} | {s['fold_defaults']} | {s['illegal_action_names']} | {s['timeouts']} | {s['exceptions']} | "
            f"{s['busts']} | `{json.dumps(s['bust_streets'], sort_keys=True)}` |"
        )
    lines.append("")
    lines.append("## Per-seat rows")
    lines.append("")
    lines.append("| mix | seat | seed | hands | delta | final stack | pressure folds | pressure loss chips | pressure loss bb/100 | decisions | fold-defaults | illegal names | timeouts | exceptions | busted | bust street |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for r in rows:
        lines.append(
            f"| {r['mix']} | {r['thorp_seat']} | {r['seed']} | {r['hands_played']} | "
            f"{r['thorp_delta']} | {r['thorp_final_stack']} | {r['pressure_fold_count']} | "
            f"{r['pressure_fold_loss_chips']} | {r['pressure_fold_loss_bb100']} | {r['decisions']} | {r['fold_defaults']} | "
            f"{r['illegal_action_names']} | {r['timeouts']} | {r['exceptions']} | {r['busted']} | {r['bust_street']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run finals-day 6-max evidence for submissions/v_final.zip")
    p.add_argument("--hands", type=int, default=800)
    p.add_argument("--seed-base", type=int, default=42)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--mix", choices=sorted(MIX_CHOICES), action="append", help="Limit to a mix; repeatable")
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

    selected_mixes = args.mix or list(table_mixes().keys())
    selected_seats = args.seat or list(range(6))
    synthetic_needed = sorted({SYNTHETIC_MIX_STYLES[mix] for mix in selected_mixes if mix in SYNTHETIC_MIX_STYLES})
    synthetic_paths: Dict[str, Path] = {}
    if synthetic_needed:
        synthetic_paths = synthetic_opponents.write_opponents(args.out_dir / "synthetic_opponents" / "src", synthetic_needed)
    mixes = table_mixes(synthetic_paths)

    started = time.time()
    rows: List[Dict[str, Any]] = []
    pressure_bleed_rows: List[Dict[str, Any]] = []
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
                pressure_bleed_rows.extend(row.pop("_pressure_bleed_hands", []))
                rows.append(row)
                print(
                    f"[quick_6max_eval] done mix={mix_name} seat={seat}: "
                    f"delta={row['thorp_delta']} pressure_folds={row['pressure_fold_count']} "
                    f"pressure_loss={row['pressure_fold_loss_chips']} decisions={row['decisions']} "
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
        "pressure_bleed_hands": pressure_bleed_rows,
    }
    (args.out_dir / "summary.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(args.out_dir / "per_match.csv", rows, [
        "mix", "thorp_seat", "seed", "hands_played", "duration_s", "thorp_delta", "thorp_final_stack",
        "pressure_fold_count", "pressure_fold_loss_chips", "pressure_fold_net_delta_chips", "pressure_fold_loss_bb100",
        "pressure_pot_after_surrendered_chips", "pressure_pot_after_surrendered_bb100",
        "decisions", "fold_defaults", "illegal_action_names", "timeouts", "exceptions", "busted", "bust_hand", "bust_street",
    ])
    write_csv(args.out_dir / "per_mix.csv", summaries, [
        "mix", "matches", "hands_total", "thorp_delta_sum", "thorp_delta_avg_per_match", "thorp_chip_per_100_hands", "thorp_bb100", "thorp_bb100_ci",
        "pressure_fold_count", "pressure_fold_loss_chips", "pressure_fold_net_delta_chips", "pressure_fold_loss_bb100",
        "pressure_pot_after_surrendered_chips", "pressure_pot_after_surrendered_bb100",
        "thorp_decisions", "fold_defaults", "illegal_action_names", "timeouts", "exceptions", "busts", "bust_rate", "bust_streets",
    ])
    write_pressure_bleed_csv(args.out_dir / "pressure_bleed_hands.csv", pressure_bleed_rows)
    write_markdown(args.out_dir / "REPORT.md", sha, rows, summaries, args.hands, args.seed_base)

    print(f"[quick_6max_eval] wrote {args.out_dir / 'REPORT.md'}")
    print(json.dumps({"duration_s": elapsed, "summaries": summaries}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
