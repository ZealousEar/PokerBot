#!/usr/bin/env python3
"""Lane B paired H2H evaluator: locked baseline vs candidate on identical seeds."""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ENGINE_ROOT = Path("/Users/farhad/Code/PokerBot")
ENGINE_DIR = ENGINE_ROOT / "ext" / "fullhouse-engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from engine.game import BIG_BLIND  # noqa: E402
from sandbox.match import run_match  # noqa: E402


def bb100(chips: int, hands: int) -> float:
    return 0.0 if hands <= 0 else (chips / BIG_BLIND) / (hands / 100.0)


def bootstrap_ci(values: list[float], *, seed: int, iterations: int = 3000) -> dict:
    if not values:
        return {"mean": 0.0, "low": 0.0, "high": 0.0}
    rng = random.Random(seed)
    draws = []
    n = len(values)
    for _ in range(iterations):
        draws.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    draws.sort()
    return {
        "mean": sum(values) / n,
        "low": draws[int(iterations * 0.025)],
        "high": draws[min(iterations - 1, int(iterations * 0.975))],
    }


def run_one(match_id: str, hero_path: str, opponent_path: str, orientation: int, hands: int, seed: int) -> dict:
    if orientation == 0:
        lineup = {"hero": hero_path, "opp": opponent_path}
    else:
        lineup = {"opp": opponent_path, "hero": hero_path}
    result = run_match(match_id, lineup, n_hands=hands, verbose=False, seed=seed)
    return {
        "match_id": match_id,
        "seed": seed,
        "orientation": orientation,
        "scheduled_hands": hands,
        "actual_hands": int(result.get("n_hands") or 0),
        "chip_delta": int(result.get("chip_delta", {}).get("hero", 0)),
        "hero_errors": list(result.get("bot_errors", {}).get("hero", []) or []),
        "opponent_errors": list(result.get("bot_errors", {}).get("opp", []) or []),
        "duration_s": float(result.get("duration_s") or 0.0),
    }


def summarize(rows: list[dict], prefix: str) -> dict:
    scheduled = sum(row["scheduled_hands"] for row in rows)
    actual = sum(row["actual_hands"] for row in rows)
    chips = sum(row["chip_delta"] for row in rows)
    scheduled_values = [bb100(row["chip_delta"], row["scheduled_hands"]) for row in rows]
    ci = bootstrap_ci(scheduled_values, seed=(len(rows) * 17 + scheduled) ^ 0xBEEF)
    return {
        f"{prefix}_scheduled_hands": scheduled,
        f"{prefix}_actual_hands": actual,
        f"{prefix}_chip_delta": chips,
        f"{prefix}_scheduled_bb100": bb100(chips, scheduled),
        f"{prefix}_scheduled_ci_low": ci["low"],
        f"{prefix}_scheduled_ci_high": ci["high"],
        f"{prefix}_actual_bb100": bb100(chips, actual),
        f"{prefix}_hero_errors": sum(len(row["hero_errors"]) for row in rows),
        f"{prefix}_opponent_errors": sum(len(row["opponent_errors"]) for row in rows),
    }


def run(args: argparse.Namespace) -> dict:
    baseline = str(Path(args.baseline_zip).resolve())
    candidate = str(Path(args.candidate_zip).resolve())
    opponent = str(Path(args.opponent).resolve())
    baseline_rows = []
    candidate_rows = []
    delta_values = []
    pair_rows = []
    scheduled = 0
    pair_index = 0
    while scheduled < args.hands:
        seed = args.base + pair_index * args.seed_stride
        for orientation in (0, 1):
            b = run_one(
                f"{args.name}_locked_b{args.base}_k{pair_index}_s{seed}_o{orientation}",
                baseline,
                opponent,
                orientation,
                args.match_len,
                seed,
            )
            c = run_one(
                f"{args.name}_cand_b{args.base}_k{pair_index}_s{seed}_o{orientation}",
                candidate,
                opponent,
                orientation,
                args.match_len,
                seed,
            )
            baseline_rows.append(b)
            candidate_rows.append(c)
            delta_chip = c["chip_delta"] - b["chip_delta"]
            delta_bb100 = bb100(delta_chip, args.match_len)
            delta_values.append(delta_bb100)
            pair_rows.append({
                "seed": seed,
                "orientation": orientation,
                "scheduled_hands": args.match_len,
                "baseline_chip_delta": b["chip_delta"],
                "candidate_chip_delta": c["chip_delta"],
                "delta_chip": delta_chip,
                "delta_scheduled_bb100": delta_bb100,
                "baseline_actual_hands": b["actual_hands"],
                "candidate_actual_hands": c["actual_hands"],
                "baseline_hero_errors": len(b["hero_errors"]),
                "candidate_hero_errors": len(c["hero_errors"]),
                "baseline_opp_errors": len(b["opponent_errors"]),
                "candidate_opp_errors": len(c["opponent_errors"]),
            })
            scheduled += args.match_len
            print(
                f"{args.name} seed={seed} o={orientation} "
                f"locked={b['chip_delta']:+d}/{b['actual_hands']} "
                f"cand={c['chip_delta']:+d}/{c['actual_hands']} "
                f"delta_bb100={delta_bb100:+.2f} "
                f"err_locked={len(b['hero_errors'])}/{len(b['opponent_errors'])} "
                f"err_cand={len(c['hero_errors'])}/{len(c['opponent_errors'])}",
                flush=True,
            )
            if scheduled >= args.hands:
                break
        pair_index += 1
    delta_ci = bootstrap_ci(delta_values, seed=args.base ^ 0xD1FF)
    payload = {
        "name": args.name,
        "baseline_zip": baseline,
        "candidate_zip": candidate,
        "opponent": opponent,
        "base": args.base,
        "requested_scheduled_hands": args.hands,
        "match_len": args.match_len,
        "seed_stride": args.seed_stride,
        "scheduled_hands": scheduled,
        "delta_bb100": delta_ci["mean"],
        "delta_ci_low": delta_ci["low"],
        "delta_ci_high": delta_ci["high"],
        "regression_ci_excludes_zero": delta_ci["high"] < 0.0,
        "improvement_ci_excludes_zero": delta_ci["low"] > 0.0,
        "baseline": summarize(baseline_rows, "baseline"),
        "candidate": summarize(candidate_rows, "candidate"),
        "pairs": pair_rows,
    }
    print("SUMMARY " + json.dumps({k: v for k, v in payload.items() if k != "pairs"}, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--baseline-zip", default=str(ENGINE_ROOT / "submissions" / "v_final.zip"))
    parser.add_argument("--candidate-zip", required=True)
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--base", type=int, default=42)
    parser.add_argument("--hands", type=int, default=50000)
    parser.add_argument("--match-len", type=int, default=400)
    parser.add_argument("--seed-stride", type=int, default=1000)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    errors = (
        payload["baseline"]["baseline_hero_errors"]
        + payload["baseline"]["baseline_opponent_errors"]
        + payload["candidate"]["candidate_hero_errors"]
        + payload["candidate"]["candidate_opponent_errors"]
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
