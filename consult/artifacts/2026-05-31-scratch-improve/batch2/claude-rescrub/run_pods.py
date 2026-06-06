"""Paired-seed six-max pod runner, parameterized by hero zip.

Adapted from the proven harness at
consult/artifacts/2026-05-30-dual-leak-swarm/laneC-toby-gauntlet/pods_candidate/run_pods.py
(same engine match.py, same opponent zips, same compositions). Differences:
  * --hero-zip selects the hero artifact (locked baseline OR a candidate).
  * --out-dir isolates each artifact's matches.jsonl so paired analysis can
    join candidate[seed] vs locked[seed] per composition.
  * Validates the protected locked SHA before and after (never modifies it).

This script NEVER imports source-tree src/ as the hero; the hero is always the
zip passed via --hero-zip, run through the engine exactly like a submission.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import statistics
import sys
import threading
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/farhad/Code/PokerBot")
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
EXPECTED_LOCKED_SHA = "e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598"
HERO_ID = "hero"

sys.path.insert(0, str(ENGINE_DIR))
from sandbox import match as match_mod  # noqa: E402
from engine.game import STARTING_STACK  # noqa: E402


PUBLIC_DRIFT_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-public-repo-drift"
PUBLIC_PATCH_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-public-drift-patch"
PUBLIC_SAT_DIR = ROOT / "consult" / "artifacts" / "2026-05-28-public-saturation"

SOURCE_ZIPS = {
    "toby_master": PUBLIC_PATCH_DIR / "opponent_zips" / "toby_master.zip",
    "mehedi_mybot": PUBLIC_DRIFT_DIR / "opponent_zips" / "mehedi_mybot.zip",
    "pav_skantbot7_9": PUBLIC_DRIFT_DIR / "opponent_zips" / "pav_skantbot7_9.zip",
    "stoppedtime24_mybot": PUBLIC_DRIFT_DIR / "opponent_zips" / "stoppedtime24_mybot.zip",
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

COMPOSITIONS = {
    "C0_BASELINE": ["hero", "template", "aggressor", "mathematician", "shark", "ref_bot_2"],
    "C1_SINGLE_TOBY_WEAK_FIELD": ["hero", "toby_master", "template", "mathematician", "shark", "ref_bot_2"],
    "C3_TOBY_MEHEDI_WEAK_FIELD": ["hero", "toby_master", "mehedi_mybot", "template", "shark", "ref_bot_2"],
    "C4_PUBLIC_NIGHTMARE": ["hero", "toby_master", "mehedi_mybot", "famadeo", "neel", "pav_skantbot7_9"],
    # Deterministic-subset pod: hero + only the bots PROVEN reproducible at a
    # fixed seed (template/mathematician/shark/ref_bot_2). aggressor dropped --
    # it is one of the two unseeded-RNG opponents. For a fixed seed each hero is
    # ONE fixed trajectory, so locked vs candidate is an EXACT paired comparison
    # with zero simulator noise (stronger than the statistical sharp-field pods).
    "C0D_DETERMINISTIC_SUBSET": ["hero", "template", "mathematician", "shark", "ref_bot_2"],
}


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
            proc_self._trap_match_id = getattr(timer._tls, "match_id", None)

        def patched_act(proc_self, game_state):
            started = time.perf_counter()
            action = timer._orig_act(proc_self, game_state)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            match_id = getattr(proc_self, "_trap_match_id", None)
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


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def percentile(values: list[float], pct: float):
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


def build_zip_from_dir(src_dir: Path, dest_zip: Path) -> None:
    bot_py = src_dir / "bot.py"
    if not bot_py.is_file():
        raise FileNotFoundError(f"missing bot.py in {src_dir}")
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    tmp_zip = dest_zip.with_suffix(dest_zip.suffix + ".tmp")
    if tmp_zip.exists():
        tmp_zip.unlink()
    with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(bot_py, "bot.py")
        data_dir = src_dir / "data"
        if data_dir.is_dir():
            for path in sorted(data_dir.rglob("*")):
                if path.is_file():
                    zf.write(path, str(path.relative_to(src_dir)))
    tmp_zip.replace(dest_zip)


def prepare_bot_paths(hero_zip: Path, opp_dir: Path) -> dict[str, Path]:
    opp_dir.mkdir(parents=True, exist_ok=True)
    bot_paths: dict[str, Path] = {"hero": hero_zip}
    for name, src_zip in SOURCE_ZIPS.items():
        dest = opp_dir / f"{name}.zip"
        if not dest.exists():
            if not src_zip.is_file():
                raise FileNotFoundError(f"missing source zip {src_zip}")
            shutil.copy2(src_zip, dest)
        bot_paths[name] = dest
    for name, src_dir in REFERENCE_DIRS.items():
        dest = opp_dir / f"{name}.zip"
        if not dest.exists():
            build_zip_from_dir(src_dir, dest)
        bot_paths[name] = dest
    return bot_paths


def load_existing(matches_path: Path) -> dict:
    records: dict = {}
    if not matches_path.is_file():
        return records
    with matches_path.open() as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            records[(record["composition"], int(record["seed"]))] = record
    return records


def append_record(matches_path: Path, record: dict) -> None:
    with matches_path.open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def match_paths(composition: str, bot_paths: dict[str, Path]) -> dict[str, str]:
    return {name: str(bot_paths[name].resolve()) for name in COMPOSITIONS[composition]}


def run_one_match(composition, seed, hands, bot_paths, timer):
    match_id = f"pod_{composition}_s{seed}"
    timer.set_match(match_id)
    try:
        result = match_mod.run_match(
            match_id, match_paths(composition, bot_paths), n_hands=hands, verbose=False, seed=seed
        )
    finally:
        timer.clear_match()
    timing = timer.pop_metrics(match_id)
    decision_counts = timing["decision_counts"]
    error_counts = timing["error_counts"]
    hero_decisions = decision_counts.get(HERO_ID, 0)
    hero_action_errors = error_counts.get(HERO_ID, 0)
    hero_latencies = timing["latencies_ms"].get(HERO_ID, [])
    hero_final_stack = result["final_stacks"].get(HERO_ID, 0)
    return {
        "composition": composition,
        "seed": seed,
        "scheduled_hands": hands,
        "actual_hands": result["n_hands"],
        "hero_chip_delta": result["chip_delta"][HERO_ID],
        "hero_final_stack": hero_final_stack,
        "hero_busted": hero_final_stack <= 0,
        "hero_decisions": hero_decisions,
        "hero_action_errors": hero_action_errors,
        "hero_p99_decide_latency_ms": round(percentile(hero_latencies, 99), 3) if hero_latencies else None,
        "chip_delta": result["chip_delta"],
        "final_stacks": result["final_stacks"],
        "bot_error_counts": {bid: len(errs) for bid, errs in result["bot_errors"].items()},
    }


def protected_shas() -> dict[str, str]:
    return {
        "v_final.zip": sha256_file(ROOT / "submissions" / "v_final.zip"),
        "best_green.zip": sha256_file(ROOT / "submissions" / "best_green.zip"),
    }


def validate_protected(stage: str) -> dict[str, str]:
    shas = protected_shas()
    bad = {k: v for k, v in shas.items() if v != EXPECTED_LOCKED_SHA}
    if bad:
        raise RuntimeError(f"protected SHA mismatch at {stage}: {bad}")
    return shas


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hero-zip", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--hands", type=int, default=400)
    p.add_argument("--seed-base", type=int, default=142)
    p.add_argument("--seeds", type=int, default=40)
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--compositions", nargs="+", choices=sorted(COMPOSITIONS), default=sorted(COMPOSITIONS))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    hero_zip = args.hero_zip.resolve()
    if not hero_zip.is_file():
        print(f"FAIL: hero zip not found {hero_zip}", file=sys.stderr)
        return 2
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    before = validate_protected("before")
    (out_dir / "protected_sha_before.json").write_text(json.dumps(before, indent=2, sort_keys=True) + "\n")

    opp_dir = out_dir / "opponent_zips"
    bot_paths = prepare_bot_paths(hero_zip, opp_dir)
    matches_path = out_dir / "matches.jsonl"

    seeds = list(range(args.seed_base, args.seed_base + args.seeds))
    records = load_existing(matches_path)
    tasks = [
        (c, s)
        for c in args.compositions
        for s in seeds
        if (c, s) not in records
    ]
    print(
        f"[pods] hero={hero_zip.name} sha={sha256_file(hero_zip)[:12]} out={out_dir.name} "
        f"comps={','.join(args.compositions)} hands={args.hands} "
        f"seeds={args.seed_base}..{args.seed_base + args.seeds - 1} jobs={args.jobs} "
        f"pending={len(tasks)} resumed={len(records)}",
        flush=True,
    )

    timer = DecisionTimer()
    timer.install()
    try:
        if args.jobs <= 1:
            for c, s in tasks:
                rec = run_one_match(c, s, args.hands, bot_paths, timer)
                records[(c, s)] = rec
                append_record(matches_path, rec)
                print(f"[pods] {c} s{s} hands={rec['actual_hands']} delta={rec['hero_chip_delta']:+d} bust={int(rec['hero_busted'])}", flush=True)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
                fut = {ex.submit(run_one_match, c, s, args.hands, bot_paths, timer): (c, s) for c, s in tasks}
                for f in concurrent.futures.as_completed(fut):
                    c, s = fut[f]
                    rec = f.result()
                    records[(c, s)] = rec
                    append_record(matches_path, rec)
                    print(f"[pods] {c} s{s} hands={rec['actual_hands']} delta={rec['hero_chip_delta']:+d} bust={int(rec['hero_busted'])}", flush=True)
    finally:
        timer.uninstall()

    after = validate_protected("after")
    (out_dir / "protected_sha_after.json").write_text(json.dumps(after, indent=2, sort_keys=True) + "\n")

    # Per-composition summary (marginal stats; paired analysis done separately).
    summary = {"hero_zip": str(hero_zip), "hero_sha": sha256_file(hero_zip),
               "generated_at": now_utc(), "hands": args.hands, "seed_base": args.seed_base,
               "seeds": args.seeds, "compositions": {}}
    for c in args.compositions:
        comp = [records[(c, s)] for s in seeds if (c, s) in records]
        deltas = [r["hero_chip_delta"] for r in comp]
        busts = sum(1 for r in comp if r["hero_busted"])
        summary["compositions"][c] = {
            "n": len(comp),
            "p10": percentile(deltas, 10), "p25": percentile(deltas, 25),
            "p50": percentile(deltas, 50), "p75": percentile(deltas, 75),
            "p90": percentile(deltas, 90),
            "mean": round(statistics.mean(deltas), 1) if deltas else None,
            "bust_rate": round(busts / len(comp), 4) if comp else None,
            "hero_action_errors": sum(r["hero_action_errors"] for r in comp),
            "hero_decisions": sum(r["hero_decisions"] for r in comp),
        }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"[pods] wrote {out_dir / 'summary.json'}")
    for c, d in summary["compositions"].items():
        print(f"[pods] {c} n={d['n']} p50={d['p50']} bust={d['bust_rate']} mean={d['mean']} err={d['hero_action_errors']}/{d['hero_decisions']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
