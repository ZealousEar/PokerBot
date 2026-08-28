"""PokerBot — `decide(game_state) -> dict`.

Schema and return shapes are documented in `docs/api-cheatsheet.md`; ground
truth lives in `ext/fullhouse-engine/sandbox/validator.py::TEST_STATES`.

The shipped archive places a tiny shim at `bot.py` (archive root) that does
`from src.bot import decide`. Heavy loads (blueprints, eval7 LUTs) happen at
module import — the engine's one-shot 30 s warmup call covers them so live
2 s decisions stay fast.

# Source: [[Pluribus-Brown-Sandholm-2019]] — blueprint + bounded overlay
# Status: SHIPPED architecture (trained abstract mixed policy inside conservative
#         hand/stack safety charts, plus a bounded identity-stable overlay).
"""
import hashlib
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
    from src.blueprint_policy import (
        DEFAULT_ARTIFACT as _BLUEPRINT_ARTIFACT,
        BlueprintPolicy as _BlueprintPolicy,
        sample_action as _sample_blueprint_action,
    )
    from src.equity import canonical_hand
    from src.preflop_lookup import lookup as _preflop_lookup
    from src.ranges import POSITIONS_BY_TABLE_SIZE
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


# Artifact failure must not turn every decision into the safe fallback. The
# trained policy is an import-time enhancement inside the hand-tuned safety
# envelope; a missing/tampered artifact cleanly falls back to that envelope.
_BLUEPRINT = None
if _MODULES_OK:
    try:
        _BLUEPRINT = _BlueprintPolicy.load(
            os.path.join(DATA_DIR, _BLUEPRINT_ARTIFACT),
            verify_digest=True,
        )
    except Exception:
        _BLUEPRINT = None


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


def _as_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return int(default)


def _policy_draw(state: dict, context: str) -> float:
    """Stable mixed-policy draw in ``[0, 1)`` for reproducible replays.

    Python's process-randomized ``hash()`` is deliberately avoided. Identical
    paired benchmark states receive identical draws, while ``hand_id`` makes
    the same information set mix across hands.
    """
    history = []
    for entry in state.get("action_log", []) or []:
        if isinstance(entry, dict):
            history.append((
                entry.get("seat"),
                entry.get("action"),
                entry.get("amount"),
                entry.get("street"),
            ))
    payload = repr((
        "blueprint-v1",
        context,
        state.get("hand_id"),
        state.get("seat_to_act"),
        state.get("street"),
        tuple(state.get("your_cards", []) or []),
        tuple(state.get("community_cards", []) or []),
        tuple(history),
    )).encode("utf-8")
    integer = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return integer / float(1 << 64)


def _preflop_blueprint_choice(
    state: dict, position: str, hand: str, context: dict, base_tag: str
):
    """Return one trained sizing inside an already-permitted chart action.

    The tiny training game is useful for mixing its discrete sizes, but is not
    trusted to reverse the full chart's fold/call/raise decision. Filtering and
    renormalizing here keeps Stage 2's price/range guarantees intact.
    """
    if _BLUEPRINT is None or os.environ.get("DISABLE_TRAINED_BLUEPRINT") == "1":
        return None
    full_raises = max(0, _as_int(context.get("full_raise_count"), 0))
    if full_raises == 0:
        pressure = "limped" if _as_int(context.get("limp_count"), 0) else "unopened"
    elif full_raises == 1:
        pressure = "open"
    elif full_raises == 2:
        pressure = "threebet"
    else:
        pressure = "fourbet"
    try:
        distribution = _BLUEPRINT.preflop_distribution(
            position,
            hand,
            pressure=pressure,
            effective_stack_bb=float(context.get("effective_stack_bb", 100.0)),
        )
        allowed = {
            "open": {"open_small", "open_large"},
            "iso_raise": {"iso_small", "iso_large"},
            "threebet": {"threebet_small", "threebet_large"},
            "fourbet": {"fourbet_small"},
        }.get(base_tag, set())
        filtered = {
            action: float(probability)
            for action, probability in distribution.items()
            if action in allowed and float(probability) > 0.0
        }
        total = sum(filtered.values())
        if total <= 0.0:
            return None
        normalized = {action: probability / total for action, probability in filtered.items()}
        key = f"preflop|{position}|{pressure}|{hand}|{base_tag}"
        return _sample_blueprint_action(normalized, _policy_draw(state, key))
    except Exception:
        return None


def _mix_preflop_tag(base_tag: str, abstract_action, hand: str, can_check: bool) -> str:
    """Compatibility hook: trained abstraction never changes chart category."""
    return base_tag


def _blind_size(state: dict) -> int:
    """Return the tournament's nominal BB, even when a short BB posts less."""
    posted = []
    for entry in state.get("action_log", []) or []:
        if isinstance(entry, dict) and entry.get("action") == "big_blind":
            posted.append(_as_int(entry.get("amount"), 0))
    # Fullhouse uses fixed 50/100 blinds.  max(100, posted) keeps a short
    # all-in blind from making every later stack appear artificially deep.
    return max([100] + posted)


def _position_for_seat(state: dict, target_seat: int) -> str:
    """Map an engine seat to the appropriate 2--9 handed lookup position.

    Seat numbers are compacted after eliminations.  Blind posts therefore
    provide the only reliable per-hand anchor.  The table in `src.ranges`
    deliberately collapses extra full-ring seats into the six-max UTG/MP
    charts while preserving BTN/CO/blind identities.
    """
    players = state.get("players", []) or []
    n = len(players) if isinstance(players, list) else 0
    if n < 2 or n > 9:
        return "UTG"

    sb_seat = None
    bb_seat = None
    for entry in state.get("action_log", []) or []:
        if not isinstance(entry, dict):
            continue
        action = entry.get("action")
        if action == "small_blind":
            sb_seat = _as_int(entry.get("seat"), -1)
        elif action == "big_blind":
            bb_seat = _as_int(entry.get("seat"), -1)

    if n == 2:
        # Heads-up: dealer/button == small blind.
        button = sb_seat if sb_seat is not None and sb_seat >= 0 else 0
    elif sb_seat is not None and sb_seat >= 0:
        button = (sb_seat - 1) % n
    elif bb_seat is not None and bb_seat >= 0:
        button = (bb_seat - 2) % n
    else:
        # Malformed-state fallback only; official action requests log blinds.
        button = 0

    offset = (_as_int(target_seat, 0) - button) % n
    return POSITIONS_BY_TABLE_SIZE[n][offset]


def _infer_position(state: dict) -> str:
    return _position_for_seat(state, _as_int(state.get("seat_to_act"), 0))


def _reconstruct_preflop(state: dict) -> dict:
    """Replay the normalized engine action log into a priced betting state.

    Engine amounts are action-specific: calls are chips owed, while raises
    and all-ins are total street bets.  Hero actions are intentionally kept;
    deleting them turns hero-open/opponent-3-bet into a false single-open
    spot.  Short all-ins are aggression but increase the full-raise count only
    when their increment meets the prior minimum full raise.
    """
    log = state.get("action_log", []) or []
    if not isinstance(log, list):
        log = []
    hero_seat = _as_int(state.get("seat_to_act"), -1)
    bb = _blind_size(state)
    seat_bets = {}
    price = 0

    # Forced bets establish the initial price but are not voluntary actions.
    for entry in log:
        if not isinstance(entry, dict):
            continue
        action = str(entry.get("action", "")).lower()
        if action not in ("small_blind", "big_blind"):
            continue
        seat = _as_int(entry.get("seat"), -1)
        amount = max(0, _as_int(entry.get("amount"), 0))
        seat_bets[seat] = max(seat_bets.get(seat, 0), amount)
        price = max(price, amount)

    last_full_raise_size = bb
    full_raise_count = 0
    hero_full_raise_count = 0
    hero_called = False
    limp_count = 0
    callers_since_raise = 0
    sequence = []
    actions = []
    last_full_raiser = None
    last_price_aggressor = None

    for index, entry in enumerate(log):
        if not isinstance(entry, dict):
            continue
        raw_action = str(entry.get("action", "")).lower()
        if raw_action in ("small_blind", "big_blind"):
            continue
        seat = _as_int(entry.get("seat"), -1)
        amount = max(0, _as_int(entry.get("amount"), 0))
        before_price = price
        before_bet = seat_bets.get(seat, 0)
        is_hero = seat == hero_seat
        detail = {
            "index": index,
            "seat": seat,
            "position": _position_for_seat(state, seat),
            "raw_action": raw_action,
            "amount": amount,
            "is_hero": is_hero,
            "price_before": before_price,
        }

        if raw_action == "raise":
            total = max(before_bet, amount)
            increment = max(0, total - before_price)
            is_full = increment >= last_full_raise_size and total > before_price
            if total > before_price:
                price = total
                last_price_aggressor = detail
                if is_full:
                    full_raise_count += 1
                    last_full_raise_size = increment
                    last_full_raiser = detail
                    callers_since_raise = 0
                    if is_hero:
                        hero_full_raise_count += 1
                elif not is_hero:
                    callers_since_raise += 1
            seat_bets[seat] = total
            detail.update({
                "kind": "full_raise" if is_full else "short_raise",
                "coarse_action": "raise",
                "amount_to": total,
                "raise_increment": increment,
                "is_full_raise": is_full,
                "is_all_in": False,
            })
            sequence.append("raise")

        elif raw_action == "all_in":
            # The normalized engine log records TOTAL bet for all-in.
            total = max(before_bet, amount)
            increment = max(0, total - before_price)
            if total <= before_price:
                detail.update({
                    "kind": "all_in_call",
                    "coarse_action": "call",
                    "amount_to": total,
                    "raise_increment": 0,
                    "is_full_raise": False,
                    "is_all_in": True,
                })
                if full_raise_count == 0:
                    limp_count += 1
                elif not is_hero:
                    callers_since_raise += 1
                if is_hero:
                    hero_called = True
                sequence.append("call")
            else:
                is_full = increment >= last_full_raise_size
                price = total
                last_price_aggressor = detail
                if is_full:
                    full_raise_count += 1
                    last_full_raise_size = increment
                    last_full_raiser = detail
                    callers_since_raise = 0
                    if is_hero:
                        hero_full_raise_count += 1
                elif full_raise_count == 0:
                    limp_count += 1
                elif not is_hero:
                    # A short all-in does not reopen action, but a cold player
                    # behind still faces its higher price; treat it as a caller
                    # for range-strength purposes.
                    callers_since_raise += 1
                detail.update({
                    "kind": "full_all_in_raise" if is_full else "short_all_in_raise",
                    "coarse_action": "raise",
                    "amount_to": total,
                    "raise_increment": increment,
                    "is_full_raise": is_full,
                    "is_all_in": True,
                })
                sequence.append("raise")
            seat_bets[seat] = total

        elif raw_action == "call":
            owed_before = max(0, before_price - before_bet)
            # Calls log amount owed.  The player may actually contribute less
            # when short, which does not change the table price.
            seat_bets[seat] = before_bet + min(amount, owed_before)
            detail.update({
                "kind": "call",
                "coarse_action": "call",
                "amount_to": seat_bets[seat],
                "is_full_raise": False,
                "is_all_in": False,
            })
            if full_raise_count == 0:
                limp_count += 1
            elif not is_hero:
                callers_since_raise += 1
            if is_hero:
                hero_called = True
            sequence.append("call")

        elif raw_action in ("fold", "check"):
            detail.update({
                "kind": raw_action,
                "coarse_action": raw_action,
                "amount_to": before_bet,
                "is_full_raise": False,
                "is_all_in": False,
            })
        else:
            continue

        actions.append(detail)

    current_bet = max(0, _as_int(state.get("current_bet"), price))
    owed = max(0, _as_int(
        state.get("amount_owed"),
        current_bet - _as_int(state.get("your_bet_this_street"), 0),
    ))
    pot = max(0, _as_int(state.get("pot"), 0))
    hero_bet = max(0, _as_int(state.get("your_bet_this_street"), 0))
    hero_stack = max(0, _as_int(state.get("your_stack"), 0))
    hero_total = hero_stack + hero_bet

    aggressor_seat = None
    if last_price_aggressor is not None:
        aggressor_seat = last_price_aggressor.get("seat")
    elif last_full_raiser is not None:
        aggressor_seat = last_full_raiser.get("seat")
    aggressor_total = hero_total
    for player in state.get("players", []) or []:
        if not isinstance(player, dict):
            continue
        if _as_int(player.get("seat"), -2) == aggressor_seat:
            aggressor_total = max(
                0,
                _as_int(player.get("stack"), 0)
                + _as_int(player.get("bet_this_street"), 0),
            )
            break
    effective_stack = min(hero_total, aggressor_total) if aggressor_seat is not None else hero_total

    price_set_by_all_in = bool(
        last_price_aggressor
        and last_price_aggressor.get("is_all_in")
        and _as_int(last_price_aggressor.get("amount_to"), -1) == current_bet
        and owed > 0
    )
    short_all_in_raise = bool(
        price_set_by_all_in and not last_price_aggressor.get("is_full_raise")
    )
    in_position = _infer_position(state) in ("BTN", "CO")

    return {
        "action_sequence": tuple(sequence),
        "actions": tuple(actions),
        "full_raise_count": full_raise_count,
        "hero_full_raise_count": hero_full_raise_count,
        "hero_called": hero_called,
        "limp_count": limp_count,
        "caller_count": callers_since_raise,
        "last_full_raiser_seat": last_full_raiser.get("seat") if last_full_raiser else None,
        "raiser_position": last_full_raiser.get("position") if last_full_raiser else "",
        "facing_all_in": price_set_by_all_in and not short_all_in_raise,
        "short_all_in_raise": short_all_in_raise,
        "current_bet": current_bet,
        "blind_size": bb,
        "raise_to_bb": float(current_bet) / float(max(1, bb)),
        "amount_owed": owed,
        "pot_odds": float(owed) / float(max(1, pot + owed)),
        "hero_stack_bb": float(hero_total) / float(max(1, bb)),
        "effective_stack": effective_stack,
        "effective_stack_bb": float(effective_stack) / float(max(1, bb)),
        "call_fraction": float(owed) / float(max(1, effective_stack)),
        "in_position": in_position,
    }


def _action_sequence_preflop(state: dict) -> tuple:
    """Compatibility view of the replay; unlike the old helper, keeps hero."""
    return _reconstruct_preflop(state)["action_sequence"]


def _preflop_action(state: dict) -> dict:
    """Resolve a preflop decision: blueprint tag → legal action."""
    hole = state.get("your_cards", []) or []
    if len(hole) != 2:
        return _safe_fallback(state)
    hand = canonical_hand(hole)
    pos = _infer_position(state)
    context = _reconstruct_preflop(state)
    seq = context["action_sequence"]
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
                if (p.get("seat") != me and not p.get("is_folded")
                        and p.get("state") != "folded"):
                    opp_seat = p.get("seat")
                    break
            if opp_seat is not None:
                widen = float(model.exploit_shift(
                    opp_seat,
                    state.get("players", []) or [],
                ).get("widen_open", 0.0))
        except Exception:
            widen = 0.0
    decision = _preflop_lookup(
        pos,
        hand,
        seq,
        widen_open=widen,
        blueprint_only=overlay_off,
        context=context,
    )
    base_tag = decision.get("tag", "fold")
    can_check = bool(state.get("can_check"))
    current_bet = max(0, _as_int(state.get("current_bet"), 0))
    min_raise_to = max(0, _as_int(state.get("min_raise_to"), 0))
    amount_owed = max(0, _as_int(state.get("amount_owed"), 0))
    bb = max(1, _as_int(context.get("blind_size"), 100))
    abstract_action = _preflop_blueprint_choice(
        state, pos, hand, context, base_tag
    )
    tag = _mix_preflop_tag(base_tag, abstract_action, hand, can_check)

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
        if can_check or amount_owed <= 0:
            return {"action": "check"}
        return {"action": "call"}
    if tag == "all_in":
        return {"action": "all_in"}

    # Raise tags
    if tag == "open":
        # Preserve both trained sizes; absent an artifact use the chart default.
        if abstract_action == "open_small":
            mult = 2.25
        elif abstract_action == "open_large":
            mult = 3.0
        else:
            mult = 2.5 if pos in ("CO", "BTN", "SB") else 3.0
        return open_raise_total(state, bb=bb, mult=mult)
    if tag == "iso_raise":
        # The trained 3.5/5 BB abstraction grows by one BB per extra limper.
        n_limps = max(1, _as_int(context.get("limp_count"), 1))
        if abstract_action == "iso_small":
            multiple = 3.5 + max(n_limps - 1, 0)
        elif abstract_action == "iso_large":
            multiple = 5.0 + max(n_limps - 1, 0)
        else:
            multiple = 4.0 + n_limps
        target = max(int(round(bb * multiple)), min_raise_to)
        return legal_raise_total(target, state)
    if tag == "threebet":
        # ~3x the open in position, 4x out of position, plus one open-size
        # per caller for a squeeze. `current_bet` is a total street bet.
        if abstract_action == "threebet_small":
            mult = 2.8 if context.get("in_position") else 3.2
        elif abstract_action == "threebet_large":
            mult = 3.5 if context.get("in_position") else 4.2
        else:
            mult = 3.0 if context.get("in_position") else 4.0
        callers = max(0, _as_int(context.get("caller_count"), 0))
        target = max(
            int(current_bet * (mult + callers)),
            min_raise_to,
        )
        return threebet_total(state, raise_to=target, bb=bb)
    if tag == "fourbet":
        # 2.2x IP / 2.4x OOP; callers add dead money but do not justify a
        # giant deep-stack commitment.
        mult = 2.15 if abstract_action == "fourbet_small" else (
            2.2 if context.get("in_position") else 2.4
        )
        callers = max(0, _as_int(context.get("caller_count"), 0))
        target = max(int(current_bet * mult + callers * bb), min_raise_to)
        return legal_raise_total(target, state)
    # Unknown tag → safe fallback.
    return _safe_fallback(state)


def _strategy(game_state: dict) -> dict:
    """Real strategy entrypoint. Caller wraps with timeout/safety guards."""
    if not isinstance(game_state, dict):
        return {"action": "fold"}
    if game_state.get("type") == "warmup":
        return {"action": "check"}
    # Consume the cumulative per-hand snapshot incrementally. The official
    # rolling match log lacks street labels and is intentionally not guessed.
    try:
        _get_model().observe_state(game_state)
    except Exception:
        pass

    street = game_state.get("street", "preflop")
    if street == "preflop":
        return _preflop_action(game_state)
    return _decide_postflop(game_state, blueprint_policy=_BLUEPRINT)


def decide(game_state) -> dict:
    """Return a legal action for the given game_state.

    Times itself with a soft 1.2 s budget and falls back to a legal safe action
    if the strategy stack misbehaves.

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
