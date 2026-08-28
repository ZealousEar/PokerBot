"""Board and made-hand classifiers for postflop commitment logic.

The board texture helpers preserve the lightweight string-card semantics from
`src.postflop.board_texture` / `_flush_suit` / `_board_paired` /
`_has_nut_flush`, while the made-hand category helpers give downstream gates a
single place to ask whether a hand has a nut flush or boat-or-better.
"""
from typing import Optional, Sequence

RANKS = "23456789TJQKA"
SUITS = "shdc"
_RANK_VAL = {r: i for i, r in enumerate(RANKS)}
_DESC_RANKS = "AKQJT98765432"


def _card_str(card) -> str:
    if isinstance(card, str):
        s = card
    else:
        s = str(card)
    if len(s) >= 2 and s[0] in _RANK_VAL and s[1] in SUITS:
        return s[:2]
    return ""


def _cards(cards: Sequence[str]) -> list:
    return [s for s in (_card_str(c) for c in (cards or ())) if s]


def _rank_counts(cards: Sequence[str]) -> dict:
    counts = {}
    for c in _cards(cards):
        counts[c[0]] = counts.get(c[0], 0) + 1
    return counts


def _suit_counts(cards: Sequence[str]) -> dict:
    counts = {}
    for c in _cards(cards):
        counts[c[1]] = counts.get(c[1], 0) + 1
    return counts


def _flush_draw(board: Sequence[str]) -> bool:
    counts = _suit_counts(board)
    return bool(counts) and max(counts.values()) >= 2


def paired(board: Sequence[str]) -> bool:
    """True when the board contains duplicate ranks."""
    ranks = [c[0] for c in _cards(board)]
    return len(set(ranks)) < len(ranks)


def flush_suit(board: Sequence[str]) -> Optional[str]:
    """Suit with 3+ board cards, if a board-enabled flush is possible."""
    counts = _suit_counts(board)
    for suit in SUITS:
        if counts.get(suit, 0) >= 3:
            return suit
    return None


def monotone(board: Sequence[str]) -> bool:
    """True when all board cards are the same suit (for 3+ card boards)."""
    cards = _cards(board)
    if len(cards) < 3:
        return False
    suits = {c[1] for c in cards}
    return len(suits) == 1


def two_tone(board: Sequence[str]) -> bool:
    """True for a two-card suit concentration before a board flush exists."""
    counts = _suit_counts(board)
    if not counts or flush_suit(board) is not None or monotone(board):
        return False
    return max(counts.values()) >= 2


def straighty(board: Sequence[str]) -> bool:
    """Cheap straight texture heuristic preserved from postflop.board_texture.

    Uses the same high-ace span check as the legacy helper; it intentionally
    does not add an A-low wheel special case.
    """
    rvals = sorted(_RANK_VAL[c[0]] for c in _cards(board))
    if not rvals:
        return False
    return (max(rvals) - min(rvals)) <= 4 and len(set(rvals)) >= 2


def high_card(board: Sequence[str]) -> bool:
    return any(c[0] in "AKQ" for c in _cards(board))


def wet(board: Sequence[str]) -> bool:
    """Legacy wet-board heuristic: flush draw/concentration or straight-y."""
    return _flush_draw(board) or straighty(board)


def board_features(board: Sequence[str]) -> dict:
    """Return board texture features consumed by commitment/postflop gates."""
    fs = flush_suit(board)
    st = straighty(board)
    fd = _flush_draw(board)
    return {
        "paired": paired(board),
        "flush_suit": fs,
        "monotone": monotone(board),
        "two_tone": two_tone(board),
        "straighty": st,
        "wet": fd or st,
        "high_card": high_card(board),
        # Backward-compatible names from src.postflop.board_texture.
        "flush_draw": fd,
        "straight_y": st,
    }


classify_board = board_features


def _combined(hole: Sequence[str], board: Sequence[str]) -> list:
    return _cards(hole) + _cards(board)


def _has_straight(cards: Sequence[str]) -> bool:
    vals = {_RANK_VAL[c[0]] for c in _cards(cards)}
    if _RANK_VAL["A"] in vals:
        vals.add(-1)  # Wheel support for actual made-hand categories.
    if len(vals) < 5:
        return False
    ordered = sorted(vals)
    run = 1
    last = None
    for v in ordered:
        if last is not None and v == last + 1:
            run += 1
            if run >= 5:
                return True
        else:
            run = 1
        last = v
    return False


def straight_completion_ranks(hole: Sequence[str], board: Sequence[str]) -> tuple:
    """Ranks which make a straight on the next card.

    This is deliberately rank based: one entry means four physical outs, not
    one.  It is cheap enough to use while weighting every candidate holding in
    an opponent range and handles wheel draws through ``_has_straight``.
    """
    cards = _combined(hole, board)
    if len(_cards(board)) >= 5 or _has_straight(cards):
        return ()
    present = {c[0] for c in cards}
    return tuple(
        rank for rank in _DESC_RANKS
        if rank not in present and _has_straight(cards + [rank + "s"])
    )


def flush_draw_suit(hole: Sequence[str], board: Sequence[str]) -> Optional[str]:
    """Suit with exactly four combined cards and at least one card to come."""
    if len(_cards(board)) >= 5 or made_flush(hole, board):
        return None
    counts = _suit_counts(_combined(hole, board))
    for suit in SUITS:
        if counts.get(suit, 0) == 4:
            return suit
    return None


def draw_features(hole: Sequence[str], board: Sequence[str]) -> dict:
    """Return inexpensive made-draw features for range conditioning."""
    straight_out_ranks = straight_completion_ranks(hole, board)
    flush_suit_value = flush_draw_suit(hole, board)
    return {
        "flush_draw_suit": flush_suit_value,
        "has_flush_draw": flush_suit_value is not None,
        "straight_out_ranks": straight_out_ranks,
        "open_ended": len(straight_out_ranks) >= 2,
        "gutshot": len(straight_out_ranks) == 1,
        "combo_draw": flush_suit_value is not None and bool(straight_out_ranks),
    }


def made_flush(hole: Sequence[str], board: Sequence[str], suit: Optional[str] = None) -> bool:
    """True if the 7-card hand contains a five-card flush."""
    cards = _combined(hole, board)
    if suit is not None:
        return sum(1 for c in cards if c[1] == suit) >= 5
    counts = _suit_counts(cards)
    return bool(counts) and max(counts.values()) >= 5


def nut_flush(hole: Sequence[str], board: Sequence[str], suit: Optional[str] = None) -> bool:
    """Current postflop nut-flush semantics: hold highest off-board suited card."""
    fs = flush_suit(board) if suit is None else suit
    if fs is None:
        return False
    board_suit = [c[0] for c in _cards(board) if c[1] == fs]
    my_suit = [c[0] for c in _cards(hole) if c[1] == fs]
    if len(board_suit) + len(my_suit) < 5:
        return False
    on_board = set(board_suit)
    for rank in _DESC_RANKS:
        if rank in on_board:
            continue
        return rank in my_suit
    return False


def category(hole: Sequence[str], board: Sequence[str]) -> str:
    """Best made-hand category for the combined hole + board cards."""
    cards = _combined(hole, board)
    if not cards:
        return "unknown"

    for suit in SUITS:
        suited = [c for c in cards if c[1] == suit]
        if len(suited) >= 5 and _has_straight(suited):
            return "straight_flush"

    counts = _rank_counts(cards)
    count_values = list(counts.values())
    if count_values and max(count_values) >= 4:
        return "four_kind"

    trips = [r for r, n in counts.items() if n >= 3]
    pairs = [r for r, n in counts.items() if n >= 2]
    if trips and len(pairs) >= 2:
        return "full_house"

    if made_flush((), cards):
        return "flush"
    if _has_straight(cards):
        return "straight"
    if trips:
        return "trips"
    if len(pairs) >= 2:
        return "two_pair"
    if pairs:
        return "pair"
    return "high_card"


def full_house_or_better(hole: Sequence[str], board: Sequence[str]) -> bool:
    return category(hole, board) in {"full_house", "four_kind", "straight_flush"}


def full_house_dominated(hole: Sequence[str], board: Sequence[str]) -> bool:
    """True when our full house is beaten by a higher board-enabled full house.

    On a double-paired board (e.g. Kd Ks Qs Qd 5c) a second-best boat such as
    QQQ-KK is drawing dead to any King (KKK-QQ), so it must NOT be treated as an
    automatic stack-off. Quads / straight flushes (handled by the caller) and
    non-full-house hands are never reported as dominated here.
    """
    if category(hole, board) != "full_house":
        return False
    # On a trip board (KKKQ2), a pocket-pair full house is behind any opponent
    # holding the fourth board rank. If hero held that card our best category
    # would already be quads, so every remaining full house is potentially
    # dominated and must go through range equity rather than auto-stack-off.
    if any(n == 3 for n in _rank_counts(board).values()):
        return True
    combined = _combined(hole, board)
    trips = [_RANK_VAL[r] for r, n in _rank_counts(combined).items() if n >= 3]
    if not trips:
        return False
    our_trips = max(trips)
    board_pairs = [_RANK_VAL[r] for r, n in _rank_counts(board).items() if n >= 2]
    # A board pair ranked above our trips lets a villain hold one card of that
    # rank for a strictly higher full house.
    return any(bp > our_trips for bp in board_pairs)


def hand_features(hole: Sequence[str], board: Sequence[str]) -> dict:
    """Return combined board + made-hand features for downstream gates."""
    features = board_features(board)
    cat = category(hole, board)
    features.update({
        "made_flush": made_flush(hole, board),
        "nut_flush": nut_flush(hole, board, features["flush_suit"]),
        "full_house_or_better": cat in {"full_house", "four_kind", "straight_flush"},
        "category": cat,
    })
    features.update(draw_features(hole, board))
    return features


classify_hand = hand_features
