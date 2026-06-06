# Edge Test Report - 2026-06-03

## Scope

Goal: expand the edge-case and synthetic-opponent test surface for expensive tournament runner failure modes without changing strategy.

Read inputs:
- `prompt-exports/POKERBOT_CONTEXT_REFRESH_2026-06-03.md`
- `docs/tournament-spec.md`
- `PROMPT.shared.md` and `PLAN.md`

Note: `PROMPT.md` is not present in this checkout. `PROMPT.shared.md` contains the relevant Done When and Verification contract.

## Files Added

- `tools/edge_case_harness.py`
- `tools/synthetic_opponents.py`
- `tests/edge_cases/test_runner_contract_extended.py`
- `tests/edge_cases/test_package_and_harness_contracts.py`
- `tests/integration/test_synthetic_opponent_edge_suite.py`

No edits were made to `src/`, `ext/fullhouse-engine/`, or preserved submission zips.

## Inventory And Gaps

Before this run, current checkout coverage was thin:
- `tests/edge_cases/test_safe_fallback.py`: 4 tests, canonical `src` fallback only.
- `tests/integration/test_analyze_postflop_trap_prevalence.py`: 4 extractor tests, not runner/bot action coverage.
- Existing `tools/self_play.py` and `tools/benchmark.py` are scaffold/TODO in this checkout.
- `docs/tournament-spec.md` confirms the expensive failure modes: crash or malformed return -> fold; invalid action -> fold; below-min raise snapped; timeout -> fold; warmup exception is reported but hand 1 continues; package/forbidden imports reject the submission.

New coverage closes or exposes these gaps:
- malformed `game_state`: partial, wrong-type, and missing-key states in `expensive_edge_states()`.
- missing/empty/contradictory legal actions: extra `legal_actions` fields plus contradictory `can_check`/owed probes.
- raise below min / above stack / equal-to-call: `check_action_contract()` and package-harness unit tests.
- all-in and side-pot states: `all_in_side_pot` state.
- warmup exception: synthetic bad bot through `runner.py`.
- per-decision timeout: synthetic slow bot through `runner.py`.
- multiway pots: `multiway_wet_flop` and six-max synthetic match.
- wet-board equity realization: `wet_board_equity_realization`.
- river bluff-catcher thresholds: `river_bluff_catcher_threshold`.
- blind-defense and 3-bet pressure: `blind_defense_3bet_pressure`.
- package structure and forbidden imports: candidate zip structure scan plus canonical `import_audit.scan_src()`.
- deterministic seed reproducibility: repeated six-max synthetic match signature comparison.

## Applicability

Default pytest subjects:
- canonical `src/` bot, copied into a temp root-shim submission directory;
- deployed zip if present: `submissions/v_qual2_ship_d54640e0.zip`;
- future candidate zips via `POKERBOT_CANDIDATE_ZIP` or path-list `POKERBOT_CANDIDATE_ZIPS`.

The runner harness invokes bot code through `ext/fullhouse-engine/sandbox/runner.py` using `.venv/bin/python` 3.10.18 by default, even when the shell's bare `pytest` is Python 3.14.3.

Synthetic opponents are generated into temp directories, not into `ext/fullhouse-engine/`:
- `maniac_all_in`
- `pot_odds_threshold`
- `river_value_threshold`
- `tight_aggressive`
- `loose_aggressive`

## Failure Classification

| Failure | Classification | Evidence | Notes |
| --- | --- | --- | --- |
| `deployed_qual2_d54640e0` returns `{"action": "all_in"}` on `near_dead_postflop_commitment` | bot bug | `pytest tests/edge_cases -x` fails in `test_subjects_do_not_large_commit_near_dead_postflop_spots`; commitment fraction `1.000` | This is a deployed-artifact behavior failure. It matches the risk class from the context refresh: under-boat / paired-board dominated commitment. No strategy fix was made in this run. |
| Harness and synthetic opponents | no harness bug found | 13 remaining edge tests pass when the bot-bug test is deselected; integration synthetic suite passes | Failure is isolated to deployed zip behavior, not package validation, runner warmup/timeout tests, or synthetic opponents. |
| Artifact lineage | artifact-lineage issue remains | Tests default to `submissions/v_qual2_ship_d54640e0.zip`; canonical `src/` is scaffold/fallback and is tested only as a contract subject | The deployed strategy source is not canonical `src/`; this report tests the preserved zip directly. |
| Benchmark strength | benchmark limitation | Synthetic suite is a small failure-mode smoke, not EV evidence | No bb/100 or tournament strength claim is made. |

## Command Evidence

### Required Edge Command - venv / sandbox-matched

Command:

```bash
.venv/bin/python -m pytest tests/edge_cases -x
```

Exit code: 1

Output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.10.18, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/farhad/Code/PokerBot
plugins: hypothesis-6.152.9
collected 14 items

tests/edge_cases/test_package_and_harness_contracts.py ......            [ 42%]
tests/edge_cases/test_runner_contract_extended.py .F

=================================== FAILURES ===================================
__________ test_subjects_do_not_large_commit_near_dead_postflop_spots __________
E       assert ["deployed_qual2_d54640e0:near_dead_postflop_commitment:large_commit:1.000:action={'action': 'all_in'}"] == []
tests/edge_cases/test_runner_contract_extended.py:72: AssertionError
=========================== short test summary info ============================
FAILED tests/edge_cases/test_runner_contract_extended.py::test_subjects_do_not_large_commit_near_dead_postflop_spots
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
========================= 1 failed, 7 passed in 0.35s ==========================
```

### Required Edge Command - literal shell command

Command:

```bash
pytest tests/edge_cases -x
```

Exit code: 1

Output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/farhad/Code/PokerBot
plugins: anyio-4.12.1
collected 14 items

tests/edge_cases/test_package_and_harness_contracts.py ......            [ 42%]
tests/edge_cases/test_runner_contract_extended.py .F

=================================== FAILURES ===================================
__________ test_subjects_do_not_large_commit_near_dead_postflop_spots __________
E       assert ["deployed_qual2_d54640e0:near_dead_postflop_commitment:large_commit:1.000:action={'action': 'all_in'}"] == []
tests/edge_cases/test_runner_contract_extended.py:72: AssertionError
=========================== short test summary info ============================
FAILED tests/edge_cases/test_runner_contract_extended.py::test_subjects_do_not_large_commit_near_dead_postflop_spots
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
========================= 1 failed, 7 passed in 0.66s ==========================
```

### Remaining Edge Surface, Excluding The Classified Bot Bug

Command:

```bash
.venv/bin/python -m pytest tests/edge_cases -k 'not subjects_do_not_large_commit_near_dead_postflop_spots'
```

Exit code: 0

Output:

```text
============================= test session starts ==============================
platform darwin -- Python 3.10.18, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/farhad/Code/PokerBot
plugins: hypothesis-6.152.9
collected 14 items / 1 deselected / 13 selected

tests/edge_cases/test_package_and_harness_contracts.py ......            [ 46%]
tests/edge_cases/test_runner_contract_extended.py ...                    [ 69%]
tests/edge_cases/test_safe_fallback.py ....                              [100%]

======================= 13 passed, 1 deselected in 1.30s =======================
```

### Targeted Integration Test - Small Synthetic Match Count

Command:

```bash
.venv/bin/python -m pytest tests/integration/test_synthetic_opponent_edge_suite.py -q
```

Exit code: 0

Output:

```text
...                                                                      [100%]
=============================== warnings summary ===============================
.venv/lib/python3.10/site-packages/eval7/rangestring.py:149
  /Users/farhad/Code/PokerBot/.venv/lib/python3.10/site-packages/eval7/rangestring.py:149: PyparsingDeprecationWarning: 'setName' deprecated - use 'set_name'
    suitedness = pyparsing.Word("os", exact=1).setName("suitedness")

.venv/lib/python3.10/site-packages/eval7/rangestring.py:150
  /Users/farhad/Code/PokerBot/.venv/lib/python3.10/site-packages/eval7/rangestring.py:150: PyparsingDeprecationWarning: 'setName' deprecated - use 'set_name'
    card = pyparsing.Word(ranks_str, suits_str, exact=2).setName("card")

.venv/lib/python3.10/site-packages/eval7/rangestring.py:152
  /Users/farhad/Code/PokerBot/.venv/lib/python3.10/site-packages/eval7/rangestring.py:152: PyparsingDeprecationWarning: 'setParseAction' deprecated - use 'set_parse_action'
    hand.setParseAction(lambda s, loc, toks: ''.join(toks))

.venv/lib/python3.10/site-packages/eval7/rangestring.py:160
  /Users/farhad/Code/PokerBot/.venv/lib/python3.10/site-packages/eval7/rangestring.py:160: PyparsingDeprecationWarning: 'setParseAction' deprecated - use 'set_parse_action'
    decimal.setParseAction(lambda s, loc, toks: ''.join(toks))

.venv/lib/python3.10/site-packages/eval7/rangestring.py:167
  /Users/farhad/Code/PokerBot/.venv/lib/python3.10/site-packages/eval7/rangestring.py:167: PyparsingDeprecationWarning: 'setParseAction' deprecated - use 'set_parse_action'
    handtype.setParseAction(lambda s, loc, toks: ''.join(toks))

.venv/lib/python3.10/site-packages/eval7/rangestring.py:175
  /Users/farhad/Code/PokerBot/.venv/lib/python3.10/site-packages/eval7/rangestring.py:175: PyparsingDeprecationWarning: 'delimitedList' deprecated - use 'DelimitedList'
    hand_group_list = pyparsing.Group(pyparsing.delimitedList(handtype_group))

.venv/lib/python3.10/site-packages/eval7/rangestring.py:180
  /Users/farhad/Code/PokerBot/.venv/lib/python3.10/site-packages/eval7/rangestring.py:180: PyparsingDeprecationWarning: 'delimitedList' deprecated - use 'DelimitedList'
    handrange = pyparsing.Optional(pyparsing.delimitedList(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
3 passed, 7 warnings in 0.42s
```

### Import Audit

Command:

```bash
python tools/import_audit.py
```

Exit code: 0

Output:

```text
cold import: 0.000s, RSS: 10.8 MB
```

Command:

```bash
.venv/bin/python tools/import_audit.py
```

Exit code: 0

Output:

```text
cold import: 0.000s, RSS: 10.7 MB
```

### Static Compile

Command:

```bash
.venv/bin/python -m py_compile tools/edge_case_harness.py tools/synthetic_opponents.py tests/edge_cases/test_runner_contract_extended.py tests/edge_cases/test_package_and_harness_contracts.py tests/integration/test_synthetic_opponent_edge_suite.py
```

Exit code: 0

Output: no output.

## Verdict

The test surface is expanded and runnable. The run is RED because the deployed Qualifier-II zip fails the new near-dead river commitment guard by returning all-in. This is classified as a bot bug in the deployed artifact, not a harness bug. No strategy fix was attempted.

Smallest next action: fix or supersede the deployed-lineage commitment gate for under-boat / paired-board near-dead river states, then rerun `pytest tests/edge_cases -x` and the synthetic integration test against the exact candidate zip.
