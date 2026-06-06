# Candidate-vs-Locked Gate Result

Generated: `2026-05-31T01:17:13Z`
Verdict: **GATE_CLEAR_FLAG_FOR_HUMAN_MODIFY**

NOTHING AUTO-PROMOTES. GATE_CLEAR only FLAGS the candidate for a human MODIFY decision; submissions/v_final.zip stays the upload target unless a human explicitly overrides.

## Artifacts

- Candidate: `consult/artifacts/2026-05-31-scratch-improve/gate-harness/true_noop_candidate.zip` sha `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- Locked baseline: `submissions/v_final.zip` sha `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- Protected SHA OK (start AND end, both canonical zips): `True`
  - v_final start `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
  - v_final end   `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
  - best_green start `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
  - best_green end   `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`

Run config: hands/match `400`, seed base `142`, seeds `2`, pods `C0`, PYTHONHASHSEED `0`, p50_tol `0.0`, bust_tol `0.0`.

## Stage results (fail-fast cheap -> expensive)

| stage | name | result | exit |
| --- | --- | --- | ---: |
| 1 | validator | PASS | 0 |
| 1 | import_audit | PASS | 0 |
| 1 | leakage_audit | PASS | 0 |
| 2 | edge_tests | PASS | 0 |
| 2 | smoke_run | PASS | 0 |

_import_audit caveat: audits working-tree `src/`, not the candidate zip; the candidate zip's imports are covered by the engine validator's forbidden-module AST scan._

## Paired six-max pods (candidate vs locked, identical seeds)

Primary gate signal is the PAIRED-DIFF median (per-seed candidate-minus-locked). Marginal medians and the marginal p50 delta are shown for context but are NOT the gate signal.

| pod | paired n | cand p50 | lock p50 | marg Δp50 | paired Δp10 | paired Δp50 | paired Δp90 | paired Δmean | paired Δstdev | cand bust | lock bust | Δbust | p50 reg | bust reg | PASS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :-: | :-: | :-: |
| C0 | 2 | 12827 | -940 | 13767 | 5993 | 13767 | 21541 | 13767.0 | 13741.9 | 0.0% | 50.0% | -50.0% | n | n | PASS |

### Paired-diff resolution floor (the smallest regression the gate can resolve)

| pod | paired Δ min | paired Δ max | paired Δ stdev |
| --- | ---: | ---: | ---: |
| C0 | 4050 | 23484 | 13741.9 |

## Decision

NOTHING AUTO-PROMOTES. A candidate that clears the FULL gate is only FLAGGED for a human MODIFY decision. `submissions/v_final.zip` remains the upload target unless a human explicitly overrides.

