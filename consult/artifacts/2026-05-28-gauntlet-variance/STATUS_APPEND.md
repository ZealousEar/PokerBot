## 2026-05-28T02:29:39Z · G1-G11 variance characterization · GREEN
- Goal: Characterize gate-level variance across five repeats of the canonical `submissions/v_final.zip` gauntlet without modifying the artifact.
- Artifact guardrail: `submissions/v_final.zip` and `submissions/best_green.zip` stayed at sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`; `ext/fullhouse-engine` stayed at `adc23b9813338d0e1e56e0158f18644b2b9ad234`.
- Runs: `consult/artifacts/2026-05-28-gauntlet-variance/run_1` through `run_5`; summary: `consult/artifacts/2026-05-28-gauntlet-variance/SUMMARY.md`.
- Pass/fail flips: none.
- All-template bb/100 mean ± std: template +71.82 ± 0.00, aggressor +109.72 ± 12.06, mathematician +144.60 ± 0.00, shark +70.43 ± 0.16, ref_bot_2 +144.60 ± 0.00.
- Ablation / ratchet / LBR / smoke: benchmark_ablate_overlay.gain_bb_per_100 32.53 ± 0.000, exploit_check.preflop_mbb_g 18.00 ± 0.000, exploit_check.aggregate_mbb_g 7.400 ± 0.000, smoke.chip_delta.v_final 14,500.0 ± 0.000, smoke_timed.v_final.p99_ms 26.41 ± 15.17; ratchet: v0_wired +74.41 ± 0.00, v1_blueprint +18.89 ± 0.00, v2_postflop +18.89 ± 0.00, v3_hardened +18.89 ± 0.00.
- Relative variance leader: `smoke` via `smoke_timed.v_final.max_ms` at 91.58% relative std.
- Source / policy anchor: `AGENTS.md` benchmark variance policy and `PROMPT.shared.md` artifact-bound G1-G11 gauntlet.
- Next action: keep `v_final.zip` locked; use the variance table as the baseline for any patch-window candidate comparison.
