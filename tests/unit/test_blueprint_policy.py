import hashlib
import json

import pytest

from src.blueprint_policy import (
    BlueprintPolicy,
    BlueprintPolicyError,
    most_likely,
    postflop_strength_bucket,
    preflop_strength_bucket,
    sample_action,
)


def test_committed_blueprint_is_trained_complete_and_mixed():
    policy = BlueprintPolicy.load()

    assert len(policy) == 1170
    assert policy.metadata["requested_iters"] > 0
    assert policy.metadata["completed_iters"] == policy.metadata["requested_iters"]
    assert policy.metadata["public_contexts"] == 234
    assert policy.metadata["policy_rows"] == len(policy)
    assert policy.metadata["meaningfully_mixed_rows"] > 0
    convergence = policy.metadata["convergence"]
    assert convergence["mean_final_gap"] < convergence["mean_initial_gap"]


def test_runtime_helpers_route_to_exact_trained_rows():
    policy = BlueprintPolicy.load()

    preflop = policy.preflop_distribution(
        "BTN", "AKs", pressure="unopened", effective_stack_bb=100
    )
    assert set(preflop) == {"fold", "open_small", "open_large"}
    assert sum(preflop.values()) == pytest.approx(1.0)

    postflop = policy.postflop_distribution(
        "river",
        0.91,
        texture="paired",
        pressure="large",
        spr=7.0,
        is_nutted=True,
    )
    assert set(postflop) == {"fold", "call", "raise_small", "raise_large"}
    assert sum(postflop.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("hand", "expected"),
    [
        ("AA", "premium"),
        ("AKs", "premium"),
        ("QJo", "medium"),
        ("76s", "weak"),
        ("72o", "trash"),
    ],
)
def test_preflop_strength_abstraction(hand, expected):
    assert preflop_strength_bucket(hand) == expected


def test_postflop_strength_abstraction_uses_structural_flags():
    assert postflop_strength_bucket(0.20) == "air"
    assert postflop_strength_bucket(0.20, has_draw=True) == "draw"
    assert postflop_strength_bucket(0.52) == "marginal"
    assert postflop_strength_bucket(0.75) == "strong"
    assert postflop_strength_bucket(0.50, is_nutted=True) == "nuts"


def test_distribution_selection_is_deterministic_and_not_forced_pure():
    distribution = {"call": 0.25, "fold": 0.75}

    assert most_likely(distribution) == "fold"
    assert sample_action(distribution, 0.10) == "call"
    assert sample_action(distribution, 0.25) == "fold"
    assert sample_action(distribution, 0.999999) == "fold"


@pytest.mark.parametrize(
    "distribution",
    [
        {"call": 1.1, "fold": -0.1},
        {"call": 1.1, "fold": 0.0},
        {"call": 0.4, "fold": 0.4},
        {"call": float("nan"), "fold": 1.0},
    ],
)
def test_distribution_selection_rejects_invalid_probabilities(distribution):
    with pytest.raises(BlueprintPolicyError):
        sample_action(distribution, 0.0)


def test_loader_rejects_tampered_artifact(tmp_path):
    payload = {
        "schema_version": 1,
        "metadata": {"requested_iters": 1, "completed_iters": 1},
        "policies": {"fixture": {"fold": 1.0}},
    }
    artifact = tmp_path / "policy.json"
    raw = (json.dumps(payload, sort_keys=True) + "\n").encode()
    artifact.write_bytes(raw)
    artifact.with_suffix(".sha256").write_text(
        f"{hashlib.sha256(raw).hexdigest()}  {artifact.name}\n"
    )
    BlueprintPolicy.load(artifact)

    artifact.write_bytes(raw + b" ")
    with pytest.raises(BlueprintPolicyError, match="digest mismatch"):
        BlueprintPolicy.load(artifact)
