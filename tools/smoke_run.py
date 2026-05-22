"""Sandbox smoke run -- exercises a submission inside the real engine sandbox
container against a reference bot for a small number of hands. Catches
runtime issues (timeout, OOM, missing data files, slow imports) that the
AST-only validator cannot detect.

The engine sandbox already supports docker mode via USE_DOCKER=true in
ext/fullhouse-engine/sandbox/match.py with the exact tournament flags
(--network none --memory 768m --cpus 0.5 --read-only --no-new-privileges
--user 1000:1000). This wrapper just builds the image if missing, kicks
off a small match, parses the JSON result, and exits 0 on clean play.

Usage:
    python tools/smoke_run.py [--zip submissions/<name>.zip]
                              [--opponent template] [--hands 200] [--seed 42]

Returns:
    exit 0  -- match completed, no bot_errors, no timeouts, >= 90 % hands played
    exit 1  -- match ran but produced errors / timeouts / short hand count
    exit 2  -- prerequisite missing (no docker, missing submission, missing opponent)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "ext" / "fullhouse-engine"
SANDBOX = ENGINE / "sandbox"
MATCH = SANDBOX / "match.py"
IMAGE = os.environ.get("SANDBOX_IMAGE", "fullhouse-sandbox:latest")


def _check_docker() -> bool:
    return shutil.which("docker") is not None


def _ensure_image() -> None:
    res = subprocess.run(
        ["docker", "image", "inspect", IMAGE],
        capture_output=True,
    )
    if res.returncode == 0:
        return
    print(f"[smoke_run] building {IMAGE} from {SANDBOX}/Dockerfile", file=sys.stderr)
    subprocess.run(
        ["docker", "build", "-t", IMAGE, str(SANDBOX)],
        check=True,
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", default="submissions/best_green.zip",
                   help="Submission archive (defaults to submissions/best_green.zip)")
    p.add_argument("--opponent", default="template",
                   help="Reference bot under ext/fullhouse-engine/bots/")
    p.add_argument("--hands", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    submission = (ROOT / args.zip).resolve()
    if not submission.is_file():
        print(f"[smoke_run] FAIL: missing submission {submission}", file=sys.stderr)
        return 2

    opponent = (ENGINE / "bots" / args.opponent).resolve()
    if not opponent.is_dir():
        print(f"[smoke_run] FAIL: missing opponent {opponent}", file=sys.stderr)
        return 2

    if not _check_docker():
        print("[smoke_run] FAIL: docker not on PATH", file=sys.stderr)
        return 2

    _ensure_image()

    env = {**os.environ, "USE_DOCKER": "true", "SANDBOX_IMAGE": IMAGE}
    cmd = [
        sys.executable, str(MATCH),
        str(submission), str(opponent),
        "--hands", str(args.hands),
        "--seed", str(args.seed),
        "--json",
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[smoke_run] FAIL: match.py exit {res.returncode}", file=sys.stderr)
        sys.stderr.write(res.stderr)
        return 1

    try:
        # match.py --json prints one JSON object on stdout (last line).
        result = json.loads(res.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as e:
        print(f"[smoke_run] FAIL: could not parse match output: {e}", file=sys.stderr)
        sys.stderr.write(res.stdout)
        return 1

    n_hands = result.get("n_hands", 0)
    errors = {b: e for b, e in result.get("bot_errors", {}).items() if e}
    chip_delta = result.get("chip_delta", {})
    duration_s = result.get("duration_s")

    print(json.dumps({
        "n_hands": n_hands,
        "expected_hands": args.hands,
        "chip_delta": chip_delta,
        "errors": errors,
        "duration_s": duration_s,
    }, indent=2))

    if n_hands < int(args.hands * 0.9):
        print(f"[smoke_run] FAIL: only {n_hands}/{args.hands} hands played", file=sys.stderr)
        return 1
    if errors:
        print(f"[smoke_run] FAIL: bot_errors {errors}", file=sys.stderr)
        return 1

    print("[smoke_run] OK", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
