"""PokerBot — `decide(game_state) -> dict`.

Schema and return shapes are documented in `docs/api-cheatsheet.md`; ground
truth lives in `ext/fullhouse-engine/sandbox/validator.py::TEST_STATES`.

The shipped archive places a tiny shim at `bot.py` (archive root) that does
`from src.bot import decide`. Heavy loads (blueprints, eval7 LUTs) happen at
module import — the engine's one-shot 30 s warmup call covers them so live
2 s decisions stay fast.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

DATA_DIR = os.environ.get(
    "BOT_DATA_DIR",
    os.path.join(os.path.dirname(_HERE), "data"),
)

try:
    from src.opponent_model import OpponentModel
    from src.preflop_lookup import lookup as _preflop_lookup
    from src.postflop import decide_postflop as _decide_postflop
    from src.ranges import canonical_hand, hand_score
    from src.sizing import sizing_to_amount
    from src.timeout_guard import run_with_budget
except ImportError:  # direct runner load from src/bot.py
    from opponent_model import OpponentModel
    from preflop_lookup import lookup as _preflop_lookup
    from postflop import decide_postflop as _decide_postflop
    from ranges import canonical_hand, hand_score
    from sizing import sizing_to_amount
    from timeout_guard import run_with_budget

_VALID_ACTIONS = {"fold", "check", "call", "raise", "all_in"}
_OVERLAY_DISABLED = os.environ.get("POKERBOT_DISABLE_OVERLAY") == "1"
_OPPONENT_MODEL = OpponentModel()


def _safe_fallback(game_state: dict) -> dict:
    """Last-resort legal action. Never raises."""
    if isinstance(game_state, dict) and game_state.get("can_check"):
        return {"action": "check"}
    return {"action": "fold"}


def _legalize_action(game_state: dict, raw_action: dict) -> dict:
    """Normalize strategy output to one of the engine's valid action shapes."""
    # Source: [[Engine-Fullhouse]]
    if not isinstance(game_state, dict) or not isinstance(raw_action, dict):
        return _safe_fallback(game_state)

    action = str(raw_action.get("action", "")).lower().strip()
    if action not in _VALID_ACTIONS:
        return _safe_fallback(game_state)

    if action == "check":
        if game_state.get("can_check"):
            return {"action": "check"}
        return {"action": "call"}

    if action == "call":
        if game_state.get("can_check"):
            return {"action": "check"}
        return {"action": "call"}

    if action == "raise":
        try:
            amount = int(raw_action.get("amount"))
        except (TypeError, ValueError):
            return _safe_fallback(game_state)
        min_raise_to = int(game_state.get("min_raise_to") or 0)
        stack_total = int(game_state.get("your_stack") or 0) + int(
            game_state.get("your_bet_this_street") or 0
        )
        if stack_total <= 0:
            return _safe_fallback(game_state)
        amount = max(amount, min_raise_to)
        if amount >= stack_total:
            return {"action": "all_in"}
        return {"action": "raise", "amount": amount}

    if action == "all_in":
        return {"action": "all_in"}

    return {"action": "fold"}


def _decide_core(game_state: dict) -> dict:
    """Fast deterministic baseline. Later gates refine the table and overlay."""
    street = game_state.get("street")
    if street == "preflop":
        return _decide_preflop(game_state)
    if street in ("flop", "turn", "river"):
        return _decide_postflop(game_state)
    return _safe_fallback(game_state)


def _position_label(game_state: dict) -> str:
    players = game_state.get("players") or []
    seat = int(game_state.get("seat_to_act") or 0)
    if len(players) == 2:
        if game_state.get("street") == "preflop":
            voluntary = [
                item.get("action")
                for item in game_state.get("action_log") or []
                if isinstance(item, dict) and item.get("action") not in ("small_blind", "big_blind")
            ]
            if not voluntary and not game_state.get("can_check"):
                return "heads_up_button"
            return "big_blind"
        return "heads_up_button" if seat == 0 else "big_blind"
    if len(players) >= 2 and seat >= len(players) - 2:
        return "button"
    if seat <= 1:
        return "early"
    return "middle"


def _action_sequence(game_state: dict) -> tuple:
    actions = []
    for item in game_state.get("action_log") or []:
        action = item.get("action") if isinstance(item, dict) else None
        if action:
            actions.append(str(action).lower())
    return tuple(actions)


def _decide_preflop(game_state: dict) -> dict:
    hand = canonical_hand(game_state.get("your_cards") or [])
    if not _OVERLAY_DISABLED:
        overlay = _pressure_preflop_overlay(game_state, hand)
        if overlay is not None:
            return overlay
    decision = _preflop_lookup(_position_label(game_state), hand, _action_sequence(game_state))
    if not decision:
        return _safe_fallback(game_state)

    action = decision.get("action")
    if action != "raise":
        return {"action": action}

    amount = decision.get("amount")
    if amount is None:
        amount = sizing_to_amount(
            decision.get("sizing", "min_raise"),
            game_state.get("pot", 0),
            game_state.get("your_stack", 0),
            game_state.get("min_raise_to", 0),
            game_state.get("your_bet_this_street", 0),
        )
    return {"action": "raise", "amount": amount}


def _pressure_preflop_overlay(game_state: dict, hand: str):
    """Tighten against observed high-pressure or fold-prone raising patterns."""
    # Source: [[Libratus-Brown-Sandholm-2017]]
    features = _OPPONENT_MODEL.pressure_features(game_state)
    if not (features["high_pressure"] or features["fold_prone_pressure"]):
        return None

    score = hand_score(hand)
    if features["fold_prone_pressure"]:
        if features["facing_raise"] and score >= 88:
            return {"action": "all_in"}
        if features["facing_raise"] and score >= 58:
            return {"action": "call"}
        return None

    if features["high_pressure"]:
        if score >= 72:
            return {"action": "all_in"}
        if game_state.get("can_check"):
            return {"action": "check"}
        return {"action": "fold"}

    return None


def decide(game_state: dict) -> dict:
    """Return a legal action for the given game_state."""
    if isinstance(game_state, dict) and game_state.get("type") == "warmup":
        return {"action": "check"}
    try:
        if not isinstance(game_state, dict):
            return {"action": "fold"}
        return run_with_budget(
            lambda state: _legalize_action(state, _decide_core(state)),
            _safe_fallback,
            game_state,
        )
    except Exception:
        return {"action": "fold"}
