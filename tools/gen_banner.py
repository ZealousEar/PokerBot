"""Generate the combined README banner (docs/assets/banner.svg).

One bordered panel containing both the PokerBot header and the Full House
Hackathon LED dot-matrix, in the project's phosphor-green / dark palette. Pure
Python, no deps — re-run to regenerate the committed asset.

    python tools/gen_banner.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "banner.svg"

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

DOT, PITCH, ROWS = 9, 12, 7
GAP_LETTER, GAP_WORD = 1, 3

W = 820
BG = "#0d1117"
PANEL = "#080b0a"
GREEN = "#00ff6a"
GREEN_DIM = "#103a22"
DIVIDER = "#00cc55"
TITLE = "#e6edf3"
SUBTLE = "#adbac7"
FAINT = "#768390"
CAPTION = "#5cef86"
CAPTION_FAINT = "#3a9c5c"
SANS = ("'Neue Haas Grotesk Display Pro', 'Neue Haas Grotesk Display', "
        "'Helvetica Neue', Helvetica, Arial, sans-serif")
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def _matrix_columns():
    cols = []
    for w, word in enumerate(WORDS):
        if w:
            cols += [[False] * ROWS] * GAP_WORD
        for li, ch in enumerate(word):
            g = GLYPHS[ch]
            for c in range(5):
                cols.append([g[r][c] == "X" for r in range(ROWS)])
            if li != len(word) - 1:
                cols += [[False] * ROWS] * GAP_LETTER
    return cols


def build_svg() -> str:
    cols = _matrix_columns()
    matrix_w = len(cols) * PITCH - (PITCH - DOT)
    matrix_h = ROWS * PITCH - (PITCH - DOT)

    # vertical layout
    divider_y = 196
    panel_top = divider_y + 20
    panel_h = matrix_h + 96
    matrix_x = (W - matrix_w) / 2
    matrix_y = panel_top + 30
    caption_y = panel_top + panel_h - 22
    height = panel_top + panel_h + 22

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" '
        f'aria-label="PokerBot — Full House Hackathon 2026 finalist entry, Powered by Quadrature">',
        "  <defs>",
        '    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">',
        f'      <stop offset="0" stop-color="{GREEN}"/>',
        f'      <stop offset="1" stop-color="{DIVIDER}"/>',
        "    </linearGradient>",
        '    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">',
        '      <feGaussianBlur stdDeviation="1.5" result="b"/>',
        '      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>',
        "    </filter>",
        "  </defs>",
        # single outer border
        f'  <rect x="1.5" y="1.5" width="{W - 3}" height="{height - 3}" rx="18" '
        f'fill="{BG}" stroke="url(#edge)" stroke-width="2"/>',
        # --- PokerBot header ---
        f'  <g fill="{GREEN}" transform="translate(648,46)">',
        '    <path d="M16 0 L30 14 L16 28 L2 14 Z"/>',
        '    <path d="M70 28 a8 8 0 1 1 12 -10 a8 8 0 1 1 12 10 l-12 12 z" fill="#b3001b"/>',
        "  </g>",
        f'  <text x="56" y="82" font-family="{SANS}" font-size="48" font-weight="700" '
        f'fill="{TITLE}" letter-spacing="0.5">PokerBot</text>',
        f'  <text x="58" y="118" font-family="{SANS}" font-size="18" fill="{SUBTLE}">'
        f'Qualified for the finals of the UK&#8217;s first quantitative poker hackathon</text>',
        f'  <text x="58" y="146" font-family="{SANS}" font-size="13" fill="{FAINT}">'
        f'6-max NLHE &#183; near-Nash blueprint + bounded exploit overlay</text>',
        # divider
        f'  <line x1="40" y1="{divider_y}" x2="{W - 40}" y2="{divider_y}" '
        f'stroke="{DIVIDER}" stroke-opacity="0.28" stroke-width="1"/>',
        # --- LED panel ---
        f'  <rect x="36" y="{panel_top}" width="{W - 72}" height="{panel_h}" rx="10" '
        f'fill="{PANEL}" stroke="{DIVIDER}" stroke-opacity="0.5" stroke-width="1.5"/>',
    ]

    dim = [f'  <g fill="{GREEN_DIM}" fill-opacity="0.5">']
    lit = [f'  <g fill="{GREEN}" filter="url(#glow)">']
    for ci, col in enumerate(cols):
        x = matrix_x + ci * PITCH
        for r in range(ROWS):
            y = matrix_y + r * PITCH
            cell = f'    <rect x="{x:.1f}" y="{y:.1f}" width="{DOT}" height="{DOT}" rx="2.4"/>'
            (lit if col[r] else dim).append(cell)
    dim.append("  </g>")
    lit.append("  </g>")
    p += dim + lit

    p.append(
        f'  <text x="{W / 2}" y="{caption_y}" text-anchor="middle" font-family="{MONO}" '
        f'font-size="15" letter-spacing="1.5" fill="{CAPTION}">Powered by Quadrature'
        f'<tspan fill="{CAPTION_FAINT}">  &#183;  </tspan>01.06.26 &#8211; 05.06.26</text>'
    )
    p.append("</svg>")
    return "\n".join(p) + "\n"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg())
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
