# Finals 6-max evidence: v_final.zip

- zip: `submissions/v_final.zip`
- sha256: `b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b`
- expected prefix: `b108eff5`; match: `True`
- engine primitive: `ext/fullhouse-engine/sandbox/match.py::run_match`
- hands per match: `50`; seat rotations: `0..5`; paired seeds: `2026060729..2026060734`
- mode: local subprocess runner under `/Users/farhad/Code/PokerBot/.venv/bin/python`

## Per-mix summary

| mix | matches | hands | Thorp delta sum | avg/match | chip/100 | bb/100 | bb/100 CI | pressure folds | pressure loss chips | pressure loss bb/100 | decisions | fold-defaults | illegal names | timeouts | exceptions | busts | bust streets |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| adaptive_overfold_pressure | 1 | 50 | 1250 | 1250.0 | 2500.0 | 25.0 | `{"half_width": 0.0, "high": 25.0, "low": 25.0, "mean": 25.0}` | 0 | 0 | 0.0 | 46 | 0 | 0 | 0 | 0 | 0 | `{}` |

## Per-seat rows

| mix | seat | seed | hands | delta | final stack | pressure folds | pressure loss chips | pressure loss bb/100 | decisions | fold-defaults | illegal names | timeouts | exceptions | busted | bust street |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| adaptive_overfold_pressure | 0 | 2026060729 | 50 | 1250 | 11250 | 0 | 0 | 0.0 | 46 | 0 | 0 | 0 | 0 | False | None |

