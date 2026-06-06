"""Behavior-only opponent pressure features.

The model deliberately ignores player names and archive labels. It derives a
small table-level signal from public actions: how often non-hero seats raise,
move all-in, call, or fold across the rolling match log.

# Source: [[Libratus-Brown-Sandholm-2017]]
# Source: [[Engine-Fullhouse]]
"""

AGGRESSIVE_ACTIONS = ("raise", "all_in")
PASSIVE_ACTIONS = ("call", "check", "fold")


class OpponentModel:
    """Stateless feature extractor over the engine's public action logs."""

    def pressure_features(self, game_state: dict) -> dict:
        hero_seat = _int(game_state.get("seat_to_act"), -1)
        actions = _observed_actions(game_state)
        other_actions = [
            item for item in actions
            if item.get("seat") is not None and _int(item.get("seat"), -2) != hero_seat
        ]

        total = 0
        raises = 0
        all_ins = 0
        calls = 0
        folds = 0
        for item in other_actions:
            action = str(item.get("action", "")).lower()
            if action in AGGRESSIVE_ACTIONS or action in PASSIVE_ACTIONS:
                total += 1
            if action in AGGRESSIVE_ACTIONS:
                raises += 1
            if action == "all_in":
                all_ins += 1
            if action == "call":
                calls += 1
            if action == "fold":
                folds += 1

        current_pressure = _current_pressure(game_state, hero_seat)
        raise_rate = raises / max(1, total)
        all_in_rate = all_ins / max(1, total)
        fold_rate = folds / max(1, total)
        call_rate = calls / max(1, total)

        high_pressure = (
            (total >= 4 and raise_rate >= 0.48)
            or (total >= 2 and raise_rate >= 0.75 and current_pressure["facing_raise"])
            or current_pressure["raise_count"] >= 2
        )
        fold_prone_pressure = (
            total >= 6
            and raise_rate >= 0.34
            and fold_rate >= 0.30
            and call_rate <= 0.35
        )

        return {
            "actions": total,
            "raises": raises,
            "all_ins": all_ins,
            "calls": calls,
            "folds": folds,
            "raise_rate": raise_rate,
            "all_in_rate": all_in_rate,
            "fold_rate": fold_rate,
            "call_rate": call_rate,
            "facing_raise": current_pressure["facing_raise"],
            "high_pressure": high_pressure,
            "fold_prone_pressure": fold_prone_pressure,
        }


def _observed_actions(game_state: dict) -> list:
    match_log = game_state.get("match_action_log")
    if isinstance(match_log, list) and match_log:
        return [item for item in match_log if isinstance(item, dict)]
    action_log = game_state.get("action_log")
    if isinstance(action_log, list):
        return [
            item for item in action_log
            if isinstance(item, dict)
            and str(item.get("action", "")).lower() not in ("small_blind", "big_blind")
        ]
    return []


def _current_pressure(game_state: dict, hero_seat: int) -> dict:
    raise_count = 0
    for item in game_state.get("action_log") or []:
        if not isinstance(item, dict):
            continue
        seat = _int(item.get("seat"), -2)
        action = str(item.get("action", "")).lower()
        if seat != hero_seat and action in AGGRESSIVE_ACTIONS:
            raise_count += 1
    return {
        "raise_count": raise_count,
        "facing_raise": bool(game_state.get("amount_owed")) and raise_count > 0,
    }


def _int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
