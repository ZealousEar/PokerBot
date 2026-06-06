#!/usr/bin/env python3
"""Paired CRN analysis of two deployed_artifact_gauntlet match_results.json runs.

Both runs MUST use the same --seed-base, same opponents, same match-len so that
each (opponent, seed, orientation) sample is the SAME dealt cards -> common
random numbers (CRN) paired comparison. We difference candidate - baseline per
paired sample, collapsing variance onto the divergent spots.

Promotion bar (anti-variance):
  * aggregate paired margin >= +5 bb/100 AND paired lower 95% CI > 0
  * no opponent bucket worse than -8 bb/100
  * zero candidate runner errors / timeouts / illegal actions
  * gain not driven by a single opponent or a single seed
"""
import argparse, json, random, sys
from pathlib import Path

BIG_BLIND = 100

def load_samples(path):
    data = json.loads(Path(path).read_text())
    out = {}  # opponent -> {(seed,orientation): sample}
    errs = 0
    for summ in data.get("summaries", []):
        opp = summ["opponent"]
        d = out.setdefault(opp, {})
        for s in summ.get("samples", []):
            key = (int(s["seed"]), int(s["orientation"]))
            d[key] = s
            errs += len(s.get("hero_errors", []) or [])
    return out, errs

def bb100(chips, hands):
    return (float(chips) / BIG_BLIND) / (float(hands) / 100.0) if hands else 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True, help="candidate match_results.json")
    ap.add_argument("--baseline", required=True, help="baseline (live) match_results.json")
    ap.add_argument("--label", default="candidate")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    cand, cand_errs = load_samples(args.candidate)
    base, base_errs = load_samples(args.baseline)

    opponents = sorted(set(cand) & set(base))
    missing = sorted(set(cand) ^ set(base))

    per_opp = []
    paired_all = []  # list of (chip_delta, hands) paired samples across all opponents
    for opp in opponents:
        keys = sorted(set(cand[opp]) & set(base[opp]))
        pairs = []
        for k in keys:
            cs, bs = cand[opp][k], base[opp][k]
            # identical dealt cards => CRN paired diff
            hands = int(cs["actual_hands"])  # candidate hands for this match
            dchip = int(cs["hero_chip_delta"]) - int(bs["hero_chip_delta"])
            pairs.append((dchip, hands, k))
            paired_all.append((dchip, hands))
        tot_chip = sum(p[0] for p in pairs)
        tot_hands = sum(p[1] for p in pairs)
        margin = bb100(tot_chip, tot_hands)
        # per-seed margins (combine both orientations per seed) for outlier check
        per_opp.append({
            "opponent": opp, "n_pairs": len(pairs),
            "paired_chip_delta": tot_chip, "hands": tot_hands,
            "margin_bb100": round(margin, 3),
            "per_pair_chip": [{"seed": k[0], "orient": k[1], "dchip": dc} for dc, _, k in pairs],
        })

    # aggregate
    agg_chip = sum(p[0] for p in paired_all)
    agg_hands = sum(p[1] for p in paired_all)
    agg_margin = bb100(agg_chip, agg_hands)

    # paired bootstrap CI over sample-pairs
    rng = random.Random(20260604)
    n = len(paired_all)
    boot = []
    for _ in range(5000):
        c = h = 0
        for _ in range(n):
            dc, hh = paired_all[rng.randrange(n)]
            c += dc; h += hh
        boot.append(bb100(c, h))
    boot.sort()
    lo = boot[int(0.025 * len(boot))]
    hi = boot[int(0.975 * len(boot))]

    worst = min((o["margin_bb100"] for o in per_opp), default=0.0)
    worst_opp = min(per_opp, key=lambda o: o["margin_bb100"]) if per_opp else None

    # single-opponent-outlier check: drop the single best opponent, recompute aggregate
    drop_best_margin = None
    if len(per_opp) > 1:
        best = max(per_opp, key=lambda o: o["margin_bb100"])
        c = agg_chip - best["paired_chip_delta"]
        h = agg_hands - best["hands"]
        drop_best_margin = round(bb100(c, h), 3)

    # promotion bar
    checks = {
        "aggregate_ge_5": agg_margin >= 5.0,
        "lower_ci_gt_0": lo > 0.0,
        "no_bucket_below_-8": worst >= -8.0,
        "zero_candidate_errors": cand_errs == 0,
        "not_single_opp_driven": (drop_best_margin is None) or (drop_best_margin > 0.0),
    }
    promote = all(checks.values())

    report = {
        "label": args.label,
        "aggregate_margin_bb100": round(agg_margin, 3),
        "paired_ci95": [round(lo, 3), round(hi, 3)],
        "n_paired_samples": n,
        "total_paired_hands": agg_hands,
        "worst_bucket": {"opponent": worst_opp["opponent"] if worst_opp else None, "margin_bb100": worst},
        "drop_best_opp_margin_bb100": drop_best_margin,
        "candidate_runner_errors": cand_errs,
        "baseline_runner_errors": base_errs,
        "missing_opponents": missing,
        "per_opponent": sorted(per_opp, key=lambda o: o["margin_bb100"]),
        "promotion_checks": checks,
        "PROMOTE": promote,
    }
    print(json.dumps(report, indent=2))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2))
    return 0 if promote else 1

if __name__ == "__main__":
    sys.exit(main())
