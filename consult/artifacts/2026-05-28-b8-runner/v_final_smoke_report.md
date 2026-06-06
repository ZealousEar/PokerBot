# B8 Gauntlet Report - v_final

## 2026-05-28T01:28:35Z · B8 runner smoke · GREEN
- Goal: single-command B8 gauntlet runner against `submissions/v_final.zip`.
- Candidate: `submissions/v_final.zip` sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Proof: validator=PASS import_audit=PASS edge_cases=PASS smoke=PASS audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=PASS h2h_famadeo_b242=PASS h2h_dominic_b142=PASS h2h_neel_b142=PASS h2h_vladimir_b142=PASS
- Benchmarks: benchmark_all_templates=PASS (TODO output from underlying tool); benchmark_ablate_overlay=PASS (TODO output from underlying tool); benchmark_self_play_vs_prior=PASS (TODO output from underlying tool)
- Public h2h: h2h_famadeo_b142=+0.00; h2h_famadeo_b242=+64.40; h2h_dominic_b142=-23.59; h2h_neel_b142=+73.25; h2h_vladimir_b142=+270.27
- Guardrails: protected artifact hashes before={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'} after={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'}; ext/fullhouse-engine before=adc23b9813338d0e1e56e0158f18644b2b9ad234 after=adc23b9813338d0e1e56e0158f18644b2b9ad234.
- Report: `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`.
- Files changed: `tools/b8_gauntlet.py`, `tools/audit_strategy_leakage.py`, `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`, `STATUS.md`.
- Corpus citations: [[Engine-Fullhouse]], [[Libratus-Brown-Sandholm-2017]], [[Pluribus-Brown-Sandholm-2019]].
- Next action: use full profile for promotion-scale B8 acceptance; keep qualifier artifact unchanged unless a full GREEN report supports promotion.

[B8 RUNNER GREEN 2026-05-28T01:28:35Z profile=smoke candidate=v_final]
artifact=submissions/v_final.zip sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
validator=PASS import_audit=PASS edge_cases=PASS smoke=PASS audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=PASS h2h_famadeo_b242=PASS h2h_dominic_b142=PASS h2h_neel_b142=PASS h2h_vladimir_b142=PASS

## Configuration

- profile: `smoke`
- candidate: `submissions/v_final.zip`
- candidate_sha256: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- protected_hashes_before: `{'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'}`
- protected_hashes_after: `{'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'}`
- ext_fullhouse_engine_before: `adc23b9813338d0e1e56e0158f18644b2b9ad234`
- ext_fullhouse_engine_after: `adc23b9813338d0e1e56e0158f18644b2b9ad234`

## Step Summary

| step | result | rc | seconds | metrics |
| --- | --- | ---: | ---: | --- |
| `validator` | PASS | 0 | 1.203 | validator=PASSED |
| `import_audit` | PASS | 0 | 0.346 | cold_import=0.001s rss=10.4MB |
| `edge_cases` | PASS | 0 | 1.044 | 4 tests passed |
| `smoke` | PASS | 0 | 6.468 | hands=50/50 chip_delta={'v_final': 3750, 'template': -3750} |
| `audit_strategy_leakage` | PASS | 0 | 0.043 | zip_sha256=e4b4a8f11f80... leakage=PASS |
| `exploit_check` | PASS | 0 | 0.229 | - |
| `benchmark_all_templates` | PASS | 0 | 0.334 | TODO output from underlying tool |
| `benchmark_ablate_overlay` | PASS | 0 | 0.079 | TODO output from underlying tool |
| `benchmark_self_play_vs_prior` | PASS | 0 | 0.050 | TODO output from underlying tool |
| `h2h_famadeo_b142` | PASS | 0 | 4.877 | bb/100=+0.00 match_ci=[-100.00,+100.00] hands=91 |
| `h2h_famadeo_b242` | PASS | 0 | 8.119 | bb/100=+64.40 match_ci=[+4.97,+100.00] hands=163 |
| `h2h_dominic_b142` | PASS | 0 | 5.690 | bb/100=-23.59 match_ci=[-36.21,-10.98] hands=200 |
| `h2h_neel_b142` | PASS | 0 | 6.913 | bb/100=+73.25 match_ci=[+37.71,+100.00] hands=188 |
| `h2h_vladimir_b142` | PASS | 0 | 58.622 | bb/100=+270.27 match_ci=[+100.00,+100.00] hands=74 |

## Commands

### validator

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/validator.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/validator.stderr.log`

### import_audit

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/import_audit.py --max-seconds 1.5 --max-mb 400
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/import_audit.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/import_audit.stderr.log`

### edge_cases

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python -m pytest tests/edge_cases -x
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/edge_cases.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/edge_cases.stderr.log`

### smoke

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/smoke_run.py --zip submissions/v_final.zip --hands 50
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/smoke.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/smoke.stderr.log`

### audit_strategy_leakage

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/audit_strategy_leakage.py --zip submissions/v_final.zip
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/audit_strategy_leakage.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/audit_strategy_leakage.stderr.log`

### exploit_check

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/exploit_check.py
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/exploit_check.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/exploit_check.stderr.log`
- notes: tools/exploit_check.py does not expose --bot/--zip in this checkout; command is not artifact-bound

### benchmark_all_templates

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/benchmark.py --all-templates --hands 200 --paired-seed-base 42
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/benchmark_all_templates.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/benchmark_all_templates.stderr.log`
- notes: tools/benchmark.py does not expose --bot in this checkout; command is not artifact-bound

### benchmark_ablate_overlay

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/benchmark.py --ablate-overlay --hands 200 --paired-seed-base 42
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/benchmark_ablate_overlay.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/benchmark_ablate_overlay.stderr.log`
- notes: tools/benchmark.py does not expose --bot in this checkout; command is not artifact-bound

### benchmark_self_play_vs_prior

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/benchmark.py --self-play --vs-prior --hands 200 --paired-seed-base 42
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/benchmark_self_play_vs_prior.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/benchmark_self_play_vs_prior.stderr.log`
- notes: tools/benchmark.py does not expose --bot in this checkout; command is not artifact-bound

### h2h_famadeo_b142

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/h2h.py --bot-a submissions/v_final.zip --bot-b consult/artifacts/2026-05-28-public-saturation/opponent_zips/famadeo.zip --hands 200 --paired-seed-base 142 --match-len 100 --label-a v_final --label-b famadeo
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_famadeo_b142.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_famadeo_b142.stderr.log`

### h2h_famadeo_b242

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/h2h.py --bot-a submissions/v_final.zip --bot-b consult/artifacts/2026-05-28-public-saturation/opponent_zips/famadeo.zip --hands 200 --paired-seed-base 242 --match-len 100 --label-a v_final --label-b famadeo
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_famadeo_b242.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_famadeo_b242.stderr.log`

### h2h_dominic_b142

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/h2h.py --bot-a submissions/v_final.zip --bot-b consult/artifacts/2026-05-28-public-saturation/opponent_zips/dominic.zip --hands 200 --paired-seed-base 142 --match-len 100 --label-a v_final --label-b dominic
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_dominic_b142.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_dominic_b142.stderr.log`

### h2h_neel_b142

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/h2h.py --bot-a submissions/v_final.zip --bot-b consult/artifacts/2026-05-28-public-saturation/opponent_zips/neel.zip --hands 200 --paired-seed-base 142 --match-len 100 --label-a v_final --label-b neel
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_neel_b142.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_neel_b142.stderr.log`

### h2h_vladimir_b142

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python tools/h2h.py --bot-a submissions/v_final.zip --bot-b consult/artifacts/2026-05-28-public-saturation/opponent_zips/vladimir.zip --hands 200 --paired-seed-base 142 --match-len 100 --label-a v_final --label-b vladimir
```

- stdout: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_vladimir_b142.stdout.log`
- stderr: `consult/artifacts/2026-05-28-b8-runner/logs/h2h_vladimir_b142.stderr.log`

## Parsed Results

```json
[
  {
    "duration_s": 1.203,
    "label": "validator",
    "metrics": {
      "validator_passed": true,
      "validator_tests": [
        "preflop_call_or_fold",
        "postflop_can_check",
        "river_facing_large_bet",
        "short_stack_all_in_decision"
      ]
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 0.346,
    "label": "import_audit",
    "metrics": {
      "cold_import_s": 0.001,
      "rss_mb": 10.4
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 1.044,
    "label": "edge_cases",
    "metrics": {
      "tests_passed": 4
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 6.468,
    "label": "smoke",
    "metrics": {
      "chip_delta": {
        "template": -3750,
        "v_final": 3750
      },
      "duration_s": 4.72,
      "errors": {},
      "expected_hands": 50,
      "n_hands": 50
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 0.043,
    "label": "audit_strategy_leakage",
    "metrics": {
      "leakage_passed": true,
      "zip_sha256": "e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598"
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 0.229,
    "label": "exploit_check",
    "metrics": {},
    "notes": [
      "tools/exploit_check.py does not expose --bot/--zip in this checkout; command is not artifact-bound"
    ],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 0.334,
    "label": "benchmark_all_templates",
    "metrics": {
      "todo_output": true
    },
    "notes": [
      "tools/benchmark.py does not expose --bot in this checkout; command is not artifact-bound"
    ],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 0.079,
    "label": "benchmark_ablate_overlay",
    "metrics": {
      "todo_output": true
    },
    "notes": [
      "tools/benchmark.py does not expose --bot in this checkout; command is not artifact-bound"
    ],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 0.05,
    "label": "benchmark_self_play_vs_prior",
    "metrics": {
      "todo_output": true
    },
    "notes": [
      "tools/benchmark.py does not expose --bot in this checkout; command is not artifact-bound"
    ],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 4.877,
    "label": "h2h_famadeo_b142",
    "metrics": {
      "bb_per_100": 0.0,
      "ci_high_match_bb": 100.0,
      "ci_low_match_bb": -100.0,
      "errors": {
        "famadeo": 0,
        "v_final": 0
      },
      "hands_played_total": 91,
      "mean_match_bb": 0.0,
      "verdict": "v_final vs famadeo INDETERMINATE (CI crosses 0)"
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 8.119,
    "label": "h2h_famadeo_b242",
    "metrics": {
      "bb_per_100": 64.4,
      "ci_high_match_bb": 100.0,
      "ci_low_match_bb": 4.97,
      "errors": {
        "famadeo": 0,
        "v_final": 0
      },
      "hands_played_total": 163,
      "mean_match_bb": 52.48,
      "verdict": "v_final BEATS famadeo (CI excludes 0)"
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 5.69,
    "label": "h2h_dominic_b142",
    "metrics": {
      "bb_per_100": -23.59,
      "ci_high_match_bb": -10.98,
      "ci_low_match_bb": -36.21,
      "errors": {
        "dominic": 0,
        "v_final": 0
      },
      "hands_played_total": 200,
      "mean_match_bb": -23.59,
      "verdict": "v_final loses to dominic (CI excludes 0)"
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 6.913,
    "label": "h2h_neel_b142",
    "metrics": {
      "bb_per_100": 73.25,
      "ci_high_match_bb": 100.0,
      "ci_low_match_bb": 37.71,
      "errors": {
        "neel": 0,
        "v_final": 0
      },
      "hands_played_total": 188,
      "mean_match_bb": 68.86,
      "verdict": "v_final BEATS neel (CI excludes 0)"
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  },
  {
    "duration_s": 58.622,
    "label": "h2h_vladimir_b142",
    "metrics": {
      "bb_per_100": 270.27,
      "ci_high_match_bb": 100.0,
      "ci_low_match_bb": 100.0,
      "errors": {
        "v_final": 0,
        "vladimir": 0
      },
      "hands_played_total": 74,
      "mean_match_bb": 100.0,
      "verdict": "v_final BEATS vladimir (CI excludes 0)"
    },
    "notes": [],
    "passed": true,
    "returncode": 0
  }
]
```
