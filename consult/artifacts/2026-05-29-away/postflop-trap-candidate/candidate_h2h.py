#!/usr/bin/env python3
"""Candidate-vs-public-opponent scheduled H2H runner for this lane."""

import argparse
import json
import random
import sys
from pathlib import Path

ENGINE_ROOT = Path("/Users/farhad/Code/PokerBot")
ENGINE_DIR = ENGINE_ROOT / "ext" / "fullhouse-engine"
sys.path.insert(0, str(ENGINE_DIR))

from engine.game import BIG_BLIND  # noqa: E402
from sandbox.match import run_match  # noqa: E402


def bb100(chips: int, hands: int) -> float:
    if hands <= 0:
        return 0.0
    return (chips / BIG_BLIND) / (hands / 100.0)


def bootstrap_ci(samples: list[dict], seed: int) -> dict:
    if not samples:
        return {"mean": 0.0, "low": 0.0, "high": 0.0}
    rng = random.Random(seed)
    values = []
    for _ in range(3000):
        chips = 0
        hands = 0
        for _ in range(len(samples)):
            row = samples[rng.randrange(len(samples))]
            chips += int(row["chip_delta"])
            hands += int(row["scheduled_hands"])
        values.append(bb100(chips, hands))
    values.sort()
    chips_total = sum(int(row["chip_delta"]) for row in samples)
    hands_total = sum(int(row["scheduled_hands"]) for row in samples)
    return {
        "mean": bb100(chips_total, hands_total),
        "low": values[int(len(values) * 0.025)],
        "high": values[int(len(values) * 0.975)],
    }


def run(args) -> dict:
    hero = str(Path(args.hero_zip).resolve())
    opponent = str(Path(args.opponent_zip).resolve())
    samples = []
    rows = []
    attempted = 0
    actual = 0
    hero_errors = 0
    opponent_errors = 0
    pair_index = 0
    while attempted < args.hands:
        seed = args.base + pair_index * args.seed_stride
        pair_chips = 0
        pair_actual = 0
        pair_scheduled = 0
        for orientation, lineup in enumerate((
            {"hero": hero, "opp": opponent},
            {"opp": opponent, "hero": hero},
        )):
            match_id = f"{args.name}_b{args.base}_k{pair_index}_s{seed}_o{orientation}"
            result = run_match(match_id, lineup, n_hands=args.match_len, verbose=False, seed=seed)
            hero_chip = int(result.get("chip_delta", {}).get("hero", 0))
            row = {
                "match_id": match_id,
                "seed": seed,
                "orientation": orientation,
                "scheduled_hands": args.match_len,
                "actual_hands": int(result.get("n_hands") or 0),
                "hero_chip_delta": hero_chip,
                "hero_scheduled_bb100": bb100(hero_chip, args.match_len),
                "hero_actual_bb100": bb100(hero_chip, int(result.get("n_hands") or 0)),
                "hero_errors": list(result.get("bot_errors", {}).get("hero", [])),
                "opponent_errors": list(result.get("bot_errors", {}).get("opp", [])),
                "duration_s": float(result.get("duration_s") or 0.0),
            }
            rows.append(row)
            pair_chips += hero_chip
            pair_actual += row["actual_hands"]
            pair_scheduled += args.match_len
            attempted += args.match_len
            actual += row["actual_hands"]
            hero_errors += len(row["hero_errors"])
            opponent_errors += len(row["opponent_errors"])
            print(
                f"{match_id} actual={row['actual_hands']}/{args.match_len} "
                f"hero_chip={hero_chip:+d} scheduled_bb100={row['hero_scheduled_bb100']:+.2f} "
                f"actual_bb100={row['hero_actual_bb100']:+.2f} "
                f"hero_err={len(row['hero_errors'])} opp_err={len(row['opponent_errors'])}",
                flush=True,
            )
            if attempted >= args.hands:
                break
        samples.append({
            "seed": seed,
            "scheduled_hands": pair_scheduled,
            "actual_hands": pair_actual,
            "chip_delta": pair_chips,
            "scheduled_bb100": bb100(pair_chips, pair_scheduled),
            "actual_bb100": bb100(pair_chips, pair_actual),
        })
        pair_index += 1
    ci = bootstrap_ci(samples, args.base ^ 0x5EED)
    payload = {
        "name": args.name,
        "hero_zip": hero,
        "opponent_zip": opponent,
        "base": args.base,
        "match_len": args.match_len,
        "seed_stride": args.seed_stride,
        "scheduled_hands": attempted,
        "actual_hands": actual,
        "hero_chip_delta": sum(row["chip_delta"] for row in samples),
        "hero_scheduled_bb100": ci["mean"],
        "hero_scheduled_ci_low": ci["low"],
        "hero_scheduled_ci_high": ci["high"],
        "hero_actual_bb100": bb100(sum(row["chip_delta"] for row in samples), actual),
        "hero_errors": hero_errors,
        "opponent_errors": opponent_errors,
        "samples": samples,
        "matches": rows,
    }
    print("SUMMARY " + json.dumps({k: v for k, v in payload.items() if k not in {"samples", "matches"}}, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--hero-zip", required=True)
    parser.add_argument("--opponent-zip", required=True)
    parser.add_argument("--base", type=int, required=True)
    parser.add_argument("--hands", type=int, default=20000)
    parser.add_argument("--match-len", type=int, default=500)
    parser.add_argument("--seed-stride", type=int, default=1000)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 1 if payload["hero_errors"] or payload["opponent_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
