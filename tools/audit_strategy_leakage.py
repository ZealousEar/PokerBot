"""Scan packaged strategy source for identity-leakage strings.

The submitted policy may use public game state and observed actions, but it
must not branch on opponent labels, artifact names, branch names, or seed-like
identity handles.

Usage:
    python tools/audit_strategy_leakage.py --zip submissions/v_final.zip
"""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _strategy_members(zf: zipfile.ZipFile) -> list[str]:
    members = []
    for name in zf.namelist():
        if name == "bot.py" or (name.startswith("src/") and name.endswith(".py")):
            members.append(name)
    return sorted(members)


def _find_hits(name: str, text: str) -> list[str]:
    hits = []
    lowered_lines = text.lower().splitlines()
    for lineno, line in enumerate(lowered_lines, start=1):
        for needle in FORBIDDEN_STRINGS:
            if needle in line:
                hits.append(f"{name}:{lineno}: {needle}")
    return hits


def audit_zip(zip_path: Path) -> list[str]:
    issues = []
    with zipfile.ZipFile(zip_path) as zf:
        members = _strategy_members(zf)
        if "bot.py" not in members:
            issues.append("bot.py missing from archive root")
        for name in members:
            try:
                text = zf.read(name).decode("utf-8")
            except UnicodeDecodeError:
                issues.append(f"{name}: not utf-8 decodable")
                continue
            issues.extend(_find_hits(name, text))
    return issues


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", type=Path, default=ROOT / "submissions" / "v_final.zip")
    args = p.parse_args()

    zip_path = args.zip
    if not zip_path.is_absolute():
        zip_path = ROOT / zip_path
    if not zip_path.is_file():
        print(f"FAIL: zip not found: {zip_path}")
        return 2

    print(f"# zip: {zip_path.relative_to(ROOT)}")
    print(f"# zip sha256: {_sha256(zip_path)}")
    issues = audit_zip(zip_path)
    if issues:
        print("STRATEGY LEAKAGE DETECTED:")
        for issue in issues:
            print(f"  {issue}")
        return 1
    print("audit_strategy_leakage PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
