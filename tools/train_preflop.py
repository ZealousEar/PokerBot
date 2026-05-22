"""Offline preflop blueprint generation.

Output: `data/preflop_blueprint.npz` (numpy.savez_compressed).
Runs locally, not in the sandbox — training compute is unrestricted.

# Source: [[PokerBot/Pluribus/Brown-Sandholm-2019]] — 6-max blueprint
# Source: [[PokerBot/MCCFR/Lanctot-2009]] — sampling strategy
"""
import argparse
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="data/preflop_blueprint.npz")
    p.add_argument("--iters", type=int, default=1_000_000)
    args = p.parse_args()
    # TODO (G2): MCCFR over 6-max preflop tree; save with numpy.savez_compressed
    print(f"TODO (G2): train {args.iters} iters, write {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
