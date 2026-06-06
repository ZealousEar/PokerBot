"""B8 single-command gauntlet for candidate submission zips.

The runner orchestrates existing verification tools as subprocesses, captures
their output under consult/artifacts, and emits a STATUS-style Markdown block.

Full profile defaults to the B8 promotion-scale command set. Smoke profile runs
the same sequence with reduced hand counts for fast harness verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT_DIR = ROOT / "consult" / "artifacts" / "2026-05-28-b8-runner"
PROTECTED_ARTIFACTS = (
    ROOT / "submissions" / "v_final.zip",
    ROOT / "submissions" / "best_green.zip",
)
PUBLIC_OPPONENT_ZIPS = {
    "famadeo": ROOT / "consult" / "artifacts" / "2026-05-28-public-saturation" / "opponent_zips" / "famadeo.zip",
    "dominic": ROOT / "consult" / "artifacts" / "2026-05-28-public-saturation" / "opponent_zips" / "dominic.zip",
    "neel": ROOT / "consult" / "artifacts" / "2026-05-28-public-saturation" / "opponent_zips" / "neel.zip",
    "vladimir": ROOT / "consult" / "artifacts" / "2026-05-28-public-saturation" / "opponent_zips" / "vladimir.zip",
}


@dataclass
class StepSpec:
    label: str
    command: list[str]
    kind: str
    requested_hands: int | None = None
    opponent: str | None = None
    base: int | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class StepResult:
    label: str
    command: list[str]
    kind: str
    returncode: int
    duration_s: float
    stdout_path: str | None
    stderr_path: str | None
    stdout_tail: str
    stderr_tail: str
    passed: bool
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_python() -> str:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return str(venv_python)
    return sys.executable


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _engine_head() -> str | None:
    engine = ROOT / "ext" / "fullhouse-engine"
    if not engine.exists():
        return None
    res = subprocess.run(
        ["git", "-C", str(engine), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    return res.stdout.strip() if res.returncode == 0 else None


def _artifact_hashes() -> dict[str, str | None]:
    return {_rel(path): _sha256(path) for path in PROTECTED_ARTIFACTS}


def _tail(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _run_raw(command: list[str], timeout_s: int | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )


def _help_supports(script: str, option: str, python: str) -> bool:
    try:
        res = _run_raw([python, script, "--help"], timeout_s=20)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return option in (res.stdout + res.stderr)


def _find_json_object(text: str) -> Any | None:
    decoder = json.JSONDecoder()
    starts = [idx for idx, char in enumerate(text) if char in "[{"]
    best_obj = None
    best_len = -1
    for start in reversed(starts):
        try:
            obj, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if end > best_len:
            best_obj = obj
            best_len = end
    return best_obj


def _parse_float(value: str) -> float:
    return float(value.replace("+", ""))


def _parse_metrics(kind: str, stdout: str, stderr: str) -> dict[str, Any]:
    combined = stdout + "\n" + stderr
    metrics: dict[str, Any] = {}

    if kind == "validator":
        metrics["validator_passed"] = "PASSED" in combined
        tests = re.findall(r"^\s*[✓x]\s+\[[^\]]+\]\s+([^:]+):", combined, flags=re.MULTILINE)
        if tests:
            metrics["validator_tests"] = tests
    elif kind == "import_audit":
        m = re.search(r"cold import:\s*([0-9.]+)s,\s*RSS:\s*([0-9.]+)\s*MB", combined)
        if m:
            metrics["cold_import_s"] = float(m.group(1))
            metrics["rss_mb"] = float(m.group(2))
    elif kind == "pytest":
        m = re.search(r"([0-9]+)\s+passed", combined)
        if m:
            metrics["tests_passed"] = int(m.group(1))
    elif kind == "smoke":
        payload = _find_json_object(stdout)
        if isinstance(payload, dict):
            metrics.update({
                "n_hands": payload.get("n_hands"),
                "expected_hands": payload.get("expected_hands"),
                "chip_delta": payload.get("chip_delta"),
                "errors": payload.get("errors"),
                "duration_s": payload.get("duration_s"),
            })
    elif kind == "audit_strategy_leakage":
        m = re.search(r"# zip sha256:\s*([0-9a-f]{64})", combined)
        if m:
            metrics["zip_sha256"] = m.group(1)
        metrics["leakage_passed"] = "audit_strategy_leakage PASS" in combined
    elif kind == "exploit_check":
        payload = _find_json_object(stdout)
        if isinstance(payload, dict):
            for key in ("preflop_mbb_g", "aggregate_mbb_g", "suite_size", "passed"):
                if key in payload:
                    metrics[key] = payload[key]
        m = re.search(r"LBR preflop=([0-9.+-]+).*aggregate=([0-9.+-]+).*over\s+([0-9]+)\s+spots", combined)
        if m:
            metrics["preflop_mbb_g"] = float(m.group(1))
            metrics["aggregate_mbb_g"] = float(m.group(2))
            metrics["suite_size"] = int(m.group(3))
    elif kind == "benchmark":
        payload = _find_json_object(stdout)
        if isinstance(payload, dict):
            metrics["json"] = payload
            if "gain_bb_per_100" in payload:
                metrics["gain_bb_per_100"] = payload.get("gain_bb_per_100")
            if "results" in payload:
                metrics["targets"] = [
                    {
                        "target": item.get("target"),
                        "bb_per_100": item.get("bb_per_100"),
                        "ci_low": item.get("ci_low"),
                        "ci_high": item.get("ci_high"),
                        "hands": item.get("hands"),
                    }
                    for item in payload.get("results", [])
                    if isinstance(item, dict)
                ]
        metrics["todo_output"] = "TODO" in combined
        lines = re.findall(
            r"benchmark\s+([^:]+):\s+bb/100=([+-]?[0-9.]+)\s+ci95=\[([+-]?[0-9.]+),\s*([+-]?[0-9.]+)\]\s+hands=([0-9]+)",
            combined,
        )
        if lines:
            metrics["benchmarks"] = [
                {
                    "target": target,
                    "bb_per_100": _parse_float(mean),
                    "ci_low": _parse_float(lo),
                    "ci_high": _parse_float(hi),
                    "hands": int(hands),
                }
                for target, mean, lo, hi, hands in lines
            ]
    elif kind == "h2h":
        m_hands = re.search(r"hands played total:\s*([0-9]+)", combined)
        if m_hands:
            metrics["hands_played_total"] = int(m_hands.group(1))
        m_match = re.search(
            r"per-match BB delta:\s*([+-]?[0-9.]+)\s+\(95% CI \[([+-]?[0-9.]+),\s*([+-]?[0-9.]+)\]\)",
            combined,
        )
        if m_match:
            metrics["mean_match_bb"] = _parse_float(m_match.group(1))
            metrics["ci_low_match_bb"] = _parse_float(m_match.group(2))
            metrics["ci_high_match_bb"] = _parse_float(m_match.group(3))
        m_bb100 = re.search(r"\s[a-zA-Z0-9_.-]+\s+bb/100:\s*([+-]?[0-9.]+)", combined)
        if m_bb100:
            metrics["bb_per_100"] = _parse_float(m_bb100.group(1))
        error_lines = re.findall(r"\s([a-zA-Z0-9_.-]+)\s+errors:\s*([0-9]+)", combined)
        if error_lines:
            metrics["errors"] = {label: int(count) for label, count in error_lines}
        verdict = re.search(r"verdict:\s*(.+)", combined)
        if verdict:
            metrics["verdict"] = verdict.group(1).strip()
    return metrics


def _semantic_pass(spec: StepSpec, result: StepResult, profile: str) -> tuple[bool, list[str]]:
    notes = list(result.notes)
    if result.returncode != 0:
        return False, notes

    if profile == "smoke":
        return True, notes

    if spec.kind == "benchmark" and result.metrics.get("todo_output"):
        notes.append("full profile rejects benchmark TODO output")
        return False, notes

    if spec.kind == "h2h":
        metrics = result.metrics
        requested = spec.requested_hands or 0
        if requested and requested < 20000:
            notes.append(f"requested_hands {requested} below B8 floor")
            return False, notes
        errors = metrics.get("errors") or {}
        if any(int(v) > 0 for v in errors.values()):
            notes.append(f"h2h bot errors present: {errors}")
            return False, notes
        if spec.opponent == "famadeo":
            if requested < 30000:
                notes.append(f"famadeo requested_hands {requested} below 30000")
                return False, notes
            bb100 = metrics.get("bb_per_100")
            ci_low = metrics.get("ci_low_match_bb")
            if bb100 is None or ci_low is None:
                notes.append("famadeo h2h metrics were not parsed")
                return False, notes
            if bb100 < 15.0 or ci_low <= 0.0:
                notes.append("famadeo gate requires bb/100 >= +15 and paired CI low > 0")
                return False, notes
        elif spec.opponent in {"dominic", "neel", "vladimir"}:
            mean = metrics.get("mean_match_bb")
            hi = metrics.get("ci_high_match_bb")
            if mean is None or hi is None:
                notes.append(f"{spec.opponent} regression metrics were not parsed")
                return False, notes
            if mean < 0.0 and hi < 0.0:
                notes.append(f"{spec.opponent} regression gate found a statistically negative h2h")
                return False, notes
    return True, notes


def _run_step(spec: StepSpec, report_dir: Path, timeout_s: int | None, profile: str) -> StepResult:
    logs_dir = report_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = logs_dir / f"{spec.label}.stdout.log"
    stderr_path = logs_dir / f"{spec.label}.stderr.log"

    start = time.monotonic()
    stdout = ""
    stderr = ""
    returncode = 0
    notes = list(spec.notes)
    if not spec.command:
        returncode = 127
        stderr = "No command generated for this step."
    else:
        try:
            res = _run_raw(spec.command, timeout_s=timeout_s)
            returncode = res.returncode
            stdout = res.stdout
            stderr = res.stderr
        except subprocess.TimeoutExpired as e:
            returncode = 124
            stdout = e.stdout or ""
            stderr = (e.stderr or "") + f"\nTIMEOUT after {timeout_s}s"
    duration_s = round(time.monotonic() - start, 3)
    _write_text(stdout_path, stdout)
    _write_text(stderr_path, stderr)
    metrics = _parse_metrics(spec.kind, stdout, stderr)
    provisional = StepResult(
        label=spec.label,
        command=spec.command,
        kind=spec.kind,
        returncode=returncode,
        duration_s=duration_s,
        stdout_path=_rel(stdout_path),
        stderr_path=_rel(stderr_path),
        stdout_tail=_tail(stdout),
        stderr_tail=_tail(stderr),
        passed=returncode == 0,
        metrics=metrics,
        notes=notes,
    )
    passed, semantic_notes = _semantic_pass(spec, provisional, profile)
    provisional.passed = passed
    provisional.notes = semantic_notes
    return provisional


def _candidate_arg(path: Path) -> str:
    return _rel(path)


def _benchmark_command(python: str, candidate: Path, mode: str, hands: int, paired_base: int = 42) -> tuple[list[str], list[str]]:
    notes: list[str] = []
    command = [python, "tools/benchmark.py"]
    if mode == "all_templates":
        command.append("--all-templates")
    elif mode == "ablate_overlay":
        command.append("--ablate-overlay")
    elif mode == "self_play_vs_prior":
        command.extend(["--self-play", "--vs-prior"])
    else:
        raise ValueError(mode)
    command.extend(["--hands", str(hands), "--paired-seed-base", str(paired_base)])
    if _help_supports("tools/benchmark.py", "--bot", python):
        command.extend(["--bot", _candidate_arg(candidate)])
    else:
        notes.append("tools/benchmark.py does not expose --bot in this checkout; command is not artifact-bound")
    return command, notes


def _exploit_command(python: str, candidate: Path) -> tuple[list[str], list[str]]:
    command = [python, "tools/exploit_check.py"]
    notes: list[str] = []
    if _help_supports("tools/exploit_check.py", "--bot", python):
        command.extend(["--bot", _candidate_arg(candidate)])
    elif _help_supports("tools/exploit_check.py", "--zip", python):
        command.extend(["--zip", _candidate_arg(candidate)])
    else:
        notes.append("tools/exploit_check.py does not expose --bot/--zip in this checkout; command is not artifact-bound")
    return command, notes


def _opponent_path(name: str) -> Path | None:
    candidate = PUBLIC_OPPONENT_ZIPS[name]
    if candidate.is_file():
        return candidate
    fallback_dirs = {
        "famadeo": ROOT / "ext" / "public-bots" / "famadeo" / "bots" / "codex_holdem",
        "dominic": ROOT / "ext" / "public-bots" / "dominic" / "bots" / "dominic",
        "neel": ROOT / "ext" / "public-bots" / "neel" / "bots" / "neel",
        "vladimir": ROOT / "ext" / "public-bots" / "vladimir" / "bots" / "vlad",
    }
    fallback = fallback_dirs[name]
    return fallback if fallback.exists() else None


def _h2h_step(python: str, candidate: Path, opponent: str, base: int, hands: int, match_len: int) -> StepSpec:
    opponent_path = _opponent_path(opponent)
    label = f"h2h_{opponent}_b{base}"
    if opponent_path is None:
        return StepSpec(
            label=label,
            command=[],
            kind="h2h",
            requested_hands=hands,
            opponent=opponent,
            base=base,
            notes=[f"opponent artifact not found for {opponent}"],
        )
    command = [
        python,
        "tools/h2h.py",
        "--bot-a",
        _candidate_arg(candidate),
        "--bot-b",
        _rel(opponent_path),
        "--hands",
        str(hands),
        "--paired-seed-base",
        str(base),
        "--match-len",
        str(match_len),
        "--label-a",
        candidate.stem,
        "--label-b",
        opponent,
    ]
    return StepSpec(
        label=label,
        command=command,
        kind="h2h",
        requested_hands=hands,
        opponent=opponent,
        base=base,
    )


def _build_steps(args: argparse.Namespace, candidate: Path) -> list[StepSpec]:
    python = args.python
    if args.profile == "full":
        smoke_hands = 200
        bench_hands = 10000
        famadeo_hands = 30000
        regression_hands = 20000
        match_len = 200
    else:
        smoke_hands = args.smoke_hands
        bench_hands = args.smoke_benchmark_hands
        famadeo_hands = args.smoke_h2h_hands
        regression_hands = args.smoke_h2h_hands
        match_len = args.smoke_match_len

    steps = [
        StepSpec(
            label="validator",
            command=[python, "ext/fullhouse-engine/sandbox/validator.py", _candidate_arg(candidate)],
            kind="validator",
        ),
        StepSpec(
            label="import_audit",
            command=[python, "tools/import_audit.py", "--max-seconds", "1.5", "--max-mb", "400"],
            kind="import_audit",
        ),
        StepSpec(
            label="edge_cases",
            command=[python, "-m", "pytest", "tests/edge_cases", "-x"],
            kind="pytest",
        ),
        StepSpec(
            label="smoke",
            command=[python, "tools/smoke_run.py", "--zip", _candidate_arg(candidate), "--hands", str(smoke_hands)],
            kind="smoke",
            requested_hands=smoke_hands,
        ),
        StepSpec(
            label="audit_strategy_leakage",
            command=[python, "tools/audit_strategy_leakage.py", "--zip", _candidate_arg(candidate)],
            kind="audit_strategy_leakage",
        ),
    ]

    exploit_command, exploit_notes = _exploit_command(python, candidate)
    steps.append(StepSpec(label="exploit_check", command=exploit_command, kind="exploit_check", notes=exploit_notes))

    for label, mode in (
        ("benchmark_all_templates", "all_templates"),
        ("benchmark_ablate_overlay", "ablate_overlay"),
        ("benchmark_self_play_vs_prior", "self_play_vs_prior"),
    ):
        command, notes = _benchmark_command(python, candidate, mode, bench_hands)
        steps.append(
            StepSpec(
                label=label,
                command=command,
                kind="benchmark",
                requested_hands=bench_hands,
                notes=notes,
            )
        )

    for base in (142, 242):
        steps.append(_h2h_step(python, candidate, "famadeo", base, famadeo_hands, match_len))
    for opponent in ("dominic", "neel", "vladimir"):
        steps.append(_h2h_step(python, candidate, opponent, 142, regression_hands, match_len))
    return steps


def _metric_summary(result: StepResult) -> str:
    m = result.metrics
    if result.kind == "import_audit" and "cold_import_s" in m:
        return f"cold_import={m['cold_import_s']:.3f}s rss={m['rss_mb']:.1f}MB"
    if result.kind == "pytest" and "tests_passed" in m:
        return f"{m['tests_passed']} tests passed"
    if result.kind == "smoke" and "n_hands" in m:
        return f"hands={m.get('n_hands')}/{m.get('expected_hands')} chip_delta={m.get('chip_delta')}"
    if result.kind == "exploit_check" and "aggregate_mbb_g" in m:
        return f"preflop={m.get('preflop_mbb_g')} aggregate={m.get('aggregate_mbb_g')} suite={m.get('suite_size')}"
    if result.kind == "benchmark":
        if "gain_bb_per_100" in m:
            return f"gain={m['gain_bb_per_100']:+.2f} bb/100"
        benches = m.get("benchmarks") or m.get("targets")
        if benches:
            parts = []
            for item in benches[:5]:
                target = item.get("target")
                bb = item.get("bb_per_100")
                parts.append(f"{target}={bb:+.2f}" if isinstance(bb, (int, float)) else str(target))
            return ", ".join(parts)
        if m.get("todo_output"):
            return "TODO output from underlying tool"
    if result.kind == "h2h":
        bb = m.get("bb_per_100")
        lo = m.get("ci_low_match_bb")
        hi = m.get("ci_high_match_bb")
        hands = m.get("hands_played_total")
        if bb is not None and lo is not None and hi is not None:
            return f"bb/100={bb:+.2f} match_ci=[{lo:+.2f},{hi:+.2f}] hands={hands}"
    if result.kind == "audit_strategy_leakage" and m.get("zip_sha256"):
        return f"zip_sha256={m['zip_sha256'][:12]}... leakage=PASS"
    if result.kind == "validator" and "validator_passed" in m:
        return "validator=PASSED" if m["validator_passed"] else "validator=not parsed as PASS"
    return "-"


def _status_block(
    started_at: str,
    profile: str,
    candidate: Path,
    candidate_sha: str,
    report_path: Path,
    results: list[StepResult],
    before_hashes: dict[str, str | None],
    after_hashes: dict[str, str | None],
    engine_before: str | None,
    engine_after: str | None,
) -> str:
    overall = "GREEN" if all(r.passed for r in results) and before_hashes == after_hashes and engine_before == engine_after else "RED"
    step_bits = " ".join(f"{r.label}={'PASS' if r.passed else 'FAIL'}" for r in results)
    h2h_bits = []
    for r in results:
        if r.kind == "h2h":
            bb = r.metrics.get("bb_per_100")
            if isinstance(bb, (int, float)):
                h2h_bits.append(f"{r.label}={bb:+.2f}")
            else:
                h2h_bits.append(f"{r.label}={'PASS' if r.passed else 'FAIL'}")
    benchmark_bits = []
    for r in results:
        if r.kind == "benchmark":
            benchmark_bits.append(f"{r.label}={'PASS' if r.passed else 'FAIL'} ({_metric_summary(r)})")
    changed_files = [
        "tools/b8_gauntlet.py",
        "tools/audit_strategy_leakage.py",
        _rel(report_path),
        "STATUS.md",
    ]
    lines = [
        f"## {started_at} · B8 runner {profile} · {overall}",
        f"- Goal: single-command B8 gauntlet runner against `{_candidate_arg(candidate)}`.",
        f"- Candidate: `{_candidate_arg(candidate)}` sha256 `{candidate_sha}`.",
        f"- Proof: {step_bits}",
        f"- Benchmarks: {'; '.join(benchmark_bits) if benchmark_bits else 'N/A'}",
        f"- Public h2h: {'; '.join(h2h_bits) if h2h_bits else 'N/A'}",
        f"- Guardrails: protected artifact hashes before={before_hashes} after={after_hashes}; ext/fullhouse-engine before={engine_before} after={engine_after}.",
        f"- Report: `{_rel(report_path)}`.",
        f"- Files changed: {', '.join(f'`{item}`' for item in changed_files)}.",
        "- Corpus citations: [[Engine-Fullhouse]], [[Libratus-Brown-Sandholm-2017]], [[Pluribus-Brown-Sandholm-2019]].",
        "- Next action: use full profile for promotion-scale B8 acceptance; keep qualifier artifact unchanged unless a full GREEN report supports promotion.",
        "",
        f"[B8 RUNNER {overall} {started_at} profile={profile} candidate={candidate.stem}]",
        f"artifact={_candidate_arg(candidate)} sha256={candidate_sha}",
        step_bits,
    ]
    return "\n".join(lines)


def _report_markdown(
    status_block: str,
    profile: str,
    candidate: Path,
    candidate_sha: str,
    results: list[StepResult],
    before_hashes: dict[str, str | None],
    after_hashes: dict[str, str | None],
    engine_before: str | None,
    engine_after: str | None,
) -> str:
    lines = [
        f"# B8 Gauntlet Report - {candidate.stem}",
        "",
        status_block,
        "",
        "## Configuration",
        "",
        f"- profile: `{profile}`",
        f"- candidate: `{_candidate_arg(candidate)}`",
        f"- candidate_sha256: `{candidate_sha}`",
        f"- protected_hashes_before: `{before_hashes}`",
        f"- protected_hashes_after: `{after_hashes}`",
        f"- ext_fullhouse_engine_before: `{engine_before}`",
        f"- ext_fullhouse_engine_after: `{engine_after}`",
        "",
        "## Step Summary",
        "",
        "| step | result | rc | seconds | metrics |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for result in results:
        lines.append(
            f"| `{result.label}` | {'PASS' if result.passed else 'FAIL'} | "
            f"{result.returncode} | {result.duration_s:.3f} | {_metric_summary(result)} |"
        )
    lines.extend(["", "## Commands", ""])
    for result in results:
        lines.extend(
            [
                f"### {result.label}",
                "",
                "```bash",
                " ".join(result.command) if result.command else "<no command>",
                "```",
                "",
                f"- stdout: `{result.stdout_path}`",
                f"- stderr: `{result.stderr_path}`",
            ]
        )
        if result.notes:
            lines.append(f"- notes: {'; '.join(result.notes)}")
        lines.append("")
    lines.extend(["## Parsed Results", "", "```json"])
    lines.append(
        json.dumps(
            [
                {
                    "label": r.label,
                    "passed": r.passed,
                    "returncode": r.returncode,
                    "duration_s": r.duration_s,
                    "metrics": r.metrics,
                    "notes": r.notes,
                }
                for r in results
            ],
            indent=2,
            sort_keys=True,
        )
    )
    lines.extend(["```", ""])
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True, type=Path, help="Candidate submission zip to verify")
    p.add_argument("--profile", choices=("full", "smoke"), default="full")
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--append-status", action="store_true")
    p.add_argument("--python", default=_default_python())
    p.add_argument("--timeout-seconds", type=int, default=0, help="Per-step timeout; 0 disables")
    p.add_argument("--smoke-hands", type=int, default=50)
    p.add_argument("--smoke-benchmark-hands", type=int, default=200)
    p.add_argument("--smoke-h2h-hands", type=int, default=200)
    p.add_argument("--smoke-match-len", type=int, default=100)
    args = p.parse_args()

    candidate = args.candidate
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    candidate = candidate.resolve()
    if not candidate.is_file():
        print(f"FAIL: candidate zip not found: {candidate}", file=sys.stderr)
        return 2
    if candidate.suffix != ".zip":
        print(f"FAIL: candidate must be a .zip: {candidate}", file=sys.stderr)
        return 2

    report_path = args.report
    if report_path is None:
        suffix = "smoke_report" if args.profile == "smoke" else "report"
        report_path = DEFAULT_REPORT_DIR / f"{candidate.stem}_{suffix}.md"
    elif not report_path.is_absolute():
        report_path = ROOT / report_path
    report_path = report_path.resolve()
    report_dir = report_path.parent
    report_dir.mkdir(parents=True, exist_ok=True)

    started_at = _utc_now()
    before_hashes = _artifact_hashes()
    engine_before = _engine_head()
    candidate_sha = _sha256(candidate)
    if candidate_sha is None:
        print(f"FAIL: cannot hash candidate: {candidate}", file=sys.stderr)
        return 2

    timeout_s = args.timeout_seconds or None
    specs = _build_steps(args, candidate)
    results: list[StepResult] = []
    for spec in specs:
        print(f"[b8] running {spec.label}: {' '.join(spec.command) if spec.command else '<no command>'}", flush=True)
        result = _run_step(spec, report_dir, timeout_s, args.profile)
        results.append(result)
        print(f"[b8] {spec.label}: {'PASS' if result.passed else 'FAIL'} rc={result.returncode} t={result.duration_s:.1f}s", flush=True)

    after_hashes = _artifact_hashes()
    engine_after = _engine_head()
    status_block = _status_block(
        started_at,
        args.profile,
        candidate,
        candidate_sha,
        report_path,
        results,
        before_hashes,
        after_hashes,
        engine_before,
        engine_after,
    )
    report = _report_markdown(
        status_block,
        args.profile,
        candidate,
        candidate_sha,
        results,
        before_hashes,
        after_hashes,
        engine_before,
        engine_after,
    )
    _write_text(report_path, report)
    _write_text(report_dir / "results.json", json.dumps([r.__dict__ for r in results], indent=2, sort_keys=True))

    if args.append_status:
        status_path = ROOT / "STATUS.md"
        with status_path.open("a") as f:
            f.write("\n\n")
            f.write(status_block)
            f.write("\n")

    print(status_block)
    print(f"\n[b8] report: {_rel(report_path)}")

    if before_hashes != after_hashes:
        print("[b8] FAIL: protected submission hashes changed", file=sys.stderr)
        return 1
    if engine_before != engine_after:
        print("[b8] FAIL: ext/fullhouse-engine HEAD changed", file=sys.stderr)
        return 1
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
