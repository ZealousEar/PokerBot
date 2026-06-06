import sys
from pathlib import Path

import pytest

from tools.edge_case_harness import (
    RUNNER_PYTHON,
    BotSpec,
    candidate_zip_paths,
    check_action_contract,
    expensive_edge_states,
    make_source_submission_dir,
)
from tools.synthetic_opponents import write_opponents


ROOT = Path(__file__).resolve().parents[2]
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from sandbox import match  # noqa: E402


def _synthetic_paths(tmp_path):
    return write_opponents(tmp_path / "synthetic_opponents")


def _match_signature(result):
    return {
        "n_hands": result["n_hands"],
        "chip_delta": result["chip_delta"],
        "final_stacks": result["final_stacks"],
        "bot_errors": result["bot_errors"],
        "actions": [
            [
                (entry.get("seat"), entry.get("bot_id"), entry.get("action"), entry.get("amount"))
                for entry in hand.get("action_log", [])
            ]
            for hand in result["hands"]
        ],
    }


def _run_six_max(hero_path, synthetic_paths, *, hands, seed):
    paths = {"hero": str(hero_path)}
    for name in [
        "maniac_all_in",
        "pot_odds_threshold",
        "river_value_threshold",
        "tight_aggressive",
        "loose_aggressive",
    ]:
        paths[name] = str(synthetic_paths[name])
    return match.run_match(
        f"edge_synth_seed_{seed}",
        paths,
        n_hands=hands,
        verbose=False,
        seed=seed,
    )


def test_synthetic_opponents_return_runner_safe_actions_on_probe_states(tmp_path, monkeypatch):
    monkeypatch.setattr(match.sys, "executable", str(RUNNER_PYTHON))
    opponents = _synthetic_paths(tmp_path)
    states = expensive_edge_states()
    failures = []

    for name, path in opponents.items():
        proc = match.BotProcess(name, str(path))
        try:
            proc.warmup()
            for state_name, state in states:
                action = proc.act(state)
                for issue in check_action_contract(action, state):
                    failures.append(f"{name}:{state_name}:{issue}:action={action}")
        finally:
            proc.stop()

    assert failures == []


def test_six_max_synthetic_suite_is_seed_reproducible_for_canonical_src(tmp_path, monkeypatch):
    monkeypatch.setattr(match.sys, "executable", str(RUNNER_PYTHON))
    hero = make_source_submission_dir(tmp_path / "hero_src")
    opponents = _synthetic_paths(tmp_path)

    first = _run_six_max(hero, opponents, hands=8, seed=20260603)
    second = _run_six_max(hero, opponents, hands=8, seed=20260603)

    assert first["n_hands"] >= 1
    assert first["bot_errors"] == {bot_id: [] for bot_id in first["bot_ids"]}
    assert _match_signature(first) == _match_signature(second)


@pytest.mark.parametrize("spec", candidate_zip_paths(include_deployed=True), ids=lambda spec: spec.name)
def test_candidate_zip_smokes_against_synthetic_edge_suite(spec: BotSpec, tmp_path, monkeypatch):
    monkeypatch.setattr(match.sys, "executable", str(RUNNER_PYTHON))
    opponents = _synthetic_paths(tmp_path)

    result = _run_six_max(spec.path, opponents, hands=6, seed=20260603)

    assert result["n_hands"] >= 1
    assert result["bot_errors"]["hero"] == []
