"""Artifact-bound gauntlet for the deployed Qualifier-II bot.

This tool is intentionally separate from tools/benchmark.py in this checkout:
benchmark.py is a historical stub and cannot target arbitrary zips. This
runner drives ext/fullhouse-engine/sandbox/match.py directly with the exact
submission zip under test, creates report-local synthetic opponent zips, and
records paired-seat match results plus direct hand-state probes.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
RUNNER = ENGINE_DIR / "sandbox" / "runner.py"
sys.path.insert(0, str(ENGINE_DIR))

from engine.game import BIG_BLIND, STARTING_STACK  # noqa: E402
from sandbox import match as match_mod  # noqa: E402


REFERENCE_BOTS = {
    "template": ENGINE_DIR / "bots" / "template",
    "aggressor": ENGINE_DIR / "bots" / "aggressor",
    "mathematician": ENGINE_DIR / "bots" / "mathematician",
    "shark": ENGINE_DIR / "bots" / "shark",
    "ref_bot_2": ENGINE_DIR / "bots" / "ref_bot_2",
}

SYNTHETIC_STYLES = (
    "all_in_maniac",
    "tight_passive",
    "loose_passive",
    "tight_aggressive",
    "loose_aggressive",
    "pot_odds_threshold",
    "river_value_threshold",
    "overfold_exploiter",
    "adaptive_overfold_exploiter",
)

VALID_ACTIONS = {"fold", "check", "call", "raise", "all_in"}

FORBIDDEN_MODULES = {
    "socket", "urllib", "urllib2", "urllib3", "requests", "httpx", "aiohttp",
    "http", "ftplib", "smtplib", "telnetlib", "xmlrpc",
    "subprocess", "multiprocessing", "pickle", "shelve", "threading",
    "ctypes", "runpy", "importlib",
}

BANNED_CALL_NAMES = {"__import__", "eval", "exec", "compile"}
BANNED_OS_FUNCS = {
    "system", "popen", "execv", "execve", "execvp", "execvpe",
    "execl", "execle", "execlp", "execlpe", "spawn", "spawnv", "spawnve",
    "spawnvp", "fork", "kill", "remove", "unlink", "rmdir", "removedirs",
    "chmod", "chown", "replace", "rename",
}


SYNTHETIC_BOT = r'''
STYLE = "__STYLE__"
RANKS = "23456789TJQKA"


def _rank_value(card):
    if not isinstance(card, str) or len(card) < 1:
        return -1
    return RANKS.find(card[0])


def _hand_tag(cards):
    if not isinstance(cards, list) or len(cards) != 2:
        return ""
    a, b = cards[0], cards[1]
    if not isinstance(a, str) or not isinstance(b, str) or len(a) < 2 or len(b) < 2:
        return ""
    ra, rb = a[0], b[0]
    sa, sb = a[1], b[1]
    if ra == rb:
        return ra + rb
    if _rank_value(a) < _rank_value(b):
        ra, rb, sa, sb = rb, ra, sb, sa
    return ra + rb + ("s" if sa == sb else "o")


def _premium(tag):
    return tag in {"AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs"}


def _broadway_or_pair(tag):
    if not tag:
        return False
    if len(tag) == 2 and tag[0] == tag[1]:
        return True
    return tag[0] in "AKQJ" or (len(tag) > 1 and tag[1] in "AKQJ")


def _tag_score(tag):
    if not tag:
        return 0
    if len(tag) == 2 and tag[0] == tag[1]:
        return 100 + max(0, RANKS.find(tag[0])) * 4
    hi = max(0, RANKS.find(tag[0]))
    lo = max(0, RANKS.find(tag[1])) if len(tag) > 1 else 0
    suited_bonus = 8 if tag.endswith("s") else 0
    connector_bonus = 4 if abs(hi - lo) <= 2 else 0
    return hi * 4 + lo + suited_bonus + connector_bonus


def _wide_pressure_open(tag):
    if not tag:
        return False
    if len(tag) == 2 and tag[0] == tag[1]:
        return RANKS.find(tag[0]) >= RANKS.find("4")
    return _tag_score(tag) >= 47 or tag[0] in "AKQJ" or tag[:2] in {"T9", "98", "87", "76", "65"}


def _deterministic_mix(state, modulo=10):
    token = str(state.get("hand_id", "")) + str(state.get("street", ""))
    for card in state.get("your_cards") or []:
        token += str(card)
    total = 0
    for ch in token:
        total += ord(ch)
    return total % max(1, int(modulo))


def _pressure_raise(state, frac=0.66):
    stack = int(state.get("your_stack") or 0)
    my_bet = int(state.get("your_bet_this_street") or 0)
    current = int(state.get("current_bet") or 0)
    min_raise = int(state.get("min_raise_to") or 0)
    pot = int(state.get("pot") or 0)
    if stack <= 0:
        return _fold_or_check(state)
    raw_target = current + max(100, int(pot * frac))
    commit_cap = my_bet + max(1, int(stack * 0.55))
    target = min(raw_target, commit_cap)
    if target < min_raise:
        if min_raise - my_bet >= int(stack * 0.55):
            return _call_or_check(state)
        target = min_raise
    return _raise_to(state, target)


def _rank_counts(state):
    cards = list(state.get("your_cards") or []) + list(state.get("community_cards") or [])
    ranks = [c[0] for c in cards if isinstance(c, str) and len(c) >= 2]
    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    return counts


def _has_pair_or_better(state):
    return any(count >= 2 for count in _rank_counts(state).values())


def _two_pair_or_better(state):
    counts = list(_rank_counts(state).values())
    return any(count >= 3 for count in counts) or sum(1 for count in counts if count >= 2) >= 2


def _raise_to(state, target):
    stack = int(state.get("your_stack") or 0)
    my_bet = int(state.get("your_bet_this_street") or 0)
    min_raise = int(state.get("min_raise_to") or 0)
    target = max(int(target), min_raise)
    if target - my_bet >= stack:
        return {"action": "all_in"}
    return {"action": "raise", "amount": target}


def _pot_raise(state, frac=0.75):
    pot = int(state.get("pot") or 0)
    current = int(state.get("current_bet") or 0)
    return _raise_to(state, current + max(100, int(pot * frac)))


def _call_or_check(state):
    return {"action": "check"} if state.get("can_check") else {"action": "call"}


def _fold_or_check(state):
    return {"action": "check"} if state.get("can_check") else {"action": "fold"}


_ADAPT_PRESSURE_ATTEMPTS = 0
_ADAPT_PRESSURE_FOLDS = 0
_ADAPT_PRESSURE_CONTINUES = 0
_ADAPT_SEEN_PRESSURES = {}


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _active_opponent_count(state):
    my_seat = _safe_int(state.get("seat_to_act"), -999)
    count = 0
    for player in state.get("players") or []:
        if not isinstance(player, dict):
            continue
        if _safe_int(player.get("seat"), -1) == my_seat:
            continue
        if player.get("is_folded") or str(player.get("state", "")).lower() == "folded":
            continue
        count += 1
    return max(1, count)


def _observe_adaptive_pressure(state):
    global _ADAPT_PRESSURE_ATTEMPTS, _ADAPT_PRESSURE_FOLDS, _ADAPT_PRESSURE_CONTINUES
    my_seat = _safe_int(state.get("seat_to_act"), -999)
    hand_id = str(state.get("hand_id", ""))
    log = state.get("action_log") or []
    for index, entry in enumerate(log):
        if not isinstance(entry, dict):
            continue
        if _safe_int(entry.get("seat"), -1) != my_seat:
            continue
        if str(entry.get("action", "")).lower() not in {"raise", "all_in"}:
            continue
        key = hand_id + ":" + str(index)
        if _ADAPT_SEEN_PRESSURES.get(key):
            continue
        response = ""
        for later in log[index + 1:]:
            if not isinstance(later, dict):
                continue
            later_seat = _safe_int(later.get("seat"), -1)
            later_action = str(later.get("action", "")).lower()
            if later_seat == my_seat:
                break
            if later_action == "fold":
                response = "fold"
                break
            if later_action in {"call", "raise", "all_in"}:
                response = "continue"
                break
        if not response:
            continue
        _ADAPT_SEEN_PRESSURES[key] = 1
        _ADAPT_PRESSURE_ATTEMPTS += 1
        if response == "fold":
            _ADAPT_PRESSURE_FOLDS += 1
        else:
            _ADAPT_PRESSURE_CONTINUES += 1


def _adaptive_fold_rate():
    return float(_ADAPT_PRESSURE_FOLDS + 2) / float(_ADAPT_PRESSURE_ATTEMPTS + 4)


def _made_rank(state):
    counts = list(_rank_counts(state).values())
    pairs = sum(1 for count in counts if count >= 2)
    if any(count >= 4 for count in counts):
        return 4
    if any(count >= 3 for count in counts):
        return 3
    if pairs >= 2:
        return 2
    if pairs == 1:
        return 1
    return 0


def _pressure_threshold(base, state):
    rate = _adaptive_fold_rate()
    threshold = int(base)
    if _ADAPT_PRESSURE_ATTEMPTS >= 12 and rate >= 0.66:
        threshold += 30
    elif _ADAPT_PRESSURE_ATTEMPTS >= 6 and rate >= 0.58:
        threshold += 18
    elif _ADAPT_PRESSURE_ATTEMPTS >= 10 and rate <= 0.44:
        threshold -= 18
    active = _active_opponent_count(state)
    if active > 1:
        threshold -= min(24, 8 * (active - 1))
    if threshold < 0:
        return 0
    if threshold > 96:
        return 96
    return threshold


def _adaptive_pressure(state, base, frac):
    if _deterministic_mix(state, 100) < _pressure_threshold(base, state):
        return _pressure_raise(state, frac)
    return {"action": "check"}


def decide(state):
    if not isinstance(state, dict):
        return {"action": "fold"}
    if state.get("type") == "warmup":
        return {"action": "check"}

    tag = _hand_tag(state.get("your_cards") or [])
    owed = int(state.get("amount_owed") or 0)
    pot = int(state.get("pot") or 0)
    stack = int(state.get("your_stack") or 0)
    street = state.get("street", "preflop")
    can_check = bool(state.get("can_check"))

    if STYLE == "all_in_maniac":
        return {"action": "all_in"} if stack > 0 else _call_or_check(state)

    if STYLE == "tight_passive":
        if _premium(tag):
            return _call_or_check(state)
        if can_check:
            return {"action": "check"}
        return {"action": "call"} if owed <= max(100, pot // 5) else {"action": "fold"}

    if STYLE == "loose_passive":
        if can_check:
            return {"action": "check"}
        return {"action": "call"} if owed <= max(100, int(0.55 * (pot + owed))) else {"action": "fold"}

    if STYLE == "tight_aggressive":
        if street == "preflop":
            if _premium(tag):
                return _pot_raise(state, 1.0)
            return _fold_or_check(state)
        if _has_pair_or_better(state):
            return _pot_raise(state, 0.8) if can_check or owed <= stack // 4 else {"action": "call"}
        return _fold_or_check(state)

    if STYLE == "loose_aggressive":
        if _broadway_or_pair(tag) or _has_pair_or_better(state) or can_check:
            return _pot_raise(state, 0.9)
        return {"action": "call"} if owed <= max(100, stack // 3) else {"action": "fold"}

    if STYLE == "pot_odds_threshold":
        if can_check:
            return {"action": "check"}
        threshold = owed / float(pot + owed) if pot + owed > 0 else 1.0
        return {"action": "call"} if threshold <= 0.30 else {"action": "fold"}

    if STYLE == "river_value_threshold":
        if street == "river" and _has_pair_or_better(state):
            if can_check:
                return _pot_raise(state, 0.66)
            return {"action": "call"} if owed <= max(100, int(0.45 * (pot + owed))) else {"action": "fold"}
        if can_check:
            return {"action": "check"}
        threshold = owed / float(pot + owed) if pot + owed > 0 else 1.0
        return {"action": "call"} if threshold <= 0.22 else {"action": "fold"}

    if STYLE == "overfold_exploiter":
        mix = _deterministic_mix(state, 10)
        threshold = owed / float(pot + owed) if pot + owed > 0 else 1.0
        made = _has_pair_or_better(state)

        if street == "preflop":
            if can_check:
                if _wide_pressure_open(tag) or mix <= 7:
                    return _pressure_raise(state, 0.80)
                return {"action": "check"}
            if _premium(tag):
                if owed <= max(300, int(stack * 0.18)) and mix <= 4:
                    return _pressure_raise(state, 0.85)
                return {"action": "call"} if owed <= max(600, int(stack * 0.24)) else {"action": "fold"}
            if _wide_pressure_open(tag) and threshold <= 0.26 and owed <= max(350, int(stack * 0.09)):
                return {"action": "call"}
            return {"action": "fold"}

        if owed > 0:
            # Bet-fold discipline: this bot pressures folds but does not pay off
            # counter-pressure with weak showdown value.
            if _two_pair_or_better(state) and threshold <= 0.18 and owed <= max(250, int(stack * 0.16)):
                return {"action": "call"}
            return _fold_or_check(state)

        if street == "flop":
            if made or mix <= 8:
                return _pressure_raise(state, 0.62)
            return {"action": "check"}
        if street == "turn":
            if made or mix <= 7:
                return _pressure_raise(state, 0.72)
            return {"action": "check"}
        if street == "river":
            if _two_pair_or_better(state) and mix <= 4:
                return _pressure_raise(state, 0.42)
            return {"action": "check"}

    if STYLE == "adaptive_overfold_exploiter":
        _observe_adaptive_pressure(state)
        price = owed / float(pot + owed) if pot + owed > 0 else 1.0
        made_rank = _made_rank(state)
        made = made_rank >= 1
        strong = made_rank >= 2
        fold_rate = _adaptive_fold_rate()
        multiway = _active_opponent_count(state) > 1

        if street == "preflop":
            if can_check:
                if _wide_pressure_open(tag) and (_deterministic_mix(state, 100) < _pressure_threshold(54 if not multiway else 34, state)):
                    return _pressure_raise(state, 0.70)
                return {"action": "check"}
            if _premium(tag):
                if owed <= max(300, int(stack * 0.16)) and _deterministic_mix(state, 100) < 38:
                    return _pressure_raise(state, 0.78)
                return {"action": "call"} if owed <= max(650, int(stack * 0.25)) else {"action": "fold"}
            if _wide_pressure_open(tag) and price <= 0.23 and owed <= max(300, int(stack * 0.075)):
                return {"action": "call"}
            return {"action": "fold"}

        if owed > 0:
            # Sharp-defensive response: keep pressure edge, but do not pay off
            # obvious value or stack off weak made hands after resistance.
            if made_rank >= 3 and price <= 0.38 and owed <= max(500, int(stack * 0.35)):
                return {"action": "call"}
            if made_rank >= 2 and price <= 0.27 and owed <= max(350, int(stack * 0.22)):
                return {"action": "call"}
            if made and price <= 0.11 and owed <= max(150, int(stack * 0.06)):
                return {"action": "call"}
            return _fold_or_check(state)

        if street == "flop":
            if strong:
                return _pressure_raise(state, 0.70)
            if made:
                return _pressure_raise(state, 0.58 if multiway else 0.64)
            base = 50 if multiway else 68
            frac = 0.55 if fold_rate < 0.60 else 0.68
            return _adaptive_pressure(state, base, frac)
        if street == "turn":
            if strong:
                return _pressure_raise(state, 0.76)
            if made and _deterministic_mix(state, 100) < _pressure_threshold(56 if not multiway else 34, state):
                return _pressure_raise(state, 0.68)
            base = 30 if multiway else 46
            frac = 0.62 if fold_rate < 0.62 else 0.78
            return _adaptive_pressure(state, base, frac)
        if street == "river":
            if strong:
                return _pressure_raise(state, 0.48)
            if (not multiway) and _ADAPT_PRESSURE_ATTEMPTS >= 12 and fold_rate >= 0.68 and _deterministic_mix(state, 100) < 16:
                return _pressure_raise(state, 0.34)
            return {"action": "check"}

    return _fold_or_check(state)
'''.lstrip()


@dataclass
class CommandResult:
    label: str
    command: list[str]
    returncode: int
    duration_s: float
    stdout_path: str
    stderr_path: str
    stdout_tail: str
    stderr_tail: str


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def tail(text: str, n: int = 3000) -> str:
    return text if len(text) <= n else text[-n:]


def run_command(label: str, command: list[str], out_dir: Path, timeout_s: int | None = None) -> CommandResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / f"{label}.stdout.log"
    stderr_path = out_dir / f"{label}.stderr.log"
    start = time.monotonic()
    try:
        res = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout_s)
        stdout = res.stdout
        stderr = res.stderr
        returncode = res.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_s}s"
        returncode = 124
    duration_s = round(time.monotonic() - start, 3)
    stdout_path.write_text(stdout)
    stderr_path.write_text(stderr)
    return CommandResult(
        label=label,
        command=command,
        returncode=returncode,
        duration_s=duration_s,
        stdout_path=rel(stdout_path),
        stderr_path=rel(stderr_path),
        stdout_tail=tail(stdout),
        stderr_tail=tail(stderr),
    )


def zip_inventory(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        infos = zf.infolist()
        names = [info.filename for info in infos]
        return {
            "path": rel(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "entry_count": len(infos),
            "entries": [
                {
                    "name": info.filename,
                    "file_size": info.file_size,
                    "compress_size": info.compress_size,
                    "is_dir": info.is_dir(),
                    "mode": (info.external_attr >> 16) & 0o777777,
                }
                for info in infos
            ],
            "root_bot_py": "bot.py" in names,
            "root_py_files": sorted(n for n in names if "/" not in n.strip("/") and n.endswith(".py")),
            "src_py_files": sorted(n for n in names if n.startswith("src/") and n.endswith(".py")),
            "data_entries": sorted(n for n in names if n.startswith("data/")),
            "py_in_data": sorted(n for n in names if n.startswith("data/") and n.endswith(".py")),
            "uncompressed_bytes": sum(info.file_size for info in infos),
        }


def safe_extract_zip(zip_path: Path, out_dir: Path) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            name = member.filename
            if name.startswith("/") or name.startswith("\\") or "\\" in name:
                raise ValueError(f"unsafe zip path: {name!r}")
            target = (out_dir / name).resolve()
            root = out_dir.resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"zip traversal path: {name!r}")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"zip symlink path: {name!r}")
        zf.extractall(out_dir)
    for p in out_dir.rglob("*"):
        if p.is_file():
            p.chmod(0o444)
        elif p.is_dir():
            p.chmod(0o555)
    out_dir.chmod(0o555)


def attr_chain(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def source_scan(extracted_dir: Path) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    imports: dict[str, list[str]] = {}
    data_refs: list[dict[str, Any]] = []
    py_files = sorted(extracted_dir.rglob("*.py"))
    for py in py_files:
        rel_path = rel(py)
        text = py.read_text()
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            issues.append({"path": rel_path, "kind": "syntax", "message": str(exc)})
            continue
        file_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    file_imports.append(alias.name)
                    if mod in FORBIDDEN_MODULES:
                        issues.append({"path": rel_path, "kind": "forbidden_import", "module": mod})
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                file_imports.append("from " + (node.module or ""))
                if mod in FORBIDDEN_MODULES:
                    issues.append({"path": rel_path, "kind": "forbidden_from", "module": mod})
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALL_NAMES:
                    issues.append({"path": rel_path, "kind": "forbidden_call", "call": node.func.id})
                if isinstance(node.func, ast.Attribute):
                    chain = attr_chain(node.func)
                    if chain.startswith("os.") and chain.split(".")[1] in BANNED_OS_FUNCS:
                        issues.append({"path": rel_path, "kind": "forbidden_call", "call": chain})
                    if chain.startswith("subprocess."):
                        issues.append({"path": rel_path, "kind": "forbidden_call", "call": chain})
                if isinstance(node.func, ast.Name) and node.func.id == "getattr":
                    if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "__builtins__":
                        issues.append({"path": rel_path, "kind": "forbidden_call", "call": "getattr(__builtins__)"})
            elif isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id == "__builtins__":
                    issues.append({"path": rel_path, "kind": "forbidden_call", "call": "__builtins__[]"})
        imports[rel_path] = sorted(set(file_imports))
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(token in line for token in ("np.load", ".npz", "BOT_DATA_DIR", "open(", "Path(")):
                data_refs.append({"path": rel_path, "line": lineno, "text": line.strip()})
    return {
        "python_files": [rel(p) for p in py_files],
        "imports": imports,
        "issues": issues,
        "forbidden_clean": not issues,
        "data_references": data_refs,
    }


def create_synthetic_opponents(out_dir: Path) -> dict[str, Path]:
    src_dir = out_dir / "synthetic_opponents" / "src"
    zip_dir = out_dir / "synthetic_opponents" / "zips"
    src_dir.mkdir(parents=True, exist_ok=True)
    zip_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    manifest: dict[str, Any] = {}
    for style in SYNTHETIC_STYLES:
        bot_dir = src_dir / style
        bot_dir.mkdir(parents=True, exist_ok=True)
        bot_py = bot_dir / "bot.py"
        bot_py.write_text(SYNTHETIC_BOT.replace("__STYLE__", style))
        zip_path = zip_dir / f"{style}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(bot_py, "bot.py")
        paths[style] = zip_path
        manifest[style] = zip_inventory(zip_path)
    write_json(out_dir / "synthetic_opponents" / "manifest.json", manifest)
    return paths


def bb100(chips: int | float, hands: int | float) -> float:
    return (float(chips) / BIG_BLIND) / (float(hands) / 100.0) if hands else 0.0


def bootstrap_ci(samples: list[dict[str, Any]], metric_hands_key: str, seed: int = 20260603) -> dict[str, float | None]:
    if not samples:
        return {"mean": None, "low": None, "high": None, "half_width": None}
    rng = random.Random(seed)
    n = len(samples)
    means: list[float] = []
    for _ in range(2000):
        chips = 0
        hands = 0
        for _ in range(n):
            s = samples[rng.randrange(n)]
            chips += int(s["hero_chip_delta"])
            hands += int(s[metric_hands_key])
        means.append(bb100(chips, hands))
    means.sort()
    chips_total = sum(int(s["hero_chip_delta"]) for s in samples)
    hands_total = sum(int(s[metric_hands_key]) for s in samples)
    low = means[int(0.025 * len(means))]
    high = means[int(0.975 * len(means))]
    mean = bb100(chips_total, hands_total)
    return {"mean": mean, "low": low, "high": high, "half_width": (high - low) / 2.0}


def hand_diagnostics(result: dict[str, Any], opponent: str, seed: int, orientation: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    prev_stack = STARTING_STACK
    for hand in result.get("hands", []):
        final_stack = int(hand.get("final_stacks", {}).get("hero", prev_stack))
        delta = final_stack - prev_stack
        prev_stack = final_stack
        if delta == 0:
            continue
        rows.append({
            "opponent": opponent,
            "seed": seed,
            "orientation": orientation,
            "hand_num": hand.get("hand_num"),
            "hand_id": hand.get("hand_id"),
            "hero_delta": delta,
            "street": hand.get("street"),
            "pot": hand.get("pot"),
            "community_cards": " ".join(hand.get("community_cards") or []),
            "showdown": hand.get("showdown"),
            "hero_cards": " ".join((hand.get("revealed_cards") or {}).get("hero", [])),
            "hand_strength": (hand.get("hand_strengths") or {}).get("hero"),
            "action_log_tail": json.dumps((hand.get("action_log") or [])[-12:], sort_keys=True),
        })
    return rows


def pressure_kind(street: str, first_aggression_on_street: bool, bot_id: str, flop_pressure_bots: set[str]) -> str:
    if street == "flop" and first_aggression_on_street:
        return "flop_cbet_or_probe"
    if street == "turn" and first_aggression_on_street and bot_id in flop_pressure_bots:
        return "turn_barrel"
    if street == "turn" and first_aggression_on_street:
        return "turn_probe"
    return "postflop_raise_pressure"


def pressure_bleed_diagnostics(result: dict[str, Any], opponent: str, seed: int, orientation: int) -> list[dict[str, Any]]:
    """Rows where hero folds flop/turn immediately after opponent pressure.

    The mechanism under test is over-folding under pressure, not generic loss.
    A row is emitted only when the engine event log shows a non-hero raise/all-in
    on flop or turn and the next relevant hero action on that street is fold.
    """
    rows: list[dict[str, Any]] = []
    prev_stack = STARTING_STACK
    for hand in result.get("hands", []):
        final_stack = int(hand.get("final_stacks", {}).get("hero", prev_stack))
        hero_delta = final_stack - prev_stack
        prev_stack = final_stack
        street_aggression_seen: dict[str, bool] = {}
        flop_pressure_bots: set[str] = set()
        last_pressure: dict[str, Any] | None = None
        for index, event in enumerate(hand.get("events") or []):
            if event.get("type") != "action":
                continue
            street = str(event.get("street") or "")
            bot_id = str(event.get("bot_id") or "")
            action = str(event.get("action") or "")
            if street in {"flop", "turn"} and bot_id != "hero" and action in {"raise", "all_in"}:
                first = not street_aggression_seen.get(street, False)
                street_aggression_seen[street] = True
                kind = pressure_kind(street, first, bot_id, flop_pressure_bots)
                if street == "flop":
                    flop_pressure_bots.add(bot_id)
                last_pressure = {
                    "street": street,
                    "pressure_kind": kind,
                    "pressure_bot": bot_id,
                    "pressure_action": action,
                    "pressure_amount": int(event.get("amount") or 0),
                    "pressure_pot_after": int(event.get("pot_after") or event.get("pot") or 0),
                    "pressure_event_index": index,
                }
                continue
            if street in {"flop", "turn"} and bot_id == "hero" and action == "fold" and last_pressure and last_pressure["street"] == street:
                rows.append({
                    "opponent": opponent,
                    "seed": seed,
                    "orientation": orientation,
                    "hand_num": hand.get("hand_num"),
                    "hand_id": hand.get("hand_id"),
                    **last_pressure,
                    "fold_event_index": index,
                    "fold_pot": int(event.get("pot") or 0),
                    "hero_delta": hero_delta,
                    "hero_chip_loss": max(0, -hero_delta),
                    "final_street": hand.get("street"),
                    "final_pot": hand.get("pot"),
                    "showdown": hand.get("showdown"),
                    "community_cards": " ".join(hand.get("community_cards") or []),
                    "action_log": json.dumps(hand.get("action_log") or [], sort_keys=True),
                })
                break
    return rows


def summarize_pressure_bleed(rows: list[dict[str, Any]], hands: int) -> dict[str, Any]:
    by_street: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for row in rows:
        by_street[str(row.get("street"))] = by_street.get(str(row.get("street")), 0) + 1
        by_kind[str(row.get("pressure_kind"))] = by_kind.get(str(row.get("pressure_kind")), 0) + 1
    chip_loss = sum(int(row.get("hero_chip_loss") or 0) for row in rows)
    net_delta = sum(int(row.get("hero_delta") or 0) for row in rows)
    surrendered_pot = sum(int(row.get("pressure_pot_after") or 0) for row in rows)
    return {
        "postflop_pressure_fold_count": len(rows),
        "postflop_pressure_fold_loss_chips": chip_loss,
        "postflop_pressure_fold_net_delta_chips": net_delta,
        "postflop_pressure_fold_loss_bb100": bb100(-chip_loss, hands),
        "pressure_pot_after_surrendered_chips": surrendered_pot,
        "pressure_pot_after_surrendered_bb100": bb100(-surrendered_pot, hands),
        "by_street": by_street,
        "by_pressure_kind": by_kind,
    }


def run_opponent_suite(hero_zip: Path, opponents: dict[str, Path], hands_per_opponent: int, match_len: int, seed_base: int) -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    all_diagnostics: list[dict[str, Any]] = []
    all_pressure_bleed: list[dict[str, Any]] = []
    n_seeds = max(1, math.ceil(hands_per_opponent / float(match_len * 2)))
    for name, opp_path in opponents.items():
        samples: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        pressure_rows: list[dict[str, Any]] = []
        for k in range(n_seeds):
            seed = seed_base + k
            orientations = [
                {"hero": str(hero_zip.resolve()), name: str(opp_path.resolve())},
                {name: str(opp_path.resolve()), "hero": str(hero_zip.resolve())},
            ]
            for orientation, paths in enumerate(orientations):
                match_id = f"deployed_{name}_s{seed}_o{orientation}"
                start = time.monotonic()
                try:
                    result = match_mod.run_match(match_id, paths, n_hands=match_len, verbose=False, seed=seed)
                    duration_s = round(time.monotonic() - start, 3)
                    hero_errors = list(result.get("bot_errors", {}).get("hero", []))
                    opp_errors = list(result.get("bot_errors", {}).get(name, []))
                    sample = {
                        "opponent": name,
                        "seed": seed,
                        "orientation": orientation,
                        "match_id": match_id,
                        "requested_hands": match_len,
                        "actual_hands": int(result.get("n_hands", 0)),
                        "duration_s": duration_s,
                        "hero_chip_delta": int(result.get("chip_delta", {}).get("hero", 0)),
                        "opponent_chip_delta": int(result.get("chip_delta", {}).get(name, 0)),
                        "hero_final_stack": int(result.get("final_stacks", {}).get("hero", 0)),
                        "opponent_final_stack": int(result.get("final_stacks", {}).get(name, 0)),
                        "hero_errors": hero_errors,
                        "opponent_errors": opp_errors,
                    }
                    samples.append(sample)
                    if hero_errors or opp_errors:
                        errors.append(sample)
                    all_diagnostics.extend(hand_diagnostics(result, name, seed, orientation))
                    pressure_rows.extend(pressure_bleed_diagnostics(result, name, seed, orientation))
                except Exception as exc:
                    errors.append({
                        "opponent": name,
                        "seed": seed,
                        "orientation": orientation,
                        "error": repr(exc),
                    })
        chips = sum(s["hero_chip_delta"] for s in samples)
        requested = sum(s["requested_hands"] for s in samples)
        actual = sum(s["actual_hands"] for s in samples)
        hero_error_count = sum(len(s.get("hero_errors", [])) for s in samples)
        opponent_error_count = sum(len(s.get("opponent_errors", [])) for s in samples)
        sample_chips = [s["hero_chip_delta"] for s in samples]
        summaries.append({
            "opponent": name,
            "opponent_path": rel(opp_path),
            "samples": samples,
            "sample_count": len(samples),
            "scheduled_hands": requested,
            "actual_hands": actual,
            "hero_chip_delta": chips,
            "scheduled_bb100": bb100(chips, requested),
            "actual_bb100": bb100(chips, actual),
            "scheduled_ci": bootstrap_ci(samples, "requested_hands", seed_base ^ len(name)),
            "actual_ci": bootstrap_ci(samples, "actual_hands", seed_base ^ (len(name) << 4)),
            "pressure_bleed": summarize_pressure_bleed(pressure_rows, actual),
            "hero_error_count": hero_error_count,
            "opponent_error_count": opponent_error_count,
            "mean_chip_delta_per_sample": statistics.mean(sample_chips) if sample_chips else None,
            "min_chip_delta_sample": min(sample_chips) if sample_chips else None,
            "max_chip_delta_sample": max(sample_chips) if sample_chips else None,
            "errors": errors,
        })
        all_pressure_bleed.extend(pressure_rows)
    all_diagnostics.sort(key=lambda r: int(r["hero_delta"]))
    all_pressure_bleed.sort(key=lambda r: (str(r.get("opponent")), int(r.get("seed") or 0), int(r.get("orientation") or 0), int(r.get("hand_num") or 0)))
    return {
        "summaries": summaries,
        "diagnostic_hands": all_diagnostics[:50],
        "pressure_bleed_hands": all_pressure_bleed,
    }


def base_players(n: int, hero_stack: int, villain_stack: int = 10000) -> list[dict[str, Any]]:
    players = []
    for seat in range(n):
        players.append({
            "seat": seat,
            "bot_id": "hero" if seat == 0 else f"villain_{seat}",
            "stack": hero_stack if seat == 0 else villain_stack,
            "state": "active",
            "is_folded": False,
            "is_all_in": False,
            "bet_this_street": 0,
            "hole_cards": None,
        })
    return players


def probe_states() -> list[dict[str, Any]]:
    return [
        {
            "name": "warmup_exception",
            "kind": "warmup",
            "state": {"type": "warmup"},
            "description": "Runner warmup call should return ok without warmup_exception.",
        },
        {
            "name": "near_drawing_dead_stackoff",
            "state": {
                "type": "action_request", "hand_id": "probe_dead_river", "street": "river",
                "seat_to_act": 0, "pot": 7000,
                "community_cards": ["Kh", "Qs", "Tc", "Td", "Ah"],
                "current_bet": 3500, "min_raise_to": 7000, "amount_owed": 3000,
                "can_check": False, "your_cards": ["2s", "Kd"], "your_stack": 6000,
                "your_bet_this_street": 500, "players": base_players(2, 6000),
                "action_log": [{"seat": 1, "action": "raise", "amount": 3500}],
            },
            "description": "Two pair on paired Broadway river facing a large bet; known Round-1 class.",
        },
        {
            "name": "dominated_underboat_near_dead_commitment",
            "state": {
                "type": "action_request", "hand_id": "probe_underboat", "street": "river",
                "seat_to_act": 0, "pot": 17800,
                "community_cards": ["Kd", "Ks", "Qs", "Qd", "5c"],
                "current_bet": 8900, "min_raise_to": 17800, "amount_owed": 8900,
                "can_check": False, "your_cards": ["Qc", "9h"], "your_stack": 9100,
                "your_bet_this_street": 0,
                "players": [
                    {"seat": 0, "bot_id": "hero", "stack": 9100, "state": "active", "is_folded": False, "is_all_in": False, "bet_this_street": 0, "hole_cards": None},
                    {"seat": 1, "bot_id": "villain_1", "stack": 1100, "state": "active", "is_folded": False, "is_all_in": False, "bet_this_street": 8900, "hole_cards": None},
                    {"seat": 2, "bot_id": "villain_2", "stack": 0, "state": "folded", "is_folded": True, "is_all_in": False, "bet_this_street": 0, "hole_cards": None},
                    {"seat": 3, "bot_id": "villain_3", "stack": 0, "state": "folded", "is_folded": True, "is_all_in": False, "bet_this_street": 0, "hole_cards": None},
                    {"seat": 4, "bot_id": "villain_4", "stack": 0, "state": "folded", "is_folded": True, "is_all_in": False, "bet_this_street": 0, "hole_cards": None},
                    {"seat": 5, "bot_id": "villain_5", "stack": 0, "state": "folded", "is_folded": True, "is_all_in": False, "bet_this_street": 0, "hole_cards": None},
                ],
                "action_log": [{"seat": 1, "action": "raise", "amount": 8900}],
            },
            "description": "Under-boat/full-house cooler class from the extended edge harness; large commit is unsafe.",
        },
        {
            "name": "multiway_wet_board",
            "state": {
                "type": "action_request", "hand_id": "probe_multiway_wet", "street": "flop",
                "seat_to_act": 0, "pot": 3600,
                "community_cards": ["Jh", "Th", "9h"],
                "current_bet": 1200, "min_raise_to": 2400, "amount_owed": 1200,
                "can_check": False, "your_cards": ["Ah", "Qs"], "your_stack": 8200,
                "your_bet_this_street": 0, "players": base_players(4, 8200),
                "action_log": [{"seat": 1, "action": "raise", "amount": 1200}],
            },
            "description": "Four-way wet monotone connected flop; tests HU-biased opponent seat selection.",
        },
        {
            "name": "river_facing_large_bet",
            "state": {
                "type": "action_request", "hand_id": "probe_river_big_bet", "street": "river",
                "seat_to_act": 0, "pot": 4200,
                "community_cards": ["7s", "Td", "2h", "Kc", "5d"],
                "current_bet": 3200, "min_raise_to": 6400, "amount_owed": 3200,
                "can_check": False, "your_cards": ["2c", "3d"], "your_stack": 6000,
                "your_bet_this_street": 0, "players": base_players(2, 6000),
                "action_log": [{"seat": 1, "action": "raise", "amount": 3200}],
            },
            "description": "Weak pair facing large river bet.",
        },
        {
            "name": "turn_jam_poor_pot_odds",
            "state": {
                "type": "action_request", "hand_id": "probe_turn_jam", "street": "turn",
                "seat_to_act": 0, "pot": 3000,
                "community_cards": ["8d", "9d", "Ts", "2c"],
                "current_bet": 8000, "min_raise_to": 16000, "amount_owed": 8000,
                "can_check": False, "your_cards": ["Ah", "Kc"], "your_stack": 8000,
                "your_bet_this_street": 0, "players": base_players(2, 8000),
                "action_log": [{"seat": 1, "action": "all_in", "amount": 8000}],
            },
            "description": "Turn jam with overcards/no made hand and poor immediate pot odds.",
        },
        {
            "name": "blind_defense_vs_3bet",
            "state": {
                "type": "action_request", "hand_id": "probe_bb_3bet", "street": "preflop",
                "seat_to_act": 0, "pot": 1500,
                "community_cards": [], "current_bet": 900, "min_raise_to": 1700,
                "amount_owed": 800, "can_check": False, "your_cards": ["Kc", "7d"],
                "your_stack": 9100, "your_bet_this_street": 100, "players": base_players(6, 9100),
                "action_log": [
                    {"seat": 0, "action": "big_blind", "amount": 100},
                    {"seat": 2, "action": "raise", "amount": 300},
                    {"seat": 4, "action": "raise", "amount": 900},
                ],
            },
            "description": "BB with dominated Kx facing a 3-bet.",
        },
        {
            "name": "all_in_side_pot_state",
            "state": {
                "type": "action_request", "hand_id": "probe_sidepot", "street": "turn",
                "seat_to_act": 0, "pot": 9800,
                "community_cards": ["As", "7d", "2c", "9h"],
                "current_bet": 3000, "min_raise_to": 6000, "amount_owed": 2000,
                "can_check": False, "your_cards": ["Ah", "Ad"], "your_stack": 5000,
                "your_bet_this_street": 1000,
                "players": [
                    {"seat": 0, "bot_id": "hero", "stack": 5000, "state": "active", "is_folded": False, "is_all_in": False, "bet_this_street": 1000, "hole_cards": None},
                    {"seat": 1, "bot_id": "short_allin", "stack": 0, "state": "all_in", "is_folded": False, "is_all_in": True, "bet_this_street": 3000, "hole_cards": None},
                    {"seat": 2, "bot_id": "covering_villain", "stack": 11000, "state": "active", "is_folded": False, "is_all_in": False, "bet_this_street": 3000, "hole_cards": None},
                ],
                "action_log": [{"seat": 1, "action": "all_in", "amount": 3000}, {"seat": 2, "action": "call", "amount": 3000}],
            },
            "description": "Side-pot style state with one all-in player and one active covering bettor.",
        },
        {
            "name": "contradictory_legal_actions",
            "state": {
                "type": "action_request", "hand_id": "probe_contradictory", "street": "flop",
                "seat_to_act": 0, "pot": 1800,
                "community_cards": ["4s", "4d", "Jc"], "current_bet": 600,
                "min_raise_to": 1200, "amount_owed": 600, "can_check": True,
                "your_cards": ["Qh", "Ts"], "your_stack": 9400,
                "your_bet_this_street": 0, "players": base_players(2, 9400),
                "action_log": [{"seat": 1, "action": "raise", "amount": 600}],
            },
            "description": "Contradictory state says can_check=True while amount_owed/current_bet are nonzero.",
        },
        {
            "name": "raise_amount_min_max_ambiguity",
            "state": {
                "type": "action_request", "hand_id": "probe_raise_bounds", "street": "preflop",
                "seat_to_act": 0, "pot": 19000,
                "community_cards": [], "current_bet": 9500, "min_raise_to": 19000,
                "amount_owed": 9400, "can_check": False, "your_cards": ["As", "Ad"],
                "your_stack": 9400, "your_bet_this_street": 100, "players": base_players(2, 9400),
                "action_log": [{"seat": 0, "action": "small_blind", "amount": 50}, {"seat": 1, "action": "big_blind", "amount": 100}, {"seat": 1, "action": "raise", "amount": 9500}],
            },
            "description": "Premium hand where min_raise_to exceeds remaining stack; should use all_in/call, not illegal raise.",
        },
        {
            "name": "timeout_expensive_equity_branch",
            "repeat": 30,
            "state": {
                "type": "action_request", "hand_id": "probe_expensive", "street": "flop",
                "seat_to_act": 0, "pot": 5000,
                "community_cards": ["Qd", "Jd", "8c"], "current_bet": 2500,
                "min_raise_to": 5000, "amount_owed": 2500, "can_check": False,
                "your_cards": ["Ad", "Td"], "your_stack": 9000, "your_bet_this_street": 0,
                "players": base_players(2, 9000), "action_log": [{"seat": 1, "action": "raise", "amount": 2500}],
            },
            "description": "Repeated flop facing-bet branch forces hand_strength plus equity_vs_range calls.",
        },
    ]


def action_shape_ok(action: Any) -> bool:
    if not isinstance(action, dict):
        return False
    act = str(action.get("action", "")).lower()
    if act not in VALID_ACTIONS:
        return False
    if act == "raise" and "amount" not in action:
        return False
    return True


def run_probe(extracted_dir: Path, probe: dict[str, Any], python: str) -> dict[str, Any]:
    bot_py = extracted_dir / "bot.py"
    env = {
        **os.environ,
        "BOT_PATH": str(bot_py),
        "BOT_DATA_DIR": str(extracted_dir / "data"),
        "ACTION_TIMEOUT": "2",
    }
    proc = subprocess.Popen(
        [python, "-u", str(RUNNER)],
        cwd=ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    def send(obj: dict[str, Any]) -> tuple[dict[str, Any] | None, float, str | None]:
        assert proc.stdin is not None and proc.stdout is not None
        started = time.perf_counter()
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if not line:
            return None, elapsed_ms, "runner produced no stdout"
        try:
            return json.loads(line), elapsed_ms, None
        except json.JSONDecodeError as exc:
            return None, elapsed_ms, f"bad runner json: {exc}: {line[:200]!r}"

    actions: list[dict[str, Any]] = []
    latencies: list[float] = []
    errors: list[str] = []
    try:
        if probe.get("kind") == "warmup":
            action, latency, error = send(probe["state"])
            if action is not None:
                actions.append(action)
            latencies.append(latency)
            if error:
                errors.append(error)
        else:
            warmup, _, warm_error = send({"type": "warmup"})
            if warm_error:
                errors.append("warmup_before_probe: " + warm_error)
            elif isinstance(warmup, dict) and warmup.get("error"):
                errors.append("warmup_before_probe: " + str(warmup))
            repeat = int(probe.get("repeat", 1))
            for _ in range(repeat):
                action, latency, error = send(probe["state"])
                if action is not None:
                    actions.append(action)
                latencies.append(latency)
                if error:
                    errors.append(error)
    finally:
        if proc.stdin is not None:
            try:
                proc.stdin.close()
            except Exception:
                pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        stderr = proc.stderr.read() if proc.stderr is not None else ""

    return {
        "name": probe["name"],
        "description": probe.get("description"),
        "repeat": int(probe.get("repeat", 1)),
        "actions": actions,
        "unique_actions": sorted({json.dumps(a, sort_keys=True) for a in actions}),
        "shape_ok": all(action_shape_ok(a) or probe.get("kind") == "warmup" for a in actions),
        "latency_ms": {
            "min": min(latencies) if latencies else None,
            "mean": statistics.mean(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
        },
        "errors": errors,
        "runner_stderr_tail": tail(stderr, 1500),
    }


def run_probes(extracted_dir: Path, python: str) -> list[dict[str, Any]]:
    return [run_probe(extracted_dir, probe, python) for probe in probe_states()]


def write_diagnostic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "opponent", "seed", "orientation", "hand_num", "hand_id", "hero_delta",
        "street", "pot", "community_cards", "showdown", "hero_cards",
        "hand_strength", "action_log_tail",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def write_pressure_bleed_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "opponent", "seed", "orientation", "hand_num", "hand_id", "street",
        "pressure_kind", "pressure_bot", "pressure_action", "pressure_amount",
        "pressure_pot_after", "pressure_event_index", "fold_event_index",
        "fold_pot", "hero_delta", "hero_chip_loss", "final_street",
        "final_pot", "showdown", "community_cards", "action_log",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot", type=Path, default=ROOT / "submissions" / "v_qual2_ship_d54640e0.zip")
    parser.add_argument("--baseline", type=Path, default=ROOT / "submissions" / "v_final.zip")
    parser.add_argument("--outdir", type=Path, default=ROOT / "consult" / "artifacts" / "2026-06-03-deployed-gauntlet")
    parser.add_argument("--extracted-dir", type=Path, default=None)
    parser.add_argument("--hands-per-opponent", type=int, default=800)
    parser.add_argument("--match-len", type=int, default=200)
    parser.add_argument("--seed-base", type=int, default=42)
    parser.add_argument("--opponents", nargs="*", default=None, help="Optional opponent names to run; default runs the full suite.")
    parser.add_argument("--python", default=str(ROOT / ".venv" / "bin" / "python"))
    parser.add_argument("--skip-matches", action="store_true")
    parser.add_argument("--skip-probes", action="store_true")
    args = parser.parse_args()

    bot = args.bot if args.bot.is_absolute() else ROOT / args.bot
    baseline = args.baseline if args.baseline.is_absolute() else ROOT / args.baseline
    outdir = args.outdir if args.outdir.is_absolute() else ROOT / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    logs_dir = outdir / "logs"
    results_dir = outdir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    extracted_dir = args.extracted_dir
    if extracted_dir is None:
        extracted_dir = outdir / "extracted" / bot.stem
    elif not extracted_dir.is_absolute():
        extracted_dir = ROOT / extracted_dir
    safe_extract_zip(bot, extracted_dir)

    started_at = now_iso()
    submission_zips = sorted((ROOT / "submissions").glob("*.zip"))
    inventories = [zip_inventory(p) for p in submission_zips]
    write_json(results_dir / "submission_zip_inventory.json", inventories)
    source_audit = source_scan(extracted_dir)
    write_json(results_dir / "source_audit.json", source_audit)

    commands = [
        run_command("import_audit_canonical_src", [args.python, "tools/import_audit.py"], logs_dir, timeout_s=120),
        run_command("edge_cases_canonical_src", [args.python, "-m", "pytest", "tests/edge_cases", "-x"], logs_dir, timeout_s=120),
        run_command("validator_deployed_zip", [args.python, "ext/fullhouse-engine/sandbox/validator.py", rel(bot), "--json"], logs_dir, timeout_s=120),
        run_command("audit_strategy_leakage_deployed_zip", [args.python, "tools/audit_strategy_leakage.py", "--zip", rel(bot)], logs_dir, timeout_s=120),
    ]
    write_json(results_dir / "verification_commands.json", [c.__dict__ for c in commands])

    synthetic_paths = create_synthetic_opponents(outdir)
    opponents = {**REFERENCE_BOTS, **synthetic_paths}
    if args.opponents:
        missing = [name for name in args.opponents if name not in opponents]
        if missing:
            parser.error(f"unknown --opponents values: {', '.join(missing)}")
        opponents = {name: opponents[name] for name in args.opponents}
    match_results: dict[str, Any] = {"summaries": [], "diagnostic_hands": [], "pressure_bleed_hands": []}
    if not args.skip_matches:
        match_results = run_opponent_suite(bot, opponents, args.hands_per_opponent, args.match_len, args.seed_base)
    write_json(results_dir / "match_results.json", match_results)
    write_diagnostic_csv(results_dir / "diagnostic_hands.csv", match_results.get("diagnostic_hands", []))
    write_pressure_bleed_csv(results_dir / "pressure_bleed_hands.csv", match_results.get("pressure_bleed_hands", []))

    probes: list[dict[str, Any]] = []
    if not args.skip_probes:
        probes = run_probes(extracted_dir, args.python)
    write_json(results_dir / "probe_results.json", probes)

    combined = {
        "started_at": started_at,
        "bot": zip_inventory(bot),
        "baseline": zip_inventory(baseline) if baseline.is_file() else None,
        "extracted_dir": rel(extracted_dir),
        "source_audit": source_audit,
        "verification_commands": [c.__dict__ for c in commands],
        "synthetic_opponents": {name: rel(path) for name, path in synthetic_paths.items()},
        "match_config": {
            "hands_per_opponent": args.hands_per_opponent,
            "match_len": args.match_len,
            "seed_base": args.seed_base,
            "opponents": list(opponents),
            "paired_orientations": True,
        },
        "match_results": match_results,
        "probe_results": probes,
    }
    write_json(results_dir / "deployed_gauntlet_results.json", combined)

    print(json.dumps({
        "ok": True,
        "results": rel(results_dir / "deployed_gauntlet_results.json"),
        "bot_sha256": combined["bot"]["sha256"],
        "opponents": len(opponents),
        "probes": len(probes),
        "match_summaries": len(match_results.get("summaries", [])),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
