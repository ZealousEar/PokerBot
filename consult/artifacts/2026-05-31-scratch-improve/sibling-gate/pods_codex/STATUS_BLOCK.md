## 2026-05-31T00:53:10Z · P1-TRAP-SIXMAX-PREVALENCE · TRAP_PREVALENCE_DANGEROUS
- Goal: Estimate whether Toby `master` and Mehedi `mybot` H2H RED matchups translate into dangerous six-max qualifier pods for locked `submissions/v_final.zip`.
- Artifact: `submissions/v_final.zip` sha before/after `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` / `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`; `best_green.zip` before/after `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` / `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Runner: artifact-bound `ext/fullhouse-engine/sandbox/match.py`, `USE_DOCKER=False`, 40 seeds/composition x 400 scheduled hands.
- Composition table:

| composition | color | p10 | p25 | p50 | p75 | p90 | mean | stdev | bust rate | hero err | opp err | p99 ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C0_BASELINE_RECHECK | AMBER | -10000 | 774 | 18875 | 24175 | 31880 | 14342 | 16693 | 22.5% | 0.000% | 0.000% | 5.796 |
| C1_SINGLE_TOBY_WEAK_FIELD | CRITICAL | -10000 | -10000 | -10000 | -4853 | 23372 | -1997 | 14592 | 75.0% | 0.000% | 0.000% | 22.957 |

- Comparison: baseline already `AMBER` with p50 `18875`; single Toby = `CRITICAL`; single Mehedi = `None`; Toby+Mehedi = `None`; driver = `early_busts`.
- Upload recommendation: `SHIP_LOCKED_ARTIFACT` unless there is already a fully-gated replacement; never overwrite `v_final.zip` or `best_green.zip`.
- Outputs: `consult/artifacts/2026-05-31-scratch-improve/sibling-gate/pods_codex/TRAP_SIXMAX_REPORT.md`, `consult/artifacts/2026-05-31-scratch-improve/sibling-gate/pods_codex/RESULTS.json`, `consult/artifacts/2026-05-31-scratch-improve/sibling-gate/pods_codex/matches.jsonl`.

