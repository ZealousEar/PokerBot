# CAMP2 SEARCH — upside-only hunt for a bot that PROVABLY beats live finals build b108eff5

Date: 2026-06-04. Goal: park the single best PROVEN winner; if nothing beats live, change nothing (valid result).
ABSOLUTE ISOLATION HONORED: canonical src/, submissions/v_final.zip, best_green.zip untouched. All work under
consult/artifacts/2026-06-04-camp2-search/. No upload performed. No pip install. ext/fullhouse-engine/ untouched.

## Baseline (immutable opponent)
- submissions/v_final.zip  sha256 = b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b  ✅ confirmed b108eff5
- Live PASSES failure-mode tester: validator ✅ · edge(fuzz+disaster no-large-commit) ✅ · probes(11 clean) ✅ · docker smoke ✅

## Methodology (proof-of-green)
- Gauntlet runs matches for --bot ONLY; baseline played separately. Pairing = run both zips at IDENTICAL --seed-base 42
  (CRN: same dealt cards per (opponent,seed,orientation)); margin = candidate_chip - live_chip differenced per paired sample.
- 12 opponents (5 reference: template/aggressor/mathematician/shark/ref_bot_2 + 7 synthetic incl finalist-field types).
  22 paired samples/opp (11 seeds x 2 orientations), hands-per-opponent 4200 (actual ~33k total; aggressive opps bust early).
- Tools: deployed_artifact_gauntlet.py (paired seeds) · paired_analyze.py (CRN diff + bootstrap CI) · failure_tester.py.
- PROMOTION BAR: aggregate >= +5 bb/100 AND paired lower-95%CI > 0 AND no bucket < -8 bb/100 AND zero candidate
  runner errors/timeouts AND gain not single-opponent-driven.
- DRIFT CONTROL (NULL = unedited archive src, same packaging) vs live = +1.211 bb/100, CI [-1.924, +4.511] → straddles 0.
  Archive src ≈ live; packaging clean; comparison VALID. Residual noise floor ~±2-4 bb/100 even with CRN.

## Candidate zips (SHA256)
- NULL (control)  bf201b82d6bb…  (drift +1.2, CI incl 0)
- A-3bet          0a3a1180a014…  widen 3-bet bluffs (ranges.py)
- B-cbet          c569cd338805…  c-bet bluff freq 0.30->0.40, dry bonus 0.10->0.15 (postflop.py)
- C-overlay       c64217056077…  MAX_DEVIATION_PP 0.20->0.27 (opponent_model.py)
- D-river         fd92bed48f22…  river payoff discipline +buffer (postflop.py)

## Packaging provenance (confirmed)
Every candidate zip was packaged from the SCRATCH tree, NOT canonical src/ (which the brief flags as a stub).
- Source copied FROM: submissions/archive/finals-ship-b108eff5-editable-source/{src,data,bot.py}
- INTO work trees:    consult/artifacts/2026-06-04-camp2-search/work-trees/<cand>/
- Packaged by copying tools/package.py into each work-tree/tools/ so package.py ROOT resolves to the work tree
  (ROOT = Path(__file__).parent.parent), bundling that tree's src+data with the standard root shim.
- Verified: candidate data blueprints are byte-identical to live v_final.zip (field_priors 5394, flop_buckets 582,
  flop_strategy 17029, preflop_blueprint 2147) — candidates differ from live ONLY in their edited src module.

## Results — screening, ~33k hands paired (CRN, seed-base 42), all 4 axes evaluated; failure_tester PASS for all
| cand | failure_tester | paired margin bb/100 | CI95 | worst bucket | drop-best-opp | cand errs | PROMOTE |
|------|----------------|----------------------|------|--------------|---------------|-----------|---------|
| A-3bet    | PASS | -2.537 | [-6.23, +0.59] | aggressor -162 (414h outlier) | -2.55 | 0 | NO |
| B-cbet    | PASS | -5.107 | [-9.62, -0.95] | -121 (small-sample) | -6.66 | 0 | NO |
| C-overlay | PASS | -0.606 | [-1.94,  0.00] | -45  (small-sample) | -0.61 | 0 | NO |
| D-river   | PASS | +1.208 | [-1.93, +4.71] | 0.0 | 0.0 | 0 | NO |

Reference for scale: NULL (unedited archive src) drift vs live = +1.211 bb/100, CI [-1.92, +4.51].

## Why no 100k escalation / no combined test
- Promotion bar = margin >= +5 bb/100 at >=100k paired. The paired point estimate is the unbiased mean; adding hands
  shrinks the CI but does NOT shift the mean. A candidate measured at +1.2 (or negative) cannot reach +5 at 100k.
- A,B,C are negative. D-river's +1.208 is statistically indistinguishable from the NULL packaging offset (+1.211),
  with worst-bucket 0.0 and drop-best 0.0 (D barely alters behaviour); even its optimistic CI edge (+4.71) is < +5.
- Therefore zero axes clear the bar -> the "combine >=2 winners" interaction test does not trigger. No new knobs added.

## FINAL VERDICT
NO IMPROVEMENT — keep live b108eff5. All four candidate axes (3-bet width, c-bet frequency, overlay magnitude,
river payoff discipline) fail to beat the live finals build. The shipped bot is already well-tuned; widening
aggression (A,B) actively bleeds value to reference/sticky opponents. NO WINNER.zip created. No upload performed.
Isolation intact: canonical src/, submissions/v_final.zip, best_green.zip, ext/ all untouched.
