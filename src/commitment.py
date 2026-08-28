"""Postflop stack, pot-odds and commitment arithmetic.

Raises/stack-offs use board-aware nuttedness.  Calls are priced from the chips
actually available to call and the portion of the pot hero can win; a hard
percentage-of-stack call cap is incorrect because it can reject positive-EV
all-in calls.  All amounts in this module distinguish total-to amounts from
the *incremental* chips hero must put in now.

# Source: [[Libratus-Brown-Sandholm-2017]] — range-aware refinement.
# Status: SHIPPED as a heuristic commitment gate. Libratus-style real-time range
#         refinement is INTENDED/dropped (compute-prohibitive at 0.5 CPU / 2 s).
"""

from src.hand_features import classify_board, classify_hand, full_house_dominated


COMMIT_FRACTION = 0.40
PAIRED_EQ_THRESHOLD = 0.80
FLUSH_EQ_THRESHOLD = 0.92
SAFE_EQ_THRESHOLD = 0.55
# Retained as a public compatibility name.  It is now the natural maximum
# (100% of the remaining stack), not the old arbitrary 25% rejection cap.
LARGE_CALL_MAX_OWED_FRACTION = 1.0
CALL_EQUITY_BUFFER = 0.015


def _float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def call_cost(state: dict) -> int:
    """Incremental chips required to call, capped by hero's remaining stack."""
    if not isinstance(state, dict):
        return 0
    owed = max(_int(state.get("amount_owed")), 0)
    stack = max(_int(state.get("your_stack")), 0)
    return min(owed, stack)


def total_after_call(state: dict) -> int:
    """Hero's total street commitment after calling (including a short call)."""
    if not isinstance(state, dict):
        return 0
    hero_bet = max(_int(state.get("your_bet_this_street")), 0)
    return hero_bet + call_cost(state)


def incremental_cost(target_total: int, state: dict) -> int:
    """Chips hero must add now to reach a total-to target.

    The result is always in ``[0, your_stack]``.  This is the quantity used by
    commitment gates; comparing a total street amount with the remaining stack
    double-counts chips hero has already invested.
    """
    if not isinstance(state, dict):
        return 0
    target = max(_int(target_total), 0)
    hero_bet = max(_int(state.get("your_bet_this_street")), 0)
    stack = max(_int(state.get("your_stack")), 0)
    return min(max(target - hero_bet, 0), stack)


def incremental_commitment_fraction(target_total: int, state: dict) -> float:
    """Fraction of hero's remaining stack required by ``target_total``."""
    stack = max(_int(state.get("your_stack")) if isinstance(state, dict) else 0, 0)
    if stack <= 0:
        return 1.0
    return incremental_cost(target_total, state) / stack


def _players(state: dict) -> list:
    players = state.get("players", []) if isinstance(state, dict) else []
    return players if isinstance(players, list) else []


def _folded(player: dict) -> bool:
    return bool(player.get("is_folded")) or player.get("state") == "folded"


def active_opponent_seats(state: dict) -> list:
    """Non-folded opponent seats, including all-in players."""
    hero = state.get("seat_to_act") if isinstance(state, dict) else None
    seats = []
    for player in _players(state):
        if not isinstance(player, dict) or player.get("seat") == hero or _folded(player):
            continue
        seat = player.get("seat")
        if seat is not None:
            seats.append(seat)
    return seats


def side_pot_eligible_seats(state: dict, target_total: int = None) -> list:
    """Opponents able to contest hero's marginal chips at ``target_total``.

    The engine does not expose lifetime hand contributions, so this is a
    conservative current-street approximation.  Active players may call using
    their remaining stack; an all-in player below the target cannot contest
    the extra side-pot layer and is excluded.
    """
    if not isinstance(state, dict):
        return []
    target = total_after_call(state) if target_total is None else max(_int(target_total), 0)
    hero = state.get("seat_to_act")
    seats = []
    for player in _players(state):
        if not isinstance(player, dict) or player.get("seat") == hero or _folded(player):
            continue
        committed = max(_int(player.get("bet_this_street")), 0)
        is_all_in = bool(player.get("is_all_in")) or player.get("state") == "all_in"
        available = 0 if is_all_in else max(_int(player.get("stack")), 0)
        if committed + available >= target:
            seats.append(player.get("seat"))
    return [seat for seat in seats if seat is not None]


def contestable_pot(state: dict, target_total: int = None) -> int:
    """Approximate the portion of the current pot hero is eligible to win.

    Contributions above a short-stacked hero's total-to cap belong to a side
    pot hero cannot win.  We can remove current-street excess exactly from the
    public player fields; prior-street layers are unavailable and remain in the
    estimate.
    """
    if not isinstance(state, dict):
        return 0
    pot = max(_int(state.get("pot")), 0)
    target = total_after_call(state) if target_total is None else max(_int(target_total), 0)
    hero = state.get("seat_to_act")
    excess = 0
    for player in _players(state):
        if not isinstance(player, dict) or player.get("seat") == hero:
            continue
        committed = max(_int(player.get("bet_this_street")), 0)
        excess += max(committed - target, 0)
    return max(pot - excess, 0)


def pot_odds_to_call(state: dict) -> float:
    """Pot odds using the short call and hero-eligible pot, not raw ``owed``."""
    cost = call_cost(state)
    if cost <= 0:
        return 0.0
    eligible = contestable_pot(state, total_after_call(state))
    return cost / (eligible + cost) if eligible + cost > 0 else 1.0


def effective_stack(state: dict, opponent_seats=None, *, after_call: bool = True) -> int:
    """Hero's effective remaining stack against relevant live opponents.

    Multiway effective stack is measured against the deepest relevant
    opponent because that player can cover the greatest part of hero's stack.
    With ``after_call=True`` both hero's call and the aggressor's already-made
    bet are removed before computing chips behind.
    """
    if not isinstance(state, dict):
        return 0
    hero_stack = max(_int(state.get("your_stack")), 0)
    hero_bet = max(_int(state.get("your_bet_this_street")), 0)
    cost = call_cost(state) if after_call else 0
    hero_behind = max(hero_stack - cost, 0)
    wanted = set(active_opponent_seats(state) if opponent_seats is None else opponent_seats)
    cover = []
    for player in _players(state):
        if not isinstance(player, dict) or player.get("seat") not in wanted or _folded(player):
            continue
        behind = max(_int(player.get("stack")), 0)
        if not after_call:
            behind += max(_int(player.get("bet_this_street")), 0) - hero_bet
        cover.append(max(behind, 0))
    return min(hero_behind, max(cover)) if cover else 0


def stack_to_pot_ratio(state: dict, opponent_seats=None, *, after_call: bool = True) -> float:
    """Effective-stack-to-contestable-pot ratio (SPR)."""
    cost = call_cost(state) if after_call else 0
    target = total_after_call(state) if after_call else max(
        _int(state.get("your_bet_this_street")) if isinstance(state, dict) else 0, 0
    )
    pot = contestable_pot(state, target) + cost
    stack = effective_stack(state, opponent_seats, after_call=after_call)
    return stack / pot if pot > 0 else float("inf")


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

    Calls are priced by range-aware equity, not the stricter raise gate.  The
    realization buffer shrinks to zero for an all-in call because no future
    decision can prevent equity realization.  There is no arbitrary 25% cap.
    """
    owed = _float(owed_frac, default=1.0)
    if owed <= 0.0:
        return True
    if owed > LARGE_CALL_MAX_OWED_FRACTION:
        return False
    odds = _float(pot_odds)
    eq = _float(eq_strong)
    realization_buffer = CALL_EQUITY_BUFFER * max(1.0 - max(owed, 0.0), 0.0)
    return eq >= odds + realization_buffer
