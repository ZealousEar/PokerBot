"""Estimate 400-hand qualifier chip-delta distributions for six-max pods.

Runs the existing Fullhouse sandbox match runner directly, then writes:
  - matches.jsonl: one raw hero result per pod/seed
  - pod_summary.json: distribution stats and operational metrics
  - SUMMARY.md: compact color table
  - STATUS_BLOCK.md: ready-to-append STATUS.md block
"""
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
sys.path.insert(0, str(ENGINE_DIR))

from sandbox import match as match_mod  # noqa: E402
from engine.game import STARTING_STACK  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "consult" / "artifacts" / "2026-05-28-pods"
HERO_ID = "hero"

BOT_PATHS = {
    "hero": ROOT / "submissions" / "v_final.zip",
    "template": ENGINE_DIR / "bots" / "template",
    "aggressor": ENGINE_DIR / "bots" / "aggressor",
    "mathematician": ENGINE_DIR / "bots" / "mathematician",
    "shark": ENGINE_DIR / "bots" / "shark",
    "ref_bot_2": ENGINE_DIR / "bots" / "ref_bot_2",
    "neel": ROOT / "ext" / "public-bots" / "neel" / "bots" / "neel",
    "dominic": ROOT / "ext" / "public-bots" / "dominic" / "bots" / "dominic",
    "famadeo": ROOT / "ext" / "public-bots" / "famadeo" / "bots" / "codex_holdem",
    "vladimir": ROOT / "ext" / "public-bots" / "vladimir" / "bots" / "vlad",
}

PODS = {
    "C1": ["hero", "template", "aggressor", "mathematician", "shark", "ref_bot_2"],
    "C2": ["hero", "neel", "dominic", "famadeo", "vladimir", "shark"],
    "C3": ["hero", "neel", "dominic", "famadeo", "aggressor", "mathematician"],
    "C4": ["hero", "vladimir", "famadeo", "template", "shark", "ref_bot_2"],
}


class DecisionTimer:
    """Thread-safe monkeypatch around BotProcess.act for per-decision timing."""

    def __init__(self):
        self._tls = threading.local()
        self._lock = threading.Lock()
        self._metrics = {}
        self._orig_init = match_mod.BotProcess.__init__
        self._orig_act = match_mod.BotProcess.act
        self._installed = False

    def install(self):
        if self._installed:
            return

        timer = self

        def patched_init(proc_self, bot_id, bot_path):
            timer._orig_init(proc_self, bot_id, bot_path)
            proc_self._qualifier_match_id = getattr(timer._tls, "match_id", None)

        def patched_act(proc_self, game_state):
            started = time.perf_counter()
            action = timer._orig_act(proc_self, game_state)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            match_id = getattr(proc_self, "_qualifier_match_id", None)
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

    def uninstall(self):
        if not self._installed:
            return
        match_mod.BotProcess.__init__ = self._orig_init
        match_mod.BotProcess.act = self._orig_act
        self._installed = False

    def set_match(self, match_id):
        self._tls.match_id = match_id
        with self._lock:
            self._metrics[match_id] = {"latencies_ms": {}, "decision_counts": {}, "error_counts": {}}

    def clear_match(self):
        if hasattr(self._tls, "match_id"):
            del self._tls.match_id

    def pop_metrics(self, match_id):
        with self._lock:
            return self._metrics.pop(
                match_id,
                {"latencies_ms": {}, "decision_counts": {}, "error_counts": {}},
            )


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(path):
    try:
        res = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return res.stdout.strip()


def percentile(values, pct):
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


def p99(values):
    return percentile(values, 99)


def round_or_none(value, digits=2):
    if value is None:
        return None
    return round(float(value), digits)


def fmt_num(value, digits=0):
    if value is None:
        return "n/a"
    if digits == 0:
        return str(int(round(float(value))))
    return f"{float(value):.{digits}f}"


def verdict_for(stats):
    if stats["p50"] is not None and stats["p50"] > 0 and stats["p10"] is not None and stats["p10"] > -5000:
        return "GREEN"
    if stats["p50"] is not None and stats["p50"] > 0:
        return "AMBER"
    return "RED"


def distribution_stats(chip_deltas):
    if not chip_deltas:
        return {
            "p10": None,
            "p50": None,
            "p90": None,
            "mean": None,
            "stdev": None,
            "min": None,
            "max": None,
        }
    return {
        "p10": round_or_none(percentile(chip_deltas, 10)),
        "p50": round_or_none(percentile(chip_deltas, 50)),
        "p90": round_or_none(percentile(chip_deltas, 90)),
        "mean": round_or_none(statistics.mean(chip_deltas)),
        "stdev": round_or_none(statistics.stdev(chip_deltas) if len(chip_deltas) > 1 else 0.0),
        "min": int(min(chip_deltas)),
        "max": int(max(chip_deltas)),
    }


def ensure_inputs():
    missing = [name for name, path in BOT_PATHS.items() if not path.exists()]
    if missing:
        details = ", ".join(f"{name}={BOT_PATHS[name]}" for name in missing)
        raise FileNotFoundError(f"Missing bot path(s): {details}")
    if not (ENGINE_DIR / "sandbox" / "match.py").is_file():
        raise FileNotFoundError(f"Missing match.py under {ENGINE_DIR}")


def match_paths(pod_name):
    return {name: str(BOT_PATHS[name].resolve()) for name in PODS[pod_name]}


def run_one_match(pod_name, seed, hands, timer):
    match_id = f"qualpods_{pod_name}_s{seed}"
    timer.set_match(match_id)
    try:
        result = match_mod.run_match(
            match_id,
            match_paths(pod_name),
            n_hands=hands,
            verbose=False,
            seed=seed,
        )
    finally:
        timer.clear_match()

    timing = timer.pop_metrics(match_id)
    hero_latencies = timing["latencies_ms"].get(HERO_ID, [])
    hero_decisions = timing["decision_counts"].get(HERO_ID, 0)
    hero_action_errors = timing["error_counts"].get(HERO_ID, 0)
    hero_bot_errors = result["bot_errors"].get(HERO_ID, [])
    final_stack = result["final_stacks"][HERO_ID]

    return {
        "pod": pod_name,
        "seed": seed,
        "match_id": match_id,
        "requested_hands": hands,
        "n_hands": result["n_hands"],
        "duration_s": result["duration_s"],
        "hero_chip_delta": result["chip_delta"][HERO_ID],
        "hero_final_stack": final_stack,
        "hero_busted": final_stack <= 0,
        "hero_decisions": hero_decisions,
        "hero_action_errors": hero_action_errors,
        "hero_error_rate": (hero_action_errors / hero_decisions) if hero_decisions else None,
        "hero_bot_errors": hero_bot_errors,
        "hero_latencies_ms": [round(float(v), 3) for v in hero_latencies],
        "hero_p99_decide_latency_ms": round_or_none(p99(hero_latencies), 3),
        "bot_error_counts": {bid: len(errors) for bid, errors in result["bot_errors"].items()},
        "chip_delta": result["chip_delta"],
        "final_stacks": result["final_stacks"],
        "pod_members": PODS[pod_name],
    }


def load_existing(matches_path):
    records = {}
    if not matches_path.is_file():
        return records
    with matches_path.open() as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            records[(record["pod"], int(record["seed"]))] = record
    return records


def append_record(matches_path, record):
    with matches_path.open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def aggregate(records, pods, seeds, hands):
    pods_out = {}
    for pod in pods:
        pod_records = [records[(pod, seed)] for seed in seeds if (pod, seed) in records]
        chip_deltas = [r["hero_chip_delta"] for r in pod_records]
        stats = distribution_stats(chip_deltas)
        hero_decisions = sum(r["hero_decisions"] for r in pod_records)
        hero_action_errors = sum(r["hero_action_errors"] for r in pod_records)
        hero_error_rate = (hero_action_errors / hero_decisions) if hero_decisions else None
        hero_latencies = []
        for record in pod_records:
            hero_latencies.extend(record.get("hero_latencies_ms", []))

        bot_error_counts = {}
        for record in pod_records:
            for bot_id, count in record["bot_error_counts"].items():
                bot_error_counts[bot_id] = bot_error_counts.get(bot_id, 0) + count

        pods_out[pod] = {
            "members": PODS[pod],
            "requested_matches": len(seeds),
            "completed_matches": len(pod_records),
            "hands_requested_per_match": hands,
            "hands_played_total": sum(r["n_hands"] for r in pod_records),
            "chip_delta_stats": stats,
            "verdict": verdict_for(stats),
            "bust_rate": round_or_none(
                sum(1 for r in pod_records if r["hero_busted"]) / len(pod_records)
                if pod_records
                else None,
                4,
            ),
            "hero_decisions": hero_decisions,
            "hero_action_errors": hero_action_errors,
            "hero_error_rate": round_or_none(hero_error_rate, 6),
            "hero_p99_decide_latency_ms": round_or_none(p99(hero_latencies), 3),
            "bot_error_counts": bot_error_counts,
            "runs": sorted(
                [
                    {
                        "seed": r["seed"],
                        "match_id": r["match_id"],
                        "n_hands": r["n_hands"],
                        "duration_s": r["duration_s"],
                        "hero_chip_delta": r["hero_chip_delta"],
                        "hero_final_stack": r["hero_final_stack"],
                        "hero_busted": r["hero_busted"],
                        "hero_decisions": r["hero_decisions"],
                        "hero_action_errors": r["hero_action_errors"],
                        "hero_error_rate": round_or_none(r["hero_error_rate"], 6),
                        "hero_p99_decide_latency_ms": r["hero_p99_decide_latency_ms"],
                    }
                    for r in pod_records
                ],
                key=lambda r: r["seed"],
            ),
        }
    return pods_out


def write_summary_md(path, summary):
    lines = [
        "# Qualifier Pod Distribution - 2026-05-28",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Hero artifact: `{summary['artifact']['hero_path']}`",
        f"Hero SHA-256: `{summary['artifact']['hero_sha256']}`",
        f"Engine commit: `{summary['artifact']['engine_commit']}`",
        f"Schedule: `{summary['artifact']['hands_per_match']}` hands x "
        f"`{summary['artifact']['seeds_per_pod']}` seeds per pod "
        f"(seed base `{summary['artifact']['seed_base']}`), local `match.py` runner.",
        "",
        "## Color Table",
        "",
        "| Pod | Color | p10 | p50 | p90 | mean | stdev | bust rate | hero error rate | hero p99 decide ms |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for pod, data in summary["pods"].items():
        stats = data["chip_delta_stats"]
        lines.append(
            f"| {pod} | {data['verdict']} | {fmt_num(stats['p10'])} | {fmt_num(stats['p50'])} | "
            f"{fmt_num(stats['p90'])} | {fmt_num(stats['mean'])} | {fmt_num(stats['stdev'])} | "
            f"{fmt_num(data['bust_rate'] * 100 if data['bust_rate'] is not None else None, 1)}% | "
            f"{fmt_num(data['hero_error_rate'] * 100 if data['hero_error_rate'] is not None else None, 3)}% | "
            f"{fmt_num(data['hero_p99_decide_latency_ms'], 3)} |"
        )

    lines += [
        "",
        "## Pod Composition",
        "",
        "| Pod | Seats |",
        "| --- | --- |",
    ]
    for pod, data in summary["pods"].items():
        lines.append(f"| {pod} | {', '.join(data['members'])} |")

    lines += [
        "",
        "Color rules: GREEN = p50 > 0 and p10 > -5000; AMBER = p50 > 0; RED = p50 <= 0.",
        "Hero error rate is action errors divided by hero decisions. Latency is based on local `BotProcess.act()` wall-clock timing.",
        "",
    ]
    path.write_text("\n".join(lines))


def status_block(summary):
    overall = "GREEN" if all(p["verdict"] == "GREEN" for p in summary["pods"].values()) else "AMBER"
    if any(p["verdict"] == "RED" for p in summary["pods"].values()):
        overall = "RED"
    lines = [
        f"## {summary['generated_at']} · QUAL-PODS · {overall}",
        f"- Goal: Estimate canonical `submissions/v_final.zip` 400-hand qualifier chip-delta distribution across four realistic six-max pods.",
        f"- Artifact: `submissions/v_final.zip` sha `{summary['artifact']['hero_sha256'][:12]}…`; engine `ext/fullhouse-engine` commit `{summary['artifact']['engine_commit']}`; runner `ext/fullhouse-engine/sandbox/match.py`; `USE_DOCKER={summary['artifact']['use_docker']}`.",
        f"- Schedule: {len(summary['pods'])} pods × {summary['artifact']['seeds_per_pod']} seeds × {summary['artifact']['hands_per_match']} hands = {summary['artifact']['total_requested_matches']} matches.",
        "- Pod color table:",
        "",
        "| Pod | Seats | Color | p10 | p50 | p90 | mean | stdev | bust rate | hero error rate | p99 ms |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for pod, data in summary["pods"].items():
        stats = data["chip_delta_stats"]
        seats = ", ".join(data["members"])
        lines.append(
            f"| {pod} | {seats} | {data['verdict']} | {fmt_num(stats['p10'])} | "
            f"{fmt_num(stats['p50'])} | {fmt_num(stats['p90'])} | {fmt_num(stats['mean'])} | "
            f"{fmt_num(stats['stdev'])} | "
            f"{fmt_num(data['bust_rate'] * 100 if data['bust_rate'] is not None else None, 1)}% | "
            f"{fmt_num(data['hero_error_rate'] * 100 if data['hero_error_rate'] is not None else None, 3)}% | "
            f"{fmt_num(data['hero_p99_decide_latency_ms'], 3)} |"
        )

    lines += [
        "",
        f"- Files changed: `tools/qualifier_pods.py`, `consult/artifacts/2026-05-28-pods/{{matches.jsonl,pod_summary.json,SUMMARY.md,STATUS_BLOCK.md}}`, `STATUS.md`.",
        "- Validator / import_audit / edge / smoke / leakage / exploit: N/A for this distribution-estimation gate; the harness exercised the real sandbox match runner and captured hero errors/latency per decision.",
        "- Next action: interpret the pod-color matrix; qualifier artifact remains unchanged.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(output_dir, records, pods, seeds, hands, seed_base):
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    hero_path = BOT_PATHS["hero"].resolve()
    pods_out = aggregate(records, pods, seeds, hands)
    summary = {
        "generated_at": generated_at,
        "artifact": {
            "hero_path": str(hero_path.relative_to(ROOT)),
            "hero_sha256": sha256_file(hero_path),
            "engine_commit": git_head(ENGINE_DIR),
            "root_commit": git_head(ROOT),
            "match_py": str((ENGINE_DIR / "sandbox" / "match.py").relative_to(ROOT)),
            "use_docker": os.environ.get("USE_DOCKER", "false").lower() == "true",
            "hands_per_match": hands,
            "seeds_per_pod": len(seeds),
            "seed_base": seed_base,
            "seeds": list(seeds),
            "total_requested_matches": len(pods) * len(seeds),
            "starting_stack": STARTING_STACK,
        },
        "pods": pods_out,
    }
    (output_dir / "pod_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_summary_md(output_dir / "SUMMARY.md", summary)
    (output_dir / "STATUS_BLOCK.md").write_text(status_block(summary) + "\n")
    return summary


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--hands", type=int, default=400)
    p.add_argument("--seed-base", type=int, default=42)
    p.add_argument("--seeds", type=int, default=100)
    p.add_argument("--pods", nargs="+", choices=sorted(PODS), default=sorted(PODS))
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--force", action="store_true", help="remove existing generated files before running")
    return p.parse_args()


def main():
    args = parse_args()
    ensure_inputs()

    output_dir = Path(args.output_dir)
    if args.force and output_dir.exists():
        for name in ("matches.jsonl", "pod_summary.json", "SUMMARY.md", "STATUS_BLOCK.md"):
            path = output_dir / name
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)
    matches_path = output_dir / "matches.jsonl"

    seeds = list(range(args.seed_base, args.seed_base + args.seeds))
    records = load_existing(matches_path)
    tasks = [(pod, seed) for pod in args.pods for seed in seeds if (pod, seed) not in records]
    print(
        f"[qualifier_pods] output={output_dir} pods={','.join(args.pods)} "
        f"hands={args.hands} seeds={args.seed_base}..{args.seed_base + args.seeds - 1} "
        f"jobs={args.jobs} pending={len(tasks)} resumed={len(records)}",
        flush=True,
    )

    timer = DecisionTimer()
    timer.install()
    try:
        if args.jobs <= 1:
            for pod, seed in tasks:
                record = run_one_match(pod, seed, args.hands, timer)
                records[(pod, seed)] = record
                append_record(matches_path, record)
                print_progress(record)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
                future_to_key = {
                    executor.submit(run_one_match, pod, seed, args.hands, timer): (pod, seed)
                    for pod, seed in tasks
                }
                for future in concurrent.futures.as_completed(future_to_key):
                    pod, seed = future_to_key[future]
                    try:
                        record = future.result()
                    except Exception as exc:
                        print(f"[qualifier_pods] FAIL pod={pod} seed={seed}: {exc}", file=sys.stderr, flush=True)
                        raise
                    records[(pod, seed)] = record
                    append_record(matches_path, record)
                    print_progress(record)
    finally:
        timer.uninstall()

    missing = [(pod, seed) for pod in args.pods for seed in seeds if (pod, seed) not in records]
    if missing:
        print(f"[qualifier_pods] incomplete: missing {len(missing)} pod/seed runs", file=sys.stderr)
        return 1

    summary = write_outputs(output_dir, records, args.pods, seeds, args.hands, args.seed_base)
    print(f"[qualifier_pods] wrote {output_dir / 'pod_summary.json'}")
    for pod, data in summary["pods"].items():
        stats = data["chip_delta_stats"]
        print(
            f"[qualifier_pods] {pod} {data['verdict']} "
            f"p10={fmt_num(stats['p10'])} p50={fmt_num(stats['p50'])} "
            f"p90={fmt_num(stats['p90'])} mean={fmt_num(stats['mean'])} "
            f"stdev={fmt_num(stats['stdev'])} bust={fmt_num(data['bust_rate'] * 100, 1)}% "
            f"err={fmt_num(data['hero_error_rate'] * 100, 3)}% "
            f"p99_ms={fmt_num(data['hero_p99_decide_latency_ms'], 3)}",
            flush=True,
        )
    return 0


def print_progress(record):
    print(
        f"[qualifier_pods] {record['pod']} seed={record['seed']} "
        f"hands={record['n_hands']} delta={record['hero_chip_delta']:+d} "
        f"bust={int(record['hero_busted'])} "
        f"hero_err={record['hero_action_errors']}/{record['hero_decisions']} "
        f"p99_ms={fmt_num(record['hero_p99_decide_latency_ms'], 3)} "
        f"dur={record['duration_s']}s",
        flush=True,
    )


if __name__ == "__main__":
    sys.exit(main())
