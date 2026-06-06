# Finals 6-max evidence: v_final.zip

- zip: `submissions/v_final.zip`
- sha256: `b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b`
- expected prefix: `b108eff5`; match: `True`
- engine primitive: `ext/fullhouse-engine/sandbox/match.py::run_match`
- hands per match: `800`; seat rotations: `0..5`; paired seeds: `42..47`
- mode: local subprocess runner under `/Users/farhad/Code/PokerBot/.venv/bin/python`

## Per-mix summary

| mix | matches | hands | Thorp delta sum | avg/match | chip/100 | decisions | fold-defaults | illegal names | timeouts | exceptions | busts | bust streets |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| reference_field | 6 | 4800 | 70730 | 11788.33 | 1473.54 | 2592 | 0 | 0 | 0 | 0 | 3 | `{"river": 3}` |
| aggro_collision | 6 | 2047 | 60000 | 10000.0 | 2931.12 | 1220 | 0 | 0 | 0 | 0 | 4 | `{"river": 4}` |
| balanced_heavy | 6 | 4800 | 73950 | 12325.0 | 1540.62 | 3385 | 0 | 0 | 0 | 0 | 2 | `{"river": 2}` |

## Per-seat rows

| mix | seat | seed | hands | delta | final stack | decisions | fold-defaults | illegal names | timeouts | exceptions | busted | bust street |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| reference_field | 0 | 42 | 800 | 47150 | 57150 | 707 | 0 | 0 | 0 | 0 | False | None |
| reference_field | 1 | 43 | 800 | 33030 | 43030 | 622 | 0 | 0 | 0 | 0 | False | None |
| reference_field | 2 | 44 | 800 | 20550 | 30550 | 1081 | 0 | 0 | 0 | 0 | False | None |
| reference_field | 3 | 45 | 800 | -10000 | 0 | 3 | 0 | 0 | 0 | 0 | True | river |
| reference_field | 4 | 46 | 800 | -10000 | 0 | 132 | 0 | 0 | 0 | 0 | True | river |
| reference_field | 5 | 47 | 800 | -10000 | 0 | 47 | 0 | 0 | 0 | 0 | True | river |
| aggro_collision | 0 | 42 | 126 | -10000 | 0 | 64 | 0 | 0 | 0 | 0 | True | river |
| aggro_collision | 1 | 43 | 143 | -10000 | 0 | 44 | 0 | 0 | 0 | 0 | True | river |
| aggro_collision | 2 | 44 | 296 | 50000 | 60000 | 467 | 0 | 0 | 0 | 0 | False | None |
| aggro_collision | 3 | 45 | 800 | -10000 | 0 | 28 | 0 | 0 | 0 | 0 | True | river |
| aggro_collision | 4 | 46 | 150 | -10000 | 0 | 32 | 0 | 0 | 0 | 0 | True | river |
| aggro_collision | 5 | 47 | 532 | 50000 | 60000 | 585 | 0 | 0 | 0 | 0 | False | None |
| balanced_heavy | 0 | 42 | 800 | 39000 | 49000 | 654 | 0 | 0 | 0 | 0 | False | None |
| balanced_heavy | 1 | 43 | 800 | 15100 | 25100 | 674 | 0 | 0 | 0 | 0 | False | None |
| balanced_heavy | 2 | 44 | 800 | 7200 | 17200 | 676 | 0 | 0 | 0 | 0 | False | None |
| balanced_heavy | 3 | 45 | 800 | -10000 | 0 | 399 | 0 | 0 | 0 | 0 | True | river |
| balanced_heavy | 4 | 46 | 800 | -10000 | 0 | 247 | 0 | 0 | 0 | 0 | True | river |
| balanced_heavy | 5 | 47 | 800 | 32650 | 42650 | 735 | 0 | 0 | 0 | 0 | False | None |

