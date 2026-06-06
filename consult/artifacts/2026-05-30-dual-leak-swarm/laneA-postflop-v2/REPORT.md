# Lane A postflop v2 report — 2026-05-30

## Verdict

**P2_ALREADY_CLEAN.** Step 1 short-circuited the lane: the two alleged blockers did not produce decision-grade CI-excluding regressions at 50k scheduled hands, so no source minimization/new strategy patch was attempted. The existing P2 postflop diff is the Lane A candidate; only `tests/edge_cases/test_postflop_trap_v2.py` was added as a guard test.

Human promotion gate required; locked v_final.zip remains upload target unless explicitly overridden.

## Candidate

- Zip: `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/zips/v_postflop_trap_v2_p2_already_clean.zip`
- Zip sha256: `d042c977f7c29b01d3cc50f98d56edbf93c4de7b1e0ef7e73a76de1b6c6345bf`
- Prior P2 zip content comparison: all archive members byte-identical; zip sha differs due archive metadata/rebuild.
- Diff: `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/DIFF.patch`

## Protected artifact invariant

- Expected SHA: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Start and end `shasum -a 256` checks matched for `submissions/v_final.zip` and `submissions/best_green.zip`.

## Step 1 blocker retest — prior P2 zip, 50k scheduled

| Opponent | scheduled bb/100 | 95% CI | errors |
| --- | ---: | ---: | ---: |
| Pav skantbot7.9 | -0.794 | [-2.896, +1.352] | 0 / 0 |
| ref aggressor | +4.400 | [+0.400, +8.400] | 0 / 0 |

Decision: Pav 7.9 CI includes zero; aggressor is non-negative/positive. P2 source minimization skipped.

## Full eval H2H — new candidate zip, 50k scheduled

| Opponent/base | scheduled | actual | scheduled bb/100 | 95% CI | actual bb/100 | errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Toby master base 142 | 50000 | 6126 | -0.800 | [-4.400, +2.800] | -6.530 | 0 / 0 |
| Toby master base 242 | 50000 | 6182 | -1.200 | [-4.800, +2.400] | -9.706 | 0 / 0 |
| Pav skantbot7.9 | 50000 | 43828 | -0.543 | [-2.384, +1.284] | -0.620 | 0 / 0 |
| Pav skantbot7.6 | 50000 | 41080 | +5.472 | [+2.972, +7.891] | +6.660 | 0 / 0 |
| famadeo codex_holdem | 50000 | 19987 | -1.205 | [-4.200, +1.704] | -3.015 | 0 / 0 |
| neel actual | 50000 | 23936 | +19.271 | [+18.579, +19.823] | +40.254 | 0 / 0 |
| stoppedtime24 mybot | 50000 | 19829 | +18.756 | [+17.200, +19.956] | +47.294 | 0 / 0 |
| ref template | 50000 | 14059 | +20.000 | [+20.000, +20.000] | +71.129 | 0 / 0 |
| ref aggressor | 50000 | 1945 | +2.000 | [-2.000, +6.000] | +51.414 | 0 / 0 |
| ref mathematician | 50000 | 6900 | +20.000 | [+20.000, +20.000] | +144.928 | 0 / 0 |
| ref shark | 50000 | 14268 | +20.000 | [+20.000, +20.000] | +70.087 | 0 / 0 |
| ref_bot_2 | 50000 | 6900 | +20.000 | [+20.000, +20.000] | +144.928 | 0 / 0 |

Locked prior Toby evidence: base 142 `-14.0` CI `[-16.0, -12.0]`; base 242 `-16.6` CI `[-18.0, -15.0]`. Candidate full-eval deltas vs locked point estimates: base 142 `+13.2` bb/100, base 242 `+15.4` bb/100.

## Static/unit gates

| Gate | Result | Evidence |
| --- | --- | --- |
| leakage audit zip | PASS | `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/command_logs/final_audit_strategy_leakage_zip.log` |
| import audit | PASS — 0.063s, 33.6 MB | `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/command_logs/final_import_audit.log` |
| edge cases | PASS — 28 passed | `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/command_logs/final_pytest_edge_cases.log` |
| exploit_check | PASS — preflop 18.0 mbb/g, aggregate 5.65 mbb/g | `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/command_logs/final_exploit_check.log` |
| validator | PASS | `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/command_logs/final_validator.log` |
| smoke 200 | PASS — actual 136/200, reason `normal_bust: fewer than two bots remain; busted=template` | `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/command_logs/final_smoke_run_200.log` |

## Notes

- `src/preflop_lookup.py` was not touched.
- `ext/fullhouse-engine/` and public bot zips were not modified.
- Step 1 old-P2 and rebuilt-candidate zips have identical archive member contents; new zip name was used as required.
- Full-eval `ref aggressor` on the rebuilt zip was `+2.0` CI `[-2.0,+6.0]`; this differs from the Step 1 old-P2 run (`+4.4` CI `[+0.4,+8.4]`) despite byte-identical archive members, so report both. Neither is a CI-excluding bad regression.

Human promotion gate required; locked v_final.zip remains upload target unless explicitly overridden.
