"""Tournament-aligned six-max benchmark for Fullhouse submissions.

Examples::

    python tools/benchmark.py --all-templates --hands 800 \\
        --paired-seed-base 42 --paired-seed-count 10

    python tools/benchmark.py --all-templates --candidate candidate.zip \\
        --baseline incumbent.zip --paired-seed-base 42

    python tools/benchmark.py --self-play --vs-prior \\
        --paired-seed-base 42 --paired-seed-count 10

Every successful run writes ``manifest.json``, ``raw_results.jsonl`` and
``summary.json``. Candidate/baseline comparisons use identical seeds and
identical focal seats. Self-play snapshot comparisons use balanced 3-v-3
tables and rotate each side through every seat.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.evaluation import (
    DEFAULT_BOOTSTRAP_SAMPLES,
    DEFAULT_ENGINE_DIR,
    FINALS_HANDS,
    BotArtifact,
    EvaluationConfig,
    EvaluationError,
    MatchFailure,
    PrerequisiteError,
    build_seed_schedule,
    default_output_dir,
    dump_json,
    evaluate,
    load_engine,
    parse_rotations,
    print_summary,
    resolve_reference_bot,
)


TEMPLATES = ("template", "aggressor", "mathematician", "shark", "ref_bot_2")
BIASED_SUITE = (
    "pot_odds_threshold",
    "river_value_threshold",
    "tight_aggressive",
    "loose_aggressive",
    "adaptive_overfold_exploiter",
)
PRIOR_SNAPSHOTS = (
    "submissions/v0_wired.zip",
    "submissions/v1_blueprint.zip",
    "submissions/v2_postflop.zip",
    "submissions/v3_hardened.zip",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--opponent",
        action="append",
        metavar="NAME",
        help="Reference name; pass once for five copies, or five times for a mixed table",
    )
    mode.add_argument("--all-templates", action="store_true", help="One six-max table with all five reference bots")
    mode.add_argument("--ablate-overlay", action="store_true", help="Compare --candidate with required blueprint-only --baseline")
    mode.add_argument("--self-play", action="store_true", help="Run a balanced 3-v-3 candidate/baseline ratchet")
    parser.add_argument("--vs-prior", action="store_true", help="With --self-play, compare against all declared prior snapshots")
    parser.add_argument("--candidate", default="submissions/v_final.zip", help="Candidate .zip, .py, or directory")
    parser.add_argument("--baseline", help="Comparison artifact; required for ablation and direct self-play")
    parser.add_argument("--hands", type=int, default=FINALS_HANDS, help="Hands per match (finals default: 800)")
    parser.add_argument("--min-bb", type=float, default=None, help="Return 1 when the selected bb/100 gate statistic is below this value")
    parser.add_argument(
        "--gate-stat",
        choices=("lower", "estimate"),
        default="lower",
        help="CI statistic used by --min-bb (default: conservative lower bound)",
    )
    parser.add_argument("--paired-seed-base", type=int, default=42, help="First common-random-number seed (default: 42)")
    parser.add_argument("--paired-seed-count", type=int, default=10, help="Number of consecutive paired seeds (default: 10)")
    parser.add_argument("--rotations", default="all", help="Comma-separated focal seats or 'all' (default)")
    parser.add_argument("--big-blind", type=int, default=100)
    parser.add_argument("--bootstrap-samples", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES)
    parser.add_argument("--bootstrap-seed", type=int, default=20260601)
    parser.add_argument("--engine-dir", type=Path, default=DEFAULT_ENGINE_DIR)
    parser.add_argument("--output-dir", type=Path, help="Artifact directory; defaults to evaluation_runs/<timestamp>-benchmark")
    parser.add_argument("--allow-bot-errors", action="store_true", help="Record engine bot errors instead of failing the run")
    return parser


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def _reference_lineup(engine_dir: Path, names: Sequence[str]) -> list[BotArtifact]:
    if len(names) == 1:
        names = tuple(names) * 5
    if len(names) != 5:
        raise EvaluationError(f"six-max replacement benchmark needs one or five --opponent values, got {len(names)}")
    return [resolve_reference_bot(engine_dir, name) for name in names]


def _biased_lineup(output_dir: Path) -> list[BotArtifact]:
    from tools.synthetic_opponents import write_opponents

    paths = write_opponents(output_dir / "synthetic_opponents")
    missing = [name for name in BIASED_SUITE if name not in paths]
    if missing:
        raise PrerequisiteError(f"synthetic opponent generator is missing: {missing}")
    return [BotArtifact(name, Path(paths[name])) for name in BIASED_SUITE]


def _config(args: argparse.Namespace, design: str) -> EvaluationConfig:
    return EvaluationConfig(
        hands=args.hands,
        seeds=build_seed_schedule(args.paired_seed_base, args.paired_seed_count),
        rotations=parse_rotations(args.rotations),
        big_blind=args.big_blind,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
        strict_errors=not args.allow_bot_errors,
        design=design,
    )


def _gate_value(summary: dict[str, Any], args: argparse.Namespace) -> tuple[float, str]:
    result = summary["result"]
    comparison = result.get("paired_comparison")
    if comparison:
        ci = comparison["candidate_minus_baseline_bb_per_100_ci"]
        label = "candidate_minus_baseline_bb_per_100"
    else:
        ci = result["conditions"]["candidate"]["scheduled_bb_per_100_ci"]
        label = "candidate_scheduled_bb_per_100"
    return float(ci[args.gate_stat]), label + "_" + args.gate_stat


def _run_one(
    *,
    args: argparse.Namespace,
    run_match,
    engine_info: dict[str, Any],
    output_dir: Path,
    candidate: BotArtifact,
    baseline: BotArtifact | None,
    opponents: Sequence[BotArtifact],
    design: str,
    label: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = evaluate(
        run_match=run_match,
        engine_provenance=engine_info,
        candidate=candidate,
        baseline=baseline,
        opponents=opponents,
        config=_config(args, design),
        output_dir=output_dir,
        run_label=label,
    )
    gate_value, gate_label = _gate_value(summary, args)
    gate = {
        "label": gate_label,
        "value": gate_value,
        "minimum": args.min_bb,
        "passed": args.min_bb is None or gate_value >= args.min_bb,
    }
    return summary, gate


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.vs_prior and not args.self_play:
        parser.error("--vs-prior requires --self-play")
    if args.self_play and not args.vs_prior and not args.baseline:
        parser.error("direct --self-play requires --baseline or --vs-prior")
    if args.ablate_overlay and not args.baseline:
        parser.error("--ablate-overlay requires a blueprint-only --baseline artifact")
    if args.paired_seed_count < 2:
        parser.error("benchmarking requires at least two paired seeds for a non-degenerate CI")

    output_dir = (args.output_dir or default_output_dir("benchmark")).expanduser().resolve()
    try:
        run_match, engine_info = load_engine(args.engine_dir)
        candidate = BotArtifact("candidate", _resolve_path(args.candidate))

        if args.self_play and args.vs_prior:
            if args.baseline:
                raise EvaluationError("--baseline and --vs-prior are mutually exclusive")
            prior_paths = [_resolve_path(path) for path in PRIOR_SNAPSHOTS]
            missing = [str(path) for path in prior_paths if not path.is_file()]
            if missing:
                raise PrerequisiteError(
                    "self-play prior snapshots are missing; provide them at the declared paths: "
                    + ", ".join(missing)
                )
            runs = []
            passed = True
            for index, prior_path in enumerate(prior_paths):
                summary, gate = _run_one(
                    args=args,
                    run_match=run_match,
                    engine_info=engine_info,
                    output_dir=output_dir / f"prior-{index}-{prior_path.stem}",
                    candidate=candidate,
                    baseline=BotArtifact(prior_path.stem, prior_path),
                    opponents=(),
                    design="head_to_head",
                    label=f"self_play_{prior_path.stem}",
                )
                runs.append({"prior": str(prior_path), "summary": summary, "gate": gate})
                passed = passed and bool(gate["passed"])
            combined = {
                "schema_version": "fullhouse-benchmark-index-v1",
                "mode": "self_play_vs_prior",
                "runs": runs,
                "passed": passed,
            }
            dump_json(output_dir / "index.json", combined)
            print_summary(combined)
            return 0 if passed else 1

        baseline = BotArtifact("baseline", _resolve_path(args.baseline)) if args.baseline else None
        if args.self_play:
            opponents: Sequence[BotArtifact] = ()
            design = "head_to_head"
            label = "self_play"
        elif args.ablate_overlay:
            opponents = _biased_lineup(output_dir)
            design = "replacement"
            label = "overlay_ablation"
        elif args.all_templates:
            opponents = _reference_lineup(args.engine_dir, TEMPLATES)
            design = "replacement"
            label = "all_templates"
        else:
            opponents = _reference_lineup(args.engine_dir, args.opponent)
            design = "replacement"
            label = "reference_benchmark"

        summary, gate = _run_one(
            args=args,
            run_match=run_match,
            engine_info=engine_info,
            output_dir=output_dir,
            candidate=candidate,
            baseline=baseline,
            opponents=opponents,
            design=design,
            label=label,
        )
        payload = {"summary": summary, "gate": gate, "output_dir": str(output_dir)}
        print_summary(payload)
        if not gate["passed"]:
            print(
                f"benchmark gate failed: {gate['label']}={gate['value']:.6g} < {gate['minimum']}",
                file=sys.stderr,
            )
            return 1
        return 0
    except PrerequisiteError as exc:
        print(f"benchmark prerequisite failure: {exc}", file=sys.stderr)
        return 3
    except (EvaluationError, MatchFailure) as exc:
        print(f"benchmark failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
