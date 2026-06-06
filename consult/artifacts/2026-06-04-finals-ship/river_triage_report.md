# River bust triage — finals 6-max evidence

Scope: existing `consult/artifacts/2026-06-04-finals-ship/6max_evidence/raw_matches/*.json`, plus diagnostic replay attempts through the marked bust hands. No `src/`, `data/`, `submissions/`, or upload changes.

## Verdict: NO repeated avoidable river-overcommit leak found.

Authoritative evidence from the stored raw JSON:

- River-marked Thorp bust hands: `9`
- Stored Thorp decisions on the river in those bust hands: `0`
- Hands with no stored Thorp river decision: `9`
- Large river call-off / raise / all-in candidates: `0`
- Final stored Thorp commitment street counts: `{'flop': 2, 'no_action': 1, 'preflop': 6}`
- Full board/card/made-hand rows recoverable from stored artifacts: `0/9`

Interpretation: these rows are marked `bust_street=river` because the all-in hand ran out to a river showdown. They are not evidence of Thorp choosing a river call/raise/all-in. The repeated pattern, if any, is earlier-street stack commitment / short-stack variance, not river overcommit.

## Evidence boundary

`tools/quick_6max_eval.py` persisted only `row`, `compact_result`, `thorp_action_records`, and `all_action_error_records`; it did not persist full `result["hands"]`, final board, revealed cards, pot events, or opponent hole cards. Reference bots use unseeded `random`, so diagnostic replay is not the same evidence sample. Board/card/made-hand buckets are therefore not recoverable from these artifacts; the river-decision verdict is authoritative for all rows because it uses stored Thorp action records.

## Bucket counts

- `unclassified_existing_json_insufficient_replay_mismatch`: 9

## Per-hand details

| match | hand | stored final Thorp action | stored committed river/total | river decision? | board / cards / made hand | pot | live river opps | bucket | evidence status |
|---|---:|---|---:|---|---|---:|---:|---|---|
| aggro_collision_seat0_seed42 | 24 | NO RIVER DECISION; final preflop: faced owed=19200, current_bet=24000, stack_before=2168, bet_this_street=4800; chose all_in | 0/6968 | no | unavailable from stored raw; replay mismatch | n/a | n/a | `unclassified_existing_json_insufficient_replay_mismatch` | stored action authoritative; cards unavailable |
| aggro_collision_seat1_seed43 | 33 | NO RIVER DECISION; final preflop: faced owed=100, current_bet=100, stack_before=200, bet_this_street=0; chose all_in | 0/200 | no | unavailable from stored raw; replay mismatch | n/a | n/a | `unclassified_existing_json_insufficient_replay_mismatch` | stored action authoritative; cards unavailable |
| aggro_collision_seat3_seed45 | 20 | NO RIVER DECISION; final preflop: faced owed=8700, current_bet=10800, stack_before=2900, bet_this_street=2100; chose all_in | 0/4950 | no | unavailable from stored raw; replay mismatch | n/a | n/a | `unclassified_existing_json_insufficient_replay_mismatch` | stored action authoritative; cards unavailable |
| aggro_collision_seat4_seed46 | 20 | NO RIVER DECISION; no Thorp action record in bust hand | 0/0 | no | unavailable from stored raw; replay mismatch | n/a | n/a | `unclassified_existing_json_insufficient_replay_mismatch` | stored action authoritative; cards unavailable |
| balanced_heavy_seat3_seed45 | 314 | NO RIVER DECISION; final preflop: faced owed=6500, current_bet=8600, stack_before=4000, bet_this_street=2100; chose all_in | 0/6050 | no | unavailable from stored raw; replay mismatch | n/a | n/a | `unclassified_existing_json_insufficient_replay_mismatch` | stored action authoritative; cards unavailable |
| balanced_heavy_seat4_seed46 | 193 | NO RIVER DECISION; final flop: faced owed=0, current_bet=0, stack_before=2900, bet_this_street=0; chose all_in | 0/8150 | no | unavailable from stored raw; replay mismatch | n/a | n/a | `unclassified_existing_json_insufficient_replay_mismatch` | stored action authoritative; cards unavailable |
| reference_field_seat3_seed45 | 0 | NO RIVER DECISION; final preflop: faced owed=6500, current_bet=10000, stack_before=6500, bet_this_street=3500; chose call | 0/10000 | no | unavailable from stored raw; replay mismatch | n/a | n/a | `unclassified_existing_json_insufficient_replay_mismatch` | stored action authoritative; cards unavailable |
| reference_field_seat4_seed46 | 91 | NO RIVER DECISION; final flop: faced owed=0, current_bet=0, stack_before=280, bet_this_street=0; chose all_in | 0/780 | no | unavailable from stored raw; replay mismatch | n/a | n/a | `unclassified_existing_json_insufficient_replay_mismatch` | stored action authoritative; cards unavailable |
| reference_field_seat5_seed47 | 29 | NO RIVER DECISION; final preflop: faced owed=100, current_bet=100, stack_before=226, bet_this_street=0; chose all_in | 0/226 | no | unavailable from stored raw; replay mismatch | n/a | n/a | `unclassified_existing_json_insufficient_replay_mismatch` | stored action authoritative; cards unavailable |

## Bottom line for future patch work

Do not patch a river-specific fold/call cap based on this evidence. There are `0` repeated river decisions and `0` river overcommit candidates in the stored action data. If a future patch window investigates this further, rerun the 6-max eval with full `result["hands"]` and rich action-request state persisted; otherwise board/card bucket triage is not recoverable from these artifacts.

