# Escalated over-folding exploiter probe

Date: 2026-06-07

## Verdict

**FINDING / NOT REPRODUCED.** The adaptive and 6-max escalations still measured real fold-to-pressure bleed, but neither run reproduced a net-negative Thorp result against frozen `b108eff5`.

Relative to the prior fixed-HU baseline (`+18.8544 bb/100` net, `-12.4285 bb/100` isolated bleed), the adaptive HU run **widened Thorp's positive margin** and reduced isolated bleed. The 6-max adaptive-pressure field also stayed strongly net-positive for Thorp.

No p-hacking/tuning after results: seeds and hands were fixed before final measurement; the observed positive results are reported as-is.

**Boundary:** this does **not** discharge the over-folding risk for future ship gates. The adaptive HU probe fired the postflop pressure-fold mechanism far less often than the fixed HU probe (39 pressure-fold rows vs 1,023 in Workstream B), so the smaller bleed is evidence that this specific adaptive instrument engaged the postflop mechanism less, not proof that Thorp has no over-folding hole.

## Artifact under test

- Bot: `submissions/v_final.zip`
- SHA256 command: `openssl dgst -sha256 submissions/v_final.zip`
- SHA256: `b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b` (**VERIFIED**, expected `b108eff5...`)
- Scope: measurement instruments only; no upload, no submission, no ship action.

## Code / instrument paths

- HU gauntlet style registry: `tools/deployed_artifact_gauntlet.py:55` adds `adaptive_overfold_exploiter`.
- Adaptive state/ramp helpers: `tools/deployed_artifact_gauntlet.py:204-302` track observed fold/continue responses to this bot's pressure and adjust thresholds.
- Adaptive exploiter policy: `tools/deployed_artifact_gauntlet.py:410-469` implements disciplined preflop, defensive continue-vs-resistance, flop/turn/river pressure.
- Standalone synthetic mirror: `tools/synthetic_opponents.py:242-457` adds the same generated opponent source for non-gauntlet tools/tests.
- 6-max synthetic mix hook: `tools/quick_6max_eval.py:31-32` and `tools/quick_6max_eval.py:118-150` add `adaptive_overfold_pressure` using five adaptive copies.
- 6-max pressure-bleed metric: `tools/quick_6max_eval.py:243-326` computes fold-after-pressure from engine `events` and consecutive Thorp stack deltas.
- 6-max run integration / raw persistence: `tools/quick_6max_eval.py:330-384` writes per-match pressure rows.
- 6-max CI / aggregation: `tools/quick_6max_eval.py:390-464` bootstraps bb/100 CI and aggregates pressure bleed.

Implementation caveat: the HU gauntlet and 6-max harness use separate generated-source copies (`tools/deployed_artifact_gauntlet.py` embedded source vs `tools/synthetic_opponents.py` standalone source). They share the same behavioral design but are not byte-identical; therefore HU-vs-6max comparisons are instrument/regime comparisons, not a pure same-code A/B.

Generated adaptive HU artifact:

- Source: `consult/artifacts/2026-06-07-overfold-probe/escalation/hu_adaptive_10000/synthetic_opponents/src/adaptive_overfold_exploiter/bot.py`
- Zip: `consult/artifacts/2026-06-07-overfold-probe/escalation/hu_adaptive_10000/synthetic_opponents/zips/adaptive_overfold_exploiter.zip`

Generated 6-max source:

- Source dir: `consult/artifacts/2026-06-07-overfold-probe/escalation/6max_adaptive_800x6/synthetic_opponents/src/adaptive_overfold_exploiter/`

## Mechanism-match metric

Same mechanism as Workstream B: postflop fold-after-pressure, computed from engine per-action `events`, not generic win-rate.

A pressure-fold row is counted when:

1. A non-Thorp bot has a flop/turn `raise` or `all_in` action event.
2. The pressure event is active on that same street.
3. Thorp subsequently folds on that same street.
4. Thorp's hand delta is computed from consecutive Thorp stack differences.

Primary bleed metric:

```text
postflop_pressure_fold_loss_chips = sum(max(0, -thorp_delta))
```

Metric caveat: this counts all same-street fold-to-pressure losses, including folds that may be strategically correct; it is a mechanism-presence/bleed instrument, not an optimal-fold counterfactual estimator.

Secondary surrendered-pot metric:

```text
pressure_pot_after_surrendered_chips = sum(pressure_event.pot_after)
```

## Verification commands

### Static / contract checks

```bash
python3 -c 'import signal, pathlib, sys; signal.alarm(5); [compile(pathlib.Path(p).read_text(), p, "exec") for p in sys.argv[1:]]; print("compiled")' \
  tools/deployed_artifact_gauntlet.py tools/synthetic_opponents.py tools/quick_6max_eval.py
```

Result: **VERIFIED `compiled`, `EXIT:0`**. Note: `py_compile` itself did not produce an exit marker in this command runner; the explicit bounded `compile()` check did.

```bash
.venv/bin/python -m pytest \
  tests/integration/test_synthetic_opponent_edge_suite.py::test_synthetic_opponents_return_runner_safe_actions_on_probe_states -q
```

Result: **VERIFIED `1 passed`, `EXIT:0`**.

### Smoke runs

HU smoke:

```bash
.venv/bin/python tools/deployed_artifact_gauntlet.py \
  --bot submissions/v_final.zip \
  --baseline submissions/v_final.zip \
  --outdir consult/artifacts/2026-06-07-overfold-probe/escalation/smoke_hu \
  --hands-per-opponent 400 \
  --match-len 200 \
  --seed-base 2026060719 \
  --opponents adaptive_overfold_exploiter \
  --skip-probes
```

Result: **VERIFIED `EXIT:0`**, 0 hero/opponent errors, pressure metric nonzero.

6-max smoke:

```bash
.venv/bin/python tools/quick_6max_eval.py \
  --hands 50 \
  --seed-base 2026060729 \
  --mix adaptive_overfold_pressure \
  --seat 0 \
  --out-dir consult/artifacts/2026-06-07-overfold-probe/escalation/smoke_6max_ci \
  --fail-on-sha-mismatch
```

Result: **VERIFIED `EXIT:0`**, 0 errors/timeouts/fold-defaults.

## Final run commands and results

### 1) Adaptive HU gauntlet

Command:

```bash
.venv/bin/python tools/deployed_artifact_gauntlet.py \
  --bot submissions/v_final.zip \
  --baseline submissions/v_final.zip \
  --outdir consult/artifacts/2026-06-07-overfold-probe/escalation/hu_adaptive_10000 \
  --hands-per-opponent 10000 \
  --match-len 200 \
  --seed-base 2026060720 \
  --opponents adaptive_overfold_exploiter \
  --skip-probes
```

Result artifact: `consult/artifacts/2026-06-07-overfold-probe/escalation/hu_adaptive_10000/results/match_results.json`

Harness: HU deployed-artifact gauntlet, paired orientations.

Seeds/hands: seeds `2026060720..2026060744`, 25 seeds x 2 orientations x 200 hands = 10,000 scheduled / 10,000 actual.

| Metric | Value |
|---|---:|
| Thorp chip delta | **+252,108** |
| Thorp bb/100 | **+25.2108** |
| Bootstrap CI | **[+23.2013, +27.1640] bb/100** |
| Hero errors | 0 |
| Opponent errors | 0 |
| Pressure-fold count | **39** |
| Pressure-fold chip loss | **15,117 chips** |
| Pressure-fold loss rate | **-1.5117 bb/100** |
| Pressure pot-after surrendered | **48,957 chips** |
| Pressure pot-after rate | **-4.8957 bb/100** |
| Pressure folds by street | flop 34, turn 5 |
| Pressure folds by kind | flop_cbet_or_probe 34, turn_barrel 2, turn_probe 3 |

Comparison to fixed HU baseline: Thorp net **increased** from `+18.8544` to `+25.2108 bb/100`; isolated bleed **decreased** from `-12.4285` to `-1.5117 bb/100`. This does **not** reproduce net-negative and does **not** shrink margin. It also does **not** clear the postflop over-folding risk, because the adaptive policy generated only 39 pressure-fold rows vs the fixed probe's 1,023.

### 2) Adaptive 6-max pressure field

Command:

```bash
.venv/bin/python tools/quick_6max_eval.py \
  --hands 800 \
  --seed-base 2026060730 \
  --mix adaptive_overfold_pressure \
  --out-dir consult/artifacts/2026-06-07-overfold-probe/escalation/6max_adaptive_800x6 \
  --fail-on-sha-mismatch
```

Result artifacts:

- Summary: `consult/artifacts/2026-06-07-overfold-probe/escalation/6max_adaptive_800x6/summary.json`
- CSV: `consult/artifacts/2026-06-07-overfold-probe/escalation/6max_adaptive_800x6/pressure_bleed_hands.csv`
- Report: `consult/artifacts/2026-06-07-overfold-probe/escalation/6max_adaptive_800x6/REPORT.md`

Harness: `tools/quick_6max_eval.py` using `ext/fullhouse-engine/sandbox/match.py::run_match`; one Thorp plus five `adaptive_overfold_exploiter` copies.

Seeds/hands: seats `0..5`, seeds `2026060730..2026060735`, 800 hands per match = 4,800 total hands.

| Metric | Value |
|---|---:|
| Thorp chip delta | **+124,240** |
| Thorp chip/100 | **+2,588.33 chips/100** |
| Thorp bb/100 | **+25.8833** |
| Bootstrap CI | **[+16.1800, +36.0546] bb/100** |
| Thorp decisions | 4,302 |
| Fold-defaults / illegal / timeouts / exceptions | 0 / 0 / 0 / 0 |
| Busts | 0 |
| Pressure-fold count | **43** |
| Pressure-fold chip loss | **18,742 chips** |
| Pressure-fold loss rate | **-3.9046 bb/100** |
| Pressure pot-after surrendered | **68,331 chips** |
| Pressure pot-after rate | **-14.2356 bb/100** |
| Pressure folds by street | flop 39, turn 4 |
| Pressure folds by kind | flop_cbet_or_probe 39, turn_barrel 2, turn_probe 2 |

Comparison to fixed HU baseline: different harness/regime, but still **not net-negative**; Thorp remains more positive than fixed HU baseline by bb/100 (`+25.8833` vs `+18.8544`). Isolated bleed exists (`-3.9046 bb/100`) but does not dominate total EV.

## Interpretation boundary

- **VERIFIED:** the adaptive instrument exists, runs legally, records fold-after-pressure from engine events, and produces the numeric results above.
- **VERIFIED:** the escalated HU and 6-max runs do not reproduce net-negative Thorp EV.
- **INFERRED:** this specific adaptive policy may be too defensive / too low-frequency to extract as much postflop fold pressure as the fixed Workstream B policy; however, tuning it after seeing results would be p-hacking, so no further tuning was done in this run.
- **INFERRED:** the original “mean EV vs a strong seed may be negative” claim remains unconfirmed by this mechanism-matched escalation. The over-folding mechanism is real, but these tests only show that the built adaptive instruments did not reproduce net-negative EV; they do not prove the risk is absent.

## Final verdict vs fixed-HU baseline

- Fixed HU baseline: `+18.8544 bb/100` net, `-12.4285 bb/100` bleed.
- Adaptive HU: `+25.2108 bb/100` net, `-1.5117 bb/100` bleed.
- Adaptive 6-max: `+25.8833 bb/100` net, `-3.9046 bb/100` bleed.

**Verdict: NOT REPRODUCED.** Margin did not shrink; it widened in HU and stayed strongly positive in 6-max. The correct finding is: net-negative was not reproduced by these instruments; the over-folding risk is still not discharged by this lower-postflop-pressure adaptive run.
