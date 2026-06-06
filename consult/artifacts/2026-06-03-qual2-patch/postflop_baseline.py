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

from src.equity import hand_strength
from src.opponent_model import get_model
from src.sizing import legal_raise_total


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
            return legal_raise_total(current_bet + max(int(pot * 0.66), 1), game_state)
        if eq > 0.55:
            return legal_raise_total(current_bet + max(int(pot * 0.5), 1), game_state)
        cbet_bluff_prob = 0.30 + shift.get("cbet_bluff_more", 0.0)
        if street == "flop" and not texture["wet"] and texture["high_card"]:
            cbet_bluff_prob += 0.10
        if 0.25 < eq < 0.55 and cbet_bluff_prob > 0.35:
            return legal_raise_total(current_bet + max(int(pot * 0.5), 1), game_state)
        return {"action": "check"}

    # Facing a bet.
    if eq >= 0.80:
        target = current_bet * 3 if current_bet > 0 else max(int(pot * 0.66), 1)
        return legal_raise_total(target, game_state)
    if eq >= call_threshold:
        return {"action": "call"}
    return {"action": "fold"}
