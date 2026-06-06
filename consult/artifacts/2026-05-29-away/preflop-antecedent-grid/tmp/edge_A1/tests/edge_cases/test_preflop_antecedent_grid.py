"""Candidate-only checks for the preflop antecedent grid.

Set PREFLOP_ANTECEDENT_CASE=A0..A5 when running against an extracted
candidate artifact. Without the env var, this file is inert so normal edge
tests keep their existing baseline contract.
"""
import os

import pytest

from src.preflop_lookup import lookup
from src.ranges import hand_score


CASE = os.environ.get("PREFLOP_ANTECEDENT_CASE")

FLOORS = {
    "A0": {},
    "A1": {"heads_up_button": 20, "small_blind": 20, "button": 20},
    "A2": {"heads_up_button": 32, "small_blind": 32, "button": 32},
    "A3": {"heads_up_button": 40, "small_blind": 40, "button": 40},
    "A4": {"heads_up_button": 50, "small_blind": 50, "button": 50},
    "A5": {"heads_up_button": 32, "small_blind": 40, "button": 40},
}


pytestmark = pytest.mark.skipif(
    CASE not in FLOORS,
    reason="set PREFLOP_ANTECEDENT_CASE=A0..A5 for candidate grid checks",
)


def _expected_open(position, hand):
    floor = FLOORS[CASE].get(position)
    if floor is None:
        return "raise"
    return "raise" if hand_score(hand) >= floor else "fold"


@pytest.mark.parametrize("position", ["heads_up_button", "small_blind", "button"])
@pytest.mark.parametrize("hand", ["32o", "72o", "94o", "75s", "Q7o"])
def test_candidate_open_floor_by_position(position, hand):
    decision = lookup(position, hand, ())
    assert decision["action"] == _expected_open(position, hand)


def test_big_blind_free_option_and_normal_range_open_stay_unchanged():
    assert lookup("big_blind", "32o", ())["action"] == "check"
    assert lookup("early", "32o", ())["action"] == "fold"
    assert lookup("early", "A7o", ())["action"] == "raise"


def test_facing_aggression_continue_logic_stays_unchanged():
    assert lookup("button", "AA", ("raise",))["action"] == "call"
    assert lookup("button", "32o", ("raise",))["action"] == "fold"
