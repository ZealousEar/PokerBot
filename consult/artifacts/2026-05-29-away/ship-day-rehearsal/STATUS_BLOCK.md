## P6 Ship-Day Rehearsal - NO-GO

Verdict: `NO_GO_SMOKE_FAIL`
Timestamp: 2026-05-29 18:04:18 EEST
Artifact under test: `submissions/v_final.zip`

Protected SHA pre-run:
- `submissions/v_final.zip`: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- `submissions/best_green.zip`: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`

Smoke run:
- Command: `.venv/bin/python tools/smoke_run.py --zip submissions/v_final.zip --hands 200`
- Result: FAIL, command exit code 1
- Observed: only `136/200` hands played
- Chip delta: `v_final=10000`, `template=-10000`
- Errors: `{}`
- Duration: `3.21s`

Stop rule applied:
- Validator, import audit, leakage audit, size/layout checks, and git contamination commands were not run after the smoke failure.
- No repair attempted.
- No candidate zip created.
- `tools/package.py` not run.
- `submissions/v_final.zip` and `submissions/best_green.zip` were not copied, replaced, rebuilt, repackaged, or chmod-modified.

Protected SHA post-run:
- `submissions/v_final.zip`: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- `submissions/best_green.zip`: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`

Command logs:
- `command_logs/01_sha_pre.txt`
- `command_logs/02_smoke_run.txt`
- `command_logs/99_sha_post.txt`
