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

# Codex wires these during G2/G3:
# from src.preflop_lookup import lookup as _preflop_lookup
# from src.postflop import decide_postflop as _decide_postflop
# from src.timeout_guard import run_with_budget


def _safe_fallback(game_state: dict) -> dict:
    """Last-resort legal action. Never raises."""
    if isinstance(game_state, dict) and game_state.get("can_check"):
        return {"action": "check"}
    return {"action": "fold"}


def decide(game_state: dict) -> dict:
    """Return a legal action for the given game_state.

    Wired through G1-G3 by Codex.
    """
    if isinstance(game_state, dict) and game_state.get("type") == "warmup":
        return {"action": "check"}
    try:
        if not isinstance(game_state, dict):
            return {"action": "fold"}
        return _safe_fallback(game_state)
    except Exception:
        return {"action": "fold"}
