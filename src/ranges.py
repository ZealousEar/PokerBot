"""Standard 6-max NLHE preflop ranges by position and action context.

Tags use canonical strings: 'AA', 'AKs', 'AKo'. Positions: UTG, MP, CO, BTN, SB, BB
for 6-max; in heads-up matches both seats use SB/BB rules. The engine deals
SB first to the dealer in HU and second-after-dealer otherwise.

Charted-quality opens; derived from public 6-max NLHE solver charts (Upswing /
GTO Wizard 100 BB charts, lightly widened for hackathon-style passive fields).

# Source: [[Pluribus-Brown-Sandholm-2019]] (open-size tree)
#         + [[Engine-Fullhouse]] (reference-bot exploit holes — most field is
#         passive, so we open wider than pure GTO)
# Status: SHIPPED — these tables bound the running action categories; a compact
#         trained lookup mixes permitted sizes without widening these ranges.
"""
from typing import FrozenSet

# Position labels by clockwise offset from the button.  The engine rebuilds a
# compact seat list after eliminations, so positions must be derived from the
# two blind posts on every hand rather than from an original seat number.
# Heads-up is the exception: the button is also the small blind.
POSITIONS_BY_TABLE_SIZE = {
    2: ("SB", "BB"),
    3: ("BTN", "SB", "BB"),
    4: ("BTN", "SB", "BB", "CO"),
    5: ("BTN", "SB", "BB", "MP", "CO"),
    6: ("BTN", "SB", "BB", "UTG", "MP", "CO"),
    7: ("BTN", "SB", "BB", "UTG", "MP", "MP", "CO"),
    8: ("BTN", "SB", "BB", "UTG", "UTG", "MP", "MP", "CO"),
    9: ("BTN", "SB", "BB", "UTG", "UTG", "UTG", "MP", "MP", "CO"),
}

POSITIONS = ("UTG", "MP", "CO", "BTN", "SB", "BB")
EARLY_POSITIONS = frozenset({"UTG", "MP"})
LATE_POSITIONS = frozenset({"CO", "BTN", "SB"})


def _expand(tags):
    """Internal helper — flatten range shorthand into explicit hand-tag set."""
    out = set()
    for t in tags:
        out.add(t)
    return frozenset(out)


# --- Open-raise (RFI) ranges ------------------------------------------------
# Conservative ranges; widen vs the passive bots in G3 via the overlay.

OPEN_UTG: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
    "AKs", "AQs", "AJs", "ATs",
    "AKo", "AQo", "AJo",
    "KQs", "KJs", "KTs",
    "QJs", "QTs",
    "JTs",
    "T9s", "98s",
])

OPEN_MP: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s",
    "AKo", "AQo", "AJo", "ATo",
    "KQs", "KJs", "KTs", "K9s",
    "KQo", "KJo",
    "QJs", "QTs", "Q9s",
    "QJo",
    "JTs", "J9s",
    "T9s", "T8s",
    "98s", "87s", "76s",
])

OPEN_CO: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "AKo", "AQo", "AJo", "ATo", "A9o",
    "KQs", "KJs", "KTs", "K9s", "K8s", "K7s",
    "KQo", "KJo", "KTo",
    "QJs", "QTs", "Q9s", "Q8s",
    "QJo", "QTo",
    "JTs", "J9s", "J8s",
    "JTo",
    "T9s", "T8s", "T7s",
    "98s", "97s",
    "87s", "86s",
    "76s", "75s",
    "65s", "54s",
])

OPEN_BTN: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o",
    "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
    "KQo", "KJo", "KTo", "K9o",
    "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s",
    "QJo", "QTo", "Q9o",
    "JTs", "J9s", "J8s", "J7s",
    "JTo", "J9o",
    "T9s", "T8s", "T7s", "T6s",
    "T9o", "T8o",
    "98s", "97s", "96s",
    "98o",
    "87s", "86s", "85s",
    "87o",
    "76s", "75s", "74s",
    "65s", "64s",
    "54s", "53s",
    "43s",
])

# SB open is "raise-or-fold" vs BB only (heads-up vs BB after others fold).
OPEN_SB: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o",
    "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s",
    "KQo", "KJo", "KTo", "K9o",
    "QJs", "QTs", "Q9s", "Q8s", "Q7s",
    "QJo", "QTo", "Q9o",
    "JTs", "J9s", "J8s", "J7s",
    "JTo", "J9o",
    "T9s", "T8s", "T7s",
    "T9o",
    "98s", "97s",
    "87s", "86s",
    "76s", "75s",
    "65s",
    "54s",
])


OPEN_RANGES = {
    "UTG": OPEN_UTG,
    "MP": OPEN_MP,
    "CO": OPEN_CO,
    "BTN": OPEN_BTN,
    "SB": OPEN_SB,
    "BB": frozenset(),
}


# --- Borderline opens (overlay widens into these vs tight_passive) ----------
# These are the marginal "iso-and-add" hands that GTO is indifferent on.
# Profitable to open vs a tight-passive field that overfolds postflop.

BORDERLINE_OPEN_UTG = _expand([
    "66", "55", "44",
    "A9s", "A8s", "A7s", "A6s", "A5s",
    "K9s", "Q9s",
    "98s", "87s",
])

BORDERLINE_OPEN_MP = _expand([
    "44", "33", "22",
    "A4s", "A3s", "A2s",
    "K8s", "K7s",
    "Q8s",
    "J8s",
    "T7s", "97s",
    "65s",
])

BORDERLINE_OPEN_CO = _expand([
    "A8o", "A7o",
    "KJo",
    "K6s", "K5s", "K4s", "K3s", "K2s",
    "Q4s", "Q3s",
    "J7s",
    "T6s",
    "96s",
    "84s",
    "53s", "43s",
])

BORDERLINE_OPEN_BTN = _expand([
    "A4o", "A3o", "A2o",
    "K8o", "K7o", "K6o",
    "Q8o", "Q7o", "Q6o",
    "J8o", "J7o",
    "T7o", "T6o",
    "96s", "95s",
    "85s", "84s",
    "74s",
    "63s", "52s", "42s", "32s",
])

BORDERLINE_OPEN_SB = _expand([
    "A5o", "K8o", "Q8o",
    "J6s", "T6s",
    "96s", "85s", "74s", "53s", "43s",
])

BORDERLINE_OPEN = {
    "UTG": BORDERLINE_OPEN_UTG,
    "MP": BORDERLINE_OPEN_MP,
    "CO": BORDERLINE_OPEN_CO,
    "BTN": BORDERLINE_OPEN_BTN,
    "SB": BORDERLINE_OPEN_SB,
    "BB": frozenset(),
}


# --- Core open ranges (tight GTO baseline for blueprint-only build) --------
# Subset of OPEN_RANGES: keep premium + standard opens, drop the speculative
# bottom-of-range hands. Used when DISABLE_OVERLAY=1 so the v1_blueprint
# snapshot plays a meaningfully tighter baseline than the with-overlay v2+.
# This separation makes the G5 ablation actually measure overlay contribution
# instead of (overlay shifts) ⊕ (already-wide blueprint).

CORE_OPEN_UTG = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88",
    "AKs", "AQs", "AJs", "ATs",
    "AKo", "AQo",
    "KQs",
])

CORE_OPEN_MP = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
    "AKs", "AQs", "AJs", "ATs", "A9s",
    "AKo", "AQo", "AJo",
    "KQs", "KJs",
])

CORE_OPEN_CO = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A5s",
    "AKo", "AQo", "AJo", "ATo",
    "KQs", "KJs", "KTs",
    "QJs", "QTs",
    "JTs",
])

CORE_OPEN_BTN = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A5s",
    "AKo", "AQo", "AJo", "ATo", "A9o",
    "KQs", "KJs", "KTs", "K9s",
    "KQo", "KJo",
    "QJs", "QTs", "Q9s",
    "JTs", "J9s",
    "T9s", "98s",
])

CORE_OPEN_SB = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A5s",
    "AKo", "AQo", "AJo",
    "KQs", "KJs", "KTs",
    "QJs", "QTs",
    "JTs",
])

CORE_OPEN_RANGES = {
    "UTG": CORE_OPEN_UTG,
    "MP": CORE_OPEN_MP,
    "CO": CORE_OPEN_CO,
    "BTN": CORE_OPEN_BTN,
    "SB": CORE_OPEN_SB,
    "BB": frozenset(),
}


# --- 3-bet ranges (vs single raise) ----------------------------------------
# Linear + polarised mix; tighter from earlier defenders.

THREEBET_VS_OPEN: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT",
    "AKs", "AQs", "AKo",
    "AJs", "ATs",
    "KQs",
    # polar bluffs
    "A5s", "A4s", "A3s", "A2s",
    "K5s", "K4s",
    "76s", "65s", "54s",
])

THREEBET_BTN_VS_OPEN: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99",
    "AKs", "AQs", "AJs", "ATs", "AKo", "AQo",
    "KQs", "KJs",
    "QJs",
    # bluffs
    "A5s", "A4s", "A3s", "A2s",
    "K5s", "K4s", "K3s",
    "Q5s", "Q4s",
    "76s", "65s", "54s",
])

THREEBET_SB_VS_OPEN: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT",
    "AKs", "AQs", "AJs", "AKo", "AQo",
    "KQs",
    # bluffs
    "A5s", "A4s", "A3s", "A2s",
    "76s", "65s", "54s",
])

THREEBET_BB_VS_OPEN: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99",
    "AKs", "AQs", "AJs", "ATs", "AKo", "AQo", "AJo",
    "KQs", "KJs",
    "QJs",
    # bluffs (BB defends widest, gets the best price)
    "A5s", "A4s", "A3s", "A2s",
    "K9s", "K8s",
    "76s", "65s", "54s",
])

# Cold-call / flat range when facing an open (in position only — out of position
# we 3-bet or fold to keep the pot small).
FLAT_VS_OPEN_BTN: FrozenSet[str] = _expand([
    "99", "88", "77", "66", "55", "44", "33", "22",
    "AJs", "ATs", "A9s", "A8s", "A7s", "A6s",
    "KJs", "KTs", "K9s",
    "QTs", "QJs", "Q9s",
    "JTs", "J9s",
    "T9s", "T8s",
    "98s", "87s", "76s", "65s",
    "AJo", "ATo",
    "KQo", "KJo",
    "QJo",
    "JTo",
])

FLAT_VS_OPEN_BB: FrozenSet[str] = _expand([
    "99", "88", "77", "66", "55", "44", "33", "22",
    "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "KJs", "KTs", "K9s", "K8s", "K7s",
    "QJs", "QTs", "Q9s", "Q8s",
    "JTs", "J9s", "J8s",
    "T9s", "T8s",
    "98s", "97s",
    "87s", "86s", "76s", "65s", "54s",
    "AQo", "AJo", "ATo", "A9o",
    "KQo", "KJo", "KTo",
    "QJo", "QTo",
    "JTo",
])


# --- 4-bet range (vs 3-bet) -------------------------------------------------
# Premium value + small bluff frequency.

FOURBET_VS_THREEBET: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "AKs", "AKo",
    "A5s", "A4s",  # value-merged bluffs
])

CALL_VS_THREEBET: FrozenSet[str] = _expand([
    "JJ", "TT", "99",
    "AQs", "AJs", "ATs", "AQo",
    "KQs",
])


# --- Price- and stack-aware continuation ranges ---------------------------
# These are deliberately conservative tournament ranges.  They prevent the
# normal 100 BB flatting charts from being reused against oversized raises or
# shoves, while retaining explicit short-stack push/fold and reshove paths.

THREEBET_VS_EARLY_OPEN: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ",
    "AKs", "AQs", "AKo",
])

SQUEEZE_VALUE: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT",
    "AKs", "AQs", "AKo",
])

FLAT_VS_EARLY_OPEN: FrozenSet[str] = _expand([
    "TT", "99", "88", "77",
    "AQs", "AJs", "ATs", "AQo",
    "KQs", "QJs", "JTs",
])

MULTIWAY_FLAT: FrozenSet[str] = _expand([
    "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AQs", "AJs", "ATs", "KQs", "KJs", "QJs", "JTs",
    "T9s", "98s", "87s", "76s", "65s",
])

FOURBET_VALUE: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "AKs", "AKo",
])

COLD_FOURBET: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "AKs", "AKo",
])

LARGE_RAISE_CONTINUE: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs",
])

PUSH_FOLD_TIGHT: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
    "AKs", "AQs", "AJs", "ATs", "AKo", "AQo", "AJo",
    "KQs",
])

PUSH_FOLD_STANDARD: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "AKo", "AQo", "AJo", "ATo",
    "KQs", "KJs", "KTs", "KQo",
    "QJs", "QTs", "JTs", "T9s",
])

PUSH_FOLD_WIDE: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "AKo", "AQo", "AJo", "ATo", "A9o", "A8o",
    "KQs", "KJs", "KTs", "K9s", "K8s", "KQo", "KJo", "KTo",
    "QJs", "QTs", "Q9s", "QJo",
    "JTs", "J9s", "JTo",
    "T9s", "T8s", "98s", "87s", "76s", "65s",
])

RESHOVE_10BB: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
    "AKs", "AQs", "AJs", "ATs", "A9s", "AKo", "AQo", "AJo", "ATo",
    "KQs",
])

RESHOVE_15BB: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
    "AKs", "AQs", "AJs", "AKo", "AQo",
    "KQs",
])

RESHOVE_20BB: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99",
    "AKs", "AQs", "AKo",
])

CALL_OFF_5BB: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "AKo", "AQo", "AJo", "ATo", "A9o", "A8o",
    "KQs", "KJs", "KTs", "KQo", "KJo",
    "QJs", "QTs", "QJo", "JTs",
])

CALL_OFF_10BB: FrozenSet[str] = RESHOVE_10BB

CALL_OFF_15BB: FrozenSet[str] = RESHOVE_15BB

CALL_OFF_20BB: FrozenSet[str] = RESHOVE_20BB

CALL_OFF_30BB: FrozenSet[str] = _expand([
    "AA", "KK", "QQ", "JJ", "AKs", "AKo",
])

CALL_OFF_DEEP: FrozenSet[str] = _expand([
    "AA", "KK",
])


def hand_in(tag: str, range_set: FrozenSet[str]) -> bool:
    return tag in range_set
