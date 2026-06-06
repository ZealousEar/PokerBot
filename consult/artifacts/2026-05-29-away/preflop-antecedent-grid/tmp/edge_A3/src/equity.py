"""Monte Carlo equity vs range using eval7.

Budget: ≤ 5 ms per call at default trials. Pre-warm eval7 LUTs at module
import so the live 2 s decisions don't pay a cold-start cost.
"""
import random

import eval7

_RANKS = "23456789TJQKA"
_SUITS = "shdc"
_FULL_DECK = tuple(rank + suit for rank in _RANKS for suit in _SUITS)

# Pre-warm eval7's evaluator tables at import.
eval7.evaluate([eval7.Card(c) for c in ("As", "Ks", "Qs", "Js", "Ts", "2c", "3d")])


def _cards(raw) -> list:
    return [eval7.Card(str(card)) for card in raw if str(card) in _FULL_DECK]


def equity_vs_range(hero: tuple, board: tuple, villain_range, trials: int = 2000) -> float:
    """Return hero's equity vs villain_range as a float in [0, 1]."""
    hero_cards = tuple(str(c) for c in hero)
    board_cards = tuple(str(c) for c in board)
    known = set(hero_cards) | set(board_cards)
    if len(hero_cards) != 2 or len(known) != len(hero_cards) + len(board_cards):
        return 0.0

    deck = [card for card in _FULL_DECK if card not in known]
    if len(deck) < 2:
        return 0.0
    rng = random.Random((hash(hero_cards) ^ hash(board_cards) ^ int(trials)) & 0xFFFFFFFF)
    range_hands = []
    if villain_range:
        for item in villain_range:
            if len(item) == 2 and item[0] not in known and item[1] not in known:
                range_hands.append((str(item[0]), str(item[1])))

    wins = ties = 0
    runouts = max(1, 5 - len(board_cards))
    hero_eval_cards = _cards(hero_cards)
    board_eval_cards = _cards(board_cards)
    for _ in range(max(1, int(trials))):
        if range_hands:
            villain = rng.choice(range_hands)
            if villain[0] in known or villain[1] in known:
                continue
            remaining = [card for card in deck if card not in villain]
        else:
            villain = tuple(rng.sample(deck, 2))
            remaining = [card for card in deck if card not in villain]
        sampled_board = rng.sample(remaining, runouts)
        full_board = board_eval_cards + _cards(sampled_board)
        hero_score = eval7.evaluate(hero_eval_cards + full_board)
        villain_score = eval7.evaluate(_cards(villain) + full_board)
        if hero_score > villain_score:
            wins += 1
        elif hero_score == villain_score:
            ties += 1
    return (wins + ties * 0.5) / max(1, int(trials))
