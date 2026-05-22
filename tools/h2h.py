"""H2H — paired-seed head-to-head between two bot artifacts.

Each seed is played twice with seats swapped (A-vs-B, then B-vs-A) so cards
and dealer position cancel out. Reports A's per-match BB delta + bootstrap
95% CI + aggregate bb/100.

Usage:
    python tools/h2h.py --bot-a <path.zip> --bot-b <path.zip> \
        [--hands 10000] [--paired-seed-base 42] \
        [--label-a claude] [--label-b codex] [--match-len 200]
"""
import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
sys.path.insert(0, str(ENGINE_DIR))

from sandbox.match import run_match  # noqa: E402
from engine.game import BIG_BLIND  # noqa: E402


def bootstrap_ci(samples, iters=2000, alpha=0.05):
    n = len(samples)
    if n == 0:
        return 0.0, 0.0, 0.0
    boot = []
    for _ in range(iters):
        s = 0.0
        for _ in range(n):
            s += random.choice(samples)
        boot.append(s / n)
    boot.sort()
    return (
        sum(samples) / n,
        boot[int(iters * alpha / 2)],
        boot[int(iters * (1 - alpha / 2))],
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bot-a", required=True)
    p.add_argument("--bot-b", required=True)
    p.add_argument("--hands", type=int, default=10000)
    p.add_argument("--paired-seed-base", type=int, default=42)
    p.add_argument("--match-len", type=int, default=200)
    p.add_argument("--label-a", default="a")
    p.add_argument("--label-b", default="b")
    args = p.parse_args()

    random.seed(args.paired_seed_base ^ 0xDEADBEEF)

    n_matches_total = max(2, args.hands // args.match_len)
    seed_count = (n_matches_total + 1) // 2

    a_path = str(Path(args.bot_a).resolve())
    b_path = str(Path(args.bot_b).resolve())

    a_bb_deltas = []
    a_chip_deltas = []
    bot_errors_total = {"a": 0, "b": 0}
    hands_played_total = 0

    print(f"H2H: {args.label_a} (a) vs {args.label_b} (b)")
    print(f"  bot-a: {a_path}")
    print(f"  bot-b: {b_path}")
    print(f"  schedule: {seed_count} seeds × 2 orientations × {args.match_len} hands "
          f"= up to {seed_count * 2 * args.match_len} hands")
    print(flush=True)

    for k in range(seed_count):
        seed = args.paired_seed_base + k
        for orientation, paths in enumerate([
            {"a": a_path, "b": b_path},
            {"b": b_path, "a": a_path},
        ]):
            match_id = f"h2h_s{seed}_o{orientation}"
            r = run_match(match_id, paths, n_hands=args.match_len,
                          verbose=False, seed=seed)
            chip_a = r["chip_delta"]["a"]
            a_chip_deltas.append(chip_a)
            a_bb_deltas.append(chip_a / BIG_BLIND)
            hands_played_total += r["n_hands"]
            errs = {bid: len(e) for bid, e in r["bot_errors"].items()}
            for bid, e in r["bot_errors"].items():
                bot_errors_total[bid] += len(e)
            print(f"  seed={seed} o={orientation} hands={r['n_hands']:3d} "
                  f"chip_a={chip_a:+7d} bb_a={chip_a / BIG_BLIND:+7.1f} "
                  f"err={errs} dur={r['duration_s']}s",
                  flush=True)

    mean_bb, lo_bb, hi_bb = bootstrap_ci(a_bb_deltas)
    total_bb_a = sum(a_chip_deltas) / BIG_BLIND
    bb_per_100 = total_bb_a / (hands_played_total / 100) if hands_played_total else 0.0

    if mean_bb > 0 and lo_bb > 0:
        verdict = f"{args.label_a} BEATS {args.label_b} (CI excludes 0)"
    elif mean_bb < 0 and hi_bb < 0:
        verdict = f"{args.label_a} loses to {args.label_b} (CI excludes 0)"
    else:
        verdict = f"{args.label_a} vs {args.label_b} INDETERMINATE (CI crosses 0)"

    print()
    print("=" * 70)
    print(f"H2H summary: {args.label_a} (a) vs {args.label_b} (b)")
    print(f"  matches: {len(a_bb_deltas)}")
    print(f"  hands played total: {hands_played_total}")
    print(f"  {args.label_a} per-match BB delta: {mean_bb:+.2f} "
          f"(95% CI [{lo_bb:+.2f}, {hi_bb:+.2f}])")
    print(f"  {args.label_a} bb/100: {bb_per_100:+.2f}")
    print(f"  {args.label_a} errors: {bot_errors_total['a']}")
    print(f"  {args.label_b} errors: {bot_errors_total['b']}")
    print(f"  verdict: {verdict}")
    print("=" * 70)


if __name__ == "__main__":
    main()
