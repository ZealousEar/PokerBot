"""Bet-sizing tree.

Discrete sizings keyed off the blueprint: 1/3 pot, 2/3 pot, pot, 2× pot,
all-in. `sizing_to_amount` converts a sizing tag plus pot and stack to the
raise total expected by the engine (`{"action": "raise", "amount": <total>}`).
"""
SIZINGS = ("third_pot", "two_third_pot", "pot", "two_x_pot", "all_in")


def sizing_to_amount(sizing: str, pot: int, stack: int) -> int:
    """Translate a sizing tag to a chip amount. Capped at `stack`."""
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
