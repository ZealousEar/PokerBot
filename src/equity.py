"""Collision-free heads-up and multiway equity using eval7.

Complete tractable rivers are enumerated exactly; other streets use
deterministic adaptive Monte Carlo against per-opponent weighted ranges.
Trial caps account for opponent count and remain comfortably inside the live
2-second decision budget. eval7 LUTs are pre-warmed at module import.

# Source: [[Pluribus-Brown-Sandholm-2019]] — depth-limited heuristic in lieu of full solve
# Status: SHIPPED — joint range equity is the running depth-limited heuristic.
"""
import hashlib
import math
import random
import time
from numbers import Real
from typing import Iterable, Mapping, Sequence

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
ALL_STARTING_HANDS = tuple(
    [rank + rank for rank in RANKS]
    + [
        hi + lo + suitedness
        for hi_index, hi in enumerate(RANKS)
        for lo in RANKS[:hi_index]
        for suitedness in ("s", "o")
    ]
)


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


def _card_text(card) -> str:
    value = card if isinstance(card, str) else str(card)
    return value if len(value) == 2 and value[0] in RANKS and value[1] in SUITS else ""


def _explicit_combo(value):
    """Normalize a concrete two-card combo, or return ``None``."""
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        return None
    c1, c2 = _card_text(value[0]), _card_text(value[1])
    if not c1 or not c2 or c1 == c2:
        return None
    return eval7.Card(c1), eval7.Card(c2)


def range_to_weighted_combos(range_spec, dead_cards: Sequence[str] = ()) -> list:
    """Expand a range into ``[((card1, card2), weight), ...]``.

    Accepted forms are intentionally liberal so existing unweighted callers
    keep working:

    * iterable of range tags (``["88+", "AT+"]``);
    * mapping or pairs of ``range_tag -> weight``;
    * concrete card pairs, weighted or unweighted.

    Overlapping tags use the maximum supplied weight instead of double
    counting the same physical holding.
    """
    dead = {_card_text(card) for card in (dead_cards or ())}
    dead.discard("")
    if isinstance(range_spec, Mapping):
        items = list(range_spec.items())
    elif isinstance(range_spec, str):
        items = [range_spec]
    else:
        try:
            items = list(range_spec or ())
        except TypeError:
            items = []

    weighted = {}

    def add(combo, weight):
        try:
            numeric_weight = float(weight)
        except (TypeError, ValueError, OverflowError):
            return
        if not math.isfinite(numeric_weight) or numeric_weight <= 0.0:
            return
        normalized = _explicit_combo(combo)
        if normalized is None:
            return
        c1, c2 = normalized
        s1, s2 = str(c1), str(c2)
        if s1 in dead or s2 in dead:
            return
        key = tuple(sorted((s1, s2)))
        previous = weighted.get(key)
        if previous is None or numeric_weight > previous[1]:
            weighted[key] = ((c1, c2), numeric_weight)

    for item in items:
        weight = 1.0
        value = item
        if isinstance(item, (tuple, list)) and len(item) == 2 and isinstance(item[1], Real):
            value, weight = item
        elif isinstance(item, (tuple, list)) and len(item) == 3 and isinstance(item[2], Real):
            value, weight = item[:2], item[2]

        combo = _explicit_combo(value)
        if combo is not None:
            add(combo, weight)
            continue
        if not isinstance(value, str):
            continue
        for combo in range_to_combos([value], dead):
            add(combo, weight)

    return list(weighted.values())


def _valid_known_cards(hero_cards: Sequence[str], board: Sequence[str]) -> bool:
    cards = [_card_text(card) for card in list(hero_cards or ()) + list(board or ())]
    return (
        len(hero_cards or ()) == 2
        and len(board or ()) <= 5
        and all(cards)
        and len(cards) == len(set(cards))
    )


def _showdown_share(hero, villains, full_board) -> float:
    hero_score = eval7.evaluate(list(hero) + list(full_board))
    scores = [eval7.evaluate(list(villain) + list(full_board)) for villain in villains]
    best = max([hero_score] + scores)
    if hero_score != best:
        return 0.0
    return 1.0 / (1 + sum(score == best for score in scores))


def _uniform_weights(options) -> bool:
    if not options:
        return False
    first = options[0][1]
    return all(abs(weight - first) <= 1e-12 for _, weight in options)


def _native_heads_up_equity(hero, board_cards, options, trials, seed, *, exact=False):
    """Use eval7's Cython range evaluator only where its assumptions hold."""
    if not options or not _uniform_weights(options):
        return None
    native_options = [(combo, 1.0) for combo, _ in options]
    try:
        if exact and len(board_cards) == 5:
            return float(eval7.py_hand_vs_range_exact(hero, native_options, board_cards))
        # Native MC is safe only when we can seed eval7's private xorshift RNG;
        # otherwise reproducible paired-seed benchmarks would be broken.
        from eval7 import xorshift_rand
        xorshift_rand.seed(int(seed))
        return float(eval7.py_hand_vs_range_monte_carlo(
            hero, native_options, board_cards, int(trials)
        ))
    except Exception:
        return None


def _exact_river_equity(hero, board_cards, option_sets, limit: int = 100000):
    """Weighted, collision-free exact river equity when the state is small."""
    if len(board_cards) != 5 or not option_sets:
        return None
    state_space = 1
    for options in option_sets:
        state_space *= max(len(options), 1)
        if state_space > limit:
            return None

    total_weight = 0.0
    total_share = 0.0

    def visit(index, used, villains, weight):
        nonlocal total_weight, total_share
        if index == len(option_sets):
            total_weight += weight
            total_share += weight * _showdown_share(hero, villains, board_cards)
            return
        for combo, combo_weight in option_sets[index]:
            names = (str(combo[0]), str(combo[1]))
            if names[0] in used or names[1] in used:
                continue
            visit(index + 1, used | set(names), villains + [combo], weight * combo_weight)

    visit(0, set(), [], 1.0)
    return total_share / total_weight if total_weight > 0.0 else None


def _choice(options, cumulative, total, rng):
    needle = rng.random() * total
    lo, hi = 0, len(cumulative) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if needle <= cumulative[mid]:
            hi = mid
        else:
            lo = mid + 1
    return options[lo][0]


def _weighted_tables(option_sets):
    tables = []
    for options in option_sets:
        cumulative = []
        total = 0.0
        for _, weight in options:
            total += weight
            cumulative.append(total)
        tables.append((options, cumulative, total))
    return tables


def _sample_collision_free(tables, base_dead, rng):
    """Joint rejection sample from independent ranges, conditioned on blockers."""
    for _ in range(16):
        villains = []
        used = set(base_dead)
        valid = True
        for options, cumulative, total in tables:
            combo = _choice(options, cumulative, total, rng)
            names = (str(combo[0]), str(combo[1]))
            if names[0] in used or names[1] in used:
                valid = False
                break
            used.update(names)
            villains.append(combo)
        if valid:
            return villains, used

    # Extremely tight overlapping ranges can make whole-tuple rejection slow.
    # Bounded sequential fallback keeps the live decision safe. Randomizing the
    # assignment order avoids consistently privileging the first opponent.
    order = list(range(len(tables)))
    rng.shuffle(order)
    chosen = [None] * len(tables)
    used = set(base_dead)
    for index in order:
        options, _, _ = tables[index]
        legal = [entry for entry in options
                 if str(entry[0][0]) not in used and str(entry[0][1]) not in used]
        if not legal:
            return None, None
        cumulative = []
        total = 0.0
        for _, weight in legal:
            total += weight
            cumulative.append(total)
        combo = _choice(legal, cumulative, total, rng)
        chosen[index] = combo
        used.update((str(combo[0]), str(combo[1])))
    return chosen, used


def adaptive_trial_cap(board: Sequence[str], opponents: int) -> int:
    """Live-safe default rollout cap, increasing with unresolved board cards."""
    base = {0: 1000, 3: 720, 4: 560, 5: 0}.get(len(board or ()), 640)
    # Each extra opponent adds an evaluation per rollout; cap total evaluations.
    return max(180, int(base * 2 / max(opponents + 1, 2))) if base else 0


def equity_vs_ranges(hero_cards: Sequence[str],
                     board: Sequence[str],
                     villain_ranges,
                     trials: int = None,
                     rng: random.Random = None,
                     *,
                     threshold: float = None,
                     target_se: float = 0.02,
                     exact_limit: int = 100000,
                     time_budget_ms: float = None,
                     adaptive: bool = True,
                     use_native: bool = True) -> float:
    """Hero's joint pot-share equity against multiple weighted ranges.

    Opponent holdings are sampled jointly and collision-free. Ties award the
    appropriate fractional pot share (not the heads-up-only one half). River
    states are exact when their collision-free product is tractable; uniform
    heads-up river ranges use eval7's native exact evaluator. Monte Carlo may
    stop early once its standard error is small or its 95% interval clears a
    supplied decision threshold.
    """
    try:
        ranges = list(villain_ranges or ())
    except TypeError:
        ranges = []
    ranges = ranges[:5]
    if not _valid_known_cards(hero_cards, board) or not ranges:
        return 0.5

    hero = [eval7.Card(_card_text(card)) for card in hero_cards]
    board_cards = [eval7.Card(_card_text(card)) for card in board]
    dead = [_card_text(card) for card in list(hero_cards) + list(board)]
    option_sets = [range_to_weighted_combos(spec, dead) for spec in ranges]
    if any(not options for options in option_sets):
        # A malformed/totally blocked action range should be neutral rather
        # than turn a live decision into an exception or false certainty.
        return 0.5

    if len(option_sets) == 1 and len(board_cards) == 5 and use_native:
        seed = _stable_seed("native_exact", tuple(hero_cards), tuple(board))
        native = _native_heads_up_equity(
            hero, board_cards, option_sets[0], 0, seed, exact=True
        )
        if native is not None:
            return min(max(native, 0.0), 1.0)

    exact = _exact_river_equity(hero, board_cards, option_sets, limit=exact_limit)
    if exact is not None:
        return min(max(exact, 0.0), 1.0)

    if trials is None:
        trials = adaptive_trial_cap(board, len(option_sets))
    try:
        max_trials = max(int(trials), 1)
    except (TypeError, ValueError, OverflowError):
        max_trials = max(adaptive_trial_cap(board, len(option_sets)), 1)

    seed = _stable_seed(
        "eq_vs_ranges", tuple(hero_cards), tuple(board), max_trials,
        tuple(tuple((str(c1), str(c2), round(weight, 8))
                    for (c1, c2), weight in options)
              for options in option_sets),
    )
    if rng is None:
        rng = random.Random(seed)

    if (use_native and not adaptive and len(option_sets) == 1
            and _uniform_weights(option_sets[0])):
        native = _native_heads_up_equity(
            hero, board_cards, option_sets[0], max_trials, seed, exact=False
        )
        if native is not None:
            return min(max(native, 0.0), 1.0)

    tables = _weighted_tables(option_sets)
    base_dead = set(dead)
    full_deck = [eval7.Card(rank + suit) for rank in RANKS for suit in SUITS]
    needed = 5 - len(board_cards)
    minimum = min(max_trials, max(96, 32 * len(option_sets)))
    started = time.perf_counter()
    total = 0.0
    total_sq = 0.0
    completed = 0

    for _ in range(max_trials):
        villains, used = _sample_collision_free(tables, base_dead, rng)
        if villains is None:
            continue
        if needed:
            available = [card for card in full_deck if str(card) not in used]
            runout = rng.sample(available, needed)
        else:
            runout = []
        share = _showdown_share(hero, villains, board_cards + runout)
        total += share
        total_sq += share * share
        completed += 1

        if completed < minimum or completed % 32:
            continue
        if time_budget_ms is not None:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if elapsed_ms >= max(float(time_budget_ms), 1.0):
                break
        if not adaptive:
            continue
        mean = total / completed
        variance = max(total_sq / completed - mean * mean, 0.0)
        se = math.sqrt(variance / completed)
        if target_se and se <= max(float(target_se), 0.0):
            break
        if threshold is not None and completed >= 128:
            margin = 1.96 * se
            if mean + margin < threshold or mean - margin > threshold:
                break

    return total / completed if completed else 0.5


joint_multiway_equity = equity_vs_ranges


def equity_vs_range(hero_cards: Sequence[str],
                    board: Sequence[str],
                    villain_range: Iterable[str],
                    trials: int = 300,
                    rng: random.Random = None) -> float:
    """Backward-compatible deterministic heads-up equity API.

    Explicit trial counts run to completion so accuracy studies retain their
    old coarse/fine semantics. Complete boards still take the safe native-exact
    fast path.
    """
    return equity_vs_ranges(
        hero_cards,
        board,
        [villain_range],
        trials=trials,
        rng=rng,
        target_se=0.0,
        adaptive=False,
        use_native=len(board or ()) == 5,
    )


def hand_strength(hero_cards: Sequence[str], board: Sequence[str], trials: int = 200,
                  opponents: int = 1) -> float:
    """Equity versus one or more uniformly random collision-free holdings."""
    try:
        n_opponents = min(max(int(opponents), 1), 5)
    except (TypeError, ValueError, OverflowError):
        n_opponents = 1
    if n_opponents > 1:
        return equity_vs_ranges(
            hero_cards,
            board,
            [ALL_STARTING_HANDS] * n_opponents,
            trials=trials,
            target_se=0.0,
            adaptive=False,
            use_native=False,
        )
    if not _valid_known_cards(hero_cards, board):
        return 0.5
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


def joint_hand_strength(hero_cards: Sequence[str], board: Sequence[str],
                        opponents: int, trials: int = 400) -> float:
    """Named convenience wrapper for uniform multiway equity."""
    return hand_strength(hero_cards, board, trials=trials, opponents=opponents)
