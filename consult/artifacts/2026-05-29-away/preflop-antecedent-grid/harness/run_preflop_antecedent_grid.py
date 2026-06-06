#!/usr/bin/env python3
"""Candidate-only preflop antecedent grid runner.

This script builds new candidate zips from the locked v_final.zip and replaces
only src/preflop_lookup.py inside those candidate archives. It does not modify
or overwrite protected submission artifacts.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import textwrap
import time
import zipfile
from pathlib import Path


WORKTREE = Path("/Users/farhad/Code/PokerBot-codex-preflop-antecedent")
MAIN_REPO = Path("/Users/farhad/Code/PokerBot")
ARTIFACT_DIR = MAIN_REPO / "consult/artifacts/2026-05-29-away/preflop-antecedent-grid"
COMMAND_LOG_DIR = ARTIFACT_DIR / "command_logs"
ZIP_DIR = ARTIFACT_DIR / "zips"
DIFF_DIR = ARTIFACT_DIR / "diffs"
TMP_DIR = ARTIFACT_DIR / "tmp"
LOCKED_ZIP = MAIN_REPO / "submissions/v_final.zip"
BEST_GREEN_ZIP = MAIN_REPO / "submissions/best_green.zip"
EXPECTED_LOCKED_SHA = "e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598"
ENGINE_DIR = MAIN_REPO / "ext/fullhouse-engine"
VALIDATOR = ENGINE_DIR / "sandbox/validator.py"
SMOKE_RUN = MAIN_REPO / "tools/smoke_run.py"


BASE_BRANCH = "release/v_final-e4b4a8f1"
MATCH_LEN = 200
BIG_BLIND = 100
STARTING_STACK = 10_000
IMPROVEMENT_THRESHOLD_BB100 = 5.0
REGRESSION_THRESHOLD_BB100 = -5.0

VARIANTS = {
    "A0": {"label": "baseline locked source", "floors": {}},
    "A1": {"label": "HU/button open floor >= 20", "floors": {"heads_up_button": 20, "small_blind": 20, "button": 20}},
    "A2": {"label": "HU/button open floor >= 32", "floors": {"heads_up_button": 32, "small_blind": 32, "button": 32}},
    "A3": {"label": "HU/button open floor >= 40", "floors": {"heads_up_button": 40, "small_blind": 40, "button": 40}},
    "A4": {"label": "HU/button open floor >= 50", "floors": {"heads_up_button": 50, "small_blind": 50, "button": 50}},
    "A5": {"label": "HU floor >= 32; six-max SB/button floor >= 40", "floors": {"heads_up_button": 32, "small_blind": 40, "button": 40}},
}

PRIMARY_OPPONENTS = {
    "toby_master": MAIN_REPO / "consult/artifacts/2026-05-29-public-drift-patch/opponent_zips/toby_master.zip",
    "mehedi_mybot": MAIN_REPO / "consult/artifacts/2026-05-29-public-repo-drift/opponent_zips/mehedi_mybot.zip",
    "pav_skantbot7_9": MAIN_REPO / "consult/artifacts/2026-05-29-public-repo-drift/opponent_zips/pav_skantbot7_9.zip",
    "pav_skantbot7_6": MAIN_REPO / "consult/artifacts/2026-05-29-public-repo-drift/opponent_zips/pav_skantbot7_6.zip",
    "famadeo": MAIN_REPO / "consult/artifacts/2026-05-28-public-saturation/opponent_zips/famadeo.zip",
    "neel": MAIN_REPO / "consult/artifacts/2026-05-28-public-saturation/opponent_zips/neel.zip",
    "stoppedtime24_mybot": MAIN_REPO / "consult/artifacts/2026-05-29-public-repo-drift/opponent_zips/stoppedtime24_mybot.zip",
}

REFERENCE_OPPONENTS = {
    "ref_template": ENGINE_DIR / "bots/template",
    "ref_aggressor": ENGINE_DIR / "bots/aggressor",
    "ref_mathematician": ENGINE_DIR / "bots/mathematician",
    "ref_shark": ENGINE_DIR / "bots/shark",
    "ref_ref_bot_2": ENGINE_DIR / "bots/ref_bot_2",
}

FORBIDDEN_STRINGS = (
    "bot_id",
    "aggressor",
    "template",
    "mathematician",
    "shark",
    "ref_bot_2",
    "v0_wired",
    "v1_blueprint",
    "v2_postflop",
    "v3_hardened",
    "best_green",
    "v_final",
    "pre_x1",
    "post_x1",
    "codex",
    "claude",
    "branch",
    "snapshot",
    "seed",
)

FORBIDDEN_MODULES = {
    "socket", "urllib", "urllib2", "urllib3", "requests", "httpx", "aiohttp",
    "http", "ftplib", "smtplib", "telnetlib", "xmlrpc", "subprocess",
    "multiprocessing", "pickle", "shelve", "threading", "ctypes", "runpy",
    "importlib",
}
BANNED_CALL_NAMES = {"__import__", "eval", "exec", "compile"}
BANNED_OS_FUNCS = {
    "system", "popen", "execv", "execve", "execvp", "execvpe", "execl",
    "execle", "execlp", "execlpe", "spawn", "spawnv", "spawnve", "spawnvp",
    "fork", "kill", "remove", "unlink", "rmdir", "removedirs", "chmod",
    "chown", "replace", "rename",
}


def ensure_dirs() -> None:
    for path in (ARTIFACT_DIR, COMMAND_LOG_DIR, ZIP_DIR, DIFF_DIR, TMP_DIR):
        path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_log(label: str, payload: str) -> None:
    (COMMAND_LOG_DIR / f"{label}.log").write_text(payload)


def run_command(label: str, argv: list[str], cwd: Path | None = None, env: dict | None = None, timeout: int | None = None) -> dict:
    start = time.time()
    proc = subprocess.run(
        argv,
        cwd=str(cwd or WORKTREE),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    elapsed = time.time() - start
    log = [
        "command: " + " ".join(argv),
        "cwd: " + str(cwd or WORKTREE),
        f"exit_code: {proc.returncode}",
        f"elapsed_s: {elapsed:.3f}",
        "",
        "[stdout]",
        proc.stdout,
        "",
        "[stderr]",
        proc.stderr,
    ]
    write_log(label, "\n".join(log))
    return {
        "label": label,
        "command": argv,
        "cwd": str(cwd or WORKTREE),
        "exit_code": proc.returncode,
        "elapsed_s": elapsed,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "log": str(COMMAND_LOG_DIR / f"{label}.log"),
    }


def protected_sha_payload() -> dict:
    return {
        "v_final": {
            "path": str(LOCKED_ZIP),
            "sha256": sha256(LOCKED_ZIP) if LOCKED_ZIP.is_file() else None,
        },
        "best_green": {
            "path": str(BEST_GREEN_ZIP),
            "sha256": sha256(BEST_GREEN_ZIP) if BEST_GREEN_ZIP.is_file() else None,
        },
    }


def assert_protected_shas() -> None:
    payload = protected_sha_payload()
    for key, item in payload.items():
        if item["sha256"] != EXPECTED_LOCKED_SHA:
            raise RuntimeError(f"{key} sha drift: expected {EXPECTED_LOCKED_SHA}, actual {item['sha256']}")


def locked_preflop_source() -> str:
    with zipfile.ZipFile(LOCKED_ZIP) as zf:
        return zf.read("src/preflop_lookup.py").decode("utf-8")


def variant_source(base_source: str, floors: dict[str, int]) -> str:
    if not floors:
        return base_source

    old = textwrap.dedent(
        '''\
        if position in ("heads_up_button", "small_blind", "button"):
            return {"action": "raise", "sizing": "min_raise", "reason": "heads_up_steal"}
        '''
    )
    old = "\n".join("        " + line if line else line for line in old.splitlines())

    if floors["heads_up_button"] == floors["small_blind"] == floors["button"]:
        floor = floors["heads_up_button"]
        new = textwrap.dedent(
            f'''\
            if position in ("heads_up_button", "small_blind", "button"):
                if score >= {floor}:
                    return {{"action": "raise", "sizing": "min_raise", "reason": "heads_up_steal"}}
                return {{"action": "fold", "reason": "steal_floor_fold"}}
            '''
        )
    else:
        new = textwrap.dedent(
            f'''\
            if position == "heads_up_button":
                if score >= {floors["heads_up_button"]}:
                    return {{"action": "raise", "sizing": "min_raise", "reason": "heads_up_steal"}}
                return {{"action": "fold", "reason": "steal_floor_fold"}}
            if position in ("small_blind", "button"):
                if score >= {floors["button"]}:
                    return {{"action": "raise", "sizing": "min_raise", "reason": "heads_up_steal"}}
                return {{"action": "fold", "reason": "steal_floor_fold"}}
            '''
        )
    new = "\n".join("        " + line if line else line for line in new.splitlines())

    if old not in base_source:
        raise RuntimeError("expected open-any branch not found in locked preflop source")
    return base_source.replace(old, new, 1)


def build_candidate_zips(results: dict) -> None:
    assert_protected_shas()
    base = locked_preflop_source()
    candidates = {}
    for case, spec in VARIANTS.items():
        source = variant_source(base, spec["floors"])
        zip_path = ZIP_DIR / f"preflop_antecedent_{case}.zip"
        if case == "A0":
            shutil.copy2(LOCKED_ZIP, zip_path)
        else:
            with zipfile.ZipFile(LOCKED_ZIP, "r") as src, zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as dst:
                preflop_info = src.getinfo("src/preflop_lookup.py")
                for info in src.infolist():
                    if info.filename == "src/preflop_lookup.py":
                        continue
                    dst.writestr(info, src.read(info.filename))
                dst.writestr(preflop_info, source.encode("utf-8"))
        diff = "".join(
            difflib.unified_diff(
                base.splitlines(keepends=True),
                source.splitlines(keepends=True),
                fromfile="A0/src/preflop_lookup.py",
                tofile=f"{case}/src/preflop_lookup.py",
            )
        )
        diff_path = DIFF_DIR / f"{case}.diff"
        diff_path.write_text(diff or "# no source diff from locked baseline\n")
        candidates[case] = {
            "label": spec["label"],
            "floors": spec["floors"],
            "zip_path": str(zip_path),
            "zip_sha256": sha256(zip_path),
            "diff_path": str(diff_path),
        }
    results["candidates"] = candidates
    save_results(results)


def strategy_members(zf: zipfile.ZipFile) -> list[str]:
    return sorted(
        name for name in zf.namelist()
        if name == "bot.py" or (name.startswith("src/") and name.endswith(".py"))
    )


def leakage_audit(zip_path: Path) -> dict:
    issues = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in strategy_members(zf):
            text = zf.read(name).decode("utf-8")
            for lineno, line in enumerate(text.lower().splitlines(), start=1):
                for needle in FORBIDDEN_STRINGS:
                    if needle in line:
                        issues.append(f"{name}:{lineno}: {needle}")
    return {"pass": not issues, "issues": issues}


def attr_chain(node) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def scan_source_file(path: Path, root: Path) -> list[str]:
    issues = []
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as e:
        return [f"{path.relative_to(root)}: SyntaxError {e}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod in FORBIDDEN_MODULES:
                    issues.append(f"{path.relative_to(root)}: forbidden import {mod}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in FORBIDDEN_MODULES:
                issues.append(f"{path.relative_to(root)}: forbidden from {mod}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALL_NAMES:
                issues.append(f"{path.relative_to(root)}: forbidden call {node.func.id}(...)")
            if isinstance(node.func, ast.Attribute):
                chain = attr_chain(node.func)
                if chain.startswith("os.") and chain.split(".")[1] in BANNED_OS_FUNCS:
                    issues.append(f"{path.relative_to(root)}: forbidden call {chain}(...)")
                if chain.startswith("subprocess."):
                    issues.append(f"{path.relative_to(root)}: forbidden call {chain}(...)")
            if isinstance(node.func, ast.Name) and node.func.id == "getattr":
                if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "__builtins__":
                    issues.append(f"{path.relative_to(root)}: getattr(__builtins__, ...)")
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and node.value.id == "__builtins__":
                issues.append(f"{path.relative_to(root)}: __builtins__[...] subscript")
    return issues


def extract_zip(zip_path: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)


def import_audit(case: str, zip_path: Path) -> dict:
    root = TMP_DIR / f"import_{case}"
    extract_zip(zip_path, root)
    issues = []
    for py in sorted((root / "src").rglob("*.py")):
        issues.extend(scan_source_file(py, root))
    issues.extend(scan_source_file(root / "bot.py", root))

    script = (
        "import resource, sys, time; "
        "sys.path.insert(0, '.'); "
        "t0=time.monotonic(); "
        "import bot; "
        "dt=time.monotonic()-t0; "
        "rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss; "
        "print(f'{dt:.4f} {rss}')"
    )
    env = {**os.environ, "BOT_DATA_DIR": str(root / "data")}
    cmd = [sys.executable, "-c", script]
    result = run_command(f"{case}_import_cold", cmd, cwd=root, env=env)
    seconds = None
    rss_mb = None
    if result["exit_code"] == 0:
        parts = result["stdout"].strip().split()
        if len(parts) >= 2:
            seconds = float(parts[0])
            rss_raw = int(parts[1])
            rss_mb = rss_raw / (1024 * 1024) if sys.platform == "darwin" else rss_raw / 1024
    passed = not issues and result["exit_code"] == 0 and seconds is not None and seconds <= 1.5 and rss_mb is not None and rss_mb <= 400
    return {
        "pass": passed,
        "issues": issues,
        "cold_import_s": seconds,
        "rss_mb": rss_mb,
        "command_log": result["log"],
    }


def edge_tests(case: str, zip_path: Path) -> dict:
    root = TMP_DIR / f"edge_{case}"
    extract_zip(zip_path, root)
    shutil.copytree(WORKTREE / "tests", root / "tests")
    env = {
        **os.environ,
        "BOT_DATA_DIR": str(root / "data"),
        "PREFLOP_ANTECEDENT_CASE": case,
        "PYTHONPATH": str(root),
    }
    cmd = [sys.executable, "-m", "pytest", "tests/edge_cases", "-x"]
    result = run_command(f"{case}_edge_tests", cmd, cwd=root, env=env)
    return {
        "pass": result["exit_code"] == 0,
        "exit_code": result["exit_code"],
        "command_log": result["log"],
    }


def verify_candidate(case: str, zip_path: Path, smoke_hands: int, skip_smoke: bool) -> dict:
    leak = leakage_audit(zip_path)
    write_log(f"{case}_leakage_audit", json.dumps(leak, indent=2))

    imp = import_audit(case, zip_path)
    edge = edge_tests(case, zip_path)

    validator = run_command(
        f"{case}_validator",
        [sys.executable, str(VALIDATOR), str(zip_path)],
        cwd=MAIN_REPO,
        timeout=120,
    )

    smoke = {"pass": None, "skipped": True, "reason": "skip_smoke requested"}
    if not skip_smoke:
        smoke_cmd = [
            sys.executable,
            str(SMOKE_RUN),
            "--zip",
            str(zip_path),
            "--opponent",
            "template",
            "--hands",
            str(smoke_hands),
            "--seed",
            "42",
        ]
        smoke_result = run_command(f"{case}_smoke", smoke_cmd, cwd=MAIN_REPO, timeout=300)
        smoke = {
            "pass": smoke_result["exit_code"] == 0,
            "exit_code": smoke_result["exit_code"],
            "command_log": smoke_result["log"],
        }

    return {
        "leakage_audit": leak,
        "import_audit": imp,
        "edge_tests": edge,
        "validator": {
            "pass": validator["exit_code"] == 0,
            "exit_code": validator["exit_code"],
            "command_log": validator["log"],
        },
        "smoke": smoke,
    }


def load_engine():
    if str(ENGINE_DIR) not in sys.path:
        sys.path.insert(0, str(ENGINE_DIR))
    from sandbox.match import run_match  # noqa: PLC0415
    return run_match


def bootstrap_ci(samples: list[int], iterations: int = 600, seed: int = 8675309) -> tuple[float, float]:
    if not samples:
        return 0.0, 0.0
    if len(samples) == 1:
        value = bb_per_100(samples)
        return value, value
    rng = random.Random(seed)
    n = len(samples)
    values = []
    for _ in range(iterations):
        total = 0
        for _ in range(n):
            total += samples[rng.randrange(n)]
        values.append((total / n) / BIG_BLIND * 100.0)
    values.sort()
    return values[int(iterations * 0.025)], values[min(iterations - 1, int(iterations * 0.975))]


def bb_per_100(samples: list[int]) -> float:
    if not samples:
        return 0.0
    return (sum(samples) / len(samples)) / BIG_BLIND * 100.0


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return ordered[idx]


def hand_samples_and_metrics(result: dict, hero_id: str, scheduled_match_hands: int, two_player: bool) -> dict:
    samples = []
    previous = {bid: STARTING_STACK for bid in result.get("bot_ids", [])}
    hu_open_opportunities = 0
    hu_button_opens = 0
    river_commit = 0
    river_commit_losing = 0
    for hand in result.get("hands", []):
        final = {bid: int(stack) for bid, stack in (hand.get("final_stacks") or {}).items()}
        current = final.get(hero_id, previous.get(hero_id, STARTING_STACK))
        prev = previous.get(hero_id, STARTING_STACK)
        samples.append(current - prev)
        previous.update(final)

        events = [event for event in hand.get("events", []) if event.get("type") == "action"]
        if two_player:
            preflop = [event for event in events if event.get("street") == "preflop"]
            if preflop and preflop[0].get("bot_id") == hero_id:
                hu_open_opportunities += 1
                if preflop[0].get("action") in ("raise", "all_in"):
                    hu_button_opens += 1

        hero_river_commits = [
            event for event in events
            if event.get("street") == "river"
            and event.get("bot_id") == hero_id
            and event.get("action") in ("call", "raise", "all_in")
        ]
        if hero_river_commits:
            river_commit += 1
            if current - prev < 0:
                river_commit_losing += 1

    return {
        "samples": samples,
        "early_bust": 1 if int(result.get("n_hands") or 0) < scheduled_match_hands else 0,
        "hu_button_open_opportunities": hu_open_opportunities,
        "hu_button_opens": hu_button_opens,
        "river_commit_hands": river_commit,
        "river_commit_losing_hands": river_commit_losing,
        "seconds_per_hand": (float(result.get("duration_s") or 0.0) / max(1, int(result.get("n_hands") or 0))),
    }


def seed_count_for_hands(hands: int, orientations: int) -> int:
    return max(1, math.ceil(hands / (MATCH_LEN * orientations)))


def run_two_player_h2h(case: str, zip_path: Path, target: str, opponent_path: Path, requested_hands: int, seed_base: int) -> dict:
    run_match = load_engine()
    if not opponent_path.exists():
        payload = {"target": target, "skipped": True, "reason": f"missing opponent {opponent_path}"}
        write_log(f"{case}_h2h_{target}", json.dumps(payload, indent=2))
        return payload

    seed_count = seed_count_for_hands(requested_hands, orientations=2)
    scheduled_hands = seed_count * 2 * MATCH_LEN
    samples = []
    chip_delta = 0
    hands_played = 0
    early_bust_matches = 0
    hero_errors = 0
    opp_errors = 0
    durations = []
    seconds_per_hand = []
    hu_open_opportunities = 0
    hu_button_opens = 0
    river_commit_hands = 0
    river_commit_losing_hands = 0
    match_rows = []

    for k in range(seed_count):
        seed = seed_base + k
        for orientation, lineup in enumerate([
            {"hero": str(zip_path), "opp": str(opponent_path)},
            {"opp": str(opponent_path), "hero": str(zip_path)},
        ]):
            match_id = f"{case}_{target}_s{seed}_o{orientation}"
            start = time.time()
            result = run_match(match_id, lineup, n_hands=MATCH_LEN, verbose=False, seed=seed)
            wall = time.time() - start
            metrics = hand_samples_and_metrics(result, "hero", MATCH_LEN, two_player=True)
            samples.extend(metrics["samples"])
            chip_delta += int(result.get("chip_delta", {}).get("hero", 0))
            hands_played += int(result.get("n_hands") or 0)
            early_bust_matches += metrics["early_bust"]
            hero_errors += len(result.get("bot_errors", {}).get("hero", []) or [])
            opp_errors += len(result.get("bot_errors", {}).get("opp", []) or [])
            durations.append(float(result.get("duration_s") or wall))
            seconds_per_hand.append(metrics["seconds_per_hand"])
            hu_open_opportunities += metrics["hu_button_open_opportunities"]
            hu_button_opens += metrics["hu_button_opens"]
            river_commit_hands += metrics["river_commit_hands"]
            river_commit_losing_hands += metrics["river_commit_losing_hands"]
            match_rows.append({
                "seed": seed,
                "orientation": orientation,
                "hands": result.get("n_hands"),
                "chip_delta": result.get("chip_delta", {}).get("hero", 0),
                "duration_s": result.get("duration_s"),
                "hero_errors": len(result.get("bot_errors", {}).get("hero", []) or []),
                "opp_errors": len(result.get("bot_errors", {}).get("opp", []) or []),
            })

    ci_low, ci_high = bootstrap_ci(samples)
    actual_bb100 = (chip_delta / max(1, hands_played)) / BIG_BLIND * 100.0
    scheduled_bb100 = (chip_delta / max(1, scheduled_hands)) / BIG_BLIND * 100.0
    payload = {
        "target": target,
        "opponent_path": str(opponent_path),
        "requested_hands": requested_hands,
        "scheduled_hands": scheduled_hands,
        "actual_hands": hands_played,
        "scheduled_bb_per_100": scheduled_bb100,
        "actual_bb_per_100": actual_bb100,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "chip_delta": chip_delta,
        "early_bust_rate": early_bust_matches / max(1, len(match_rows)),
        "hero_errors": hero_errors,
        "opponent_errors": opp_errors,
        "duration_s": sum(durations),
        "p99_latency_s": None,
        "p99_latency_note": "engine run_match does not expose per-decision latency",
        "p99_match_seconds_per_hand_proxy": percentile(seconds_per_hand, 99),
        "hu_button_open_opportunities": hu_open_opportunities,
        "hu_button_opens": hu_button_opens,
        "hu_button_open_frequency": hu_button_opens / max(1, hu_open_opportunities),
        "river_trap_entries": None,
        "river_trap_note": "decision logs do not label traps; river losing commit is a proxy",
        "river_losing_commit_hands": river_commit_losing_hands,
        "river_commit_hands": river_commit_hands,
        "river_losing_commit_frequency": river_commit_losing_hands / max(1, river_commit_hands),
        "matches": match_rows,
    }
    write_log(f"{case}_h2h_{target}", json.dumps(payload, indent=2))
    return payload


def run_lineup(case: str, zip_path: Path, label: str, opponents: dict[str, Path], requested_hands: int, seed_base: int) -> dict:
    run_match = load_engine()
    missing = [str(path) for path in opponents.values() if not path.exists()]
    if missing:
        payload = {"target": label, "skipped": True, "reason": "missing opponents", "missing": missing}
        write_log(f"{case}_h2h_{label}", json.dumps(payload, indent=2))
        return payload

    seed_count = seed_count_for_hands(requested_hands, orientations=1)
    scheduled_hands = seed_count * MATCH_LEN
    lineup = {"hero": str(zip_path)}
    for name, path in opponents.items():
        lineup[name] = str(path)

    samples = []
    chip_delta = 0
    hands_played = 0
    early_bust_matches = 0
    hero_errors = 0
    durations = []
    seconds_per_hand = []
    river_commit_hands = 0
    river_commit_losing_hands = 0
    match_rows = []
    for k in range(seed_count):
        seed = seed_base + k
        match_id = f"{case}_{label}_s{seed}"
        start = time.time()
        result = run_match(match_id, lineup, n_hands=MATCH_LEN, verbose=False, seed=seed)
        wall = time.time() - start
        metrics = hand_samples_and_metrics(result, "hero", MATCH_LEN, two_player=False)
        samples.extend(metrics["samples"])
        chip_delta += int(result.get("chip_delta", {}).get("hero", 0))
        hands_played += int(result.get("n_hands") or 0)
        early_bust_matches += metrics["early_bust"]
        hero_errors += len(result.get("bot_errors", {}).get("hero", []) or [])
        durations.append(float(result.get("duration_s") or wall))
        seconds_per_hand.append(metrics["seconds_per_hand"])
        river_commit_hands += metrics["river_commit_hands"]
        river_commit_losing_hands += metrics["river_commit_losing_hands"]
        match_rows.append({
            "seed": seed,
            "hands": result.get("n_hands"),
            "chip_delta": result.get("chip_delta", {}).get("hero", 0),
            "duration_s": result.get("duration_s"),
            "hero_errors": len(result.get("bot_errors", {}).get("hero", []) or []),
        })

    ci_low, ci_high = bootstrap_ci(samples)
    actual_bb100 = (chip_delta / max(1, hands_played)) / BIG_BLIND * 100.0
    scheduled_bb100 = (chip_delta / max(1, scheduled_hands)) / BIG_BLIND * 100.0
    payload = {
        "target": label,
        "opponent_paths": {name: str(path) for name, path in opponents.items()},
        "requested_hands": requested_hands,
        "scheduled_hands": scheduled_hands,
        "actual_hands": hands_played,
        "scheduled_bb_per_100": scheduled_bb100,
        "actual_bb_per_100": actual_bb100,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "chip_delta": chip_delta,
        "early_bust_rate": early_bust_matches / max(1, len(match_rows)),
        "hero_errors": hero_errors,
        "duration_s": sum(durations),
        "p99_latency_s": None,
        "p99_latency_note": "engine run_match does not expose per-decision latency",
        "p99_match_seconds_per_hand_proxy": percentile(seconds_per_hand, 99),
        "hu_button_open_opportunities": None,
        "hu_button_opens": None,
        "hu_button_open_frequency": None,
        "river_trap_entries": None,
        "river_trap_note": "decision logs do not label traps; river losing commit is a proxy",
        "river_losing_commit_hands": river_commit_losing_hands,
        "river_commit_hands": river_commit_hands,
        "river_losing_commit_frequency": river_commit_losing_hands / max(1, river_commit_hands),
        "matches": match_rows,
    }
    write_log(f"{case}_h2h_{label}", json.dumps(payload, indent=2))
    return payload


def run_h2h_grid(results: dict, h2h_hands: int, ref_hands: int, seed_base: int) -> None:
    for case, candidate in results["candidates"].items():
        zip_path = Path(candidate["zip_path"])
        case_results = {}
        for target, path in PRIMARY_OPPONENTS.items():
            case_results[target] = run_two_player_h2h(case, zip_path, target, path, h2h_hands, seed_base)
            save_partial_h2h(results, case, case_results)
        for target, path in REFERENCE_OPPONENTS.items():
            case_results[target] = run_two_player_h2h(case, zip_path, target, path, ref_hands, seed_base)
            save_partial_h2h(results, case, case_results)
        case_results["ref_sixmax_mix"] = run_lineup(case, zip_path, "ref_sixmax_mix", REFERENCE_OPPONENTS, ref_hands, seed_base)
        save_partial_h2h(results, case, case_results)


def save_partial_h2h(results: dict, case: str, case_results: dict) -> None:
    results.setdefault("h2h", {})[case] = case_results
    save_results(results)


def verify_all(results: dict, smoke_hands: int, skip_smoke: bool) -> None:
    for case, candidate in results["candidates"].items():
        candidate["verification"] = verify_candidate(case, Path(candidate["zip_path"]), smoke_hands, skip_smoke)
        save_results(results)


def all_verification_passed(candidate: dict) -> bool:
    verification = candidate.get("verification", {})
    keys = ("leakage_audit", "import_audit", "edge_tests", "validator", "smoke")
    for key in keys:
        item = verification.get(key, {})
        if item.get("pass") is not True:
            return False
    return True


def decide(results: dict) -> dict:
    h2h = results.get("h2h", {})
    baseline = h2h.get("A0", {})
    evaluations = {}
    for case in VARIANTS:
        if case == "A0":
            continue
        case_results = h2h.get(case, {})
        toby_delta = None
        mehedi_delta = None
        regressions = []
        for target in ("toby_master", "mehedi_mybot"):
            if target in baseline and target in case_results:
                delta = case_results[target].get("actual_bb_per_100", 0.0) - baseline[target].get("actual_bb_per_100", 0.0)
                if target == "toby_master":
                    toby_delta = delta
                else:
                    mehedi_delta = delta
        for target, base_row in baseline.items():
            if target in ("toby_master", "mehedi_mybot"):
                continue
            row = case_results.get(target)
            if not row or row.get("skipped"):
                continue
            delta = row.get("actual_bb_per_100", 0.0) - base_row.get("actual_bb_per_100", 0.0)
            if delta <= REGRESSION_THRESHOLD_BB100:
                regressions.append({"target": target, "delta_bb_per_100": delta})
        improves_targets = (
            toby_delta is not None and mehedi_delta is not None
            and toby_delta >= IMPROVEMENT_THRESHOLD_BB100
            and mehedi_delta >= IMPROVEMENT_THRESHOLD_BB100
        )
        evaluations[case] = {
            "toby_delta_bb_per_100": toby_delta,
            "mehedi_delta_bb_per_100": mehedi_delta,
            "improves_toby_mehedi": improves_targets,
            "green_regressions": regressions,
            "verification_passed": all_verification_passed(results["candidates"].get(case, {})),
        }

    improving = [case for case, row in evaluations.items() if row["improves_toby_mehedi"]]
    if not improving:
        verdict = "NO_PREFLOP_ONLY_FIX"
        selected = None
    else:
        promotable = [
            case for case in improving
            if evaluations[case]["verification_passed"] and not evaluations[case]["green_regressions"]
        ]
        if promotable:
            verdict = "DEFENSIVE_PREFLOP_CANDIDATE"
            selected = max(
                promotable,
                key=lambda c: (evaluations[c]["toby_delta_bb_per_100"] or 0.0) + (evaluations[c]["mehedi_delta_bb_per_100"] or 0.0),
            )
        else:
            verdict = "NOT_PROMOTABLE"
            selected = max(
                improving,
                key=lambda c: (evaluations[c]["toby_delta_bb_per_100"] or 0.0) + (evaluations[c]["mehedi_delta_bb_per_100"] or 0.0),
            )
    return {
        "verdict": verdict,
        "selected_candidate": selected,
        "material_improvement_threshold_bb_per_100": IMPROVEMENT_THRESHOLD_BB100,
        "green_regression_threshold_bb_per_100": REGRESSION_THRESHOLD_BB100,
        "evaluations": evaluations,
    }


def metric_row(row: dict | None) -> str:
    if not row:
        return "not run"
    if row.get("skipped"):
        return "skipped"
    return (
        f"{row.get('actual_bb_per_100', 0.0):+.2f} "
        f"[{row.get('ci_low', 0.0):+.2f}, {row.get('ci_high', 0.0):+.2f}] "
        f"hands={row.get('actual_hands')}/{row.get('scheduled_hands')} "
        f"err={row.get('hero_errors')}"
    )


def write_report(results: dict) -> None:
    decision = decide(results)
    results["decision"] = decision
    results["protected_sha_after"] = protected_sha_payload()
    save_results(results)

    lines = [
        "# P3 Preflop Antecedent Grid Report",
        "",
        f"Verdict: {decision['verdict']}",
        f"Selected candidate: {decision['selected_candidate'] or 'none'}",
        "",
        "Protected artifacts:",
        f"- v_final.zip before/after: {results['protected_sha_before']['v_final']['sha256']} / {results['protected_sha_after']['v_final']['sha256']}",
        f"- best_green.zip before/after: {results['protected_sha_before']['best_green']['sha256']} / {results['protected_sha_after']['best_green']['sha256']}",
        "",
        "Decision rule:",
        f"- Material Toby/Mehedi improvement: actual bb/100 delta >= {IMPROVEMENT_THRESHOLD_BB100:.1f} on both targets vs A0.",
        f"- GREEN regression: non-target actual bb/100 delta <= {REGRESSION_THRESHOLD_BB100:.1f} vs A0.",
        "- Per-decision p99 latency is unavailable from the engine API; proxy seconds/hand is recorded in RESULTS.json.",
        "- River trap entries are not labelled in decision logs; river losing commit frequency is recorded as a proxy.",
        "",
        "Candidate zips:",
    ]
    for case, candidate in results.get("candidates", {}).items():
        lines.append(f"- {case}: {candidate['zip_path']} sha256={candidate['zip_sha256']}")

    lines.extend(["", "Verification:", "", "| candidate | leakage | import | edge | validator | smoke |", "|---|---:|---:|---:|---:|---:|"])
    for case, candidate in results.get("candidates", {}).items():
        v = candidate.get("verification", {})
        lines.append(
            f"| {case} | {v.get('leakage_audit', {}).get('pass')} | "
            f"{v.get('import_audit', {}).get('pass')} | {v.get('edge_tests', {}).get('pass')} | "
            f"{v.get('validator', {}).get('pass')} | {v.get('smoke', {}).get('pass')} |"
        )

    targets = list(PRIMARY_OPPONENTS.keys()) + list(REFERENCE_OPPONENTS.keys()) + ["ref_sixmax_mix"]
    lines.extend(["", "H2H actual bb/100 (95% bootstrap CI):", ""])
    for target in targets:
        lines.append(f"## {target}")
        lines.append("")
        lines.append("| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |")
        lines.append("|---|---:|---:|---:|---:|")
        for case in VARIANTS:
            row = results.get("h2h", {}).get(case, {}).get(target)
            if not row or row.get("skipped"):
                lines.append(f"| {case} | skipped | | | |")
                continue
            open_freq = row.get("hu_button_open_frequency")
            river_freq = row.get("river_losing_commit_frequency")
            lines.append(
                f"| {case} | {metric_row(row)} | "
                f"{'' if open_freq is None else f'{open_freq:.3f}'} | "
                f"{row.get('early_bust_rate', 0.0):.3f} | "
                f"{'' if river_freq is None else f'{river_freq:.3f}'} |"
            )
        lines.append("")

    lines.extend(["Decision details:", ""])
    for case, row in decision["evaluations"].items():
        lines.append(
            f"- {case}: Toby delta={row['toby_delta_bb_per_100']}, "
            f"Mehedi delta={row['mehedi_delta_bb_per_100']}, "
            f"improves={row['improves_toby_mehedi']}, regressions={row['green_regressions']}"
        )
    lines.extend(["", "Locked v_final.zip remains upload target unless human explicitly opens MODIFY gate."])
    (ARTIFACT_DIR / "PREFLOP_ANTECEDENT_GRID_REPORT.md").write_text("\n".join(lines) + "\n")

    status = [
        f"[P3 PREFLOP ANTECEDENT GRID {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}]",
        f"verdict={decision['verdict']} selected={decision['selected_candidate'] or 'none'}",
        f"protected_v_final_sha_before={results['protected_sha_before']['v_final']['sha256']}",
        f"protected_v_final_sha_after={results['protected_sha_after']['v_final']['sha256']}",
        f"protected_best_green_sha_before={results['protected_sha_before']['best_green']['sha256']}",
        f"protected_best_green_sha_after={results['protected_sha_after']['best_green']['sha256']}",
        f"results={ARTIFACT_DIR / 'RESULTS.json'}",
        f"report={ARTIFACT_DIR / 'PREFLOP_ANTECEDENT_GRID_REPORT.md'}",
        "Locked v_final.zip remains upload target unless human explicitly opens MODIFY gate.",
    ]
    (ARTIFACT_DIR / "STATUS_BLOCK.md").write_text("\n".join(status) + "\n")


def save_results(results: dict) -> None:
    (ARTIFACT_DIR / "RESULTS.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")


def load_or_init_results() -> dict:
    path = ARTIFACT_DIR / "RESULTS.json"
    if path.is_file():
        return json.loads(path.read_text())
    return {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "worktree": str(WORKTREE),
        "main_repo": str(MAIN_REPO),
        "base_branch": BASE_BRANCH,
        "locked_zip": str(LOCKED_ZIP),
        "expected_locked_sha": EXPECTED_LOCKED_SHA,
        "protected_sha_before": protected_sha_payload(),
        "commands_use_python": sys.executable,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--h2h", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--h2h-hands", type=int, default=1000)
    parser.add_argument("--ref-hands", type=int, default=600)
    parser.add_argument("--smoke-hands", type=int, default=200)
    parser.add_argument("--seed-base", type=int, default=142)
    parser.add_argument("--skip-smoke", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    assert_protected_shas()
    results = load_or_init_results()
    results["protected_sha_before"] = results.get("protected_sha_before") or protected_sha_payload()
    results["run_config"] = {
        "h2h_hands": args.h2h_hands,
        "ref_hands": args.ref_hands,
        "smoke_hands": args.smoke_hands,
        "seed_base": args.seed_base,
        "match_len": MATCH_LEN,
    }

    if args.all or args.build:
        build_candidate_zips(results)
    if args.all or args.verify:
        verify_all(results, args.smoke_hands, args.skip_smoke)
    if args.all or args.h2h:
        run_h2h_grid(results, args.h2h_hands, args.ref_hands, args.seed_base)
    if args.all or args.report:
        write_report(results)
    assert_protected_shas()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
