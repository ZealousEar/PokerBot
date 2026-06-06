"""Bet-sizing tree.

Discrete sizings keyed off the blueprint: 1/3 pot, 2/3 pot, pot, 2× pot,
all-in. `sizing_to_amount` converts a sizing tag plus pot and stack to the
raise total expected by the engine (`{"action": "raise", "amount": <total>}`).
"""
SIZINGS = ("min_raise", "third_pot", "half_pot", "two_third_pot", "pot", "two_x_pot", "all_in")


def sizing_to_amount(
    sizing: str,
    pot: int,
    stack: int,
    min_raise_to: int = 0,
    already_in: int = 0,
) -> int:
    """Translate a sizing tag to the engine's total raise amount."""
    total_stack = max(0, int(stack or 0) + int(already_in or 0))
    min_raise_to = max(0, int(min_raise_to or 0))
    pot = max(0, int(pot or 0))
    if total_stack <= 0:
        return 0
    if sizing == "min_raise":
        return min(max(min_raise_to, already_in), total_stack)
    if sizing == "third_pot":
        target = already_in + pot // 3
        return min(max(target, min_raise_to), total_stack)
    if sizing == "half_pot":
        target = already_in + pot // 2
        return min(max(target, min_raise_to), total_stack)
    if sizing == "two_third_pot":
        target = already_in + (pot * 2) // 3
        return min(max(target, min_raise_to), total_stack)
    if sizing == "pot":
        target = already_in + pot
        return min(max(target, min_raise_to), total_stack)
    if sizing == "two_x_pot":
        target = already_in + pot * 2
        return min(max(target, min_raise_to), total_stack)
    if sizing == "all_in":
        return total_stack
    raise ValueError(f"unknown sizing {sizing!r}")
