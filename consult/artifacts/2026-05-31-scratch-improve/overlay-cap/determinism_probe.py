"""Determinism probe: run a single match (hero vs one opponent or a field)
TWICE with identical seed and report hero final stack + hero decision count.

If two runs with the same hero, same seed, same ACTION_TIMEOUT produce
identical (final_stack, hero_decisions), the hero+engine+that-opponent are
deterministic for that seed. Divergence localizes the noise:
  * vs deterministic opponent (template) diverging => hero/engine timing.
  * vs randomizing opponent (toby) diverging => opponent mixed-strategy RNG.

Run with ACTION_TIMEOUT=30 to remove wall-clock timeout folds from the picture.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path("/Users/farhad/Code/PokerBot")
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
sys.path.insert(0, str(ENGINE_DIR))
from sandbox import match as match_mod  # noqa: E402

HERO = "hero"


def count_hero_decisions(result: dict) -> int:
    n = 0
    for hand in result.get("hands", []):
        for ev in hand.get("events", []):
            if ev.get("type") == "action" and ev.get("bot_id") == HERO:
                n += 1
    return n


def run_once(hero_zip: Path, opp_zips: dict, seed: int, hands: int) -> dict:
    paths = {HERO: str(hero_zip.resolve())}
    for name, p in opp_zips.items():
        paths[name] = str(Path(p).resolve())
    t0 = time.time()
    result = match_mod.run_match(f"det_s{seed}", paths, n_hands=hands, verbose=False, seed=seed)
    return {
        "final_stacks": result["final_stacks"],
        "hero_final_stack": result["final_stacks"].get(HERO, 0),
        "hero_chip_delta": result["chip_delta"][HERO],
        "n_hands": result["n_hands"],
        "hero_decisions": count_hero_decisions(result),
        "bot_errors": {k: len(v) for k, v in result["bot_errors"].items()},
        "duration_s": round(time.time() - t0, 2),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--hero-zip", required=True, type=Path)
    p.add_argument("--opp", nargs="+", required=True, help="name=path pairs")
    p.add_argument("--seed", type=int, default=142)
    p.add_argument("--hands", type=int, default=400)
    p.add_argument("--repeats", type=int, default=2)
    args = p.parse_args()

    opp_zips = {}
    for item in args.opp:
        name, path = item.split("=", 1)
        opp_zips[name] = path

    runs = []
    for i in range(args.repeats):
        r = run_once(args.hero_zip, opp_zips, args.seed, args.hands)
        runs.append(r)
        print(f"[det] run{i} seed={args.seed} hero_final={r['hero_final_stack']} "
              f"delta={r['hero_chip_delta']:+d} hands={r['n_hands']} "
              f"hero_decisions={r['hero_decisions']} errs={r['bot_errors']} dur={r['duration_s']}s",
              flush=True)

    base = (runs[0]["hero_final_stack"], runs[0]["hero_decisions"], runs[0]["n_hands"])
    identical = all((r["hero_final_stack"], r["hero_decisions"], r["n_hands"]) == base for r in runs)
    print(f"[det] DETERMINISTIC={identical} opponents={list(opp_zips)} "
          f"ACTION_TIMEOUT={__import__('os').environ.get('ACTION_TIMEOUT','2')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
