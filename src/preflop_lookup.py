"""Preflop blueprint lookup.

Loads `data/preflop_blueprint.npz` eagerly at module import (covered by the
engine's 30 s warmup). Returns action + sizing for (position, hand, action_seq).

# Source: [[PokerBot/Pluribus/Brown-Sandholm-2019]] — 6-max blueprint
"""
import os
from pathlib import Path

_DATA_DIR = Path(os.environ.get(
    "BOT_DATA_DIR",
    Path(__file__).resolve().parent.parent / "data",
))
_BLUEPRINT_PATH = _DATA_DIR / "preflop_blueprint.npz"

# TODO (G2): load blueprint eagerly here.
_blueprint = None


def lookup(position: str, hand: tuple, action_seq: tuple):
    """Return blueprint action for the given preflop context, or None if not covered."""
    # TODO (G2): implement
    return None
