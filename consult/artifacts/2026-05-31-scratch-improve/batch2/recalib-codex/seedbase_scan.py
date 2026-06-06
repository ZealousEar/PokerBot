"""Locked-only C0 seed-base scan to find a NON-SATURATING operating point.

Goal (task Step 1): find a toby/aggressor seed base where locked v_final's C0
bust rate is well off the -10000 floor (target <50%), so the chip-delta metric
has resolution for the directional reads. C0 = [hero, template, aggressor,
mathematician, shark, ref_bot_2] (the aggressor reference field, no toby).

Runs LOCKED ONLY (submissions/v_final.zip as hero) at jobs=1 over several
candidate bases with a modest seed count each. Reuses run_pods machinery.

ARTIFACT-LOCAL. Never writes submissions/. Never edits src/. Verifies the
protected SHA before/after.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LANE = Path("/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-31-scratch-improve/batch2/recalib-codex")
sys.path.insert(0, str(LANE))
import run_pods as rp  # noqa: E402

ROOT = Path("/Users/farhad/Code/PokerBot")
LOCKED = ROOT / "submissions" / "v_final.zip"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bases", type=int, nargs="+", required=True)
    ap.add_argument("--seeds", type=int, default=14)
    ap.add_argument("--hands", type=int, default=400)
    ap.add_argument("--out", type=Path, default=LANE / "seedbase_scan_results.json")
    args = ap.parse_args()

    rp.validate_protected("scan_before")

    opp_dir = LANE / "scan_opponent_zips"
    bot_paths = rp.prepare_bot_paths(LOCKED.resolve(), opp_dir)

    timer = rp.DecisionTimer()
    timer.install()
    results = {}
    try:
        for base in args.bases:
            seeds = list(range(base, base + args.seeds))
            deltas, busts, errs = [], 0, 0
            recs = []
            for s in seeds:
                rec = rp.run_one_match("C0_BASELINE", s, args.hands, bot_paths, timer)
                deltas.append(rec["hero_chip_delta"])
                busts += int(rec["hero_busted"])
                errs += rec["hero_action_errors"]
                recs.append({"seed": s, "delta": rec["hero_chip_delta"], "bust": int(rec["hero_busted"]),
                             "opp_errs": {k: v for k, v in rec["bot_error_counts"].items() if k != "hero" and v}})
                print(f"[scan] base={base} s{s} delta={rec['hero_chip_delta']:+d} bust={int(rec['hero_busted'])}", flush=True)
            n = len(deltas)
            p50 = rp.percentile(deltas, 50)
            results[str(base)] = {
                "base": base, "seeds": args.seeds, "n": n,
                "bust_rate": round(busts / n, 4), "busts": busts,
                "p50": p50, "mean": round(sum(deltas) / n, 1),
                "min": min(deltas), "max": max(deltas),
                "hero_action_errors": errs,
                "p50_off_floor": p50 > -10000,
                "per_seed": recs,
            }
            print(f"[scan] === base={base}: bust_rate={results[str(base)]['bust_rate']} p50={p50} "
                  f"off_floor={results[str(base)]['p50_off_floor']} ===", flush=True)
    finally:
        timer.uninstall()

    rp.validate_protected("scan_after")
    args.out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(f"[scan] wrote {args.out}", flush=True)

    # Rank by bust rate ascending; flag bases with bust<0.50.
    ranked = sorted(results.values(), key=lambda d: d["bust_rate"])
    print("\n[scan] RANKING (lowest bust first):", flush=True)
    for d in ranked:
        flag = "  <-- candidate (bust<0.50)" if d["bust_rate"] < 0.50 else ""
        print(f"  base={d['base']} bust_rate={d['bust_rate']} p50={d['p50']} mean={d['mean']}{flag}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
