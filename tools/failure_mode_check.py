"""Failure-mode tester — one reusable "does this bot break?" gate per zip.

Composes existing tooling (no new strategy logic, weakens no safety rail):

  A. SHA + zip structure/forbidden-import scan   (edge_case_harness.validate_zip_structure)
  B. Engine validator (authoritative AST+size)   (ext/.../sandbox/validator.py --json)
  C. Import audit                                 (tools/import_audit.py)
  D. Edge-case pytest suite against THIS zip      (pytest tests/edge_cases -x, POKERBOT_CANDIDATE_ZIP=<zip>)
  E. Fuzz/contract sweep against THIS zip         (edge_case_harness.validate_actions_for_states over
                                                   expensive_edge_states(): varied streets/stacks/can_check/
                                                   all-in/min-raise; asserts no exceptions, no >2.25s,
                                                   no illegal/malformed actions, and the harness large-commit
                                                   guard on its guarded near-dead states)
  F. Disaster-spot probe pass (NO large-commit)   (deployed_artifact_gauntlet.py --bot <zip> --skip-matches,
                                                   then assert the known disaster probes do not large-commit,
                                                   are shape-legal, error-free, and within the 2s budget)
  G. Sandbox smoke run                            (tools/smoke_run.py --zip <zip> --hands 200)

Every step must pass for an overall PASS. Outputs a pass/fail summary with the zip SHA.

Disaster probes asserted in step F (gauntlet probe names → task disaster classes):
  near_drawing_dead_stackoff                  -> near-dead postflop stack-off (the R2 leak class)
  dominated_underboat_near_dead_commitment    -> dominated underboat near-dead
  multiway_wet_board                          -> A-high flush draw on monotone board
  river_facing_large_bet                      -> weak pair facing a large river bet (near-dead)
  turn_jam_poor_pot_odds                      -> overcards/no-made-hand turn jam (near-dead)
TPTK-into-set is additionally covered by step E's harness large-commit guard states.

Usage:
  python tools/failure_mode_check.py --zip submissions/v_final.zip
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"

sys.path.insert(0, str(TOOLS))

import edge_case_harness as h  # noqa: E402
import deployed_artifact_gauntlet as g  # noqa: E402

# Gauntlet probe names whose only safe outcome is a non-large commit (fold/check or
# a small call). A large commit (>=0.40 stack, per harness is_large_commit) on any of
# these is a catastrophic finals-losing leak.
DISASTER_PROBES = {
    "near_drawing_dead_stackoff",
    "dominated_underboat_near_dead_commitment",
    "multiway_wet_board",
    "river_facing_large_bet",
    "turn_jam_poor_pot_odds",
}
PROBE_LATENCY_MAX_MS = 2000.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(label: str, command: list[str], timeout_s: int) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, timeout=timeout_s
        )
    except subprocess.TimeoutExpired:
        return False, f"{label}: TIMEOUT after {timeout_s}s"
    ok = proc.returncode == 0
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-8:]
    return ok, f"{label}: exit={proc.returncode}\n    " + "\n    ".join(tail)


def main() -> int:
    parser = argparse.ArgumentParser(description="Failure-mode tester for a bot zip.")
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--python", default=str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable))
    parser.add_argument(
        "--outdir",
        type=Path,
        default=None,
        help="Gauntlet probe output dir (default: consult/artifacts/finals-freeze/<stem>-fmc).",
    )
    args = parser.parse_args()

    zip_path = args.zip if args.zip.is_absolute() else ROOT / args.zip
    if not zip_path.is_file():
        print(f"FAIL: zip not found: {zip_path}")
        return 2
    py = args.python
    sha = sha256_file(zip_path)
    outdir = args.outdir or (ROOT / "consult" / "artifacts" / "finals-freeze" / f"{zip_path.stem}-fmc")
    outdir = outdir if outdir.is_absolute() else ROOT / outdir
    outdir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"FAILURE-MODE CHECK  zip={zip_path.relative_to(ROOT)}")
    print(f"sha256={sha}")
    print("=" * 72)

    results: list[tuple[str, bool, str]] = []

    # ---- A. zip structure / forbidden-import scan ----
    struct_issues = h.validate_zip_structure(zip_path)
    results.append((
        "A_zip_structure",
        not struct_issues,
        "clean" if not struct_issues else "issues=" + "; ".join(struct_issues),
    ))

    # ---- B. engine validator (authoritative) ----
    ok, detail = run_cmd(
        "B_engine_validator",
        [py, str(ENGINE_DIR / "sandbox" / "validator.py"), str(zip_path), "--json"],
        timeout_s=120,
    )
    results.append(("B_engine_validator", ok, detail))

    # ---- C. import audit ----
    ok, detail = run_cmd("C_import_audit", [py, "tools/import_audit.py"], timeout_s=120)
    results.append(("C_import_audit", ok, detail))

    # ---- D. edge-case pytest against THIS zip ----
    env = {**os.environ, "POKERBOT_CANDIDATE_ZIP": str(zip_path)}
    try:
        proc = subprocess.run(
            [py, "-m", "pytest", "tests/edge_cases", "-x", "-q"],
            cwd=ROOT, capture_output=True, text=True, timeout=300, env=env,
        )
        ok = proc.returncode == 0
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-6:]
        detail = "exit=%d\n    %s" % (proc.returncode, "\n    ".join(tail))
    except subprocess.TimeoutExpired:
        ok, detail = False, "TIMEOUT"
    results.append(("D_edge_cases_pytest", ok, detail))

    # ---- E. fuzz/contract sweep against THIS zip ----
    # Pass the zip directly: RunnerClient extracts it and mounts data/ so the
    # bot's blueprints load (passing an extracted bot.py would drop data/).
    try:
        failures = h.validate_actions_for_states(zip_path, h.expensive_edge_states())
        ok = not failures
        detail = "clean (%d states)" % len(h.expensive_edge_states()) if ok \
            else "failures=" + "; ".join(failures)
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"exception: {exc!r}"
    results.append(("E_fuzz_contract_sweep", ok, detail))

    # ---- F. disaster-spot probe pass (gauntlet --skip-matches) ----
    probe_ok = True
    probe_detail_lines: list[str] = []
    try:
        proc = subprocess.run(
            [py, "tools/deployed_artifact_gauntlet.py", "--bot", str(zip_path),
             "--outdir", str(outdir), "--skip-matches", "--python", py],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
        )
        if proc.returncode != 0:
            probe_ok = False
            probe_detail_lines.append(
                "gauntlet exit=%d: %s" % (proc.returncode, (proc.stdout + proc.stderr).strip()[-400:])
            )
        probe_file = outdir / "results" / "probe_results.json"
        probes = json.loads(probe_file.read_text()) if probe_file.is_file() else []
        states_by_name = {p["name"]: p["state"] for p in g.probe_states() if "state" in p}
        seen = set()
        for pr in probes:
            name = pr["name"]
            if name in DISASTER_PROBES:
                seen.add(name)
            if pr.get("errors"):
                probe_ok = False
                probe_detail_lines.append(f"{name}: errors={pr['errors']}")
            if not pr.get("shape_ok", True):
                probe_ok = False
                probe_detail_lines.append(f"{name}: illegal/malformed action shape")
            lat_max = (pr.get("latency_ms") or {}).get("max")
            if lat_max is not None and lat_max > PROBE_LATENCY_MAX_MS:
                probe_ok = False
                probe_detail_lines.append(f"{name}: latency_max={lat_max:.0f}ms>2000ms")
            if name in DISASTER_PROBES:
                state = states_by_name.get(name, {})
                for action in pr.get("actions", []):
                    if h.is_large_commit(action, state):
                        probe_ok = False
                        frac = h.commitment_fraction(action, state)
                        probe_detail_lines.append(
                            f"{name}: LARGE_COMMIT frac={frac:.3f} action={action}"
                        )
        missing = DISASTER_PROBES - seen
        if missing:
            probe_ok = False
            probe_detail_lines.append(f"disaster probes missing from run: {sorted(missing)}")
    except Exception as exc:  # noqa: BLE001
        probe_ok = False
        probe_detail_lines.append(f"exception: {exc!r}")
    results.append((
        "F_disaster_probes",
        probe_ok,
        "no large-commit on disaster spots" if probe_ok else "; ".join(probe_detail_lines),
    ))

    # ---- G. sandbox smoke run ----
    try:
        proc = subprocess.run(
            [py, "tools/smoke_run.py", "--zip", str(zip_path), "--hands", "200"],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
        )
        out = proc.stdout + proc.stderr
        ok = proc.returncode == 0 and ("OK:" in out or "requested_hands_completed" in out)
        # surface any hero errors
        if '"hero_errors": []' not in out and "hero_errors" in out:
            ok = False
        tail = out.strip().splitlines()[-4:]
        detail = "exit=%d\n    %s" % (proc.returncode, "\n    ".join(tail))
    except subprocess.TimeoutExpired:
        ok, detail = False, "TIMEOUT"
    results.append(("G_smoke_run", ok, detail))

    # ---- summary ----
    print("\nRESULTS")
    overall = True
    for label, ok, detail in results:
        overall = overall and ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {detail}")
    print("-" * 72)
    verdict = "PASS" if overall else "FAIL"
    print(f"FAILURE-MODE CHECK: {verdict}  zip={zip_path.name}  sha256={sha}")
    print("=" * 72)
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
