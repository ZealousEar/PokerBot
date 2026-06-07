"""Generate the Full House Hackathon banner SVG (docs/assets/fullhouse-banner.svg).

An LED dot-matrix rendering of "FULL HOUSE" in the project's phosphor-green /
dark palette, echoing the hackathon's terminal aesthetic, with a framed border
and the "Powered by Quadrature · 01.06.26 – 05.06.26" caption. Pure Python, no
deps — re-run to regenerate the committed asset.

    python tools/gen_fullhouse_banner.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "fullhouse-banner.svg"

# 5x7 dot-matrix glyphs (X = lit).
GLYPHS = {
    "F": ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "X...."],
    "U": ["X...X", "X...X", "X...X", "X...X", "X...X", "X...X", "XXXXX"],
    "L": ["X....", "X....", "X....", "X....", "X....", "X....", "XXXXX"],
    "H": ["X...X", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    "O": [".XXX.", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    "S": [".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."],
    "E": ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "XXXXX"],
}
WORDS = ["FULL", "HOUSE"]

# Geometry.
DOT = 9          # lit-dot size
PITCH = 12       # dot-to-dot spacing
GAP_LETTER = 1   # blank columns between letters in a word
GAP_WORD = 3     # blank columns between words
PAD_X = 46       # matrix inset from the frame, horizontally
PAD_TOP = 40
ROWS = 7

BG = "#080b0a"
GREEN = "#00ff6a"
GREEN_DIM = "#103a22"
FRAME = "#00cc55"
CAPTION = "#5cef86"
CAPTION_FAINT = "#3a9c5c"


def _matrix_columns():
    """Return list of column bit-strings (top->bottom) for the whole banner,
    plus the total column count."""
    cols = []  # each entry: list of 7 booleans
    for w, word in enumerate(WORDS):
        if w:
            for _ in range(GAP_WORD):
                cols.append([False] * ROWS)
        for li, ch in enumerate(word):
            g = GLYPHS[ch]
            for c in range(5):
                cols.append([g[r][c] == "X" for r in range(ROWS)])
            if li != len(word) - 1:
                for _ in range(GAP_LETTER):
                    cols.append([False] * ROWS)
    return cols


def build_svg() -> str:
    cols = _matrix_columns()
    n_cols = len(cols)
    matrix_w = n_cols * PITCH - (PITCH - DOT)
    matrix_h = ROWS * PITCH - (PITCH - DOT)
    width = matrix_w + 2 * PAD_X
    caption_y = PAD_TOP + matrix_h + 46
    height = caption_y + 34

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Full House Hackathon 2026 — Powered by Quadrature, 01.06.26 to 05.06.26">',
        "  <defs>",
        '    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">',
        '      <feGaussianBlur stdDeviation="1.6" result="b"/>',
        '      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>',
        "    </filter>",
        "  </defs>",
        f'  <rect x="0" y="0" width="{width}" height="{height}" rx="14" fill="{BG}"/>',
        # double frame
        f'  <rect x="6.5" y="6.5" width="{width - 13}" height="{height - 13}" rx="11" '
        f'fill="none" stroke="{FRAME}" stroke-opacity="0.9" stroke-width="2"/>',
        f'  <rect x="12.5" y="12.5" width="{width - 25}" height="{height - 25}" rx="8" '
        f'fill="none" stroke="{FRAME}" stroke-opacity="0.4" stroke-width="1"/>',
    ]

    # dim grid (off dots) then lit dots
    dim = ['  <g fill="' + GREEN_DIM + '" fill-opacity="0.5">']
    lit = [f'  <g fill="{GREEN}" filter="url(#glow)">']
    for ci, col in enumerate(cols):
        x = PAD_X + ci * PITCH
        for r in range(ROWS):
            y = PAD_TOP + r * PITCH
            cell = (f'    <rect x="{x}" y="{y}" width="{DOT}" height="{DOT}" rx="2.4"/>')
            (lit if col[r] else dim).append(cell)
    dim.append("  </g>")
    lit.append("  </g>")
    parts.extend(dim)
    parts.extend(lit)

    cx = width / 2
    parts.append(
        f'  <text x="{cx}" y="{caption_y}" text-anchor="middle" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="15" letter-spacing="1.5" fill="{CAPTION}">'
        f'Powered by Quadrature'
        f'<tspan fill="{CAPTION_FAINT}">  &#183;  </tspan>'
        f'01.06.26 &#8211; 05.06.26</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg())
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
