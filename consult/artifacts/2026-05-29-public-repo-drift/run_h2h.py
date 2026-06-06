#!/usr/bin/env python3
"""Artifact-local H2H runner for 2026-05-29 public repo drift audit.

Writes only under consult/artifacts/2026-05-29-public-repo-drift/.
Hero is always submissions/v_final.zip.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import sys
import time
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
ARTIFACT_DIR = ROOT / "consult" / "artifacts" / "2026-05-29-public-repo-drift"
LOG_DIR = ARTIFACT_DIR / "logs"
ZIP_DIR = ARTIFACT_DIR / "opponent_zips"
HERO_ZIP = ROOT / "submissions" / "v_final.zip"

sys.path.insert(0, str(ENGINE_DIR))
from engine.game import BIG_BLIND  # noqa: E402
from sandbox import match as match_mod  # noqa: E402

BOOTSTRAP_ITERS = 5000
CI_ALPHA = 0.05


class InstrumentedBotProcess(match_mod.BotProcess):
    latencies = defaultdict(list)
    stdout_noise = defaultdict(int)
    stdout_noise_examples = defaultdict(list)

    @classmethod
    def reset(cls):
        cls.latencies = defaultdict(list)
        cls.stdout_noise = defaultdict(int)
        cls.stdout_noise_examples = defaultdict(list)

    def _read_json_obj(self):
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise EOFError("Bot process died")
            text = line.strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                self.stdout_noise[self.bot_id] += 1
                if len(self.stdout_noise_examples[self.bot_id]) < 5:
                    self.stdout_noise_examples[self.bot_id].append(text[:200])

    def warmup(self):
        if self._proc is None:
            return
        try:
            self._proc.stdin.write(json.dumps({"type": "warmup"}) + "\n")
            self._proc.stdin.flush()
            self._read_json_obj()
        except Exception as e:
            self.errors.append("warmup_failed: " + str(e))

    def act(self, game_state):
        if self._proc is None:
            return {"action": "fold", "error": "no_process"}
        start = time.perf_counter()
        try:
            self._proc.stdin.write(json.dumps(game_state) + "\n")
            self._proc.stdin.flush()
            action = self._read_json_obj()
            if "error" in action:
                self.errors.append(action["error"])
            return action
        except Exception as e:
            self.errors.append(str(e))
            return {"action": "fold", "error": str(e)}
        finally:
            self.latencies[self.bot_id].append(time.perf_counter() - start)


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def describe_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        names = sorted(z.namelist())
        infos = z.infolist()
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "has_root_bot_py": "bot.py" in names,
        "data_bytes": sum(i.file_size for i in infos if i.filename.startswith("data/")),
        "sha256": sha256(path),
    }


def ensure_root_bot_zip(src_dir: Path, out_zip: Path) -> dict:
    src_dir = src_dir.resolve()
    if not (src_dir / "bot.py").is_file():
        raise FileNotFoundError(f"missing bot.py under {src_dir}")
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(src_dir / "bot.py", "bot.py")
        data_dir = src_dir / "data"
        if data_dir.is_dir():
            for f in sorted(data_dir.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts and not f.name.endswith((".pyc", ".pyo")):
                    z.write(f, str(Path("data") / f.relative_to(data_dir)))
    return describe_zip(out_zip)


def percentile(values, p):
    if not values:
        return 0.0
    xs = sorted(values)
    idx = min(len(xs) - 1, max(0, math.ceil((p / 100.0) * len(xs)) - 1))
    return xs[idx]


def bb100(chips, hands):
    if hands <= 0:
        return 0.0
    return (chips / BIG_BLIND) / (hands / 100.0)


def bootstrap_ci(samples, seed):
    if not samples:
        return {"mean": 0.0, "low": 0.0, "high": 0.0, "half_width": 0.0}
    rng = random.Random(seed)
    n = len(samples)
    means = []
    for _ in range(BOOTSTRAP_ITERS):
        chips = 0
        hands = 0
        for _ in range(n):
            s = samples[rng.randrange(n)]
            chips += int(s["chip_delta"])
            hands += int(s.get("metric_hands", s["hands"]))
        means.append(bb100(chips, hands))
    means.sort()
    chips_total = sum(int(s["chip_delta"]) for s in samples)
    hands_total = sum(int(s.get("metric_hands", s["hands"])) for s in samples)
    mean = bb100(chips_total, hands_total)
    low = means[int(BOOTSTRAP_ITERS * CI_ALPHA / 2)]
    high = means[int(BOOTSTRAP_ITERS * (1 - CI_ALPHA / 2))]
    return {"mean": mean, "low": low, "high": high, "half_width": (high - low) / 2.0}


def verdict(mean, low, high):
    if mean > 0 and low > -20:
        return "GREEN"
    if high < 0 or (low <= -20 and mean <= 0):
        return "RED"
    return "AMBER"


def run_one(name: str, src_dir: Path, base: int, target_hands: int, match_len: int, seed_stride: int,
            repo: str, head_sha: str, bot_path: str, force: bool = False) -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{name}_s{base}.log"
    json_path = LOG_DIR / f"{name}_s{base}.json"
    if json_path.is_file() and log_path.is_file() and not force:
        print(f"[skip] {name} base={base}: existing {json_path}")
        return json.loads(json_path.read_text())

    opp_zip = ZIP_DIR / f"{name}.zip"
    opp_zip_info = ensure_root_bot_zip(src_dir, opp_zip)
    hero_info = describe_zip(HERO_ZIP)

    original_bot_process = match_mod.BotProcess
    match_mod.BotProcess = InstrumentedBotProcess
    InstrumentedBotProcess.reset()

    samples = []
    match_rows = []
    hands_total = 0
    attempted_total = 0
    hero_errors = 0
    opp_errors = 0
    early_bust_matches = 0
    match_count = 0

    with log_path.open("w", encoding="utf-8") as log:
        def line(text=""):
            print(text, file=log, flush=True)

        line(f"PUBLIC REPO DRIFT H2H {now_iso()}")
        line(f"name={name} repo={repo} head_sha={head_sha} bot_path={bot_path}")
        line(f"hero={HERO_ZIP} sha256={hero_info['sha256']}")
        line(f"opponent_src={src_dir}")
        line(f"opponent_zip={opp_zip} sha256={opp_zip_info['sha256']}")
        line(f"target_scheduled_hands={target_hands} match_len={match_len} seed_stride={seed_stride}")
        line("seed schedule: seed = base + k * seed_stride; each seed runs two seat orientations")
        line()

        k = 0
        try:
            while attempted_total < target_hands:
                seed = base + k * seed_stride
                pair_chips = pair_hands = pair_attempted = pair_early = 0
                pair_hero_errors = pair_opp_errors = 0
                for orientation, paths in enumerate([
                    {"hero": str(HERO_ZIP.resolve()), "opp": str(opp_zip.resolve())},
                    {"opp": str(opp_zip.resolve()), "hero": str(HERO_ZIP.resolve())},
                ]):
                    match_id = f"drift_{name}_s{base}_k{k}_seed{seed}_o{orientation}"
                    started = time.perf_counter()
                    row = {"seed": seed, "orientation": orientation, "match_id": match_id, "attempted_hands": match_len}
                    try:
                        result = match_mod.run_match(match_id, paths, n_hands=match_len, verbose=False, seed=seed)
                        row.update({
                            "hands": int(result["n_hands"]),
                            "duration_s": float(result["duration_s"]),
                            "hero_chip_delta": int(result["chip_delta"]["hero"]),
                            "opp_chip_delta": int(result["chip_delta"]["opp"]),
                            "hero_errors": list(result["bot_errors"]["hero"]),
                            "opp_errors": list(result["bot_errors"]["opp"]),
                        })
                    except Exception as e:
                        row.update({
                            "hands": 0,
                            "duration_s": round(time.perf_counter() - started, 3),
                            "hero_chip_delta": 0,
                            "opp_chip_delta": 0,
                            "hero_errors": [f"match_failed: {e}"],
                            "opp_errors": [],
                        })
                    match_rows.append(row)
                    match_count += 1
                    attempted_total += match_len
                    hands_total += int(row["hands"])
                    pair_hands += int(row["hands"])
                    pair_attempted += match_len
                    pair_chips += int(row["hero_chip_delta"])
                    he = len(row["hero_errors"])
                    oe = len(row["opp_errors"])
                    hero_errors += he; opp_errors += oe
                    pair_hero_errors += he; pair_opp_errors += oe
                    if int(row["hands"]) < match_len:
                        early_bust_matches += 1; pair_early += 1
                    line(
                        f"seed={seed} o={orientation} hands={int(row['hands']):4d}/{match_len} "
                        f"hero_chip={int(row['hero_chip_delta']):+7d} "
                        f"hero_bb100_sched={bb100(int(row['hero_chip_delta']), match_len):+8.2f} "
                        f"hero_bb100_actual={bb100(int(row['hero_chip_delta']), int(row['hands'])):+8.2f} "
                        f"hero_err={he} opp_err={oe} dur={float(row['duration_s']):.2f}s"
                    )
                samples.append({
                    "seed": seed,
                    "hands": pair_hands,
                    "attempted_hands": pair_attempted,
                    "metric_hands": pair_attempted,
                    "chip_delta": pair_chips,
                    "bb_per_100": bb100(pair_chips, pair_attempted),
                    "actual_bb_per_100": bb100(pair_chips, pair_hands),
                    "early_bust_matches": pair_early,
                    "hero_errors": pair_hero_errors,
                    "opp_errors": pair_opp_errors,
                })
                if (k + 1) % 10 == 0:
                    print(
                        f"[run] {name} base={base} pairs={k+1} scheduled={attempted_total}/{target_hands} "
                        f"actual={hands_total} bb100_sched={bb100(sum(s['chip_delta'] for s in samples), attempted_total):+.2f}",
                        flush=True,
                    )
                k += 1
        finally:
            match_mod.BotProcess = original_bot_process

        ci = bootstrap_ci(samples, seed=base ^ 0xD21F7)
        hero_lat = InstrumentedBotProcess.latencies.get("hero", [])
        opp_lat = InstrumentedBotProcess.latencies.get("opp", [])
        result = {
            "name": name,
            "repo": repo,
            "head_sha": head_sha,
            "bot_path": bot_path,
            "base": base,
            "created_at": now_iso(),
            "target_scheduled_hands": target_hands,
            "match_len": match_len,
            "seed_stride": seed_stride,
            "seed_pairs": len(samples),
            "matches": match_count,
            "attempted_hands": attempted_total,
            "hands_played": hands_total,
            "hero_chip_delta": sum(s["chip_delta"] for s in samples),
            "hero_bb_per_100": ci["mean"],
            "hero_actual_bb_per_100": bb100(sum(s["chip_delta"] for s in samples), hands_total),
            "ci_low": ci["low"],
            "ci_high": ci["high"],
            "ci_half_width": ci["half_width"],
            "verdict": verdict(ci["mean"], ci["low"], ci["high"]),
            "early_bust_matches": early_bust_matches,
            "early_bust_rate": early_bust_matches / match_count if match_count else 0.0,
            "hero_errors": hero_errors,
            "opponent_errors": opp_errors,
            "hero_p99_decide_latency_s": percentile(hero_lat, 99),
            "hero_max_decide_latency_s": max(hero_lat) if hero_lat else 0.0,
            "opponent_p99_decide_latency_s": percentile(opp_lat, 99),
            "stdout_noise": dict(InstrumentedBotProcess.stdout_noise),
            "stdout_noise_examples": dict(InstrumentedBotProcess.stdout_noise_examples),
            "hero_zip": hero_info,
            "opponent_zip": opp_zip_info,
            "samples": samples,
            "match_rows": match_rows,
            "log_path": str(log_path),
            "json_path": str(json_path),
        }
        line()
        line("SUMMARY_JSON " + json.dumps({k: v for k, v in result.items() if k not in {"samples", "match_rows"}}, sort_keys=True))
        line(
            f"SUMMARY name={name} base={base} verdict={result['verdict']} "
            f"bb100={ci['mean']:+.2f} ci=[{ci['low']:+.2f},{ci['high']:+.2f}] "
            f"half_width={ci['half_width']:.2f} scheduled={attempted_total} actual_hands={hands_total} "
            f"early_bust_rate={result['early_bust_rate']:.3f} hero_errors={hero_errors} opp_errors={opp_errors} "
            f"hero_p99_latency_s={result['hero_p99_decide_latency_s']:.4f}"
        )

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"[done] {name} base={base} verdict={result['verdict']} "
        f"bb100={result['hero_bb_per_100']:+.2f} ci=[{result['ci_low']:+.2f},{result['ci_high']:+.2f}] "
        f"scheduled={result['attempted_hands']} actual={result['hands_played']} hero_err={hero_errors} opp_err={opp_errors}",
        flush=True,
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("package")
    p.add_argument("--name", required=True)
    p.add_argument("--src-dir", required=True)
    r = sub.add_parser("run")
    r.add_argument("--name", required=True)
    r.add_argument("--src-dir", required=True)
    r.add_argument("--repo", default="")
    r.add_argument("--head-sha", default="")
    r.add_argument("--bot-path", default="")
    r.add_argument("--base", type=int, default=142)
    r.add_argument("--hands", type=int, default=20000)
    r.add_argument("--match-len", type=int, default=500)
    r.add_argument("--seed-stride", type=int, default=1000)
    r.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if not HERO_ZIP.is_file():
        print(f"missing hero zip: {HERO_ZIP}", file=sys.stderr); return 2
    if args.cmd == "package":
        info = ensure_root_bot_zip(Path(args.src_dir), ZIP_DIR / f"{args.name}.zip")
        print(json.dumps(info, indent=2, sort_keys=True))
        return 0
    if args.cmd == "run":
        run_one(args.name, Path(args.src_dir), args.base, args.hands, args.match_len, args.seed_stride,
                args.repo, args.head_sha, args.bot_path, args.force)
        return 0
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
