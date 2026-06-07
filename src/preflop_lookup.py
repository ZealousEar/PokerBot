"""Preflop blueprint lookup.

Heuristic blueprint (per solver policy — hand-tuned tables ship before MCCFR
training). Routes (position, hand, action_seq) → decision tag. The bot module
converts the tag into a legal action via `src.sizing`.

# Source: [[Pluribus-Brown-Sandholm-2019]] — blueprint shape (position × hand × action-seq)
# Status: SHIPPED — hand-tuned range tables (see module docstring above). The
#         MCCFR-trained blueprint is INTENDED, not the running policy.
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
           blueprint_only: bool = False) -> dict:
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

    if not action_seq or all(a == "fold" for a in action_seq):
        # Unopened — open or fold.
        if hand in open_range or (border and hand in border):
            return {"tag": "open"}
        if position == "BB":
            return {"tag": "check"}
        return {"tag": "fold"}

    # Filter only meaningful actions ahead.
    raises = [a for a in action_seq if a == "raise"]
    calls = [a for a in action_seq if a == "call"]

    if len(raises) == 0 and calls:
        # Limped pot — iso-raise wider, otherwise check (BB) or fold.
        if hand in OPEN_RANGES.get("BTN", frozenset()):
            return {"tag": "iso_raise"}
        if position == "BB":
            return {"tag": "check"}
        return {"tag": "fold"}

    if len(raises) == 1:
        # Facing a single open raise.
        threebet = _threebet_set(position)
        flat = _flat_set(position)
        if hand in threebet:
            return {"tag": "threebet"}
        if hand in flat:
            return {"tag": "call"}
        return {"tag": "fold"}

    if len(raises) == 2:
        # Facing a 3-bet.
        if hand in FOURBET_VS_THREEBET:
            return {"tag": "fourbet"}
        if hand in CALL_VS_THREEBET:
            return {"tag": "call"}
        return {"tag": "fold"}

    if len(raises) >= 3:
        # Facing a 4-bet+ — only premiums continue.
        if hand in {"AA", "KK", "AKs", "AKo"}:
            return {"tag": "all_in"}
        return {"tag": "fold"}

    return {"tag": "fold"}
