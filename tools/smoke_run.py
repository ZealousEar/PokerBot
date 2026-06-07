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
    exit 0  -- match ran cleanly; normal early bust / match completion is OK
    exit 1  -- match ran but produced bot errors / timeouts / invalid early stop
    exit 2  -- prerequisite missing (no docker, missing submission, missing opponent)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
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


def _docker_supports_no_new_privileges() -> bool:
    res = subprocess.run(["docker", "run", "--help"], capture_output=True, text=True)
    return "--no-new-privileges" in (res.stdout + res.stderr)


def _install_docker_flag_shim(env: dict[str, str], tmp: tempfile.TemporaryDirectory[str]) -> None:
    real_docker = shutil.which("docker")
    if not real_docker:
        return
    wrapper = Path(tmp.name) / "docker"
    wrapper.write_text(
        """#!/usr/bin/env python3
import os
import sys

real = os.environ["REAL_DOCKER"]
args = []
for arg in sys.argv[1:]:
    if arg == "--no-new-privileges":
        args.extend(["--security-opt", "no-new-privileges"])
    else:
        args.append(arg)
os.execv(real, [real] + args)
"""
    )
    wrapper.chmod(0o755)
    env["REAL_DOCKER"] = real_docker
    env["PATH"] = tmp.name + os.pathsep + env.get("PATH", "")


def _bot_id_for_path(path: Path) -> str:
    """Mirror match.py's default bot_id derivation for the first bot path."""
    bot_id = path.stem if path.suffix in (".py", ".zip") else path.name
    if bot_id == "bot":
        bot_id = path.parent.name
    return bot_id or "bot_0"


def _early_termination_reason(actual_hands: int, requested_hands: int, final_stacks: dict) -> str:
    if actual_hands >= requested_hands:
        return "requested_hands_completed"
    if final_stacks:
        alive = [bot_id for bot_id, stack in final_stacks.items() if stack > 0]
        busted = [bot_id for bot_id, stack in final_stacks.items() if stack <= 0]
        if len(alive) < 2:
            return "normal_bust: fewer than two bots remain; busted=" + ",".join(busted)
    return "unknown_early_termination"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", default="submissions/v_final.zip",
                   help="Submission archive (defaults to submissions/v_final.zip)")
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
    shim_tmp = None
    if not _docker_supports_no_new_privileges():
        shim_tmp = tempfile.TemporaryDirectory(prefix="fh_docker_shim_")
        _install_docker_flag_shim(env, shim_tmp)
        print(
            "[smoke_run] docker shim: translating --no-new-privileges "
            "to --security-opt no-new-privileges",
            file=sys.stderr,
        )
    cmd = [
        sys.executable, str(MATCH),
        str(submission), str(opponent),
        "--hands", str(args.hands),
        "--seed", str(args.seed),
        "--json",
    ]
    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    finally:
        if shim_tmp is not None:
            shim_tmp.cleanup()
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

    actual_hands = result.get("n_hands", 0)
    requested_hands = args.hands
    errors = {b: e for b, e in result.get("bot_errors", {}).items() if e}
    chip_delta = result.get("chip_delta", {})
    duration_s = result.get("duration_s")
    final_stacks = result.get("final_stacks", {})
    hero_id = _bot_id_for_path(submission)
    hero_errors = errors.get(hero_id, [])
    early_reason = _early_termination_reason(actual_hands, requested_hands, final_stacks)

    print(json.dumps({
        "requested_hands": requested_hands,
        "actual_hands": actual_hands,
        "early_termination_reason": early_reason,
        "hero_id": hero_id,
        "hero_errors": hero_errors,
        "chip_delta": chip_delta,
        "final_stacks": final_stacks,
        "errors": errors,
        "duration_s": duration_s,
    }, indent=2))

    if hero_errors:
        print(f"[smoke_run] FAIL: hero_errors {hero_errors}", file=sys.stderr)
        return 1
    if errors:
        print(f"[smoke_run] FAIL: bot_errors {errors}", file=sys.stderr)
        return 1
    if actual_hands < requested_hands and not early_reason.startswith("normal_bust"):
        print(
            f"[smoke_run] FAIL: {actual_hands}/{requested_hands} hands "
            f"without normal bust ({early_reason})",
            file=sys.stderr,
        )
        return 1

    print(f"[smoke_run] OK: {early_reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
