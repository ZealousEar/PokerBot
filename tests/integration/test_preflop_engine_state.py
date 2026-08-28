"""Regression probes against the official Fullhouse engine state machine."""
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = Path(os.environ.get("FULLHOUSE_ENGINE_DIR", ROOT / "ext" / "fullhouse-engine"))
if not (ENGINE_DIR / "engine" / "game.py").is_file():
    pytest.skip("requires official fullhouse-engine", allow_module_level=True)
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from engine.game import PokerEngine  # noqa: E402
from src.bot import _infer_position, _preflop_action, _reconstruct_preflop  # noqa: E402


def test_engine_positions_map_every_table_size_and_wraparound():
    for n in range(2, 10):
        engine = PokerEngine(
            f"positions_{n}",
            [f"p{i}" for i in range(n)],
            dealer_seat=n - 1,
            seed=10 + n,
        )
        state = engine.start_hand()
        expected_first = "SB" if n == 2 else ("BTN" if n == 3 else "CO" if n == 4 else None)
        if expected_first is not None:
            assert _infer_position(state) == expected_first
        # The cutoff is always immediately clockwise before the button and
        # must not be swallowed by the generic UTG branch at four handed.
        if n >= 4:
            state["seat_to_act"] = (engine.dealer_seat - 1) % n
            assert _infer_position(state) == "CO"


def test_engine_hero_open_then_threebet_preserves_both_raise_levels():
    engine = PokerEngine("hero_open_3bet", ["hero", "sb", "bb"], dealer_seat=0, seed=91)
    state = engine.start_hand()
    assert state["seat_to_act"] == 0
    state = engine.apply_action(0, {"action": "raise", "amount": 250})
    state = engine.apply_action(1, {"action": "raise", "amount": 900})
    state = engine.apply_action(2, {"action": "fold"})
    state["your_cards"] = ["As", "Qs"]

    replay = _reconstruct_preflop(state)
    assert replay["action_sequence"] == ("raise", "raise")
    assert replay["full_raise_count"] == 2
    assert replay["hero_full_raise_count"] == 1
    assert _preflop_action(state) == {"action": "call"}


@pytest.mark.parametrize(
    ("button_stack", "kind", "full_raise_count"),
    [
        (180, "all_in_call", 1),
        (450, "short_all_in_raise", 1),
        (500, "full_all_in_raise", 2),
    ],
)
def test_engine_normalized_all_in_totals_replay_correctly(
    button_stack,
    kind,
    full_raise_count,
):
    engine = PokerEngine(
        f"all_in_{button_stack}",
        ["button", "sb", "bb", "co"],
        dealer_seat=0,
        starting_stacks={"button": button_stack},
        seed=button_stack,
    )
    state = engine.start_hand()
    assert state["seat_to_act"] == 3
    state = engine.apply_action(3, {"action": "raise", "amount": 300})
    state = engine.apply_action(0, {"action": "all_in"})
    replay = _reconstruct_preflop(state)
    assert replay["actions"][-1]["kind"] == kind
    assert replay["full_raise_count"] == full_raise_count


def test_engine_100bb_shove_does_not_trigger_normal_big_blind_flat_chart(monkeypatch):
    monkeypatch.setenv("DISABLE_OVERLAY", "1")
    engine = PokerEngine("deep_shove", ["villain", "hero"], dealer_seat=0, seed=7)
    state = engine.start_hand()
    state = engine.apply_action(0, {"action": "all_in"})
    state["your_cards"] = ["2s", "2d"]

    replay = _reconstruct_preflop(state)
    assert replay["facing_all_in"] is True
    assert replay["effective_stack_bb"] == pytest.approx(100.0)
    assert _preflop_action(state) == {"action": "fold"}
