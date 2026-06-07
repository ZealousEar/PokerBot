"""Import audit — verifies cold-start time, RSS, and absence of forbidden
imports across every `.py` file in `src/`.

The engine's validator only AST-scans `bot.py`. We scan all submitted source
so transitive imports from `src/*` are caught locally before upload.

Usage:
    python tools/import_audit.py [--max-seconds 1.5] [--max-mb 400]
"""
import argparse
import ast
import subprocess
import sys
import time
from pathlib import Path

# Mirrors ext/fullhouse-engine/sandbox/validator.py::FORBIDDEN_MODULES
FORBIDDEN_MODULES = {
    "socket", "urllib", "urllib2", "urllib3", "requests", "httpx", "aiohttp",
    "http", "ftplib", "smtplib", "telnetlib", "xmlrpc",
    "subprocess", "multiprocessing",
    "pickle", "shelve",
    "threading",
    "ctypes",
    "runpy", "importlib",
}

# Mirrors validator BANNED_CALL_NAMES + BANNED_OS_FUNCS + extras.
BANNED_CALL_NAMES = {"__import__", "eval", "exec", "compile"}
BANNED_OS_FUNCS = {
    "system", "popen", "execv", "execve", "execvp", "execvpe",
    "execl", "execle", "execlp", "execlpe",
    "spawn", "spawnv", "spawnve", "spawnvp",
    "fork", "kill", "remove", "unlink", "rmdir", "removedirs",
    "chmod", "chown", "replace", "rename",
}

ROOT = Path(__file__).resolve().parent.parent


def _attr_chain(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def scan_file(path: Path) -> list[str]:
    """Return a list of human-readable issues found in this file."""
    issues: list[str] = []
    try:
        source = path.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{path.relative_to(ROOT)}: SyntaxError {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod in FORBIDDEN_MODULES:
                    issues.append(f"{path.relative_to(ROOT)}: forbidden import {mod}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in FORBIDDEN_MODULES:
                issues.append(f"{path.relative_to(ROOT)}: forbidden from {mod}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALL_NAMES:
                issues.append(f"{path.relative_to(ROOT)}: forbidden call {node.func.id}(...)")
            if isinstance(node.func, ast.Attribute):
                chain = _attr_chain(node.func)
                if chain.startswith("os.") and chain.split(".")[1] in BANNED_OS_FUNCS:
                    issues.append(f"{path.relative_to(ROOT)}: forbidden call {chain}(...)")
                if chain.startswith("subprocess."):
                    issues.append(f"{path.relative_to(ROOT)}: forbidden call {chain}(...)")
            if isinstance(node.func, ast.Name) and node.func.id == "getattr":
                if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "__builtins__":
                    issues.append(f"{path.relative_to(ROOT)}: getattr(__builtins__, …)")
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and node.value.id == "__builtins__":
                issues.append(f"{path.relative_to(ROOT)}: __builtins__[…] subscript")
    return issues


def scan_src() -> list[str]:
    src_dir = ROOT / "src"
    if not src_dir.exists():
        return []
    issues = []
    for py in sorted(src_dir.rglob("*.py")):
        issues.extend(scan_file(py))
    return issues


def measure_cold_import() -> tuple[float, float]:
    """Return (seconds, peak_rss_mb) for `import bot` in a fresh subprocess."""
    script = (
        "import time, resource, sys; "
        "sys.path.insert(0, 'src'); "
        "t0 = time.monotonic(); "
        "import bot; "
        "dt = time.monotonic() - t0; "
        "rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss; "
        "print(f'{dt:.4f} {rss}')"
    )
    out = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip().split()
    seconds = float(out[0])
    rss_raw = int(out[1])
    # macOS: ru_maxrss in bytes; Linux: in kilobytes
    rss_mb = rss_raw / (1024 * 1024) if sys.platform == "darwin" else rss_raw / 1024
    return seconds, rss_mb


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max-seconds", type=float, default=1.5)
    p.add_argument("--max-mb", type=float, default=400.0)
    args = p.parse_args()

    issues = scan_src()
    if issues:
        print("FORBIDDEN IMPORTS / CALLS:")
        for i in issues:
            print(f"  {i}")
        return 2

    try:
        seconds, rss_mb = measure_cold_import()
    except subprocess.CalledProcessError as e:
        print("IMPORT FAILED:")
        print(e.stderr)
        return 3

    print(f"cold import: {seconds:.3f}s, RSS: {rss_mb:.1f} MB")
    fail = False
    if seconds > args.max_seconds:
        print(f"  FAIL: cold import {seconds:.3f}s > {args.max_seconds}s")
        fail = True
    if rss_mb > args.max_mb:
        print(f"  FAIL: RSS {rss_mb:.1f}MB > {args.max_mb}MB")
        fail = True
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
