"""Bet-sizing tree.

Discrete sizings: 1/3 pot, 2/3 pot, pot, 2x pot, all-in. The engine wants
the TOTAL chips put in (`amount`), not the increment-over-current-bet.

# Source: [[Pluribus-Brown-Sandholm-2019]] — discrete sizing tree
"""
SIZINGS = ("third_pot", "two_third_pot", "pot", "two_x_pot", "all_in")


def _safe_fallback(state) -> dict:
    if isinstance(state, dict) and state.get("can_check"):
        return {"action": "check"}
    return {"action": "fold"}


def sizing_to_amount(sizing: str, pot: int, stack: int) -> int:
    """Translate a sizing tag to a chip amount. Capped at `stack`."""
    pot = int(pot)
    stack = int(stack)
    if sizing == "third_pot":
        return min(pot // 3, stack)
    if sizing == "two_third_pot":
        return min((pot * 2) // 3, stack)
    if sizing == "pot":
        return min(pot, stack)
    if sizing == "two_x_pot":
        return min(pot * 2, stack)
    if sizing == "all_in":
        return stack
    raise ValueError(f"unknown sizing {sizing!r}")


def legal_raise_total(target_total: int, state: dict) -> dict:
    """Return a legal raise/all-in action for a total-chip target.

    `target_total` is the total chips we put in this street, matching the
    engine's `amount` semantics. Below `min_raise_to` the engine snaps up,
    but we snap here too so logs reflect intent. Malformed inputs fall back to
    a safe non-raise action so no illegal amount escapes.
    """
    if not isinstance(state, dict):
        return {"action": "fold"}
    try:
        my_stack = int(state.get("your_stack", 0))
        my_bet = int(state.get("your_bet_this_street", 0))
        min_raise_to = int(state.get("min_raise_to", 0))
        target = max(int(target_total), min_raise_to)
    except (TypeError, ValueError, OverflowError):
        return _safe_fallback(state)

    chips_needed = target - my_bet
    if target <= 0 or my_stack <= 0 or chips_needed <= 0:
        return _safe_fallback(state)
    if chips_needed >= my_stack:
        return {"action": "all_in"}
    return {"action": "raise", "amount": int(target)}


def pot_fraction_raise_total(pot: int, state: dict, fraction: float = 0.66) -> int:
    """Return target total = current_bet + fraction*pot for postflop raises."""
    current_bet = int(state.get("current_bet", 0))
    return current_bet + max(int(int(pot) * float(fraction)), 1)


def pot_size_bet(pot: int, state: dict, fraction: float = 0.66) -> dict:
    """Build a postflop raise with target = current_bet + fraction*pot.

    `pot` here is engine `pot` (already includes our facing bet). `state` is
    the live action_request dict. Snaps to legal limits and falls back to
    all-in when stack is short.
    """
    try:
        target = pot_fraction_raise_total(pot, state, fraction=fraction)
    except (TypeError, ValueError, OverflowError, AttributeError):
        return _safe_fallback(state)
    return legal_raise_total(target, state)


def open_raise_total(state: dict, bb: int = 100, mult: float = 2.5) -> dict:
    """Build a preflop open: target total = mult * BB."""
    target = int(round(mult * bb))
    return legal_raise_total(target, state)


def threebet_total(state: dict, raise_to: int, bb: int = 100) -> dict:
    """Build a 3-bet: ~3x the open in position, ~4x out of position. Caller
    selects by passing the right multiplier here via raise_to."""
    return legal_raise_total(raise_to, state)
