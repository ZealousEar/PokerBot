"""G1 legal-action contract tests for every public decision path."""
import pytest

from src import bot


VALID = {"fold", "check", "call", "raise", "all_in"}


def state(**overrides):
    base = {
        "type": "action_request",
        "hand_id": "edge_001",
        "street": "preflop",
        "seat_to_act": 0,
        "pot": 150,
        "community_cards": [],
        "current_bet": 100,
        "min_raise_to": 200,
        "amount_owed": 100,
        "can_check": False,
        "your_cards": ["As", "Kh"],
        "your_stack": 9900,
        "your_bet_this_street": 0,
        "players": [],
        "action_log": [],
    }
    base.update(overrides)
    return base


def assert_legal(action, game_state):
    assert isinstance(action, dict)
    assert action.get("action") in VALID
    if action["action"] == "raise":
        assert isinstance(action.get("amount"), int)
        assert action["amount"] >= game_state["min_raise_to"]
    if action["action"] == "check":
        assert game_state.get("can_check")


@pytest.mark.parametrize(
    "game_state",
    [
        state(can_check=True, amount_owed=0, current_bet=0, min_raise_to=100),
        state(can_check=False, amount_owed=100),
        state(street="flop", community_cards=["7s", "Td", "2h"], can_check=True, amount_owed=0),
        state(street="river", community_cards=["7s", "Td", "2h", "Kc", "5d"], amount_owed=2500),
        state(your_stack=80, your_bet_this_street=20, amount_owed=100),
    ],
)
def test_decide_returns_legal_action_for_engine_states(game_state):
    assert_legal(bot.decide(game_state), game_state)


def test_decide_handles_warmup_and_malformed_inputs():
    assert bot.decide({"type": "warmup"}) == {"action": "check"}
    for value in (None, 42, [], "bad", object()):
        result = bot.decide(value)
        assert isinstance(result, dict)
        assert result["action"] in VALID


@pytest.mark.parametrize(
    "raw, expected",
    [
        ({"action": "fold"}, {"action": "fold"}),
        ({"action": "check"}, {"action": "call"}),
        ({"action": "call"}, {"action": "call"}),
        ({"action": "raise", "amount": 150}, {"action": "raise", "amount": 200}),
        ({"action": "raise", "amount": 20000}, {"action": "all_in"}),
        ({"action": "all_in"}, {"action": "all_in"}),
        ({"action": "raise"}, {"action": "fold"}),
        ({"action": "nonsense"}, {"action": "fold"}),
    ],
)
def test_legalize_action_shapes(raw, expected):
    assert bot._legalize_action(state(), raw) == expected


def test_legalize_check_when_free():
    game_state = state(can_check=True, amount_owed=0, current_bet=0, min_raise_to=100)
    assert bot._legalize_action(game_state, {"action": "check"}) == {"action": "check"}
    assert bot._legalize_action(game_state, {"action": "call"}) == {"action": "check"}
