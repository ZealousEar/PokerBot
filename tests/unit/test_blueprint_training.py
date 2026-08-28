import hashlib
from pathlib import Path

from src.blueprint_policy import BlueprintPolicy
from tools.train_blueprint import (
    build_context_specs,
    serialize_artifact,
    train_blueprint,
    write_artifact,
)


def test_context_grid_covers_preflop_and_postflop_abstractions():
    specs = build_context_specs()

    assert len(specs) == 234
    assert sum(spec.domain == "preflop" for spec in specs) == 90
    assert sum(spec.domain == "postflop" for spec in specs) == 144
    assert all(len(spec.strengths) == 5 for spec in specs)
    assert all(spec.actions for spec in specs)


def test_small_training_run_is_reproducible_convergent_and_loadable(tmp_path):
    # One signaling spot from each street domain is enough to test the trainer
    # mechanics without retraining the committed full grid in the unit suite.
    all_specs = build_context_specs()
    specs = [all_specs[0], all_specs[100]]

    first = train_blueprint(40, specs=specs)
    second = train_blueprint(40, specs=specs)

    assert serialize_artifact(first) == serialize_artifact(second)
    metadata = first["metadata"]
    assert metadata["requested_iters"] == 40
    assert metadata["completed_iters"] == 40
    assert metadata["policy_rows"] == 10
    assert metadata["meaningfully_mixed_rows"] > 0
    assert (
        metadata["convergence"]["mean_final_gap"]
        < metadata["convergence"]["mean_initial_gap"]
    )

    artifact = tmp_path / "trained.json"
    digest = write_artifact(first, artifact)
    assert len(digest) == 64
    loaded = BlueprintPolicy.load(artifact)
    assert len(loaded) == 10


def test_committed_artifact_records_current_trainer_and_loader_sources():
    root = Path(__file__).resolve().parents[2]
    policy = BlueprintPolicy.load()

    def digest(relative):
        return hashlib.sha256((root / relative).read_bytes()).hexdigest()

    assert policy.metadata["trainer_sha256"] == digest("tools/train_blueprint.py")
    assert policy.metadata["runtime_loader_sha256"] == digest("src/blueprint_policy.py")
