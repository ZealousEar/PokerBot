Hard invariant:
- Do not modify, rebuild, repackage, copy over, or replace:
  submissions/v_final.zip
  submissions/best_green.zip
- Both must remain sha256:
  e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
- Do not edit ext/fullhouse-engine/.
- Do not edit ext/public-bots/ snapshots.
- Do not infer ship behavior from current main src/. Main may be scaffold/stub.
- If strategy source is needed, use release/v_final-e4b4a8f1 or extract the locked zip.
- Any candidate artifact must have a new name and must never replace v_final.zip or best_green.zip.
- All commands must use .venv/bin/python, not host python.
- Record protected artifact SHA before and after the run.
- Write all outputs under consult/artifacts/2026-05-29-away/<lane-name>/ unless explicitly told otherwise.

Task: P4 Public drift completeness sweep, no strategy edits.

Use the global Hard Invariant above.

Goal:
Complete the public-opponent drift matrix after the Toby/Mehedi findings.

Output directory:
consult/artifacts/2026-05-29-away/public-drift-completeness/

No edits allowed except scripts/logs under this artifact directory.

Repos / bot families:
1. TobyCoad/fullhouse-engine:
   - bots/master
   - any other valid custom bots under bots/
2. Mehedi-dev-2404/fullhouse-engine:
   - bots/mybot
   - any other valid custom bots under bots/
3. Pav1602/fullhouse-engine:
   - all skantbot7 variants:
     7.0, 7.1, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9
   - if 7.2 or other versions exist, include them.
4. stoppedtime24/fullhouse-engine:
   - bots/mybot
5. vladimirfilip/fullhouse-engine:
   - live bots/vlad if data/gto_strategy.npz is present locally or recoverable from prior local snapshot.
   - if live public lacks the model file, report TIMEBOXED_UNUSABLE and reuse previous local vladimir audit only as background.
6. famadeo/fullhouse-engine:
   - bots/codex_holdem; confirm unchanged SHA and do not rerun unless changed.
7. agrawalneel25/fullhouse-engine:
   - neel-work/bots/neel; confirm unchanged SHA and do not rerun unless changed.
8. Any fork pushed within the last 72 hours with custom bots/ and non-template bot.py.

Steps:
1. Enumerate public forks using gh api or git remote search.
2. Record:
   repo | branch | latest commit | commit date | bot path | LOC | data files | validator status.
3. Package valid bots into temporary zips under:
   consult/artifacts/2026-05-29-away/public-drift-completeness/opponent_zips/
4. Validate every temporary opponent zip.
5. H2H triage:
   - For new or changed bots: run at least a triage schedule.
   - Escalate any mean <= 0, CI low <= -10, or surprising early-bust behavior.
6. Report scheduled and actual bb/100 separately.
7. Record hero errors, opponent errors, and p99 latency if available.

Verdict rules:
- GREEN: mean > 0 and CI low > -20
- AMBER: CI overlaps zero but CI low > -20
- RED: CI high < 0 or stable mean <= 0 with CI high <= +5
- NEW_THREAT: valid bot not in prior matrix, regardless of first result
- UNUSABLE: missing required data / invalid package
- TIMEBOXED: could not collect enough actual hands

Outputs:
- PUBLIC_DRIFT_COMPLETENESS_REPORT.md
- RESULTS.json
- opponent_inventory.json
- command_logs/
- STATUS_BLOCK.md

Report must answer:
1. Are Pav intermediate versions hiding a RED cell?
2. Are Toby and Mehedi still the only RED public cells?
3. Did any recently pushed fork add a new custom bot?
4. Does live vladimir invalidate the prior local positive audit?
5. Does anything justify opening a pre-qualifier MODIFY gate?

Default recommendation:
Do not modify v_final.zip without a fully-gated candidate.
Verify protected SHAs after the run.
