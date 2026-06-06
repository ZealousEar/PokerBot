"""Preflop blueprint lookup.

Loads `data/preflop_blueprint.npz` eagerly at module import (covered by the
engine's 30 s warmup). Returns action + sizing for (position, hand, action_seq).

# Source: [[Pluribus-Brown-Sandholm-2019]]
# Source: [[MCCFR-Lanctot-2009]]
"""
import os
from pathlib import Path

import numpy as np

try:
    from src.ranges import STRONG_CONTINUE, hand_score
except ImportError:  # direct runner load from src/preflop_lookup.py
    from ranges import STRONG_CONTINUE, hand_score

_DATA_DIR = Path(os.environ.get(
    "BOT_DATA_DIR",
    Path(__file__).resolve().parent.parent / "data",
))
_BLUEPRINT_PATH = _DATA_DIR / "preflop_blueprint.npz"

_SCORES = {}
if _BLUEPRINT_PATH.exists():
    with np.load(_BLUEPRINT_PATH, allow_pickle=False) as data:
        hands = data["hands"].astype(str)
        scores = data["scores"].astype(int)
        _SCORES = {hand: int(score) for hand, score in zip(hands, scores)}


def lookup(position: str, hand: tuple, action_seq: tuple):
    """Return blueprint action for the given preflop context, or None if not covered."""
    hand_key = "".join(hand) if isinstance(hand, tuple) else str(hand or "")
    score = _SCORES.get(hand_key, hand_score(hand_key))
    voluntary = tuple(a for a in action_seq if a not in ("small_blind", "big_blind"))
    facing_aggression = any(a in ("raise", "all_in") for a in voluntary)

    if not facing_aggression:
        if position in ("heads_up_button", "small_blind", "button"):
            if score >= 32:
                return {"action": "raise", "sizing": "min_raise", "reason": "heads_up_steal"}
            return {"action": "fold", "reason": "steal_floor_fold"}
        if position == "big_blind":
            return {"action": "check", "reason": "free_option"}
        if score >= 58:
            return {"action": "raise", "sizing": "min_raise", "reason": "range_open"}
        return {"action": "fold", "reason": "range_fold"}

    if hand_key in STRONG_CONTINUE or score >= 86:
        return {"action": "call", "reason": "strong_continue"}
    if score >= 76 and len(voluntary) <= 1:
        return {"action": "call", "reason": "priced_continue"}
    return {"action": "fold", "reason": "dominated_vs_aggression"}
