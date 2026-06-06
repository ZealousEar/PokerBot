STYLE = "loose_aggressive"
RANKS = "23456789TJQKA"


def _rank_value(card):
    if not isinstance(card, str) or len(card) < 1:
        return -1
    return RANKS.find(card[0])


def _hand_tag(cards):
    if not isinstance(cards, list) or len(cards) != 2:
        return ""
    a, b = cards[0], cards[1]
    if not isinstance(a, str) or not isinstance(b, str) or len(a) < 2 or len(b) < 2:
        return ""
    ra, rb = a[0], b[0]
    sa, sb = a[1], b[1]
    if ra == rb:
        return ra + rb
    if _rank_value(a) < _rank_value(b):
        ra, rb, sa, sb = rb, ra, sb, sa
    return ra + rb + ("s" if sa == sb else "o")


def _premium(tag):
    return tag in {"AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs"}


def _broadway_or_pair(tag):
    if not tag:
        return False
    if len(tag) == 2 and tag[0] == tag[1]:
        return True
    return tag[0] in "AKQJ" or (len(tag) > 1 and tag[1] in "AKQJ")


def _has_pair_or_better(state):
    cards = list(state.get("your_cards") or []) + list(state.get("community_cards") or [])
    ranks = [c[0] for c in cards if isinstance(c, str) and len(c) >= 2]
    for r in set(ranks):
        if ranks.count(r) >= 2:
            return True
    return False


def _raise_to(state, target):
    stack = int(state.get("your_stack") or 0)
    my_bet = int(state.get("your_bet_this_street") or 0)
    min_raise = int(state.get("min_raise_to") or 0)
    target = max(int(target), min_raise)
    if target - my_bet >= stack:
        return {"action": "all_in"}
    return {"action": "raise", "amount": target}


def _pot_raise(state, frac=0.75):
    pot = int(state.get("pot") or 0)
    current = int(state.get("current_bet") or 0)
    return _raise_to(state, current + max(100, int(pot * frac)))


def _call_or_check(state):
    return {"action": "check"} if state.get("can_check") else {"action": "call"}


def _fold_or_check(state):
    return {"action": "check"} if state.get("can_check") else {"action": "fold"}


def decide(state):
    if not isinstance(state, dict):
        return {"action": "fold"}
    if state.get("type") == "warmup":
        return {"action": "check"}

    tag = _hand_tag(state.get("your_cards") or [])
    owed = int(state.get("amount_owed") or 0)
    pot = int(state.get("pot") or 0)
    stack = int(state.get("your_stack") or 0)
    street = state.get("street", "preflop")
    can_check = bool(state.get("can_check"))

    if STYLE == "all_in_maniac":
        return {"action": "all_in"} if stack > 0 else _call_or_check(state)

    if STYLE == "tight_passive":
        if _premium(tag):
            return _call_or_check(state)
        if can_check:
            return {"action": "check"}
        return {"action": "call"} if owed <= max(100, pot // 5) else {"action": "fold"}

    if STYLE == "loose_passive":
        if can_check:
            return {"action": "check"}
        return {"action": "call"} if owed <= max(100, int(0.55 * (pot + owed))) else {"action": "fold"}

    if STYLE == "tight_aggressive":
        if street == "preflop":
            if _premium(tag):
                return _pot_raise(state, 1.0)
            return _fold_or_check(state)
        if _has_pair_or_better(state):
            return _pot_raise(state, 0.8) if can_check or owed <= stack // 4 else {"action": "call"}
        return _fold_or_check(state)

    if STYLE == "loose_aggressive":
        if _broadway_or_pair(tag) or _has_pair_or_better(state) or can_check:
            return _pot_raise(state, 0.9)
        return {"action": "call"} if owed <= max(100, stack // 3) else {"action": "fold"}

    if STYLE == "pot_odds_threshold":
        if can_check:
            return {"action": "check"}
        threshold = owed / float(pot + owed) if pot + owed > 0 else 1.0
        return {"action": "call"} if threshold <= 0.30 else {"action": "fold"}

    if STYLE == "river_value_threshold":
        if street == "river" and _has_pair_or_better(state):
            if can_check:
                return _pot_raise(state, 0.66)
            return {"action": "call"} if owed <= max(100, int(0.45 * (pot + owed))) else {"action": "fold"}
        if can_check:
            return {"action": "check"}
        threshold = owed / float(pot + owed) if pot + owed > 0 else 1.0
        return {"action": "call"} if threshold <= 0.22 else {"action": "fold"}

    return _fold_or_check(state)
