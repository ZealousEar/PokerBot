"""Deterministic synthetic opponents for edge-case match smoke tests.

These are not strategy benchmarks. They are pressure fixtures designed to
trigger runner failure classes: all-in pressure, pot-odds calls, river value
thresholds, TAG pressure, and LAG pressure. The generated bots avoid randomness
so paired-seed reproducibility failures point at the subject bot or harness.
"""
from __future__ import annotations

import argparse
from pathlib import Path


COMMON_HELPERS = r'''
RANK_ORDER = "23456789TJQKA"


def _num(state, key, default=0):
    try:
        return int(state.get(key, default) or 0)
    except Exception:
        return default


def _cards(state):
    cards = state.get("your_cards") or []
    if len(cards) != 2:
        return ["2c", "7d"]
    return cards


def _ranks(cards):
    return [c[0] for c in cards if isinstance(c, str) and c]


def _rank_value(rank):
    try:
        return RANK_ORDER.index(rank)
    except ValueError:
        return 0


def _has_pair_or_better(state):
    ranks = _ranks(_cards(state)) + _ranks(state.get("community_cards") or [])
    return any(ranks.count(r) >= 2 for r in ranks)


def _hole_strength(state):
    ranks = _ranks(_cards(state))
    if len(ranks) < 2:
        return 0
    values = sorted((_rank_value(r) for r in ranks), reverse=True)
    paired = ranks[0] == ranks[1]
    suited = _cards(state)[0][-1:] == _cards(state)[1][-1:]
    score = values[0] * 4 + values[1]
    if paired:
        score += 40
    if suited:
        score += 5
    return score


def _can_check(state):
    return bool(state.get("can_check")) or _num(state, "amount_owed") <= 0


def _safe_passive(state):
    if _can_check(state):
        return {"action": "check"}
    return {"action": "fold"}


def _raise_to(state, multiple=3):
    stack = _num(state, "your_stack")
    already = _num(state, "your_bet_this_street")
    cap = stack + already
    min_raise = _num(state, "min_raise_to", _num(state, "current_bet") + 100)
    if cap <= 0:
        return {"action": "fold"}
    if cap <= min_raise:
        return {"action": "all_in"}
    target = max(min_raise, min(cap - 1, min_raise * multiple))
    return {"action": "raise", "amount": target}
'''


OPPONENT_SOURCES = {
    "maniac_all_in": COMMON_HELPERS + r'''
def decide(state):
    if state.get("type") == "warmup":
        return {"action": "check"}
    if _num(state, "your_stack") > 0:
        return {"action": "all_in"}
    return _safe_passive(state)
''',
    "pot_odds_threshold": COMMON_HELPERS + r'''
def decide(state):
    if state.get("type") == "warmup":
        return {"action": "check"}
    owed = _num(state, "amount_owed")
    pot = max(_num(state, "pot"), 1)
    if _can_check(state):
        return {"action": "check"}
    if owed > 0 and pot / max(owed, 1) >= 2.75:
        return {"action": "call"}
    return {"action": "fold"}
''',
    "river_value_threshold": COMMON_HELPERS + r'''
def decide(state):
    if state.get("type") == "warmup":
        return {"action": "check"}
    street = state.get("street")
    owed = _num(state, "amount_owed")
    pot = max(_num(state, "pot"), 1)
    if street == "river" and _has_pair_or_better(state):
        if _can_check(state):
            return _raise_to(state, 2)
        if owed / pot <= 0.35:
            return {"action": "call"}
    return _safe_passive(state)
''',
    "tight_aggressive": COMMON_HELPERS + r'''
def decide(state):
    if state.get("type") == "warmup":
        return {"action": "check"}
    street = state.get("street")
    strength = _hole_strength(state)
    owed = _num(state, "amount_owed")
    pot = max(_num(state, "pot"), 1)
    if street == "preflop":
        if strength >= 82:
            return _raise_to(state, 3)
        if strength >= 55 and owed / pot <= 0.20:
            return {"action": "call"}
        return _safe_passive(state)
    if _has_pair_or_better(state):
        if _can_check(state):
            return _raise_to(state, 2)
        if owed / pot <= 0.25:
            return {"action": "call"}
    return _safe_passive(state)
''',
    "loose_aggressive": COMMON_HELPERS + r'''
def decide(state):
    if state.get("type") == "warmup":
        return {"action": "check"}
    street = state.get("street")
    strength = _hole_strength(state)
    owed = _num(state, "amount_owed")
    pot = max(_num(state, "pot"), 1)
    hand_id = str(state.get("hand_id", ""))
    deterministic_mix = sum(ord(ch) for ch in hand_id) % 5
    if street == "preflop" and strength >= 35:
        return _raise_to(state, 2)
    if _can_check(state):
        if deterministic_mix in (0, 2, 4):
            return _raise_to(state, 2)
        return {"action": "check"}
    if owed / pot <= 0.45:
        return {"action": "call"}
    if deterministic_mix == 1 and _num(state, "your_stack") > owed:
        return _raise_to(state, 2)
    return {"action": "fold"}
''',
}


def write_opponents(target_dir: Path, names: list[str] | None = None) -> dict[str, Path]:
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    selected = names or sorted(OPPONENT_SOURCES)
    paths: dict[str, Path] = {}
    for name in selected:
        if name not in OPPONENT_SOURCES:
            raise KeyError(f"unknown synthetic opponent {name!r}")
        bot_dir = target_dir / name
        bot_dir.mkdir(parents=True, exist_ok=True)
        (bot_dir / "bot.py").write_text(OPPONENT_SOURCES[name])
        paths[name] = bot_dir
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--names", nargs="*", default=None)
    args = parser.parse_args()
    paths = write_opponents(args.output, args.names)
    for name, path in sorted(paths.items()):
        print(f"{name}: {path / 'bot.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
