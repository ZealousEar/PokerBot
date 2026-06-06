"""Postflop strategy.

Flop / turn / river: equity-driven heuristics with board-texture awareness
and overlay-aware c-bet bluffing. Equity comes from `src.equity` (Monte Carlo
eval7); opponent reads come from `src.opponent_model`.

Trial counts kept small (≤ 280) so each call stays well under 50 ms — leaves
the 2 s decision budget with abundant headroom.

# Source: [[Cepheus-Bowling-2015]] — bucket-style state abstraction; the
#         heuristic plays the role of the abstracted bucket lookup until G3
#         CFR+ training replaces it (gated by AGENTS.md solver policy).
"""
from typing import List

from src.commitment import COMMIT_FRACTION, can_call_large, can_commit_raise
from src.equity import hand_strength, equity_vs_range
from src.opponent_model import get_model
from src.sizing import legal_raise_total, pot_fraction_raise_total, pot_size_bet


# Lightweight villain range archetypes for equity_vs_range. Used as priors
# when no model is warm.
PRIOR_RANGE_TIGHT = ["88+", "AT+", "KQs", "KJs"]
PRIOR_RANGE_LOOSE = ["22+", "A2+", "K9+", "QT+", "JT", "T9s", "98s"]


def board_texture(board: List[str]) -> dict:
    """Return cheap structural features: wet/dry, paired, flush-y, straight-y."""
    if not board:
        return {"wet": False, "paired": False, "flush_draw": False, "straight_y": False,
                "high_card": False}
    ranks = [c[0] for c in board]
    suits = [c[1] for c in board]
    suit_counts = {s: suits.count(s) for s in set(suits)}
    rank_order = "23456789TJQKA"
    rvals = sorted(rank_order.index(r) for r in ranks)
    paired = len(set(ranks)) < len(ranks)
    flush_draw = max(suit_counts.values()) >= 2
    straight_y = (max(rvals) - min(rvals)) <= 4 and len(set(rvals)) >= 2
    high_card = any(r in "AKQ" for r in ranks)
    return {
        "wet": flush_draw or straight_y,
        "paired": paired,
        "flush_draw": flush_draw,
        "straight_y": straight_y,
        "high_card": high_card,
    }


def _opponent_seat(state: dict) -> int:
    me = state.get("seat_to_act", -1)
    for p in state.get("players", []):
        if p.get("seat") != me and not p.get("is_folded") and p.get("state") != "folded":
            return p.get("seat", -1)
    return -1


def _flush_suit(board):
    """Suit with 3+ cards on the board (a flush is possible), else None."""
    suits = [c[1] for c in board if isinstance(c, str) and len(c) >= 2]
    for s in set(suits):
        if suits.count(s) >= 3:
            return s
    return None


def _board_paired(board):
    ranks = [c[0] for c in board if isinstance(c, str) and len(c) >= 2]
    return len(set(ranks)) < len(ranks)


def _has_nut_flush(hole, board, suit):
    """True if we hold a made flush of `suit` using its nut (highest off-board) card."""
    if suit is None:
        return False
    board_suit = [c[0] for c in board if isinstance(c, str) and len(c) >= 2 and c[1] == suit]
    my_suit = [c[0] for c in hole if isinstance(c, str) and len(c) >= 2 and c[1] == suit]
    if len(board_suit) + len(my_suit) < 5:
        return False
    on_board = set(board_suit)
    for r in "AKQJT98765432":
        if r in on_board:
            continue
        return r in my_suit
    return False


def _can_commit(hole, board, eq_strong):
    """Compatibility wrapper for the extracted commitment gate."""
    return can_commit_raise(hole, board, eq_strong)


def decide_postflop(game_state: dict, *, blueprint_only: bool = False) -> dict:
    """Equity-driven postflop decision. Always returns a legal action.

    `blueprint_only=True` skips the opponent-model overlay (used for the
    ablation benchmark to measure overlay contribution).
    """
    can_check = bool(game_state.get("can_check"))
    pot = int(game_state.get("pot", 0))
    my_stack = int(game_state.get("your_stack", 0))
    owed = int(game_state.get("amount_owed", 0))
    current_bet = int(game_state.get("current_bet", 0))
    street = game_state.get("street", "flop")
    hole = list(game_state.get("your_cards", []))
    board = list(game_state.get("community_cards", []))
    if my_stack <= 0:
        return {"action": "check"} if can_check else {"action": "call"}
    if len(hole) != 2:
        return {"action": "check"} if can_check else {"action": "fold"}

    texture = board_texture(board)
    model = get_model()
    opp = _opponent_seat(game_state)
    if blueprint_only or opp < 0:
        shift = {"widen_open": 0.0, "cbet_bluff_more": 0.0,
                 "value_thinner": 0.0, "bluff_catch_less": 0.0,
                 "tighten_open": 0.0, "fold_to_pressure_less": 0.0,
                 "value_widen_vs_aggro": 0.0}
        archetype = "unknown"
    else:
        shift = model.exploit_shift(opp)
        archetype = model.archetype(opp)

    # Higher trial counts give tighter equity estimates on close calls. At
    # ~20 µs/evaluate, 280 trials = ~6 ms — well under the 50 ms budget.
    base_trials = {"flop": 280, "turn": 220, "river": 180}.get(street, 200)
    eq = hand_strength(hole, board, trials=base_trials)

    # Pot odds.
    pot_odds = owed / (pot + owed) if (pot + owed) > 0 and owed > 0 else 0.0
    call_threshold = pot_odds + 0.03  # small implied-odds / variance buffer
    if archetype == "loose_passive":
        call_threshold -= shift.get("value_thinner", 0.0) * 0.3
    if shift.get("bluff_catch_less", 0.0) > 0 and street == "river":
        call_threshold += shift["bluff_catch_less"] * 0.3
    # Against hyper-aggressive villains: their large bets carry less info,
    # so we don't fold to pressure as easily on rivers with marginal hands.
    if shift.get("fold_to_pressure_less", 0.0) > 0 and street == "river":
        call_threshold -= shift["fold_to_pressure_less"] * 0.3

    value_threshold_thin = 0.70
    # Against aggressive villains, value-bet wider — their calls extend to
    # marginal hands we'd otherwise check.
    if shift.get("value_widen_vs_aggro", 0.0) > 0:
        value_threshold_thin -= shift["value_widen_vs_aggro"] * 0.2

    if can_check:
        if eq > value_threshold_thin:
            return pot_size_bet(pot, game_state, fraction=0.66)
        if eq > 0.55:
            return pot_size_bet(pot, game_state, fraction=0.50)
        cbet_bluff_prob = 0.30 + shift.get("cbet_bluff_more", 0.0)
        if street == "flop" and not texture["wet"] and texture["high_card"]:
            cbet_bluff_prob += 0.10
        # Candidate B: one more low-risk stab on dry, unpaired, non-high-card
        # flops the finalist field overfolds. Mutually exclusive with the
        # high-card bump above; wet/paired/turn/river/value/sizing untouched.
        if street == "flop" and not texture["wet"] and not texture["paired"] and not texture["high_card"]:
            cbet_bluff_prob += 0.07
        if 0.25 < eq < 0.55 and cbet_bluff_prob > 0.35:
            return pot_size_bet(pot, game_state, fraction=0.50)
        return {"action": "check"}

    # Facing a bet. `eq` is equity-vs-RANDOM, which overstates us when a villain
    # bets/raises (their range is capped strong, esp. on flush/paired boards).
    # The previous code re-raised geometrically off random equity, which
    # compounds in raise wars into full-stack jams at ~12% real equity (measured
    # qualifier leak: 16 all-ins, 12% won, -81k chips). Use a pot-fraction
    # target and gate every LARGE raise on board-aware nuttedness. Calls use a
    # separate range-aware pot-odds permission.
    # Source: [[Libratus-Brown-Sandholm-2017]] — range-aware refinement.
    commit_frac = COMMIT_FRACTION
    eq_strong = equity_vs_range(hole, board, PRIOR_RANGE_TIGHT, trials=base_trials)
    commit_ok = can_commit_raise(hole, board, eq_strong)
    owed_frac = owed / my_stack if my_stack > 0 else 1.0

    if eq >= 0.80:
        raw_target = pot_fraction_raise_total(pot, game_state, fraction=0.66)
        capped_target = min(raw_target, current_bet + max(pot, 1))
        # Raise `amount` is a total street commitment, not only the increment.
        commit_chips = max(owed, capped_target)
        if commit_chips >= commit_frac * my_stack and not commit_ok:
            if can_call_large(eq_strong, pot_odds, owed_frac):
                return {"action": "call"}
            return {"action": "fold"}
        return legal_raise_total(capped_target, game_state)

    if eq >= call_threshold:
        if not commit_ok and not can_call_large(eq_strong, pot_odds, owed_frac):
            return {"action": "fold"}
        return {"action": "call"}
    return {"action": "fold"}
