# P6 Ship-Day Rehearsal and Contamination Sentinel

Timestamp: 2026-05-29 18:04:18 EEST
Workdir: `/Users/farhad/Code/PokerBot`
Output directory: `consult/artifacts/2026-05-29-away/ship-day-rehearsal/`

## Verdict

`NO_GO_SMOKE_FAIL`

The locked artifact did not complete the required 200-hand sandbox smoke run. Per the stop rule, the remaining verification sequence was not run and no repair, copy, rebuild, repackage, or candidate artifact step was attempted.

## Protected Artifact Integrity

Expected SHA for both protected artifacts:

`e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`

Pre-run SHA check:

| Artifact | SHA | Match |
| --- | --- | --- |
| `submissions/v_final.zip` | `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` | yes |
| `submissions/best_green.zip` | `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` | yes |

Post-run SHA check:

| Artifact | SHA | Match |
| --- | --- | --- |
| `submissions/v_final.zip` | `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` | yes |
| `submissions/best_green.zip` | `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` | yes |

`shasum` emitted locale warnings in both SHA logs, but returned exit code 0 and printed the expected hashes.

## Commands Run

### 1. Protected SHA precheck

Command:

```sh
shasum -a 256 submissions/v_final.zip submissions/best_green.zip
```

Result: PASS.

Log: `command_logs/01_sha_pre.txt`

### 2. Sandbox smoke run

Command:

```sh
.venv/bin/python tools/smoke_run.py --zip submissions/v_final.zip --hands 200
```

Result: FAIL, exit code 1.

Observed output:

```json
{
  "n_hands": 136,
  "expected_hands": 200,
  "chip_delta": {
    "v_final": 10000,
    "template": -10000
  },
  "errors": {},
  "duration_s": 3.21
}
```

Failure reason: only `136/200` hands played. The expected condition was `200/200` hands.

Log: `command_logs/02_smoke_run.txt`

### 3. Protected SHA postcheck

Command:

```sh
shasum -a 256 submissions/v_final.zip submissions/best_green.zip
```

Result: PASS.

Log: `command_logs/99_sha_post.txt`

## Commands Not Run

The following required checks were skipped because the smoke command failed and the task required stopping on first failure:

- `.venv/bin/python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip`
- `.venv/bin/python tools/import_audit.py --max-seconds 1.5 --max-mb 400`
- `.venv/bin/python tools/audit_strategy_leakage.py --zip submissions/v_final.zip`
- `du -h submissions/v_final.zip`
- `unzip -l submissions/v_final.zip | tail -20`
- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git show-ref --heads release/v_final-e4b4a8f1 || true`

## Invariant Compliance

- No source files edited.
- No candidate zip created.
- `tools/package.py` not run.
- `submissions/v_final.zip` not modified, rebuilt, repackaged, copied over, replaced, or chmod-modified.
- `submissions/best_green.zip` not modified, rebuilt, repackaged, copied over, replaced, or chmod-modified.
- `ext/fullhouse-engine/` not edited.
- `ext/public-bots/` snapshots not edited.
- Strategy behavior was tested from the locked zip, not inferred from `src/`.
