# LANE B — bounded-overlay magnitude reduction — VERDICT

**gate_clearer = FALSE for both candidates. Do NOT promote. Locked v_final.zip remains the upload target.**

Protected SHA `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` verified for
`submissions/{v_final,best_green}.zip` at lane START and END (unchanged; never touched).

## Premise correction (load-bearing)
The lane's `MAX_DEVIATION_PP ~0.20` scalar **does not exist in the shipped artifact.**
- A scalar `MAX_DEVIATION_PP` lived in a SUPERSEDED overlay design (commit 329767d). The X1 patch
  (9904ed1) replaced it; the shipped `v_final.zip` was built from commit `a00561c` (verified:
  every `src/*.py` in v_final == a00561c byte-for-byte).
- The real overlay = `src/bot.py::_pressure_preflop_overlay`: **preflop-only, discrete, hardcoded
  hand-score thresholds** (no scalar knob). It overrides the blueprint only when
  `OpponentModel.pressure_features` flags `high_pressure` or `fold_prone_pressure`.

## Translation of the thesis (documented, not a scalar)
Monotone ladder on the ALL-IN (bust-risk) branches; defensive (check/fold/call) branches kept
(they are the thesis-aligned downside reducers):
- **cap015**: high_pressure shove gate 72 -> 96 (QQ+, AKs/AKo/AQs); fold-prone shove 88 -> 100 (KK+, AKs).
- **cap010**: remove the all-in branch entirely -> overlay is purely defensive.

Runtime-verified on packaged `decide()` (not just the source diff):
- 88 (score 80), high_pressure: locked=all_in, cap015=fold, cap010=fold.
- AKs (score 103), high_pressure: locked=all_in, cap015=all_in, cap010=fold.
Build fidelity: each candidate zip differs from locked ONLY in the overlay block of `src/bot.py`;
all other src + all data npz + the root shim are byte-identical.

## Why the specified 40-seed paired six-max gate is NOT satisfiable
Empirically falsified the common-random-numbers premise: **locked-vs-locked, same seed, jobs=1,
identical hero, seed 142 swung bust -> +37279** between two runs. Determinism probes (ACTION_TIMEOUT=30)
localize the cause precisely:
- hero + {template, mathematician, shark, ref_bot_2} => FULLY reproducible (exact final stack + decision count).
- **toby_master and aggressor => non-reproducible** (unseeded internal mixed-strategy RNG; the engine
  seeds only card dealing, not opponent RNG).
Every decisive pod contains a non-reproducible opponent (C0 has aggressor; C1/C3/C4 have toby), so
paired-seed differencing cannot isolate a sub-stack overlay effect. `tools/exploit_check.py` (LBR) is a
TODO stub, so success-bar (b) cannot be affirmatively measured either.

## What WAS measured (noise-free)
1. **Overlay firing rate** (locked hero, captured real preflop states): ~1/1000 preflop decisions in
   most fields; ~11.5/1000 only in the public-nightmare field. When it fires and a cap changes the
   action, the change is **exclusively all_in -> fold/check** (a shove-removal). See `overlay_divergence.json`.
2. **Enumeration map** (`overlay_enumeration.json`): all changes are shove-removals (monotone,
   downside-only). cap015 removes shoves for 22 hands (high_pressure band) + 10 (fold-prone); cap010
   removes all 28 + 13. No change ever ADDS aggression.
3. **EXACT-PAIRED deterministic-subset SUBSTITUTE pod** (`detpod_paired_summary.json`); the specified
   C0/C1/C3/C4 @ >=40 paired seeds is unsatisfiable (unseeded opponents), so this uses the proven-reproducible
   field C0D=[hero, template, mathematician, shark, ref_bot_2], 24 seeds, jobs=1, removing SIMULATION noise
   (NOT card/seed variance):
   - locked: p50=12025, bust=0/24, mean=12536
   - cap015: p50=11925 (-100), bust=1/24, mean=11163
   - cap010: p50=11925 (-100), bust=0/24, mean=12188
   ~75-83% of seeds are BYTE-IDENTICAL across all three heroes (the overlay almost never fires vs a passive
   field). Only ~4-6/24 seeds change outcome at all, and on those the swings are huge and MIXED-SIGN
   (-18150, -14750, +9850) because one all_in->fold cascades through the whole match. These differences are
   WITHIN-NOISE at this n and NOT distinguishable from locked or from each other:
   - cap015 1/24 bust vs cap010 0/24 is small-count noise, NOT a cap015 weakness. Proof from this same data:
     seed 716 *busts* cap015 (-10000) but *helps* cap010 (+14600); and cap010 removes a strict SUPERSET of
     cap015's shoves yet busts 0/24. Shove-removal is therefore not systematically bust-causing.
   - (Caveat: seed 721 shows cap015 differing while cap010 matches locked despite the nesting -- a re-converged
     trajectory cascade; do not over-read per-seed deltas.)

## Verdict against the INVERTED bar (improvement is the goal)
Neither cap015 nor cap010 clears. Both are bounded, monotone shove-reductions (all_in -> fold/check only,
never adding aggression). In the measurable (reproducible) regime both sit p50 -100 vs locked with bust
counts (1/24, 0/24) that are within small-count noise of locked (0/24) and of each other; the specified
sharp-field >=40-seed paired gate is unsatisfiable, so their net six-max downside/EV sign is **at/below the
noise floor AND unresolvable given pairing is broken by unseeded opponents**. Neither demonstrates the
required downside IMPROVEMENT. The intervention is real, correctly built, and thesis-directionally sound,
but it fires almost exclusively in precisely the pods that are unmeasurable; against the passive field it is
a near-no-op flat-to-slightly-negative on EV (consistent with removing thin shoves that are +EV vs a weak
field). Honest negative result; do not promote.

## Artifacts
- Candidates: `cap015.zip` (sha 61055f07...), `cap010.zip` (sha 8d6ac258...)
- Build-fidelity ref: `rebuild_nochange.zip` (byte-identical content to locked v_final)
- Harness: `run_pods.py`, `determinism_probe.py`, `overlay_divergence.py`, `overlay_enumeration.py`
- Results: `overlay_divergence.json`, `overlay_enumeration.json`, `detpod_paired_summary.json`,
  `detpod_run.log`, `detpod_{locked,cap015,cap010}/`
- Stage logs: `stage1_logs/`, `stage2_logs/`
