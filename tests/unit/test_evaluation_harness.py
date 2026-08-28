import json
import sys
from pathlib import Path

import pytest

from tools import benchmark, qualifier_replay, self_play
from tools.evaluation import (
    BotArtifact,
    EvaluationConfig,
    EvaluationError,
    MatchFailure,
    clustered_bootstrap_ci,
    evaluate,
    load_engine,
    make_head_to_head_lineup,
    make_replacement_lineup,
)


def _artifact(tmp_path: Path, name: str) -> BotArtifact:
    path = tmp_path / f"{name}.py"
    path.write_text("def decide(state):\n    return {'action': 'fold'}\n", encoding="utf-8")
    return BotArtifact(name, path)


def test_replacement_rotation_sends_every_identity_through_every_seat(tmp_path):
    hero = _artifact(tmp_path, "hero")
    opponents = [_artifact(tmp_path, f"opp{i}") for i in range(5)]
    occupied = {artifact.label: set() for artifact in [hero, *opponents]}

    for rotation in range(6):
        paths, metadata = make_replacement_lineup(hero, opponents, rotation)
        assert len(paths) == 6
        assert metadata["seats"][rotation]["bot_id"] == "hero"
        for row in metadata["seats"]:
            occupied[row["artifact"]].add(row["seat"])

    assert occupied == {label: set(range(6)) for label in occupied}


def test_head_to_head_rotation_is_three_vs_three_and_balanced(tmp_path):
    candidate = _artifact(tmp_path, "candidate")
    baseline = _artifact(tmp_path, "baseline")
    candidate_seats = set()
    baseline_seats = set()

    for rotation in range(6):
        paths, metadata = make_head_to_head_lineup(candidate, baseline, rotation)
        assert len(paths) == 6
        assert len(metadata["focal_ids"]) == 3
        assert len(metadata["opposing_ids"]) == 3
        for row in metadata["seats"]:
            if row["artifact"] == "candidate":
                candidate_seats.add(row["seat"])
            else:
                baseline_seats.add(row["seat"])

    assert candidate_seats == set(range(6))
    assert baseline_seats == set(range(6))


def test_paired_replacement_evaluation_writes_raw_manifest_and_seed_cluster_ci(tmp_path):
    candidate = _artifact(tmp_path, "candidate")
    baseline = _artifact(tmp_path, "baseline")
    opponents = [_artifact(tmp_path, f"opp{i}") for i in range(5)]
    calls = []

    def fake_run_match(name, paths, *, n_hands, verbose, seed):
        del verbose
        hero_seat = list(paths).index("hero")
        calls.append((name, seed, hero_seat, tuple(paths)))
        hero_path = Path(paths["hero"]).stem
        common_noise = seed * 3 + hero_seat * 7
        hero_delta = common_noise + (100 if hero_path == "candidate" else 60)
        return {
            "n_hands": n_hands,
            "chip_delta": {bot_id: hero_delta if bot_id == "hero" else -hero_delta / 5 for bot_id in paths},
            "final_stacks": {bot_id: 10_000 for bot_id in paths},
            "bot_errors": {bot_id: [] for bot_id in paths},
            "hands": [],
        }

    output_dir = tmp_path / "evaluation"
    config = EvaluationConfig(
        hands=100,
        seeds=(10, 11),
        rotations=(0, 3),
        big_blind=100,
        bootstrap_samples=200,
        bootstrap_seed=9,
        design="replacement",
    )
    summary = evaluate(
        run_match=fake_run_match,
        engine_provenance={"engine": "fake"},
        candidate=candidate,
        baseline=baseline,
        opponents=opponents,
        config=config,
        output_dir=output_dir,
        run_label="unit",
    )

    assert len(calls) == 8
    for first, second in zip(calls[::2], calls[1::2]):
        assert first[0] == second[0]
        assert first[1:3] == second[1:3]
        assert first[3] == second[3]
    ci = summary["result"]["paired_comparison"]["candidate_minus_baseline_bb_per_100_ci"]
    assert ci["estimate"] == pytest.approx(0.4)
    assert ci["cluster_count"] == 2
    assert ci["method"] == "seed_cluster_percentile"

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in (output_dir / "raw_results.jsonl").read_text().splitlines()]
    saved_summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "complete"
    assert manifest["engine_calls"] == 8
    assert len(raw) == 8
    assert saved_summary == summary


def test_head_to_head_uses_one_engine_call_per_seed_rotation(tmp_path):
    candidate = _artifact(tmp_path, "candidate")
    baseline = _artifact(tmp_path, "baseline")
    calls = []

    def fake_run_match(name, paths, *, n_hands, verbose, seed):
        del name, verbose, seed
        calls.append(tuple(paths.values()))
        deltas = {
            bot_id: 30 if Path(path).stem == "candidate" else -30
            for bot_id, path in paths.items()
        }
        return {"n_hands": n_hands, "chip_delta": deltas, "bot_errors": {}}

    summary = evaluate(
        run_match=fake_run_match,
        engine_provenance={"engine": "fake"},
        candidate=candidate,
        baseline=baseline,
        opponents=(),
        config=EvaluationConfig(
            hands=100,
            seeds=(1, 2),
            rotations=(0, 1, 2),
            bootstrap_samples=50,
            design="head_to_head",
        ),
        output_dir=tmp_path / "head_to_head",
    )

    assert len(calls) == 6
    comparison = summary["result"]["paired_comparison"]
    assert comparison["pair_count"] == 6
    assert comparison["candidate_minus_baseline_bb_per_100_ci"]["estimate"] == pytest.approx(0.6)


def test_strict_engine_errors_fail_and_mark_manifest(tmp_path):
    candidate = _artifact(tmp_path, "candidate")
    opponents = [_artifact(tmp_path, f"opp{i}") for i in range(5)]
    output_dir = tmp_path / "failed"

    def failed_match(name, paths, *, n_hands, verbose, seed):
        del name, verbose, seed
        return {
            "n_hands": n_hands,
            "chip_delta": {bot_id: 0 for bot_id in paths},
            "bot_errors": {"hero": ["timeout"]},
        }

    with pytest.raises(MatchFailure, match="bot errors"):
        evaluate(
            run_match=failed_match,
            engine_provenance={"engine": "fake"},
            candidate=candidate,
            opponents=opponents,
            config=EvaluationConfig(hands=10, seeds=(1,), rotations=(0,)),
            output_dir=output_dir,
        )
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert manifest["failure"]["type"] == "MatchFailure"


def test_clustered_ci_averages_rotations_within_seed_before_resampling():
    ci = clustered_bootstrap_ci(
        {1: [0.0, 100.0], 2: [20.0, 20.0]}, samples=500, rng_seed=4
    )
    assert ci["estimate"] == pytest.approx(35.0)
    assert ci["cluster_count"] == 2


def test_history_analyzer_and_decision_replay_support_engine_json_fixture():
    state = {
        "hand_id": "h1",
        "street": "preflop",
        "your_cards": ["As", "Ks"],
        "players": [],
        "amount_owed": 100,
    }
    document = {
        "n_hands": 1,
        "chip_delta": {"hero": 150, "villain": -150},
        "hands": [
            {
                "hand_id": "h1",
                "players": [
                    {"seat": 0, "bot_id": "hero"},
                    {"seat": 1, "bot_id": "villain"},
                ],
                "community_cards": [],
                "action_log": [
                    {
                        "seat": 0,
                        "street": "preflop",
                        "action": "raise",
                        "amount": 300,
                        "state_before": state,
                    },
                    {"seat": 1, "street": "preflop", "action": "fold"},
                ],
            }
        ],
    }

    summary, hand_records, decisions = qualifier_replay.analyze_documents(
        [("fixture.json", document)], hero_id="hero"
    )
    assert summary["match_count"] == 1
    assert summary["hand_count"] == 1
    assert summary["action_counts"] == {"raise": 1}
    assert summary["chip_delta_total"] == 150
    assert len(hand_records) == 1
    assert len(decisions) == 1

    replay_summary, replay_records = qualifier_replay.replay_decisions(
        decisions, lambda replay_state: {"action": "raise", "amount": 300}
    )
    assert replay_summary["action_agreement_rate"] == 1.0
    assert replay_summary["exact_agreement_rate"] == 1.0
    assert replay_records[0]["actual_action"]["amount"] == 300


def test_history_analyzer_prefers_official_rich_events_for_bot_and_street():
    document = {
        "chip_delta": {"hero": 20, "villain": -20},
        "hands": [
            {
                "hand_id": "official_h1",
                "action_log": [{"seat": 0, "action": "call", "amount": 100}],
                "events": [
                    {
                        "type": "action",
                        "street": "preflop",
                        "seat": 0,
                        "bot_id": "hero",
                        "action": "call",
                        "amount": 100,
                    },
                    {"type": "showdown", "street": "river"},
                ],
            }
        ],
    }

    summary, records, _ = qualifier_replay.analyze_documents(
        [("official.json", document)], hero_id="hero"
    )
    assert summary["action_counts"] == {"call": 1}
    assert summary["street_action_counts"] == {"preflop": {"call": 1}}
    assert records[0]["actions"][0]["actor"] == "hero"


def test_history_analyzer_fails_when_no_hands_are_recognized():
    with pytest.raises(EvaluationError, match="no recognizable hands"):
        qualifier_replay.analyze_documents([("empty.json", {"metadata": {}})])


def test_qualifier_analysis_cli_is_engine_free_and_writes_machine_outputs(tmp_path, capsys):
    history = tmp_path / "qualifier.json"
    history.write_text(
        json.dumps(
            {
                "chip_delta": {"hero": 75, "villain": -75},
                "hands": [
                    {
                        "hand_id": "q1",
                        "players": [{"seat": 0, "bot_id": "hero"}],
                        "action_log": [{"seat": 0, "action": "fold", "street": "preflop"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "qualifier_output"

    assert qualifier_replay.main(
        ["--history", str(history), "--hero-id", "hero", "--output-dir", str(output)]
    ) == 0
    manifest = json.loads((output / "manifest.json").read_text())
    summary = json.loads((output / "summary.json").read_text())
    records = [json.loads(line) for line in (output / "records.jsonl").read_text().splitlines()]
    assert manifest["status"] == "complete"
    assert summary["analysis"]["chip_delta_total"] == 75
    assert records[0]["record_type"] == "hand"
    assert json.loads(capsys.readouterr().out)["output_dir"] == str(output.resolve())


def test_benchmark_cli_runs_against_documented_engine_api(tmp_path, capsys):
    engine = tmp_path / "engine"
    sandbox = engine / "sandbox"
    sandbox.mkdir(parents=True)
    (sandbox / "__init__.py").write_text("", encoding="utf-8")
    (sandbox / "runner.py").write_text("# fake runner\n", encoding="utf-8")
    (sandbox / "match.py").write_text(
        "def run_match(name, paths, n_hands, verbose, seed):\n"
        "    delta = seed + list(paths).index('hero')\n"
        "    return {'n_hands': n_hands, "
        "'chip_delta': {key: (delta if key == 'hero' else -delta / 5) for key in paths}, "
        "'bot_errors': {key: [] for key in paths}, 'hands': []}\n",
        encoding="utf-8",
    )
    for name in benchmark.TEMPLATES:
        bot_dir = engine / "bots" / name
        bot_dir.mkdir(parents=True)
        (bot_dir / "bot.py").write_text(
            "def decide(state):\n    return {'action': 'fold'}\n", encoding="utf-8"
        )
    candidate = _artifact(tmp_path, "cli_candidate")
    output = tmp_path / "cli_output"
    try:
        code = benchmark.main(
            [
                "--all-templates",
                "--candidate",
                str(candidate.path),
                "--hands",
                "10",
                "--paired-seed-base",
                "5",
                "--paired-seed-count",
                "2",
                "--rotations",
                "0,5",
                "--bootstrap-samples",
                "20",
                "--engine-dir",
                str(engine),
                "--output-dir",
                str(output),
            ]
        )
    finally:
        for name in list(sys.modules):
            if name == "sandbox" or name.startswith("sandbox."):
                sys.modules.pop(name, None)
        while str(engine.resolve()) in sys.path:
            sys.path.remove(str(engine.resolve()))

    assert code == 0
    assert json.loads((output / "manifest.json").read_text())["status"] == "complete"
    assert len((output / "raw_results.jsonl").read_text().splitlines()) == 4
    stdout = capsys.readouterr().out
    assert json.loads(stdout)["output_dir"] == str(output.resolve())


def test_engine_loader_can_switch_between_checkouts_in_one_process(tmp_path):
    roots = []
    try:
        for marker in ("first", "second"):
            engine = tmp_path / marker
            sandbox = engine / "sandbox"
            sandbox.mkdir(parents=True)
            (sandbox / "__init__.py").write_text("", encoding="utf-8")
            (sandbox / "runner.py").write_text("# runner\n", encoding="utf-8")
            (sandbox / "match.py").write_text(
                f"def run_match(*args, **kwargs):\n    return {{'marker': '{marker}'}}\n",
                encoding="utf-8",
            )
            roots.append(engine.resolve())

        first, first_info = load_engine(roots[0])
        second, second_info = load_engine(roots[1])
        assert first()["marker"] == "first"
        assert second()["marker"] == "second"
        assert first_info["match_file"] != second_info["match_file"]
    finally:
        for name in list(sys.modules):
            if name == "sandbox" or name.startswith("sandbox."):
                sys.modules.pop(name, None)
        for root in roots:
            while str(root) in sys.path:
                sys.path.remove(str(root))


def test_cli_tools_fail_nonzero_when_external_prerequisites_are_missing(tmp_path, capsys):
    missing_engine = tmp_path / "missing-engine"
    assert benchmark.main(
        [
            "--all-templates",
            "--paired-seed-count",
            "2",
            "--engine-dir",
            str(missing_engine),
            "--output-dir",
            str(tmp_path / "bench"),
        ]
    ) == 3
    assert self_play.main(
        [
            "--opponent",
            "template",
            "--engine-dir",
            str(missing_engine),
            "--output-dir",
            str(tmp_path / "self"),
        ]
    ) == 3
    assert qualifier_replay.main(
        ["--history", str(tmp_path / "missing.json"), "--output-dir", str(tmp_path / "replay")]
    ) == 3
    assert "prerequisite failure" in capsys.readouterr().err
