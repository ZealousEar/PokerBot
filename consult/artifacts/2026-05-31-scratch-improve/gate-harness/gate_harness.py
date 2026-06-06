"""Survival-aware candidate-vs-locked gate harness (reusable).

Gates ANY candidate submission zip against the locked baseline on
decision-grade paired-seed six-max pods, with a fail-fast cheap->expensive
staged pipeline. Built for the 2026-06-02 patch window: evaluate a candidate
fast and safely, never auto-promote.

This tool is ARTIFACT-LOCAL. It does NOT import or modify src/, and it never
writes to submissions/. The hero (candidate) and baseline (locked) are always
loaded as zip files passed on the command line; the engine runs each bot in
its own subprocess (dev mode) or container (USE_DOCKER=true).

Pipeline (a candidate that fails an earlier stage does NOT advance):
  Stage 1 (cheap):   engine validator (candidate zip)
                     + tools/import_audit.py (working src/ — see caveat)
                     + tools/audit_strategy_leakage.py (candidate zip)
  Stage 2 (medium):  pytest tests/edge_cases
                     + tools/smoke_run.py (candidate zip, authoritative docker)
  Stage 3 (expensive, LAST): paired-seed six-max pods for candidate AND locked
                     on identical seeds; decisive pods (C0, C1) run first.

PASS/FAIL is computed on the PAIRED-DIFF distribution (per-seed
candidate-minus-locked chip delta), not the difference of marginal medians —
that preserves the variance reduction the paired design exists for. A pod
PASSes only if there is NO p50 regression AND NO bust-rate regression vs the
locked baseline.

import_audit caveat: tools/import_audit.py audits the working-tree src/, NOT
the candidate zip (it has no --zip flag). It is meaningful only when the
candidate was built from the current src/. The candidate zip's actual imports
are covered by the engine validator's forbidden-module AST scan on the zip.

NOTHING AUTO-PROMOTES. A candidate that clears every gate is only FLAGGED for
a human MODIFY decision; submissions/v_final.zip remains the upload target
unless a human explicitly overrides.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Fixed paths / invariants
# --------------------------------------------------------------------------
ROOT = Path("/Users/farhad/Code/PokerBot")
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
VENV_PY = ROOT / ".venv" / "bin" / "python"
LANE_DIR = ROOT / "consult" / "artifacts" / "2026-05-31-scratch-improve" / "gate-harness"

# HARD invariant: both canonical locked zips must match this sha at start+end,
# independent of whichever --locked is passed.
EXPECTED_PROTECTED_SHA = "e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598"
PROTECTED_ZIPS = {
    "submissions/v_final.zip": ROOT / "submissions" / "v_final.zip",
    "submissions/best_green.zip": ROOT / "submissions" / "best_green.zip",
}

VALIDATOR = ENGINE_DIR / "sandbox" / "validator.py"
IMPORT_AUDIT = ROOT / "tools" / "import_audit.py"
LEAKAGE_AUDIT = ROOT / "tools" / "audit_strategy_leakage.py"
SMOKE_RUN = ROOT / "tools" / "smoke_run.py"
EDGE_TESTS = ROOT / "tests" / "edge_cases"

HERO_ID = "hero"

# Engine imports (dev mode runs each bot in its own subprocess via runner.py).
sys.path.insert(0, str(ENGINE_DIR))
from sandbox import match as match_mod  # noqa: E402
from engine.game import STARTING_STACK  # noqa: E402

# --------------------------------------------------------------------------
# Opponent sourcing (replicates the proven dual-leak laneC pattern).
# Public-bot zips are COPIED and reference bots are BUILT into a lane-local
# opponent_zips/ dir; nothing outside the lane dir is written.
# --------------------------------------------------------------------------
PUBLIC_DRIFT_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-public-repo-drift"
PUBLIC_PATCH_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-public-drift-patch"
PUBLIC_SAT_DIR = ROOT / "consult" / "artifacts" / "2026-05-28-public-saturation"

SOURCE_ZIPS = {
    "toby_master": PUBLIC_PATCH_DIR / "opponent_zips" / "toby_master.zip",
    "mehedi_mybot": PUBLIC_DRIFT_DIR / "opponent_zips" / "mehedi_mybot.zip",
    "pav_skantbot7_9": PUBLIC_DRIFT_DIR / "opponent_zips" / "pav_skantbot7_9.zip",
    "famadeo": PUBLIC_SAT_DIR / "opponent_zips" / "famadeo.zip",
    "neel": PUBLIC_SAT_DIR / "opponent_zips" / "neel.zip",
}

REFERENCE_DIRS = {
    "template": ENGINE_DIR / "bots" / "template",
    "aggressor": ENGINE_DIR / "bots" / "aggressor",
    "mathematician": ENGINE_DIR / "bots" / "mathematician",
    "shark": ENGINE_DIR / "bots" / "shark",
    "ref_bot_2": ENGINE_DIR / "bots" / "ref_bot_2",
}

# Composition seat NAMES (the hero seat is filled at runtime by candidate/locked).
COMPOSITIONS = {
    "C0": ["hero", "template", "aggressor", "mathematician", "shark", "ref_bot_2"],
    "C1": ["hero", "toby_master", "template", "mathematician", "shark", "ref_bot_2"],
    "C3": ["hero", "toby_master", "mehedi_mybot", "template", "shark", "ref_bot_2"],
    "C4": ["hero", "toby_master", "mehedi_mybot", "famadeo", "neel", "pav_skantbot7_9"],
}
# Decisive ordering: C0 baseline, then C1 single-Toby weak field, then C3/C4.
POD_ORDER = ["C0", "C1", "C3", "C4"]


# --------------------------------------------------------------------------
# Decision timer (verbatim pattern from proven laneC run_pods.py).
# Thread-safe monkeypatch around BotProcess.act for per-seat decision timing
# and action-error counting. Used identically for candidate and locked runs.
# --------------------------------------------------------------------------
class DecisionTimer:
    def __init__(self) -> None:
        self._tls = threading.local()
        self._lock = threading.Lock()
        self._metrics: dict[str, dict] = {}
        self._orig_init = match_mod.BotProcess.__init__
        self._orig_act = match_mod.BotProcess.act
        self._installed = False

    def install(self) -> None:
        if self._installed:
            return
        timer = self

        def patched_init(proc_self, bot_id, bot_path):
            timer._orig_init(proc_self, bot_id, bot_path)
            proc_self._gate_match_id = getattr(timer._tls, "match_id", None)

        def patched_act(proc_self, game_state):
            started = time.perf_counter()
            action = timer._orig_act(proc_self, game_state)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            match_id = getattr(proc_self, "_gate_match_id", None)
            if match_id:
                with timer._lock:
                    bucket = timer._metrics.setdefault(
                        match_id,
                        {"latencies_ms": {}, "decision_counts": {}, "error_counts": {}},
                    )
                    bot_id = proc_self.bot_id
                    bucket["decision_counts"][bot_id] = bucket["decision_counts"].get(bot_id, 0) + 1
                    if isinstance(action, dict) and action.get("error"):
                        bucket["error_counts"][bot_id] = bucket["error_counts"].get(bot_id, 0) + 1
                    bucket["latencies_ms"].setdefault(bot_id, []).append(elapsed_ms)
            return action

        match_mod.BotProcess.__init__ = patched_init
        match_mod.BotProcess.act = patched_act
        self._installed = True

    def uninstall(self) -> None:
        if not self._installed:
            return
        match_mod.BotProcess.__init__ = self._orig_init
        match_mod.BotProcess.act = self._orig_act
        self._installed = False

    def set_match(self, match_id: str) -> None:
        self._tls.match_id = match_id
        with self._lock:
            self._metrics[match_id] = {"latencies_ms": {}, "decision_counts": {}, "error_counts": {}}

    def clear_match(self) -> None:
        if hasattr(self._tls, "match_id"):
            del self._tls.match_id

    def pop_metrics(self, match_id: str) -> dict:
        with self._lock:
            return self._metrics.pop(
                match_id, {"latencies_ms": {}, "decision_counts": {}, "error_counts": {}}
            )


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    pos = (len(ordered) - 1) * (pct / 100.0)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(ordered[lo])
    return float(ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo))


def r(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def fmt(value: float | int | None, digits: int = 0) -> str:
    if value is None:
        return "n/a"
    if digits == 0:
        return str(int(round(float(value))))
    return f"{float(value):.{digits}f}"


def distribution(values: list[float]) -> dict[str, Any]:
    if not values:
        return {k: None for k in ("count", "p10", "p25", "p50", "p75", "p90", "mean", "stdev", "min", "max")}
    return {
        "count": len(values),
        "p10": r(percentile(values, 10)),
        "p25": r(percentile(values, 25)),
        "p50": r(percentile(values, 50)),
        "p75": r(percentile(values, 75)),
        "p90": r(percentile(values, 90)),
        "mean": r(statistics.mean(values)),
        "stdev": r(statistics.stdev(values) if len(values) > 1 else 0.0),
        "min": r(min(values)),
        "max": r(max(values)),
    }


# --------------------------------------------------------------------------
# Protected-SHA guard (independent of --locked)
# --------------------------------------------------------------------------
def protected_shas() -> dict[str, str]:
    return {name: sha256_file(path) for name, path in PROTECTED_ZIPS.items()}


def assert_protected(stage: str) -> dict[str, str]:
    shas = protected_shas()
    bad = {name: sha for name, sha in shas.items() if sha != EXPECTED_PROTECTED_SHA}
    if bad:
        raise SystemExit(
            f"FATAL protected-SHA mismatch at {stage}: {bad}\n"
            f"expected {EXPECTED_PROTECTED_SHA}. STOPPING. protected_sha_ok=false"
        )
    return shas


# --------------------------------------------------------------------------
# Opponent zip preparation (lane-local; copy/build only)
# --------------------------------------------------------------------------
def build_zip_from_dir(src_dir: Path, dest_zip: Path) -> None:
    import zipfile

    bot_py = src_dir / "bot.py"
    if not bot_py.is_file():
        raise FileNotFoundError(f"missing bot.py in {src_dir}")
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest_zip.with_suffix(dest_zip.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(bot_py, "bot.py")
        data_dir = src_dir / "data"
        if data_dir.is_dir():
            for p in sorted(data_dir.rglob("*")):
                if p.is_file():
                    zf.write(p, str(p.relative_to(src_dir)))
    tmp.replace(dest_zip)


def prepare_opponents(compositions: list[str], force_zips: bool) -> tuple[dict[str, Path], dict[str, dict]]:
    import shutil

    needed: set[str] = set()
    for comp in compositions:
        for name in COMPOSITIONS[comp]:
            if name != "hero":
                needed.add(name)

    out_dir = LANE_DIR / "opponent_zips"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    manifest: dict[str, dict] = {}

    for name in sorted(needed):
        dest = out_dir / f"{name}.zip"
        if name in SOURCE_ZIPS:
            src = SOURCE_ZIPS[name]
            if not src.is_file():
                raise FileNotFoundError(f"missing source opponent zip {src}")
            if force_zips or not dest.exists():
                shutil.copy2(src, dest)
            kind = "copied_zip"
            source = relative(src)
        elif name in REFERENCE_DIRS:
            src_dir = REFERENCE_DIRS[name]
            if force_zips or not dest.exists():
                build_zip_from_dir(src_dir, dest)
            kind = "built_reference_zip"
            source = relative(src_dir)
        else:
            raise KeyError(f"unknown opponent {name}")
        paths[name] = dest
        manifest[name] = {"source": source, "path": relative(dest), "sha256": sha256_file(dest), "kind": kind}

    return paths, manifest


# --------------------------------------------------------------------------
# Single match (verbatim pattern from proven laneC run_pods.py)
# --------------------------------------------------------------------------
def infer_bust(result: dict) -> dict | None:
    previous_stack = STARTING_STACK
    for hand in result.get("hands", []):
        final_stacks = hand.get("final_stacks", {})
        stack = final_stacks.get(HERO_ID, previous_stack)
        if previous_stack > 0 and stack <= 0:
            return {
                "hand_num": hand.get("hand_num"),
                "street": hand.get("street"),
                "showdown": hand.get("showdown"),
                "pot": hand.get("pot"),
            }
        previous_stack = stack
    return None


def seat_paths(comp: str, hero_zip: Path, opp_paths: dict[str, Path]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in COMPOSITIONS[comp]:
        out[name] = str(hero_zip.resolve()) if name == "hero" else str(opp_paths[name].resolve())
    return out


def run_one_match(comp: str, seed: int, hands: int, hero_zip: Path, opp_paths: dict[str, Path], timer: DecisionTimer, tag: str) -> dict:
    match_id = f"gate_{tag}_{comp}_s{seed}"
    timer.set_match(match_id)
    try:
        result = match_mod.run_match(
            match_id, seat_paths(comp, hero_zip, opp_paths), n_hands=hands, verbose=False, seed=seed
        )
    finally:
        timer.clear_match()

    timing = timer.pop_metrics(match_id)
    decision_counts = timing["decision_counts"]
    error_counts = timing["error_counts"]
    hero_latencies = timing["latencies_ms"].get(HERO_ID, [])
    hero_decisions = decision_counts.get(HERO_ID, 0)
    hero_action_errors = error_counts.get(HERO_ID, 0)

    opp_ids = [b for b in COMPOSITIONS[comp] if b != HERO_ID]
    opp_decisions = sum(decision_counts.get(b, 0) for b in opp_ids)
    opp_action_errors = sum(error_counts.get(b, 0) for b in opp_ids)

    hero_final = result["final_stacks"].get(HERO_ID, 0)
    return {
        "side": tag,
        "composition": comp,
        "seed": seed,
        "scheduled_hands": hands,
        "actual_hands": result["n_hands"],
        "duration_s": result["duration_s"],
        "hero_chip_delta": result["chip_delta"][HERO_ID],
        "hero_final_stack": hero_final,
        "hero_busted": hero_final <= 0,
        "hero_bust_cause": infer_bust(result),
        "hero_decisions": hero_decisions,
        "hero_action_errors": hero_action_errors,
        "hero_bot_errors": len(result["bot_errors"].get(HERO_ID, [])),
        "hero_p99_decide_latency_ms": r(percentile(hero_latencies, 99), 3),
        "opponent_decisions": opp_decisions,
        "opponent_action_errors": opp_action_errors,
        "chip_delta": result["chip_delta"],
        "seats": COMPOSITIONS[comp],
    }


# --------------------------------------------------------------------------
# matches.jsonl IO (namespaced per side, inside per-candidate run dir)
# --------------------------------------------------------------------------
def load_existing(path: Path) -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    if not path.is_file():
        return out
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            out[(rec["composition"], int(rec["seed"]))] = rec
    return out


def append_record(path: Path, rec: dict) -> None:
    with path.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")


def run_side(
    tag: str,
    hero_zip: Path,
    compositions: list[str],
    seeds: list[int],
    hands: int,
    opp_paths: dict[str, Path],
    matches_path: Path,
    jobs: int,
    timer: DecisionTimer,
) -> dict[tuple[str, int], dict]:
    records = load_existing(matches_path)
    tasks = [(c, s) for c in compositions for s in seeds if (c, s) not in records]
    print(
        f"[gate:{tag}] hero={relative(hero_zip)} comps={','.join(compositions)} "
        f"hands={hands} seeds={seeds[0]}..{seeds[-1]} jobs={jobs} pending={len(tasks)} resumed={len(records)}",
        flush=True,
    )
    if jobs <= 1:
        for comp, seed in tasks:
            rec = run_one_match(comp, seed, hands, hero_zip, opp_paths, timer, tag)
            records[(comp, seed)] = rec
            append_record(matches_path, rec)
            _progress(rec)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
            fut = {
                ex.submit(run_one_match, comp, seed, hands, hero_zip, opp_paths, timer, tag): (comp, seed)
                for comp, seed in tasks
            }
            for f in concurrent.futures.as_completed(fut):
                comp, seed = fut[f]
                rec = f.result()
                records[(comp, seed)] = rec
                append_record(matches_path, rec)
                _progress(rec)
    return records


def _progress(rec: dict) -> None:
    print(
        f"[gate:{rec['side']}] {rec['composition']} seed={rec['seed']} "
        f"hands={rec['actual_hands']}/{rec['scheduled_hands']} delta={rec['hero_chip_delta']:+d} "
        f"bust={int(rec['hero_busted'])} hero_err={rec['hero_action_errors']}/{rec['hero_decisions']} "
        f"p99_ms={fmt(rec['hero_p99_decide_latency_ms'], 3)} dur={rec['duration_s']}s",
        flush=True,
    )


# --------------------------------------------------------------------------
# Cheap/medium gate stages (subprocess to the canonical tools)
# --------------------------------------------------------------------------
def run_cmd(name: str, cmd: list[str], cwd: Path = ROOT, env: dict | None = None) -> dict:
    print(f"[gate:stage] {name}: {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env)
    out_tail = "\n".join((proc.stdout or "").strip().splitlines()[-12:])
    err_tail = "\n".join((proc.stderr or "").strip().splitlines()[-12:])
    passed = proc.returncode == 0
    print(f"[gate:stage] {name}: {'PASS' if passed else 'FAIL'} (exit {proc.returncode})", flush=True)
    return {
        "name": name,
        "cmd": cmd,
        "returncode": proc.returncode,
        "passed": passed,
        "stdout_tail": out_tail,
        "stderr_tail": err_tail,
    }


def stage1_cheap(candidate_zip: Path) -> list[dict]:
    return [
        run_cmd("validator", [str(VENV_PY), str(VALIDATOR), str(candidate_zip)]),
        # CAVEAT: import_audit reads working-tree src/, NOT the candidate zip.
        run_cmd("import_audit", [str(VENV_PY), str(IMPORT_AUDIT)]),
        run_cmd("leakage_audit", [str(VENV_PY), str(LEAKAGE_AUDIT), "--zip", str(candidate_zip)]),
    ]


def stage2_medium(candidate_zip: Path, smoke_hands: int, smoke_opponent: str) -> list[dict]:
    results = [run_cmd("edge_tests", [str(VENV_PY), "-m", "pytest", str(EDGE_TESTS), "-x", "-q"])]
    # smoke_run takes a repo-relative --zip; pass relative when possible.
    try:
        zip_arg = str(candidate_zip.resolve().relative_to(ROOT))
    except ValueError:
        zip_arg = str(candidate_zip.resolve())
    results.append(
        run_cmd(
            "smoke_run",
            [str(VENV_PY), str(SMOKE_RUN), "--zip", zip_arg, "--opponent", smoke_opponent, "--hands", str(smoke_hands)],
        )
    )
    return results


# --------------------------------------------------------------------------
# Pairing + PASS/FAIL verdict
# --------------------------------------------------------------------------
def pair_pods(
    candidate: dict[tuple[str, int], dict],
    locked: dict[tuple[str, int], dict],
    compositions: list[str],
    seeds: list[int],
    p50_tol: float,
    bust_tol: float,
) -> dict[str, Any]:
    comp_out: dict[str, Any] = {}
    overall_pass = True
    any_incomplete = False

    for comp in compositions:
        paired_seeds = [s for s in seeds if (comp, s) in candidate and (comp, s) in locked]
        complete = len(paired_seeds) == len(seeds)
        if not complete:
            any_incomplete = True

        cand_recs = [candidate[(comp, s)] for s in paired_seeds]
        lock_recs = [locked[(comp, s)] for s in paired_seeds]
        cand_deltas = [float(x["hero_chip_delta"]) for x in cand_recs]
        lock_deltas = [float(x["hero_chip_delta"]) for x in lock_recs]
        paired_diffs = [
            float(candidate[(comp, s)]["hero_chip_delta"] - locked[(comp, s)]["hero_chip_delta"])
            for s in paired_seeds
        ]

        cand_dist = distribution(cand_deltas)
        lock_dist = distribution(lock_deltas)
        diff_dist = distribution(paired_diffs)

        cand_busts = sum(1 for x in cand_recs if x["hero_busted"])
        lock_busts = sum(1 for x in lock_recs if x["hero_busted"])
        cand_bust_rate = (cand_busts / len(cand_recs)) if cand_recs else None
        lock_bust_rate = (lock_busts / len(lock_recs)) if lock_recs else None

        # Marginal p50 delta (reported, NOT used as the primary gate signal).
        marginal_p50_delta = (
            r(cand_dist["p50"] - lock_dist["p50"]) if cand_dist["p50"] is not None and lock_dist["p50"] is not None else None
        )
        bust_rate_delta = (
            r(cand_bust_rate - lock_bust_rate, 4)
            if cand_bust_rate is not None and lock_bust_rate is not None
            else None
        )

        # PRIMARY gate signal: paired-diff median (per-seed cand-locked). This
        # preserves the variance reduction of the paired design. A regression
        # is a paired-diff median below -p50_tol (a real median chip loss).
        paired_p50 = diff_dist["p50"]
        p50_regression = paired_p50 is not None and paired_p50 < -p50_tol
        bust_regression = bust_rate_delta is not None and bust_rate_delta > bust_tol

        pod_pass = complete and (not p50_regression) and (not bust_regression)
        if not pod_pass:
            overall_pass = False

        comp_out[comp] = {
            "complete": complete,
            "paired_count": len(paired_seeds),
            "scheduled_count": len(seeds),
            "missing_candidate_seeds": sorted(set(seeds) - {s for s in seeds if (comp, s) in candidate}),
            "missing_locked_seeds": sorted(set(seeds) - {s for s in seeds if (comp, s) in locked}),
            "candidate_chip_delta": cand_dist,
            "locked_chip_delta": lock_dist,
            "paired_diff_candidate_minus_locked": diff_dist,
            "marginal_p50_delta_candidate_minus_locked": marginal_p50_delta,
            "candidate_bust_rate": r(cand_bust_rate, 4),
            "locked_bust_rate": r(lock_bust_rate, 4),
            "bust_rate_delta_candidate_minus_locked": bust_rate_delta,
            "candidate_busts": cand_busts,
            "locked_busts": lock_busts,
            "p50_regression": p50_regression,
            "bust_regression": bust_regression,
            "pod_pass": pod_pass,
            "candidate_hero_action_errors": sum(x["hero_action_errors"] for x in cand_recs),
            "candidate_hero_decisions": sum(x["hero_decisions"] for x in cand_recs),
            "candidate_hero_p99_decide_latency_ms": r(
                percentile([x["hero_p99_decide_latency_ms"] for x in cand_recs if x.get("hero_p99_decide_latency_ms") is not None], 99), 3
            ),
        }

    return {"compositions": comp_out, "all_pods_pass": overall_pass and not any_incomplete, "any_incomplete": any_incomplete}


# --------------------------------------------------------------------------
# Report writers
# --------------------------------------------------------------------------
def write_summary(summary: dict, run_dir: Path) -> None:
    (run_dir / "gate_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_markdown(summary, run_dir / "GATE_RESULTS.md")


def write_markdown(summary: dict, path: Path) -> None:
    pods = summary.get("pods")
    lines = [
        "# Candidate-vs-Locked Gate Result",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Verdict: **{summary['verdict']}**",
        "",
        summary["verdict_note"],
        "",
        "## Artifacts",
        "",
        f"- Candidate: `{summary['candidate']['path']}` sha `{summary['candidate']['sha256']}`",
        f"- Locked baseline: `{summary['locked']['path']}` sha `{summary['locked']['sha256']}`",
        f"- Protected SHA OK (start AND end, both canonical zips): `{summary['protected_sha_ok']}`",
        f"  - v_final start `{summary['protected_sha_before']['submissions/v_final.zip']}`",
        f"  - v_final end   `{summary['protected_sha_after']['submissions/v_final.zip']}`",
        f"  - best_green start `{summary['protected_sha_before']['submissions/best_green.zip']}`",
        f"  - best_green end   `{summary['protected_sha_after']['submissions/best_green.zip']}`",
        "",
        f"Run config: hands/match `{summary['config']['hands']}`, seed base `{summary['config']['seed_base']}`, "
        f"seeds `{summary['config']['seeds']}`, pods `{', '.join(summary['config']['pods'])}`, "
        f"PYTHONHASHSEED `{summary['config']['pythonhashseed']}`, "
        f"p50_tol `{summary['config']['p50_tol']}`, bust_tol `{summary['config']['bust_tol']}`.",
        "",
        "## Stage results (fail-fast cheap -> expensive)",
        "",
        "| stage | name | result | exit |",
        "| --- | --- | --- | ---: |",
    ]
    for st in summary["stages"]:
        lines.append(f"| {st['stage']} | {st['name']} | {'PASS' if st['passed'] else 'FAIL'} | {st['returncode']} |")

    lines += [
        "",
        "_import_audit caveat: audits working-tree `src/`, not the candidate zip; the candidate zip's imports are covered by the engine validator's forbidden-module AST scan._",
        "",
    ]

    if pods is None:
        lines += ["## Pods", "", "_Not reached (an earlier stage failed or pods were skipped)._", ""]
    else:
        lines += [
            "## Paired six-max pods (candidate vs locked, identical seeds)",
            "",
            "Primary gate signal is the PAIRED-DIFF median (per-seed candidate-minus-locked). "
            "Marginal medians and the marginal p50 delta are shown for context but are NOT the gate signal.",
            "",
            "| pod | paired n | cand p50 | lock p50 | marg Δp50 | paired Δp10 | paired Δp50 | paired Δp90 | paired Δmean | paired Δstdev | cand bust | lock bust | Δbust | p50 reg | bust reg | PASS |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :-: | :-: | :-: |",
        ]
        for comp in summary["config"]["pods"]:
            if comp not in pods["compositions"]:
                continue
            d = pods["compositions"][comp]
            diff = d["paired_diff_candidate_minus_locked"]
            lines.append(
                f"| {comp} | {d['paired_count']} | {fmt(d['candidate_chip_delta']['p50'])} | "
                f"{fmt(d['locked_chip_delta']['p50'])} | {fmt(d['marginal_p50_delta_candidate_minus_locked'])} | "
                f"{fmt(diff['p10'])} | {fmt(diff['p50'])} | {fmt(diff['p90'])} | {fmt(diff['mean'], 1)} | {fmt(diff['stdev'], 1)} | "
                f"{fmt((d['candidate_bust_rate'] or 0) * 100, 1)}% | {fmt((d['locked_bust_rate'] or 0) * 100, 1)}% | "
                f"{fmt((d['bust_rate_delta_candidate_minus_locked'] or 0) * 100, 1)}% | "
                f"{'Y' if d['p50_regression'] else 'n'} | {'Y' if d['bust_regression'] else 'n'} | "
                f"{'PASS' if d['pod_pass'] else 'FAIL'} |"
            )
        lines += [
            "",
            "### Paired-diff resolution floor (the smallest regression the gate can resolve)",
            "",
            "| pod | paired Δ min | paired Δ max | paired Δ stdev |",
            "| --- | ---: | ---: | ---: |",
        ]
        for comp in summary["config"]["pods"]:
            if comp not in pods["compositions"]:
                continue
            diff = pods["compositions"][comp]["paired_diff_candidate_minus_locked"]
            lines.append(f"| {comp} | {fmt(diff['min'])} | {fmt(diff['max'])} | {fmt(diff['stdev'], 1)} |")
        lines += [""]

    lines += [
        "## Decision",
        "",
        "NOTHING AUTO-PROMOTES. A candidate that clears the FULL gate is only FLAGGED for a human MODIFY decision. "
        "`submissions/v_final.zip` remains the upload target unless a human explicitly overrides.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--candidate", required=True, help="candidate submission zip to gate")
    p.add_argument("--locked", default=str(ROOT / "submissions" / "v_final.zip"), help="locked baseline zip")
    p.add_argument("--pods", default="C0,C1", help="comma list from C0,C1,C3,C4 (decisive order enforced)")
    p.add_argument("--seed-base", type=int, default=142)
    p.add_argument("--seeds", type=int, default=40, help="paired seed count (>=40 for a decision-grade gate)")
    p.add_argument("--hands", type=int, default=400)
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--p50-tol", type=float, default=0.0, help="paired-diff median below -p50_tol = regression (default 0; raise to the measured noise floor)")
    p.add_argument("--bust-tol", type=float, default=0.0, help="candidate bust-rate above locked by more than this = regression")
    p.add_argument("--smoke-hands", type=int, default=200)
    p.add_argument("--smoke-opponent", default="template")
    p.add_argument("--skip-stage1", action="store_true", help="skip validator/import/leakage (NOT for a full gate)")
    p.add_argument("--skip-stage2", action="store_true", help="skip edge/smoke (NOT for a full gate)")
    p.add_argument("--allow-small-seeds", action="store_true", help="permit <40 seeds (self-test / wiring only)")
    p.add_argument("--force-zips", action="store_true", help="rebuild/copy lane-local opponent zips")
    p.add_argument("--run-name", default=None, help="override per-candidate run dir name")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Pin string-hash randomization so any latent hash()-seeded RNG in a bot is
    # reproducible across candidate and locked subprocesses (engine launches
    # each bot with {**os.environ}). Makes the no-regression floor trustworthy.
    os.environ.setdefault("PYTHONHASHSEED", "0")

    candidate_zip = Path(args.candidate).resolve()
    locked_zip = Path(args.locked).resolve()
    if not candidate_zip.is_file():
        raise SystemExit(f"missing candidate {candidate_zip}")
    if not locked_zip.is_file():
        raise SystemExit(f"missing locked {locked_zip}")

    pods = [c.strip() for c in args.pods.split(",") if c.strip()]
    for c in pods:
        if c not in COMPOSITIONS:
            raise SystemExit(f"unknown pod {c}; choose from {sorted(COMPOSITIONS)}")
    pods = [c for c in POD_ORDER if c in pods]  # enforce decisive order

    if args.seeds < 40 and not args.allow_small_seeds:
        raise SystemExit(
            f"--seeds={args.seeds} is below the decision-grade floor of 40. "
            f"Pass --allow-small-seeds ONLY for a wiring self-test and document the count."
        )

    seeds = list(range(args.seed_base, args.seed_base + args.seeds))

    # Per-candidate run dir keyed by sha8 to avoid stale-cache collisions.
    cand_sha = sha256_file(candidate_zip)
    run_name = args.run_name or f"run_{cand_sha[:8]}"
    run_dir = LANE_DIR / "runs" / run_name
    (run_dir / "pods_candidate").mkdir(parents=True, exist_ok=True)
    (run_dir / "pods_locked").mkdir(parents=True, exist_ok=True)

    print(f"[gate] candidate={relative(candidate_zip)} sha={cand_sha[:12]} run_dir={relative(run_dir)}", flush=True)

    protected_before = assert_protected("START")
    (run_dir / "protected_sha_before.json").write_text(json.dumps(protected_before, indent=2, sort_keys=True) + "\n")

    stages: list[dict] = []
    gate_failed_stage: str | None = None

    # ---- Stage 1 (cheap) ----
    if not args.skip_stage1:
        for res in stage1_cheap(candidate_zip):
            stages.append({"stage": 1, **res})
            if not res["passed"] and gate_failed_stage is None:
                gate_failed_stage = f"stage1:{res['name']}"
    else:
        print("[gate] Stage 1 SKIPPED (--skip-stage1)", flush=True)

    # ---- Stage 2 (medium) ----
    if gate_failed_stage is None and not args.skip_stage2:
        for res in stage2_medium(candidate_zip, args.smoke_hands, args.smoke_opponent):
            stages.append({"stage": 2, **res})
            if not res["passed"] and gate_failed_stage is None:
                gate_failed_stage = f"stage2:{res['name']}"
    elif args.skip_stage2:
        print("[gate] Stage 2 SKIPPED (--skip-stage2)", flush=True)

    # ---- Stage 3 (expensive: paired pods) ----
    pods_result: dict | None = None
    opponent_manifest: dict | None = None
    if gate_failed_stage is None:
        opp_paths, opponent_manifest = prepare_opponents(pods, args.force_zips)
        timer = DecisionTimer()
        timer.install()
        try:
            candidate_records = run_side(
                "candidate", candidate_zip, pods, seeds, args.hands, opp_paths,
                run_dir / "pods_candidate" / "matches.jsonl", args.jobs, timer,
            )
            locked_records = run_side(
                "locked", locked_zip, pods, seeds, args.hands, opp_paths,
                run_dir / "pods_locked" / "matches.jsonl", args.jobs, timer,
            )
        finally:
            timer.uninstall()
        pods_result = pair_pods(candidate_records, locked_records, pods, seeds, args.p50_tol, args.bust_tol)
    else:
        print(f"[gate] Stage 3 (pods) NOT REACHED; died at {gate_failed_stage}", flush=True)

    protected_after = assert_protected("END")
    (run_dir / "protected_sha_after.json").write_text(json.dumps(protected_after, indent=2, sort_keys=True) + "\n")
    protected_ok = all(v == EXPECTED_PROTECTED_SHA for v in {**protected_before, **protected_after}.values())

    # ---- Verdict ----
    stages_all_pass = all(s["passed"] for s in stages)
    if not protected_ok:
        verdict = "ABORT_PROTECTED_SHA_MISMATCH"
    elif gate_failed_stage is not None:
        verdict = f"GATE_FAIL_{gate_failed_stage.upper().replace(':', '_')}"
    elif pods_result is None:
        verdict = "INCOMPLETE_PODS_NOT_RUN"
    elif pods_result["any_incomplete"]:
        verdict = "INCOMPLETE_PODS"
    elif not pods_result["all_pods_pass"]:
        verdict = "GATE_FAIL_POD_REGRESSION"
    elif stages_all_pass:
        verdict = "GATE_CLEAR_FLAG_FOR_HUMAN_MODIFY"
    else:
        verdict = "GATE_FAIL"

    summary = {
        "generated_at": now_utc(),
        "verdict": verdict,
        "verdict_note": (
            "NOTHING AUTO-PROMOTES. GATE_CLEAR only FLAGS the candidate for a human MODIFY decision; "
            "submissions/v_final.zip stays the upload target unless a human explicitly overrides."
        ),
        "candidate": {"path": relative(candidate_zip), "sha256": cand_sha},
        "locked": {"path": relative(locked_zip), "sha256": sha256_file(locked_zip)},
        "protected_sha_before": protected_before,
        "protected_sha_after": protected_after,
        "expected_protected_sha": EXPECTED_PROTECTED_SHA,
        "protected_sha_ok": protected_ok,
        "config": {
            "pods": pods,
            "seed_base": args.seed_base,
            "seeds": args.seeds,
            "hands": args.hands,
            "jobs": args.jobs,
            "p50_tol": args.p50_tol,
            "bust_tol": args.bust_tol,
            "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
            "use_docker": os.environ.get("USE_DOCKER", "false").lower() == "true",
            "allow_small_seeds": args.allow_small_seeds,
            "skip_stage1": args.skip_stage1,
            "skip_stage2": args.skip_stage2,
        },
        "died_at_stage": gate_failed_stage,
        "stages": stages,
        "opponent_zips": opponent_manifest,
        "pods": pods_result,
    }
    write_summary(summary, run_dir)

    print(f"[gate] wrote {run_dir / 'gate_summary.json'}", flush=True)
    print(f"[gate] wrote {run_dir / 'GATE_RESULTS.md'}", flush=True)
    print(f"[gate] verdict={verdict} protected_sha_ok={protected_ok}", flush=True)
    if pods_result is not None:
        for comp in pods:
            d = pods_result["compositions"].get(comp)
            if not d:
                continue
            diff = d["paired_diff_candidate_minus_locked"]
            print(
                f"[gate] {comp} paired_n={d['paired_count']} "
                f"paired_diff p50={fmt(diff['p50'])} mean={fmt(diff['mean'], 1)} stdev={fmt(diff['stdev'], 1)} "
                f"min={fmt(diff['min'])} max={fmt(diff['max'])} "
                f"cand_bust={fmt((d['candidate_bust_rate'] or 0) * 100, 1)}% lock_bust={fmt((d['locked_bust_rate'] or 0) * 100, 1)}% "
                f"PASS={d['pod_pass']}",
                flush=True,
            )

    # Exit code: 0 = gate cleared; 2 = protected SHA abort; 1 = any gate fail/incomplete.
    if not protected_ok:
        return 2
    return 0 if verdict == "GATE_CLEAR_FLAG_FOR_HUMAN_MODIFY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
