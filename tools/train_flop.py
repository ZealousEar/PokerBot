"""Offline flop bucket + strategy generation.

Outputs:
    data/flop_buckets.npz    # bucket id per canonical flop
    data/flop_strategy.npz   # action distribution per bucket × hand bin
"""
import argparse
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--buckets", type=int, default=200)
    p.add_argument("--hand-bins", type=int, default=50)
    args = p.parse_args()
    # TODO (G3): cluster flops into N buckets, run MCCFR per bucket × hand bin
    print(f"TODO (G3): {args.buckets} flop buckets × {args.hand_bins} hand bins")
    return 0


if __name__ == "__main__":
    sys.exit(main())
