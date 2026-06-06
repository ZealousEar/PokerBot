#!/usr/bin/env python3
"""Run five artifact-bound gauntlet repeats and persist logs per repeat."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


CANONICAL_ROOT = Path("/Users/farhad/Code/PokerBot")
GAUNTLET_ROOT = Path("/Users/farhad/Code/PokerBot-gauntlet")
ARTIFACT_ROOT = CANONICAL_ROOT / "consult" / "artifacts" / "2026-05-28-gauntlet-variance"
EXPECTED_SHA = "e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598"
PYTHON = GAUNTLET_ROOT / ".venv" / "bin" / "python"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_capture(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def guardrails() -> dict:
    paths = {
        "canonical_v_final": CANONICAL_ROOT / "submissions" / "v_final.zip",
        "canonical_best_green": CANONICAL_ROOT / "submissions" / "best_green.zip",
        "gauntlet_v_final": GAUNTLET_ROOT / "submissions" / "v_final.zip",
        "gauntlet_best_green": GAUNTLET_ROOT / "submissions" / "best_green.zip",
    }
    hashes = {name: sha256(path) for name, path in paths.items()}
    bad = {name: value for name, value in hashes.items() if value != EXPECTED_SHA}
    engine_commit = run_capture(["git", "-C", "ext/fullhouse-engine", "rev-parse", "HEAD"], CANONICAL_ROOT)
    gauntlet_head = run_capture(["git", "rev-parse", "HEAD"], GAUNTLET_ROOT)
    return {
        "hashes": hashes,
        "hashes_ok": not bad,
        "bad_hashes": bad,
        "canonical_head": run_capture(["git", "rev-parse", "HEAD"], CANONICAL_ROOT),
        "gauntlet_head": gauntlet_head,
        "engine_commit": engine_commit,
    }


def commands() -> list[tuple[str, list[str]]]:
    py = str(PYTHON)
    timed_smoke = ARTIFACT_ROOT / "timed_smoke.py"
    return [
        ("validator", [py, "ext/fullhouse-engine/sandbox/validator.py", "submissions/v_final.zip", "--json"]),
        ("import_audit", [py, "tools/import_audit.py"]),
        ("edge_cases", [py, "-m", "pytest", "tests/edge_cases", "-x"]),
        ("smoke", [py, "tools/smoke_run.py", "--zip", "submissions/v_final.zip", "--hands", "200"]),
        (
            "smoke_timed",
            [
                py,
                str(timed_smoke),
                "--repo",
                str(GAUNTLET_ROOT),
                "--zip",
                "submissions/v_final.zip",
                "--hands",
                "200",
                "--seed",
                "42",
            ],
        ),
        ("audit_strategy_leakage", [py, "tools/audit_strategy_leakage.py", "--zip", "submissions/v_final.zip"]),
        (
            "exploit_check",
            [
                py,
                "tools/exploit_check.py",
                "--bot",
                "submissions/v_final.zip",
                "--max-preflop-mbb",
                "100",
                "--max-aggregate-mbb",
                "200",
            ],
        ),
        (
            "benchmark_all_templates",
            [
                py,
                "tools/benchmark.py",
                "--all-templates",
                "--hands",
                "10000",
                "--bot",
                "submissions/v_final.zip",
                "--paired-seed-base",
                "42",
            ],
        ),
        (
            "benchmark_ablate_overlay",
            [
                py,
                "tools/benchmark.py",
                "--ablate-overlay",
                "--hands",
                "10000",
                "--bot",
                "submissions/v_final.zip",
                "--paired-seed-base",
                "42",
            ],
        ),
        (
            "benchmark_self_play_vs_prior",
            [
                py,
                "tools/benchmark.py",
                "--self-play",
                "--vs-prior",
                "--hands",
                "10000",
                "--bot",
                "submissions/v_final.zip",
                "--paired-seed-base",
                "42",
            ],
        ),
    ]


def run_one(label: str, cmd: list[str], run_dir: Path, heartbeat_s: int) -> dict:
    log_path = run_dir / f"{label}.log"
    started = time.time()
    with log_path.open("w") as log:
        log.write(f"# label={label}\n")
        log.write(f"# cwd={GAUNTLET_ROOT}\n")
        log.write(f"# started_utc={utc_now()}\n")
        log.write("# command=" + " ".join(shlex.quote(part) for part in cmd) + "\n\n")
        log.flush()
        process = subprocess.Popen(cmd, cwd=GAUNTLET_ROOT, stdout=log, stderr=subprocess.STDOUT, text=True)
        next_heartbeat = time.time() + heartbeat_s
        while process.poll() is None:
            time.sleep(1)
            now = time.time()
            if now >= next_heartbeat:
                elapsed = int(now - started)
                print(f"[{utc_now()}] {run_dir.name} {label} still running ({elapsed}s)", flush=True)
                next_heartbeat = now + heartbeat_s
        returncode = process.returncode
        finished = utc_now()
        duration = time.time() - started
        log.write(f"\n# finished_utc={finished}\n")
        log.write(f"# returncode={returncode}\n")
        log.write(f"# duration_s={duration:.3f}\n")
    meta = {
        "label": label,
        "command": cmd,
        "cwd": str(GAUNTLET_ROOT),
        "log": log_path.name,
        "started_utc": datetime.fromtimestamp(started, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "finished_utc": finished,
        "duration_s": duration,
        "returncode": returncode,
        "passed": returncode == 0,
    }
    (run_dir / f"{label}.meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(f"[{utc_now()}] {run_dir.name} {label} done rc={returncode} duration={duration:.1f}s", flush=True)
    return meta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--heartbeat-s", type=int, default=30)
    args = parser.parse_args()

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    preflight = guardrails()
    (ARTIFACT_ROOT / "PREFLIGHT.json").write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n")
    if not preflight["hashes_ok"]:
        print(json.dumps(preflight, indent=2, sort_keys=True))
        return 2
    print(f"[{utc_now()}] preflight ok: engine={preflight['engine_commit']} gauntlet={preflight['gauntlet_head']}", flush=True)

    all_runs = []
    for index in range(1, args.runs + 1):
        run_dir = ARTIFACT_ROOT / f"run_{index}"
        run_dir.mkdir(parents=True, exist_ok=True)
        run_guardrails = guardrails()
        (run_dir / "guardrails_start.json").write_text(json.dumps(run_guardrails, indent=2, sort_keys=True) + "\n")
        print(f"[{utc_now()}] starting {run_dir.name}", flush=True)
        metas = []
        for label, cmd in commands():
            metas.append(run_one(label, cmd, run_dir, args.heartbeat_s))
        end_guardrails = guardrails()
        (run_dir / "guardrails_end.json").write_text(json.dumps(end_guardrails, indent=2, sort_keys=True) + "\n")
        run_manifest = {
            "run": index,
            "started_guardrails": run_guardrails,
            "finished_guardrails": end_guardrails,
            "commands": metas,
            "passed": all(item["passed"] for item in metas) and end_guardrails["hashes_ok"],
        }
        (run_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2, sort_keys=True) + "\n")
        all_runs.append(run_manifest)
        print(f"[{utc_now()}] finished {run_dir.name} passed={run_manifest['passed']}", flush=True)

    postflight = guardrails()
    (ARTIFACT_ROOT / "POSTFLIGHT.json").write_text(json.dumps(postflight, indent=2, sort_keys=True) + "\n")
    (ARTIFACT_ROOT / "RUNS.json").write_text(json.dumps(all_runs, indent=2, sort_keys=True) + "\n")
    if not postflight["hashes_ok"]:
        print(json.dumps(postflight, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    return 0 if all(item["passed"] for item in all_runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
