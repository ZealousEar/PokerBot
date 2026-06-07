# Finals 6-max evidence: v_final.zip

- zip: `submissions/v_final.zip`
- sha256: `b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b`
- expected prefix: `b108eff5`; match: `True`
- engine primitive: `ext/fullhouse-engine/sandbox/match.py::run_match`
- hands per match: `800`; seat rotations: `0..5`; paired seeds: `2026060730..2026060735`
- mode: local subprocess runner under `/Users/farhad/Code/PokerBot/.venv/bin/python`

## Per-mix summary

| mix | matches | hands | Thorp delta sum | avg/match | chip/100 | bb/100 | bb/100 CI | pressure folds | pressure loss chips | pressure loss bb/100 | decisions | fold-defaults | illegal names | timeouts | exceptions | busts | bust streets |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| adaptive_overfold_pressure | 6 | 4800 | 124240 | 20706.67 | 2588.33 | 25.8833 | `{"half_width": 9.9373, "high": 36.0546, "low": 16.18, "mean": 25.9077}` | 43 | 18742 | -3.9046 | 4302 | 0 | 0 | 0 | 0 | 0 | `{}` |

## Per-seat rows

| mix | seat | seed | hands | delta | final stack | pressure folds | pressure loss chips | pressure loss bb/100 | decisions | fold-defaults | illegal names | timeouts | exceptions | busted | bust street |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| adaptive_overfold_pressure | 0 | 2026060730 | 800 | 17974 | 27974 | 7 | 1734 | -2.1675 | 721 | 0 | 0 | 0 | 0 | False | None |
| adaptive_overfold_pressure | 1 | 2026060731 | 800 | 19499 | 29499 | 8 | 2591 | -3.2388 | 731 | 0 | 0 | 0 | 0 | False | None |
| adaptive_overfold_pressure | 2 | 2026060732 | 800 | 34894 | 44894 | 9 | 3059 | -3.8237 | 719 | 0 | 0 | 0 | 0 | False | None |
| adaptive_overfold_pressure | 3 | 2026060733 | 800 | 17820 | 27820 | 5 | 6840 | -8.55 | 695 | 0 | 0 | 0 | 0 | False | None |
| adaptive_overfold_pressure | 4 | 2026060734 | 800 | 3146 | 13146 | 9 | 3034 | -3.7925 | 726 | 0 | 0 | 0 | 0 | False | None |
| adaptive_overfold_pressure | 5 | 2026060735 | 800 | 30907 | 40907 | 5 | 1484 | -1.855 | 710 | 0 | 0 | 0 | 0 | False | None |

