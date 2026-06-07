"""PokerBot — `decide(game_state) -> dict`.

Schema and return shapes are documented in `docs/api-cheatsheet.md`; ground
truth lives in `ext/fullhouse-engine/sandbox/validator.py::TEST_STATES`.

The shipped archive places a tiny shim at `bot.py` (archive root) that does
`from src.bot import decide`. Heavy loads (blueprints, eval7 LUTs) happen at
module import — the engine's one-shot 30 s warmup call covers them so live
2 s decisions stay fast.

# Source: [[Pluribus-Brown-Sandholm-2019]] — blueprint + bounded overlay
"""
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

DATA_DIR = os.environ.get(
    "BOT_DATA_DIR",
    os.path.join(os.path.dirname(_HERE), "data"),
)

# Eager imports — covered by the 30 s warmup. eval7 LUT pre-warm happens in
# src.equity at import time.
try:
    from src.equity import canonical_hand
    from src.preflop_lookup import lookup as _preflop_lookup
    from src.postflop import decide_postflop as _decide_postflop
    from src.opponent_model import get_model as _get_model
    from src.sizing import (
        legal_raise_total,
        open_raise_total,
        threebet_total,
    )
    from src.timeout_guard import run_with_budget
    _MODULES_OK = True
except Exception:
    # If anything fails at import, we still want decide() to be callable.
    _MODULES_OK = False


def _safe_fallback(game_state) -> dict:
    """Last-resort legal action. Never raises."""
    if isinstance(game_state, dict) and game_state.get("can_check"):
        return {"action": "check"}
    return {"action": "fold"}


def _legalize_action(state, action) -> dict:
    """Final-layer legalizer for any proposed action.

    Snaps below-min raises up to `min_raise_to`, converts over-stack raises
    to all-in, validates `amount` is a non-negative int, and falls back to a
    safe action on malformed inputs. Belt-and-suspenders defense after
    `sizing.legal_raise_total` — catches any future regression that produces
    a negative or non-int amount.
    """
    safe = _safe_fallback(state)
    if not isinstance(action, dict):
        return safe
    act = action.get("action")
    if act in ("fold", "check", "call", "all_in"):
        if act == "check" and not (isinstance(state, dict) and state.get("can_check")):
            return safe
        return {"action": act}
    if act != "raise":
        return safe
    try:
        amount = int(action.get("amount"))
    except (TypeError, ValueError):
        return safe
    if not isinstance(state, dict):
        return {"action": "fold"}
    try:
        my_stack = int(state.get("your_stack", 0))
        my_bet = int(state.get("your_bet_this_street", 0))
        min_raise_to = int(state.get("min_raise_to", 0))
    except (TypeError, ValueError):
        return safe
    if amount < min_raise_to:
        amount = min_raise_to
    if amount <= 0:
        return safe
    chips_needed = amount - my_bet
    if my_stack <= 0 or chips_needed <= 0:
        return safe
    if chips_needed >= my_stack:
        return {"action": "all_in"}
    return {"action": "raise", "amount": int(amount)}


def _infer_position(state: dict) -> str:
    """Best-effort position label from action_log and player count."""
    players = state.get("players", []) or []
    n = len(players)
    seat = state.get("seat_to_act", 0)
    if n == 2:
        # Heads-up: SB = dealer. Determine from action_log small_blind entry.
        for entry in state.get("action_log", []) or []:
            if entry.get("action") == "small_blind":
                return "SB" if entry.get("seat") == seat else "BB"
        return "SB"
    # 6-max approximation: count blinds, then label by distance from BTN.
    sb_seat = None
    bb_seat = None
    for entry in state.get("action_log", []) or []:
        if entry.get("action") == "small_blind":
            sb_seat = entry.get("seat")
        elif entry.get("action") == "big_blind":
            bb_seat = entry.get("seat")
    if sb_seat is None or bb_seat is None:
        # Fallback: assume seat 0 is SB.
        sb_seat = 0
        bb_seat = (sb_seat + 1) % n
    btn_seat = (sb_seat - 1) % n
    offset = (seat - btn_seat) % n
    # offset: 0=BTN, 1=SB, 2=BB, 3=UTG, 4=MP, 5=CO (and continuing for >6)
    labels = ["BTN", "SB", "BB", "UTG", "MP", "HJ", "CO"]
    if offset >= len(labels):
        return "UTG"
    label = labels[offset]
    if label == "HJ":
        return "MP"
    return label


def _action_sequence_preflop(state: dict) -> tuple:
    """Build a coarse (raise/call/fold) action sequence ahead of us preflop.
    Skips blinds and our own bets."""
    seq = []
    my_seat = state.get("seat_to_act")
    for entry in state.get("action_log", []) or []:
        if entry.get("action") in ("small_blind", "big_blind"):
            continue
        if entry.get("seat") == my_seat:
            continue
        act = entry.get("action")
        if act == "raise" or act == "all_in":
            seq.append("raise")
        elif act == "call":
            seq.append("call")
        elif act == "fold":
            seq.append("fold")
    return tuple(seq)


def _preflop_action(state: dict) -> dict:
    """Resolve a preflop decision: blueprint tag → legal action."""
    hole = state.get("your_cards", []) or []
    if len(hole) != 2:
        return _safe_fallback(state)
    hand = canonical_hand(hole)
    pos = _infer_position(state)
    seq = _action_sequence_preflop(state)
    overlay_off = os.environ.get("DISABLE_OVERLAY") == "1"
    overlay_legacy = os.environ.get("OVERLAY_LEGACY") == "1"
    widen = 0.0
    if not overlay_off and not overlay_legacy:
        try:
            model = _get_model()
            # Find the opponent seat for the widen_open lookup.
            me = state.get("seat_to_act", -1)
            opp_seat = None
            for p in state.get("players", []) or []:
                if p.get("seat") != me and not p.get("is_folded"):
                    opp_seat = p.get("seat")
                    break
            if opp_seat is not None:
                widen = float(model.exploit_shift(opp_seat).get("widen_open", 0.0))
        except Exception:
            widen = 0.0
    decision = _preflop_lookup(pos, hand, seq, widen_open=widen,
                               blueprint_only=overlay_off)
    tag = decision.get("tag", "fold")
    can_check = bool(state.get("can_check"))
    current_bet = int(state.get("current_bet", 0))
    pot = int(state.get("pot", 0))
    my_stack = int(state.get("your_stack", 0))
    my_bet = int(state.get("your_bet_this_street", 0))
    min_raise_to = int(state.get("min_raise_to", 0))

    if tag == "fold":
        if can_check:
            return {"action": "check"}
        return {"action": "fold"}
    if tag == "check":
        if can_check:
            return {"action": "check"}
        # If "check" wasn't actually free, fall through to call/fold decision.
        return {"action": "fold"}
    if tag == "call":
        if can_check:
            return {"action": "check"}
        return {"action": "call"}
    if tag == "all_in":
        return {"action": "all_in"}

    # Raise tags
    if tag == "open":
        # 2.5 BB open from CO/BTN; 3 BB from earlier; 3 BB SB vs BB
        bb = 100
        mult = 2.5 if pos in ("CO", "BTN", "SB") else 3.0
        target = max(int(round(bb * mult)), min_raise_to)
        return legal_raise_total(target, state)
    if tag == "iso_raise":
        # Iso over limpers — 4 BB + 1 BB per limper.
        bb = 100
        n_limps = sum(1 for e in (state.get("action_log") or [])
                      if e.get("action") == "call")
        target = max(int(bb * (4 + n_limps)), min_raise_to)
        return legal_raise_total(target, state)
    if tag == "threebet":
        # ~3x the raise IP, 3.5-4x OOP. Use current_bet as raise size.
        mult = 3.0 if pos in ("BTN", "CO") else 3.5
        target = max(int(current_bet * mult), min_raise_to)
        return legal_raise_total(target, state)
    if tag == "fourbet":
        # 2.2-2.5x the 3-bet.
        target = max(int(current_bet * 2.3), min_raise_to)
        return legal_raise_total(target, state)
    # Unknown tag → safe fallback.
    return _safe_fallback(state)


def _strategy(game_state: dict) -> dict:
    """Real strategy entrypoint. Caller wraps with timeout/safety guards."""
    if not isinstance(game_state, dict):
        return {"action": "fold"}
    if game_state.get("type") == "warmup":
        return {"action": "check"}
    # Update opponent model from the rolling match_action_log.
    log = game_state.get("match_action_log") or []
    try:
        _get_model().observe_log(log, game_state.get("hand_id"))
    except Exception:
        pass

    street = game_state.get("street", "preflop")
    if street == "preflop":
        return _preflop_action(game_state)
    return _decide_postflop(game_state)


def decide(game_state) -> dict:
    """Return a legal action for the given game_state.

    Never raises. Times itself with a soft 1.2 s budget and falls back to a
    legal safe action if the strategy stack misbehaves.

    SAFE_FALLBACK_ONLY=1 short-circuits the strategy stack entirely — used
    for the v0_wired snapshot to capture the "wired but no strategy yet"
    floor at the G1 gate.
    """
    try:
        if not isinstance(game_state, dict):
            return {"action": "fold"}
        if game_state.get("type") == "warmup":
            return {"action": "check"}
        if os.environ.get("SAFE_FALLBACK_ONLY") == "1":
            return _legalize_action(game_state, _safe_fallback(game_state))
        if not _MODULES_OK:
            return _legalize_action(game_state, _safe_fallback(game_state))
        action = run_with_budget(_strategy, _safe_fallback, game_state)
        return _legalize_action(game_state, action)
    except Exception:
        return _safe_fallback(game_state) if isinstance(game_state, dict) else {"action": "fold"}
