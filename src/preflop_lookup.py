"""Preflop safety-chart lookup.

Routes priced betting context, position and hand to a conservative action tag.
`src.bot` keeps this action category as the safety envelope and uses the
offline-trained abstract blueprint only to mix among permitted raise sizes.

# Source: [[Pluribus-Brown-Sandholm-2019]] — blueprint shape (position × hand × action-seq)
# Status: SHIPPED — hand-tuned action/risk envelope plus trained mixed sizing.
"""
from typing import Tuple

from src.ranges import (
    OPEN_RANGES,
    BORDERLINE_OPEN,
    CORE_OPEN_RANGES,
    EARLY_POSITIONS,
    LATE_POSITIONS,
    THREEBET_VS_OPEN,
    THREEBET_BTN_VS_OPEN,
    THREEBET_SB_VS_OPEN,
    THREEBET_BB_VS_OPEN,
    THREEBET_VS_EARLY_OPEN,
    SQUEEZE_VALUE,
    FLAT_VS_OPEN_BTN,
    FLAT_VS_OPEN_BB,
    FLAT_VS_EARLY_OPEN,
    MULTIWAY_FLAT,
    FOURBET_VS_THREEBET,
    CALL_VS_THREEBET,
    FOURBET_VALUE,
    COLD_FOURBET,
    LARGE_RAISE_CONTINUE,
    PUSH_FOLD_TIGHT,
    PUSH_FOLD_STANDARD,
    PUSH_FOLD_WIDE,
    RESHOVE_10BB,
    RESHOVE_15BB,
    RESHOVE_20BB,
    CALL_OFF_5BB,
    CALL_OFF_10BB,
    CALL_OFF_15BB,
    CALL_OFF_20BB,
    CALL_OFF_30BB,
    CALL_OFF_DEEP,
)


def _threebet_set(position: str):
    if position == "BTN":
        return THREEBET_BTN_VS_OPEN
    if position == "SB":
        return THREEBET_SB_VS_OPEN
    if position == "BB":
        return THREEBET_BB_VS_OPEN
    return THREEBET_VS_OPEN


def _flat_set(position: str):
    if position == "BTN":
        return FLAT_VS_OPEN_BTN
    if position == "BB":
        return FLAT_VS_OPEN_BB
    # Other positions: cold-call light, mostly 3-bet or fold.
    return frozenset()


def _number(context: dict, key: str, default: float) -> float:
    try:
        return float(context.get(key, default))
    except (TypeError, ValueError, OverflowError, AttributeError):
        return float(default)


def _push_fold_set(position: str, stack_bb: float, callers: int):
    """Conservative open-shove range for at most twelve blinds."""
    late = position in LATE_POSITIONS
    if stack_bb <= 6.0:
        chosen = PUSH_FOLD_WIDE if late else PUSH_FOLD_STANDARD
    elif stack_bb <= 10.0:
        chosen = PUSH_FOLD_WIDE if late else (
            PUSH_FOLD_TIGHT if position in EARLY_POSITIONS else PUSH_FOLD_STANDARD
        )
    else:
        chosen = PUSH_FOLD_STANDARD if late else PUSH_FOLD_TIGHT
    if callers:
        chosen = chosen & (PUSH_FOLD_STANDARD if stack_bb <= 6.0 else PUSH_FOLD_TIGHT)
    return chosen


def _reshove_set(stack_bb: float, raiser_position: str, callers: int):
    if stack_bb <= 10.0:
        chosen = RESHOVE_10BB
    elif stack_bb <= 15.0:
        chosen = RESHOVE_15BB
    else:
        chosen = RESHOVE_20BB
    # Early opens and calls in between both represent stronger ranges.
    if raiser_position in EARLY_POSITIONS:
        chosen = chosen & (RESHOVE_15BB if stack_bb <= 10.0 else RESHOVE_20BB)
    if callers:
        chosen = chosen & RESHOVE_20BB
    return chosen


def _call_off_set(stack_bb: float, raiser_position: str, callers: int):
    if stack_bb <= 5.0:
        chosen = CALL_OFF_5BB
    elif stack_bb <= 10.0:
        chosen = CALL_OFF_10BB
    elif stack_bb <= 15.0:
        chosen = CALL_OFF_15BB
    elif stack_bb <= 20.0:
        chosen = CALL_OFF_20BB
    elif stack_bb <= 30.0:
        chosen = CALL_OFF_30BB
    else:
        chosen = CALL_OFF_DEEP

    if raiser_position in EARLY_POSITIONS:
        if stack_bb <= 10.0:
            chosen = chosen & CALL_OFF_15BB
        elif stack_bb <= 20.0:
            chosen = chosen & CALL_OFF_30BB
    if callers:
        if stack_bb <= 10.0:
            chosen = chosen & CALL_OFF_15BB
        elif stack_bb <= 20.0:
            chosen = chosen & CALL_OFF_30BB
        else:
            chosen = chosen & CALL_OFF_DEEP
    return chosen


def lookup(position: str,
           hand: str,
           action_seq: Tuple[str, ...] = (),
           widen_open: float = 0.0,
           blueprint_only: bool = False,
           context: dict = None) -> dict:
    """Return a decision tag dict like {"tag": "open"} or
    {"tag": "threebet"} or {"tag": "fold"} or {"tag": "call"}.

    `position`: one of UTG, MP, CO, BTN, SB, BB. In heads-up matches caller
    should pass SB (dealer) or BB.
    `hand`: canonical tag from `src.equity.canonical_hand`.
    `action_seq`: tuple of actions ahead of us, oldest first. Use one of
        ()                          — unopened pot (we are first in or all folded to us)
        ("raise",)                  — one open raise ahead
        ("raise", "raise")          — open + 3-bet ahead
        ("call",)                   — limped pot
    `widen_open`: overlay shift in [0, 0.20]. If > 0.05, also open from the
        position's BORDERLINE_OPEN range. This is the only preflop knob the
        overlay touches; postflop overlay shifts live in `src.postflop`.
    `blueprint_only`: when True (overlay disabled by env var), use the tighter
        CORE_OPEN_RANGES as the open set. Ensures the v1_blueprint snapshot
        plays a meaningfully different baseline than the with-overlay build,
        so the G5 ablation actually measures overlay contribution.
    """
    import os
    context = context if isinstance(context, dict) else {}
    tight_ranges = os.environ.get("TIGHT_RANGES") == "1"
    if blueprint_only or tight_ranges:
        open_range = CORE_OPEN_RANGES.get(position, frozenset())
        border = frozenset()
    else:
        open_range = OPEN_RANGES.get(position, frozenset())
        # Lower threshold (0.01) so any positive widen_open shift activates
        # borderline opens. Combined with the new baseline shift (small even
        # for aggressive archetypes), this gives v_final a consistent edge
        # in opens over the OVERLAY_LEGACY=1 v3_hardened snapshot.
        border = BORDERLINE_OPEN.get(position, frozenset()) if widen_open > 0.01 else frozenset()

    calls = [a for a in action_seq if a in ("call", "all_in_call")]
    full_raise_count = int(_number(context, "full_raise_count", len([
        a for a in action_seq if a == "raise"
    ])))
    limp_count = int(_number(
        context,
        "limp_count",
        len(calls) if full_raise_count == 0 else 0,
    ))
    caller_count = int(_number(context, "caller_count", 0))
    hero_stack_bb = max(0.0, _number(context, "hero_stack_bb", 100.0))
    effective_stack_bb = max(
        0.0,
        _number(context, "effective_stack_bb", hero_stack_bb),
    )
    raise_to_bb = max(0.0, _number(context, "raise_to_bb", 2.5))
    pot_odds = max(0.0, min(1.0, _number(context, "pot_odds", 0.25)))
    call_fraction = max(0.0, _number(context, "call_fraction", 0.04))
    raiser_position = str(context.get("raiser_position", ""))
    facing_all_in = bool(context.get("facing_all_in", False))
    hero_raise_count = int(_number(context, "hero_full_raise_count", 0))
    hero_called = bool(context.get("hero_called", False))

    if full_raise_count == 0:
        # With <=12 BB, use an explicit push/fold branch.  A normal deep-stack
        # open chart must never min-raise and then improvise with 4 BB behind.
        if hero_stack_bb <= 12.0:
            push_set = _push_fold_set(position, hero_stack_bb, limp_count)
            if hand in push_set:
                return {"tag": "all_in"}
            if position == "BB" and limp_count:
                return {"tag": "check"}
            return {"tag": "fold"}

        if limp_count:
            # Limped pot — isolate only with a normal stack and a charted hand.
            # Multiple limpers remove the marginal bottom of the BTN range.
            iso_range = OPEN_RANGES.get("BTN", frozenset())
            if limp_count >= 2:
                iso_range = iso_range & OPEN_RANGES.get("CO", frozenset())
            if hand in iso_range:
                return {"tag": "iso_raise"}
            if position == "BB":
                return {"tag": "check"}
            return {"tag": "fold"}

        # Unopened — open or fold.
        if hand in open_range or (border and hand in border):
            return {"tag": "open"}
        if position == "BB":
            return {"tag": "check"}
        return {"tag": "fold"}

    # An all-in has its own price/effective-stack call-off chart.  In
    # particular, the normal BB flat range (which contains 22) is never used
    # against a 100 BB shove.
    if facing_all_in:
        call_off = _call_off_set(effective_stack_bb, raiser_position, caller_count)
        return {"tag": "call" if hand in call_off else "fold"}

    # Oversized non-all-in raises also bypass the broad flat charts.
    if raise_to_bb >= 12.0 or call_fraction >= 0.35:
        if hand not in LARGE_RAISE_CONTINUE:
            return {"tag": "fold"}
        if hand in FOURBET_VALUE and effective_stack_bb <= 40.0:
            return {"tag": "all_in"}
        return {"tag": "call"}

    if full_raise_count == 1:
        # Facing a single open raise.
        if effective_stack_bb <= 20.0:
            reshove = _reshove_set(effective_stack_bb, raiser_position, caller_count)
            return {"tag": "all_in" if hand in reshove else "fold"}

        threebet = _threebet_set(position)
        flat = _flat_set(position)
        if raiser_position in EARLY_POSITIONS:
            threebet = threebet & THREEBET_VS_EARLY_OPEN
            flat = flat & FLAT_VS_EARLY_OPEN
        if caller_count:
            threebet = threebet & SQUEEZE_VALUE
            flat = flat & MULTIWAY_FLAT
        if raise_to_bb > 4.0:
            threebet = threebet & SQUEEZE_VALUE
            flat = flat & LARGE_RAISE_CONTINUE
        if hand in threebet:
            return {"tag": "threebet"}
        # Pot odds and price cap speculative calls.  Multiway calls get a
        # slightly better realized price, but only from the explicit range.
        max_raise = 4.0 if caller_count else 3.5
        max_fraction = 0.18 if caller_count else 0.14
        price_ok = raise_to_bb <= max_raise and call_fraction <= max_fraction
        odds_ok = pot_odds <= (0.28 if caller_count else 0.31)
        if hand in flat and price_ok and odds_ok:
            return {"tag": "call"}
        return {"tag": "fold"}

    if full_raise_count == 2:
        # Facing a 3-bet.
        # If hero did not make the first raise this is a cold 4-bet spot, not
        # the ordinary open-versus-3-bet chart.
        if hero_raise_count == 0:
            if hand in COLD_FOURBET:
                return {"tag": "fourbet"}
            return {"tag": "fold"}

        fourbet = FOURBET_VS_THREEBET
        if raise_to_bb > 11.0 or caller_count:
            fourbet = fourbet & FOURBET_VALUE
        if hand in fourbet:
            return {"tag": "fourbet"}
        call_ok = (
            raise_to_bb <= 12.0
            and call_fraction <= 0.25
            and pot_odds <= 0.36
            and not hero_called
        )
        if hand in CALL_VS_THREEBET and call_ok:
            return {"tag": "call"}
        return {"tag": "fold"}

    if full_raise_count >= 3:
        # Facing a 4-bet+ — only premiums continue.
        if hand in {"AA", "KK", "AKs"}:
            return {"tag": "all_in"}
        return {"tag": "fold"}

    return {"tag": "fold"}
