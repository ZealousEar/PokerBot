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
