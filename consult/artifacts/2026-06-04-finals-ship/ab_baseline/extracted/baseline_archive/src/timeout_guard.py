"""Wall-clock budget tracker.

The engine enforces the 2 s deadline via a daemon thread under its own
control (`ext/fullhouse-engine/sandbox/runner.py::_call_with_timeout`); bot
code cannot use `threading` itself (validator FORBIDDEN_MODULES). So this
module just lets the decision pipeline check remaining budget at expensive
steps and short-circuit to the safe fallback if running low.
"""
import time
from contextlib import contextmanager
from typing import Callable

# Per-decision budget caps — soft, advisory. The engine's 2 s is hard.
SOFT_DEADLINE_S = 1.20   # target completion
HARD_FALLBACK_S = 1.80   # past this, return safe action no matter what


@contextmanager
def deadline(seconds: float = SOFT_DEADLINE_S):
    """Context manager yielding `remaining()` -> seconds left in budget."""
    start = time.monotonic()
    yield lambda: seconds - (time.monotonic() - start)


def run_with_budget(decision_fn: Callable[[dict], dict],
                    fallback_fn: Callable[[dict], dict],
                    game_state: dict,
                    budget_s: float = SOFT_DEADLINE_S) -> dict:
    """Call decision_fn; on exception or over-budget return fallback_fn."""
    start = time.monotonic()
    try:
        result = decision_fn(game_state)
        if time.monotonic() - start > budget_s:
            return fallback_fn(game_state)
        return result
    except Exception:
        return fallback_fn(game_state)
