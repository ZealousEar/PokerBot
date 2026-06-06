# G1-G11 Gauntlet Variance: canonical v_final.zip

- Generated: 2026-05-28T02:29:39Z
- Artifact: `submissions/v_final.zip` / `submissions/best_green.zip` sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- Execution worktree: `/Users/farhad/Code/PokerBot-gauntlet` @ `a00561cfadf18d3bc2b03ef2403e55346207670c`
- Canonical tree: `/Users/farhad/Code/PokerBot` @ `050b058d733b17418f68d3b846948b27caa13c40`
- Engine commit: `adc23b9813338d0e1e56e0158f18644b2b9ad234`
- Command policy: benchmarks and exploit check were artifact-bound with `--bot submissions/v_final.zip`; smoke used the real Docker sandbox; `smoke_timed` is a measurement wrapper for p99 latency only.
- Relative variance ranking uses max coefficient of variation across outcome/runtime-signal metrics for each gate. Fixed counts, caps, validator elapsed, and command wall time are excluded from ranking but retained in the full metric table. Mean/std are sample statistics over 5 repeats.

## Guardrails

- Preflight hashes ok: `True`
- Postflight hashes ok: `True`
- Any pip install requests surfaced: `none`

## Pass/Fail Matrix

| Gate | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Flip flag |
|---|---:|---:|---:|---:|---:|---|
| `audit_strategy_leakage` | PASS | PASS | PASS | PASS | PASS |  |
| `benchmark_ablate_overlay` | PASS | PASS | PASS | PASS | PASS |  |
| `benchmark_all_templates` | PASS | PASS | PASS | PASS | PASS |  |
| `benchmark_self_play_vs_prior` | PASS | PASS | PASS | PASS | PASS |  |
| `edge_cases` | PASS | PASS | PASS | PASS | PASS |  |
| `exploit_check` | PASS | PASS | PASS | PASS | PASS |  |
| `import_audit` | PASS | PASS | PASS | PASS | PASS |  |
| `smoke` | PASS | PASS | PASS | PASS | PASS |  |
| `validator` | PASS | PASS | PASS | PASS | PASS |  |

## Flip Flags

- No gate flipped pass/fail across the five repeats.

## Relative Variance Ranking

| Rank | Gate | Max relative std | Worst metric |
|---:|---|---:|---|
| 1 | `smoke` | 91.58% | `smoke_timed.v_final.max_ms` |
| 2 | `edge_cases` | 82.93% | `edge_cases.pytest_duration_s` |
| 3 | `import_audit` | 32.00% | `import_audit.cold_import_s` |
| 4 | `benchmark_all_templates` | 18.56% | `benchmark_all_templates.aggressor.ci_low` |
| 5 | `benchmark_ablate_overlay` | 0.00% | `` |
| 6 | `benchmark_self_play_vs_prior` | 0.00% | `` |
| 7 | `exploit_check` | 0.00% | `` |

## Numeric Metrics

| Gate | Metric | n | Mean ± std | Relative std |
|---|---|---:|---:|---:|
| `audit_strategy_leakage` | `audit_strategy_leakage.issue_count` | 5 | 0.000 ± 0.000 | 0.00% |
| `audit_strategy_leakage` | `audit_strategy_leakage.wall_duration_s` | 5 | 1.017 ± 0.009 | 0.92% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.bb_per_100` | 5 | -2.089 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.chip_delta` | 5 | -20,886.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_passive.bb_per_100` | 5 | -67.85 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_passive.chip_delta` | 5 | -113,106.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_passive.ci_high` | 5 | 20.13 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_passive.ci_low` | 5 | -153.62 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_passive.duration_s` | 5 | 39.80 ± 48.10 | 120.85% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_passive.hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_passive.requested_hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_pressure.bb_per_100` | 5 | -84.11 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_pressure.chip_delta` | 5 | -140,210.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_pressure.ci_high` | 5 | -32.16 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_pressure.ci_low` | 5 | -131.28 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_pressure.duration_s` | 5 | 12.99 ± 14.34 | 110.39% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_pressure.hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.loose_pressure.requested_hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.sharp_3bet_punisher.bb_per_100` | 5 | 14.99 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.sharp_3bet_punisher.chip_delta` | 5 | 24,970.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.sharp_3bet_punisher.ci_high` | 5 | 52.38 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.sharp_3bet_punisher.ci_low` | 5 | -17.38 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.sharp_3bet_punisher.duration_s` | 5 | 9.362 ± 10.60 | 113.25% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.sharp_3bet_punisher.hands` | 5 | 1,666.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.sharp_3bet_punisher.requested_hands` | 5 | 1,666.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.six_max_synthetic_mix.bb_per_100` | 5 | 80.83 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.six_max_synthetic_mix.chip_delta` | 5 | 134,665.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.six_max_synthetic_mix.ci_high` | 5 | 147.14 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.six_max_synthetic_mix.ci_low` | 5 | 18.29 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.six_max_synthetic_mix.duration_s` | 5 | 11.30 ± 14.24 | 126.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.six_max_synthetic_mix.hands` | 5 | 1,666.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.six_max_synthetic_mix.requested_hands` | 5 | 1,666.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_passive.bb_per_100` | 5 | 10.94 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_passive.chip_delta` | 5 | 18,243.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_passive.ci_high` | 5 | 36.77 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_passive.ci_low` | 5 | -11.61 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_passive.duration_s` | 5 | 7.786 ± 9.023 | 115.88% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_passive.hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_passive.requested_hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_pressure.bb_per_100` | 5 | 32.72 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_pressure.chip_delta` | 5 | 54,552.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_pressure.ci_high` | 5 | 69.04 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_pressure.ci_low` | 5 | -2.832 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_pressure.duration_s` | 5 | 9.374 ± 11.11 | 118.55% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_pressure.hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.blueprint_only.tight_pressure.requested_hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.gain_bb_per_100` | 5 | 32.53 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.wall_duration_s` | 5 | 229.29 ± 277.54 | 121.05% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.bb_per_100` | 5 | 30.44 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.chip_delta` | 5 | 304,365.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_passive.bb_per_100` | 5 | -67.85 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_passive.chip_delta` | 5 | -113,106.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_passive.ci_high` | 5 | 20.13 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_passive.ci_low` | 5 | -153.62 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_passive.duration_s` | 5 | 40.04 ± 47.80 | 119.36% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_passive.hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_passive.requested_hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_pressure.bb_per_100` | 5 | 116.89 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_pressure.chip_delta` | 5 | 194,850.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_pressure.ci_high` | 5 | 236.41 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_pressure.ci_low` | 5 | -4.379 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_pressure.duration_s` | 5 | 36.76 ± 47.01 | 127.87% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_pressure.hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.loose_pressure.requested_hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.sharp_3bet_punisher.bb_per_100` | 5 | 4.316 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.sharp_3bet_punisher.chip_delta` | 5 | 7,190.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.sharp_3bet_punisher.ci_high` | 5 | 69.86 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.sharp_3bet_punisher.ci_low` | 5 | -55.60 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.sharp_3bet_punisher.duration_s` | 5 | 16.29 ± 18.79 | 115.39% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.sharp_3bet_punisher.hands` | 5 | 1,666.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.sharp_3bet_punisher.requested_hands` | 5 | 1,666.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.six_max_synthetic_mix.bb_per_100` | 5 | 85.26 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.six_max_synthetic_mix.chip_delta` | 5 | 142,036.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.six_max_synthetic_mix.ci_high` | 5 | 160.91 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.six_max_synthetic_mix.ci_low` | 5 | 15.49 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.six_max_synthetic_mix.duration_s` | 5 | 10.48 ± 12.81 | 122.17% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.six_max_synthetic_mix.hands` | 5 | 1,666.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.six_max_synthetic_mix.requested_hands` | 5 | 1,666.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_passive.bb_per_100` | 5 | 10.94 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_passive.chip_delta` | 5 | 18,243.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_passive.ci_high` | 5 | 36.77 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_passive.ci_low` | 5 | -11.61 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_passive.duration_s` | 5 | 7.754 ± 8.964 | 115.60% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_passive.hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_passive.requested_hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_pressure.bb_per_100` | 5 | 33.08 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_pressure.chip_delta` | 5 | 55,152.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_pressure.ci_high` | 5 | 69.40 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_pressure.ci_low` | 5 | -2.022 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_pressure.duration_s` | 5 | 9.398 ± 11.08 | 117.91% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_pressure.hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_ablate_overlay` | `benchmark_ablate_overlay.with_overlay.tight_pressure.requested_hands` | 5 | 1,667.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.aggressor.bb_per_100` | 5 | 109.72 ± 12.06 | 10.99% |
| `benchmark_all_templates` | `benchmark_all_templates.aggressor.chip_delta` | 5 | 1,097,242.8 ± 120,566.3 | 10.99% |
| `benchmark_all_templates` | `benchmark_all_templates.aggressor.ci_high` | 5 | 159.26 ± 12.92 | 8.12% |
| `benchmark_all_templates` | `benchmark_all_templates.aggressor.ci_low` | 5 | 63.68 ± 11.82 | 18.56% |
| `benchmark_all_templates` | `benchmark_all_templates.aggressor.duration_s` | 5 | 210.70 ± 206.94 | 98.21% |
| `benchmark_all_templates` | `benchmark_all_templates.aggressor.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.aggressor.requested_hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.mathematician.bb_per_100` | 5 | 144.60 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.mathematician.chip_delta` | 5 | 1,446,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.mathematician.ci_high` | 5 | 145.76 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.mathematician.ci_low` | 5 | 143.41 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.mathematician.duration_s` | 5 | 118.91 ± 154.74 | 130.13% |
| `benchmark_all_templates` | `benchmark_all_templates.mathematician.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.mathematician.requested_hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.min_bb` | 5 | 15.00 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.ref_bot_2.bb_per_100` | 5 | 144.60 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.ref_bot_2.chip_delta` | 5 | 1,446,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.ref_bot_2.ci_high` | 5 | 145.76 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.ref_bot_2.ci_low` | 5 | 143.41 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.ref_bot_2.duration_s` | 5 | 109.47 ± 133.01 | 121.51% |
| `benchmark_all_templates` | `benchmark_all_templates.ref_bot_2.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.ref_bot_2.requested_hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.shark.bb_per_100` | 5 | 70.43 ± 0.158 | 0.22% |
| `benchmark_all_templates` | `benchmark_all_templates.shark.chip_delta` | 5 | 704,320.0 ± 1,583.0 | 0.22% |
| `benchmark_all_templates` | `benchmark_all_templates.shark.ci_high` | 5 | 71.48 ± 0.148 | 0.21% |
| `benchmark_all_templates` | `benchmark_all_templates.shark.ci_low` | 5 | 69.37 ± 0.173 | 0.25% |
| `benchmark_all_templates` | `benchmark_all_templates.shark.duration_s` | 5 | 47.29 ± 59.69 | 126.23% |
| `benchmark_all_templates` | `benchmark_all_templates.shark.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.shark.requested_hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.template.bb_per_100` | 5 | 71.82 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.template.chip_delta` | 5 | 718,200.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.template.ci_high` | 5 | 72.67 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.template.ci_low` | 5 | 70.94 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.template.duration_s` | 5 | 37.51 ± 20.14 | 53.68% |
| `benchmark_all_templates` | `benchmark_all_templates.template.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.template.requested_hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_all_templates` | `benchmark_all_templates.wall_duration_s` | 5 | 570.32 ± 623.25 | 109.28% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.min_bb` | 5 | 3.000 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v0_wired.bb_per_100` | 5 | 74.41 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v0_wired.chip_delta` | 5 | 744,050.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v0_wired.ci_high` | 5 | 74.99 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v0_wired.ci_low` | 5 | 73.86 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v0_wired.duration_s` | 5 | 42.39 ± 47.87 | 112.91% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v0_wired.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v0_wired.requested_hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v1_blueprint.bb_per_100` | 5 | 18.89 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v1_blueprint.chip_delta` | 5 | 188,950.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v1_blueprint.ci_high` | 5 | 26.99 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v1_blueprint.ci_low` | 5 | 10.75 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v1_blueprint.duration_s` | 5 | 46.57 ± 55.39 | 118.93% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v1_blueprint.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v1_blueprint.requested_hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v2_postflop.bb_per_100` | 5 | 18.89 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v2_postflop.chip_delta` | 5 | 188,950.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v2_postflop.ci_high` | 5 | 26.99 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v2_postflop.ci_low` | 5 | 10.75 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v2_postflop.duration_s` | 5 | 38.04 ± 34.64 | 91.04% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v2_postflop.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v2_postflop.requested_hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v3_hardened.bb_per_100` | 5 | 18.89 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v3_hardened.chip_delta` | 5 | 188,950.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v3_hardened.ci_high` | 5 | 26.99 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v3_hardened.ci_low` | 5 | 10.75 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v3_hardened.duration_s` | 5 | 32.45 ± 22.30 | 68.72% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v3_hardened.hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.v3_hardened.requested_hands` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `benchmark_self_play_vs_prior` | `benchmark_self_play_vs_prior.wall_duration_s` | 5 | 184.29 ± 188.34 | 102.20% |
| `edge_cases` | `edge_cases.pytest_duration_s` | 5 | 0.390 ± 0.323 | 82.93% |
| `edge_cases` | `edge_cases.tests_failed` | 5 | 0.000 ± 0.000 | 0.00% |
| `edge_cases` | `edge_cases.tests_passed` | 5 | 25.00 ± 0.000 | 0.00% |
| `edge_cases` | `edge_cases.wall_duration_s` | 5 | 1.211 ± 0.449 | 37.05% |
| `exploit_check` | `exploit_check.aggregate_mbb_g` | 5 | 7.400 ± 0.000 | 0.00% |
| `exploit_check` | `exploit_check.max_aggregate_mbb` | 5 | 200.00 ± 0.000 | 0.00% |
| `exploit_check` | `exploit_check.max_preflop_mbb` | 5 | 100.00 ± 0.000 | 0.00% |
| `exploit_check` | `exploit_check.preflop_mbb_g` | 5 | 18.00 ± 0.000 | 0.00% |
| `exploit_check` | `exploit_check.suite_size` | 5 | 20.00 ± 0.000 | 0.00% |
| `exploit_check` | `exploit_check.wall_duration_s` | 5 | 1.011 ± 0.006 | 0.57% |
| `import_audit` | `import_audit.cold_import_s` | 5 | 0.089 ± 0.029 | 32.00% |
| `import_audit` | `import_audit.rss_mb` | 5 | 32.12 ± 0.444 | 1.38% |
| `import_audit` | `import_audit.wall_duration_s` | 5 | 1.014 ± 0.010 | 0.98% |
| `smoke` | `smoke.chip_delta.template` | 5 | -14,500.0 ± 0.000 | 0.00% |
| `smoke` | `smoke.chip_delta.v_final` | 5 | 14,500.0 ± 0.000 | 0.00% |
| `smoke` | `smoke.duration_s` | 5 | 5.536 ± 1.876 | 33.89% |
| `smoke` | `smoke.expected_hands` | 5 | 200.00 ± 0.000 | 0.00% |
| `smoke` | `smoke.n_hands` | 5 | 200.00 ± 0.000 | 0.00% |
| `smoke` | `smoke.wall_duration_s` | 5 | 6.245 ± 2.182 | 34.94% |
| `smoke` | `smoke_timed.chip_delta.template` | 5 | -10,000.0 ± 0.000 | 0.00% |
| `smoke` | `smoke_timed.chip_delta.v_final` | 5 | 10,000.0 ± 0.000 | 0.00% |
| `smoke` | `smoke_timed.duration_s` | 5 | 3.390 ± 1.464 | 43.20% |
| `smoke` | `smoke_timed.n_hands` | 5 | 136.00 ± 0.000 | 0.00% |
| `smoke` | `smoke_timed.template.count` | 5 | 135.00 ± 0.000 | 0.00% |
| `smoke` | `smoke_timed.template.max_ms` | 5 | 31.64 ± 15.43 | 48.79% |
| `smoke` | `smoke_timed.template.mean_ms` | 5 | 9.751 ± 1.959 | 20.10% |
| `smoke` | `smoke_timed.template.p50_ms` | 5 | 10.06 ± 0.592 | 5.88% |
| `smoke` | `smoke_timed.template.p95_ms` | 5 | 21.87 ± 8.593 | 39.30% |
| `smoke` | `smoke_timed.template.p99_ms` | 5 | 28.79 ± 14.87 | 51.64% |
| `smoke` | `smoke_timed.v_final.count` | 5 | 71.00 ± 0.000 | 0.00% |
| `smoke` | `smoke_timed.v_final.max_ms` | 5 | 37.77 ± 34.59 | 91.58% |
| `smoke` | `smoke_timed.v_final.mean_ms` | 5 | 10.01 ± 1.553 | 15.51% |
| `smoke` | `smoke_timed.v_final.p50_ms` | 5 | 10.96 ± 4.441 | 40.52% |
| `smoke` | `smoke_timed.v_final.p95_ms` | 5 | 21.20 ± 6.705 | 31.63% |
| `smoke` | `smoke_timed.v_final.p99_ms` | 5 | 26.41 ± 15.17 | 57.44% |
| `smoke` | `smoke_timed.wall_duration_s` | 5 | 4.029 ± 1.757 | 43.61% |
| `validator` | `validator.error_count` | 5 | 0.000 ± 0.000 | 0.00% |
| `validator` | `validator.max_test_elapsed_s` | 5 | 0.000 ± 0.000 | 223.61% |
| `validator` | `validator.test_count` | 5 | 4.000 ± 0.000 | 0.00% |
| `validator` | `validator.tests_passed` | 5 | 4.000 ± 0.000 | 0.00% |
| `validator` | `validator.total_test_elapsed_s` | 5 | 0.000 ± 0.000 | 223.61% |
| `validator` | `validator.wall_duration_s` | 5 | 1.009 ± 0.003 | 0.33% |

## Run Logs

- `run_1/` manifest: `run_1/run_manifest.json` passed=`True`
- `run_2/` manifest: `run_2/run_manifest.json` passed=`True`
- `run_3/` manifest: `run_3/run_manifest.json` passed=`True`
- `run_4/` manifest: `run_4/run_manifest.json` passed=`True`
- `run_5/` manifest: `run_5/run_manifest.json` passed=`True`
