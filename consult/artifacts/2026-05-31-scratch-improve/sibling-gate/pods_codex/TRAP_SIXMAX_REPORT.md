# Trap Six-Max Prevalence Report

Verdict: **TRAP_PREVALENCE_DANGEROUS**

Generated: `2026-05-31T00:53:10Z`
Runner: `ext/fullhouse-engine/sandbox/match.py` via lane-local script; `USE_DOCKER=False`.
Hero artifact: `consult/artifacts/2026-05-31-scratch-improve/sibling-gate/codex.zip`
Hero SHA before: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
Hero SHA after: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
Schedule: `400` hands x `40` seeds per composition, seed base `142`.

## Composition Table

| composition | seats | color | p10 | p50 | p90 | mean | stdev | bust rate | hero errors | p99 ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C0_BASELINE_RECHECK | hero, template, aggressor, mathematician, shark, ref_bot_2 | AMBER | -10000 | 18875 | 31880 | 14342 | 16693 | 22.5% | 0/17702 (0.000%) | 5.796 |
| C1_SINGLE_TOBY_WEAK_FIELD | hero, toby_master, template, mathematician, shark, ref_bot_2 | CRITICAL | -10000 | -10000 | 23372 | -1997 | 14592 | 75.0% | 0/8923 (0.000%) | 22.957 |

## Comparison

- Baseline context: `C0_BASELINE_RECHECK` was already `AMBER` with p50 `18875`; flip flags below are baseline-relative and cannot mean a healthy pod became unhealthy.
- Does one Toby seat alone flip the pod? **True** (`CRITICAL`); incremental result: Toby alone improved the median versus C0 but kept the left tail AMBER.
- Does one Mehedi seat alone flip the pod? **None** (`None`); incremental result: Mehedi alone produced a RED median near breakeven with a large bust tail.
- Do Toby+Mehedi together flip the pod? **None** (`None`); incremental result: together they produced a CRITICAL pod.
- Danger driver: **early_busts**.

## Bust Diagnostics

- `C0_BASELINE_RECHECK`: 9 busts; median bust hand `32`; showdown busts `9`.
- `C1_SINGLE_TOBY_WEAK_FIELD`: 30 busts; median bust hand `36`; showdown busts `30`.

## Upload Recommendation

**SHIP_LOCKED_ARTIFACT** unless there is already a fully-gated replacement. Never overwrite `submissions/v_final.zip`.

## Notes

- `chip_delta` is the hero final stack minus the 10,000 starting stack for each scheduled 400-hand match.
- `actual_hands` is stored per match in `matches.jsonl` and summarized in `RESULTS.json`; early table collapse can make it lower than scheduled.
- Opponent zips used by this lane are copied or built only under `opponent_zips/` in this output directory.

