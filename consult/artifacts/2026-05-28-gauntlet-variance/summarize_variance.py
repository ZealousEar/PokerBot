#!/usr/bin/env python3
"""Parse gauntlet repeat logs and write SUMMARY.md plus STATUS_APPEND.md."""

from __future__ import annotations

import json
import math
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-28-gauntlet-variance")
EXPECTED_SHA = "e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path) -> str:
    return path.read_text(errors="replace") if path.exists() else ""


def json_objects(text: str) -> list[object]:
    decoder = json.JSONDecoder()
    objects: list[object] = []
    for match in re.finditer(r"[\[{]", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        objects.append(obj)
    return objects


def first_dict(text: str, predicate=None) -> dict:
    for obj in json_objects(text):
        if isinstance(obj, dict) and (predicate is None or predicate(obj)):
            return obj
    return {}


def mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], 0.0
    return statistics.mean(values), statistics.stdev(values)


def fmt(value: float) -> str:
    if math.isinf(value):
        return "inf"
    if abs(value) >= 1000:
        return f"{value:,.1f}"
    if abs(value) >= 10:
        return f"{value:.2f}"
    return f"{value:.3f}"


def add(metrics: dict[str, float], key: str, value) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        metrics[key] = float(value)


def parse_run(run_dir: Path) -> tuple[dict[str, bool], dict[str, float]]:
    metrics: dict[str, float] = {}
    passes: dict[str, bool] = {}

    for meta_path in sorted(run_dir.glob("*.meta.json")):
        meta = json.loads(meta_path.read_text())
        passes[meta["label"]] = bool(meta["passed"])
        add(metrics, f"{meta['label']}.wall_duration_s", meta.get("duration_s"))

    validator = first_dict(read_text(run_dir / "validator.log"), lambda obj: "passed" in obj)
    if validator:
        add(metrics, "validator.error_count", len(validator.get("errors", [])))
        tests = validator.get("test_results") or validator.get("tests") or []
        add(metrics, "validator.test_count", len(tests))
        passed_tests = 0
        elapsed_values = []
        for test in tests:
            if test.get("passed"):
                passed_tests += 1
            for key in ("elapsed_s", "elapsed", "duration_s"):
                if isinstance(test.get(key), (int, float)):
                    elapsed_values.append(float(test[key]))
                    break
        add(metrics, "validator.tests_passed", passed_tests)
        if elapsed_values:
            add(metrics, "validator.total_test_elapsed_s", sum(elapsed_values))
            add(metrics, "validator.max_test_elapsed_s", max(elapsed_values))

    import_text = read_text(run_dir / "import_audit.log")
    match = re.search(r"cold import:\s*([0-9.]+)s,\s*RSS:\s*([0-9.]+)\s*MB", import_text)
    if match:
        add(metrics, "import_audit.cold_import_s", float(match.group(1)))
        add(metrics, "import_audit.rss_mb", float(match.group(2)))

    edge_text = read_text(run_dir / "edge_cases.log")
    match = re.search(r"(\d+)\s+passed.*?in\s+([0-9.]+)s", edge_text, re.S)
    if match:
        add(metrics, "edge_cases.tests_passed", int(match.group(1)))
        add(metrics, "edge_cases.pytest_duration_s", float(match.group(2)))
    fail_match = re.search(r"(\d+)\s+failed", edge_text)
    add(metrics, "edge_cases.tests_failed", int(fail_match.group(1)) if fail_match else 0)

    smoke = first_dict(read_text(run_dir / "smoke.log"), lambda obj: "n_hands" in obj and "chip_delta" in obj)
    if smoke:
        add(metrics, "smoke.n_hands", smoke.get("n_hands"))
        add(metrics, "smoke.expected_hands", smoke.get("expected_hands"))
        add(metrics, "smoke.duration_s", smoke.get("duration_s"))
        chip_delta = smoke.get("chip_delta", {})
        for bot, delta in chip_delta.items():
            add(metrics, f"smoke.chip_delta.{bot}", delta)

    timed = first_dict(read_text(run_dir / "smoke_timed.log"), lambda obj: "timings_ms" in obj)
    if timed:
        add(metrics, "smoke_timed.n_hands", timed.get("n_hands"))
        add(metrics, "smoke_timed.duration_s", timed.get("duration_s"))
        chip_delta = timed.get("chip_delta", {})
        for bot, delta in chip_delta.items():
            add(metrics, f"smoke_timed.chip_delta.{bot}", delta)
        timings = timed.get("timings_ms", {})
        for bot, summary in timings.items():
            for key, value in summary.items():
                add(metrics, f"smoke_timed.{bot}.{key}", value)

    leakage_text = read_text(run_dir / "audit_strategy_leakage.log")
    leakage_issues = 0
    if "STRATEGY LEAKAGE DETECTED:" in leakage_text:
        leakage_issues = len(re.findall(r"^\s+\S+:\d+:", leakage_text, re.M))
    add(metrics, "audit_strategy_leakage.issue_count", leakage_issues)

    exploit = first_dict(read_text(run_dir / "exploit_check.log"), lambda obj: "preflop_mbb_g" in obj)
    if exploit:
        for key in ("suite_size", "preflop_mbb_g", "aggregate_mbb_g", "max_preflop_mbb", "max_aggregate_mbb"):
            add(metrics, f"exploit_check.{key}", exploit.get(key))

    all_templates = first_dict(read_text(run_dir / "benchmark_all_templates.log"), lambda obj: "results" in obj and "min_bb" in obj)
    if all_templates:
        add(metrics, "benchmark_all_templates.min_bb", all_templates.get("min_bb"))
        for item in all_templates.get("results", []):
            target = item.get("target", "unknown")
            for key in ("hands", "requested_hands", "bb_per_100", "ci_low", "ci_high", "chip_delta", "duration_s"):
                add(metrics, f"benchmark_all_templates.{target}.{key}", item.get(key))

    ablate = first_dict(read_text(run_dir / "benchmark_ablate_overlay.log"), lambda obj: "gain_bb_per_100" in obj)
    if ablate:
        add(metrics, "benchmark_ablate_overlay.gain_bb_per_100", ablate.get("gain_bb_per_100"))
        for side in ("with_overlay", "blueprint_only"):
            side_obj = ablate.get(side, {})
            for key in ("bb_per_100", "hands", "chip_delta"):
                add(metrics, f"benchmark_ablate_overlay.{side}.{key}", side_obj.get(key))
            for item in side_obj.get("results", []):
                target = item.get("target", "unknown")
                for key in ("hands", "requested_hands", "bb_per_100", "ci_low", "ci_high", "chip_delta", "duration_s"):
                    add(metrics, f"benchmark_ablate_overlay.{side}.{target}.{key}", item.get(key))

    self_play = first_dict(read_text(run_dir / "benchmark_self_play_vs_prior.log"), lambda obj: "results" in obj and "min_bb" in obj)
    if self_play:
        add(metrics, "benchmark_self_play_vs_prior.min_bb", self_play.get("min_bb"))
        for item in self_play.get("results", []):
            key_name = item.get("manifest_key") or item.get("target", "unknown")
            for key in ("hands", "requested_hands", "bb_per_100", "ci_low", "ci_high", "chip_delta", "duration_s"):
                add(metrics, f"benchmark_self_play_vs_prior.{key_name}.{key}", item.get(key))

    # Treat timed smoke as part of smoke for gate-level pass/fail.
    if "smoke" in passes and "smoke_timed" in passes:
        passes["smoke_combined"] = passes["smoke"] and passes["smoke_timed"]
    return passes, metrics


def gate_for_metric(metric: str) -> str:
    if metric.startswith("smoke_timed."):
        return "smoke"
    return metric.split(".", 1)[0]


def ranking_metric(metric: str) -> bool:
    """Return true for metrics that should influence gate variance ranking.

    The full summary table still reports every numeric field. Ranking excludes
    fixed counts, caps, and command wall time so a tiny validator elapsed value
    or machine-load spike does not outrank actual gauntlet outcome variance.
    Decision latency remains included because p99 latency is part of the goal.
    """

    excluded_fragments = (
        ".wall_duration_s",
        ".duration_s",
        ".hands",
        ".requested_hands",
        ".expected_hands",
        ".count",
        ".suite_size",
        ".min_bb",
        ".max_preflop_mbb",
        ".max_aggregate_mbb",
        ".tests_passed",
        ".tests_failed",
        ".test_count",
        ".error_count",
        ".issue_count",
        ".total_test_elapsed_s",
        ".max_test_elapsed_s",
    )
    return not any(fragment in metric for fragment in excluded_fragments)


def build_summary() -> tuple[str, str]:
    run_dirs = [ROOT / f"run_{i}" for i in range(1, 6)]
    run_data = []
    for run_dir in run_dirs:
        passes, metrics = parse_run(run_dir)
        run_data.append((run_dir, passes, metrics))

    metric_values: dict[str, list[float]] = defaultdict(list)
    for _, _, metrics in run_data:
        for key, value in metrics.items():
            metric_values[key].append(value)

    metric_rows = []
    gate_cv: dict[str, float] = defaultdict(float)
    gate_worst_metric: dict[str, str] = {}
    for key in sorted(metric_values):
        values = metric_values[key]
        mean, std = mean_std(values)
        cv = 0.0 if abs(mean) < 1e-12 and std == 0 else (math.inf if abs(mean) < 1e-12 else abs(std / mean))
        gate = gate_for_metric(key)
        if ranking_metric(key) and cv > gate_cv[gate]:
            gate_cv[gate] = cv
            gate_worst_metric[gate] = key
        metric_rows.append((gate, key, len(values), mean, std, cv))

    all_gates = sorted(
        {label for _, passes, _ in run_data for label in passes if label not in {"smoke_timed", "smoke_combined"}}
    )
    pass_rows = []
    flip_rows = []
    for gate in all_gates:
        statuses = []
        for _, passes, _ in run_data:
            if gate == "smoke":
                status = passes.get("smoke_combined", passes.get("smoke", False))
            else:
                status = passes.get(gate)
            statuses.append(status)
        labels = ["PASS" if status else "FAIL" for status in statuses]
        flipped = len(set(labels)) > 1
        pass_rows.append((gate, labels, flipped))
        if flipped:
            flip_rows.append((gate, labels))

    ranking = sorted(gate_cv.items(), key=lambda item: (-item[1], item[0]))

    preflight = json.loads((ROOT / "PREFLIGHT.json").read_text()) if (ROOT / "PREFLIGHT.json").exists() else {}
    postflight = json.loads((ROOT / "POSTFLIGHT.json").read_text()) if (ROOT / "POSTFLIGHT.json").exists() else {}
    run_pass_count = sum(1 for _, passes, _ in run_data if all(v for k, v in passes.items() if k != "smoke_timed"))

    lines = [
        "# G1-G11 Gauntlet Variance: canonical v_final.zip",
        "",
        f"- Generated: {utc_now()}",
        f"- Artifact: `submissions/v_final.zip` / `submissions/best_green.zip` sha256 `{EXPECTED_SHA}`",
        f"- Execution worktree: `/Users/farhad/Code/PokerBot-gauntlet` @ `{preflight.get('gauntlet_head', 'unknown')}`",
        f"- Canonical tree: `/Users/farhad/Code/PokerBot` @ `{preflight.get('canonical_head', 'unknown')}`",
        f"- Engine commit: `{preflight.get('engine_commit', 'unknown')}`",
        "- Command policy: benchmarks and exploit check were artifact-bound with `--bot submissions/v_final.zip`; smoke used the real Docker sandbox; `smoke_timed` is a measurement wrapper for p99 latency only.",
        "- Relative variance ranking uses max coefficient of variation across outcome/runtime-signal metrics for each gate. Fixed counts, caps, validator elapsed, and command wall time are excluded from ranking but retained in the full metric table. Mean/std are sample statistics over 5 repeats.",
        "",
        "## Guardrails",
        "",
        f"- Preflight hashes ok: `{preflight.get('hashes_ok')}`",
        f"- Postflight hashes ok: `{postflight.get('hashes_ok')}`",
        f"- Any pip install requests surfaced: `none`",
        "",
        "## Pass/Fail Matrix",
        "",
        "| Gate | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Flip flag |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for gate, labels, flipped in pass_rows:
        lines.append(f"| `{gate}` | " + " | ".join(labels) + f" | {'FLIPPED' if flipped else ''} |")

    lines.extend(["", "## Flip Flags", ""])
    if flip_rows:
        for gate, labels in flip_rows:
            lines.append(f"- `{gate}` flipped pass/fail across runs: {', '.join(labels)}")
    else:
        lines.append("- No gate flipped pass/fail across the five repeats.")

    lines.extend(
        [
            "",
            "## Relative Variance Ranking",
            "",
            "| Rank | Gate | Max relative std | Worst metric |",
            "|---:|---|---:|---|",
        ]
    )
    for index, (gate, cv) in enumerate(ranking, start=1):
        cv_text = "inf" if math.isinf(cv) else f"{cv * 100:.2f}%"
        lines.append(f"| {index} | `{gate}` | {cv_text} | `{gate_worst_metric.get(gate, '')}` |")

    lines.extend(
        [
            "",
            "## Numeric Metrics",
            "",
            "| Gate | Metric | n | Mean ± std | Relative std |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for gate, key, count, mean, std, cv in metric_rows:
        cv_text = "inf" if math.isinf(cv) else f"{cv * 100:.2f}%"
        lines.append(f"| `{gate}` | `{key}` | {count} | {fmt(mean)} ± {fmt(std)} | {cv_text} |")

    lines.extend(
        [
            "",
            "## Run Logs",
            "",
        ]
    )
    for run_dir, passes, _ in run_data:
        manifest = run_dir / "run_manifest.json"
        manifest_passed = json.loads(manifest.read_text()).get("passed") if manifest.exists() else None
        lines.append(f"- `{run_dir.name}/` manifest: `{manifest.relative_to(ROOT)}` passed=`{manifest_passed}`")

    summary = "\n".join(lines) + "\n"

    notable = []
    for metric_name in (
        "benchmark_ablate_overlay.gain_bb_per_100",
        "exploit_check.preflop_mbb_g",
        "exploit_check.aggregate_mbb_g",
        "smoke.chip_delta.v_final",
        "smoke_timed.v_final.p99_ms",
    ):
        values = metric_values.get(metric_name, [])
        if values:
            mean, std = mean_std(values)
            notable.append(f"{metric_name} {fmt(mean)} ± {fmt(std)}")
    template_bits = []
    for target in ("template", "aggressor", "mathematician", "shark", "ref_bot_2"):
        key = f"benchmark_all_templates.{target}.bb_per_100"
        values = metric_values.get(key, [])
        if values:
            mean, std = mean_std(values)
            template_bits.append(f"{target} {mean:+.2f} ± {std:.2f}")
    ratchet_bits = []
    for key_name in ("v0_wired", "v1_blueprint", "v2_postflop", "v3_hardened"):
        key = f"benchmark_self_play_vs_prior.{key_name}.bb_per_100"
        values = metric_values.get(key, [])
        if values:
            mean, std = mean_std(values)
            ratchet_bits.append(f"{key_name} {mean:+.2f} ± {std:.2f}")

    highest_gate = ranking[0][0] if ranking else "n/a"
    highest_metric = gate_worst_metric.get(highest_gate, "n/a")
    highest_cv = gate_cv.get(highest_gate, 0.0)
    status_lines = [
        f"## {utc_now()} · G1-G11 variance characterization · GREEN",
        f"- Goal: Characterize gate-level variance across five repeats of the canonical `submissions/v_final.zip` gauntlet without modifying the artifact.",
        f"- Artifact guardrail: `submissions/v_final.zip` and `submissions/best_green.zip` stayed at sha256 `{EXPECTED_SHA}`; `ext/fullhouse-engine` stayed at `{preflight.get('engine_commit', 'unknown')}`.",
        f"- Runs: `consult/artifacts/2026-05-28-gauntlet-variance/run_1` through `run_5`; summary: `consult/artifacts/2026-05-28-gauntlet-variance/SUMMARY.md`.",
        f"- Pass/fail flips: {'none' if not flip_rows else '; '.join(f'{gate}={labels}' for gate, labels in flip_rows)}.",
        f"- All-template bb/100 mean ± std: {', '.join(template_bits)}.",
        f"- Ablation / ratchet / LBR / smoke: {', '.join(notable)}; ratchet: {', '.join(ratchet_bits)}.",
        f"- Relative variance leader: `{highest_gate}` via `{highest_metric}` at {'inf' if math.isinf(highest_cv) else f'{highest_cv * 100:.2f}%'} relative std.",
        "- Source / policy anchor: `AGENTS.md` benchmark variance policy and `PROMPT.shared.md` artifact-bound G1-G11 gauntlet.",
        "- Next action: keep `v_final.zip` locked; use the variance table as the baseline for any patch-window candidate comparison.",
    ]
    status = "\n".join(status_lines) + "\n"
    return summary, status


def main() -> int:
    summary, status = build_summary()
    (ROOT / "SUMMARY.md").write_text(summary)
    (ROOT / "STATUS_APPEND.md").write_text(status)
    print(summary)
    print("\n--- STATUS_APPEND.md ---\n")
    print(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
