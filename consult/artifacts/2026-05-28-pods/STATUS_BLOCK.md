## 2026-05-28T01:53:19Z · QUAL-PODS · RED
- Goal: Estimate canonical `submissions/v_final.zip` 400-hand qualifier chip-delta distribution across four realistic six-max pods.
- Artifact: `submissions/v_final.zip` sha `e4b4a8f11f80…`; engine `ext/fullhouse-engine` commit `adc23b9813338d0e1e56e0158f18644b2b9ad234`; runner `ext/fullhouse-engine/sandbox/match.py`; `USE_DOCKER=False`.
- Schedule: 4 pods × 100 seeds × 400 hands = 400 matches.
- Pod color table:

| Pod | Seats | Color | p10 | p50 | p90 | mean | stdev | bust rate | hero error rate | p99 ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | hero, template, aggressor, mathematician, shark, ref_bot_2 | RED | -10000 | -10000 | 13575 | -1513 | 12181 | 63.0% | 0.000% | 8.292 |
| C2 | hero, neel, dominic, famadeo, vladimir, shark | AMBER | -10000 | 3954 | 26732 | 5352 | 14981 | 35.0% | 0.000% | 39.245 |
| C3 | hero, neel, dominic, famadeo, aggressor, mathematician | RED | -10000 | -9637 | 24122 | 638 | 14899 | 50.0% | 0.000% | 65.479 |
| C4 | hero, vladimir, famadeo, template, shark, ref_bot_2 | AMBER | -10000 | 4182 | 26042 | 4866 | 13950 | 32.0% | 0.000% | 65.287 |

- Files changed: `tools/qualifier_pods.py`, `consult/artifacts/2026-05-28-pods/{matches.jsonl,pod_summary.json,SUMMARY.md,STATUS_BLOCK.md}`, `STATUS.md`.
- Validator / import_audit / edge / smoke / leakage / exploit: N/A for this distribution-estimation gate; the harness exercised the real sandbox match runner and captured hero errors/latency per decision.
- Next action: interpret the pod-color matrix; qualifier artifact remains unchanged.

