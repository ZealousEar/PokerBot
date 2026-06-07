"""Render the shipped preflop RFI (raise-first-in) ranges as 13x13 grids.

One panel per position, read straight from the `src.ranges` frozensets that the
bot actually uses — so the picture is the policy, not a redrawing of it. Grid
convention (standard hold'em chart): ranks A..2 on both axes, pairs on the
diagonal, suited hands above it, offsuit below.

Engine-free; needs only matplotlib + src.ranges.

Usage:
    python tools/plot_preflop_heatmap.py            # writes notebooks/figures/preflop_heatmap.png
    python tools/plot_preflop_heatmap.py -o out.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt  # noqa: E402
# NB: the backend is left untouched at import so this module is safe to import
# from a notebook (which uses the inline backend). The CLI entry point forces
# the headless Agg backend in main().

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ranges import OPEN_RANGES, POSITIONS  # noqa: E402

RANKS = "AKQJT98765432"  # descending, standard chart order
DEFAULT_OUT = ROOT / "notebooks" / "figures" / "preflop_heatmap.png"
IN_COLOR = "#1f6feb"
OUT_COLOR = "#e6edf3"


def hand_tag(i: int, j: int) -> str:
    """Canonical tag for grid cell (row i, col j) under the standard chart
    convention: diagonal = pairs, upper = suited, lower = offsuit."""
    hi, lo = RANKS[i], RANKS[j]
    if i == j:
        return hi + lo          # pair, e.g. "AA"
    if i < j:
        return hi + lo + "s"    # suited (row rank is higher)
    return lo + hi + "o"        # offsuit (col rank is higher)


def _membership_matrix(range_set):
    return [[1 if hand_tag(i, j) in range_set else 0 for j in range(13)] for i in range(13)]


def render(out_path: Path | None = DEFAULT_OUT):
    """Build the 6-position RFI figure. Saves to out_path if given; returns the
    matplotlib Figure either way (so a notebook can display it inline)."""
    cmap = matplotlib.colors.ListedColormap([OUT_COLOR, IN_COLOR])
    fig, axes = plt.subplots(2, 3, figsize=(13, 9))
    for ax, pos in zip(axes.flat, POSITIONS):
        range_set = OPEN_RANGES[pos]
        matrix = _membership_matrix(range_set)
        ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="equal")
        ax.set_xticks(range(13))
        ax.set_yticks(range(13))
        ax.set_xticks([x - 0.5 for x in range(14)], minor=True)
        ax.set_yticks([y - 0.5 for y in range(14)], minor=True)
        ax.set_xticklabels(list(RANKS), fontsize=8)
        ax.set_yticklabels(list(RANKS), fontsize=8)
        ax.tick_params(length=0)
        ax.grid(which="minor", color="white", linewidth=1)
        n_hands = len(range_set)
        subtitle = f"{n_hands} hand classes" if n_hands else "no RFI (BB defends)"
        ax.set_title(f"{pos} — {subtitle}", fontsize=11)
    fig.suptitle(
        "Shipped preflop RFI ranges by position (pairs ↘, suited ◤, offsuit ◢)",
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=150)
    return fig


def main() -> int:
    matplotlib.use("Agg")  # headless CLI rendering
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("-o", "--out", default=str(DEFAULT_OUT), help="output PNG path")
    args = p.parse_args()
    render(Path(args.out))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
