# API Cheatsheet

Authoritative sources:
- `ext/fullhouse-engine/bots/template/bot.py` — calling convention with annotated game_state keys
- `ext/fullhouse-engine/sandbox/validator.py` — `TEST_STATES` show concrete game_state shapes for `preflop_call_or_fold`, `postflop_can_check`, `river_facing_large_bet`, `short_stack_all_in_decision`
- `ext/fullhouse-engine/sandbox/runner.py` — timeout enforcement + warmup behavior

## `decide(game_state) -> dict`
Called once per action. Must return within 2 s for `type=="action_request"`; 30 s for `type=="warmup"`.

## game_state keys (action_request)

| Key | Type | Description |
|---|---|---|
| `type` | str | `"action_request"` for live decisions, `"warmup"` once before hand 1 |
| `hand_id` | str | Unique hand identifier |
| `street` | str | `preflop` / `flop` / `turn` / `river` |
| `seat_to_act` | int | Your seat (0-5) |
| `pot` | int | Total chips in pot |
| `community_cards` | list[str] | Board, e.g. `["As", "Kd", "7h"]` (empty preflop) |
| `current_bet` | int | Highest bet on this street |
| `min_raise_to` | int | Minimum legal raise **total** (not increment) |
| `amount_owed` | int | Chips needed to call (0 = free check) |
| `can_check` | bool | True when `amount_owed == 0` |
| `your_cards` | list[str] | Your hole cards, e.g. `["Ah", "Kh"]` |
| `your_stack` | int | Your remaining chips |
| `your_bet_this_street` | int | Chips you've already put in this street |
| `players` | list[dict] | Public info per seat: `seat`, `bot_id`, `stack`, `state` (`"active"`/`"folded"`/`"all_in"`), `is_folded`, `is_all_in`, `bet_this_street`, `hole_cards` (`None` for opponents) |
| `action_log` | list[dict] | All actions this hand: `{seat, action, amount}` |

## Card format
Strings like `"As"`, `"Td"`. Ranks: `2 3 4 5 6 7 8 9 T J Q K A`. Suits: `s` `h` `d` `c`.

## Return shapes (`validator.VALID_ACTIONS`)

```python
{"action": "fold"}
{"action": "check"}                       # only when can_check is True
{"action": "call"}
{"action": "raise", "amount": 1200}       # amount = TOTAL bet, not raise-by
{"action": "all_in"}                       # distinct from raise-to-stack
```

Invalid actions default to fold. Raises below `min_raise_to` are snapped up to the minimum automatically.

## Warmup
Before hand 1 the engine sends a state with `type == "warmup"` and a 30 s budget. The runner discards your return value but emits `{"ok": False, "error": "warmup_exception"}` if you raise. Use this call to trigger blueprint loads / eval7 LUT initialisation that would otherwise blow the 2 s decision deadline.

## Engine harness extras
- `ext/fullhouse-engine/sandbox/runner.py` — thread-based timeout, daemon worker keeps running if Python can't preempt; bot code itself cannot use `threading`.
- `ext/fullhouse-engine/sandbox/validator.py` — pre-submission validator that mirrors tournament-time AST + runtime checks; run it before packaging a submission.
- `ext/fullhouse-engine/sandbox/match.py` — local match driver used by `tools/self_play.py` and `tools/benchmark.py`.
- `ext/fullhouse-engine/engine/tournament.py` — Swiss pairing, standings, finalist selection.
