"""Postflop strategy.

Flop / turn / river: joint multiway, action-conditioned range equity with
board-texture awareness, stack/side-pot gates, and overlay-aware c-bets.
Equity comes from `src.equity`; opponent reads come from `src.opponent_model`.

Adaptive trial caps range from 180 to 620 before opponent-count adjustment.
The synthetic six-max suite stays below roughly 120 ms on the development
machine, leaving substantial room inside the 2-second decision budget.

# Source: [[Cepheus-Bowling-2015]] — bucket-style state abstraction; the
#         safety gates bound a compact offline-trained mixed sizing lookup.
# Status: SHIPPED — conservative equity/commitment action gates with trained
#         abstract sizing mixes. This is not real-time solving.
"""
import hashlib
from typing import List

from src.blueprint_policy import sample_action as sample_blueprint_action
from src.commitment import (
    COMMIT_FRACTION,
    active_opponent_seats,
    call_cost,
    can_call_large,
    can_commit_raise,
    incremental_commitment_fraction,
    incremental_cost,
    pot_odds_to_call,
    side_pot_eligible_seats,
    stack_to_pot_ratio,
)
from src.equity import equity_vs_ranges, range_to_weighted_combos
from src.hand_features import classify_board, classify_hand, full_house_dominated
from src.opponent_model import get_model
from src.sizing import (
    is_full_raise_target,
    legal_raise_total,
    normalized_raise_total,
    pot_fraction_raise_total,
    pot_size_bet,
)


# Lightweight villain range archetypes for equity_vs_range. Used as priors
# when no model is warm.
PRIOR_RANGE_TIGHT = ["88+", "AT+", "KQs", "KJs"]
PRIOR_RANGE_LOOSE = ["22+", "A2+", "K9+", "QT+", "JT", "T9s", "98s"]

# Weighted preflop priors. Postflop action and board interaction reweight the
# physical combos below, so these are starting distributions rather than the
# old one-size-fits-all "tight" bettor range.
RANGE_UNKNOWN = {
    "22+": 0.75, "A2s+": 0.90, "A7o+": 0.55,
    "K7s+": 0.65, "K9o+": 0.45, "Q8s+": 0.58, "QTo+": 0.42,
    "J8s+": 0.50, "JTo": 0.40, "T8s+": 0.48,
    "98s": 0.52, "87s": 0.44, "76s": 0.38, "65s": 0.32, "54s": 0.28,
}
RANGE_CALL = {
    "22+": 0.85, "A2s+": 0.78, "A9o+": 0.48,
    "K8s+": 0.68, "KTo+": 0.44, "Q9s+": 0.62, "QTo+": 0.44,
    "J9s+": 0.62, "JTo": 0.44, "T8s+": 0.58,
    "98s": 0.64, "87s": 0.58, "76s": 0.50, "65s": 0.42, "54s": 0.36,
}
RANGE_AGGRESSIVE = {
    "66+": 0.88, "ATs+": 0.90, "AQo+": 0.92,
    "KTs+": 0.72, "KQo": 0.78, "QTs+": 0.62, "JTs": 0.62,
    "T9s": 0.48, "98s": 0.38, "87s": 0.30,
    "A2s": 0.35, "A3s": 0.35, "A4s": 0.35, "A5s": 0.42,
}
RANGE_RAISE = {
    "88+": 1.00, "AJs+": 0.90, "AQo+": 0.94,
    "KQs": 0.82, "KJs": 0.52, "QJs": 0.48, "JTs": 0.42,
    "T9s": 0.28, "98s": 0.22,
    "A2s": 0.24, "A3s": 0.24, "A4s": 0.26, "A5s": 0.34,
}
RANGE_SHALLOW_ALL_IN = {
    "44+": 1.00, "A7s+": 1.00, "ATo+": 0.96,
    "KTs+": 0.82, "KQo": 0.88, "QJs": 0.64, "JTs": 0.52,
    "T9s": 0.36, "A2s": 0.34, "A3s": 0.34, "A4s": 0.36, "A5s": 0.44,
}


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


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _players(state):
    players = state.get("players", []) if isinstance(state, dict) else []
    return players if isinstance(players, list) else []


def _player_by_seat(state, seat):
    for player in _players(state):
        if isinstance(player, dict) and player.get("seat") == seat:
            return player
    return None


def _is_folded(player):
    return bool(player.get("is_folded")) or player.get("state") == "folded"


def _all_in_is_aggressive(source, index, state, *, explicit):
    """Whether an all-in total strictly exceeds the price before it.

    Fullhouse logs the player's total street commitment for ``all_in``. A
    same-total or under-call all-in is therefore not an aggression.
    """
    entry = source[index]
    total = max(_int(entry.get("amount")), 0)
    if total <= 0:
        return False
    prior_price = 0
    for prior in source[:index]:
        if not isinstance(prior, dict):
            continue
        action = prior.get("action")
        if action not in ("bet", "raise", "all_in"):
            continue
        amount = max(_int(prior.get("amount")), 0)
        if not explicit:
            # In the cumulative unlabelled log, accept an earlier price only
            # when its total still equals that actor's live street commitment.
            player = _player_by_seat(state, prior.get("seat")) or {}
            if amount <= 0 or amount != max(_int(player.get("bet_this_street")), 0):
                continue
        if action in ("bet", "raise") or amount > prior_price:
            prior_price = max(prior_price, amount)
    return total > prior_price


def identify_aggressor(state: dict) -> int:
    """Best current-street aggressor from public bets and action history.

    Newer engines may attach a ``street`` field to log entries; older finals
    logs did not. For legacy logs we require the entry amount/player's current
    street commitment to match the live bet before falling back to the last
    non-folded aggressor. This prevents a preflop raise from being mistaken for
    the player who made the current flop/turn/river bet.
    """
    if not isinstance(state, dict):
        return -1
    hero = state.get("seat_to_act")
    current_bet = max(_int(state.get("current_bet")), 0)
    street = state.get("street")
    log = state.get("action_log", []) or []
    log = log if isinstance(log, list) else []
    aggressive = {"bet", "raise", "all_in"}
    explicit = [entry for entry in log
                if isinstance(entry, dict) and entry.get("street") == street]
    source = explicit if explicit else log

    # With the official unlabelled cumulative log, a zero live bet gives no
    # evidence that an old preflop/flop aggression belongs to this street.
    if not explicit and current_bet <= 0:
        return -1

    for index in range(len(source) - 1, -1, -1):
        entry = source[index]
        if not isinstance(entry, dict) or entry.get("action") not in aggressive:
            continue
        seat = entry.get("seat")
        player = _player_by_seat(state, seat)
        if seat == hero or (player is not None and _is_folded(player)):
            continue
        if entry.get("action") == "all_in" and not _all_in_is_aggressive(
            source, index, state, explicit=bool(explicit)
        ):
            continue
        if explicit:
            return seat if seat is not None else -1
        player_bet = max(_int(player.get("bet_this_street")) if player else 0, 0)
        action_total = max(_int(entry.get("amount")), 0)
        if action_total == current_bet and player_bet == current_bet:
            return seat if seat is not None else -1

    # With no usable log, a *unique* non-hero seat at the live maximum is the
    # only defensible aggressor reconstruction. Multiple equal commitments are
    # ambiguous (bettor plus callers), so fail closed in that case.
    candidates = []
    for player in _players(state):
        if not isinstance(player, dict) or player.get("seat") == hero or _is_folded(player):
            continue
        if max(_int(player.get("bet_this_street")), 0) == current_bet:
            candidates.append(player.get("seat"))
    if len(candidates) == 1 and candidates[0] is not None:
        return candidates[0]
    return -1


def _opponent_seat(state: dict) -> int:
    aggressor = identify_aggressor(state)
    if aggressor >= 0:
        return aggressor
    opponents = active_opponent_seats(state)
    return opponents[0] if opponents else -1


def action_context(state: dict, seat: int) -> dict:
    """Current-street public action context for one opponent."""
    player = _player_by_seat(state, seat) or {}
    street = state.get("street") if isinstance(state, dict) else None
    log = state.get("action_log", []) if isinstance(state, dict) else []
    log = log if isinstance(log, list) else []
    explicit = [entry for entry in log
                if isinstance(entry, dict) and entry.get("street") == street]
    source = explicit if explicit else log
    current_bet = max(_int(state.get("current_bet")) if isinstance(state, dict) else 0, 0)
    player_bet = max(_int(player.get("bet_this_street")), 0)
    aggressor = identify_aggressor(state)
    is_all_in = bool(player.get("is_all_in")) or player.get("state") == "all_in"
    raises = 0
    if explicit:
        latest = None
        street_aggressions = 0
        for index, entry in enumerate(source):
            if not isinstance(entry, dict):
                continue
            aggressive = entry.get("action") in ("bet", "raise") or (
                entry.get("action") == "all_in"
                and _all_in_is_aggressive(source, index, state, explicit=True)
            )
            if aggressive:
                street_aggressions += 1
            if entry.get("seat") == seat:
                latest = entry.get("action")
                if aggressive:
                    raises += 1
        if is_all_in and seat == aggressor:
            label = "all_in"
        elif seat == aggressor:
            label = "raise" if raises > 1 or street_aggressions > 1 else "bet"
        elif latest in ("call", "all_in") or (
            current_bet > 0 and player_bet == current_bet
        ):
            label = "call"
        elif latest == "check":
            label = "check"
        else:
            label = "unknown"
    else:
        # The official log has no street markers. Attribute only facts visible
        # in current commitments; never reuse a preflop call/check/raise.
        if is_all_in and seat == aggressor:
            label = "all_in"
            raises = 1
        elif seat == aggressor:
            prior_live_bet = any(
                isinstance(other, dict)
                and other.get("seat") != seat
                and 0 < max(_int(other.get("bet_this_street")), 0) < current_bet
                for other in _players(state)
            )
            label = "raise" if prior_live_bet else "bet"
            raises = int(prior_live_bet)
        elif current_bet > 0 and player_bet > 0 and (
            player_bet == current_bet or is_all_in
        ):
            label = "call"
        else:
            label = "unknown"
    pot = max(_int(state.get("pot")) if isinstance(state, dict) else 0, 0)
    owed = max(_int(state.get("amount_owed")) if isinstance(state, dict) else 0, 0)
    pressure = owed / max(pot - owed, 1) if owed else 0.0
    hero_start = (
        max(_int(state.get("your_stack")), 0)
        + max(_int(state.get("your_bet_this_street")), 0)
    ) if isinstance(state, dict) else 0
    opponent_start = max(_int(player.get("stack")), 0) + player_bet
    starting_spr = min(hero_start, opponent_start) / max(pot - owed, 1)
    return {
        "label": label,
        "is_aggressor": seat == aggressor,
        "raise_count": raises,
        "pressure": pressure,
        "starting_spr": starting_spr,
        "explicit_street": bool(explicit),
    }


def _model_archetype(model, seat, players):
    try:
        return model.archetype(seat, players)
    except TypeError:
        try:
            return model.archetype(seat)
        except Exception:
            return "unknown"
    except Exception:
        return "unknown"


def _model_shift(model, seat, players):
    try:
        return model.exploit_shift(seat, players)
    except TypeError:
        try:
            return model.exploit_shift(seat)
        except Exception:
            return {}
    except Exception:
        return {}


def _range_prior(context, archetype, spr):
    label = context.get("label")
    # SPR after a call is always zero against an all-in seat, so classify jam
    # depth from reconstructed pre-wager effective stack / pot instead.
    if label == "all_in" and context.get("starting_spr", spr) <= 4.0:
        prior = dict(RANGE_SHALLOW_ALL_IN)
    elif label == "all_in":
        prior = dict(RANGE_RAISE)
    elif label == "raise" or context.get("raise_count", 0) > 1:
        prior = dict(RANGE_RAISE)
    elif label in ("bet", "all_in"):
        prior = dict(RANGE_AGGRESSIVE)
    elif label == "call":
        prior = dict(RANGE_CALL)
    else:
        prior = dict(RANGE_UNKNOWN)

    if archetype in ("loose_aggressive", "loose_passive"):
        for tag, weight in RANGE_UNKNOWN.items():
            prior[tag] = max(prior.get(tag, 0.0), weight * 0.72)
    elif archetype in ("tight_aggressive", "tight_passive"):
        # Non-linear shrinkage matters after weighted normalization: low-mass
        # marginal/bluff tags contract more than already-high value tags.
        for tag in list(prior):
            prior[tag] = prior[tag] ** 1.35
    return prior


def _interaction_multiplier(features, context, archetype):
    category = features.get("category", "high_card")
    aggressive = context.get("label") in ("bet", "raise", "all_in")
    if aggressive:
        made = {
            "straight_flush": 3.0, "four_kind": 3.0, "full_house": 2.6,
            "flush": 2.1, "straight": 2.0, "trips": 1.8,
            "two_pair": 1.55, "pair": 0.82, "high_card": 0.28,
        }.get(category, 0.5)
        if features.get("combo_draw"):
            made = max(made, 1.45)
        elif features.get("has_flush_draw") or features.get("open_ended"):
            made = max(made, 1.05)
        elif features.get("gutshot"):
            made = max(made, 0.62)
        pressure = context.get("pressure", 0.0)
        if pressure >= 1.0 and category in ("pair", "high_card") and not features.get("combo_draw"):
            made *= 0.62
        elif pressure <= 0.45 and category in ("pair", "high_card"):
            made *= 1.18
        if archetype == "loose_aggressive" and category in ("pair", "high_card"):
            made *= 1.45
        if archetype in ("tight_passive", "loose_passive") and category == "high_card":
            made *= 0.55
        return made
    if context.get("label") == "call":
        made = {
            "straight_flush": 0.72, "four_kind": 0.72, "full_house": 0.78,
            "flush": 0.92, "straight": 0.96, "trips": 1.02,
            "two_pair": 1.14, "pair": 1.22, "high_card": 0.42,
        }.get(category, 0.8)
        if features.get("combo_draw"):
            made = max(made, 1.48)
        elif features.get("has_flush_draw") or features.get("open_ended"):
            made = max(made, 1.28)
        elif features.get("gutshot"):
            made = max(made, 0.78)
        return made
    return 1.0


def weighted_range_for(state: dict, seat: int, model=None, *, archetype=None):
    """Physical combo range conditioned on action, board and opponent profile."""
    model = get_model() if model is None and archetype is None else model
    players = _players(state)
    context = action_context(state, seat)
    archetype = archetype or _model_archetype(model, seat, players)
    spr = context.get("starting_spr", stack_to_pot_ratio(state, [seat], after_call=False))
    prior = _range_prior(context, archetype, spr)
    dead = list(state.get("your_cards", []) or []) + list(state.get("community_cards", []) or [])
    board = list(state.get("community_cards", []) or [])
    combos = range_to_weighted_combos(prior, dead)
    weighted = []
    for combo, base_weight in combos:
        hole = [str(combo[0]), str(combo[1])]
        features = classify_hand(hole, board)
        multiplier = _interaction_multiplier(features, context, archetype)
        weighted.append((combo, min(max(base_weight * multiplier, 0.01), 5.0)))
    return weighted


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


def _deterministic_roll(state, label) -> float:
    payload = repr((
        label,
        state.get("hand_id"),
        state.get("street"),
        tuple(state.get("your_cards", []) or []),
        tuple(state.get("community_cards", []) or []),
        len(state.get("action_log", []) or []),
    )).encode("utf-8")
    integer = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return integer / float(1 << 64)


def _trained_sizing(
    policy,
    state: dict,
    equity: float,
    texture: dict,
    spr: float,
    hand_info: dict,
    allowed,
):
    """Sample a trained size inside the heuristic action/safety envelope."""
    if policy is None or not allowed:
        return None
    if texture.get("monotone"):
        texture_name = "monotone"
    elif texture.get("paired"):
        texture_name = "paired"
    elif texture.get("wet"):
        texture_name = "wet"
    else:
        texture_name = "dry"

    owed = call_cost(state)
    pot = max(_int(state.get("pot")), 0)
    if bool(state.get("can_check")) or owed <= 0:
        pressure = "free"
    else:
        wager_ratio = owed / max(pot - owed, 1)
        pressure = "small" if wager_ratio <= 0.40 else (
            "medium" if wager_ratio <= 0.85 else "large"
        )

    category = hand_info.get("category")
    nutted = category in {"straight_flush", "four_kind"}
    nutted = nutted or bool(hand_info.get("nut_flush"))
    if category == "full_house":
        nutted = nutted or not full_house_dominated(
            state.get("your_cards", []) or [],
            state.get("community_cards", []) or [],
        )
    has_draw = bool(
        hand_info.get("combo_draw")
        or hand_info.get("has_flush_draw")
        or hand_info.get("open_ended")
        or hand_info.get("gutshot")
    )
    try:
        distribution = policy.postflop_distribution(
            state.get("street", "flop"),
            float(equity),
            texture=texture_name,
            pressure=pressure,
            spr=min(max(float(spr), 0.0), 1000.0),
            has_draw=has_draw,
            is_nutted=nutted,
        )
        filtered = {
            action: float(probability)
            for action, probability in distribution.items()
            if action in set(allowed) and float(probability) > 0.0
        }
        total = sum(filtered.values())
        if total <= 0.0:
            return None
        normalized = {action: probability / total for action, probability in filtered.items()}
        label = "trained|" + texture_name + "|" + pressure + "|" + ",".join(sorted(allowed))
        return sample_blueprint_action(
            normalized,
            _deterministic_roll(state, label),
        )
    except Exception:
        return None


def decide_postflop(
    game_state: dict,
    *,
    blueprint_only: bool = False,
    blueprint_policy=None,
) -> dict:
    """Equity-driven postflop decision. Always returns a legal action.

    `blueprint_only=True` skips the opponent-model overlay (used for the
    ablation benchmark to measure overlay contribution).
    """
    if not isinstance(game_state, dict):
        return {"action": "fold"}
    can_check = bool(game_state.get("can_check"))
    pot = max(_int(game_state.get("pot")), 0)
    my_stack = max(_int(game_state.get("your_stack")), 0)
    street = game_state.get("street", "flop")
    hole_value = game_state.get("your_cards", [])
    board_value = game_state.get("community_cards", [])
    hole = list(hole_value) if isinstance(hole_value, (list, tuple)) else []
    board = list(board_value) if isinstance(board_value, (list, tuple)) else []
    if my_stack <= 0:
        return {"action": "check"} if can_check else {"action": "call"}
    if len(hole) != 2:
        return {"action": "check"} if can_check else {"action": "fold"}

    texture = classify_board(board)
    model = get_model()
    opponents = active_opponent_seats(game_state)
    aggressor = identify_aggressor(game_state)
    opp = aggressor if aggressor >= 0 else (opponents[0] if opponents else -1)
    players = _players(game_state)
    if blueprint_only or opp < 0:
        shift = {"widen_open": 0.0, "cbet_bluff_more": 0.0,
                 "value_thinner": 0.0, "bluff_catch_less": 0.0,
                 "tighten_open": 0.0, "fold_to_pressure_less": 0.0,
                 "value_widen_vs_aggro": 0.0}
        archetype = "unknown"
    else:
        shift = _model_shift(model, opp, players)
        archetype = _model_archetype(model, opp, players)

    # Joint, action-conditioned equity. Every live opponent receives its own
    # range and all hole-card samples are collision-free. When player metadata
    # is unavailable, retain a single broad fallback instead of pretending
    # that no opponent exists.
    ranges_by_seat = {}
    for seat in opponents:
        ranges_by_seat[seat] = weighted_range_for(
            game_state, seat, model=None if blueprint_only else model,
            archetype="unknown" if blueprint_only else None,
        )
    villain_ranges = [ranges_by_seat[seat] for seat in opponents]
    if not villain_ranges:
        villain_ranges = [PRIOR_RANGE_LOOSE]

    pot_odds = pot_odds_to_call(game_state)
    owed_chips = call_cost(game_state)
    owed_frac = owed_chips / my_stack if my_stack > 0 else 1.0
    spr = stack_to_pot_ratio(
        game_state, [aggressor] if aggressor >= 0 else opponents, after_call=True
    )
    # Small realization buffer when chips remain behind; all-in calls realize
    # all equity and are judged directly against pot odds.
    realization_buffer = 0.018 * max(1.0 - owed_frac, 0.0)
    if texture.get("wet") and street != "river":
        realization_buffer += 0.006
    call_threshold = pot_odds + realization_buffer
    if archetype == "loose_passive":
        call_threshold -= shift.get("value_thinner", 0.0) * 0.3
    if shift.get("bluff_catch_less", 0.0) > 0 and street == "river":
        call_threshold += shift["bluff_catch_less"] * 0.3
    # Against hyper-aggressive villains: their large bets carry less info,
    # so we don't fold to pressure as easily on rivers with marginal hands.
    if shift.get("fold_to_pressure_less", 0.0) > 0 and street == "river":
        call_threshold -= shift["fold_to_pressure_less"] * 0.3
    call_threshold = min(max(call_threshold, 0.0), 1.0)

    base_trials = {"flop": 620, "turn": 480, "river": 320}.get(street, 420)
    # Bound total eval7 work as the table grows. With five opponents this is
    # 180 rollouts / 1,080 native evaluations, comfortably inside 2 seconds.
    base_trials = max(180, int(base_trials * 2 / max(len(villain_ranges) + 1, 2)))
    eq = equity_vs_ranges(
        hole,
        board,
        villain_ranges,
        trials=base_trials,
        threshold=call_threshold if not can_check else None,
        target_se=0.022,
        adaptive=True,
        use_native=True,
    )

    opponent_count = max(len(villain_ranges), 1)
    value_threshold_strong = max(0.43, 0.72 - 0.07 * (opponent_count - 1))
    value_threshold_thin = max(0.34, 0.56 - 0.045 * (opponent_count - 1))
    if shift.get("value_widen_vs_aggro", 0.0) > 0:
        value_threshold_thin -= shift["value_widen_vs_aggro"] * 0.2

    hero_features = classify_hand(hole, board)

    if can_check:
        # No opponent with chips behind can call another bet (all-in-only pot).
        can_be_called = any(
            max(_int((_player_by_seat(game_state, seat) or {}).get("stack")), 0) > 0
            for seat in opponents
        )
        if not can_be_called and opponents:
            return {"action": "check"}
        if eq >= value_threshold_strong:
            trained = _trained_sizing(
                blueprint_policy, game_state, eq, texture, spr, hero_features,
                {"bet_small", "bet_large"},
            )
            fraction = {"bet_small": 0.33, "bet_large": 0.75}.get(
                trained,
                0.75 if texture.get("wet") or opponent_count > 1 else 0.66,
            )
            return pot_size_bet(pot, game_state, fraction=fraction)
        if eq >= value_threshold_thin and not (texture.get("wet") and opponent_count > 2):
            trained = _trained_sizing(
                blueprint_policy, game_state, eq, texture, spr, hero_features,
                {"bet_small", "bet_large"},
            )
            fraction = {"bet_small": 0.33, "bet_large": 0.75}.get(trained, 0.50)
            return pot_size_bet(pot, game_state, fraction=fraction)
        cbet_bluff_prob = (0.30 + shift.get("cbet_bluff_more", 0.0)) / opponent_count
        if street == "flop" and not texture["wet"] and texture["high_card"]:
            cbet_bluff_prob += 0.10
        if hero_features.get("combo_draw"):
            cbet_bluff_prob += 0.12
        elif hero_features.get("has_flush_draw") or hero_features.get("open_ended"):
            cbet_bluff_prob += 0.07
        cbet_bluff_prob = min(max(cbet_bluff_prob, 0.0), 0.65)
        fair_share = 1.0 / (opponent_count + 1)
        if (fair_share * 0.50 < eq < value_threshold_thin
                and _deterministic_roll(game_state, "cbet") < cbet_bluff_prob):
            trained = _trained_sizing(
                blueprint_policy, game_state, eq, texture, spr, hero_features,
                {"bet_small", "bet_large"},
            )
            fraction = {"bet_small": 0.33, "bet_large": 0.75}.get(
                trained,
                0.33 if not texture.get("wet") else 0.50,
            )
            return pot_size_bet(pot, game_state, fraction=fraction)
        return {"action": "check"}

    call_ok = can_call_large(eq, pot_odds, owed_frac) and eq >= call_threshold
    # Preserve the measured near-dead leak fix without reinstating the old
    # blanket 25%-of-stack cap: only a structurally dominated full house facing
    # a large commitment is forced out here.
    if owed_frac >= COMMIT_FRACTION and full_house_dominated(hole, board):
        call_ok = False
    raise_threshold = max(0.61, pot_odds + 0.24)
    if opponent_count > 1:
        raise_threshold = max(0.48, raise_threshold - 0.045 * (opponent_count - 1))
    if spr <= 1.0:
        raise_threshold -= 0.03

    if eq >= raise_threshold:
        trained = _trained_sizing(
            blueprint_policy, game_state, eq, texture, spr, hero_features,
            {"raise_small", "raise_large"},
        )
        fraction = {"raise_small": 0.55, "raise_large": 1.0}.get(trained, 0.66)
        raw_target = pot_fraction_raise_total(pot, game_state, fraction=fraction)
        target = normalized_raise_total(raw_target, game_state)
        # Recheck the min raise *before* applying the stack-off gate. Snapping a
        # small intended target up to a large legal minimum must not bypass the
        # commitment calculation.
        if is_full_raise_target(target, game_state):
            eligible = side_pot_eligible_seats(game_state, target)
            if eligible:
                raise_eq = eq
                if set(eligible) != set(opponents):
                    eligible_ranges = [ranges_by_seat[seat]
                                       for seat in eligible if seat in ranges_by_seat]
                    if eligible_ranges:
                        raise_eq = equity_vs_ranges(
                            hole, board, eligible_ranges,
                            trials=max(160, base_trials // 2),
                            threshold=0.55, target_se=0.03,
                        )
                commit_fraction = incremental_commitment_fraction(target, game_state)
                # ``incremental_cost`` is intentionally evaluated after target
                # normalization; it includes call + raise but excludes chips
                # hero already put in this street.
                commit_chips = incremental_cost(target, game_state)
                commit_ok = can_commit_raise(hole, board, raise_eq)
                if commit_chips > 0 and (
                    commit_fraction < COMMIT_FRACTION or commit_ok
                ):
                    return legal_raise_total(target, game_state)

    if call_ok:
        return {"action": "call"}
    return {"action": "fold"}
