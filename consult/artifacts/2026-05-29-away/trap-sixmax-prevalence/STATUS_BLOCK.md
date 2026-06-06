## 2026-05-29T15:45:54Z · P1-TRAP-SIXMAX-PREVALENCE · TRAP_PREVALENCE_DANGEROUS
- Goal: Estimate whether Toby `master` and Mehedi `mybot` H2H RED matchups translate into dangerous six-max qualifier pods for locked `submissions/v_final.zip`.
- Artifact: `submissions/v_final.zip` sha before/after `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` / `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`; `best_green.zip` before/after `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` / `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Runner: artifact-bound `ext/fullhouse-engine/sandbox/match.py`, `USE_DOCKER=False`, 100 seeds/composition x 400 scheduled hands.
- Composition table:

| composition | color | p10 | p25 | p50 | p75 | p90 | mean | stdev | bust rate | hero err | opp err | p99 ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C0_BASELINE_RECHECK | CRITICAL | -10000 | -10000 | -10000 | 5462 | 13457 | -3387 | 10364 | 68.0% | 0.000% | 0.000% | 23.752 |
| C1_SINGLE_TOBY_WEAK_FIELD | AMBER | -10000 | -10000 | 10536 | 24786 | 32486 | 9520 | 18384 | 36.0% | 0.000% | 0.000% | 18.108 |
| C2_SINGLE_MEHEDI_WEAK_FIELD | RED | -10000 | -10000 | -118 | 8637 | 15183 | 1454 | 10148 | 29.0% | 0.000% | 0.000% | 20.982 |
| C3_TOBY_MEHEDI_WEAK_FIELD | CRITICAL | -10000 | -10000 | -10000 | 8184 | 15674 | -306 | 12857 | 52.0% | 0.000% | 0.000% | 26.848 |
| C4_PUBLIC_NIGHTMARE | RED | -10000 | -10000 | -1082 | 6062 | 17234 | 661 | 13182 | 42.0% | 0.000% | 0.000% | 7.748 |
| C5_TRAP_HEAVY | RED | -10000 | -10000 | -1832 | 6616 | 13596 | 327 | 12195 | 42.0% | 0.000% | 0.000% | 15.642 |
| C6_DOMINIC_RENAME_COMPARISON | CRITICAL | -10000 | -10000 | -10000 | 8581 | 22496 | 881 | 14103 | 52.0% | 0.000% | 0.000% | 18.410 |
| C7_TWO_TOBY_CLONES | CRITICAL | -10000 | -10000 | -10000 | 11372 | 31512 | 2405 | 18710 | 62.0% | 0.000% | 0.000% | 22.965 |

- Comparison: baseline already `CRITICAL` with p50 `-10000`; single Toby = `AMBER`; single Mehedi = `RED`; Toby+Mehedi = `CRITICAL`; driver = `early_busts`.
- Upload recommendation: `SHIP_LOCKED_ARTIFACT` unless there is already a fully-gated replacement; never overwrite `v_final.zip` or `best_green.zip`.
- Outputs: `consult/artifacts/2026-05-29-away/trap-sixmax-prevalence/TRAP_SIXMAX_REPORT.md`, `consult/artifacts/2026-05-29-away/trap-sixmax-prevalence/RESULTS.json`, `consult/artifacts/2026-05-29-away/trap-sixmax-prevalence/matches.jsonl`.

