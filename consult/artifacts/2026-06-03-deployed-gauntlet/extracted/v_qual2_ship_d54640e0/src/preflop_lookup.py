"""Preflop blueprint lookup.

Heuristic blueprint (per solver policy — hand-tuned tables ship before MCCFR
training). Routes (position, hand, action_seq) → decision tag. The bot module
converts the tag into a legal action via `src.sizing`.

# Source: [[Pluribus-Brown-Sandholm-2019]] — blueprint shape (position × hand × action-seq)
"""
from typing import Tuple

from src.ranges import (
    OPEN_RANGES,
    BORDERLINE_OPEN,
    CORE_OPEN_RANGES,
    THREEBET_VS_OPEN,
    THREEBET_BTN_VS_OPEN,
    THREEBET_SB_VS_OPEN,
    THREEBET_BB_VS_OPEN,
    FLAT_VS_OPEN_BTN,
    FLAT_VS_OPEN_BB,
    FOURBET_VS_THREEBET,
    CALL_VS_THREEBET,
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


def lookup(position: str,
           hand: str,
           action_seq: Tuple[str, ...] = (),
           widen_open: float = 0.0,
           tighten_open: float = 0.0,
           blueprint_only: bool = False) -> dict:
    """Return a decision tag dict like {"tag": "open"} or
    {"tag": "threebet"} or {"tag": "fold"} or {"tag": "call"}.

    `position`: one of UTG, MP, CO, BTN, SB, BB. In heads-up matches caller
    should pass SB (dealer) or BB.
    `hand`: canonical tag from `src.equity.canonical_hand`.
    `action_seq`: tuple of actions ahead of us, oldest first.
    `widen_open`: overlay shift in [0, 0.20]. If > 0.01, open from the
        position's BORDERLINE_OPEN range (looser opens vs passive villains).
    `tighten_open`: overlay shift in [0, 0.20]. If > 0.05, fall back to
        CORE_OPEN_RANGES (tighter opens vs hyperaggressive villains who
        3-bet light), and skip flat-call hands in favor of fold or 3-bet.
    `blueprint_only`: ablation hook — uses CORE_OPEN_RANGES and ignores
        widen/tighten shifts. Called from `decide_blueprint_only` to measure
        overlay contribution at benchmark time.
    """
    if blueprint_only:
        open_range = CORE_OPEN_RANGES.get(position, frozenset())
        border = frozenset()
    elif tighten_open > 0.05:
        # Hyperaggressive villain detected — tighten opens so we don't open
        # into light 3-bets. Drops bottom-of-range speculative hands.
        open_range = CORE_OPEN_RANGES.get(position, frozenset())
        border = frozenset()
    else:
        open_range = OPEN_RANGES.get(position, frozenset())
        border = BORDERLINE_OPEN.get(position, frozenset()) if widen_open > 0.01 else frozenset()

    if not action_seq or all(a == "fold" for a in action_seq):
        if hand in open_range or (border and hand in border):
            return {"tag": "open"}
        if position == "BB":
            return {"tag": "check"}
        return {"tag": "fold"}

    raises = [a for a in action_seq if a == "raise"]
    calls = [a for a in action_seq if a == "call"]

    if len(raises) == 0 and calls:
        if hand in OPEN_RANGES.get("BTN", frozenset()):
            return {"tag": "iso_raise"}
        if position == "BB":
            return {"tag": "check"}
        return {"tag": "fold"}

    if len(raises) == 1:
        threebet = _threebet_set(position)
        flat = _flat_set(position)
        if hand in threebet:
            return {"tag": "threebet"}
        # Against hyperaggressive opens we collapse the flat-call range — the
        # raiser is likely to barrel postflop, so flats lose EV. 3-bet-or-fold.
        if hand in flat and tighten_open <= 0.05:
            return {"tag": "call"}
        return {"tag": "fold"}

    if len(raises) == 2:
        if hand in FOURBET_VS_THREEBET:
            return {"tag": "fourbet"}
        # Tighten 3-bet defense vs hyperaggressive 3-bettors: drop the call
        # range to just premiums (light 3-bets get folded out).
        if tighten_open > 0.05:
            if hand in {"JJ", "TT", "AQs"}:
                return {"tag": "call"}
            return {"tag": "fold"}
        if hand in CALL_VS_THREEBET:
            return {"tag": "call"}
        return {"tag": "fold"}

    if len(raises) >= 3:
        if hand in {"AA", "KK", "AKs", "AKo"}:
            return {"tag": "all_in"}
        return {"tag": "fold"}

    return {"tag": "fold"}
