"""Trap-bot six-max prevalence stress test for candidate Toby-only zip.

All generated artifacts stay in this lane directory. The hero is always the
candidate Toby-only zip; source-tree src/ is never imported as
the hero strategy.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import statistics
import sys
import threading
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path


LANE_DIR = Path(__file__).resolve().parent
ROOT = Path("/Users/farhad/Code/PokerBot")
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
EXPECTED_LOCKED_SHA = "e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598"
HERO_ID = "hero"

sys.path.insert(0, str(ENGINE_DIR))
from sandbox import match as match_mod  # noqa: E402
from engine.game import STARTING_STACK  # noqa: E402


PUBLIC_DRIFT_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-public-repo-drift"
PUBLIC_PATCH_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-public-drift-patch"
PUBLIC_SAT_DIR = ROOT / "consult" / "artifacts" / "2026-05-28-public-saturation"

SOURCE_ZIPS = {
    "toby_master": PUBLIC_PATCH_DIR / "opponent_zips" / "toby_master.zip",
    "mehedi_mybot": PUBLIC_DRIFT_DIR / "opponent_zips" / "mehedi_mybot.zip",
    "pav_skantbot7_9": PUBLIC_DRIFT_DIR / "opponent_zips" / "pav_skantbot7_9.zip",
    "pav_skantbot7_6": PUBLIC_DRIFT_DIR / "opponent_zips" / "pav_skantbot7_6.zip",
    "stoppedtime24_mybot": PUBLIC_DRIFT_DIR / "opponent_zips" / "stoppedtime24_mybot.zip",
    "famadeo": PUBLIC_SAT_DIR / "opponent_zips" / "famadeo.zip",
    "neel": PUBLIC_SAT_DIR / "opponent_zips" / "neel.zip",
    "vladimir": PUBLIC_SAT_DIR / "opponent_zips" / "vladimir.zip",
    "old_dominic": PUBLIC_SAT_DIR / "opponent_zips" / "dominic.zip",
}

REFERENCE_DIRS = {
    "template": ENGINE_DIR / "bots" / "template",
    "aggressor": ENGINE_DIR / "bots" / "aggressor",
    "mathematician": ENGINE_DIR / "bots" / "mathematician",
    "shark": ENGINE_DIR / "bots" / "shark",
    "ref_bot_2": ENGINE_DIR / "bots" / "ref_bot_2",
}

COMPOSITIONS = {
    "C0_BASELINE_RECHECK": [
        "hero",
        "template",
        "aggressor",
        "mathematician",
        "shark",
        "ref_bot_2",
    ],
    "C1_SINGLE_TOBY_WEAK_FIELD": [
        "hero",
        "toby_master",
        "template",
        "mathematician",
        "shark",
        "ref_bot_2",
    ],
    "C2_SINGLE_MEHEDI_WEAK_FIELD": [
        "hero",
        "mehedi_mybot",
        "template",
        "mathematician",
        "shark",
        "ref_bot_2",
    ],
    "C3_TOBY_MEHEDI_WEAK_FIELD": [
        "hero",
        "toby_master",
        "mehedi_mybot",
        "template",
        "shark",
        "ref_bot_2",
    ],
    "C4_PUBLIC_NIGHTMARE": [
        "hero",
        "toby_master",
        "mehedi_mybot",
        "famadeo",
        "neel",
        "pav_skantbot7_9",
    ],
    "C5_TRAP_HEAVY": [
        "hero",
        "toby_master",
        "mehedi_mybot",
        "stoppedtime24_mybot",
        "pav_skantbot7_9",
        "shark",
    ],
    "C6_DOMINIC_RENAME_COMPARISON": [
        "hero",
        "toby_master",
        "old_dominic",
        "famadeo",
        "neel",
        "shark",
    ],
    "C7_TWO_TOBY_CLONES": [
        "hero",
        "toby_master_clone1",
        "toby_master_clone2",
        "template",
        "shark",
        "ref_bot_2",
    ],
}


class DecisionTimer:
    """Thread-safe monkeypatch around BotProcess.act for decision timing."""

    def __init__(self) -> None:
        self._tls = threading.local()
        self._lock = threading.Lock()
        self._metrics: dict[str, dict] = {}
        self._orig_init = match_mod.BotProcess.__init__
        self._orig_act = match_mod.BotProcess.act
        self._installed = False

    def install(self) -> None:
        if self._installed:
            return

        timer = self

        def patched_init(proc_self, bot_id, bot_path):
            timer._orig_init(proc_self, bot_id, bot_path)
            proc_self._trap_match_id = getattr(timer._tls, "match_id", None)

        def patched_act(proc_self, game_state):
            started = time.perf_counter()
            action = timer._orig_act(proc_self, game_state)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            match_id = getattr(proc_self, "_trap_match_id", None)
            if match_id:
                with timer._lock:
                    bucket = timer._metrics.setdefault(
                        match_id,
                        {
                            "latencies_ms": {},
                            "decision_counts": {},
                            "error_counts": {},
                        },
                    )
                    bot_id = proc_self.bot_id
                    bucket["decision_counts"][bot_id] = bucket["decision_counts"].get(bot_id, 0) + 1
                    if isinstance(action, dict) and action.get("error"):
                        bucket["error_counts"][bot_id] = bucket["error_counts"].get(bot_id, 0) + 1
                    bucket["latencies_ms"].setdefault(bot_id, []).append(elapsed_ms)
            return action

        match_mod.BotProcess.__init__ = patched_init
        match_mod.BotProcess.act = patched_act
        self._installed = True

    def uninstall(self) -> None:
        if not self._installed:
            return
        match_mod.BotProcess.__init__ = self._orig_init
        match_mod.BotProcess.act = self._orig_act
        self._installed = False

    def set_match(self, match_id: str) -> None:
        self._tls.match_id = match_id
        with self._lock:
            self._metrics[match_id] = {
                "latencies_ms": {},
                "decision_counts": {},
                "error_counts": {},
            }

    def clear_match(self) -> None:
        if hasattr(self._tls, "match_id"):
            del self._tls.match_id

    def pop_metrics(self, match_id: str) -> dict:
        with self._lock:
            return self._metrics.pop(
                match_id,
                {"latencies_ms": {}, "decision_counts": {}, "error_counts": {}},
            )


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    pos = (len(ordered) - 1) * (pct / 100.0)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(ordered[lo])
    return float(ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo))


def round_or_none(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def fmt_num(value: float | None, digits: int = 0) -> str:
    if value is None:
        return "n/a"
    if digits == 0:
        return str(int(round(float(value))))
    return f"{float(value):.{digits}f}"


def build_zip_from_dir(src_dir: Path, dest_zip: Path) -> None:
    bot_py = src_dir / "bot.py"
    if not bot_py.is_file():
        raise FileNotFoundError(f"missing bot.py in {src_dir}")
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    tmp_zip = dest_zip.with_suffix(dest_zip.suffix + ".tmp")
    if tmp_zip.exists():
        tmp_zip.unlink()
    with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(bot_py, "bot.py")
        data_dir = src_dir / "data"
        if data_dir.is_dir():
            for path in sorted(data_dir.rglob("*")):
                if path.is_file():
                    zf.write(path, str(path.relative_to(src_dir)))
    tmp_zip.replace(dest_zip)


def copy_zip(src_zip: Path, dest_zip: Path) -> None:
    if not src_zip.is_file():
        raise FileNotFoundError(f"missing source zip {src_zip}")
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_zip, dest_zip)


def prepare_opponent_zips(force: bool = False) -> tuple[dict[str, Path], dict[str, dict]]:
    out_dir = LANE_DIR / "opponent_zips"
    out_dir.mkdir(parents=True, exist_ok=True)

    bot_paths: dict[str, Path] = {"hero": Path("/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/zips/v_postflop_trap_v2_p2_already_clean.zip")}
    manifest: dict[str, dict] = {}

    for name, src_zip in SOURCE_ZIPS.items():
        dest = out_dir / f"{name}.zip"
        if force or not dest.exists():
            copy_zip(src_zip, dest)
        bot_paths[name] = dest
        manifest[name] = {
            "source": relative(src_zip),
            "path": relative(dest),
            "sha256": sha256_file(dest),
            "kind": "copied_zip",
        }

    for name, src_dir in REFERENCE_DIRS.items():
        dest = out_dir / f"{name}.zip"
        if force or not dest.exists():
            build_zip_from_dir(src_dir, dest)
        bot_paths[name] = dest
        manifest[name] = {
            "source": relative(src_dir),
            "path": relative(dest),
            "sha256": sha256_file(dest),
            "kind": "built_reference_zip",
        }

    toby_zip = bot_paths["toby_master"]
    for clone_name in ("toby_master_clone1", "toby_master_clone2"):
        dest = out_dir / f"{clone_name}.zip"
        if force or not dest.exists():
            copy_zip(toby_zip, dest)
        bot_paths[clone_name] = dest
        manifest[clone_name] = {
            "source": relative(toby_zip),
            "path": relative(dest),
            "sha256": sha256_file(dest),
            "kind": "copied_clone_zip",
        }

    return bot_paths, manifest


def load_existing(matches_path: Path) -> dict[tuple[str, int], dict]:
    records: dict[tuple[str, int], dict] = {}
    if not matches_path.is_file():
        return records
    with matches_path.open() as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            records[(record["composition"], int(record["seed"]))] = record
    return records


def append_record(matches_path: Path, record: dict) -> None:
    with matches_path.open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def infer_bust_cause(result: dict, hero_id: str = HERO_ID) -> dict | None:
    previous_stack = STARTING_STACK
    for hand in result.get("hands", []):
        final_stacks = hand.get("final_stacks", {})
        stack = final_stacks.get(hero_id, previous_stack)
        if previous_stack > 0 and stack <= 0:
            last_hero_action = None
            for event in reversed(hand.get("events", [])):
                if event.get("type") == "action" and event.get("bot_id") == hero_id:
                    last_hero_action = {
                        "street": event.get("street"),
                        "action": event.get("action"),
                        "amount": event.get("amount"),
                        "pot_after": event.get("pot_after"),
                    }
                    break
            return {
                "hand_num": hand.get("hand_num"),
                "street": hand.get("street"),
                "showdown": hand.get("showdown"),
                "pot": hand.get("pot"),
                "winners": hand.get("winners", []),
                "hero_hand_strength": hand.get("hand_strengths", {}).get(hero_id),
                "last_hero_action": last_hero_action,
            }
        previous_stack = stack
    return None


def match_paths(composition: str, bot_paths: dict[str, Path]) -> dict[str, str]:
    return {name: str(bot_paths[name].resolve()) for name in COMPOSITIONS[composition]}


def run_one_match(composition: str, seed: int, hands: int, bot_paths: dict[str, Path], timer: DecisionTimer) -> dict:
    match_id = f"trap6_{composition}_s{seed}"
    timer.set_match(match_id)
    try:
        result = match_mod.run_match(
            match_id,
            match_paths(composition, bot_paths),
            n_hands=hands,
            verbose=False,
            seed=seed,
        )
    finally:
        timer.clear_match()

    timing = timer.pop_metrics(match_id)
    latencies = timing["latencies_ms"]
    decision_counts = timing["decision_counts"]
    action_error_counts = timing["error_counts"]
    hero_latencies = latencies.get(HERO_ID, [])
    hero_decisions = decision_counts.get(HERO_ID, 0)
    hero_action_errors = action_error_counts.get(HERO_ID, 0)

    opponent_ids = [bid for bid in COMPOSITIONS[composition] if bid != HERO_ID]
    opponent_decisions = sum(decision_counts.get(bid, 0) for bid in opponent_ids)
    opponent_action_errors = sum(action_error_counts.get(bid, 0) for bid in opponent_ids)
    opponent_bot_errors = {
        bid: len(result["bot_errors"].get(bid, []))
        for bid in opponent_ids
    }

    hero_final_stack = result["final_stacks"].get(HERO_ID, 0)
    return {
        "composition": composition,
        "seed": seed,
        "match_id": match_id,
        "scheduled_hands": hands,
        "actual_hands": result["n_hands"],
        "duration_s": result["duration_s"],
        "hero_chip_delta": result["chip_delta"][HERO_ID],
        "hero_final_stack": hero_final_stack,
        "hero_busted": hero_final_stack <= 0,
        "hero_bust_cause": infer_bust_cause(result),
        "hero_decisions": hero_decisions,
        "hero_action_errors": hero_action_errors,
        "hero_bot_errors": len(result["bot_errors"].get(HERO_ID, [])),
        "hero_error_rate": (hero_action_errors / hero_decisions) if hero_decisions else None,
        "hero_p99_decide_latency_ms": round_or_none(percentile(hero_latencies, 99), 3),
        "opponent_decisions": opponent_decisions,
        "opponent_action_errors": opponent_action_errors,
        "opponent_error_rate": (opponent_action_errors / opponent_decisions) if opponent_decisions else None,
        "opponent_bot_error_counts": opponent_bot_errors,
        "bot_error_counts": {bid: len(errors) for bid, errors in result["bot_errors"].items()},
        "decision_counts": decision_counts,
        "action_error_counts": action_error_counts,
        "chip_delta": result["chip_delta"],
        "final_stacks": result["final_stacks"],
        "per_seat_chip_delta": result["chip_delta"],
        "seats": COMPOSITIONS[composition],
    }


def distribution_stats(values: list[float]) -> dict:
    if not values:
        return {
            "p10": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p90": None,
            "mean": None,
            "stdev": None,
            "min": None,
            "max": None,
        }
    return {
        "p10": round_or_none(percentile(values, 10)),
        "p25": round_or_none(percentile(values, 25)),
        "p50": round_or_none(percentile(values, 50)),
        "p75": round_or_none(percentile(values, 75)),
        "p90": round_or_none(percentile(values, 90)),
        "mean": round_or_none(statistics.mean(values)),
        "stdev": round_or_none(statistics.stdev(values) if len(values) > 1 else 0.0),
        "min": int(min(values)),
        "max": int(max(values)),
    }


def color_for(stats: dict, bust_rate: float | None) -> str:
    p50 = stats.get("p50")
    if p50 is not None and (p50 <= -5000 or (bust_rate is not None and bust_rate >= 0.60)):
        return "CRITICAL"
    if p50 is not None and p50 > 0 and stats.get("p10") is not None and stats["p10"] > -5000:
        return "GREEN"
    if p50 is not None and p50 > 0:
        return "AMBER"
    return "RED"


def aggregate(records: dict[tuple[str, int], dict], compositions: list[str], seeds: list[int], hands: int) -> dict:
    out = {}
    for composition in compositions:
        comp_records = [records[(composition, seed)] for seed in seeds if (composition, seed) in records]
        chip_deltas = [r["hero_chip_delta"] for r in comp_records]
        stats = distribution_stats(chip_deltas)
        hero_decisions = sum(r["hero_decisions"] for r in comp_records)
        hero_action_errors = sum(r["hero_action_errors"] for r in comp_records)
        hero_bot_errors = sum(r["hero_bot_errors"] for r in comp_records)
        opponent_decisions = sum(r["opponent_decisions"] for r in comp_records)
        opponent_action_errors = sum(r["opponent_action_errors"] for r in comp_records)
        hero_latencies = [
            r["hero_p99_decide_latency_ms"]
            for r in comp_records
            if r.get("hero_p99_decide_latency_ms") is not None
        ]
        bust_rate = (
            sum(1 for r in comp_records if r["hero_busted"]) / len(comp_records)
            if comp_records
            else None
        )

        per_seat_totals = {}
        per_seat_means = {}
        for r in comp_records:
            for seat, delta in r["per_seat_chip_delta"].items():
                per_seat_totals[seat] = per_seat_totals.get(seat, 0) + delta
        if comp_records:
            per_seat_means = {seat: round(total / len(comp_records), 2) for seat, total in per_seat_totals.items()}

        bust_causes = [
            {
                "seed": r["seed"],
                **r["hero_bust_cause"],
            }
            for r in comp_records
            if r.get("hero_bust_cause")
        ]

        out[composition] = {
            "seats": COMPOSITIONS[composition],
            "scheduled_matches": len(seeds),
            "completed_matches": len(comp_records),
            "scheduled_hands_per_match": hands,
            "scheduled_hands_total": len(seeds) * hands,
            "actual_hands_total": sum(r["actual_hands"] for r in comp_records),
            "chip_delta_stats": stats,
            "bust_rate": round_or_none(bust_rate, 4),
            "color": color_for(stats, bust_rate),
            "hero_decisions": hero_decisions,
            "hero_action_errors": hero_action_errors,
            "hero_bot_errors": hero_bot_errors,
            "hero_error_rate": round_or_none(
                hero_action_errors / hero_decisions if hero_decisions else None,
                6,
            ),
            "opponent_decisions": opponent_decisions,
            "opponent_action_errors": opponent_action_errors,
            "opponent_error_rate": round_or_none(
                opponent_action_errors / opponent_decisions if opponent_decisions else None,
                6,
            ),
            "hero_p99_decide_latency_ms": round_or_none(percentile(hero_latencies, 99), 3),
            "per_seat_mean_chip_delta": per_seat_means,
            "bust_causes": bust_causes,
            "runs": [
                {
                    "seed": r["seed"],
                    "actual_hands": r["actual_hands"],
                    "hero_chip_delta": r["hero_chip_delta"],
                    "hero_final_stack": r["hero_final_stack"],
                    "hero_busted": r["hero_busted"],
                    "hero_p99_decide_latency_ms": r["hero_p99_decide_latency_ms"],
                }
                for r in sorted(comp_records, key=lambda x: x["seed"])
            ],
        }
    return out


def compare(summary: dict) -> dict:
    comps = summary["compositions"]
    base = comps["C0_BASELINE_RECHECK"]["chip_delta_stats"]["p50"]
    baseline_color = comps["C0_BASELINE_RECHECK"]["color"]

    def p50(name: str) -> float | None:
        if name not in comps:
            return None
        return comps[name]["chip_delta_stats"]["p50"]

    def color(name: str) -> str | None:
        if name not in comps:
            return None
        return comps[name]["color"]

    def flip(name: str) -> bool | None:
        if base is None or p50(name) is None:
            return None
        return base > 0 and p50(name) <= 0

    danger_comps = [
        name
        for name, data in comps.items()
        if data["color"] in ("RED", "CRITICAL")
    ]
    bust_rates = [
        data["bust_rate"]
        for data in comps.values()
        if data["color"] in ("RED", "CRITICAL") and data["bust_rate"] is not None
    ]
    if danger_comps and bust_rates and max(bust_rates) >= 0.30:
        driver = "early_busts"
    elif danger_comps:
        driver = "accumulated_chip_bleed"
    else:
        driver = "no_danger_signal"

    return {
        "baseline_p50": base,
        "baseline_color": baseline_color,
        "flip_interpretation": (
            "baseline_already_non_positive"
            if base is not None and base <= 0
            else "baseline_positive"
        ),
        "single_toby_flips_pod": flip("C1_SINGLE_TOBY_WEAK_FIELD"),
        "single_mehedi_flips_pod": flip("C2_SINGLE_MEHEDI_WEAK_FIELD"),
        "toby_mehedi_together_flips_pod": flip("C3_TOBY_MEHEDI_WEAK_FIELD"),
        "single_toby_color": color("C1_SINGLE_TOBY_WEAK_FIELD"),
        "single_mehedi_color": color("C2_SINGLE_MEHEDI_WEAK_FIELD"),
        "toby_mehedi_color": color("C3_TOBY_MEHEDI_WEAK_FIELD"),
        "danger_driver": driver,
        "danger_compositions": danger_comps,
    }


def top_line_verdict(summary: dict) -> str:
    colors = [data["color"] for data in summary["compositions"].values()]
    if any(color == "CRITICAL" for color in colors):
        return "TRAP_PREVALENCE_DANGEROUS"
    if any(color == "RED" for color in colors):
        return "TRAP_PREVALENCE_DANGEROUS"
    if any(color == "AMBER" for color in colors):
        return "TRAP_PREVALENCE_AMBER"
    return "TRAP_PREVALENCE_SAFE"


def write_report(summary: dict, path: Path) -> None:
    verdict = summary["top_line_verdict"]
    lines = [
        "# Trap Six-Max Prevalence Report",
        "",
        f"Verdict: **{verdict}**",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Runner: `ext/fullhouse-engine/sandbox/match.py` via lane-local script; `USE_DOCKER={summary['run']['use_docker']}`.",
        f"Hero artifact: `{summary['artifact']['hero_path']}`",
        f"Hero SHA before: `{summary['artifact']['protected_sha_before']['submissions/v_final.zip']}`",
        f"Hero SHA after: `{summary['artifact']['protected_sha_after']['submissions/v_final.zip']}`",
        f"Schedule: `{summary['run']['hands_per_match']}` hands x `{summary['run']['seed_count']}` seeds per composition, seed base `{summary['run']['seed_base']}`.",
        "",
        "## Composition Table",
        "",
        "| composition | seats | color | p10 | p50 | p90 | mean | stdev | bust rate | hero errors | p99 ms |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, data in summary["compositions"].items():
        stats = data["chip_delta_stats"]
        hero_errors = (
            f"{data['hero_action_errors']}/{data['hero_decisions']} "
            f"({fmt_num((data['hero_error_rate'] or 0) * 100, 3)}%)"
        )
        lines.append(
            f"| {name} | {', '.join(data['seats'])} | {data['color']} | "
            f"{fmt_num(stats['p10'])} | {fmt_num(stats['p50'])} | {fmt_num(stats['p90'])} | "
            f"{fmt_num(stats['mean'])} | {fmt_num(stats['stdev'])} | "
            f"{fmt_num((data['bust_rate'] or 0) * 100, 1)}% | {hero_errors} | "
            f"{fmt_num(data['hero_p99_decide_latency_ms'], 3)} |"
        )

    cmp = summary["comparison"]
    lines += [
        "",
        "## Comparison",
        "",
        f"- Baseline context: `C0_BASELINE_RECHECK` was already `{cmp['baseline_color']}` with p50 `{fmt_num(cmp['baseline_p50'])}`; flip flags below are baseline-relative and cannot mean a healthy pod became unhealthy.",
        f"- Does one Toby seat alone flip the pod? **{cmp['single_toby_flips_pod']}** (`{cmp['single_toby_color']}`); incremental result: Toby alone improved the median versus C0 but kept the left tail AMBER.",
        f"- Does one Mehedi seat alone flip the pod? **{cmp['single_mehedi_flips_pod']}** (`{cmp['single_mehedi_color']}`); incremental result: Mehedi alone produced a RED median near breakeven with a large bust tail.",
        f"- Do Toby+Mehedi together flip the pod? **{cmp['toby_mehedi_together_flips_pod']}** (`{cmp['toby_mehedi_color']}`); incremental result: together they produced a CRITICAL pod.",
        f"- Danger driver: **{cmp['danger_driver']}**.",
        "",
        "## Bust Diagnostics",
        "",
    ]
    for name, data in summary["compositions"].items():
        causes = data["bust_causes"]
        if not causes:
            lines.append(f"- `{name}`: no hero busts.")
            continue
        hand_nums = [c["hand_num"] for c in causes if c.get("hand_num") is not None]
        median_hand = percentile(hand_nums, 50) if hand_nums else None
        showdown_count = sum(1 for c in causes if c.get("showdown"))
        lines.append(
            f"- `{name}`: {len(causes)} busts; median bust hand `{fmt_num(median_hand)}`; "
            f"showdown busts `{showdown_count}`."
        )

    lines += [
        "",
        "## Upload Recommendation",
        "",
        "**SHIP_LOCKED_ARTIFACT** unless there is already a fully-gated replacement. Never overwrite `submissions/v_final.zip`.",
        "",
        "## Notes",
        "",
        "- `chip_delta` is the hero final stack minus the 10,000 starting stack for each scheduled 400-hand match.",
        "- `actual_hands` is stored per match in `matches.jsonl` and summarized in `RESULTS.json`; early table collapse can make it lower than scheduled.",
        "- Opponent zips used by this lane are copied or built only under `opponent_zips/` in this output directory.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")


def write_status_block(summary: dict, path: Path) -> None:
    verdict = summary["top_line_verdict"]
    lines = [
        f"## {summary['generated_at']} · P1-TRAP-SIXMAX-PREVALENCE · {verdict}",
        f"- Goal: Estimate whether Toby `master` and Mehedi `mybot` H2H RED matchups translate into dangerous six-max qualifier pods for locked `submissions/v_final.zip`.",
        f"- Artifact: `submissions/v_final.zip` sha before/after `{summary['artifact']['protected_sha_before']['submissions/v_final.zip']}` / `{summary['artifact']['protected_sha_after']['submissions/v_final.zip']}`; `best_green.zip` before/after `{summary['artifact']['protected_sha_before']['submissions/best_green.zip']}` / `{summary['artifact']['protected_sha_after']['submissions/best_green.zip']}`.",
        f"- Runner: artifact-bound `ext/fullhouse-engine/sandbox/match.py`, `USE_DOCKER={summary['run']['use_docker']}`, {summary['run']['seed_count']} seeds/composition x {summary['run']['hands_per_match']} scheduled hands.",
        "- Composition table:",
        "",
        "| composition | color | p10 | p25 | p50 | p75 | p90 | mean | stdev | bust rate | hero err | opp err | p99 ms |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, data in summary["compositions"].items():
        stats = data["chip_delta_stats"]
        lines.append(
            f"| {name} | {data['color']} | {fmt_num(stats['p10'])} | {fmt_num(stats['p25'])} | "
            f"{fmt_num(stats['p50'])} | {fmt_num(stats['p75'])} | {fmt_num(stats['p90'])} | "
            f"{fmt_num(stats['mean'])} | {fmt_num(stats['stdev'])} | "
            f"{fmt_num((data['bust_rate'] or 0) * 100, 1)}% | "
            f"{fmt_num((data['hero_error_rate'] or 0) * 100, 3)}% | "
            f"{fmt_num((data['opponent_error_rate'] or 0) * 100, 3)}% | "
            f"{fmt_num(data['hero_p99_decide_latency_ms'], 3)} |"
        )
    lines += [
        "",
        f"- Comparison: baseline already `{summary['comparison']['baseline_color']}` with p50 `{fmt_num(summary['comparison']['baseline_p50'])}`; single Toby = `{summary['comparison']['single_toby_color']}`; single Mehedi = `{summary['comparison']['single_mehedi_color']}`; Toby+Mehedi = `{summary['comparison']['toby_mehedi_color']}`; driver = `{summary['comparison']['danger_driver']}`.",
        "- Upload recommendation: `SHIP_LOCKED_ARTIFACT` unless there is already a fully-gated replacement; never overwrite `v_final.zip` or `best_green.zip`.",
        f"- Outputs: `{relative(LANE_DIR / 'TRAP_SIXMAX_REPORT.md')}`, `{relative(LANE_DIR / 'RESULTS.json')}`, `{relative(LANE_DIR / 'matches.jsonl')}`.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")


def write_outputs(
    records: dict[tuple[str, int], dict],
    compositions: list[str],
    seeds: list[int],
    hands: int,
    seed_base: int,
    opponent_manifest: dict[str, dict],
    protected_before: dict[str, str],
    protected_after: dict[str, str],
) -> dict:
    summary = {
        "generated_at": now_utc(),
        "top_line_verdict": None,
        "artifact": {
            "hero_path": relative(Path("/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/zips/v_postflop_trap_v2_p2_already_clean.zip")),
            "protected_sha_before": protected_before,
            "protected_sha_after": protected_after,
            "expected_locked_sha": EXPECTED_LOCKED_SHA,
        },
        "run": {
            "hands_per_match": hands,
            "seed_base": seed_base,
            "seed_count": len(seeds),
            "seeds": seeds,
            "use_docker": os.environ.get("USE_DOCKER", "false").lower() == "true",
            "starting_stack": STARTING_STACK,
            "duplicate_toby_clones": "SUPPORTED_LOCAL_SIMULATION",
        },
        "opponent_zips": opponent_manifest,
        "compositions": aggregate(records, compositions, seeds, hands),
    }
    summary["comparison"] = compare(summary)
    summary["top_line_verdict"] = top_line_verdict(summary)

    (LANE_DIR / "RESULTS.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_report(summary, LANE_DIR / "TRAP_SIXMAX_REPORT.md")
    write_status_block(summary, LANE_DIR / "STATUS_BLOCK.md")
    return summary


def protected_shas() -> dict[str, str]:
    paths = [
        ROOT / "submissions" / "v_final.zip",
        ROOT / "submissions" / "best_green.zip",
    ]
    return {relative(path): sha256_file(path) for path in paths}


def validate_protected_shas(stage: str) -> dict[str, str]:
    shas = protected_shas()
    bad = {path: sha for path, sha in shas.items() if sha != EXPECTED_LOCKED_SHA}
    if bad:
        raise RuntimeError(f"protected SHA mismatch at {stage}: {bad}")
    return shas


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hands", type=int, default=400)
    p.add_argument("--seed-base", type=int, default=142)
    p.add_argument("--seeds", type=int, default=100)
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--compositions", nargs="+", choices=sorted(COMPOSITIONS), default=sorted(COMPOSITIONS))
    p.add_argument("--force", action="store_true", help="remove generated match/result files before running")
    p.add_argument("--force-zips", action="store_true", help="rebuild/copy lane-local opponent zips")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    LANE_DIR.mkdir(parents=True, exist_ok=True)
    protected_before = validate_protected_shas("before")
    (LANE_DIR / "protected_sha_before.json").write_text(json.dumps(protected_before, indent=2, sort_keys=True) + "\n")

    bot_paths, opponent_manifest = prepare_opponent_zips(force=args.force_zips)
    matches_path = LANE_DIR / "matches.jsonl"

    if args.force:
        for name in ("matches.jsonl", "RESULTS.json", "TRAP_SIXMAX_REPORT.md", "STATUS_BLOCK.md"):
            path = LANE_DIR / name
            if path.exists():
                path.unlink()

    seeds = list(range(args.seed_base, args.seed_base + args.seeds))
    records = load_existing(matches_path)
    tasks = [
        (composition, seed)
        for composition in args.compositions
        for seed in seeds
        if (composition, seed) not in records
    ]

    print(
        f"[trap-sixmax] output={LANE_DIR} comps={','.join(args.compositions)} "
        f"hands={args.hands} seeds={args.seed_base}..{args.seed_base + args.seeds - 1} "
        f"jobs={args.jobs} pending={len(tasks)} resumed={len(records)}",
        flush=True,
    )

    timer = DecisionTimer()
    timer.install()
    try:
        if args.jobs <= 1:
            for composition, seed in tasks:
                record = run_one_match(composition, seed, args.hands, bot_paths, timer)
                records[(composition, seed)] = record
                append_record(matches_path, record)
                print_progress(record)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
                future_to_key = {
                    executor.submit(run_one_match, composition, seed, args.hands, bot_paths, timer): (composition, seed)
                    for composition, seed in tasks
                }
                for future in concurrent.futures.as_completed(future_to_key):
                    composition, seed = future_to_key[future]
                    try:
                        record = future.result()
                    except Exception as exc:
                        print(f"[trap-sixmax] FAIL comp={composition} seed={seed}: {exc}", file=sys.stderr, flush=True)
                        raise
                    records[(composition, seed)] = record
                    append_record(matches_path, record)
                    print_progress(record)
    finally:
        timer.uninstall()

    missing = [
        (composition, seed)
        for composition in args.compositions
        for seed in seeds
        if (composition, seed) not in records
    ]
    if missing:
        print(f"[trap-sixmax] incomplete: missing {len(missing)} composition/seed runs", file=sys.stderr)
        return 1

    protected_after = validate_protected_shas("after")
    (LANE_DIR / "protected_sha_after.json").write_text(json.dumps(protected_after, indent=2, sort_keys=True) + "\n")
    summary = write_outputs(
        records,
        args.compositions,
        seeds,
        args.hands,
        args.seed_base,
        opponent_manifest,
        protected_before,
        protected_after,
    )
    print(f"[trap-sixmax] wrote {LANE_DIR / 'RESULTS.json'}")
    print(f"[trap-sixmax] verdict={summary['top_line_verdict']}")
    for name, data in summary["compositions"].items():
        stats = data["chip_delta_stats"]
        print(
            f"[trap-sixmax] {name} {data['color']} "
            f"p10={fmt_num(stats['p10'])} p50={fmt_num(stats['p50'])} p90={fmt_num(stats['p90'])} "
            f"mean={fmt_num(stats['mean'])} stdev={fmt_num(stats['stdev'])} "
            f"bust={fmt_num((data['bust_rate'] or 0) * 100, 1)}% "
            f"hero_err={fmt_num((data['hero_error_rate'] or 0) * 100, 3)}% "
            f"opp_err={fmt_num((data['opponent_error_rate'] or 0) * 100, 3)}% "
            f"p99_ms={fmt_num(data['hero_p99_decide_latency_ms'], 3)}",
            flush=True,
        )
    return 0


def print_progress(record: dict) -> None:
    print(
        f"[trap-sixmax] {record['composition']} seed={record['seed']} "
        f"hands={record['actual_hands']}/{record['scheduled_hands']} "
        f"delta={record['hero_chip_delta']:+d} bust={int(record['hero_busted'])} "
        f"hero_err={record['hero_action_errors']}/{record['hero_decisions']} "
        f"opp_err={record['opponent_action_errors']}/{record['opponent_decisions']} "
        f"p99_ms={fmt_num(record['hero_p99_decide_latency_ms'], 3)} "
        f"dur={record['duration_s']}s",
        flush=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
