"""Monte Carlo equity vs range using eval7.

Budget: ≤ 5 ms per call at default trials. Pre-warm eval7 LUTs at module
import so the live 2 s decisions do not pay a cold-start cost.

# Source: [[Pluribus-Brown-Sandholm-2019]] — depth-limited heuristic in lieu of full solve
"""
import hashlib
import random
from typing import Iterable, Sequence

import eval7


def _stable_hash(*parts) -> int:
    """Deterministic RNG key, stable across processes (Python's hash() is
    randomized per-process by the interpreter's hash-randomization env var).
    Uses sha1 of repr."""
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


def expand_range_tag(tag: str) -> list:
    """Expand a range tag ('AKs', 'TT', '88+', 'A5s+', 'QJs-T9s', 'AK')
    into a list of canonical hand strings. Best-effort."""
    out = []
    if "+" in tag and "-" not in tag:
        base = tag[:-1]
        if len(base) == 2 and base[0] == base[1]:
            # Pair plus: 88+ -> 88,99,...,AA
            i = _RANK_VAL[base[0]]
            for j in range(i, len(RANKS)):
                out.append(RANKS[j] + RANKS[j])
        elif len(base) == 3:
            # Like A5s+ -> A5s,A6s,...,AKs (gap closes toward higher)
            hi, lo, su = base[0], base[1], base[2]
            for j in range(_RANK_VAL[lo], _RANK_VAL[hi]):
                out.append(hi + RANKS[j] + su)
        elif len(base) == 2:
            # Like AK -> AKs, AKo
            out.append(base + "s")
            out.append(base + "o")
        return out
    if "-" in tag:
        # Like 88-22 or QJs-T9s. Best-effort.
        a, b = tag.split("-")
        if len(a) == 2 and a[0] == a[1] and len(b) == 2 and b[0] == b[1]:
            lo = min(_RANK_VAL[a[0]], _RANK_VAL[b[0]])
            hi = max(_RANK_VAL[a[0]], _RANK_VAL[b[0]])
            for j in range(lo, hi + 1):
                out.append(RANKS[j] + RANKS[j])
        return out
    if len(tag) == 2 and tag[0] != tag[1]:
        out.append(tag + "s")
        out.append(tag + "o")
        return out
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
                else:  # offsuit
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
        # Derive the RNG key deterministically from (hand, board) so identical
        # inputs give identical equity — required for reproducible benchmarks.
        rng = random.Random(_stable_hash("eq_vs_range", tuple(hero_cards),
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
    rng = random.Random(_stable_hash("hand_strength", tuple(hero_cards),
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
