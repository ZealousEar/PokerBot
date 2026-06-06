# Deployed Qualifier-II Gauntlet Report

Date: 2026-06-03  
Target: `submissions/v_qual2_ship_d54640e0.zip`  
Verdict: **RED for finals promotion / not stronger than SIMPLE on this evidence**

## Bottom Line

The deployed Qualifier-II zip is preserved locally and lineage-correct:
`d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421`.
It is byte-identical to `consult/artifacts/2026-06-03-qual2-patch/v_qual2_SHIP_bestgreen+fix.zip` and different from the alternate
`v_qual2_stackoff_fix.zip` (`0ec835b6...`).

It is **runtime-safe on validator and Docker smoke**: validator passed, Docker smoke played 200/200 hands with zero errors, extracted import was 0.0431s / 22.3 MB. It is **not safer/stronger than SIMPLE e4b4a8f1** on the fresh evidence:

- Direct H2H: deployed lost to SIMPLE over 8,954 played hands, `-51.54 bb/100`; per-match BB delta `-92.31`, 95% CI `[-96.08, -88.02]`; zero errors for both.
- Comparable reference/synthetic suite: deployed trails SIMPLE on 8/12 opponents by scheduled bb/100, including 4/5 bundled reference bots.
- Edge/probe failure: deployed all-ins a dominated under-boat / near-dead full-house state (`Qc9h` on `Kd Ks Qs Qd 5c`) for 100% current-stack commitment.

## Artifact Lineage

| artifact | size | sha256 | layout summary |
|---|---:|---|---|
| `submissions/best_green.zip` | 28,208 | `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` | root `bot.py`, 9 `src/*.py`, includes 3 `.npz` |
| `submissions/v_final.zip` | 28,208 | `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` | SIMPLE baseline, byte-identical to `best_green.zip` |
| `submissions/v_qual2_ship_d54640e0.zip` | 18,492 | `d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421` | deployed target, root `bot.py`, 9 `src/*.py`, only `data/.gitkeep` |
| `submissions/v_final_reaudit.zip` | 28,208 | `9a3b812ec8f44b55d6d2f7dfee0a89d7d187de3b572e55932bbcd89d1dacc0b0` | same size/layout class as SIMPLE |
| `submissions/v_final_pre_x1.zip` | 28,534 | `5d65561e522f595173408bd9a8ffbbd3246646edf36c897f30baab9776eb7cef` | pre-X1 snapshot |
| `submissions/v3_hardened.zip` | 28,110 | `7caa4f6346f76191c83e8716a2ab4a3a516033f069d0a1058341ef2bc21dbec5` | gate snapshot |
| `submissions/v2_postflop.zip` | 28,110 | `348723049f8ba3e99e36c01ec703681c0bc41289431d956def393ef2e8da6b57` | gate snapshot |
| `submissions/v1_blueprint.zip` | 9,289 | `f729b9ad311f6a5dc9b276f41302c5fcb7c16f288976d271be3d5764c5bede3c` | gate snapshot |
| `submissions/v0_wired.zip` | 5,682 | `0792be72e472c5a36608d3e9fafcada3b0a6a80da3f7f55c9b21fa4972c38112` | gate snapshot |
| `submissions/v0_scaffold.zip` | 5,098 | `7df4e70240f18338860b03a4b87c3b09ba810609d815e2509ba23e14b986ffb3` | scaffold snapshot |

Extracted deployed bot: `consult/artifacts/2026-06-03-deployed-gauntlet/extracted/v_qual2_ship_d54640e0/`

Key extracted file hashes:

- root `bot.py`: `70f88f16d12193da9516807a6ac3835d95a67060e4b9d6b24868807fcb2de999`
- `src/bot.py`: `06d09cd1c9eede311ffed8b4ac09616c101bffb98ebe72362e70a683e5c988dc`
- `src/postflop.py`: `7f9238bc0e6975a71be5426dd8f4509f189995198bbb8e4c873b0da84fd42ce0`

## Package And Source Inspection

- Root `bot.py` exists; no extra root `.py`; no `.py` under `data/`; no symlinks/traversal found.
- Deployed zip bundles no `.npz`; `data/` contains only `.gitkeep`.
- Source scan over extracted `bot.py` + `src/*.py`: **no forbidden imports/calls** by AST scan.
- Data load evidence: no `np.load`, no `.npz`, no `open(` in extracted deployed source. Only data reference is `BOT_DATA_DIR` fallback in `src/bot.py`.
- Runtime imports are Python tables + `eval7`; no packaged data dependency was proven.

## Command Results

| command | rc | result |
|---|---:|---|
| `.venv/bin/python tools/import_audit.py` | 0 | **PASS**, but canonical `src/` only: cold import ~0.000s / 10.3 MB |
| extracted deployed import probe | 0 | **PASS**, 0.0431s / 22.3 MB, `decide` present |
| `.venv/bin/python -m pytest tests/edge_cases -x` | 1 | **FAIL**, deployed zip large-commits `near_dead_postflop_commitment` with `{'action': 'all_in'}` |
| `.venv/bin/python ext/fullhouse-engine/sandbox/validator.py submissions/v_qual2_ship_d54640e0.zip --json` | 0 | **PASS**, 4/4 validator states |
| `.venv/bin/python tools/audit_strategy_leakage.py --zip submissions/v_qual2_ship_d54640e0.zip` | 1 | **FAIL**, literal scanner flags `snapshot`, `branch`, `seed`, `aggressor`, `v1_blueprint` strings |
| `.venv/bin/python tools/smoke_run.py --zip submissions/v_qual2_ship_d54640e0.zip --hands 200 --opponent template --seed 42` | 0 | **PASS**, 200/200, hero errors `[]`, chip delta `+4050` |
| `.venv/bin/python tools/h2h.py --bot-a submissions/v_qual2_ship_d54640e0.zip --bot-b submissions/v_final.zip --hands 10000 --paired-seed-base 42 --match-len 200` | 0 | **RUN PASS / STRATEGY RED**, deployed `-51.54 bb/100`, CI excludes 0 against SIMPLE |

Important limitation: current canonical `tools/benchmark.py` and `tools/exploit_check.py` are TODO stubs and cannot provide official G9-G11 or LBR artifact-bound evidence in this checkout. Smallest next command for that specific blocked criterion is to run the zip-aware release worktree tools:

```bash
cd /Users/farhad/Code/PokerBot-gauntlet
.venv/bin/python tools/benchmark.py --all-templates --hands 10000 --bot ../PokerBot/submissions/v_qual2_ship_d54640e0.zip --paired-seed-base 42
.venv/bin/python tools/exploit_check.py --bot ../PokerBot/submissions/v_qual2_ship_d54640e0.zip --max-preflop-mbb 100 --max-aggregate-mbb 200
```

## Opponent Gauntlet

Method: `tools/deployed_artifact_gauntlet.py` drives `ext/fullhouse-engine/sandbox/match.py` directly. Each opponent used 3 seeds x 2 seat orientations x 200 hands = 1,200 scheduled hands. CI is bootstrap over the six paired-orientation samples; actual hands are often much lower because early bust ends matches. Treat this as diagnostic, not acceptance-grade.

| opponent | deployed sched bb/100 | SIMPLE sched bb/100 | deployed - SIMPLE | deployed CI | actual hands deployed/simple |
|---|---:|---:|---:|---|---:|
| template | +2.33 | +50.00 | -47.67 | [-13.04, +15.50] | 1200 / 843 |
| aggressor | +33.33 | +0.00 | +33.33 | [+0.00, +50.00] | 81 / 61 |
| mathematician | +26.50 | +50.00 | -23.50 | [+20.42, +32.96] | 1200 / 415 |
| shark | +10.21 | +50.00 | -39.79 | [-24.00, +39.67] | 921 / 810 |
| ref_bot_2 | +26.50 | +50.00 | -23.50 | [+20.33, +33.42] | 1200 / 415 |
| all_in_maniac | +16.67 | -16.67 | +33.33 | [-16.67, +50.00] | 58 / 54 |
| tight_passive | +35.45 | +50.00 | -14.55 | [+20.91, +47.25] | 1085 / 601 |
| loose_passive | +50.00 | -16.67 | +66.67 | [+50.00, +50.00] | 146 / 131 |
| tight_aggressive | +7.96 | +50.00 | -42.04 | [-25.83, +37.54] | 839 / 945 |
| loose_aggressive | -16.67 | -16.67 | +0.00 | [-50.00, +16.67] | 358 / 89 |
| pot_odds_threshold | +50.00 | -16.67 | +66.67 | [+50.00, +50.00] | 282 / 131 |
| river_value_threshold | +28.75 | +50.00 | -21.25 | [+25.25, +31.38] | 1200 / 811 |

Interpretation: deployed gains against some crude pressure/passive synthetic bots, but loses substantial ground versus most bundled references and loses decisively to SIMPLE directly. This is not evidence of a stronger finals bot.

## Direct Probes

All probe actions had legal shapes and no runner errors. Latencies stayed under 8 ms after warmup. Key outcomes:

| probe | action | verdict |
|---|---|---|
| `warmup_exception` | `{"ok": true}` | pass |
| `near_drawing_dead_stackoff` | `fold` | pass for the original two-pair leak shape |
| `dominated_underboat_near_dead_commitment` | `all_in` | **fail: 100% stack commit with dominated under-boat class** |
| `multiway_wet_board` | `call` | legal; strategic multiway risk remains |
| `river_facing_large_bet` | `fold` | pass |
| `turn_jam_poor_pot_odds` | `fold` | pass |
| `blind_defense_vs_3bet` | `fold` | legal; likely over-tight but not crash/legality failure |
| `all_in_side_pot_state` | `all_in` | legal with AA; side-pot path did not crash |
| `contradictory_legal_actions` | `check` | legal-shape only; contradictory synthetic state |
| `raise_amount_min_max_ambiguity` | `all_in` | pass: no illegal raise-to-stack |
| `timeout_expensive_equity_branch` | `call` x30 | pass: max 7.25 ms |

## 10 Diagnostic Hands / States

| # | type | id | signal |
|---:|---|---|---|
| 1 | probe | `dominated_underboat_near_dead_commitment` | `Qc9h` on `Kd Ks Qs Qd 5c`, facing 8,900 into 17,800 with stack 9,100 -> `all_in`; this is the clearest finals blocker. |
| 2 | hand | `deployed_all_in_maniac_s43_o1_h0000` | `4s4h` called all-in preflop, lost full stack; hero delta `-10000`. |
| 3 | hand | `deployed_tight_aggressive_s44_o0_h0117` | `JhJc` stacks off and loses on `4d 9s 4h 7c Ah`; hero delta `-9775`. |
| 4 | hand | `deployed_aggressor_s42_o1_h0020` | `AhKc` raise war/all-in, high card at showdown; hero delta `-9460`. |
| 5 | hand | `deployed_all_in_maniac_s42_o0_h0005` | `QhTd` calls all-in, high card; hero delta `-9250`. |
| 6 | hand | `deployed_shark_s44_o0_h0117` | `JhJc` call/all-in line loses nearly full stack; hero delta `-9150`. |
| 7 | hand | `deployed_shark_s42_o1_h0062` | `QcQh` all-in on paired ace board, loses; hero delta `-8800`. |
| 8 | hand | `deployed_template_s42_o1_h0062` | same `QcQh` paired ace-board all-in pattern versus template; hero delta `-8500`. |
| 9 | hand | `deployed_tight_aggressive_s43_o1_h0139` | `JhJc` repeated raise/all-in on paired king board; hero delta `-7900`. |
| 10 | hand | `deployed_loose_aggressive_s42_o0_h0011` | `Ac8s` check-call/call/call river line on paired board; hero delta `-7390`. |

Full diagnostic hand CSV: `consult/artifacts/2026-06-03-deployed-gauntlet/results/diagnostic_hands.csv`.

## Failure Taxonomy

- **Strategy leak:** dominated full-house / under-boat gate is unsafe. The `_can_commit` fix handles flush/paired/safe branches but still lets some boat-looking hands commit when their boat rank is dominated by obvious board-pair combinations.
- **Strategy leak:** HU pressure and raise-war discipline remains weak. Direct H2H versus SIMPLE shows repeated full-stack losses without runtime errors.
- **Legality/runtime:** no runtime crash, timeout, warmup, or package-layout failure observed. Validator and Docker smoke passed.
- **Policy/tooling:** literal strategy-leakage audit fails on comments/strings. AST scan found no forbidden import/call and no identity branch was proven, but the current gate command exits 1 and must be resolved or explicitly waived before finals.
- **Benchmark limitation:** official artifact-bound G9-G11 and LBR are blocked in this checkout by stub `benchmark.py` / `exploit_check.py`. The wrapper suite is diagnostic, not a replacement for the release worktree benchmark ladder.
- **Lineage confusion:** canonical `src/` is not the deployed strategy. All strength/safety claims here target the zip hash above, not current-main `src/`.

## Required Fixes Before Finals

1. Add a board-nuttedness gate for full houses/boats: distinguish top boat/quads from dominated under-boats on double-paired boards; add a regression state for `Qc9h` on `Kd Ks Qs Qd 5c`.
2. Re-run direct deployed-vs-SIMPLE H2H after any fix; do not ship a candidate that loses to SIMPLE with CI excluding zero unless there is stronger six-max evidence explaining why.
3. Re-run six-max pods, not just HU, because this bot is tuned for 6-max and HU probes can distort EV. Still, HU failures are valid leak detectors.
4. Resolve the leakage audit failure either by removing flagged strategy-source strings/comments or changing the scanner to ignore comments/docstrings with an explicit policy decision.
5. Run the release worktree zip-aware `benchmark.py` and `exploit_check.py` on the exact zip before any finals upload.

## Machine-Readable Artifacts

- `results/deployed_gauntlet_results.json`
- `results/submission_zip_inventory.json`
- `results/source_audit.json`
- `results/probe_results.json`
- `results/match_results.json`
- `results/comparison_vs_simple.csv`
- `results/comparison_vs_simple.json`
- `results/command_summary.json`
- `results/diagnostic_hands.csv`

No preserved submission zip was modified. No `src/` file was edited. No `STATUS.md` entry was appended because the deployed gauntlet is RED.
