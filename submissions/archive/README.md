# submissions/archive — preserved, NOT for finals (nothing deleted)

## r2-leaky-DO-NOT-SHIP/  — builds that contain the postflop stack-off leak
- `v_qual2_ship_d54640e0.zip`            sha256 d54640e0... — the build that went LIVE to R2 (leaky).
- `v_final_be7503d3_LEAKY_preserved.zip` sha256 be7503d3... — v2 strategy WITH the leak.
- `v_final_dir_be7503d3_LEAKY_src/`      — unpacked be7503d3 source (commitment.py has the
                                           `full_house_or_better -> return True` leak; NO full_house_dominated).
                                           This was previously the misleadingly-named `submissions/v_final/` dir.

## duplicate-of-finals-ship/
- `v_finals_rc_patched.zip`  sha256 b108eff5... — byte-identical to the shipped v_final.zip.

## finals-ship-b108eff5-editable-source/
- Clean extract of the shipped v_final.zip (b108eff5). Edit HERE if improving the ship,
  then repackage with tools/package.py and re-verify (validator + edge + smoke).

## pre-finals-snapshots/  — gate snapshots + superseded RCs (kept for history / benchmarking)
- v0_scaffold, v0_wired, v1_blueprint, v2_postflop, v3_hardened  (gate snapshots;
  tools/benchmark.py --vs-prior historically referenced these at submissions/ top level).
- v_final_pre_x1, v_final_reaudit                                (superseded RCs)
- v_final_SIMPLE_e4b4a8f1_preserved.zip                          (== best_green.zip, e4b4a8f1)
