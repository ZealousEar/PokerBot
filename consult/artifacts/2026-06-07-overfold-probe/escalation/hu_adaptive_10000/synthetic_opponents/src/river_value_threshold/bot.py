STYLE = "river_value_threshold"
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


def _tag_score(tag):
    if not tag:
        return 0
    if len(tag) == 2 and tag[0] == tag[1]:
        return 100 + max(0, RANKS.find(tag[0])) * 4
    hi = max(0, RANKS.find(tag[0]))
    lo = max(0, RANKS.find(tag[1])) if len(tag) > 1 else 0
    suited_bonus = 8 if tag.endswith("s") else 0
    connector_bonus = 4 if abs(hi - lo) <= 2 else 0
    return hi * 4 + lo + suited_bonus + connector_bonus


def _wide_pressure_open(tag):
    if not tag:
        return False
    if len(tag) == 2 and tag[0] == tag[1]:
        return RANKS.find(tag[0]) >= RANKS.find("4")
    return _tag_score(tag) >= 47 or tag[0] in "AKQJ" or tag[:2] in {"T9", "98", "87", "76", "65"}


def _deterministic_mix(state, modulo=10):
    token = str(state.get("hand_id", "")) + str(state.get("street", ""))
    for card in state.get("your_cards") or []:
        token += str(card)
    total = 0
    for ch in token:
        total += ord(ch)
    return total % max(1, int(modulo))


def _pressure_raise(state, frac=0.66):
    stack = int(state.get("your_stack") or 0)
    my_bet = int(state.get("your_bet_this_street") or 0)
    current = int(state.get("current_bet") or 0)
    min_raise = int(state.get("min_raise_to") or 0)
    pot = int(state.get("pot") or 0)
    if stack <= 0:
        return _fold_or_check(state)
    raw_target = current + max(100, int(pot * frac))
    commit_cap = my_bet + max(1, int(stack * 0.55))
    target = min(raw_target, commit_cap)
    if target < min_raise:
        if min_raise - my_bet >= int(stack * 0.55):
            return _call_or_check(state)
        target = min_raise
    return _raise_to(state, target)


def _rank_counts(state):
    cards = list(state.get("your_cards") or []) + list(state.get("community_cards") or [])
    ranks = [c[0] for c in cards if isinstance(c, str) and len(c) >= 2]
    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    return counts


def _has_pair_or_better(state):
    return any(count >= 2 for count in _rank_counts(state).values())


def _two_pair_or_better(state):
    counts = list(_rank_counts(state).values())
    return any(count >= 3 for count in counts) or sum(1 for count in counts if count >= 2) >= 2


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


_ADAPT_PRESSURE_ATTEMPTS = 0
_ADAPT_PRESSURE_FOLDS = 0
_ADAPT_PRESSURE_CONTINUES = 0
_ADAPT_SEEN_PRESSURES = {}


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _active_opponent_count(state):
    my_seat = _safe_int(state.get("seat_to_act"), -999)
    count = 0
    for player in state.get("players") or []:
        if not isinstance(player, dict):
            continue
        if _safe_int(player.get("seat"), -1) == my_seat:
            continue
        if player.get("is_folded") or str(player.get("state", "")).lower() == "folded":
            continue
        count += 1
    return max(1, count)


def _observe_adaptive_pressure(state):
    global _ADAPT_PRESSURE_ATTEMPTS, _ADAPT_PRESSURE_FOLDS, _ADAPT_PRESSURE_CONTINUES
    my_seat = _safe_int(state.get("seat_to_act"), -999)
    hand_id = str(state.get("hand_id", ""))
    log = state.get("action_log") or []
    for index, entry in enumerate(log):
        if not isinstance(entry, dict):
            continue
        if _safe_int(entry.get("seat"), -1) != my_seat:
            continue
        if str(entry.get("action", "")).lower() not in {"raise", "all_in"}:
            continue
        key = hand_id + ":" + str(index)
        if _ADAPT_SEEN_PRESSURES.get(key):
            continue
        response = ""
        for later in log[index + 1:]:
            if not isinstance(later, dict):
                continue
            later_seat = _safe_int(later.get("seat"), -1)
            later_action = str(later.get("action", "")).lower()
            if later_seat == my_seat:
                break
            if later_action == "fold":
                response = "fold"
                break
            if later_action in {"call", "raise", "all_in"}:
                response = "continue"
                break
        if not response:
            continue
        _ADAPT_SEEN_PRESSURES[key] = 1
        _ADAPT_PRESSURE_ATTEMPTS += 1
        if response == "fold":
            _ADAPT_PRESSURE_FOLDS += 1
        else:
            _ADAPT_PRESSURE_CONTINUES += 1


def _adaptive_fold_rate():
    return float(_ADAPT_PRESSURE_FOLDS + 2) / float(_ADAPT_PRESSURE_ATTEMPTS + 4)


def _made_rank(state):
    counts = list(_rank_counts(state).values())
    pairs = sum(1 for count in counts if count >= 2)
    if any(count >= 4 for count in counts):
        return 4
    if any(count >= 3 for count in counts):
        return 3
    if pairs >= 2:
        return 2
    if pairs == 1:
        return 1
    return 0


def _pressure_threshold(base, state):
    rate = _adaptive_fold_rate()
    threshold = int(base)
    if _ADAPT_PRESSURE_ATTEMPTS >= 12 and rate >= 0.66:
        threshold += 30
    elif _ADAPT_PRESSURE_ATTEMPTS >= 6 and rate >= 0.58:
        threshold += 18
    elif _ADAPT_PRESSURE_ATTEMPTS >= 10 and rate <= 0.44:
        threshold -= 18
    active = _active_opponent_count(state)
    if active > 1:
        threshold -= min(24, 8 * (active - 1))
    if threshold < 0:
        return 0
    if threshold > 96:
        return 96
    return threshold


def _adaptive_pressure(state, base, frac):
    if _deterministic_mix(state, 100) < _pressure_threshold(base, state):
        return _pressure_raise(state, frac)
    return {"action": "check"}


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

    if STYLE == "overfold_exploiter":
        mix = _deterministic_mix(state, 10)
        threshold = owed / float(pot + owed) if pot + owed > 0 else 1.0
        made = _has_pair_or_better(state)

        if street == "preflop":
            if can_check:
                if _wide_pressure_open(tag) or mix <= 7:
                    return _pressure_raise(state, 0.80)
                return {"action": "check"}
            if _premium(tag):
                if owed <= max(300, int(stack * 0.18)) and mix <= 4:
                    return _pressure_raise(state, 0.85)
                return {"action": "call"} if owed <= max(600, int(stack * 0.24)) else {"action": "fold"}
            if _wide_pressure_open(tag) and threshold <= 0.26 and owed <= max(350, int(stack * 0.09)):
                return {"action": "call"}
            return {"action": "fold"}

        if owed > 0:
            # Bet-fold discipline: this bot pressures folds but does not pay off
            # counter-pressure with weak showdown value.
            if _two_pair_or_better(state) and threshold <= 0.18 and owed <= max(250, int(stack * 0.16)):
                return {"action": "call"}
            return _fold_or_check(state)

        if street == "flop":
            if made or mix <= 8:
                return _pressure_raise(state, 0.62)
            return {"action": "check"}
        if street == "turn":
            if made or mix <= 7:
                return _pressure_raise(state, 0.72)
            return {"action": "check"}
        if street == "river":
            if _two_pair_or_better(state) and mix <= 4:
                return _pressure_raise(state, 0.42)
            return {"action": "check"}

    if STYLE == "adaptive_overfold_exploiter":
        _observe_adaptive_pressure(state)
        price = owed / float(pot + owed) if pot + owed > 0 else 1.0
        made_rank = _made_rank(state)
        made = made_rank >= 1
        strong = made_rank >= 2
        fold_rate = _adaptive_fold_rate()
        multiway = _active_opponent_count(state) > 1

        if street == "preflop":
            if can_check:
                if _wide_pressure_open(tag) and (_deterministic_mix(state, 100) < _pressure_threshold(54 if not multiway else 34, state)):
                    return _pressure_raise(state, 0.70)
                return {"action": "check"}
            if _premium(tag):
                if owed <= max(300, int(stack * 0.16)) and _deterministic_mix(state, 100) < 38:
                    return _pressure_raise(state, 0.78)
                return {"action": "call"} if owed <= max(650, int(stack * 0.25)) else {"action": "fold"}
            if _wide_pressure_open(tag) and price <= 0.23 and owed <= max(300, int(stack * 0.075)):
                return {"action": "call"}
            return {"action": "fold"}

        if owed > 0:
            # Sharp-defensive response: keep pressure edge, but do not pay off
            # obvious value or stack off weak made hands after resistance.
            if made_rank >= 3 and price <= 0.38 and owed <= max(500, int(stack * 0.35)):
                return {"action": "call"}
            if made_rank >= 2 and price <= 0.27 and owed <= max(350, int(stack * 0.22)):
                return {"action": "call"}
            if made and price <= 0.11 and owed <= max(150, int(stack * 0.06)):
                return {"action": "call"}
            return _fold_or_check(state)

        if street == "flop":
            if strong:
                return _pressure_raise(state, 0.70)
            if made:
                return _pressure_raise(state, 0.58 if multiway else 0.64)
            base = 50 if multiway else 68
            frac = 0.55 if fold_rate < 0.60 else 0.68
            return _adaptive_pressure(state, base, frac)
        if street == "turn":
            if strong:
                return _pressure_raise(state, 0.76)
            if made and _deterministic_mix(state, 100) < _pressure_threshold(56 if not multiway else 34, state):
                return _pressure_raise(state, 0.68)
            base = 30 if multiway else 46
            frac = 0.62 if fold_rate < 0.62 else 0.78
            return _adaptive_pressure(state, base, frac)
        if street == "river":
            if strong:
                return _pressure_raise(state, 0.48)
            if (not multiway) and _ADAPT_PRESSURE_ATTEMPTS >= 12 and fold_rate >= 0.68 and _deterministic_mix(state, 100) < 16:
                return _pressure_raise(state, 0.34)
            return {"action": "check"}

    return _fold_or_check(state)
