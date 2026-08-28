from src.postflop import action_context, identify_aggressor, weighted_range_for


class _ColdModel:
    def archetype(self, seat, players=None):
        return "unknown"


def _player(seat, stack=8000, bet=0, *, folded=False):
    return {
        "seat": seat,
        "bot_id": f"bot-{seat}",
        "stack": stack,
        "bet_this_street": bet,
        "is_folded": folded,
        "is_all_in": False,
        "state": "folded" if folded else "active",
    }


def _state():
    return {
        "street": "flop",
        "seat_to_act": 0,
        "pot": 1800,
        "current_bet": 600,
        "amount_owed": 600,
        "your_stack": 8000,
        "your_bet_this_street": 0,
        "your_cards": ["Kh", "Qh"],
        "community_cards": ["Ah", "7d", "2c"],
        "players": [_player(0), _player(1, bet=0), _player(2, bet=600)],
        "action_log": [
            {"street": "preflop", "seat": 1, "action": "raise", "amount": 300},
            {"street": "flop", "seat": 1, "action": "check", "amount": 0},
            {"street": "flop", "seat": 2, "action": "raise", "amount": 600},
        ],
    }


def test_identifies_actual_current_street_aggressor():
    state = _state()
    assert identify_aggressor(state) == 2
    assert action_context(state, 2)["label"] == "bet"
    assert action_context(state, 1)["label"] == "check"


def test_legacy_log_uses_live_current_street_bet_to_find_aggressor():
    state = _state()
    for entry in state["action_log"]:
        entry.pop("street")
    assert identify_aggressor(state) == 2


def test_legacy_log_does_not_reuse_old_aggressor_when_live_bet_is_zero():
    state = _state()
    for entry in state["action_log"]:
        entry.pop("street")
    state.update(current_bet=0, amount_owed=0)
    for player in state["players"]:
        player["bet_this_street"] = 0
    assert identify_aggressor(state) == -1


def test_unlabelled_all_in_call_is_not_the_aggressor():
    state = _state()
    state["players"] = [
        _player(0),
        _player(1, stack=7500, bet=500),
        {
            **_player(2, stack=0, bet=500),
            "is_all_in": True,
            "state": "all_in",
        },
    ]
    state.update(current_bet=500, amount_owed=500)
    state["action_log"] = [
        {"seat": 1, "action": "raise", "amount": 500},
        {"seat": 2, "action": "all_in", "amount": 500},
    ]
    assert identify_aggressor(state) == 1
    assert action_context(state, 2)["label"] == "call"


def test_unlabelled_same_actor_old_raise_is_not_counted_on_new_street():
    state = _state()
    state["action_log"] = [
        {"seat": 2, "action": "raise", "amount": 300},
        {"seat": 1, "action": "call", "amount": 300},
        {"seat": 2, "action": "raise", "amount": 600},
    ]
    assert identify_aggressor(state) == 2
    assert action_context(state, 2)["label"] == "bet"
    assert action_context(state, 2)["raise_count"] == 0


def test_unlabelled_old_call_does_not_label_unacted_player_as_caller():
    state = _state()
    state["players"].append(_player(3, bet=0))
    state["action_log"] = [
        {"seat": 2, "action": "raise", "amount": 300},
        {"seat": 3, "action": "call", "amount": 300},
        {"seat": 2, "action": "raise", "amount": 600},
    ]
    assert action_context(state, 3)["label"] == "unknown"


def test_aggressive_range_weights_made_hands_above_air():
    state = _state()
    weighted = weighted_range_for(state, 2, model=_ColdModel())
    by_cards = {frozenset((str(combo[0]), str(combo[1]))): weight
                for combo, weight in weighted}
    # AA is top set; KQ is only two overcards on A72. Both are in the base
    # aggressive prior, and board/action conditioning must favor the made hand.
    top_set = by_cards[frozenset(("As", "Ad"))]
    air = by_cards[frozenset(("Ks", "Qd"))]
    assert top_set > air * 3


def test_deep_all_in_uses_tighter_range_than_shallow_jam():
    shallow = _state()
    shallow.update(pot=3600, current_bet=2400, amount_owed=2400, your_stack=2400)
    shallow["players"][2].update(stack=0, bet_this_street=2400,
                                  is_all_in=True, state="all_in")
    shallow["action_log"][-1].update(action="all_in", amount=2400)

    deep = _state()
    deep.update(pot=10400, current_bet=9200, amount_owed=9200, your_stack=9200)
    deep["players"][2].update(stack=0, bet_this_street=9200,
                              is_all_in=True, state="all_in")
    deep["action_log"][-1].update(action="all_in", amount=9200)

    shallow_cards = {frozenset((str(c[0]), str(c[1])))
                     for c, _ in weighted_range_for(shallow, 2, model=_ColdModel())}
    deep_cards = {frozenset((str(c[0]), str(c[1])))
                  for c, _ in weighted_range_for(deep, 2, model=_ColdModel())}
    assert frozenset(("4s", "4d")) in shallow_cards
    assert frozenset(("4s", "4d")) not in deep_cards
