"""Reproducible six-max evaluation primitives for the Fullhouse engine.

The official engine is a separate checkout under ``ext/fullhouse-engine``.
This module contains no poker simulation of its own: it validates and loads the
official ``sandbox.match.run_match`` entry point, schedules tournament-shaped
six-player matches, and preserves the engine's raw output.

Two experimental designs are supported:

``replacement``
    Evaluate one bot, or compare two bots, in the same seat against the same
    five-opponent lineup using common random seeds.  Rotating the focal seat
    through all six seats removes a fixed-seat advantage.

``head_to_head``
    Put three copies of each bot at one six-max table.  A six-rotation schedule
    swaps the candidates through every seat.  This is used for snapshot
    ratchets, not for reference-opponent benchmarking.

The raw JSONL is written after every engine call.  Bootstrap intervals resample
seed clusters (rather than pretending the six seat rotations are independent).
"""
from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import platform
import random
import subprocess
import sys
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
SCHEMA_VERSION = "fullhouse-evaluation-v1"
SIX_MAX_SEATS = 6
QUALIFIER_HANDS = 400
FINALS_HANDS = 800
DEFAULT_BIG_BLIND = 100
DEFAULT_BOOTSTRAP_SAMPLES = 10_000


class EvaluationError(RuntimeError):
    """Base class for a failed or invalid evaluation."""


class PrerequisiteError(EvaluationError):
    """An external input, artifact, or engine checkout is absent."""


class MatchFailure(EvaluationError):
    """The engine ran but returned an unusable or error-bearing result."""


@dataclass(frozen=True)
class BotArtifact:
    label: str
    path: Path


@dataclass(frozen=True)
class EvaluationConfig:
    hands: int
    seeds: tuple[int, ...]
    rotations: tuple[int, ...] = tuple(range(SIX_MAX_SEATS))
    big_blind: int = DEFAULT_BIG_BLIND
    bootstrap_samples: int = DEFAULT_BOOTSTRAP_SAMPLES
    bootstrap_seed: int = 20260601
    strict_errors: bool = True
    design: str = "replacement"

    def validate(self) -> None:
        if self.hands <= 0:
            raise EvaluationError("hands must be positive")
        if not self.seeds:
            raise EvaluationError("at least one seed is required")
        if self.big_blind <= 0:
            raise EvaluationError("big_blind must be positive")
        if self.bootstrap_samples < 0:
            raise EvaluationError("bootstrap_samples cannot be negative")
        if self.design not in {"replacement", "head_to_head"}:
            raise EvaluationError(f"unknown design: {self.design}")
        if not self.rotations:
            raise EvaluationError("at least one seat rotation is required")
        invalid = [seat for seat in self.rotations if seat not in range(SIX_MAX_SEATS)]
        if invalid:
            raise EvaluationError(f"seat rotations must be 0..5, got {invalid}")


RunMatch = Callable[..., Mapping[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, set):
        return sorted(value)
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=_json_default,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(payload, sort_keys=True, default=_json_default, allow_nan=False)
            + "\n"
        )
        handle.flush()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_digest(path: Path) -> str:
    """Hash a file or a directory tree without relying on git metadata."""
    path = path.resolve()
    if path.is_file():
        return sha256_file(path)
    if not path.is_dir():
        raise PrerequisiteError(f"bot artifact does not exist: {path}")
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise PrerequisiteError(f"bot artifact directory is empty: {path}")
    for item in files:
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(bytes.fromhex(sha256_file(item)))
    return digest.hexdigest()


def validate_artifact(artifact: BotArtifact) -> BotArtifact:
    path = artifact.path.expanduser().resolve()
    if not (path.is_file() or path.is_dir()):
        raise PrerequisiteError(f"missing {artifact.label} bot artifact: {path}")
    if path.is_file() and path.suffix not in {".py", ".zip"}:
        raise PrerequisiteError(
            f"{artifact.label} artifact must be a .py, .zip, or directory: {path}"
        )
    return BotArtifact(artifact.label, path)


def git_provenance(root: Path = ROOT) -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args], cwd=root, text=True, capture_output=True, timeout=5
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    commit = run("rev-parse", "HEAD")
    status = run("status", "--porcelain", "--untracked-files=no")
    return {
        "commit": commit,
        "tracked_worktree_dirty": bool(status) if status is not None else None,
    }


def load_engine(engine_dir: Path = DEFAULT_ENGINE_DIR) -> tuple[RunMatch, dict[str, Any]]:
    """Load the official engine's public match function.

    ``sandbox.match`` imports sibling modules by package name, so the engine
    root is placed on ``sys.path``.  A conflicting previously imported sandbox
    is rejected rather than silently running the wrong engine.
    """
    engine_dir = engine_dir.expanduser().resolve()
    runner = engine_dir / "sandbox" / "runner.py"
    match_file = engine_dir / "sandbox" / "match.py"
    if not runner.is_file() or not match_file.is_file():
        raise PrerequisiteError(
            "official engine checkout is incomplete; expected "
            f"{runner} and {match_file}"
        )

    loaded = sys.modules.get("sandbox.match")
    loaded_path = (
        Path(getattr(loaded, "__file__", "")).resolve() if loaded is not None else None
    )
    if loaded is not None and loaded_path == match_file:
        module = loaded
    else:
        # Test suites and orchestration processes may evaluate more than one
        # engine checkout in sequence. sandbox.match imports ``engine.game`` by
        # an absolute package name, so both package trees must be evicted before
        # switching roots. Existing module objects held by callers keep working.
        loaded_game = sys.modules.get("engine.game")
        loaded_game_path = (
            Path(getattr(loaded_game, "__file__", "")).resolve()
            if loaded_game is not None
            else None
        )
        game_file = engine_dir / "engine" / "game.py"
        if loaded is not None or (
            loaded_game_path is not None and loaded_game_path != game_file
        ):
            for module_name in list(sys.modules):
                if (
                    module_name == "sandbox"
                    or module_name.startswith("sandbox.")
                    or module_name == "engine"
                    or module_name.startswith("engine.")
                ):
                    sys.modules.pop(module_name, None)
        if str(engine_dir) in sys.path:
            sys.path.remove(str(engine_dir))
        sys.path.insert(0, str(engine_dir))
        importlib.invalidate_caches()
        try:
            module = importlib.import_module("sandbox.match")
        except Exception as exc:  # pragma: no cover - exact engine import varies
            raise PrerequisiteError(f"could not import official engine: {exc}") from exc
        imported_path = Path(getattr(module, "__file__", "")).resolve()
        if imported_path != match_file:
            raise PrerequisiteError(
                f"imported sandbox.match from {imported_path}, expected {match_file}"
            )

    run_match = getattr(module, "run_match", None)
    if not callable(run_match):
        raise PrerequisiteError(f"{match_file} does not expose callable run_match")
    return run_match, {
        "engine_dir": str(engine_dir),
        "match_file": str(match_file),
        "match_sha256": sha256_file(match_file),
        "runner_sha256": sha256_file(runner),
        "git": git_provenance(engine_dir) if (engine_dir / ".git").exists() else None,
    }


def resolve_reference_bot(engine_dir: Path, name: str) -> BotArtifact:
    if not name or Path(name).name != name:
        raise PrerequisiteError(f"invalid reference opponent name: {name!r}")
    path = engine_dir.expanduser().resolve() / "bots" / name
    if not path.is_dir():
        raise PrerequisiteError(f"missing reference opponent {name}: {path}")
    return BotArtifact(name, path)


def make_replacement_lineup(
    focal: BotArtifact,
    opponents: Sequence[BotArtifact],
    focal_seat: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    if len(opponents) != SIX_MAX_SEATS - 1:
        raise EvaluationError(
            f"replacement design requires exactly five opponents, got {len(opponents)}"
        )
    if focal_seat not in range(SIX_MAX_SEATS):
        raise EvaluationError(f"focal seat must be 0..5, got {focal_seat}")
    # Rotate the entire base lineup rather than merely inserting the focal bot
    # at a new index.  This sends every participant through all six seats while
    # preserving the same relative table order.
    by_seat: dict[int, tuple[str, BotArtifact]] = {focal_seat: ("hero", focal)}
    for index, opponent in enumerate(opponents):
        seat = (focal_seat + index + 1) % SIX_MAX_SEATS
        by_seat[seat] = (f"opponent_{index}_{opponent.label}", opponent)
    slots = [by_seat[seat] for seat in range(SIX_MAX_SEATS)]
    paths = {bot_id: str(artifact.path) for bot_id, artifact in slots}
    return paths, {
        "focal_ids": ["hero"],
        "opposing_ids": [bot_id for bot_id, _ in slots if bot_id != "hero"],
        "seats": [
            {"seat": seat, "bot_id": bot_id, "artifact": artifact.label}
            for seat, (bot_id, artifact) in enumerate(slots)
        ],
    }


def make_head_to_head_lineup(
    candidate: BotArtifact,
    baseline: BotArtifact,
    rotation: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Create a 3-v-3 table; rotations swap each bot through every seat."""
    if rotation not in range(SIX_MAX_SEATS):
        raise EvaluationError(f"rotation must be 0..5, got {rotation}")
    candidate_seats = {(rotation + offset) % SIX_MAX_SEATS for offset in range(3)}
    slots: list[tuple[str, BotArtifact]] = []
    candidate_index = 0
    baseline_index = 0
    for seat in range(SIX_MAX_SEATS):
        if seat in candidate_seats:
            slots.append((f"candidate_{candidate_index}", candidate))
            candidate_index += 1
        else:
            slots.append((f"baseline_{baseline_index}", baseline))
            baseline_index += 1
    paths = {bot_id: str(artifact.path) for bot_id, artifact in slots}
    return paths, {
        "focal_ids": [bot_id for bot_id, _ in slots if bot_id.startswith("candidate_")],
        "opposing_ids": [bot_id for bot_id, _ in slots if bot_id.startswith("baseline_")],
        "seats": [
            {"seat": seat, "bot_id": bot_id, "artifact": artifact.label}
            for seat, (bot_id, artifact) in enumerate(slots)
        ],
    }


def _as_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MatchFailure(f"engine result {label} must be numeric, got {value!r}")
    number = float(value)
    if not math.isfinite(number):
        raise MatchFailure(f"engine result {label} is not finite: {value!r}")
    return number


def _score_result(
    result: Mapping[str, Any],
    metadata: Mapping[str, Any],
    config: EvaluationConfig,
) -> dict[str, Any]:
    if not isinstance(result, Mapping):
        raise MatchFailure(f"run_match returned {type(result).__name__}, expected mapping")
    n_hands_raw = result.get("n_hands")
    if isinstance(n_hands_raw, bool) or not isinstance(n_hands_raw, int) or n_hands_raw <= 0:
        raise MatchFailure(f"engine returned invalid n_hands: {n_hands_raw!r}")
    chip_delta = result.get("chip_delta")
    if not isinstance(chip_delta, Mapping):
        raise MatchFailure("engine result is missing chip_delta mapping")

    focal_ids = list(metadata["focal_ids"])
    missing = [bot_id for bot_id in focal_ids if bot_id not in chip_delta]
    if missing:
        raise MatchFailure(f"engine result chip_delta is missing focal ids: {missing}")
    focal_total = sum(_as_number(chip_delta[bot_id], f"chip_delta[{bot_id}]") for bot_id in focal_ids)
    focal_score = focal_total / len(focal_ids)

    error_map = result.get("bot_errors", {})
    if error_map is None:
        error_map = {}
    if not isinstance(error_map, Mapping):
        raise MatchFailure("engine result bot_errors must be a mapping")
    nonempty_errors = {str(bot_id): value for bot_id, value in error_map.items() if value}
    if config.strict_errors and nonempty_errors:
        raise MatchFailure(f"engine reported bot errors: {nonempty_errors}")

    # Scheduled-hand normalization preserves the tournament cost of busting
    # early.  Actual-hand normalization is included as a diagnostic only.
    scheduled_bb100 = focal_score / config.big_blind * 100.0 / config.hands
    actual_bb100 = focal_score / config.big_blind * 100.0 / n_hands_raw
    return {
        "actual_hands": n_hands_raw,
        "scheduled_hands": config.hands,
        "early_termination": n_hands_raw < config.hands,
        "focal_chip_delta": focal_score,
        "scheduled_bb_per_100": scheduled_bb100,
        "actual_bb_per_100": actual_bb100,
        "bot_errors": nonempty_errors,
    }


def percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise EvaluationError("cannot calculate a percentile of no values")
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    location = max(0.0, min(1.0, probability)) * (len(ordered) - 1)
    lower = math.floor(location)
    upper = math.ceil(location)
    if lower == upper:
        return ordered[lower]
    weight = location - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def clustered_bootstrap_ci(
    values_by_seed: Mapping[int, Sequence[float]],
    *,
    samples: int,
    rng_seed: int,
    confidence: float = 0.95,
) -> dict[str, Any]:
    clusters = [tuple(float(value) for value in values) for _, values in sorted(values_by_seed.items())]
    if not clusters or any(not cluster for cluster in clusters):
        raise EvaluationError("bootstrap requires at least one value in every seed cluster")
    cluster_means = [sum(cluster) / len(cluster) for cluster in clusters]
    estimate = sum(cluster_means) / len(cluster_means)
    if samples == 0 or len(clusters) == 1:
        return {
            "estimate": estimate,
            "lower": estimate,
            "upper": estimate,
            "confidence": confidence,
            "bootstrap_samples": samples,
            "cluster_count": len(clusters),
            "method": "degenerate_seed_cluster_percentile",
        }
    rng = random.Random(rng_seed)
    simulated: list[float] = []
    for _ in range(samples):
        draw = [cluster_means[rng.randrange(len(cluster_means))] for _ in cluster_means]
        simulated.append(sum(draw) / len(draw))
    alpha = (1.0 - confidence) / 2.0
    return {
        "estimate": estimate,
        "lower": percentile(simulated, alpha),
        "upper": percentile(simulated, 1.0 - alpha),
        "confidence": confidence,
        "bootstrap_samples": samples,
        "cluster_count": len(clusters),
        "method": "seed_cluster_percentile",
    }


def _summarize_records(records: Sequence[Mapping[str, Any]], config: EvaluationConfig) -> dict[str, Any]:
    by_condition: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        by_condition.setdefault(str(record["condition"]), []).append(record)

    conditions: dict[str, Any] = {}
    for index, (condition, rows) in enumerate(sorted(by_condition.items())):
        bb_by_seed: dict[int, list[float]] = {}
        chips_by_seed: dict[int, list[float]] = {}
        for row in rows:
            seed = int(row["seed"])
            bb_by_seed.setdefault(seed, []).append(float(row["score"]["scheduled_bb_per_100"]))
            chips_by_seed.setdefault(seed, []).append(float(row["score"]["focal_chip_delta"]))
        conditions[condition] = {
            "match_count": len(rows),
            "seed_count": len(bb_by_seed),
            "seat_rotations": sorted({int(row["rotation"]) for row in rows}),
            "scheduled_hands": sum(int(row["score"]["scheduled_hands"]) for row in rows),
            "actual_hands": sum(int(row["score"]["actual_hands"]) for row in rows),
            "early_terminations": sum(bool(row["score"]["early_termination"]) for row in rows),
            "scheduled_bb_per_100_ci": clustered_bootstrap_ci(
                bb_by_seed,
                samples=config.bootstrap_samples,
                rng_seed=config.bootstrap_seed + index,
            ),
            "chip_delta_per_match_ci": clustered_bootstrap_ci(
                chips_by_seed,
                samples=config.bootstrap_samples,
                rng_seed=config.bootstrap_seed + 1000 + index,
            ),
        }

    comparison = None
    if {"candidate", "baseline"}.issubset(by_condition):
        candidate = {
            (int(row["seed"]), int(row["rotation"])): row for row in by_condition["candidate"]
        }
        baseline = {
            (int(row["seed"]), int(row["rotation"])): row for row in by_condition["baseline"]
        }
        if set(candidate) != set(baseline):
            raise MatchFailure("candidate and baseline runs do not form complete seed/seat pairs")
        delta_by_seed: dict[int, list[float]] = {}
        chip_delta_by_seed: dict[int, list[float]] = {}
        for key in sorted(candidate):
            seed, _ = key
            delta = (
                float(candidate[key]["score"]["scheduled_bb_per_100"])
                - float(baseline[key]["score"]["scheduled_bb_per_100"])
            )
            chip_delta = (
                float(candidate[key]["score"]["focal_chip_delta"])
                - float(baseline[key]["score"]["focal_chip_delta"])
            )
            delta_by_seed.setdefault(seed, []).append(delta)
            chip_delta_by_seed.setdefault(seed, []).append(chip_delta)
        comparison = {
            "pair_count": len(candidate),
            "seed_count": len(delta_by_seed),
            "candidate_minus_baseline_bb_per_100_ci": clustered_bootstrap_ci(
                delta_by_seed,
                samples=config.bootstrap_samples,
                rng_seed=config.bootstrap_seed + 2000,
            ),
            "candidate_minus_baseline_chip_delta_per_match_ci": clustered_bootstrap_ci(
                chip_delta_by_seed,
                samples=config.bootstrap_samples,
                rng_seed=config.bootstrap_seed + 3000,
            ),
        }
    return {"conditions": conditions, "paired_comparison": comparison}


def _manifest_base(
    output_dir: Path,
    config: EvaluationConfig,
    candidate: BotArtifact,
    baseline: BotArtifact | None,
    opponents: Sequence[BotArtifact],
    engine_provenance: Mapping[str, Any],
) -> dict[str, Any]:
    artifacts = [candidate, *opponents]
    if baseline is not None:
        artifacts.append(baseline)
    artifact_rows = []
    for artifact in artifacts:
        artifact_rows.append(
            {
                "label": artifact.label,
                "path": str(artifact.path),
                "sha256": artifact_digest(artifact.path),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "created_utc": utc_now(),
        "status": "running",
        "command": sys.argv,
        "cwd": str(Path.cwd()),
        "output_dir": str(output_dir),
        "python": {"version": platform.python_version(), "executable": sys.executable},
        "platform": platform.platform(),
        "git": git_provenance(),
        "engine": dict(engine_provenance),
        "config": asdict(config),
        "artifacts": artifact_rows,
        "outputs": {
            "manifest": "manifest.json",
            "raw_results": "raw_results.jsonl",
            "summary": "summary.json",
        },
    }


def evaluate(
    *,
    run_match: RunMatch,
    engine_provenance: Mapping[str, Any],
    candidate: BotArtifact,
    opponents: Sequence[BotArtifact],
    config: EvaluationConfig,
    output_dir: Path,
    baseline: BotArtifact | None = None,
    run_label: str = "benchmark",
) -> dict[str, Any]:
    """Execute a complete evaluation and return its summary payload."""
    config.validate()
    candidate = validate_artifact(candidate)
    baseline = validate_artifact(baseline) if baseline is not None else None
    opponents = tuple(validate_artifact(opponent) for opponent in opponents)
    if config.design == "replacement" and len(opponents) != 5:
        raise EvaluationError("replacement evaluation requires exactly five opponents")
    if config.design == "head_to_head":
        if baseline is None:
            raise EvaluationError("head_to_head evaluation requires a baseline")
        if opponents:
            raise EvaluationError("head_to_head evaluation does not accept external opponents")

    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    raw_path = output_dir / "raw_results.jsonl"
    summary_path = output_dir / "summary.json"
    if raw_path.exists():
        raise EvaluationError(f"refusing to overwrite existing raw results: {raw_path}")
    manifest = _manifest_base(
        output_dir, config, candidate, baseline, opponents, engine_provenance
    )
    manifest["run_label"] = run_label
    dump_json(manifest_path, manifest)

    records: list[dict[str, Any]] = []
    run_index = 0
    engine_calls = 0
    try:
        if config.design == "replacement":
            conditions = [("candidate", candidate)]
            if baseline is not None:
                conditions.append(("baseline", baseline))
            for seed in config.seeds:
                for rotation in config.rotations:
                    # Candidate and baseline are adjacent in the schedule, so
                    # each common-random-number pair is completed immediately.
                    for condition, focal in conditions:
                        paths, lineup = make_replacement_lineup(focal, opponents, rotation)
                        # Keep match/hand ids identical inside the pair. Bots
                        # and synthetic opponents may seed mixed actions or MC
                        # equity from hand_id; condition-specific ids would
                        # inject avoidable policy noise despite identical cards.
                        match_name = f"{run_label}_{seed}_seat{rotation}"
                        result = run_match(
                            match_name,
                            paths,
                            n_hands=config.hands,
                            verbose=False,
                            seed=seed,
                        )
                        engine_calls += 1
                        score = _score_result(result, lineup, config)
                        record = {
                            "schema_version": SCHEMA_VERSION,
                            "run_index": run_index,
                            "match_name": match_name,
                            "condition": condition,
                            "seed": seed,
                            "rotation": rotation,
                            "lineup": lineup,
                            "score": score,
                            "engine_result": result,
                        }
                        append_jsonl(raw_path, record)
                        records.append(record)
                        run_index += 1
        else:
            assert baseline is not None
            for seed in config.seeds:
                for rotation in config.rotations:
                    paths, lineup = make_head_to_head_lineup(candidate, baseline, rotation)
                    match_name = f"{run_label}_{seed}_rotation{rotation}"
                    result = run_match(
                        match_name,
                        paths,
                        n_hands=config.hands,
                        verbose=False,
                        seed=seed,
                    )
                    engine_calls += 1
                    candidate_score = _score_result(result, lineup, config)
                    inverse_lineup = {
                        **lineup,
                        "focal_ids": lineup["opposing_ids"],
                        "opposing_ids": lineup["focal_ids"],
                    }
                    baseline_score = _score_result(result, inverse_lineup, config)
                    for condition, score in (
                        ("candidate", candidate_score),
                        ("baseline", baseline_score),
                    ):
                        record = {
                            "schema_version": SCHEMA_VERSION,
                            "run_index": run_index,
                            "match_name": match_name,
                            "condition": condition,
                            "seed": seed,
                            "rotation": rotation,
                            "lineup": lineup,
                            "score": score,
                            # Store the raw result once; the baseline record
                            # points to its paired candidate record.
                            "engine_result": result if condition == "candidate" else None,
                            "engine_result_run_index": run_index if condition == "candidate" else run_index - 1,
                        }
                        append_jsonl(raw_path, record)
                        records.append(record)
                        run_index += 1

        summary = {
            "schema_version": SCHEMA_VERSION,
            "created_utc": utc_now(),
            "run_label": run_label,
            "design": config.design,
            "result": _summarize_records(records, config),
        }
        dump_json(summary_path, summary)
        manifest.update(
            {
                "status": "complete",
                "completed_utc": utc_now(),
                "engine_calls": engine_calls,
                "result_records": len(records),
            }
        )
        dump_json(manifest_path, manifest)
        return summary
    except Exception as exc:
        manifest.update(
            {
                "status": "failed",
                "completed_utc": utc_now(),
                "engine_calls_completed": engine_calls,
                "failure": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                },
            }
        )
        dump_json(manifest_path, manifest)
        if isinstance(exc, EvaluationError):
            raise
        raise MatchFailure(f"engine match failed: {exc}") from exc


def build_seed_schedule(base: int, count: int) -> tuple[int, ...]:
    if count <= 0:
        raise EvaluationError("paired seed count must be positive")
    return tuple(base + offset for offset in range(count))


def parse_rotations(value: str) -> tuple[int, ...]:
    if value == "all":
        return tuple(range(SIX_MAX_SEATS))
    try:
        seats = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise EvaluationError(f"invalid seat rotations: {value!r}") from exc
    if not seats:
        raise EvaluationError("seat rotations cannot be empty")
    if len(set(seats)) != len(seats):
        raise EvaluationError(f"seat rotations contain duplicates: {value!r}")
    invalid = [seat for seat in seats if seat not in range(SIX_MAX_SEATS)]
    if invalid:
        raise EvaluationError(f"seat rotations must be 0..5, got {invalid}")
    return seats


def default_output_dir(prefix: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ROOT / "evaluation_runs" / f"{stamp}-{prefix}"


def print_summary(summary: Mapping[str, Any]) -> None:
    """Emit one machine-readable JSON object to stdout."""
    print(json.dumps(summary, sort_keys=True, default=_json_default, allow_nan=False))
