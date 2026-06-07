"""Postflop commitment and large-call permission gates.

Large raises/stack-offs use board-aware nuttedness, while calls use range-aware
pot odds plus a commitment-fraction cap. This keeps the Qual-II >=40%-stack
leak fix while allowing priced-in calls that are not safe stack-offs.

# Source: [[Libratus-Brown-Sandholm-2017]] — range-aware refinement.
# Status: SHIPPED as a heuristic commitment gate. Libratus-style real-time range
#         refinement is INTENDED/dropped (compute-prohibitive at 0.5 CPU / 2 s).
"""

from src.hand_features import classify_board, classify_hand, full_house_dominated


COMMIT_FRACTION = 0.40
PAIRED_EQ_THRESHOLD = 0.80
FLUSH_EQ_THRESHOLD = 0.92
SAFE_EQ_THRESHOLD = 0.55
LARGE_CALL_MAX_OWED_FRACTION = 0.25
CALL_EQUITY_BUFFER = 0.03


def _float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def can_commit_raise(hole, board, eq_strong) -> bool:
    """Return True if a large raise/stack-off is allowed.

    Ordering is intentional: full-house-or-better first, then paired boards,
    then unpaired flush boards. A nut flush on a paired board is *not* an
    automatic stack-off because it can be drawing dead to a boat.
    """
    eq = _float(eq_strong)
    board_info = classify_board(board)
    hand_info = classify_hand(hole, board)
    made = hand_info.get("category")

    # Quads or straight flush are always safe stack-offs.
    if made in ("four_kind", "straight_flush"):
        return True

    if board_info.get("paired"):
        # Paired boards breed higher full houses. Allow a large stack-off ONLY
        # with an undominated (nut) full house; route second-best boats AND bare
        # trips (e.g. trip-K on a KK7 board) to the range-aware call gate, which
        # folds when the call commits too much of the stack. Closes the Qual-II
        # near-dead stack-off leak (second-best boat on a double-paired board).
        if hand_info.get("full_house_or_better"):
            return not full_house_dominated(hole, board)
        return False

    if board_info.get("flush_suit") is not None:
        return bool(hand_info.get("nut_flush")) or eq >= FLUSH_EQ_THRESHOLD
    return eq >= SAFE_EQ_THRESHOLD


def can_call_large(eq_strong, pot_odds, owed_frac) -> bool:
    """Return True if a call is allowed when a large raise is not.

    Calls are priced by range-aware equity, not by the stricter nuttedness gate.
    The owed-fraction cap preserves the rule #1 leak fix: dominated hands still
    fold when the call itself commits too much of the remaining stack.
    """
    owed = _float(owed_frac, default=1.0)
    if owed <= 0.0:
        return True
    if owed > LARGE_CALL_MAX_OWED_FRACTION:
        return False
    odds = _float(pot_odds)
    eq = _float(eq_strong)
    return eq >= odds + CALL_EQUITY_BUFFER
