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

Task: P6 Ship-day rehearsal and contamination sentinel, no edits except report.

Use the global Hard Invariant above.

Goal:
Run the 2026-06-01 ship-day verification sequence now and produce a GO/NO-GO report for the locked artifact.

Output directory:
consult/artifacts/2026-05-29-away/ship-day-rehearsal/

No source edits.
No candidate zip.
No package.py against v_final.zip.
Do not touch submissions/v_final.zip or submissions/best_green.zip.
Note: the orchestrator has already chmod 444'd both protected zips; do not chmod them back.

Commands:
1. cd ~/Code/PokerBot
2. shasum -a 256 submissions/v_final.zip submissions/best_green.zip
   Expected both:
   e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598

3. .venv/bin/python tools/smoke_run.py --zip submissions/v_final.zip --hands 200
   Expected: 200/200, 0 hero errors, positive or non-catastrophic chip delta.

4. .venv/bin/python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip
   Expected: PASSED, 4/4 TEST_STATES.

5. .venv/bin/python tools/import_audit.py --max-seconds 1.5 --max-mb 400
   Expected: cold < 1.5s, RSS < 400 MB, forbidden imports 0.

6. .venv/bin/python tools/audit_strategy_leakage.py --zip submissions/v_final.zip
   Expected: PASS, zero hits.

7. du -h submissions/v_final.zip
8. unzip -l submissions/v_final.zip | tail -20
   Expected:
   total <= 250 MB,
   bot.py at root <= 5 MB,
   data/ <= 200 MB,
   no other .py at root,
   no .py inside data/,
   no symlinks.

9. git status --short
10. git branch --show-current
11. git rev-parse HEAD
12. git show-ref --heads release/v_final-e4b4a8f1 || true

Outputs:
- SHIP_DAY_REHEARSAL.md
- command_logs/
- GO_NO_GO.txt
- STATUS_BLOCK.md

GO_NO_GO.txt must be exactly one of:
GO_UPLOAD_LOCKED_V_FINAL
NO_GO_SHA_MISMATCH
NO_GO_VALIDATOR_FAIL
NO_GO_SMOKE_FAIL
NO_GO_IMPORT_FAIL
NO_GO_LEAKAGE_FAIL
NO_GO_SIZE_LAYOUT_FAIL
NO_GO_WORKTREE_CONTAMINATION

If any command fails:
- Do not attempt repair.
- Do not copy best_green.
- Do not run package.py.
- Record exact failure and stop.

Verify protected SHAs after the run.
