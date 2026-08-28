import pytest

from src.bot import (
    _action_sequence_preflop,
    _infer_position,
    _preflop_action,
    _reconstruct_preflop,
)
from src.preflop_lookup import lookup
from src.ranges import POSITIONS_BY_TABLE_SIZE


def _player(seat, stack=9900, bet=0, *, all_in=False):
    return {
        "seat": seat,
        "bot_id": f"p{seat}",
        "stack": stack,
        "state": "all_in" if all_in else "active",
        "is_folded": False,
        "is_all_in": all_in,
        "bet_this_street": bet,
        "hole_cards": None,
    }


def _state(n=6, hero=0, **overrides):
    state = {
        "type": "action_request",
        "hand_id": "preflop_probe",
        "street": "preflop",
        "seat_to_act": hero,
        "pot": 150,
        "community_cards": [],
        "current_bet": 100,
        "min_raise_to": 200,
        "amount_owed": 100,
        "can_check": False,
        "your_cards": ["2s", "2d"],
        "your_stack": 9900,
        "your_bet_this_street": 0,
        "players": [_player(i) for i in range(n)],
        "action_log": [
            {"seat": 1 % n, "action": "small_blind", "amount": 50},
            {"seat": 2 % n, "action": "big_blind", "amount": 100},
        ],
    }
    state.update(overrides)
    return state


@pytest.mark.parametrize("n", range(2, 10))
def test_positions_cover_two_to_nine_handed_tables_with_wrapped_button(n):
    # For n>=3, button n-1 gives SB=0 and BB=1.  This also exercises modulo
    # wraparound.  Heads-up button/SB=0 and BB=1.
    sb = 0
    bb = 1
    blinds = [
        {"seat": sb, "action": "small_blind", "amount": 50},
        {"seat": bb, "action": "big_blind", "amount": 100},
    ]
    button = sb if n == 2 else n - 1
    expected = POSITIONS_BY_TABLE_SIZE[n]
    for offset, label in enumerate(expected):
        seat = (button + offset) % n
        state = _state(n=n, hero=seat, action_log=blinds)
        assert _infer_position(state) == label


def test_four_handed_seat_left_of_bb_is_co_not_utg():
    state = _state(n=4, hero=3)
    assert _infer_position(state) == "CO"


def test_hero_open_is_retained_when_facing_a_threebet():
    state = _state(
        n=6,
        hero=5,
        pot=1300,
        current_bet=900,
        min_raise_to=1550,
        amount_owed=650,
        your_cards=["As", "Qs"],
        your_stack=9750,
        your_bet_this_street=250,
        action_log=[
            {"seat": 1, "action": "small_blind", "amount": 50},
            {"seat": 2, "action": "big_blind", "amount": 100},
            {"seat": 5, "action": "raise", "amount": 250},
            {"seat": 1, "action": "raise", "amount": 900},
            {"seat": 2, "action": "fold", "amount": 0},
        ],
        players=[
            _player(0),
            _player(1, stack=9100, bet=900),
            _player(2, stack=9900, bet=100),
            _player(3),
            _player(4),
            _player(5, stack=9750, bet=250),
        ],
    )
    replay = _reconstruct_preflop(state)
    assert _action_sequence_preflop(state) == ("raise", "raise")
    assert replay["full_raise_count"] == 2
    assert replay["hero_full_raise_count"] == 1
    assert _preflop_action(state) == {"action": "call"}


@pytest.mark.parametrize(
    ("all_in_total", "expected_sequence", "expected_kind", "full_raises"),
    [
        (180, ("raise", "call"), "all_in_call", 1),
        (450, ("raise", "raise"), "short_all_in_raise", 1),
        (500, ("raise", "raise"), "full_all_in_raise", 2),
    ],
)
def test_all_in_replay_distinguishes_call_short_raise_and_full_raise(
    all_in_total,
    expected_sequence,
    expected_kind,
    full_raises,
):
    state = _state(
        n=4,
        hero=1,
        current_bet=max(300, all_in_total),
        amount_owed=max(250, all_in_total - 50),
        action_log=[
            {"seat": 1, "action": "small_blind", "amount": 50},
            {"seat": 2, "action": "big_blind", "amount": 100},
            {"seat": 3, "action": "raise", "amount": 300},
            {"seat": 0, "action": "all_in", "amount": all_in_total},
        ],
    )
    replay = _reconstruct_preflop(state)
    assert replay["action_sequence"] == expected_sequence
    assert replay["actions"][-1]["kind"] == expected_kind
    assert replay["full_raise_count"] == full_raises


def test_big_blind_twos_fold_to_100bb_shove_but_defend_min_open(monkeypatch):
    monkeypatch.setenv("DISABLE_OVERLAY", "1")
    shove = _state(
        n=2,
        hero=1,
        pot=10100,
        current_bet=10000,
        min_raise_to=19900,
        amount_owed=9900,
        your_stack=9900,
        your_bet_this_street=100,
        players=[
            _player(0, stack=0, bet=10000, all_in=True),
            _player(1, stack=9900, bet=100),
        ],
        action_log=[
            {"seat": 0, "action": "small_blind", "amount": 50},
            {"seat": 1, "action": "big_blind", "amount": 100},
            {"seat": 0, "action": "all_in", "amount": 10000},
        ],
    )
    assert _preflop_action(shove) == {"action": "fold"}

    min_open = _state(
        n=2,
        hero=1,
        pot=300,
        current_bet=200,
        min_raise_to=300,
        amount_owed=100,
        your_stack=9900,
        your_bet_this_street=100,
        players=[
            _player(0, stack=9800, bet=200),
            _player(1, stack=9900, bet=100),
        ],
        action_log=[
            {"seat": 0, "action": "small_blind", "amount": 50},
            {"seat": 1, "action": "big_blind", "amount": 100},
            {"seat": 0, "action": "raise", "amount": 200},
        ],
    )
    assert _preflop_action(min_open) == {"action": "call"}


def test_short_stack_unopened_premium_uses_push_fold_branch(monkeypatch):
    monkeypatch.setenv("DISABLE_OVERLAY", "1")
    state = _state(
        n=6,
        hero=3,
        your_cards=["Qh", "Qs"],
        your_stack=800,
        your_bet_this_street=0,
    )
    assert _preflop_action(state) == {"action": "all_in"}


def _lookup_context(**overrides):
    context = {
        "full_raise_count": 1,
        "hero_full_raise_count": 0,
        "hero_called": False,
        "caller_count": 0,
        "hero_stack_bb": 100.0,
        "effective_stack_bb": 100.0,
        "raise_to_bb": 2.5,
        "pot_odds": 0.25,
        "call_fraction": 0.02,
        "raiser_position": "CO",
        "facing_all_in": False,
    }
    context.update(overrides)
    return context


def test_normal_response_uses_raiser_position_and_callers():
    late_open = lookup("BTN", "A5s", ("raise",), context=_lookup_context())
    early_open = lookup(
        "BTN",
        "A5s",
        ("raise",),
        context=_lookup_context(raiser_position="UTG"),
    )
    squeezed = lookup(
        "BTN",
        "A5s",
        ("raise", "call"),
        context=_lookup_context(caller_count=1),
    )
    assert late_open == {"tag": "threebet"}
    assert early_open == {"tag": "fold"}
    assert squeezed == {"tag": "fold"}


def test_normal_flat_uses_raise_size_and_pot_odds():
    good_price = lookup("BB", "22", ("raise",), context=_lookup_context())
    bad_odds = lookup(
        "BB",
        "22",
        ("raise",),
        context=_lookup_context(pot_odds=0.40),
    )
    oversized = lookup(
        "BB",
        "22",
        ("raise",),
        context=_lookup_context(raise_to_bb=5.0),
    )
    assert good_price == {"tag": "call"}
    assert bad_odds == {"tag": "fold"}
    assert oversized == {"tag": "fold"}


def test_effective_stack_switches_normal_response_to_reshove():
    deep = lookup("BB", "AQs", ("raise",), context=_lookup_context())
    short = lookup(
        "BB",
        "AQs",
        ("raise",),
        context=_lookup_context(hero_stack_bb=15.0, effective_stack_bb=15.0),
    )
    assert deep == {"tag": "threebet"}
    assert short == {"tag": "all_in"}
