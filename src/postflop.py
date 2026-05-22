"""Postflop strategy.

Flop: bucket lookup from `data/flop_strategy.npz`.
Turn/river: heuristic driven by `equity_vs_range` + `opponent_model`.

# Source: [[PokerBot/Cepheus/Bowling-2015]] — abstraction / bucketing
"""
import os
from pathlib import Path

_DATA_DIR = Path(os.environ.get(
    "BOT_DATA_DIR",
    Path(__file__).resolve().parent.parent / "data",
))

# TODO (G3): load flop_buckets.npz and flop_strategy.npz at import.
_flop_buckets = None
_flop_strategy = None


def decide_postflop(game_state: dict) -> dict:
    """Return a postflop action. Placeholder — Codex implements during G3."""
    if game_state.get("can_check"):
        return {"action": "check"}
    return {"action": "fold"}
