import src.bot as bot
import src.postflop as postflop


class _SizingPolicy:
    def __init__(self, preflop_action="open_small", postflop_action="bet_small"):
        self.preflop_action = preflop_action
        self.postflop_action = postflop_action
        self.preflop_calls = 0
        self.postflop_calls = 0

    def preflop_distribution(self, *args, **kwargs):
        self.preflop_calls += 1
        return {self.preflop_action: 1.0}

    def postflop_distribution(self, *args, **kwargs):
        self.postflop_calls += 1
        return {self.postflop_action: 1.0}


class _BrokenPolicy:
    def preflop_distribution(self, *args, **kwargs):
        raise ValueError("corrupt policy")


def _player(seat, stack=9900, bet=0):
    return {
        "seat": seat,
        "bot_id": f"p{seat}",
        "stack": stack,
        "state": "active",
        "is_folded": False,
        "is_all_in": False,
        "bet_this_street": bet,
        "hole_cards": None,
    }


def _preflop_state(cards=("As", "Kd")):
    # BTN=0, SB=1, BB=2, CO=5.
    return {
        "type": "action_request",
        "hand_id": "mix_preflop",
        "street": "preflop",
        "seat_to_act": 5,
        "pot": 150,
        "community_cards": [],
        "current_bet": 100,
        "min_raise_to": 200,
        "amount_owed": 100,
        "can_check": False,
        "your_cards": list(cards),
        "your_stack": 10000,
        "your_bet_this_street": 0,
        "players": [_player(i) for i in range(6)],
        "action_log": [
            {"seat": 1, "action": "small_blind", "amount": 50},
            {"seat": 2, "action": "big_blind", "amount": 100},
        ],
    }


def _postflop_state(*, can_check=True):
    owed = 0 if can_check else 500
    current_bet = 0 if can_check else 500
    return {
        "type": "action_request",
        "hand_id": "mix_postflop",
        "street": "flop",
        "seat_to_act": 0,
        "pot": 1000,
        "community_cards": ["Ah", "7d", "2c"],
        "current_bet": current_bet,
        "min_raise_to": 100 if can_check else 1000,
        "amount_owed": owed,
        "can_check": can_check,
        "your_cards": ["As", "Ad"],
        "your_stack": 5000,
        "your_bet_this_street": 0,
        "players": [
            _player(0, stack=5000),
            _player(1, stack=4500, bet=current_bet),
        ],
        "action_log": [] if can_check else [
            {"seat": 1, "action": "raise", "amount": current_bet},
        ],
    }


def test_trained_preflop_lookup_selects_distinct_permitted_sizes(monkeypatch):
    small = _SizingPolicy(preflop_action="open_small")
    monkeypatch.setattr(bot, "_BLUEPRINT", small)
    assert bot._preflop_action(_preflop_state()) == {"action": "raise", "amount": 225}
    assert small.preflop_calls == 1

    large = _SizingPolicy(preflop_action="open_large")
    monkeypatch.setattr(bot, "_BLUEPRINT", large)
    assert bot._preflop_action(_preflop_state()) == {"action": "raise", "amount": 300}
    assert large.preflop_calls == 1


def test_committed_blueprint_is_loaded_into_live_bot_path():
    assert bot._BLUEPRINT is not None
    assert bot._BLUEPRINT.metadata["completed_iters"] > 0


def test_trained_preflop_lookup_cannot_widen_a_chart_fold(monkeypatch):
    policy = _SizingPolicy(preflop_action="open_large")
    monkeypatch.setattr(bot, "_BLUEPRINT", policy)
    # CO 72o is outside the maintained open chart, so the artifact cannot turn
    # its sizing recommendation into an aggressive action.
    assert bot._preflop_action(_preflop_state(("7s", "2d"))) == {"action": "fold"}
    assert policy.preflop_calls == 1


def test_missing_blueprint_falls_back_to_chart_default(monkeypatch):
    monkeypatch.setattr(bot, "_BLUEPRINT", None)
    assert bot._preflop_action(_preflop_state()) == {"action": "raise", "amount": 250}

    monkeypatch.setattr(bot, "_BLUEPRINT", _BrokenPolicy())
    assert bot._preflop_action(_preflop_state()) == {"action": "raise", "amount": 250}


def test_trained_postflop_lookup_selects_distinct_safe_bet_sizes(monkeypatch):
    monkeypatch.setattr(postflop, "equity_vs_ranges", lambda *args, **kwargs: 0.95)

    small = _SizingPolicy(postflop_action="bet_small")
    action = postflop.decide_postflop(
        _postflop_state(), blueprint_only=True, blueprint_policy=small
    )
    assert action == {"action": "raise", "amount": 330}
    assert small.postflop_calls == 1

    large = _SizingPolicy(postflop_action="bet_large")
    action = postflop.decide_postflop(
        _postflop_state(), blueprint_only=True, blueprint_policy=large
    )
    assert action == {"action": "raise", "amount": 750}
    assert large.postflop_calls == 1


def test_trained_postflop_lookup_cannot_override_fold_gate(monkeypatch):
    monkeypatch.setattr(postflop, "equity_vs_ranges", lambda *args, **kwargs: 0.0)
    policy = _SizingPolicy(postflop_action="raise_large")
    action = postflop.decide_postflop(
        _postflop_state(can_check=False),
        blueprint_only=True,
        blueprint_policy=policy,
    )
    assert action == {"action": "fold"}
    assert policy.postflop_calls == 0
