"""Postflop strategy.

Flop: bucket lookup from `data/flop_strategy.npz`.
Turn/river: heuristic driven by `equity_vs_range` + `opponent_model`.

# Source: [[Cepheus-Bowling-2015]]
"""
import os
from pathlib import Path

import numpy as np

_DATA_DIR = Path(os.environ.get(
    "BOT_DATA_DIR",
    Path(__file__).resolve().parent.parent / "data",
))

_flop_buckets = None
_flop_strategy = None
_buckets_path = _DATA_DIR / "flop_buckets.npz"
_strategy_path = _DATA_DIR / "flop_strategy.npz"
if _buckets_path.exists():
    with np.load(_buckets_path, allow_pickle=False) as data:
        _flop_buckets = data["bucket_ids"].astype(int)
if _strategy_path.exists():
    with np.load(_strategy_path, allow_pickle=False) as data:
        _flop_strategy = data["strategy"].astype(float)


def decide_postflop(game_state: dict) -> dict:
    """Return a low-cost postflop action for the G2 deterministic baseline."""
    # Source: [[Engine-Fullhouse]]
    pot = int(game_state.get("pot") or 0)
    min_raise_to = int(game_state.get("min_raise_to") or 0)
    already_in = int(game_state.get("your_bet_this_street") or 0)
    stack_total = int(game_state.get("your_stack") or 0) + already_in

    if game_state.get("can_check"):
        if pot >= 200 and stack_total > min_raise_to:
            amount = max(min_raise_to, already_in + (pot * 2) // 3)
            amount = min(amount, stack_total)
            if amount > already_in:
                return {"action": "raise", "amount": amount}
        return {"action": "check"}

    owed = int(game_state.get("amount_owed") or 0)
    cards = game_state.get("your_cards") or []
    board = game_state.get("community_cards") or []
    ranks = [str(c)[0] for c in cards if c] + [str(c)[0] for c in board if c]
    paired = any(ranks.count(rank) >= 2 for rank in {str(c)[0] for c in cards if c})
    if paired and owed <= max(100, pot // 3):
        return {"action": "call"}
    return {"action": "fold"}
