#!/usr/bin/env python3
"""Reusable failure-mode tester for a candidate (or live) submission zip.

Checks (all must pass):
  1. validator      - ext/fullhouse-engine/sandbox/validator.py (AST + size, authoritative)
  2. forbidden-scan - candidate src .py scanned for forbidden imports/calls (import_audit-equivalent)
  3. edge           - POKERBOT_CANDIDATE_ZIP=<zip> pytest tests/edge_cases -x
                      (fuzz contract + disaster-spot no-large-commit guard, threshold 0.40)
  4. probes         - gauntlet --skip-matches: every probe shape_ok, no runner error, latency <= 2.25s
  5. smoke          - tools/smoke_run.py --zip <zip> --hands N (real container; skipped if --no-smoke)

Reports PASS/FAIL per check + overall + SHA256. Exit 0 only if every requested check passes.
Usage: failure_tester.py --zip <zip> [--src <candidate_src_dir>] [--hands 200] [--no-smoke]
"""
import argparse, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # repo root (…/PokerBot)
PY = str(ROOT / ".venv" / "bin" / "python")

def sha256(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()

def run(cmd, timeout=300, env=None):
    e = dict(os.environ); e.update(env or {})
    try:
        r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout, env=e)
        return r.returncode, (r.stdout or "")[-4000:], (r.stderr or "")[-2000:]
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--src", default=None, help="candidate src dir for forbidden scan")
    ap.add_argument("--hands", type=int, default=200)
    ap.add_argument("--no-smoke", action="store_true")
    args = ap.parse_args()
    zip_path = Path(args.zip).resolve()
    results = {}

    # 1. validator
    rc, out, err = run([PY, "ext/fullhouse-engine/sandbox/validator.py", str(zip_path), "--json"])
    results["validator"] = {"pass": rc == 0, "rc": rc, "tail": (out or err)[-600:]}

    # 2. forbidden-scan on candidate src
    if args.src:
        sys.path.insert(0, str(ROOT))
        from tools.edge_case_harness import scan_source_for_forbidden
        issues = []
        for py in sorted(Path(args.src).rglob("*.py")):
            issues += scan_source_for_forbidden(py.read_text(), str(py))
        results["forbidden_scan"] = {"pass": not issues, "issues": issues}
    else:
        results["forbidden_scan"] = {"pass": True, "issues": [], "note": "skipped (no --src)"}

    # 3. edge pytest with candidate zip
    rc, out, err = run([PY, "-m", "pytest", "tests/edge_cases", "-x", "-q"],
                       env={"POKERBOT_CANDIDATE_ZIP": str(zip_path)})
    results["edge"] = {"pass": rc == 0, "rc": rc, "tail": (out or err)[-900:]}

    # 4. probes via gauntlet --skip-matches
    with tempfile.TemporaryDirectory(dir=str(ROOT / "consult/artifacts/2026-06-04-camp2-search")) as td:
        rc, out, err = run([PY, "tools/deployed_artifact_gauntlet.py", "--bot", str(zip_path),
                            "--baseline", str(zip_path), "--skip-matches", "--outdir", td])
        probe_pass, probe_detail = False, "gauntlet failed"
        pf = Path(td) / "results" / "probe_results.json"
        if pf.is_file():
            probes = json.loads(pf.read_text())
            bad = []
            for p in probes:
                if not p.get("shape_ok"): bad.append(f"{p['name']}:shape")
                if p.get("errors"): bad.append(f"{p['name']}:err={p['errors']}")
                lat_ms = (p.get("latency_ms") or {}).get("max", 0) or 0
                if lat_ms > 2250: bad.append(f"{p['name']}:lat_ms={lat_ms}")
            probe_pass = (rc == 0) and not bad
            probe_detail = bad or f"{len(probes)} probes clean"
        results["probes"] = {"pass": probe_pass, "detail": probe_detail}

    # 5. smoke
    if args.no_smoke:
        results["smoke"] = {"pass": True, "note": "skipped (--no-smoke)"}
    else:
        rc, out, err = run([PY, "tools/smoke_run.py", "--zip", str(zip_path), "--hands", str(args.hands)], timeout=420)
        results["smoke"] = {"pass": rc == 0, "rc": rc, "tail": (out or err)[-600:]}

    overall = all(v["pass"] for v in results.values())
    report = {"zip": str(zip_path), "sha256": sha256(zip_path), "PASS": overall, "checks": results}
    print(json.dumps(report, indent=2))
    return 0 if overall else 1

if __name__ == "__main__":
    sys.exit(main())
