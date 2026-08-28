from src.commitment import (
    call_cost,
    contestable_pot,
    effective_stack,
    incremental_commitment_fraction,
    incremental_cost,
    pot_odds_to_call,
    side_pot_eligible_seats,
    stack_to_pot_ratio,
)
from src.sizing import (
    legal_raise_total,
    normalized_raise_total,
    pot_fraction_raise_total,
)
from src.hand_features import full_house_dominated


def _player(seat, stack, bet, *, folded=False, all_in=False):
    return {
        "seat": seat,
        "stack": stack,
        "bet_this_street": bet,
        "is_folded": folded,
        "is_all_in": all_in,
        "state": "folded" if folded else ("all_in" if all_in else "active"),
    }


def test_short_stack_pot_odds_remove_ineligible_side_pot():
    state = {
        "seat_to_act": 0,
        "pot": 2000,
        "amount_owed": 1000,
        "your_stack": 200,
        "your_bet_this_street": 0,
        "players": [
            _player(0, 200, 0),
            _player(1, 0, 1000, all_in=True),
            _player(2, 5000, 1000),
        ],
    }
    assert call_cost(state) == 200
    # Hero can win only 200 of each opponent's current-street contribution.
    assert contestable_pot(state) == 400
    assert pot_odds_to_call(state) == 200 / 600


def test_incremental_commitment_excludes_already_invested_chips():
    state = {"your_stack": 800, "your_bet_this_street": 200}
    assert incremental_cost(800, state) == 600
    assert incremental_commitment_fraction(800, state) == 0.75


def test_effective_stack_and_spr_are_after_call():
    state = {
        "seat_to_act": 0,
        "pot": 1200,
        "amount_owed": 400,
        "your_stack": 1600,
        "your_bet_this_street": 100,
        "players": [
            _player(0, 1600, 100),
            _player(1, 900, 500),
            _player(2, 4000, 500),
        ],
    }
    assert effective_stack(state, [1], after_call=True) == 900
    assert effective_stack(state, [2], after_call=True) == 1200
    assert stack_to_pot_ratio(state, [2], after_call=True) == 1200 / 1600


def test_side_pot_eligibility_excludes_lower_all_in():
    state = {
        "seat_to_act": 0,
        "amount_owed": 200,
        "your_stack": 3000,
        "your_bet_this_street": 800,
        "players": [
            _player(0, 3000, 800),
            _player(1, 0, 1000, all_in=True),
            _player(2, 1800, 1000),
            _player(3, 0, 700, all_in=True),
        ],
    }
    assert side_pot_eligible_seats(state, 1600) == [2]


def test_pot_fraction_raise_includes_existing_bet_call_and_post_call_pot():
    state = {
        "pot": 1800,
        "current_bet": 600,
        "amount_owed": 400,
        "your_bet_this_street": 200,
        "your_stack": 5000,
        "min_raise_to": 1000,
    }
    # called total 600 + 50% of (1800 pot + 400 call) = 1700 total-to.
    assert pot_fraction_raise_total(1800, state, fraction=0.5) == 1700


def test_min_raise_is_rechecked_before_action_is_emitted():
    state = {
        "pot": 3000,
        "current_bet": 1500,
        "amount_owed": 1000,
        "your_bet_this_street": 500,
        "your_stack": 6000,
        "min_raise_to": 4000,
        "can_check": False,
    }
    assert normalized_raise_total(2200, state) == 4000
    assert incremental_cost(normalized_raise_total(2200, state), state) == 3500
    assert legal_raise_total(2200, state) == {"action": "raise", "amount": 4000}


def test_short_all_in_below_minimum_stays_all_in_not_illegal_raise():
    state = {
        "current_bet": 2000,
        "amount_owed": 2000,
        "your_bet_this_street": 0,
        "your_stack": 900,
        "min_raise_to": 4000,
        "can_check": False,
    }
    assert normalized_raise_total(5000, state) == 900
    assert legal_raise_total(5000, state) == {"action": "all_in"}


def test_trip_board_full_house_is_potentially_quads_dominated():
    assert full_house_dominated(["Qh", "Qd"], ["Ks", "Kh", "Kc", "Qs", "2d"])
