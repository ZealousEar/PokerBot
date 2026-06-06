# Trap Six-Max Prevalence Report

Verdict: **TRAP_PREVALENCE_DANGEROUS**

Generated: `2026-05-29T15:45:54Z`
Runner: `ext/fullhouse-engine/sandbox/match.py` via lane-local script; `USE_DOCKER=False`.
Hero artifact: `submissions/v_final.zip`
Hero SHA before: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
Hero SHA after: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
Schedule: `400` hands x `100` seeds per composition, seed base `142`.

## Composition Table

| composition | seats | color | p10 | p50 | p90 | mean | stdev | bust rate | hero errors | p99 ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C0_BASELINE_RECHECK | hero, template, aggressor, mathematician, shark, ref_bot_2 | CRITICAL | -10000 | -10000 | 13457 | -3387 | 10364 | 68.0% | 0/21211 (0.000%) | 23.752 |
| C1_SINGLE_TOBY_WEAK_FIELD | hero, toby_master, template, mathematician, shark, ref_bot_2 | AMBER | -10000 | 10536 | 32486 | 9520 | 18384 | 36.0% | 0/36961 (0.000%) | 18.108 |
| C2_SINGLE_MEHEDI_WEAK_FIELD | hero, mehedi_mybot, template, mathematician, shark, ref_bot_2 | RED | -10000 | -118 | 15183 | 1454 | 10148 | 29.0% | 0/40358 (0.000%) | 20.982 |
| C3_TOBY_MEHEDI_WEAK_FIELD | hero, toby_master, mehedi_mybot, template, shark, ref_bot_2 | CRITICAL | -10000 | -10000 | 15674 | -306 | 12857 | 52.0% | 0/32092 (0.000%) | 26.848 |
| C4_PUBLIC_NIGHTMARE | hero, toby_master, mehedi_mybot, famadeo, neel, pav_skantbot7_9 | RED | -10000 | -1082 | 17234 | 661 | 13182 | 42.0% | 0/33992 (0.000%) | 7.748 |
| C5_TRAP_HEAVY | hero, toby_master, mehedi_mybot, stoppedtime24_mybot, pav_skantbot7_9, shark | RED | -10000 | -1832 | 13596 | 327 | 12195 | 42.0% | 0/32038 (0.000%) | 15.642 |
| C6_DOMINIC_RENAME_COMPARISON | hero, toby_master, old_dominic, famadeo, neel, shark | CRITICAL | -10000 | -10000 | 22496 | 881 | 14103 | 52.0% | 0/30819 (0.000%) | 18.410 |
| C7_TWO_TOBY_CLONES | hero, toby_master_clone1, toby_master_clone2, template, shark, ref_bot_2 | CRITICAL | -10000 | -10000 | 31512 | 2405 | 18710 | 62.0% | 0/29937 (0.000%) | 22.965 |

## Comparison

- Baseline context: `C0_BASELINE_RECHECK` was already `CRITICAL` with p50 `-10000`; flip flags below are baseline-relative and cannot mean a healthy pod became unhealthy.
- Does one Toby seat alone flip the pod? **False** (`AMBER`); incremental result: Toby alone improved the median versus C0 but kept the left tail AMBER.
- Does one Mehedi seat alone flip the pod? **False** (`RED`); incremental result: Mehedi alone produced a RED median near breakeven with a large bust tail.
- Do Toby+Mehedi together flip the pod? **False** (`CRITICAL`); incremental result: together they produced a CRITICAL pod.
- Danger driver: **early_busts**.

## Bust Diagnostics

- `C0_BASELINE_RECHECK`: 68 busts; median bust hand `62`; showdown busts `68`.
- `C1_SINGLE_TOBY_WEAK_FIELD`: 36 busts; median bust hand `82`; showdown busts `36`.
- `C2_SINGLE_MEHEDI_WEAK_FIELD`: 29 busts; median bust hand `165`; showdown busts `29`.
- `C3_TOBY_MEHEDI_WEAK_FIELD`: 52 busts; median bust hand `82`; showdown busts `52`.
- `C4_PUBLIC_NIGHTMARE`: 42 busts; median bust hand `105`; showdown busts `42`.
- `C5_TRAP_HEAVY`: 42 busts; median bust hand `96`; showdown busts `42`.
- `C6_DOMINIC_RENAME_COMPARISON`: 52 busts; median bust hand `118`; showdown busts `52`.
- `C7_TWO_TOBY_CLONES`: 62 busts; median bust hand `53`; showdown busts `62`.

## Upload Recommendation

**SHIP_LOCKED_ARTIFACT** unless there is already a fully-gated replacement. Never overwrite `submissions/v_final.zip`.

## Notes

- `chip_delta` is the hero final stack minus the 10,000 starting stack for each scheduled 400-hand match.
- `actual_hands` is stored per match in `matches.jsonl` and summarized in `RESULTS.json`; early table collapse can make it lower than scheduled.
- Opponent zips used by this lane are copied or built only under `opponent_zips/` in this output directory.

