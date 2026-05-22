"""Replay a hand-history JSON through `src.bot.decide` for reproducible
diagnosis. Useful during the patch window (`docs/playbooks/patch-window.md`).

Usage:
    python tools/replay.py --hand path/to/history.json
"""
import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--hand", type=Path, required=True)
    args = p.parse_args()
    history = json.loads(args.hand.read_text())
    # TODO: walk decision points in history, call src.bot.decide on each
    # reconstructed game_state, print action_under_test vs action_in_history.
    print(f"TODO: replay {len(history.get('events', []))} events from {args.hand}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
