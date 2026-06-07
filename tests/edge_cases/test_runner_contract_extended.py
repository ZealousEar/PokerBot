import pytest

pytestmark = pytest.mark.requires_engine

from tools.edge_case_harness import (
    LARGE_COMMITMENT_GUARD_STATES,
    BotSpec,
    RunnerClient,
    candidate_zip_paths,
    check_action_contract,
    commitment_fraction,
    expensive_edge_states,
    is_large_commit,
    make_source_submission_dir,
)


@pytest.fixture(scope="module")
def bot_subjects(tmp_path_factory):
    root = tmp_path_factory.mktemp("bot_subjects")
    subjects = [
        BotSpec("canonical_src", make_source_submission_dir(root / "canonical_src"), "SRC"),
    ]
    subjects.extend(candidate_zip_paths(include_deployed=True))
    return subjects


def test_subjects_survive_warmup_and_expensive_failure_states(bot_subjects):
    states = expensive_edge_states()
    failures = []

    for spec in bot_subjects:
        with RunnerClient(spec.path) as runner:
            warmup = runner.send({"type": "warmup"})
            if warmup.payload.get("ok") is not True:
                failures.append(f"{spec.name}:warmup_failed:{warmup.payload}")

            for name, state in states:
                result = runner.send(state)
                action = result.payload
                if "error" in action:
                    failures.append(f"{spec.name}:{name}:runner_error:{action['error']}")
                if result.elapsed_s > 2.25:
                    failures.append(f"{spec.name}:{name}:elapsed:{result.elapsed_s:.3f}s")
                for issue in check_action_contract(action, state):
                    failures.append(f"{spec.name}:{name}:{issue}:action={action}")

    assert failures == []


def test_subjects_do_not_large_commit_near_dead_postflop_spots(bot_subjects):
    vulnerable = [
        (name, state)
        for name, state in expensive_edge_states()
        if name in LARGE_COMMITMENT_GUARD_STATES
    ]
    failures = []

    for spec in bot_subjects:
        with RunnerClient(spec.path) as runner:
            warmup = runner.send({"type": "warmup"})
            if warmup.payload.get("ok") is not True:
                failures.append(f"{spec.name}:warmup_failed:{warmup.payload}")
                continue
            for name, state in vulnerable:
                result = runner.send(state)
                action = result.payload
                if is_large_commit(action, state, threshold=0.40):
                    failures.append(
                        f"{spec.name}:{name}:large_commit:"
                        f"{commitment_fraction(action, state):.3f}:action={action}"
                    )

    assert failures == []


def test_runner_reports_warmup_exception_without_poisoning_next_decision(tmp_path):
    bot_dir = tmp_path / "warmup_exception_bot"
    bot_dir.mkdir()
    (bot_dir / "bot.py").write_text(
        """
def decide(state):
    if state.get("type") == "warmup":
        raise RuntimeError("boom")
    if state.get("can_check"):
        return {"action": "check"}
    return {"action": "fold"}
""".strip()
    )

    with RunnerClient(bot_dir, action_timeout_s=1, warmup_timeout_s=1) as runner:
        warmup = runner.send({"type": "warmup"})
        assert warmup.payload == {"ok": False, "error": "warmup_exception"}

        action = runner.send({
            "type": "action_request",
            "amount_owed": 0,
            "can_check": True,
        })
        assert action.payload == {"action": "check"}


def test_runner_reports_per_decision_timeout(tmp_path):
    bot_dir = tmp_path / "timeout_bot"
    bot_dir.mkdir()
    (bot_dir / "bot.py").write_text(
        """
import time


def decide(state):
    if state.get("type") == "warmup":
        return {"action": "check"}
    time.sleep(2)
    return {"action": "check"}
""".strip()
    )

    with RunnerClient(bot_dir, action_timeout_s=1, warmup_timeout_s=1) as runner:
        assert runner.send({"type": "warmup"}).payload == {"ok": True}
        result = runner.send({
            "type": "action_request",
            "amount_owed": 0,
            "can_check": True,
        })

    assert result.payload == {"action": "fold", "error": "timeout"}
    assert result.elapsed_s < 1.75
