# Qualifier Pod Distribution - 2026-05-28

Generated: `2026-05-28T01:53:19Z`
Hero artifact: `submissions/v_final.zip`
Hero SHA-256: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
Engine commit: `adc23b9813338d0e1e56e0158f18644b2b9ad234`
Schedule: `400` hands x `100` seeds per pod (seed base `42`), local `match.py` runner.

## Color Table

| Pod | Color | p10 | p50 | p90 | mean | stdev | bust rate | hero error rate | hero p99 decide ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | RED | -10000 | -10000 | 13575 | -1513 | 12181 | 63.0% | 0.000% | 8.292 |
| C2 | AMBER | -10000 | 3954 | 26732 | 5352 | 14981 | 35.0% | 0.000% | 39.245 |
| C3 | RED | -10000 | -9637 | 24122 | 638 | 14899 | 50.0% | 0.000% | 65.479 |
| C4 | AMBER | -10000 | 4182 | 26042 | 4866 | 13950 | 32.0% | 0.000% | 65.287 |

## Pod Composition

| Pod | Seats |
| --- | --- |
| C1 | hero, template, aggressor, mathematician, shark, ref_bot_2 |
| C2 | hero, neel, dominic, famadeo, vladimir, shark |
| C3 | hero, neel, dominic, famadeo, aggressor, mathematician |
| C4 | hero, vladimir, famadeo, template, shark, ref_bot_2 |

Color rules: GREEN = p50 > 0 and p10 > -5000; AMBER = p50 > 0; RED = p50 <= 0.
Hero error rate is action errors divided by hero decisions. Latency is based on local `BotProcess.act()` wall-clock timing.
