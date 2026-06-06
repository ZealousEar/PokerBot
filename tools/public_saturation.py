"""Public-bot saturation sweeps for artifact-bound H2H evidence.

This is intentionally separate from tools/benchmark.py, which is still a
historical gate stub in this tree. It drives ext/fullhouse-engine directly,
packages public bots into root-bot.py archives under the artifact directory,
and writes one log plus one JSON sidecar per (opponent, seed base).
"""
import argparse
import json
import math
import os
import random
import shutil
import sys
import time
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
sys.path.insert(0, str(ENGINE_DIR))

from engine.game import BIG_BLIND  # noqa: E402
from sandbox import match as match_mod  # noqa: E402

ARTIFACT_DIR = ROOT / "consult" / "artifacts" / "2026-05-28-public-saturation"
HERO_ZIP = ROOT / "submissions" / "v_final.zip"

OPPONENTS = {
    "vladimir": {
        "src": ROOT / "ext" / "public-bots" / "vladimir" / "bots" / "vlad",
        "claimed_zip": ROOT / "ext" / "public-bots" / "vladimir" / "bots" / "vlad.zip",
        "bases": [142, 242, 342, 442],
    },
    "famadeo": {
        "src": ROOT / "ext" / "public-bots" / "famadeo" / "bots" / "codex_holdem",
        "bases": [142, 242],
    },
    "dominic": {
        "src": ROOT / "ext" / "public-bots" / "dominic" / "bots" / "dominic",
        "bases": [142, 242],
    },
    "neel": {
        "src": ROOT / "ext" / "public-bots" / "neel" / "bots" / "neel",
        "bases": [142, 242],
    },
}

BOOTSTRAP_ITERS = 5000
CI_ALPHA = 0.05


class InstrumentedBotProcess(match_mod.BotProcess):
    """BotProcess variant that records action latency and skips stdout noise."""

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


def ensure_root_bot_zip(src_dir: Path, out_zip: Path) -> dict:
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


def describe_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        names = sorted(z.namelist())
        has_root_bot = "bot.py" in names
        data_bytes = sum(info.file_size for info in z.infolist() if info.filename.startswith("data/"))
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "has_root_bot_py": has_root_bot,
        "data_bytes": data_bytes,
        "sha256": sha256(path),
    }


def sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    """Bootstrap seed-pair chip deltas into a scheduled-hand bb/100 CI."""
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
    return {
        "mean": mean,
        "low": low,
        "high": high,
        "half_width": (high - low) / 2.0,
    }


def verdict(mean, low, high):
    if mean > 0 and low > -20:
        return "GREEN"
    if high < 0:
        return "RED"
    return "AMBER"


def run_base(opponent, base, target_hands, match_len, seed_stride, force=False):
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = ARTIFACT_DIR / f"{opponent}_s{base}.log"
    json_path = ARTIFACT_DIR / f"{opponent}_s{base}.json"
    if json_path.is_file() and log_path.is_file() and not force:
        print(f"[skip] {opponent} base={base}: existing {json_path}")
        return json.loads(json_path.read_text())

    opp_info = OPPONENTS[opponent]
    opp_zip = ARTIFACT_DIR / "opponent_zips" / f"{opponent}.zip"
    opp_zip_info = ensure_root_bot_zip(opp_info["src"], opp_zip)
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

        line(f"PUBLIC SATURATION {now_iso()}")
        line(f"opponent={opponent} base={base}")
        line(f"hero={HERO_ZIP} sha256={hero_info['sha256']}")
        line(f"opponent_zip={opp_zip} sha256={opp_zip_info['sha256']}")
        if opp_info.get("claimed_zip"):
            claimed = opp_info["claimed_zip"]
            claimed_ok = claimed.is_file() and describe_zip(claimed)["has_root_bot_py"]
            line(f"claimed_zip={claimed} root_bot_py={claimed_ok}")
        line(f"target_scheduled_hands={target_hands} match_len={match_len} seed_stride={seed_stride}")
        line("seed schedule: seed = base + k * seed_stride; each seed runs two seat orientations")
        line()

        k = 0
        try:
            while attempted_total < target_hands:
                seed = base + k * seed_stride
                pair_chips = 0
                pair_hands = 0
                pair_attempted = 0
                pair_early = 0
                pair_hero_errors = 0
                pair_opp_errors = 0
                for orientation, paths in enumerate([
                    {"hero": str(HERO_ZIP.resolve()), "opp": str(opp_zip.resolve())},
                    {"opp": str(opp_zip.resolve()), "hero": str(HERO_ZIP.resolve())},
                ]):
                    match_id = f"public_{opponent}_s{base}_k{k}_seed{seed}_o{orientation}"
                    started = time.perf_counter()
                    row = {
                        "seed": seed,
                        "orientation": orientation,
                        "match_id": match_id,
                        "attempted_hands": match_len,
                    }
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
                    hero_errors += he
                    opp_errors += oe
                    pair_hero_errors += he
                    pair_opp_errors += oe
                    if int(row["hands"]) < match_len:
                        early_bust_matches += 1
                        pair_early += 1
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
                        f"[run] {opponent} base={base} pairs={k + 1} "
                        f"scheduled={attempted_total}/{target_hands} actual={hands_total} "
                        f"bb100_sched={bb100(sum(s['chip_delta'] for s in samples), attempted_total):+.2f}",
                        flush=True,
                    )
                k += 1
        finally:
            match_mod.BotProcess = original_bot_process

        ci = bootstrap_ci(samples, seed=base ^ 0xBAD5EED)
        hero_lat = InstrumentedBotProcess.latencies.get("hero", [])
        opp_lat = InstrumentedBotProcess.latencies.get("opp", [])
        result = {
            "opponent": opponent,
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
            "log_path": str(log_path),
            "json_path": str(json_path),
        }
        line()
        line("SUMMARY_JSON " + json.dumps({k: v for k, v in result.items() if k != "samples"}, sort_keys=True))
        line(
            f"SUMMARY opponent={opponent} base={base} verdict={result['verdict']} "
            f"bb100={ci['mean']:+.2f} ci=[{ci['low']:+.2f},{ci['high']:+.2f}] "
            f"half_width={ci['half_width']:.2f} scheduled={attempted_total} actual_hands={hands_total} "
            f"early_bust_rate={result['early_bust_rate']:.3f} hero_errors={hero_errors} "
            f"hero_p99_latency_s={result['hero_p99_decide_latency_s']:.4f}"
        )

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"[done] {opponent} base={base} verdict={result['verdict']} "
        f"bb100={result['hero_bb_per_100']:+.2f} ci=[{result['ci_low']:+.2f},{result['ci_high']:+.2f}] "
        f"half_width={result['ci_half_width']:.2f} hands={result['hands_played']} log={log_path}",
        flush=True,
    )
    return result


def load_expected_results():
    rows = []
    missing = []
    for opponent, info in OPPONENTS.items():
        for base in info["bases"]:
            path = ARTIFACT_DIR / f"{opponent}_s{base}.json"
            log_path = ARTIFACT_DIR / f"{opponent}_s{base}.log"
            if not path.is_file() or not log_path.is_file():
                missing.append((opponent, base))
                continue
            rows.append(json.loads(path.read_text()))
    return rows, missing


def aggregate_results(write=True):
    rows, missing = load_expected_results()
    by_opp = {}
    for row in rows:
        by_opp.setdefault(row["opponent"], []).append(row)

    aggregates = {}
    for opponent, opp_rows in sorted(by_opp.items()):
        samples = []
        for row in opp_rows:
            samples.extend(row["samples"])
        ci = bootstrap_ci(samples, seed=sum(ord(c) for c in opponent) ^ 0x51A7)
        matches = sum(r["matches"] for r in opp_rows)
        early = sum(r["early_bust_matches"] for r in opp_rows)
        aggregates[opponent] = {
            "opponent": opponent,
            "bases": [r["base"] for r in sorted(opp_rows, key=lambda x: x["base"])],
            "runs": len(opp_rows),
            "seed_pairs": sum(r["seed_pairs"] for r in opp_rows),
            "matches": matches,
            "hands_played": sum(r["hands_played"] for r in opp_rows),
            "attempted_hands": sum(r["attempted_hands"] for r in opp_rows),
            "hero_chip_delta": sum(r["hero_chip_delta"] for r in opp_rows),
            "hero_bb_per_100": ci["mean"],
            "hero_actual_bb_per_100": bb100(
                sum(r["hero_chip_delta"] for r in opp_rows),
                sum(r["hands_played"] for r in opp_rows),
            ),
            "ci_low": ci["low"],
            "ci_high": ci["high"],
            "ci_half_width": ci["half_width"],
            "verdict": verdict(ci["mean"], ci["low"], ci["high"]),
            "early_bust_rate": early / matches if matches else 0.0,
            "hero_errors": sum(r["hero_errors"] for r in opp_rows),
            "opponent_errors": sum(r["opponent_errors"] for r in opp_rows),
            "hero_p99_decide_latency_s": max((r["hero_p99_decide_latency_s"] for r in opp_rows), default=0.0),
            "stdout_noise": {
                "hero": sum(r.get("stdout_noise", {}).get("hero", 0) for r in opp_rows),
                "opp": sum(r.get("stdout_noise", {}).get("opp", 0) for r in opp_rows),
            },
        }

    summary = {
        "created_at": now_iso(),
        "artifact_dir": str(ARTIFACT_DIR),
        "hero_zip": str(HERO_ZIP),
        "hero_sha256": sha256(HERO_ZIP),
        "missing": [{"opponent": o, "base": b} for o, b in missing],
        "runs": rows,
        "aggregates": aggregates,
    }

    if write:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        (ARTIFACT_DIR / "RESULTS.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (ARTIFACT_DIR / "SUMMARY.md").write_text(render_summary(summary), encoding="utf-8")
    return summary


def render_summary(summary):
    lines = []
    lines.append("# Public Bot Saturation - 2026-05-28")
    lines.append("")
    lines.append(f"- Artifact: `{summary['hero_zip']}`")
    lines.append(f"- Artifact sha256: `{summary['hero_sha256']}`")
    lines.append(f"- Evidence directory: `{summary['artifact_dir']}`")
    lines.append("- Verdict rule: GREEN = mean > 0 and CI low > -20; RED = CI high < 0; AMBER = mixed.")
    lines.append("- CI unit: bootstrap 95% CI over paired seed-pair chip deltas, reported as bb/100 over scheduled hands.")
    lines.append("- p99 latency is the conservative max of per-base local runner p99 decide latencies.")
    if summary["missing"]:
        lines.append(f"- Missing runs: `{summary['missing']}`")
    lines.append("")
    lines.append("| Opponent | Bases | Verdict | Mean bb/100 | 95% CI | Half-width | Scheduled | Actual | Early-bust rate | Hero errors | Hero p99 latency |")
    lines.append("|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for opponent in ["vladimir", "famadeo", "dominic", "neel"]:
        agg = summary["aggregates"].get(opponent)
        if not agg:
            lines.append(f"| {opponent} | - | MISSING | - | - | - | - | - | - | - |")
            continue
        bases = ",".join(str(b) for b in agg["bases"])
        lines.append(
            f"| {opponent} | {bases} | {agg['verdict']} | {agg['hero_bb_per_100']:+.2f} | "
            f"[{agg['ci_low']:+.2f}, {agg['ci_high']:+.2f}] | {agg['ci_half_width']:.2f} | "
            f"{agg['attempted_hands']} | {agg['hands_played']} | {agg['early_bust_rate']:.1%} | {agg['hero_errors']} | "
            f"{agg['hero_p99_decide_latency_s']:.4f}s |"
        )
    lines.append("")
    lines.append("## Per-Base Runs")
    lines.append("")
    lines.append("| Opponent | Base | Log | Verdict | Mean bb/100 | 95% CI | Half-width | Scheduled | Actual | Early-bust rate | Hero errors | Opp errors |")
    lines.append("|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in sorted(summary["runs"], key=lambda r: (r["opponent"], r["base"])):
        log_name = Path(row["log_path"]).name
        lines.append(
            f"| {row['opponent']} | {row['base']} | `{log_name}` | {row['verdict']} | "
            f"{row['hero_bb_per_100']:+.2f} | [{row['ci_low']:+.2f}, {row['ci_high']:+.2f}] | "
            f"{row['ci_half_width']:.2f} | {row['attempted_hands']} | {row['hands_played']} | {row['early_bust_rate']:.1%} | "
            f"{row['hero_errors']} | {row['opponent_errors']} |"
        )
    lines.append("")
    lines.append("## Packaging")
    lines.append("")
    lines.append("Public bots were packaged into valid root-`bot.py` zips under `opponent_zips/`; `ext/fullhouse-engine/` was not modified.")
    return "\n".join(lines) + "\n"


def append_status(summary):
    status = ROOT / "STATUS.md"
    lines = []
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## {now_iso()} · PUBLIC-SATURATION · GREEN (public-bot matchup bands resolved)")
    lines.append("- Goal: resolve public-bot matchup bands for canonical `submissions/v_final.zip`.")
    lines.append(f"- Artifact sha256: `{summary['hero_sha256']}`.")
    lines.append(f"- Evidence: `consult/artifacts/2026-05-28-public-saturation/` with one `<opp>_s<base>.log` and JSON sidecar per requested run.")
    lines.append("- Method: artifact-bound paired H2H, two seat orientations per seed, bootstrap 95% CI over paired seed-pair chip deltas normalized by scheduled hands.")
    lines.append("- Verdicts:")
    for opponent in ["vladimir", "famadeo", "dominic", "neel"]:
        agg = summary["aggregates"].get(opponent)
        if not agg:
            lines.append(f"  - {opponent}: MISSING")
            continue
        lines.append(
            f"  - {opponent}: {agg['verdict']} mean={agg['hero_bb_per_100']:+.2f} "
            f"CI=[{agg['ci_low']:+.2f},{agg['ci_high']:+.2f}] "
            f"half_width={agg['ci_half_width']:.2f} scheduled={agg['attempted_hands']} actual_hands={agg['hands_played']} "
            f"early_bust_rate={agg['early_bust_rate']:.1%} hero_errors={agg['hero_errors']} "
            f"hero_p99_latency={agg['hero_p99_decide_latency_s']:.4f}s"
        )
    lines.append("- Files changed: `tools/public_saturation.py`, `consult/artifacts/2026-05-28-public-saturation/{SUMMARY.md,RESULTS.json,*.log,*.json,opponent_zips/*.zip}`, `STATUS.md`.")
    lines.append("- Next action: keep `submissions/v_final.zip` unchanged; use any AMBER/RED public-bot cells as finals-review inputs only.")
    with status.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--opponent", choices=sorted(OPPONENTS), help="Run one opponent")
    p.add_argument("--base", type=int, help="Run one base for --opponent")
    p.add_argument("--all", action="store_true", help="Run the full requested matrix")
    p.add_argument("--aggregate", action="store_true", help="Regenerate SUMMARY.md and RESULTS.json")
    p.add_argument("--append-status", action="store_true", help="Append STATUS.md from current aggregate")
    p.add_argument("--hands", type=int, default=100000, help="Scheduled hands per (opponent, base); actual hands may be lower after bust-outs")
    p.add_argument("--match-len", type=int, default=500)
    p.add_argument("--seed-stride", type=int, default=1000)
    p.add_argument("--force", action="store_true", help="Rerun even if JSON/log exist")
    return p.parse_args()


def main():
    args = parse_args()
    if not HERO_ZIP.is_file():
        print(f"missing hero zip: {HERO_ZIP}", file=sys.stderr)
        return 2
    if args.all:
        for opponent, info in OPPONENTS.items():
            for base in info["bases"]:
                run_base(opponent, base, args.hands, args.match_len, args.seed_stride, force=args.force)
        aggregate_results(write=True)
        return 0
    if args.opponent:
        bases = [args.base] if args.base is not None else OPPONENTS[args.opponent]["bases"]
        for base in bases:
            run_base(args.opponent, base, args.hands, args.match_len, args.seed_stride, force=args.force)
        aggregate_results(write=True)
        return 0
    if args.aggregate or args.append_status:
        summary = aggregate_results(write=True)
        if args.append_status:
            if summary["missing"]:
                print(f"refusing to append STATUS with missing runs: {summary['missing']}", file=sys.stderr)
                return 3
            append_status(summary)
        return 0
    print("Specify --all, --opponent, --aggregate, or --append-status", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
