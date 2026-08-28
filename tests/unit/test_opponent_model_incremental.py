"""Regression contracts for identity-safe incremental opponent tracking."""

import math

import numpy as np
import pytest

from src import opponent_model as om
from src.opponent_model import (
    DEFAULT_PFR,
    DEFAULT_VPIP,
    MAX_AF,
    SHIFT_KEYS,
    OpponentModel,
)


def _players(*pairs):
    return [
        {"seat": seat, "bot_id": bot_id, "state": "active"}
        for seat, bot_id in pairs
    ]


def _state(hand_id, street, actions, players=None):
    return {
        "type": "action_request",
        "hand_id": str(hand_id),
        "street": street,
        "players": players or _players((0, "hero"), (1, "villain")),
        "action_log": list(actions),
    }


def test_repeated_identical_state_is_a_noop():
    model = OpponentModel()
    state = _state(
        1,
        "preflop",
        [
            {"seat": 0, "action": "small_blind", "amount": 50},
            {"seat": 1, "action": "raise", "amount": 250},
        ],
    )
    model.observe_state(state)
    before = model.raw_counts("villain")
    for _ in range(20):
        model.observe_state(state)
    assert model.raw_counts("villain") == before
    assert before["hands"] == 1
    assert before["vpip_done"] == 1
    assert before["pfr_done"] == 1


def test_new_postflop_suffix_never_inflates_vpip_or_pfr():
    model = OpponentModel()
    preflop = [
        {"seat": 0, "action": "small_blind", "amount": 50},
        {"seat": 1, "action": "raise", "amount": 250},
        {"seat": 0, "action": "call", "amount": 250},
    ]
    model.observe_state(_state(2, "preflop", preflop))
    baseline = model.raw_counts("villain")

    flop = preflop + [
        {"seat": 0, "action": "check", "amount": 0, "street": "flop"},
        {"seat": 1, "action": "bet", "amount": 350, "street": "flop"},
        {"seat": 0, "action": "call", "amount": 350, "street": "flop"},
    ]
    model.observe_state(_state(2, "flop", flop))
    after = model.raw_counts("villain")
    assert after["vpip_done"] == baseline["vpip_done"] == 1
    assert after["pfr_done"] == baseline["pfr_done"] == 1
    assert after["bets_raises"] == 1
    assert after["cbet_opportunities"] == 1
    assert after["cbet_done"] == 1


def test_cbet_facing_and_fold_are_counted_only_when_observed():
    model = OpponentModel()
    players = _players((0, "caller"), (1, "raiser"), (2, "folder"))
    preflop = [
        {"seat": 1, "action": "raise", "amount": 300},
        {"seat": 2, "action": "call", "amount": 300},
        {"seat": 0, "action": "call", "amount": 300},
    ]
    model.observe_state(_state(3, "preflop", preflop, players))
    flop = preflop + [
        {"seat": 0, "action": "check", "amount": 0, "street": "flop"},
        {"seat": 1, "action": "bet", "amount": 400, "street": "flop"},
        {"seat": 2, "action": "fold", "amount": 0, "street": "flop"},
        {"seat": 0, "action": "call", "amount": 400, "street": "flop"},
    ]
    model.observe_state(_state(3, "flop", flop, players))

    assert model.raw_counts("raiser")["cbet_opportunities"] == 1
    assert model.raw_counts("raiser")["cbet_done"] == 1
    assert model.raw_counts("folder")["cbet_faced"] == 1
    assert model.raw_counts("folder")["cbet_folded"] == 1
    assert model.raw_counts("caller")["cbet_faced"] == 1
    assert model.raw_counts("caller")["cbet_folded"] == 0


def test_unlabelled_cross_street_suffix_fails_closed():
    """A next-flop snapshot still contains unseen preflop tail actions."""
    model = OpponentModel()
    preflop_seen = [{"seat": 1, "action": "raise", "amount": 300}]
    model.observe_state(_state(4, "preflop", preflop_seen))

    # Hero's returned preflop call was not visible on the prior decide call.
    # The following villain action is on the flop, but neither entry has a
    # street marker, so their boundary is unknowable and both must be skipped.
    mixed_transition = preflop_seen + [
        {"seat": 0, "action": "call", "amount": 300},
        {"seat": 1, "action": "bet", "amount": 450},
    ]
    model.observe_state(_state(4, "flop", mixed_transition))
    counts = model.raw_counts("villain")
    assert counts["vpip_done"] == 1
    assert counts["pfr_done"] == 1
    assert counts["bets_raises"] == 0
    assert counts["cbet_opportunities"] == 0


def test_profiles_follow_bot_id_across_seat_reindex_and_reuse():
    model = OpponentModel()
    model.observe_state(
        _state(
            10,
            "preflop",
            [{"seat": 1, "action": "raise", "amount": 250}],
            _players((0, "hero"), (1, "alpha"), (2, "beta")),
        )
    )
    # Alpha moves after a bust; gamma takes alpha's old physical seat.
    remapped = _players((0, "hero"), (1, "gamma"), (2, "alpha"))
    model.observe_state(
        _state(
            11,
            "preflop",
            [
                {"seat": 1, "action": "fold", "amount": 0},
                {"seat": 2, "action": "call", "amount": 100},
            ],
            remapped,
        )
    )

    assert model.identity_for(1) == "gamma"
    assert model.identity_for(2) == "alpha"
    assert model.raw_counts("alpha")["hands"] == 2
    assert model.raw_counts("alpha")["vpip_done"] == 2
    assert model.raw_counts("alpha")["pfr_done"] == 1
    assert model.raw_counts("gamma")["hands"] == 1
    assert model.raw_counts("gamma")["vpip_done"] == 0
    # Legacy seat reads resolve to the current occupant, not pooled history.
    assert model.raw_counts(1) == model.raw_counts("gamma")


def test_rolling_200_entry_window_preserves_cumulative_counts():
    model = OpponentModel()
    history = [
        {
            "hand_num": hand,
            "street": "preflop",
            "seat": 1,
            "bot_id": "villain",
            "action": "call" if hand % 2 else "fold",
            "amount": 100 if hand % 2 else 0,
        }
        for hand in range(250)
    ]
    model.observe_log(history[:200])
    model.observe_log(history[50:250])
    model.observe_log(history[50:250])  # exact replay is also a no-op
    counts = model.raw_counts("villain")
    assert counts["hands"] == 250
    assert counts["vpip_chances"] == 250
    assert counts["vpip_done"] == 125


def test_unlabelled_postflop_history_is_not_guessed_preflop():
    model = OpponentModel()
    model.observe_log([
        {
            "hand_num": 1,
            "seat": 1,
            "bot_id": "villain",
            "action": "raise",
            "amount": 500,
        }
    ])
    assert model.raw_counts("villain") == {}
    assert model.features("villain")["vpip"] == DEFAULT_VPIP
    assert model.exploit_shift("villain") == {key: 0.0 for key in SHIFT_KEYS}


def test_bayesian_features_are_bounded_and_shrunk():
    model = OpponentModel()
    for hand in range(5):
        model.observe_state(
            _state(
                hand,
                "preflop",
                [{"seat": 1, "action": "raise", "amount": 300}],
            )
        )
    features = model.features("villain")
    assert DEFAULT_VPIP < features["vpip"] < 1.0
    assert DEFAULT_PFR < features["pfr"] < 1.0
    assert 0.0 < features["confidence"] < 1.0
    for name in ("vpip", "pfr", "cbet", "fold_to_cbet", "confidence"):
        assert 0.0 <= features[name] <= 1.0
    assert 0.0 <= features["af"] <= MAX_AF


def test_corrupt_counters_fail_closed_to_neutral(monkeypatch):
    model = OpponentModel()
    model._counts["villain"].update({
        "hands": 100,
        "vpip_chances": 10,
        "vpip_done": 11,  # impossible
    })
    monkeypatch.setattr(om, "_FIELD_PRIORS", {
        "feature_names": ("vpip",),
        "cluster_names": ("x",),
        "cluster_centroids": np.zeros((1, 1), dtype=np.float32),
        "cluster_scales": np.ones((1,), dtype=np.float32),
        "shift_by_cluster": np.ones((1, len(SHIFT_KEYS)), dtype=np.float32),
    })
    features = model.features("villain")
    assert features["confidence"] == 0.0
    assert features["vpip"] == DEFAULT_VPIP
    assert model.archetype("villain") == "unknown"
    assert model.exploit_shift("villain") == {key: 0.0 for key in SHIFT_KEYS}


def test_corrupt_logs_do_not_create_folded_profiles():
    model = OpponentModel()
    players = _players((0, "hero"), (1, "villain"))
    for hand in range(40):
        model.observe_state(
            _state(
                f"bad-{hand}",
                "preflop",
                [{"seat": 1, "action": "teleport", "amount": float("nan")}],
                players,
            )
        )
    assert model.features("villain")["hands"] == 0
    assert model.features("villain")["confidence"] == 0.0
    assert model.exploit_shift("villain") == {key: 0.0 for key in SHIFT_KEYS}


def test_probability_contract_survives_extreme_valid_counts():
    model = OpponentModel()
    counts = model._counts["villain"]
    counts.update({
        "hands": 1_000_000,
        "vpip_chances": 1_000_000,
        "vpip_done": 1_000_000,
        "pfr_chances": 1_000_000,
        "pfr_done": 0,
        "bets_raises": 1_000_000,
        "calls": 0,
        "cbet_opportunities": 1_000_000,
        "cbet_done": 1_000_000,
        "cbet_faced": 1_000_000,
        "cbet_folded": 0,
    })
    features = model.features("villain")
    assert all(math.isfinite(value) for value in features.values())
    for name in ("vpip", "pfr", "cbet", "fold_to_cbet", "confidence"):
        assert 0.0 <= features[name] <= 1.0
    assert 0.0 <= features["af"] <= MAX_AF
