"""Bet-sizing tree.

Discrete sizings: 1/3 pot, 2/3 pot, pot, 2x pot, all-in. The engine wants
the TOTAL chips put in (`amount`), not the increment-over-current-bet.

# Source: [[Pluribus-Brown-Sandholm-2019]] — discrete sizing tree
# Status: SHIPPED — the discrete sizing tree is the running sizing logic.
"""
SIZINGS = ("third_pot", "two_third_pot", "pot", "two_x_pot", "all_in")


def _safe_fallback(state) -> dict:
    if isinstance(state, dict) and state.get("can_check"):
        return {"action": "check"}
    return {"action": "fold"}


def _int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


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


def normalized_raise_total(target_total: int, state: dict) -> int:
    """Return the executable total-to target after min-raise/stack checks.

    The returned value may be below ``min_raise_to`` only when it represents a
    legal short all-in.  A value at or below ``current_bet`` is not a full
    raise; ``legal_raise_total`` still expresses it as the engine's ``all_in``
    action when hero cannot cover the call.
    """
    if not isinstance(state, dict):
        return 0
    try:
        target = max(int(target_total), 0)
    except (TypeError, ValueError, OverflowError):
        return 0
    hero_bet = max(_int(state.get("your_bet_this_street")), 0)
    stack = max(_int(state.get("your_stack")), 0)
    current_bet = max(_int(state.get("current_bet")), 0)
    min_raise_to = max(_int(state.get("min_raise_to")), 0)
    max_total = hero_bet + stack
    if stack <= 0 or max_total <= hero_bet:
        return 0
    full_raise_min = max(min_raise_to, current_bet + 1)
    return min(max(target, full_raise_min), max_total)


def raise_increment(target_total: int, state: dict) -> int:
    """Incremental chips hero adds now for a normalized total-to target."""
    if not isinstance(state, dict):
        return 0
    target = normalized_raise_total(target_total, state)
    hero_bet = max(_int(state.get("your_bet_this_street")), 0)
    return max(target - hero_bet, 0)


def is_full_raise_target(target_total: int, state: dict) -> bool:
    """Whether the normalized target clears the current legal minimum."""
    if not isinstance(state, dict):
        return False
    target = normalized_raise_total(target_total, state)
    current_bet = max(_int(state.get("current_bet")), 0)
    min_raise_to = max(_int(state.get("min_raise_to")), current_bet + 1)
    return target > current_bet and target >= min_raise_to


def legal_raise_total(target_total: int, state: dict) -> dict:
    """Return a legal raise/all-in action for a total-chip target.

    `target_total` is the total chips we put in this street, matching the
    engine's `amount` semantics. Below `min_raise_to` the engine snaps up,
    but we snap here too so logs reflect intent. Malformed inputs fall back to
    a safe non-raise action so no illegal amount escapes.
    """
    if not isinstance(state, dict):
        return {"action": "fold"}
    my_stack = max(_int(state.get("your_stack")), 0)
    my_bet = max(_int(state.get("your_bet_this_street")), 0)
    current_bet = max(_int(state.get("current_bet")), 0)
    owed = max(_int(state.get("amount_owed")), 0)
    target = normalized_raise_total(target_total, state)
    chips_needed = target - my_bet
    if target <= 0 or my_stack <= 0 or chips_needed <= 0:
        return _safe_fallback(state)
    if chips_needed >= my_stack:
        return {"action": "all_in"}
    # Recheck after stack capping: a below-min target is not a legal raise.
    if target <= current_bet or target < max(_int(state.get("min_raise_to")), current_bet + 1):
        return {"action": "all_in"} if my_stack <= owed else _safe_fallback(state)
    return {"action": "raise", "amount": int(target)}


def pot_fraction_raise_total(pot: int, state: dict, fraction: float = 0.66) -> int:
    """Return a correct pot-fraction total-to raise target.

    Facing a bet, the sizing base is the pot *after hero calls*.  Under the
    engine's total-to semantics this is::

        existing hero bet + call increment + fraction * (pot + call increment)

    The previous implementation omitted the call from the pot-size base and
    therefore undersized every facing-bet raise.
    """
    if not isinstance(state, dict):
        raise TypeError("state must be a dict")
    pot_value = max(_int(pot), 0)
    hero_bet = max(_int(state.get("your_bet_this_street")), 0)
    current_bet = max(_int(state.get("current_bet")), 0)
    owed = max(_int(state.get("amount_owed")), 0)
    frac = max(float(fraction), 0.0)
    called_total = max(hero_bet + owed, current_bet)
    pot_after_call = pot_value + owed
    raise_by = max(int(round(pot_after_call * frac)), 1)
    return called_total + raise_by


def pot_size_bet(pot: int, state: dict, fraction: float = 0.66) -> dict:
    """Build a postflop raise with target = current_bet + fraction*pot.

    ``pot`` includes the opponent's facing bet but not hero's pending call.
    ``state`` is the live action_request dict. The result snaps to legal limits
    and falls back to all-in when stack is short.
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
