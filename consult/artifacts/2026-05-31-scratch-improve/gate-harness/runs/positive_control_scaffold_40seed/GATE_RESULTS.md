# Candidate-vs-Locked Gate Result

Generated: `2026-05-31T01:16:48Z`
Verdict: **GATE_FAIL_POD_REGRESSION**

NOTHING AUTO-PROMOTES. GATE_CLEAR only FLAGS the candidate for a human MODIFY decision; submissions/v_final.zip stays the upload target unless a human explicitly overrides.

## Artifacts

- Candidate: `consult/artifacts/2026-05-31-scratch-improve/gate-harness/scaffold_candidate.zip` sha `8266cb49fd6ce7c32ae2c7db90737fd33788423f5525c0f155ddcfd51f7c9b5f`
- Locked baseline: `submissions/v_final.zip` sha `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- Protected SHA OK (start AND end, both canonical zips): `True`
  - v_final start `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
  - v_final end   `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
  - best_green start `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
  - best_green end   `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`

Run config: hands/match `400`, seed base `142`, seeds `40`, pods `C0, C1`, PYTHONHASHSEED `0`, p50_tol `6000.0`, bust_tol `0.15`.

## Stage results (fail-fast cheap -> expensive)

| stage | name | result | exit |
| --- | --- | --- | ---: |

_import_audit caveat: audits working-tree `src/`, not the candidate zip; the candidate zip's imports are covered by the engine validator's forbidden-module AST scan._

## Paired six-max pods (candidate vs locked, identical seeds)

Primary gate signal is the PAIRED-DIFF median (per-seed candidate-minus-locked). Marginal medians and the marginal p50 delta are shown for context but are NOT the gate signal.

| pod | paired n | cand p50 | lock p50 | marg Δp50 | paired Δp10 | paired Δp50 | paired Δp90 | paired Δmean | paired Δstdev | cand bust | lock bust | Δbust | p50 reg | bust reg | PASS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :-: | :-: | :-: |
| C0 | 40 | -6075 | -10000 | 3925 | -20463 | 0 | 5055 | -4010.6 | 11514.0 | 25.0% | 65.0% | -40.0% | n | n | PASS |
| C1 | 40 | -9550 | 2488 | -12038 | -46373 | -11962 | 550 | -17030.5 | 18294.5 | 27.5% | 40.0% | -12.5% | Y | n | FAIL |

### Paired-diff resolution floor (the smallest regression the gate can resolve)

| pod | paired Δ min | paired Δ max | paired Δ stdev |
| --- | ---: | ---: | ---: |
| C0 | -42606 | 6700 | 11514.0 |
| C1 | -55044 | 1550 | 18294.5 |

## Decision

NOTHING AUTO-PROMOTES. A candidate that clears the FULL gate is only FLAGGED for a human MODIFY decision. `submissions/v_final.zip` remains the upload target unless a human explicitly overrides.

