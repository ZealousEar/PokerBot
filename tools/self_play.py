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
# Mirror tests/conftest.py: probe the sandbox runner file, not just the dir,
# so a partial checkout without the sandbox is also caught.
ENGINE_RUNNER = ENGINE_DIR / "sandbox" / "runner.py"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--opponent", required=True,
                   help="Name in ext/fullhouse-engine/bots/")
    p.add_argument("--hands", type=int, default=100)
    p.add_argument("--strict", action="store_true",
                   help="Exit nonzero on any crash, illegal action, or timeout")
    args = p.parse_args()

    # Engine guard (fires first): self-play drives the engine's match runner,
    # which lives in the separate ext/fullhouse-engine checkout (gitignored,
    # absent in this public repo).
    if not ENGINE_RUNNER.is_file():
        print(
            f"self_play.py requires the engine clone at {ENGINE_DIR} (absent in "
            "this public repo). Self-play matches ran on the private engine "
            "harness and are not reproduced here.",
            file=sys.stderr,
        )
        return 4

    # Driving matches through the engine match driver is not implemented in this
    # public repo; it ran on the private engine harness.
    print(
        f"self-play vs {args.opponent} is not implemented in this public repo; "
        "matches ran on the private engine harness.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
