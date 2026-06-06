# Public Bot Saturation - 2026-05-28

- Artifact: `/Users/farhad/Code/PokerBot/submissions/v_final.zip`
- Artifact sha256: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- Evidence directory: `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-28-public-saturation`
- Verdict rule: GREEN = mean > 0 and CI low > -20; RED = CI high < 0; AMBER = mixed.
- CI unit: bootstrap 95% CI over paired seed-pair chip deltas, reported as bb/100 over scheduled hands.
- p99 latency is the conservative max of per-base local runner p99 decide latencies.

| Opponent | Bases | Verdict | Mean bb/100 | 95% CI | Half-width | Scheduled | Actual | Early-bust rate | Hero errors | Hero p99 latency |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| vladimir | 142,242,342,442 | GREEN | +3.70 | [+2.40, +5.00] | 1.30 | 400000 | 20081 | 100.0% | 0 | 0.0399s |
| famadeo | 142,242 | GREEN | +0.65 | [-1.30, +2.60] | 1.95 | 200000 | 43914 | 99.5% | 0 | 0.0643s |
| dominic | 142,242 | AMBER | -1.22 | [-3.24, +0.72] | 1.98 | 200000 | 77337 | 95.0% | 0 | 0.0764s |
| neel | 142,242 | GREEN | +14.69 | [+13.50, +15.81] | 1.15 | 200000 | 102276 | 85.8% | 0 | 0.0633s |

## Per-Base Runs

| Opponent | Base | Log | Verdict | Mean bb/100 | 95% CI | Half-width | Scheduled | Actual | Early-bust rate | Hero errors | Opp errors |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dominic | 142 | `dominic_s142.log` | AMBER | -0.28 | [-3.22, +2.50] | 2.86 | 100000 | 40006 | 95.0% | 0 | 0 |
| dominic | 242 | `dominic_s242.log` | AMBER | -2.15 | [-4.86, +0.57] | 2.71 | 100000 | 37331 | 95.0% | 0 | 0 |
| famadeo | 142 | `famadeo_s142.log` | GREEN | +1.10 | [-1.59, +3.78] | 2.68 | 100000 | 21972 | 99.0% | 0 | 0 |
| famadeo | 242 | `famadeo_s242.log` | GREEN | +0.20 | [-2.60, +3.00] | 2.80 | 100000 | 21942 | 100.0% | 0 | 0 |
| neel | 142 | `neel_s142.log` | GREEN | +15.24 | [+13.64, +16.72] | 1.54 | 100000 | 51393 | 85.0% | 0 | 0 |
| neel | 242 | `neel_s242.log` | GREEN | +14.13 | [+12.43, +15.78] | 1.68 | 100000 | 50883 | 86.5% | 0 | 0 |
| vladimir | 142 | `vladimir_s142.log` | GREEN | +4.80 | [+2.40, +7.20] | 2.40 | 100000 | 5091 | 100.0% | 0 | 0 |
| vladimir | 242 | `vladimir_s242.log` | GREEN | +4.80 | [+2.20, +7.60] | 2.70 | 100000 | 4961 | 100.0% | 0 | 0 |
| vladimir | 342 | `vladimir_s342.log` | GREEN | +1.60 | [-1.00, +4.20] | 2.60 | 100000 | 4970 | 100.0% | 0 | 0 |
| vladimir | 442 | `vladimir_s442.log` | GREEN | +3.60 | [+1.00, +6.40] | 2.70 | 100000 | 5059 | 100.0% | 0 | 0 |

## Packaging

Public bots were packaged into valid root-`bot.py` zips under `opponent_zips/`; `ext/fullhouse-engine/` was not modified.
