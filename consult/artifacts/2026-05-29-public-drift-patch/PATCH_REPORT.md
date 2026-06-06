NO_PATCH

# Public drift patch report — 2026-05-29

## Decision

**NO_PATCH.** Phase A reproduced and localized the Toby `master` deficit, but the material clusters are river/postflop heuristic failures in `src/postflop.py:38-53`, which is explicitly outside the allowed scope (`New postflop EV veto` forbidden). The allowed seams did not explain a material share of the loss. Phase B was not entered and no candidate zip was created.

Promotion recommendation: **keep `submissions/v_final.zip` locked**. Do not promote anything.

## Artifact and invariant status

- Canonical artifact hash verified: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- `submissions/v_final.zip`: unchanged
- `submissions/best_green.zip`: unchanged
- `submissions/v_public_drift_candidate.zip`: not created by this run
- `ext/fullhouse-engine/`: read-only; not edited
- `data/*.npz`: not edited
- Canonical `tests/edge_cases/`: not edited

## Diff summary

No strategy/source candidate diff exists. Files written only under `consult/artifacts/2026-05-29-public-drift-patch/`:

- `instrumented_h2h.py` — artifact-local decision-cluster probe using a `BotProcess.act()` monkey-patch.
- `logs/toby_master_decisions_s142.jsonl` — hero decision records.
- `logs/toby_master_instrumented_s142.json` — full probe result and clusters.
- `logs/toby_master_clusters_s142.json` — compact cluster summary.
- `opponent_zips/toby_master.zip` — packaged Toby opponent for the probe.
- `CLUSTER_NOTES.md`, `PATCH_REPORT.md`, `RESULTS.json` — required outputs.

## Command log

Commands were run from `/Users/farhad/Code/PokerBot` using `.venv/bin/python` for project Python work.

1. Read supplied evidence:
   - `consult/artifacts/2026-05-29-public-repo-drift/DRIFT_REPORT.md`
   - `consult/artifacts/2026-05-29-public-repo-drift/RESULTS.json`
   - `consult/artifacts/2026-05-29-pre-qualifier-triage/TRIAGE.md`
   - `consult/artifacts/2026-05-28-pre-qualifier-review/REVIEW.md`
2. Read/spot-checked H2H runner and packaged source lines:
   - `consult/artifacts/2026-05-29-public-repo-drift/run_h2h.py`
   - `tools/public_saturation.py`
   - `unzip -p submissions/v_final.zip src/postflop.py src/preflop_lookup.py src/bot.py src/opponent_model.py`
3. Phase A probe:
   - `.venv/bin/python consult/artifacts/2026-05-29-public-drift-patch/instrumented_h2h.py --hands 20000`
   - Result: 20,000 scheduled / 963 actual hands, hero `-260,000` chips, `-13.00 bb/100` scheduled, 3,481 hero decision records, hero errors `0`, opponent errors `0`.
4. Cluster parse:
   - `.venv/bin/python - <<'PY' ... read logs/toby_master_clusters_s142.json ... PY`
   - Top last-decision clusters were river `raise_le_2/3pot` and river `fold` clusters, not preflop overlay/position/limp-iso/legalizer clusters.
5. Artifact hash check:
   - `shasum -a 256 submissions/v_final.zip submissions/best_green.zip`
   - Both printed `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.

## Phase A result

See `CLUSTER_NOTES.md` for details. Summary:

| rank | street | position_label | true_position_label | action class | count | chips | bb/100 scheduled | likely source |
|---:|---|---|---|---|---:|---:|---:|---|
| 1 | river | heads_up_button | heads_up_button | `raise` / `raise_le_2/3pot` | 22 | -55,792 | -2.790 | `src/postflop.py:38-44` |
| 2 | river | big_blind | heads_up_button | `fold` | 21 | -53,256 | -2.663 | `src/postflop.py:46-53` |
| 3 | river | heads_up_button | heads_up_button | `fold` | 21 | -51,807 | -2.590 | `src/postflop.py:46-53` |

Allowed seams were not material:

- Preflop pressure overlay all-in as last losing decision: 1 instance, -10 chips, `-0.001 bb/100` scheduled.
- Preflop current-pressure folds after two raises: about `-1.03 bb/100` scheduled, much smaller than the river clusters.
- Six-max position labeling: not exercised by a heads-up H2H probe and not consumed postflop.
- Limp + iso: unavailable in heads-up.
- Illegal check-to-call: no supporting evidence.

## Gate results

| gate | status | evidence / reason |
|---|---|---|
| Phase A decision-cluster analysis | GREEN for reproduction/localization; BLOCKED for patch | Reproduced Toby deficit at `-13.00 bb/100`; localized material loss to forbidden postflop surface. |
| Phase B minimal patch | SKIPPED | No allowed-scope seam localized materially. |
| import_audit | SKIPPED | No candidate zip. |
| edge_cases | SKIPPED | No candidate zip / no new strategy test because no patch. |
| validator | SKIPPED | No candidate zip. |
| smoke | SKIPPED | No candidate zip. |
| leakage | SKIPPED | No candidate zip. |
| exploit_check | SKIPPED | No candidate zip. |
| all-template benchmark | SKIPPED | No candidate zip. |
| Toby H2H candidate vs canonical | SKIPPED | No candidate zip; Phase A canonical replay only. |
| Mehedi H2H candidate non-regression | SKIPPED | No candidate zip. |
| H2H regression checks | SKIPPED | No candidate zip. |

## Final recommendation

Keep `submissions/v_final.zip` / `submissions/best_green.zip` locked. The only material Toby-localized fix would require postflop strategy changes forbidden by this task and too risky before the 2026-06-01 qualifier without a full separate gate.
