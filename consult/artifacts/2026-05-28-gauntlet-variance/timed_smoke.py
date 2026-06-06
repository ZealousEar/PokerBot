#!/usr/bin/env python3
"""Run the release smoke match while recording per-action latency.

This is a measurement wrapper around ext/fullhouse-engine/sandbox/match.py.
It keeps the same Docker sandbox path as tools/smoke_run.py, then monkeypatches
BotProcess.act in-process so p99 latency can be reported without editing the
engine or strategy source.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[index]


def ensure_image(sandbox: Path, image: str) -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("docker not on PATH")
    inspect = subprocess.run(["docker", "image", "inspect", image], capture_output=True)
    if inspect.returncode == 0:
        return
    subprocess.run(["docker", "build", "-t", image, str(sandbox)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--zip", default="submissions/v_final.zip")
    parser.add_argument("--opponent", default="template")
    parser.add_argument("--hands", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--image", default=os.environ.get("SANDBOX_IMAGE", "fullhouse-sandbox:latest"))
    args = parser.parse_args()

    repo = args.repo.resolve()
    engine = repo / "ext" / "fullhouse-engine"
    sandbox = engine / "sandbox"
    submission = (repo / args.zip).resolve()
    opponent = (engine / "bots" / args.opponent).resolve()
    if not submission.is_file():
        print(json.dumps({"passed": False, "error": f"missing submission {submission}"}))
        return 2
    if not opponent.is_dir():
        print(json.dumps({"passed": False, "error": f"missing opponent {opponent}"}))
        return 2

    ensure_image(sandbox, args.image)
    os.chdir(repo)
    os.environ["USE_DOCKER"] = "true"
    os.environ["SANDBOX_IMAGE"] = args.image
    if str(engine) not in sys.path:
        sys.path.insert(0, str(engine))

    from sandbox import match  # noqa: PLC0415

    match.USE_DOCKER = True
    match.SANDBOX_IMAGE = args.image
    timings_by_bot: dict[str, list[float]] = {}
    original_warmup = match.BotProcess.warmup

    def compatible_start(self):  # type: ignore[no-untyped-def]
        container_bot_py = "/bot/bot.py"
        if match.USE_DOCKER:
            cmd = [
                "docker",
                "run",
                "--rm",
                "-i",
                "--network",
                "none",
                "--memory",
                match.CONTAINER_MEMORY,
                "--memory-swap",
                match.CONTAINER_MEMORY,
                "--cpus",
                match.CONTAINER_CPUS,
                "--read-only",
                "--security-opt",
                "no-new-privileges",
                "--user",
                "1000:1000",
                "--tmpfs",
                "/tmp:size=" + match.CONTAINER_TMPFS_SIZE,
                "-v",
                self._mount_src + ":/bot:ro",
                "-e",
                "ACTION_TIMEOUT=" + str(match.ACTION_TIMEOUT),
                "-e",
                "BOT_PATH=" + container_bot_py,
                "-e",
                "BOT_DATA_DIR=/bot/data",
                match.SANDBOX_IMAGE,
            ]
        else:
            cmd = [sys.executable, "-u", str(match.RUNNER_PATH)]

        host_bot_py = os.path.join(self._mount_src, "bot.py")
        env = {
            **os.environ,
            "BOT_PATH": container_bot_py if match.USE_DOCKER else host_bot_py,
            "BOT_DATA_DIR": "/bot/data" if match.USE_DOCKER else os.path.join(self._mount_src, "data"),
            "ACTION_TIMEOUT": str(match.ACTION_TIMEOUT),
        }
        return subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

    def timed_act(self, game_state):  # type: ignore[no-untyped-def]
        start = time.perf_counter()
        try:
            if self._proc is None:
                return {"action": "fold", "error": "no_process"}
            self._proc.stdin.write(json.dumps(game_state) + "\n")
            self._proc.stdin.flush()
            line = self._proc.stdout.readline()
            if not line:
                stderr = self._proc.stderr.read() if self._proc.stderr else ""
                if stderr:
                    self.errors.append("stderr: " + stderr[-2000:])
                raise EOFError("Bot process died")
            action = json.loads(line.strip())
            if "error" in action:
                self.errors.append(action["error"])
            return action
        except Exception as exc:
            self.errors.append(str(exc))
            return {"action": "fold", "error": str(exc)}
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            timings_by_bot.setdefault(self.bot_id, []).append(elapsed_ms)

    def timed_warmup(self):  # type: ignore[no-untyped-def]
        original_warmup(self)
        if self.errors and self._proc is not None and self._proc.poll() is not None and self._proc.stderr:
            stderr = self._proc.stderr.read()
            if stderr:
                self.errors.append("warmup_stderr: " + stderr[-2000:])

    match.BotProcess.act = timed_act
    match.BotProcess.warmup = timed_warmup
    match.BotProcess._start = compatible_start
    result = match.run_match(
        "timed_smoke",
        {"v_final": str(submission), args.opponent: str(opponent)},
        n_hands=args.hands,
        verbose=False,
        seed=args.seed,
    )

    errors = {bot: errs for bot, errs in result.get("bot_errors", {}).items() if errs}
    timing_summary = {}
    for bot, values in timings_by_bot.items():
        timing_summary[bot] = {
            "count": len(values),
            "mean_ms": sum(values) / len(values) if values else 0.0,
            "p50_ms": percentile(values, 50.0),
            "p95_ms": percentile(values, 95.0),
            "p99_ms": percentile(values, 99.0),
            "max_ms": max(values) if values else 0.0,
        }
    short_hands = result.get("n_hands", 0) < int(args.hands * 0.9)
    passed = result.get("n_hands", 0) > 0 and not errors and bool(timing_summary.get("v_final"))
    payload = {
        "passed": passed,
        "measurement_only": True,
        "short_hands": short_hands,
        "n_hands": result.get("n_hands", 0),
        "expected_hands": args.hands,
        "seed": args.seed,
        "chip_delta": result.get("chip_delta", {}),
        "errors": errors,
        "duration_s": result.get("duration_s"),
        "use_docker": match.USE_DOCKER,
        "sandbox_image": match.SANDBOX_IMAGE,
        "timings_ms": timing_summary,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("timed_smoke PASS" if passed else "timed_smoke FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
