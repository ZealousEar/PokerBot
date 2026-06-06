"""G4 hardening cases around legal fallback, sizing, and budget wrappers."""
from src import bot
from src.sizing import sizing_to_amount
from src.timeout_guard import run_with_budget


def state(**overrides):
    base = {
        "type": "action_request",
        "hand_id": "hard_001",
        "street": "turn",
        "seat_to_act": 0,
        "pot": 2400,
        "community_cards": ["As", "7d", "2h", "Tc"],
        "current_bet": 800,
        "min_raise_to": 1600,
        "amount_owed": 800,
        "can_check": False,
        "your_cards": ["Ah", "Kd"],
        "your_stack": 2200,
        "your_bet_this_street": 0,
        "players": [
            {"seat": 0, "bot_id": "hero", "stack": 2200, "state": "active", "is_folded": False, "is_all_in": False, "bet_this_street": 0, "hole_cards": None},
            {"seat": 1, "bot_id": "villain", "stack": 7400, "state": "active", "is_folded": False, "is_all_in": False, "bet_this_street": 800, "hole_cards": None},
        ],
        "action_log": [],
    }
    base.update(overrides)
    return base


def test_raise_below_min_is_snapped_to_minimum_total():
    assert bot._legalize_action(state(), {"action": "raise", "amount": 900}) == {
        "action": "raise",
        "amount": 1600,
    }


def test_raise_above_stack_becomes_all_in():
    assert bot._legalize_action(state(your_stack=1200), {"action": "raise", "amount": 5000}) == {
        "action": "all_in",
    }


def test_malformed_raise_uses_safe_fallback():
    assert bot._legalize_action(state(), {"action": "raise", "amount": "bad"}) == {"action": "fold"}


def test_side_pot_shaped_all_in_state_returns_legal_action():
    game_state = state(
        your_stack=0,
        amount_owed=0,
        can_check=True,
        players=[
            {"seat": 0, "bot_id": "hero", "stack": 0, "state": "all_in", "is_folded": False, "is_all_in": True, "bet_this_street": 1800, "hole_cards": None},
            {"seat": 1, "bot_id": "short", "stack": 0, "state": "all_in", "is_folded": False, "is_all_in": True, "bet_this_street": 900, "hole_cards": None},
            {"seat": 2, "bot_id": "deep", "stack": 6000, "state": "active", "is_folded": False, "is_all_in": False, "bet_this_street": 1800, "hole_cards": None},
        ],
    )
    assert bot.decide(game_state)["action"] in {"check", "fold", "call", "raise", "all_in"}


def test_sizing_uses_total_raise_amount_and_stack_cap():
    assert sizing_to_amount("half_pot", pot=900, stack=1000, min_raise_to=700, already_in=50) == 700
    assert sizing_to_amount("all_in", pot=900, stack=1000, min_raise_to=700, already_in=50) == 1050


def test_run_with_budget_falls_back_on_exception():
    def broken(_state):
        raise RuntimeError("boom")

    assert run_with_budget(broken, bot._safe_fallback, state()) == {"action": "fold"}
