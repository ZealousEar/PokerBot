"""Reusable edge-case harness for local and packaged PokerBot builds.

The tests in this repo need to exercise three subjects without editing them:

* the canonical source tree in ``src/``;
* the preserved deployed zip in ``submissions/``;
* any future candidate zip supplied through ``POKERBOT_CANDIDATE_ZIP(S)``.

This module talks to bots through the Fullhouse runner process instead of
importing candidate code into pytest. That keeps module caches isolated and
lets the bot run under the sandbox-matched Python 3.10 venv even when the host
``pytest`` entrypoint is a different Python.
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
RUNNER_PATH = ROOT / "ext" / "fullhouse-engine" / "sandbox" / "runner.py"
DEPLOYED_ZIP = ROOT / "submissions" / "v_final.zip"

_VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
RUNNER_PYTHON = Path(os.environ.get("POKERBOT_RUNNER_PYTHON", _VENV_PYTHON if _VENV_PYTHON.exists() else sys.executable))

VALID_ACTIONS = {"fold", "check", "call", "raise", "all_in"}

MAX_PACKAGE_SIZE_BYTES = 250 * 1024 * 1024
MAX_DATA_SIZE_BYTES = 200 * 1024 * 1024
MAX_BOT_PY_SIZE_BYTES = 5 * 1024 * 1024

FORBIDDEN_MODULES = {
    "socket", "urllib", "urllib2", "urllib3", "requests", "httpx", "aiohttp",
    "http", "ftplib", "smtplib", "telnetlib", "xmlrpc",
    "subprocess", "multiprocessing",
    "pickle", "shelve",
    "threading",
    "ctypes",
    "runpy", "importlib",
}

BANNED_CALL_NAMES = {"__import__", "eval", "exec", "compile"}
BANNED_OS_FUNCS = {
    "system", "popen", "execv", "execve", "execvp", "execvpe",
    "execl", "execle", "execlp", "execlpe",
    "spawn", "spawnv", "spawnve", "spawnvp",
    "fork", "kill", "remove", "unlink", "rmdir", "removedirs",
    "chmod", "chown", "replace", "rename",
}

SOURCE_SHIM = '''"""Temporary test shim for canonical src/ bot."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from src.bot import decide as _impl


def decide(game_state):
    return _impl(game_state)
'''


@dataclass(frozen=True)
class BotSpec:
    name: str
    path: Path
    lineage: str


@dataclass(frozen=True)
class RunnerResult:
    payload: dict
    elapsed_s: float


def _coerce_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _copy_py_tree(src_dir: Path, dst_dir: Path) -> None:
    for src_file in sorted(src_dir.rglob("*.py")):
        if "__pycache__" in src_file.parts:
            continue
        rel = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        dst_file.write_text(src_file.read_text())


def make_source_submission_dir(target: Path) -> Path:
    """Create a temp submission directory from canonical ``src/`` only."""
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    (target / "bot.py").write_text(SOURCE_SHIM)
    _copy_py_tree(ROOT / "src", target / "src")
    data_dir = target / "data"
    data_dir.mkdir()
    (data_dir / ".gitkeep").write_text("")
    return target


def candidate_zip_paths(include_deployed: bool = True) -> list[BotSpec]:
    """Return deployed plus env-specified candidate zips that exist."""
    specs: list[BotSpec] = []
    seen: set[Path] = set()
    if include_deployed and DEPLOYED_ZIP.exists():
        specs.append(BotSpec("finals_submission", DEPLOYED_ZIP, "DEPLOYED"))
        seen.add(DEPLOYED_ZIP.resolve())

    env_values = []
    for key in ("POKERBOT_CANDIDATE_ZIP", "POKERBOT_CANDIDATE_ZIPS"):
        raw = os.environ.get(key)
        if raw:
            env_values.extend(part for part in raw.split(os.pathsep) if part)

    for idx, raw_path in enumerate(env_values):
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        resolved = path.resolve()
        if resolved in seen or not path.exists():
            continue
        specs.append(BotSpec(f"candidate_zip_{idx}", path, "CANDIDATE"))
        seen.add(resolved)
    return specs


def _safe_extract_zip(zip_path: Path, tmpdir: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            name = member.filename
            if name.startswith(("/", "\\")):
                raise ValueError(f"unsafe absolute zip path: {name!r}")
            norm = os.path.normpath(str(tmpdir / name))
            if not norm.startswith(str(tmpdir) + os.sep) and norm != str(tmpdir):
                raise ValueError(f"unsafe traversal zip path: {name!r}")
            mode = member.external_attr >> 16
            if stat.S_IFMT(mode) == stat.S_IFLNK:
                raise ValueError(f"symlink in zip: {name!r}")
        zf.extractall(tmpdir)
    if not (tmpdir / "bot.py").is_file():
        raise ValueError("zip archive must contain bot.py at the root")
    return tmpdir


class RunnerClient:
    """Persistent runner.py process for one bot subject."""

    def __init__(self, bot_path: Path, action_timeout_s: int = 2, warmup_timeout_s: int = 30):
        self.bot_path = Path(bot_path)
        self.action_timeout_s = action_timeout_s
        self.warmup_timeout_s = warmup_timeout_s
        self._tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self._mount_src = self._prepare_mount()
        env = {
            **os.environ,
            "BOT_PATH": str(self._mount_src / "bot.py"),
            "BOT_DATA_DIR": str(self._mount_src / "data"),
            "ACTION_TIMEOUT": str(action_timeout_s),
            "WARMUP_TIMEOUT": str(warmup_timeout_s),
        }
        self._proc = subprocess.Popen(
            [str(RUNNER_PYTHON), "-u", str(RUNNER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

    def _prepare_mount(self) -> Path:
        if self.bot_path.is_dir():
            if not (self.bot_path / "bot.py").is_file():
                raise ValueError(f"bot directory lacks bot.py: {self.bot_path}")
            return self.bot_path
        if self.bot_path.suffix == ".zip":
            self._tmpdir = tempfile.TemporaryDirectory(prefix="pokerbot_edge_zip_")
            return _safe_extract_zip(self.bot_path, Path(self._tmpdir.name))
        if self.bot_path.suffix == ".py" and self.bot_path.is_file():
            self._tmpdir = tempfile.TemporaryDirectory(prefix="pokerbot_edge_py_")
            mount = Path(self._tmpdir.name)
            shutil.copy(self.bot_path, mount / "bot.py")
            return mount
        raise ValueError(f"unsupported bot path: {self.bot_path}")

    def send(self, state: dict) -> RunnerResult:
        if self._proc.stdin is None or self._proc.stdout is None:
            raise RuntimeError("runner process is not connected")
        start = time.monotonic()
        self._proc.stdin.write(json.dumps(state) + "\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        elapsed = time.monotonic() - start
        if not line:
            stderr = self._proc.stderr.read() if self._proc.stderr is not None else ""
            raise RuntimeError(f"runner process produced no output; stderr={stderr!r}")
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"runner produced invalid JSON: {line!r}") from exc
        return RunnerResult(payload=payload, elapsed_s=elapsed)

    def close(self) -> None:
        try:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
        except BrokenPipeError:
            pass
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._proc.kill()
        if self._tmpdir is not None:
            self._tmpdir.cleanup()

    def __enter__(self) -> "RunnerClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def check_action_contract(action: dict, state: dict, *, enforce_stack_all_in: bool = False) -> list[str]:
    """Return runner-safety issues for an action in a specific state."""
    issues: list[str] = []
    if not isinstance(action, dict):
        return [f"action_not_dict:{type(action).__name__}"]
    raw_action = action.get("action")
    if raw_action is None:
        return ["missing_action"]
    verb = str(raw_action).lower().strip()
    if verb not in VALID_ACTIONS:
        issues.append(f"invalid_action:{raw_action!r}")
        return issues

    amount_owed = _coerce_int(state.get("amount_owed"), 0)
    can_check = bool(state.get("can_check"))
    if verb == "check" and amount_owed > 0 and not can_check:
        issues.append("check_facing_bet")

    if verb == "raise":
        if "amount" not in action:
            issues.append("raise_missing_amount")
            return issues
        amount = _coerce_int(action.get("amount"), -1)
        min_raise_to = _coerce_int(state.get("min_raise_to"), 0)
        current_bet = _coerce_int(state.get("current_bet"), 0)
        your_bet = _coerce_int(state.get("your_bet_this_street"), 0)
        stack = _coerce_int(state.get("your_stack"), 0)
        cap = stack + your_bet
        if amount < 0:
            issues.append("raise_amount_not_int")
        if min_raise_to and amount < min_raise_to:
            issues.append(f"raise_below_min:{amount}<min_raise_to:{min_raise_to}")
        if amount <= max(current_bet, your_bet):
            issues.append(f"raise_equal_or_below_call:{amount}<=current_bet_or_bet")
        if cap and amount > cap:
            issues.append(f"raise_above_stack_cap:{amount}>cap:{cap}")
        if enforce_stack_all_in and cap and amount == cap:
            issues.append("raise_to_stack_cap_should_be_all_in")
    return issues


def commitment_fraction(action: dict, state: dict) -> float:
    """Approximate fraction of current stack committed by this action."""
    if not isinstance(action, dict):
        return 0.0
    stack = max(_coerce_int(state.get("your_stack"), 0), 1)
    your_bet = _coerce_int(state.get("your_bet_this_street"), 0)
    verb = str(action.get("action", "")).lower().strip()
    if verb == "all_in":
        return 1.0
    if verb == "call":
        return max(_coerce_int(state.get("amount_owed"), 0), 0) / stack
    if verb == "raise":
        amount = _coerce_int(action.get("amount"), your_bet)
        return max(amount - your_bet, 0) / stack
    return 0.0


def is_large_commit(action: dict, state: dict, threshold: float = 0.40) -> bool:
    return commitment_fraction(action, state) >= threshold


def _player(seat: int, stack: int = 10000, bet: int = 0, *, all_in: bool = False, folded: bool = False) -> dict:
    return {
        "seat": seat,
        "bot_id": f"seat_{seat}",
        "stack": stack,
        "state": "all_in" if all_in else ("folded" if folded else "active"),
        "is_folded": folded,
        "is_all_in": all_in,
        "bet_this_street": bet,
        "hole_cards": None,
    }


def _base_state(**overrides) -> dict:
    state = {
        "type": "action_request",
        "hand_id": "edge_base",
        "street": "flop",
        "seat_to_act": 0,
        "pot": 1200,
        "community_cards": ["Ah", "Td", "7s"],
        "current_bet": 0,
        "min_raise_to": 100,
        "amount_owed": 0,
        "can_check": True,
        "your_cards": ["As", "Kd"],
        "your_stack": 9000,
        "your_bet_this_street": 0,
        "players": [_player(i) for i in range(6)],
        "action_log": [],
    }
    state.update(overrides)
    return state


def expensive_edge_states() -> list[tuple[str, dict]]:
    """Synthetic tournament failure states for decide() contract tests."""
    long_log = [
        {"hand_num": i // 8, "seat": i % 6, "bot_id": f"seat_{i % 6}", "action": "raise" if i % 5 == 0 else "call", "amount": 100 + i}
        for i in range(200)
    ]
    return [
        ("malformed_missing_keys", {"type": "action_request", "hand_id": "malformed_missing", "amount_owed": 100, "can_check": False}),
        (
            "malformed_wrong_types",
            {
                "type": "action_request",
                "hand_id": "malformed_wrong_types",
                "street": None,
                "pot": "many",
                "community_cards": "AhKhQh",
                "current_bet": "500",
                "min_raise_to": "1000",
                "amount_owed": "500",
                "can_check": False,
                "your_cards": [None, "??"],
                "your_stack": "9000",
                "your_bet_this_street": "0",
                "players": "not-a-player-list",
            },
        ),
        ("missing_legal_actions", _base_state(hand_id="missing_legal_actions")),
        ("empty_legal_actions", _base_state(hand_id="empty_legal_actions", legal_actions=[])),
        (
            "contradictory_legal_actions",
            _base_state(
                hand_id="contradictory_legal_actions",
                current_bet=600,
                min_raise_to=1200,
                amount_owed=600,
                can_check=False,
                legal_actions=["check"],
            ),
        ),
        (
            "raise_below_min_probe",
            _base_state(
                hand_id="raise_below_min_probe",
                street="turn",
                pot=3200,
                community_cards=["As", "Kd", "9h", "2c"],
                current_bet=1000,
                min_raise_to=2500,
                amount_owed=1000,
                can_check=False,
                your_cards=["Ad", "Qs"],
                your_stack=7000,
            ),
        ),
        (
            "raise_above_stack_probe",
            _base_state(
                hand_id="raise_above_stack_probe",
                street="preflop",
                community_cards=[],
                pot=1400,
                current_bet=1200,
                min_raise_to=2400,
                amount_owed=1100,
                can_check=False,
                your_cards=["Kh", "Ks"],
                your_stack=900,
                your_bet_this_street=100,
            ),
        ),
        (
            "equal_to_call_ambiguity",
            _base_state(
                hand_id="equal_to_call_ambiguity",
                street="preflop",
                community_cards=[],
                pot=2700,
                current_bet=1200,
                min_raise_to=2400,
                amount_owed=1100,
                can_check=False,
                your_cards=["Ac", "Qc"],
                your_stack=8000,
                your_bet_this_street=100,
            ),
        ),
        (
            "all_in_side_pot",
            _base_state(
                hand_id="all_in_side_pot",
                street="turn",
                pot=21400,
                community_cards=["Qh", "Jh", "7c", "2h"],
                current_bet=3500,
                min_raise_to=7000,
                amount_owed=180,
                can_check=False,
                your_cards=["Ah", "Qs"],
                your_stack=180,
                your_bet_this_street=3320,
                players=[
                    _player(0, stack=180, bet=3320),
                    _player(1, stack=0, bet=3500, all_in=True),
                    _player(2, stack=0, bet=2100, all_in=True),
                    _player(3, stack=7200, bet=3500),
                    _player(4, stack=0, bet=900, all_in=True),
                    _player(5, stack=0, bet=0, folded=True),
                ],
                action_log=[
                    {"seat": 1, "action": "all_in", "amount": 3500},
                    {"seat": 2, "action": "all_in", "amount": 2100},
                    {"seat": 3, "action": "call", "amount": 3500},
                ],
            ),
        ),
        (
            "multiway_wet_flop",
            _base_state(
                hand_id="multiway_wet_flop",
                street="flop",
                pot=4800,
                community_cards=["Jh", "Th", "9c"],
                current_bet=1600,
                min_raise_to=3200,
                amount_owed=1600,
                can_check=False,
                your_cards=["Qd", "Qc"],
                your_stack=7600,
                players=[_player(i, stack=9000 - i * 500, bet=1600 if i in (1, 2, 3) else 0) for i in range(6)],
            ),
        ),
        (
            "wet_board_equity_realization",
            _base_state(
                hand_id="wet_board_equity_realization",
                street="river",
                pot=12600,
                community_cards=["8d", "Ah", "2h", "7c", "3h"],
                current_bet=6300,
                min_raise_to=12600,
                amount_owed=6300,
                can_check=False,
                your_cards=["Jh", "Js"],
                your_stack=7900,
                players=[_player(0, stack=7900, bet=0), _player(1, stack=4200, bet=6300)] + [_player(i, folded=True) for i in range(2, 6)],
            ),
        ),
        (
            "river_bluff_catcher_threshold",
            _base_state(
                hand_id="river_bluff_catcher_threshold",
                street="river",
                pot=14200,
                community_cards=["Kh", "Qs", "Tc", "Td", "Ah"],
                current_bet=7100,
                min_raise_to=14200,
                amount_owed=7100,
                can_check=False,
                your_cards=["2s", "Kd"],
                your_stack=9800,
                players=[_player(0, stack=9800, bet=0), _player(1, stack=2900, bet=7100)] + [_player(i, folded=True) for i in range(2, 6)],
            ),
        ),
        (
            "blind_defense_3bet_pressure",
            _base_state(
                hand_id="blind_defense_3bet_pressure",
                street="preflop",
                community_cards=[],
                pot=3300,
                current_bet=1600,
                min_raise_to=3200,
                amount_owed=1500,
                can_check=False,
                your_cards=["Ks", "Qs"],
                your_stack=8400,
                your_bet_this_street=100,
                action_log=[
                    {"seat": 0, "action": "big_blind", "amount": 100},
                    {"seat": 2, "action": "raise", "amount": 300},
                    {"seat": 4, "action": "raise", "amount": 1600},
                ],
            ),
        ),
        (
            "near_dead_postflop_commitment",
            _base_state(
                hand_id="near_dead_postflop_commitment",
                street="river",
                pot=17800,
                community_cards=["Kd", "Ks", "Qs", "Qd", "5c"],
                current_bet=8900,
                min_raise_to=17800,
                amount_owed=8900,
                can_check=False,
                your_cards=["Qc", "9h"],
                your_stack=9100,
                players=[_player(0, stack=9100, bet=0), _player(1, stack=1100, bet=8900)] + [_player(i, folded=True) for i in range(2, 6)],
            ),
        ),
        (
            "timeout_stress_long_match_log",
            _base_state(
                hand_id="timeout_stress_long_match_log",
                street="turn",
                pot=9800,
                community_cards=["Ac", "Kc", "Qc", "2d"],
                current_bet=3200,
                min_raise_to=6400,
                amount_owed=3200,
                can_check=False,
                your_cards=["Ad", "Qh"],
                your_stack=12000,
                match_action_log=long_log,
                action_log=long_log[-40:],
            ),
        ),
    ]


LARGE_COMMITMENT_GUARD_STATES = {
    "wet_board_equity_realization",
    "river_bluff_catcher_threshold",
    "near_dead_postflop_commitment",
}


def _attr_chain(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def scan_source_for_forbidden(source: str, display: str) -> list[str]:
    issues: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"{display}: SyntaxError {exc}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod in FORBIDDEN_MODULES:
                    issues.append(f"{display}: forbidden import {mod}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in FORBIDDEN_MODULES:
                issues.append(f"{display}: forbidden from {mod}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALL_NAMES:
                issues.append(f"{display}: forbidden call {node.func.id}(...)")
            if isinstance(node.func, ast.Attribute):
                chain = _attr_chain(node.func)
                if chain.startswith("os.") and chain.split(".")[1] in BANNED_OS_FUNCS:
                    issues.append(f"{display}: forbidden call {chain}(...)")
                if chain.startswith("subprocess."):
                    issues.append(f"{display}: forbidden call {chain}(...)")
            if isinstance(node.func, ast.Name) and node.func.id == "getattr":
                if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "__builtins__":
                    issues.append(f"{display}: getattr(__builtins__, ...)")
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and node.value.id in {"__builtins__", "globals", "locals"}:
                issues.append(f"{display}: suspicious subscript on {node.value.id}")
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                if node.value.func.id in {"globals", "locals"}:
                    issues.append(f"{display}: forbidden call {node.value.func.id}()[...]")
    return issues


def validate_zip_structure(zip_path: Path) -> list[str]:
    """Validate package layout, size caps, and forbidden imports for a zip."""
    issues: list[str] = []
    zip_path = Path(zip_path)
    if not zip_path.exists():
        return [f"missing zip: {zip_path}"]
    size = zip_path.stat().st_size
    if size > MAX_PACKAGE_SIZE_BYTES:
        issues.append(f"archive_size:{size}>{MAX_PACKAGE_SIZE_BYTES}")
    data_size = 0
    names: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            name = info.filename
            names.append(name)
            if name.startswith(("/", "\\")):
                issues.append(f"absolute_path:{name}")
            norm = os.path.normpath(name)
            if norm.startswith("..") or os.path.isabs(norm):
                issues.append(f"path_traversal:{name}")
            mode = info.external_attr >> 16
            if stat.S_IFMT(mode) == stat.S_IFLNK:
                issues.append(f"symlink:{name}")
            if name.startswith("data/"):
                data_size += info.file_size
                if name.endswith(".py"):
                    issues.append(f"python_inside_data:{name}")
            if name == "bot.py" and info.file_size > MAX_BOT_PY_SIZE_BYTES:
                issues.append(f"bot_py_size:{info.file_size}>{MAX_BOT_PY_SIZE_BYTES}")
            if name.endswith(".py"):
                try:
                    source = zf.read(info).decode("utf-8")
                except UnicodeDecodeError:
                    issues.append(f"non_utf8_python:{name}")
                else:
                    issues.extend(scan_source_for_forbidden(source, f"{zip_path.name}:{name}"))

    if "bot.py" not in names:
        issues.append("missing_root_bot_py")
    root_py = sorted(name for name in names if "/" not in name and name.endswith(".py"))
    if root_py != ["bot.py"]:
        issues.append(f"unexpected_root_py:{root_py}")
    if data_size > MAX_DATA_SIZE_BYTES:
        issues.append(f"data_size:{data_size}>{MAX_DATA_SIZE_BYTES}")
    return issues


def validate_actions_for_states(bot_path: Path, states: Iterable[tuple[str, dict]]) -> list[str]:
    """Run one bot through states and return human-readable failures."""
    failures: list[str] = []
    with RunnerClient(bot_path) as runner:
        warmup = runner.send({"type": "warmup"})
        if warmup.payload.get("ok") is not True:
            failures.append(f"warmup_failed:{warmup.payload}")
        for name, state in states:
            result = runner.send(state)
            action = result.payload
            if "error" in action:
                failures.append(f"{name}:runner_error:{action.get('error')}")
            if result.elapsed_s > 2.25:
                failures.append(f"{name}:elapsed:{result.elapsed_s:.3f}s>2.25s")
            issues = check_action_contract(action, state)
            failures.extend(f"{name}:{issue}:action={action}" for issue in issues)
            if name in LARGE_COMMITMENT_GUARD_STATES and is_large_commit(action, state):
                failures.append(
                    f"{name}:large_near_dead_commitment:{commitment_fraction(action, state):.3f}:action={action}"
                )
    return failures
