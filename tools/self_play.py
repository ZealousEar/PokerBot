"""Self-play harness — runs N hands of our bot vs a named opponent.

Drives `ext/fullhouse-engine/sandbox/match.py` and reports crashes, illegal
actions, and timeouts.

Usage:
    python tools/self_play.py --opponent template --hands 100 [--strict]
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--opponent", required=True,
                   help="Name in ext/fullhouse-engine/bots/")
    p.add_argument("--hands", type=int, default=100)
    p.add_argument("--strict", action="store_true",
                   help="Exit nonzero on any crash, illegal action, or timeout")
    args = p.parse_args()

    if not ENGINE_DIR.exists():
        print(f"FAIL: engine not cloned at {ENGINE_DIR}")
        return 4

    # TODO (G1): import sandbox.match, instantiate a 2-bot match (ours vs opponent),
    # drive N hands, parse runner stderr for "TIMEOUT" / "BOT EXCEPTION" / "BAD JSON",
    # count illegal-action defaults. In --strict mode, exit 1 on any incident.
    print(f"TODO (G1): run {args.hands} hands vs {args.opponent} (strict={args.strict})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
