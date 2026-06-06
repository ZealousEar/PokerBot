"""Standard preflop ranges by position and effective stack depth.

Format: `RANGES[position][stack_depth_bb] -> frozenset[str]` of canonical
hand strings (e.g. `"AKs"`, `"99"`, `"T9o"`).
"""
# Source: [[Pluribus-Brown-Sandholm-2019]]

RANKS = "23456789TJQKA"
RANK_VALUE = {rank: i for i, rank in enumerate(RANKS, start=2)}


def canonical_hand(cards) -> str:
    """Return canonical two-card notation such as AA, AKs, or T9o."""
    if not cards or len(cards) < 2:
        return ""
    c1, c2 = str(cards[0]), str(cards[1])
    r1, r2 = c1[0], c2[0]
    if r1 not in RANK_VALUE or r2 not in RANK_VALUE:
        return ""
    if RANK_VALUE[r2] > RANK_VALUE[r1]:
        c1, c2 = c2, c1
        r1, r2 = c1[0], c2[0]
    if r1 == r2:
        return r1 + r2
    return r1 + r2 + ("s" if c1[1:2] == c2[1:2] else "o")


def hand_score(hand: str) -> int:
    """Compact strength score for deterministic range decisions."""
    if not hand:
        return 0
    r1, r2 = hand[0], hand[1]
    high = RANK_VALUE.get(r1, 0)
    low = RANK_VALUE.get(r2, 0)
    if high == 0 or low == 0:
        return 0
    if r1 == r2:
        return 48 + high * 4
    score = high * 4 + low * 2
    gap = max(0, high - low - 1)
    score -= gap * 3
    if hand.endswith("s"):
        score += 5
    if high >= 14:
        score += 7
    if high >= 13 and low >= 10:
        score += 5
    if low >= 10:
        score += 4
    return score


PREMIUM = frozenset({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs"})
STRONG_CONTINUE = frozenset(
    {
        "AA", "KK", "QQ", "JJ", "TT", "99",
        "AKs", "AKo", "AQs", "AQo", "AJs", "KQs",
    }
)

OPEN_HEADS_UP = frozenset(
    hand
    for r1 in reversed(RANKS)
    for r2 in reversed(RANKS)
    for hand in (
        [r1 + r2] if r1 == r2
        else [r1 + r2 + "s", r1 + r2 + "o"] if RANK_VALUE[r1] > RANK_VALUE[r2]
        else []
    )
)

RANGES: dict = {
    "heads_up_button": {100: OPEN_HEADS_UP},
    "big_blind_defend": {100: STRONG_CONTINUE},
    "premium": {100: PREMIUM},
}
