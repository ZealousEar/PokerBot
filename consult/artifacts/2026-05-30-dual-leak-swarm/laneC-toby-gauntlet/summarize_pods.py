#!/usr/bin/env python3
"""Write paired Lane C pod summary from incremental matches.jsonl files.

This is artifact-local glue: it does not import or modify the hero strategy.
It pairs locked vs candidate by composition and seed, then writes the two
requested outputs:
- pod_summary.json
- POD_RESULTS.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/Users/farhad/Code/PokerBot")
LANE_DIR = ROOT / "consult" / "artifacts" / "2026-05-30-dual-leak-swarm" / "laneC-toby-gauntlet"
LOCKED_MATCHES = LANE_DIR / "pods_locked" / "matches.jsonl"
CANDIDATE_MATCHES = LANE_DIR / "pods_candidate" / "matches.jsonl"
EXPECTED_PROTECTED_SHA = "e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598"
CANDIDATE_ZIP = (
    ROOT
    / "consult"
    / "artifacts"
    / "2026-05-30-dual-leak-swarm"
    / "laneA-postflop-v2"
    / "zips"
    / "v_postflop_trap_v2_p2_already_clean.zip"
)
DEFAULT_COMPOSITIONS = [
    "C3_TOBY_MEHEDI_WEAK_FIELD",
    "C1_SINGLE_TOBY_WEAK_FIELD",
    "C0_BASELINE_RECHECK",
    "C4_PUBLIC_NIGHTMARE",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
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


def r(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def fmt(value: float | int | None, digits: int = 0) -> str:
    if value is None:
        return "n/a"
    if digits == 0:
        return str(int(round(float(value))))
    return f"{float(value):.{digits}f}"


def stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "sum": None,
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
        "count": len(values),
        "sum": int(sum(values)),
        "p10": r(percentile(values, 10)),
        "p25": r(percentile(values, 25)),
        "p50": r(percentile(values, 50)),
        "p75": r(percentile(values, 75)),
        "p90": r(percentile(values, 90)),
        "mean": r(statistics.mean(values)),
        "stdev": r(statistics.stdev(values) if len(values) > 1 else 0.0),
        "min": int(min(values)),
        "max": int(max(values)),
    }


def load_matches(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    out: dict[tuple[str, int], dict[str, Any]] = {}
    if not path.exists():
        return out
    with path.open() as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            key = (record["composition"], int(record["seed"]))
            out[key] = record
    return out


def side_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    deltas = [float(x["hero_chip_delta"]) for x in records]
    decisions = sum(int(x.get("hero_decisions") or 0) for x in records)
    action_errors = sum(int(x.get("hero_action_errors") or 0) for x in records)
    bot_errors = sum(int(x.get("hero_bot_errors") or 0) for x in records)
    opponent_decisions = sum(int(x.get("opponent_decisions") or 0) for x in records)
    opponent_action_errors = sum(int(x.get("opponent_action_errors") or 0) for x in records)
    p99s = [float(x["hero_p99_decide_latency_ms"]) for x in records if x.get("hero_p99_decide_latency_ms") is not None]
    actual_hands = [int(x.get("actual_hands") or 0) for x in records]
    return {
        "chip_delta": stats(deltas),
        "busts": sum(1 for x in records if x.get("hero_busted")),
        "bust_rate": r((sum(1 for x in records if x.get("hero_busted")) / len(records)) if records else None, 4),
        "actual_hands": stats([float(x) for x in actual_hands]),
        "hero_decisions": decisions,
        "hero_action_errors": action_errors,
        "hero_action_error_rate": r((action_errors / decisions) if decisions else None, 6),
        "hero_bot_errors": bot_errors,
        "opponent_decisions": opponent_decisions,
        "opponent_action_errors": opponent_action_errors,
        "opponent_action_error_rate": r((opponent_action_errors / opponent_decisions) if opponent_decisions else None, 6),
        "hero_p99_decide_latency_ms": r(percentile(p99s, 99), 3),
    }


def summarize(compositions: list[str], seed_base: int, seeds: int) -> dict[str, Any]:
    locked = load_matches(LOCKED_MATCHES)
    candidate = load_matches(CANDIDATE_MATCHES)
    seed_list = list(range(seed_base, seed_base + seeds))
    protected = {
        "submissions/v_final.zip": sha256_file(ROOT / "submissions" / "v_final.zip"),
        "submissions/best_green.zip": sha256_file(ROOT / "submissions" / "best_green.zip"),
    }
    candidate_sha = sha256_file(CANDIDATE_ZIP) if CANDIDATE_ZIP.exists() else None

    comp_out: dict[str, Any] = {}
    total_paired_delta = 0
    completed_comps = 0
    all_bust_no_worse = True
    any_bust_worse = False
    toby_comp_delta = 0

    for comp in compositions:
        locked_available = [seed for seed in seed_list if (comp, seed) in locked]
        candidate_available = [seed for seed in seed_list if (comp, seed) in candidate]
        paired_seeds = [seed for seed in seed_list if (comp, seed) in locked and (comp, seed) in candidate]
        locked_records = [locked[(comp, seed)] for seed in paired_seeds]
        candidate_records = [candidate[(comp, seed)] for seed in paired_seeds]
        paired_diffs = [
            float(candidate[(comp, seed)]["hero_chip_delta"] - locked[(comp, seed)]["hero_chip_delta"])
            for seed in paired_seeds
        ]
        locked_side = side_summary(locked_records)
        candidate_side = side_summary(candidate_records)
        paired_total = int(sum(paired_diffs)) if paired_diffs else None
        paired_mean = r(statistics.mean(paired_diffs), 2) if paired_diffs else None
        complete = len(paired_seeds) == len(seed_list)
        if paired_diffs:
            total_paired_delta += int(sum(paired_diffs))
        if complete:
            completed_comps += 1
            lb = locked_side["bust_rate"] or 0.0
            cb = candidate_side["bust_rate"] or 0.0
            if cb > lb:
                all_bust_no_worse = False
                any_bust_worse = True
            if "TOBY" in comp:
                toby_comp_delta += int(sum(paired_diffs))

        comp_out[comp] = {
            "complete": complete,
            "scheduled_seeds": seed_list,
            "locked_available_seeds": locked_available,
            "candidate_available_seeds": candidate_available,
            "paired_seeds": paired_seeds,
            "paired_count": len(paired_seeds),
            "paired_candidate_minus_locked_total_chip_delta": paired_total,
            "paired_candidate_minus_locked_mean_chip_delta": paired_mean,
            "paired_candidate_minus_locked_distribution": stats(paired_diffs),
            "locked": locked_side,
            "candidate": candidate_side,
        }

    protected_ok = all(sha == EXPECTED_PROTECTED_SHA for sha in protected.values())
    all_complete = completed_comps == len(compositions)
    if not all_complete:
        verdict = "INCOMPLETE"
    elif not protected_ok:
        verdict = "ABORT_PROTECTED_SHA_MISMATCH"
    elif any_bust_worse:
        verdict = "SHIP_LOCKED"
    elif total_paired_delta > 0 and toby_comp_delta > 0 and all_bust_no_worse:
        verdict = "TOBY_ONLY_PROMOTABLE_REQUIRES_HUMAN_GATE"
    else:
        verdict = "SHIP_LOCKED"

    return {
        "generated_at": now_utc(),
        "scope": {
            "hands_per_match": 400,
            "seed_base": seed_base,
            "seed_count": seeds,
            "compositions": compositions,
            "candidate_zip": rel(CANDIDATE_ZIP),
            "baseline_zip": "submissions/v_final.zip",
        },
        "protected_sha": protected,
        "expected_protected_sha": EXPECTED_PROTECTED_SHA,
        "protected_sha_ok": protected_ok,
        "candidate_sha256": candidate_sha,
        "totals": {
            "completed_compositions": completed_comps,
            "requested_compositions": len(compositions),
            "all_complete": all_complete,
            "paired_candidate_minus_locked_total_chip_delta_completed": total_paired_delta,
            "toby_containing_paired_delta_completed": toby_comp_delta,
            "candidate_bust_rate_no_worse_all_complete_comps": all_bust_no_worse,
        },
        "verdict": verdict,
        "verdict_note": "Human promotion gate required; locked v_final.zip remains upload target unless explicitly overridden.",
        "compositions": comp_out,
    }


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Lane C Toby-Only Six-Max Pod Results",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Verdict: **{summary['verdict']}**",
        "",
        summary["verdict_note"],
        "",
        "## Artifact integrity",
        "",
        f"- Baseline: `submissions/v_final.zip` sha `{summary['protected_sha']['submissions/v_final.zip']}`",
        f"- Best green: `submissions/best_green.zip` sha `{summary['protected_sha']['submissions/best_green.zip']}`",
        f"- Protected SHA OK: `{summary['protected_sha_ok']}`",
        f"- Candidate: `{summary['scope']['candidate_zip']}` sha `{summary['candidate_sha256']}`",
        "",
        "## Paired composition table",
        "",
        "| composition | paired seeds | paired Δ total | paired Δ mean | diff p10 | diff p50 | diff p90 | locked bust | cand bust | locked p50 | cand p50 | locked mean | cand mean | locked p99 ms | cand p99 ms | hero errors locked | hero errors cand |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for comp in summary["scope"]["compositions"]:
        data = summary["compositions"][comp]
        diff = data["paired_candidate_minus_locked_distribution"]
        locked = data["locked"]
        cand = data["candidate"]
        lines.append(
            f"| {comp} | {data['paired_count']} | {fmt(data['paired_candidate_minus_locked_total_chip_delta'])} | "
            f"{fmt(data['paired_candidate_minus_locked_mean_chip_delta'], 1)} | {fmt(diff['p10'])} | {fmt(diff['p50'])} | {fmt(diff['p90'])} | "
            f"{fmt((locked['bust_rate'] or 0) * 100, 1)}% | {fmt((cand['bust_rate'] or 0) * 100, 1)}% | "
            f"{fmt(locked['chip_delta']['p50'])} | {fmt(cand['chip_delta']['p50'])} | "
            f"{fmt(locked['chip_delta']['mean'])} | {fmt(cand['chip_delta']['mean'])} | "
            f"{fmt(locked['hero_p99_decide_latency_ms'], 3)} | {fmt(cand['hero_p99_decide_latency_ms'], 3)} | "
            f"{locked['hero_action_errors']} / {locked['hero_decisions']} | {cand['hero_action_errors']} / {cand['hero_decisions']} |"
        )
    lines += [
        "",
        "## Completion detail",
        "",
    ]
    for comp in summary["scope"]["compositions"]:
        data = summary["compositions"][comp]
        missing_locked = sorted(set(data["scheduled_seeds"]) - set(data["locked_available_seeds"]))
        missing_candidate = sorted(set(data["scheduled_seeds"]) - set(data["candidate_available_seeds"]))
        lines.append(
            f"- `{comp}`: complete `{data['complete']}`; paired `{data['paired_count']}`; "
            f"missing locked `{missing_locked}`; missing candidate `{missing_candidate}`."
        )
    lines += [
        "",
        "## Decider frame",
        "",
        "Default is `SHIP_LOCKED`. `TOBY_ONLY_PROMOTABLE` requires clearly positive or solidly neutral paired pod chip-delta with a real Toby-pod gain and no worse candidate bust rate.",
        "",
        "Human promotion gate required; locked v_final.zip remains upload target unless explicitly overridden.",
        "",
    ]
    path.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed-base", type=int, default=142)
    p.add_argument("--seeds", type=int, default=40)
    p.add_argument("--compositions", nargs="+", default=DEFAULT_COMPOSITIONS)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    summary = summarize(args.compositions, args.seed_base, args.seeds)
    (LANE_DIR / "pod_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_markdown(summary, LANE_DIR / "POD_RESULTS.md")
    print(f"wrote {LANE_DIR / 'pod_summary.json'}")
    print(f"wrote {LANE_DIR / 'POD_RESULTS.md'}")
    print(f"verdict={summary['verdict']}")
    for comp, data in summary["compositions"].items():
        print(
            comp,
            "paired", data["paired_count"],
            "delta", data["paired_candidate_minus_locked_total_chip_delta"],
            "bust", data["candidate"]["bust_rate"], "vs", data["locked"]["bust_rate"],
        )
    return 0 if summary["protected_sha_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
