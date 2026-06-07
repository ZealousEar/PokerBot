"""Exact-enumeration baselines for validating the Monte-Carlo equity estimator.

`src/equity.py` estimates hero equity vs a villain range by Monte-Carlo
sampling (a villain combo + a random run-out, repeated `trials` times). On the
turn and river the remaining board is small enough to enumerate *exactly*, which
gives a ground-truth number to check the estimator against. This module provides
that exact baseline plus a convergence sweep, reusing the same
`range_to_combos` + `eval7.evaluate` primitives the bot uses.

Engine-free: only eval7 is needed.
"""
from __future__ import annotations

import itertools
from typing import Iterable, Sequence

import eval7

from src.equity import RANKS, SUITS, equity_vs_range, range_to_combos


def exact_equity_vs_range(
    hero: Sequence[str], board: Sequence[str], villain_range: Iterable[str]
) -> float:
    """Exact hero equity vs `villain_range` by full enumeration of villain
    combos and remaining board run-outs. Cheap on turn (1 card) and river
    (0 cards); usable but heavier on the flop (2 cards)."""
    dead = list(hero) + list(board)
    hero_cards = [eval7.Card(c) for c in hero]
    board_cards = [eval7.Card(c) for c in board]
    combos = range_to_combos(villain_range, dead)
    if not combos:
        return 0.5
    needed = 5 - len(board_cards)
    total = 0.0
    n = 0
    for vc1, vc2 in combos:
        used = set(dead) | {str(vc1), str(vc2)}
        deck = [eval7.Card(r + s) for r in RANKS for s in SUITS if (r + s) not in used]
        for runout in itertools.combinations(deck, needed):
            full = board_cards + list(runout)
            hero_score = eval7.evaluate(hero_cards + full)
            vill_score = eval7.evaluate([vc1, vc2] + full)
            if hero_score > vill_score:
                total += 1.0
            elif hero_score == vill_score:
                total += 0.5
            n += 1
    return total / n if n else 0.5


def convergence_sweep(
    hero: Sequence[str],
    board: Sequence[str],
    villain_range: Iterable[str],
    trial_grid: Sequence[int] = (100, 300, 1000, 3000, 10000),
):
    """Return (trial_grid, mc_estimates, exact) so a caller can plot how the
    Monte-Carlo estimate converges to the enumerated baseline."""
    villain_range = list(villain_range)
    exact = exact_equity_vs_range(hero, board, villain_range)
    mc = [equity_vs_range(hero, board, villain_range, trials=t) for t in trial_grid]
    return list(trial_grid), mc, exact
