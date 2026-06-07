# Over-folding exploiter probe — Workstream B

Date: 2026-06-07

## Verdict

**FINDING / NOT REPRODUCED:** the mechanism-matched probe measured a real fold-to-pressure bleed, but it did **not** reproduce a negative Thorp matchup against this fixed sharp over-folding exploiter.

- **Overall Thorp delta vs `overfold_exploiter`: VERIFIED +188,506 chips over 9,998 actual hands** (`+18.8544 bb/100`, bootstrap CI `[+16.9687, +21.0541]`).
- **Isolated postflop fold-to-pressure bleed: VERIFIED -124,260 chips** over 1,023 flop/turn pressure-fold hands (`-12.4285 bb/100`).
- **Secondary surrendered-pot metric:** pressure-event pot after the cbet/barrel that induced the fold sums to **406,131 chips** (`-40.6212 bb/100` as a pot-surrendered rate).

Interpretation: the named over-folding mechanism is present and measurable, but this first mechanism-matched fixed exploiter does not make it dominate Thorp's total EV. That means the original diagnosis is **incomplete or requires a stronger/adaptive exploiter**; this run should not be p-hacked into a negative result.

## Artifact under test

- Bot: `submissions/v_final.zip`
- SHA256 command: `openssl dgst -sha256 submissions/v_final.zip`
- SHA256: `b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b` (**VERIFIED**, expected `b108eff5...`)

## Exploiter / metric implementation

Code added only in allowed Workstream B paths:

- Standing gauntlet opponent pool: `tools/deployed_artifact_gauntlet.py:55` adds `overfold_exploiter`.
- Embedded exploiter behavior: `tools/deployed_artifact_gauntlet.py:262-302` / generated source `consult/artifacts/2026-06-07-overfold-probe/run_10000/synthetic_opponents/src/overfold_exploiter/bot.py:186-224`.
  - Wide pressure/open helper: generated `bot.py:50-56`.
  - Preflop wide open/continue: generated `bot.py:191-202`.
  - Bet-fold discipline under resistance: generated `bot.py:204-209`.
  - Flop cbet and turn barrel pressure: generated `bot.py:211-218`.
- Standalone synthetic generator mirror: `tools/synthetic_opponents.py:165-239`; action-contract bet-fold line at `tools/synthetic_opponents.py:223-226`.
- Bleed metric parser: `tools/deployed_artifact_gauntlet.py:575-632`.
- Bleed summary: `tools/deployed_artifact_gauntlet.py:635-657`.
- CSV export: `tools/deployed_artifact_gauntlet.py:1029-1044`.
- Targeted gauntlet filtering: `tools/deployed_artifact_gauntlet.py:1054` and `tools/deployed_artifact_gauntlet.py:1092-1096`.

Generated exploiter artifact:

- Source: `consult/artifacts/2026-06-07-overfold-probe/run_10000/synthetic_opponents/src/overfold_exploiter/bot.py`
- Zip: `consult/artifacts/2026-06-07-overfold-probe/run_10000/synthetic_opponents/zips/overfold_exploiter.zip`

## Methodology

### Mechanism-match definition

This probe measures the specified **over-folding bleed**, not preflop busting or generic win-rate.

A pressure-fold row is counted only when all conditions hold:

1. Engine `hand["events"]` contains a non-hero `action` event on `flop` or `turn` with `action in {"raise", "all_in"}`.
2. That event is the active pressure event on the same street.
3. A subsequent hero `action == "fold"` occurs on that same street.
4. The hand's hero chip delta is computed from consecutive hero stack differences in that match.

Primary bleed metric:

```text
postflop_pressure_fold_loss_chips = sum(max(0, -hero_delta))
for rows satisfying the flop/turn fold-to-pressure condition.
```

Secondary pot-surrender metric:

```text
pressure_pot_after_surrendered_chips = sum(pressure_event.pot_after)
for the same rows.
```

### Exact run command

```bash
.venv/bin/python tools/deployed_artifact_gauntlet.py \
  --bot submissions/v_final.zip \
  --baseline submissions/v_final.zip \
  --outdir consult/artifacts/2026-06-07-overfold-probe/run_10000 \
  --hands-per-opponent 10000 \
  --match-len 200 \
  --seed-base 2026060710 \
  --opponents overfold_exploiter \
  --skip-probes
```

Command result: **VERIFIED `EXIT:0`**.

Harness mode: existing deployed artifact gauntlet, HU paired-seat orientations. Seeds: **2026060710 through 2026060734 inclusive** (`25` seeds × `2` orientations × `200` scheduled hands = `10,000` scheduled; `9,998` actual because the engine stops a match when fewer than two bots remain alive).

Primary result artifact: `consult/artifacts/2026-06-07-overfold-probe/run_10000/results/deployed_gauntlet_results.json`

Bleed CSV: `consult/artifacts/2026-06-07-overfold-probe/run_10000/results/pressure_bleed_hands.csv`

## Results

From `run_10000/results/match_results.json`:

| Metric | Value |
|---|---:|
| Opponent | `overfold_exploiter` |
| Sample count | 50 paired orientation samples |
| Scheduled hands | 10,000 |
| Actual hands | 9,998 |
| Thorp chip delta | **+188,506** |
| Thorp bb/100 | **+18.8544** |
| Bootstrap CI | `[+16.9687, +21.0541] bb/100` |
| Hero errors | 0 |
| Opponent errors | 0 |
| Pressure-fold count | **1,023** |
| Pressure-fold chip loss | **124,260 chips** |
| Pressure-fold loss rate | **-12.4285 bb/100** |
| Pressure pot-after surrendered | **406,131 chips** |
| Pressure pot-after rate | **-40.6212 bb/100** |
| Pressure folds by street | flop 923, turn 100 |
| Pressure folds by kind | flop_cbet_or_probe 923, turn_barrel 53, turn_probe 47 |

## Verification notes

- `py_compile tools/deployed_artifact_gauntlet.py tools/synthetic_opponents.py`: **VERIFIED `EXIT:0`**.
- `pytest tests/integration/test_synthetic_opponent_edge_suite.py::test_synthetic_opponents_return_runner_safe_actions_on_probe_states -q`: **VERIFIED `1 passed`, `EXIT:0`**.
- Gauntlet embedded checks in `run_10000/results/deployed_gauntlet_results.json`:
  - `tools/import_audit.py`: returncode 0.
  - `pytest tests/edge_cases -x`: returncode 0, 14 passed.
  - `ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip --json`: returncode 0, passed true.
  - `tools/audit_strategy_leakage.py --zip submissions/v_final.zip`: returncode 1 from existing strategy-string scan. This is recorded, but the match itself ran with 0 hero/opponent errors and the validator passed.

## Conclusion

The missing instrument now exists and records the mechanism-matched bleed. The measured bleed is nontrivial, but the fixed exploiter does **not** reproduce a negative b108eff5 result. Forward remediation should treat this as a measurement result: either the finals failure required a more adaptive/sharper opponent than this fixed policy, or other loss mechanisms combined with over-folding to produce the observed failure. No shipping or live-retune action was taken.
