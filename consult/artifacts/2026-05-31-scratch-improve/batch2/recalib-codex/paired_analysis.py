"""Paired-diff analysis: codex vs locked at the calibrated operating point.

Joins gate_codex/matches.jsonl vs gate_locked/matches.jsonl per (composition,
seed), computes the per-seed paired diff (codex - locked) and its distribution,
bust counts per hero, and per-composition verdicts.

DECISION-GRADE gate = C0D_DETERMINISTIC_SUBSET only (zero sim-noise; the locked-
vs-locked floor is exactly 0, so tolerance is TIGHT). C0/C1 are DIRECTIONAL-ONLY
(contain unseeded aggressor/toby; per-seed outcomes are not self-reproducible).
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

LANE = Path("/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-31-scratch-improve/batch2/recalib-codex")

# Tight C0D tolerances: deterministic field, locked-vs-locked floor == 0.
# A real median chip regression on C0D is any negative paired-diff median below
# this small slack (allow a tiny epsilon for a single re-converged cascade seed,
# but far below the noisy-field 6000). bust_tol tight too.
C0D_P50_TOL = 500.0     # paired-diff median must be >= -500 to PASS (≈ no median regression)
C0D_BUST_TOL = 0.05     # codex bust-rate may exceed locked by at most 5pp on the deterministic field


def load(d: str) -> dict:
    recs = [json.loads(l) for l in (LANE / d / "matches.jsonl").read_text().splitlines() if l.strip()]
    out = {}
    for r in recs:
        out[(r["composition"], int(r["seed"]))] = r
    return out


def percentile(values, pct):
    if not values:
        return None
    o = sorted(values)
    if len(o) == 1:
        return float(o[0])
    pos = (len(o) - 1) * (pct / 100.0)
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return float(o[lo])
    return float(o[lo] + (o[hi] - o[lo]) * (pos - lo))


def dist(values):
    if not values:
        return {}
    return {
        "n": len(values),
        "p10": round(percentile(values, 10), 1), "p25": round(percentile(values, 25), 1),
        "p50": round(percentile(values, 50), 1), "p75": round(percentile(values, 75), 1),
        "p90": round(percentile(values, 90), 1),
        "mean": round(statistics.mean(values), 1),
        "stdev": round(statistics.stdev(values), 1) if len(values) > 1 else 0.0,
        "min": round(min(values), 1), "max": round(max(values), 1),
    }


def main():
    codex = load("gate_codex")
    locked = load("gate_locked")
    comps = sorted({c for (c, s) in codex} & {c for (c, s) in locked})

    report = {"operating_point": {"seed_base": 900, "jobs": 1, "hands": 400},
              "tolerances_C0D": {"p50_tol": C0D_P50_TOL, "bust_tol": C0D_BUST_TOL},
              "compositions": {}}

    for c in comps:
        seeds = sorted(s for (cc, s) in codex if cc == c and (c, s) in locked)
        cdel = [codex[(c, s)]["hero_chip_delta"] for s in seeds]
        ldel = [locked[(c, s)]["hero_chip_delta"] for s in seeds]
        pdiff = [codex[(c, s)]["hero_chip_delta"] - locked[(c, s)]["hero_chip_delta"] for s in seeds]
        cbust = sum(1 for s in seeds if codex[(c, s)]["hero_busted"])
        lbust = sum(1 for s in seeds if locked[(c, s)]["hero_busted"])
        n = len(seeds)
        cbust_rate = round(cbust / n, 4) if n else None
        lbust_rate = round(lbust / n, 4) if n else None
        bust_delta = round(cbust_rate - lbust_rate, 4) if n else None

        # Byte-identical (zero-diff) seed count: a sanity tell for C0D determinism.
        identical = sum(1 for s in seeds if codex[(c, s)]["hero_final_stack"] == locked[(c, s)]["hero_final_stack"]
                        and codex[(c, s)]["hero_chip_delta"] == locked[(c, s)]["hero_chip_delta"])
        differing = [s for s in seeds if codex[(c, s)]["hero_chip_delta"] != locked[(c, s)]["hero_chip_delta"]]

        pd = dist(pdiff)
        entry = {
            "n": n,
            "codex_chip_delta": dist(cdel),
            "locked_chip_delta": dist(ldel),
            "paired_diff_codex_minus_locked": pd,
            "codex_bust": cbust, "locked_bust": lbust,
            "codex_bust_rate": cbust_rate, "locked_bust_rate": lbust_rate,
            "bust_rate_delta": bust_delta,
            "seeds_identical": identical,
            "seeds_differing": differing,
            "n_differing": len(differing),
            "per_seed_when_differing": {
                str(s): {"codex": codex[(c, s)]["hero_chip_delta"], "locked": locked[(c, s)]["hero_chip_delta"],
                         "diff": codex[(c, s)]["hero_chip_delta"] - locked[(c, s)]["hero_chip_delta"],
                         "codex_bust": int(codex[(c, s)]["hero_busted"]), "locked_bust": int(locked[(c, s)]["hero_busted"])}
                for s in differing
            },
        }

        if c == "C0D_DETERMINISTIC_SUBSET":
            p50 = pd.get("p50")
            p50_reg = p50 is not None and p50 < -C0D_P50_TOL
            bust_reg = bust_delta is not None and bust_delta > C0D_BUST_TOL
            entry["GATE_ROLE"] = "DECISION_GRADE"
            entry["p50_regression"] = p50_reg
            entry["bust_regression"] = bust_reg
            entry["pod_pass"] = (not p50_reg) and (not bust_reg)
        else:
            entry["GATE_ROLE"] = "DIRECTIONAL_ONLY"

        report["compositions"][c] = entry

    c0d = report["compositions"].get("C0D_DETERMINISTIC_SUBSET", {})
    report["C0D_gate_pass"] = c0d.get("pod_pass", None)

    (LANE / "paired_analysis.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    # Console summary
    print("=" * 90)
    print("PAIRED ANALYSIS: codex vs locked @ base 900, jobs=1, 400 hands")
    print("=" * 90)
    order = ["C0D_DETERMINISTIC_SUBSET", "C0_BASELINE", "C1_SINGLE_TOBY_WEAK_FIELD"]
    for c in order:
        if c not in report["compositions"]:
            continue
        e = report["compositions"][c]
        print(f"\n### {c}  [{e['GATE_ROLE']}]  n={e['n']}")
        print(f"  codex   chip-delta: p50={e['codex_chip_delta']['p50']:>10} mean={e['codex_chip_delta']['mean']:>10} bust={e['codex_bust']}/{e['n']} ({e['codex_bust_rate']})")
        print(f"  locked  chip-delta: p50={e['locked_chip_delta']['p50']:>10} mean={e['locked_chip_delta']['mean']:>10} bust={e['locked_bust']}/{e['n']} ({e['locked_bust_rate']})")
        pd = e["paired_diff_codex_minus_locked"]
        print(f"  PAIRED DIFF (codex-locked): p50={pd['p50']:>10} mean={pd['mean']:>10} stdev={pd['stdev']:>10} min={pd['min']} max={pd['max']}")
        print(f"  bust_rate_delta (codex-locked) = {e['bust_rate_delta']:+.4f}  ({e['codex_bust']} vs {e['locked_bust']})")
        print(f"  seeds identical={e['seeds_identical']}/{e['n']}  differing={e['n_differing']}")
        if c == "C0D_DETERMINISTIC_SUBSET":
            print(f"  >>> p50_regression={e['p50_regression']} (tol -{C0D_P50_TOL})  bust_regression={e['bust_regression']} (tol {C0D_BUST_TOL})")
            print(f"  >>> C0D POD_PASS = {e['pod_pass']}")
            if e["n_differing"] <= 12 and e["n_differing"] > 0:
                print(f"  per-seed where differing:")
                for s, v in sorted(e["per_seed_when_differing"].items(), key=lambda kv: int(kv[0])):
                    print(f"      seed {s}: codex={v['codex']:+d} locked={v['locked']:+d} diff={v['diff']:+d} cbust={v['codex_bust']} lbust={v['locked_bust']}")
    print(f"\n{'='*90}")
    print(f"C0D DECISION-GRADE GATE PASS = {report['C0D_gate_pass']}")
    print(f"{'='*90}")
    print(f"\nwrote {LANE/'paired_analysis.json'}")


if __name__ == "__main__":
    main()
