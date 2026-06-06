"""Monte Carlo equity vs range using eval7.

Budget: ≤ 5 ms per call at default trials. Pre-warm eval7 LUTs at module
import so the live 2 s decisions do not pay a cold-start cost.

# Source: [[Pluribus-Brown-Sandholm-2019]] — depth-limited heuristic in lieu of full solve
"""
import hashlib
import random
from typing import Iterable, Sequence

import eval7


def _stable_seed(*parts) -> int:
    """Deterministic seed across processes (Python's hash() is randomized
    per-process by PYTHONHASHSEED). Uses sha1 of repr."""
    payload = repr(parts).encode("utf-8")
    return int(hashlib.sha1(payload).hexdigest()[:8], 16)

# Pre-warm eval7 hand-rank LUT (covered by the 30 s warmup).
_WARM_DECK = [eval7.Card(r + s) for r in "23456789TJQKA" for s in "shdc"]
_ = eval7.evaluate(_WARM_DECK[:7])

RANKS = "23456789TJQKA"
SUITS = "shdc"
_RANK_VAL = {r: i for i, r in enumerate(RANKS)}


def parse_card(s: str) -> eval7.Card:
    return eval7.Card(s)


def canonical_hand(cards: Sequence[str]) -> str:
    """Return canonical hand tag like 'AA', 'AKs', 'T9o' from ['As','Kh']."""
    if len(cards) != 2:
        return ""
    r0, s0 = cards[0][0], cards[0][1]
    r1, s1 = cards[1][0], cards[1][1]
    if r0 == r1:
        return r0 + r1
    if _RANK_VAL[r0] < _RANK_VAL[r1]:
        r0, r1, s0, s1 = r1, r0, s1, s0
    return r0 + r1 + ("s" if s0 == s1 else "o")


def _canonical_nonpair(hi: str, lo: str, suffix: str = "") -> str:
    """Return high-rank-first canonical non-pair notation."""
    if hi not in _RANK_VAL or lo not in _RANK_VAL or hi == lo:
        return ""
    if _RANK_VAL[hi] < _RANK_VAL[lo]:
        hi, lo = lo, hi
    return hi + lo + suffix


def _nonpair_plus(hi: str, lo: str, suffixes: Sequence[str]) -> list:
    """Expand Ax+/Kx+ style ranges, excluding the primary rank itself.

    Examples:
    - AT+  -> ATs,ATo,AJs,AJo,AQs,AQo,AKs,AKo
    - A5s+ -> A5s,A6s,...,AKs
    """
    if hi not in _RANK_VAL or lo not in _RANK_VAL or hi == lo:
        return []
    if _RANK_VAL[hi] < _RANK_VAL[lo]:
        hi, lo = lo, hi
    out = []
    for j in range(_RANK_VAL[lo], _RANK_VAL[hi]):
        kicker = RANKS[j]
        if kicker == hi:
            continue
        for su in suffixes:
            out.append(hi + kicker + su)
    return out


def expand_range_tag(tag: str) -> list:
    """Expand poker range notation into canonical hand strings.

    Unsuffixed non-pair tags mean both suited and offsuit combos (`AK` ->
    `AKs`, `AKo`). Unsuffixed plus tags also expand both suited and offsuit
    kickers (`AT+` -> AT/AJ/AQ/AK, suited and offsuit). Public signature kept
    stable for postflop equity callers.
    """
    tag = (tag or "").strip()
    if not tag:
        return []

    if "+" in tag and "-" not in tag:
        base = tag[:-1]
        if len(base) == 2 and base[0] == base[1] and base[0] in _RANK_VAL:
            # Pair plus: 88+ -> 88,99,...,AA
            return [RANKS[j] + RANKS[j]
                    for j in range(_RANK_VAL[base[0]], len(RANKS))]
        if len(base) == 3 and base[2] in ("s", "o"):
            return _nonpair_plus(base[0], base[1], (base[2],))
        if len(base) == 2 and base[0] != base[1]:
            return _nonpair_plus(base[0], base[1], ("s", "o"))
        return []

    if "-" in tag:
        # Pair ranges like 88-22, and connector ladders like QJs-T9s.
        a, b = tag.split("-", 1)
        if (len(a) == 2 and len(b) == 2 and a[0] == a[1] and b[0] == b[1]
                and a[0] in _RANK_VAL and b[0] in _RANK_VAL):
            lo = min(_RANK_VAL[a[0]], _RANK_VAL[b[0]])
            hi = max(_RANK_VAL[a[0]], _RANK_VAL[b[0]])
            return [RANKS[j] + RANKS[j] for j in range(lo, hi + 1)]
        if len(a) in (2, 3) and len(b) == len(a):
            suffix = a[2:] if len(a) == 3 else ""
            if suffix == b[2:] and (not suffix or suffix in ("s", "o")):
                ahi, alo = a[0], a[1]
                bhi, blo = b[0], b[1]
                if all(r in _RANK_VAL for r in (ahi, alo, bhi, blo)):
                    step = 1 if _RANK_VAL[bhi] >= _RANK_VAL[ahi] else -1
                    span = abs(_RANK_VAL[bhi] - _RANK_VAL[ahi])
                    if abs(_RANK_VAL[blo] - _RANK_VAL[alo]) == span:
                        out = []
                        for n in range(span + 1):
                            hi = RANKS[_RANK_VAL[ahi] + step * n]
                            lo = RANKS[_RANK_VAL[alo] + step * n]
                            if suffix:
                                out.append(_canonical_nonpair(hi, lo, suffix))
                            else:
                                out.extend((_canonical_nonpair(hi, lo, "s"),
                                            _canonical_nonpair(hi, lo, "o")))
                        return [h for h in out if h]
        return []

    if len(tag) == 2 and tag[0] == tag[1] and tag[0] in _RANK_VAL:
        return [tag]
    if len(tag) == 2 and tag[0] != tag[1]:
        h = _canonical_nonpair(tag[0], tag[1])
        return [h + "s", h + "o"] if h else []
    if len(tag) == 3 and tag[2] in ("s", "o"):
        h = _canonical_nonpair(tag[0], tag[1], tag[2])
        return [h] if h else []
    return [tag]


def range_to_combos(range_tags: Iterable[str], dead_cards: Sequence[str] = ()) -> list:
    """Return list of (card1, card2) eval7.Card pairs for the given range,
    excluding any combos that use dead_cards."""
    dead = set()
    for c in dead_cards:
        if isinstance(c, str) and len(c) == 2:
            dead.add(c)
    combos = []
    seen = set()
    for tag in range_tags:
        for h in expand_range_tag(tag):
            if h in seen:
                continue
            seen.add(h)
            if len(h) == 2:  # pair
                r = h[0]
                cards = [r + s for s in SUITS]
                for i in range(4):
                    for j in range(i + 1, 4):
                        c1, c2 = cards[i], cards[j]
                        if c1 in dead or c2 in dead:
                            continue
                        combos.append((eval7.Card(c1), eval7.Card(c2)))
            elif len(h) == 3:
                hi, lo, su = h[0], h[1], h[2]
                if su == "s":
                    for s in SUITS:
                        c1, c2 = hi + s, lo + s
                        if c1 in dead or c2 in dead:
                            continue
                        combos.append((eval7.Card(c1), eval7.Card(c2)))
                elif su == "o":
                    for s1 in SUITS:
                        for s2 in SUITS:
                            if s1 == s2:
                                continue
                            c1, c2 = hi + s1, lo + s2
                            if c1 in dead or c2 in dead:
                                continue
                            combos.append((eval7.Card(c1), eval7.Card(c2)))
    return combos


def equity_vs_range(hero_cards: Sequence[str],
                    board: Sequence[str],
                    villain_range: Iterable[str],
                    trials: int = 300,
                    rng: random.Random = None) -> float:
    """Hero equity vs a random combo drawn from villain_range, over `trials`
    Monte Carlo rollouts. Returns float in [0, 1]. Tunable trials lets postflop
    callers stay within budget."""
    if rng is None:
        # Seed deterministically from (hand, board) so identical inputs give
        # identical equity — required for reproducible benchmarks.
        rng = random.Random(_stable_seed("eq_vs_range", tuple(hero_cards),
                                          tuple(board), trials))
    hero = [eval7.Card(c) for c in hero_cards]
    board_cards = [eval7.Card(c) for c in board]
    dead = list(hero_cards) + list(board)
    combos = range_to_combos(villain_range, dead)
    if not combos:
        return 0.5
    deck = [eval7.Card(r + s) for r in RANKS for s in SUITS
            if (r + s) not in dead]
    needed = 5 - len(board_cards)
    wins = 0.0
    n = 0
    for _ in range(trials):
        vc1, vc2 = rng.choice(combos)
        if str(vc1) in dead or str(vc2) in dead:
            continue
        local_deck = [c for c in deck if c != vc1 and c != vc2]
        rng.shuffle(local_deck)
        runout = local_deck[:needed]
        full_board = board_cards + runout
        hero_score = eval7.evaluate(hero + full_board)
        vill_score = eval7.evaluate([vc1, vc2] + full_board)
        if hero_score > vill_score:
            wins += 1.0
        elif hero_score == vill_score:
            wins += 0.5
        n += 1
    return wins / n if n else 0.5


def hand_strength(hero_cards: Sequence[str], board: Sequence[str], trials: int = 200) -> float:
    """Equity vs a uniformly-random 2-card villain holding. Cheap baseline
    metric for postflop decisions when no read is available."""
    rng = random.Random(_stable_seed("hand_strength", tuple(hero_cards),
                                      tuple(board), trials))
    hero = [eval7.Card(c) for c in hero_cards]
    board_cards = [eval7.Card(c) for c in board]
    dead = list(hero_cards) + list(board)
    deck = [eval7.Card(r + s) for r in RANKS for s in SUITS
            if (r + s) not in dead]
    needed = 5 - len(board_cards)
    wins = 0.0
    n = 0
    for _ in range(trials):
        rng.shuffle(deck)
        vc1, vc2 = deck[0], deck[1]
        runout = deck[2:2 + needed]
        full_board = board_cards + runout
        hero_score = eval7.evaluate(hero + full_board)
        vill_score = eval7.evaluate([vc1, vc2] + full_board)
        if hero_score > vill_score:
            wins += 1.0
        elif hero_score == vill_score:
            wins += 0.5
        n += 1
    return wins / n if n else 0.5
