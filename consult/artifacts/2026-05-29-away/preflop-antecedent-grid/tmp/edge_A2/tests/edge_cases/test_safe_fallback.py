"""Verify `_safe_fallback` and `decide` always return a legal action.

Game states modeled on ext/fullhouse-engine/sandbox/validator.py::TEST_STATES.
"""
from src import bot


_PREFLOP_FACING_BET = {
    "type": "action_request",
    "street": "preflop",
    "pot": 150,
    "community_cards": [],
    "current_bet": 100,
    "min_raise_to": 200,
    "amount_owed": 100,
    "can_check": False,
    "your_cards": ["As", "Kh"],
    "your_stack": 9900,
    "your_bet_this_street": 0,
}

_FLOP_CAN_CHECK = {
    "type": "action_request",
    "street": "flop",
    "pot": 300,
    "community_cards": ["7s", "Td", "2h"],
    "current_bet": 0,
    "min_raise_to": 100,
    "amount_owed": 0,
    "can_check": True,
    "your_cards": ["Ah", "Kd"],
    "your_stack": 9850,
    "your_bet_this_street": 0,
}

_VALID = {"fold", "check", "call", "raise", "all_in"}


def test_safe_fallback_checks_when_possible():
    assert bot._safe_fallback(_FLOP_CAN_CHECK) == {"action": "check"}


def test_safe_fallback_folds_facing_bet():
    assert bot._safe_fallback(_PREFLOP_FACING_BET) == {"action": "fold"}


def test_decide_handles_warmup_without_raising():
    result = bot.decide({"type": "warmup"})
    assert isinstance(result, dict)
    assert "action" in result


def test_decide_returns_legal_action_on_garbage():
    for gs in [{}, _PREFLOP_FACING_BET, _FLOP_CAN_CHECK, {"random_garbage": True}, None, 42, []]:
        result = bot.decide(gs)
        assert isinstance(result, dict)
        assert result["action"] in _VALID
        if result["action"] == "raise":
            assert "amount" in result
