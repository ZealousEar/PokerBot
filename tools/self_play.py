"""Run a reproducible six-max match schedule against a reference opponent.

The named opponent is instantiated in five seats. The hero and the ordered
opponent lineup are rotated together through all six seats, so every process
occupies every seat once per seed. Raw engine results, a provenance manifest,
and seed-clustered confidence intervals are always persisted on success.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.evaluation import (  # noqa: E402
    DEFAULT_BOOTSTRAP_SAMPLES,
    DEFAULT_ENGINE_DIR,
    QUALIFIER_HANDS,
    BotArtifact,
    EvaluationConfig,
    EvaluationError,
    MatchFailure,
    PrerequisiteError,
    build_seed_schedule,
    default_output_dir,
    evaluate,
    load_engine,
    parse_rotations,
    print_summary,
    resolve_reference_bot,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opponent", required=True, help="Name under ext/fullhouse-engine/bots/")
    parser.add_argument("--candidate", default="submissions/v_final.zip", help="Hero .zip, .py, or directory")
    parser.add_argument("--hands", type=int, default=QUALIFIER_HANDS, help="Hands per match (qualifier default: 400)")
    parser.add_argument("--seed", type=int, default=42, help="First deterministic seed")
    parser.add_argument("--seed-count", type=int, default=1, help="Number of consecutive seeds")
    parser.add_argument("--rotations", default="all", help="Comma-separated focal seats or 'all' (default)")
    parser.add_argument("--big-blind", type=int, default=100)
    parser.add_argument("--bootstrap-samples", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES)
    parser.add_argument("--bootstrap-seed", type=int, default=20260601)
    parser.add_argument("--engine-dir", type=Path, default=DEFAULT_ENGINE_DIR)
    parser.add_argument("--output-dir", type=Path, help="Artifact directory; defaults to evaluation_runs/<timestamp>-self-play")
    parser.add_argument("--strict", action="store_true", help="Compatibility flag; strict error handling is already the default")
    parser.add_argument("--allow-bot-errors", action="store_true", help="Record bot errors instead of failing")
    return parser


def _resolve_candidate(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = (args.output_dir or default_output_dir("self-play")).expanduser().resolve()
    try:
        run_match, engine_info = load_engine(args.engine_dir)
        opponent = resolve_reference_bot(args.engine_dir, args.opponent)
        config = EvaluationConfig(
            hands=args.hands,
            seeds=build_seed_schedule(args.seed, args.seed_count),
            rotations=parse_rotations(args.rotations),
            big_blind=args.big_blind,
            bootstrap_samples=args.bootstrap_samples,
            bootstrap_seed=args.bootstrap_seed,
            strict_errors=not args.allow_bot_errors,
            design="replacement",
        )
        summary = evaluate(
            run_match=run_match,
            engine_provenance=engine_info,
            candidate=BotArtifact("candidate", _resolve_candidate(args.candidate)),
            baseline=None,
            opponents=tuple(opponent for _ in range(5)),
            config=config,
            output_dir=output_dir,
            run_label=f"self_play_{args.opponent}",
        )
        print_summary({"summary": summary, "output_dir": str(output_dir)})
        return 0
    except PrerequisiteError as exc:
        print(f"self-play prerequisite failure: {exc}", file=sys.stderr)
        return 3
    except (EvaluationError, MatchFailure) as exc:
        print(f"self-play failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
