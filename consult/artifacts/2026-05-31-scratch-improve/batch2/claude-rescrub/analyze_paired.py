"""Exact-paired analysis: candidate C0D vs locked C0D on identical seeds.

Decision-grade signal per the lane spec: the deterministic-subset field
[hero, template, mathematician, shark, ref_bot_2] is fully reproducible at a
fixed seed, so candidate[seed] - locked[seed] is an EXACT paired chip diff with
zero simulator noise. Reports paired-diff distribution + bust comparison.
"""
import json, statistics, sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
COMP = "C0D_DETERMINISTIC_SUBSET"

def load(out_dir):
    recs = {}
    mp = LANE / out_dir / "matches.jsonl"
    for line in mp.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["composition"] == COMP:
            recs[int(r["seed"])] = r
    return recs

def pct(vals, p):
    if not vals: return None
    o = sorted(vals); 
    if len(o)==1: return float(o[0])
    pos=(len(o)-1)*(p/100.0); import math
    lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi: return float(o[lo])
    return float(o[lo]+(o[hi]-o[lo])*(pos-lo))

cand = load("detpod_candidate")
lock = load("detpod_locked")
seeds = sorted(set(cand) & set(lock))
assert seeds, "no overlapping seeds"

paired = []
cand_busts = lock_busts = 0
cand_errs = lock_errs = 0
per_seed = {}
n_byte_identical = 0
for s in seeds:
    cd = cand[s]["hero_chip_delta"]; ld = lock[s]["hero_chip_delta"]
    diff = cd - ld
    paired.append(diff)
    cb = cand[s]["hero_busted"]; lb = lock[s]["hero_busted"]
    cand_busts += int(cb); lock_busts += int(lb)
    cand_errs += cand[s]["hero_action_errors"]; lock_errs += lock[s]["hero_action_errors"]
    if cd == ld: n_byte_identical += 1
    per_seed[s] = {"candidate": cd, "locked": ld, "diff": diff,
                   "cand_bust": cb, "lock_bust": lb}

cand_deltas = [cand[s]["hero_chip_delta"] for s in seeds]
lock_deltas = [lock[s]["hero_chip_delta"] for s in seeds]

out = {
  "regime": f"exact_paired_deterministic_subset {COMP}=[hero,template,mathematician,shark,ref_bot_2]",
  "n": len(seeds), "seeds": seeds, "jobs": 1, "seed_base": seeds[0], "hands": 400,
  "candidate_sha": cand[seeds[0]].get("hero_sha"),
  "n_seeds_byte_identical_outcome": n_byte_identical,
  "candidate": {"p50": pct(cand_deltas,50), "mean": round(statistics.mean(cand_deltas),1),
                "bust": cand_busts, "bust_rate": round(cand_busts/len(seeds),4),
                "action_errors": cand_errs},
  "locked":    {"p50": pct(lock_deltas,50), "mean": round(statistics.mean(lock_deltas),1),
                "bust": lock_busts, "bust_rate": round(lock_busts/len(seeds),4),
                "action_errors": lock_errs},
  "paired_diff": {
      "p10": pct(paired,10), "p25": pct(paired,25), "p50": pct(paired,50),
      "p75": pct(paired,75), "p90": pct(paired,90),
      "mean": round(statistics.mean(paired),1),
      "stdev": round(statistics.stdev(paired),1) if len(paired)>1 else 0.0,
      "min": min(paired), "max": max(paired), "sum": sum(paired),
  },
  "marginal_p50_delta_cand_minus_lock": pct(cand_deltas,50) - pct(lock_deltas,50),
  "bust_delta_cand_minus_lock": round(cand_busts/len(seeds) - lock_busts/len(seeds),4),
  "per_seed": per_seed,
}
(LANE / "paired_summary.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({k:out[k] for k in ("n","candidate","locked","paired_diff",
      "marginal_p50_delta_cand_minus_lock","bust_delta_cand_minus_lock",
      "n_seeds_byte_identical_outcome")}, indent=2))
