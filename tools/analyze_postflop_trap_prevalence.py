#!/usr/bin/env python3
"""Patch-window postflop trap prevalence extractor.

Reads JSON, JSONL, or directories of hand histories and emits field-level
signals for the Toby/Mehedi postflop-trap class. This is tooling only: it does
not write runtime priors or strategy data.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


WRAPPER_HAND_LIST_ALIASES = [
    "hands",
    "records",
    "histories",
    "hand_histories",
    "handHistories",
]
ACTION_LIST_ALIASES = [
    "action_log",
    "actionLog",
    "actions",
    "events",
    "log",
    "moves",
    "plays",
]
STREET_LIST_ALIASES = [
    "streets",
    "rounds",
    "phases",
    "betting_rounds",
    "bettingRounds",
    "street_actions",
    "streetActions",
]
STREET_NAME_ALIASES = ["street", "name", "round", "phase"]
TOP_LEVEL_ALIASES = {
    "players": ["players", "seats", "participants", "participant_list", "participantList"],
    "big_blind": ["big_blind", "bigBlind", "bigblind", "bb", "BB", "big_blind_amount", "bigBlindAmount"],
}
ACTION_FIELD_ALIASES = {
    "actor": ["actor", "actor_id", "actorId", "player", "player_id", "playerId", "seat", "seat_to_act", "seatToAct"],
    "action": ["action", "type", "verb", "move", "event", "event_type", "eventType", "decision"],
    "street": ["street", "round", "phase"],
    "amount": ["amount", "size", "bet_size", "betSize", "wager", "chips", "total", "raise_to", "raiseTo"],
    "amount_bb": ["amount_bb", "amountBB", "amountBb", "bb_amount", "bbAmount", "size_bb", "sizeBB", "bet_size_bb", "betSizeBB", "wager_bb", "wagerBB"],
    "to_call": ["to_call", "toCall", "amount_to_call", "amountToCall", "call_amount", "callAmount", "amount_owed", "amountOwed", "owed"],
    "can_check": ["can_check", "canCheck", "check_allowed", "checkAllowed"],
    "facing_bet": ["facing_bet", "facingBet", "facing_raise", "facingRaise", "facing_action", "facingAction"],
    "position": ["position", "pos", "position_label", "positionLabel", "seat_position", "seatPosition"],
    "board": ["board", "community_cards", "communityCards", "board_cards", "boardCards", "community"],
    "texture": ["board_texture", "boardTexture", "board_texture_bucket", "boardTextureBucket", "texture", "texture_bucket", "textureBucket"],
}
DELTA_VALUE_ALIASES = [
    "chip_delta",
    "chipDelta",
    "hand_delta",
    "handDelta",
    "final_hand_chip_delta",
    "finalHandChipDelta",
    "delta",
    "net",
    "profit",
    "chips_won",
    "chipsWon",
    "win_loss",
    "winLoss",
]
DELTA_MAP_ALIASES = [
    "chip_deltas",
    "chipDeltas",
    "stack_delta",
    "stackDelta",
    "stack_deltas",
    "stackDeltas",
    "net_by_player",
    "netByPlayer",
    "outcome",
    "outcomes",
    "results",
]

AGGRESSIVE_ACTIONS = {
    "bet",
    "bets",
    "betted",
    "raise",
    "raises",
    "raised",
    "open",
    "opens",
    "opened",
}
ALL_IN_ACTIONS = {
    "allin",
    "all_in",
    "all-in",
    "jam",
    "jams",
    "jammed",
    "shove",
    "shoves",
    "shoved",
    "push",
    "pushes",
    "pushed",
}
CALL_ACTIONS = {"call", "calls", "called", "match", "matches", "matched"}
FOLD_ACTIONS = {"fold", "folds", "folded", "pass", "passes", "passed"}
CHECK_ACTIONS = {"check", "checks", "checked"}
POSTFLOP_STREETS = {"flop", "turn", "river"}
RANK_ORDER = {r: i for i, r in enumerate("23456789TJQKA", start=2)}
CARD_RE = re.compile(r"([2-9TJQKA])([cdhsCDHS])")


def _normalize_key(value: Any) -> str:
    return "".join(ch for ch in str(value).lower() if ch not in "_- /")


def _key_by_alias(mapping: dict[str, Any], aliases: list[str]) -> str | None:
    if not isinstance(mapping, dict):
        return None
    by_normalized = {_normalize_key(k): k for k in mapping}
    for alias in aliases:
        key = by_normalized.get(_normalize_key(alias))
        if key is not None:
            return key
    return None


def _value_by_alias(mapping: dict[str, Any], aliases: list[str], default: Any = None) -> Any:
    key = _key_by_alias(mapping, aliases)
    return mapping.get(key, default) if key is not None else default


def _finite_float(value: Any) -> tuple[float | None, bool]:
    if value in (None, ""):
        return None, False
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, False
    if not math.isfinite(parsed):
        return None, True
    return parsed, False


def _canonical_street(value: Any) -> str:
    norm = _normalize_key(value if value is not None else "preflop")
    if norm in {"pre", "pf", "preflop", "beforeflop"}:
        return "preflop"
    if norm in {"f", "flop"}:
        return "flop"
    if norm in {"t", "turn"}:
        return "turn"
    if norm in {"r", "river"}:
        return "river"
    return str(value).strip().lower() if value is not None else "preflop"


def _canonical_action(raw_action: Any, to_call: Any = None) -> str:
    if raw_action is None:
        return "unknown"
    norm = _normalize_key(raw_action)
    owed, _ = _finite_float(to_call)
    if norm == "checkcall":
        return "call" if owed and owed > 0 else "check"
    if norm in {_normalize_key(x) for x in ALL_IN_ACTIONS}:
        return "all_in"
    if norm in {_normalize_key(x) for x in AGGRESSIVE_ACTIONS}:
        return "raise"
    if norm in {_normalize_key(x) for x in CALL_ACTIONS}:
        return "call"
    if norm in {_normalize_key(x) for x in FOLD_ACTIONS}:
        return "fold"
    if norm in {_normalize_key(x) for x in CHECK_ACTIONS}:
        return "check"
    return "unknown"


def _canonical_position(value: Any) -> str | None:
    if value in (None, ""):
        return None
    norm = _normalize_key(value)
    aliases = {
        "btn": "button",
        "button": "button",
        "dealer": "button",
        "sb": "small_blind",
        "smallblind": "small_blind",
        "bb": "big_blind",
        "bigblind": "big_blind",
        "utg": "early",
        "ep": "early",
        "early": "early",
        "mp": "middle",
        "middle": "middle",
        "hj": "middle",
        "co": "cutoff",
        "cutoff": "cutoff",
        "headsbutton": "heads_up_button",
        "headsupbutton": "heads_up_button",
    }
    return aliases.get(norm, str(value).strip().lower().replace(" ", "_").replace("-", "_"))


def _walk_records_with_source(path: Path) -> Iterable[tuple[str, dict[str, Any]]]:
    if path.is_file():
        yield from _walk_records_from_file(path)
        return
    for child in sorted(path.rglob("*")):
        if child.is_file() and child.suffix.lower() in {".json", ".jsonl", ".log"}:
            yield from _walk_records_from_file(child)


def _walk_records_from_file(path: Path) -> Iterable[tuple[str, dict[str, Any]]]:
    text = path.read_text(encoding="utf-8")
    source = str(path)
    try:
        obj = json.loads(text)
        for record in _records_from_json_object(obj):
            yield source, record
        return
    except json.JSONDecodeError:
        pass

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        for record in _records_from_json_object(obj):
            yield source, record


def _records_from_json_object(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                yield item
        return
    if not isinstance(obj, dict):
        return
    wrapped = _find_wrapped_hand_records(obj)
    if wrapped:
        yield from wrapped
        return
    yield obj


def _looks_like_action_entry(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if _key_by_alias(entry, ACTION_FIELD_ALIASES["action"]) is not None:
        return True
    return any(isinstance(value, str) and _canonical_action(value) != "unknown" for value in entry.values())


def _looks_like_action_list(value: Any) -> bool:
    return isinstance(value, list) and any(_looks_like_action_entry(item) for item in value)


def _actions_from_container(container: dict[str, Any]) -> list[dict[str, Any]]:
    key = _key_by_alias(container, ACTION_LIST_ALIASES)
    if key is not None and _looks_like_action_list(container.get(key)):
        return [item for item in container[key] if isinstance(item, dict)]
    for value in container.values():
        if _looks_like_action_list(value):
            return [item for item in value if isinstance(item, dict)]
    return []


def _looks_like_street_collection(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_looks_like_action_list(v) or (isinstance(v, dict) and _actions_from_container(v)) for v in value.values())
    if isinstance(value, list):
        return any(isinstance(item, dict) and _actions_from_container(item) for item in value)
    return False


def _looks_like_hand_record(record: Any) -> bool:
    if not isinstance(record, dict):
        return False
    wrapper_keys = {_normalize_key(alias) for alias in WRAPPER_HAND_LIST_ALIASES}
    for key, value in record.items():
        if _looks_like_action_list(value):
            return True
        if _normalize_key(key) not in wrapper_keys and _looks_like_street_collection(value):
            return True
    return False


def _hand_records_from_list(items: list[Any]) -> list[dict[str, Any]]:
    dict_items = [item for item in items if isinstance(item, dict)]
    if any(_looks_like_hand_record(item) for item in dict_items):
        return dict_items
    for item in dict_items:
        wrapped = _find_wrapped_hand_records(item)
        if wrapped:
            return wrapped
    return []


def _find_wrapped_hand_records(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        return _hand_records_from_list(obj)
    if not isinstance(obj, dict):
        return []
    if _looks_like_hand_record(obj):
        return [obj]

    key = _key_by_alias(obj, WRAPPER_HAND_LIST_ALIASES)
    if key is not None:
        value = obj.get(key)
        if isinstance(value, list):
            records = _hand_records_from_list(value)
            if records:
                return records
        records = _find_wrapped_hand_records(value)
        if records:
            return records

    for value in obj.values():
        records = _find_wrapped_hand_records(value)
        if records:
            return records
    return []


def _schema_keys(records: list[dict[str, Any]]) -> dict[str, Any]:
    top = sorted({key for record in records if isinstance(record, dict) for key in record.keys()})
    action_keys: set[str] = set()
    for record in records:
        for entry, _ in _extract_action_entries(record):
            action_keys.update(entry.keys())
    return {"top_level_keys": top, "action_keys": sorted(action_keys)}


def _extract_action_entries(record: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    direct_key = _key_by_alias(record, ACTION_LIST_ALIASES)
    if direct_key is not None and _looks_like_action_list(record.get(direct_key)):
        return [(dict(entry), {}) for entry in record[direct_key] if isinstance(entry, dict)]
    for key, value in record.items():
        if _normalize_key(key) in {_normalize_key(alias) for alias in WRAPPER_HAND_LIST_ALIASES}:
            continue
        if _looks_like_action_list(value):
            return [(dict(entry), {}) for entry in value if isinstance(entry, dict)]

    street_value = _value_by_alias(record, STREET_LIST_ALIASES, None)
    if street_value is None:
        for value in record.values():
            if _looks_like_street_collection(value):
                street_value = value
                break
    return _flatten_street_actions(street_value)


def _flatten_street_actions(street_value: Any) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    flattened: list[tuple[dict[str, Any], dict[str, Any]]] = []
    if isinstance(street_value, dict):
        iterable = street_value.items()
    elif isinstance(street_value, list):
        iterable = enumerate(street_value)
    else:
        return flattened

    for key, container in iterable:
        parent: dict[str, Any] = {}
        if isinstance(container, dict):
            parent_street = _value_by_alias(container, STREET_NAME_ALIASES, key)
            parent["street"] = parent_street
            parent_board = _value_by_alias(container, ACTION_FIELD_ALIASES["board"], None)
            parent_texture = _value_by_alias(container, ACTION_FIELD_ALIASES["texture"], None)
            if parent_board is not None:
                parent["board"] = parent_board
            if parent_texture is not None:
                parent["texture"] = parent_texture
            entries = _actions_from_container(container)
        elif _looks_like_action_list(container):
            parent["street"] = key
            entries = [item for item in container if isinstance(item, dict)]
        else:
            continue
        for entry in entries:
            copied = dict(entry)
            if _key_by_alias(copied, ACTION_FIELD_ALIASES["street"]) is None:
                copied["_inferred_street"] = parent.get("street")
            if parent.get("board") is not None and _key_by_alias(copied, ACTION_FIELD_ALIASES["board"]) is None:
                copied["_inferred_board"] = parent["board"]
            if parent.get("texture") is not None and _key_by_alias(copied, ACTION_FIELD_ALIASES["texture"]) is None:
                copied["_inferred_texture"] = parent["texture"]
            flattened.append((copied, parent))
    return flattened


def _entry_value(entry: dict[str, Any], field: str, default: Any = None) -> Any:
    value = _value_by_alias(entry, ACTION_FIELD_ALIASES[field], None)
    if value is not None:
        return value
    inferred_key = f"_inferred_{field}"
    return entry.get(inferred_key, default)


def _detect_big_blind(record: dict[str, Any]) -> float:
    value = _value_by_alias(record, TOP_LEVEL_ALIASES["big_blind"], None)
    if value is None:
        blinds = _value_by_alias(record, ["blinds", "blind_structure", "blindStructure"], None)
        if isinstance(blinds, dict):
            value = _value_by_alias(blinds, TOP_LEVEL_ALIASES["big_blind"], None)
    parsed, rejected = _finite_float(value)
    if rejected or parsed is None or parsed <= 0:
        return 1.0
    return parsed


def _entry_amount(entry: dict[str, Any], big_blind: float, failures: Counter) -> float | None:
    amount, rejected = _finite_float(_entry_value(entry, "amount", None))
    if rejected:
        failures["nonfinite_amounts_rejected"] += 1
    if amount is not None:
        return amount
    amount_bb, rejected_bb = _finite_float(_entry_value(entry, "amount_bb", None))
    if rejected_bb:
        failures["nonfinite_amounts_rejected"] += 1
    if amount_bb is None:
        return None
    return amount_bb * big_blind


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    norm = _normalize_key(value)
    if norm in {"true", "t", "yes", "y", "1"}:
        return True
    if norm in {"false", "f", "no", "n", "0"}:
        return False
    return None


def _entry_context_flags(entry: dict[str, Any]) -> tuple[bool | None, bool]:
    explicit_can_check = _bool_or_none(_entry_value(entry, "can_check", None))
    explicit_facing = _bool_or_none(_entry_value(entry, "facing_bet", None))
    to_call, _ = _finite_float(_entry_value(entry, "to_call", None))
    if explicit_can_check is None and to_call is not None:
        explicit_can_check = to_call <= 0.0
    facing_bet = bool(explicit_facing) or (to_call is not None and to_call > 0.0) or explicit_can_check is False
    return explicit_can_check, facing_bet


def _card_tokens(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [rank.upper() + suit.lower() for rank, suit in CARD_RE.findall(value)]
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            if isinstance(item, str):
                match = CARD_RE.search(item)
                if match:
                    out.append(match.group(1).upper() + match.group(2).lower())
            elif isinstance(item, dict):
                rank = _value_by_alias(item, ["rank", "r"], None)
                suit = _value_by_alias(item, ["suit", "s"], None)
                if rank is not None and suit is not None:
                    token = str(rank).upper()[:1] + str(suit).lower()[:1]
                    if CARD_RE.fullmatch(token):
                        out.append(token)
        return out
    return []


def _canonical_texture(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    text = re.sub(r"_+", "_", text)
    if "flush_draw" in text or "flushdraw" in text or text.startswith("wet"):
        prefix = re.match(r"^(\d+card)_", text)
        return f"{prefix.group(1)}_wet_flush_draw" if prefix else "wet_flush_draw"
    return text


def _board_texture_bucket(entry: dict[str, Any], record: dict[str, Any]) -> str:
    explicit = _canonical_texture(_entry_value(entry, "texture", None))
    if explicit:
        return explicit
    board = _entry_value(entry, "board", None)
    if board is None:
        board = _value_by_alias(record, ACTION_FIELD_ALIASES["board"], None)
    cards = _card_tokens(board)
    if len(cards) < 3:
        return "unknown"
    ranks = [card[0] for card in cards]
    suits = [card[1] for card in cards]
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)
    paired = max(rank_counts.values()) >= 2
    max_suit = max(suit_counts.values()) if suit_counts else 0
    vals = sorted(RANK_ORDER.get(rank, 0) for rank in ranks)
    connected = len(vals) >= 3 and vals[-1] - vals[0] <= 5
    pair_tag = "paired" if paired else "unpaired"
    if not paired and len(cards) >= 4 and max_suit >= 3:
        return f"{len(cards)}card_wet_flush_draw"
    if max_suit == len(cards):
        suit_tag = "monotone"
    elif max_suit >= 2:
        suit_tag = "two_tone"
    else:
        suit_tag = "rainbow"
    speed = "connected" if connected else "static"
    return f"{len(cards)}card_{pair_tag}_{suit_tag}_{speed}"


def _texture_category(bucket: str) -> str:
    text = bucket.lower()
    if "wet_flush_draw" in text or "flush_draw" in text:
        return "wet_flush_draw"
    text = re.sub(r"^\d+card_", "", text)
    if "paired" in text and "two_tone" in text and "static" in text and "unpaired" not in text:
        return "paired_two_tone_static"
    if "unpaired" in text and "two_tone" in text and "static" in text:
        return "unpaired_two_tone_static"
    return text


def _position_for_entry(entry: dict[str, Any]) -> str:
    explicit = _canonical_position(_entry_value(entry, "position", None))
    if explicit:
        return explicit
    actor = _entry_value(entry, "actor", None)
    if isinstance(actor, int):
        return f"seat_{actor}"
    if isinstance(actor, str) and actor.isdigit():
        return f"seat_{actor}"
    return "unknown"


def _delta_from_mapping(mapping: Any, actor: Any) -> float | None:
    if not isinstance(mapping, dict):
        return None
    keys = [actor, str(actor)] if actor is not None else []
    for key in keys:
        if key in mapping:
            value, _ = _finite_float(mapping[key])
            if value is not None:
                return value
    return None


def _extract_delta(entry: dict[str, Any], record: dict[str, Any], actor: Any) -> float | None:
    for mapping_source in (entry, record):
        for alias in DELTA_MAP_ALIASES:
            value = _value_by_alias(mapping_source, [alias], None)
            delta = _delta_from_mapping(value, actor)
            if delta is not None:
                return delta
        for alias in DELTA_VALUE_ALIASES:
            value = _value_by_alias(mapping_source, [alias], None)
            if isinstance(value, dict):
                delta = _delta_from_mapping(value, actor)
                if delta is not None:
                    return delta
            parsed, rejected = _finite_float(value)
            if parsed is not None and not rejected:
                return parsed
    return None


def _new_frequency_bucket() -> dict[str, int]:
    return {"total": 0, "raise": 0, "all_in": 0, "fold": 0, "call": 0}


def _add_example(bucket: dict[str, Any], parsed: dict[str, Any]) -> None:
    examples = bucket.setdefault("examples", [])
    if len(examples) >= 5:
        return
    examples.append({
        "hand_id": parsed.get("hand_id"),
        "actor": parsed.get("actor"),
        "street": parsed.get("street"),
        "position": parsed.get("position"),
        "action": parsed.get("action"),
        "board_texture_bucket": parsed.get("board_texture_bucket"),
        "amount": parsed.get("amount"),
        "chip_delta": parsed.get("chip_delta"),
    })


def _record_fingerprint(fingerprints: dict[str, dict[str, Any]], name: str, parsed: dict[str, Any]) -> None:
    bucket = fingerprints.setdefault(name, {"count": 0, "examples": []})
    bucket["count"] += 1
    _add_example(bucket, parsed)


def analyze_path(path: Path | str, top_n: int = 20) -> dict[str, Any]:
    input_path = Path(path)
    pairs = list(_walk_records_with_source(input_path))
    records = [record for _, record in pairs]
    sources = [source for source, _ in pairs]
    failures: Counter = Counter()
    source_quality: dict[str, Counter] = defaultdict(Counter)
    schema = _schema_keys(records)

    cluster_counts: Counter = Counter()
    cluster_details: dict[str, dict[str, Any]] = {}
    cluster_impacts: dict[str, dict[str, Any]] = defaultdict(lambda: {"chip_impact": 0.0, "impact_records": 0, "examples": []})
    river_can_check = defaultdict(_new_frequency_bucket)
    river_facing = defaultdict(_new_frequency_bucket)
    fingerprints: dict[str, dict[str, Any]] = {}
    parsed_by_hand: dict[str, list[dict[str, Any]]] = defaultdict(list)

    records_successfully_parsed = 0
    postflop_records = 0
    river_records = 0
    amount_records = 0
    outcome_records = 0

    for record, source in zip(records, sources):
        if not isinstance(record, dict):
            failures["non_dict_records"] += 1
            continue
        entries = _extract_action_entries(record)
        if not entries:
            failures["records_without_actions"] += 1
            source_quality[source]["records_without_actions"] += 1
            continue
        big_blind = _detect_big_blind(record)
        parsed_any = False
        hand_id = (
            _value_by_alias(record, ["hand_id", "handId", "id", "match_hand_id", "matchHandId"], None)
            or f"{source}#{len(parsed_by_hand)}"
        )
        for entry, _parent in entries:
            raw_action = _entry_value(entry, "action", None)
            to_call = _entry_value(entry, "to_call", None)
            action = _canonical_action(raw_action, to_call)
            if raw_action is None:
                failures["action_entries_missing_action"] += 1
                continue
            if action == "unknown":
                failures["action_entries_unknown_action"] += 1
                source_quality[source]["unknown_action_entries"] += 1
                continue
            street = _canonical_street(_entry_value(entry, "street", "preflop"))
            actor = _entry_value(entry, "actor", None)
            amount = _entry_amount(entry, big_blind, failures)
            if amount is not None:
                amount_records += 1
            can_check, facing_bet = _entry_context_flags(entry)
            texture_bucket = _board_texture_bucket(entry, record)
            category = _texture_category(texture_bucket)
            position = _position_for_entry(entry)
            chip_delta = _extract_delta(entry, record, actor)
            if chip_delta is not None:
                outcome_records += 1
            parsed = {
                "hand_id": hand_id,
                "actor": actor,
                "street": street,
                "position": position,
                "action": action,
                "amount": amount,
                "can_check": can_check,
                "facing_bet": facing_bet,
                "board_texture_bucket": texture_bucket,
                "board_texture_category": category,
                "chip_delta": chip_delta,
            }
            parsed_by_hand[str(hand_id)].append(parsed)
            parsed_any = True

            if street == "preflop" and facing_bet and action in {"fold", "all_in"} and (chip_delta is None or chip_delta < 0):
                _record_fingerprint(fingerprints, "mehedi_preflop_pressure_early_bust_like", parsed)

            if street not in POSTFLOP_STREETS:
                continue
            postflop_records += 1
            if street == "river":
                river_records += 1
            cluster_key = f"{street}__{position}__{action}__{texture_bucket}"
            cluster_counts[cluster_key] += 1
            cluster_details[cluster_key] = {
                "cluster_key": cluster_key,
                "street": street,
                "position": position,
                "hero_action": action,
                "board_texture_bucket": texture_bucket,
                "board_texture_category": category,
            }
            if chip_delta is not None:
                impact = cluster_impacts[cluster_key]
                impact["chip_impact"] += chip_delta
                impact["impact_records"] += 1
                _add_example(impact, parsed)

            if street == "river" and can_check is True and category in {
                "unpaired_two_tone_static",
                "wet_flush_draw",
                "paired_two_tone_static",
            }:
                bucket = river_can_check[category]
                bucket["total"] += 1
                if action in {"raise", "all_in"}:
                    bucket[action] += 1
                    _record_fingerprint(fingerprints, f"toby_river_can_check_{category}_raise_like", parsed)

            if street == "river" and facing_bet and category in {
                "paired_two_tone_static",
                "unpaired_two_tone_static",
            }:
                bucket = river_facing[category]
                bucket["total"] += 1
                if action in {"fold", "call"}:
                    bucket[action] += 1
                if action == "fold" and category == "paired_two_tone_static":
                    _record_fingerprint(fingerprints, "toby_paired_board_river_facing_bet_fold_like", parsed)

        if parsed_any:
            records_successfully_parsed += 1

    for hand_actions in parsed_by_hand.values():
        by_actor: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for parsed in hand_actions:
            by_actor[parsed["actor"]].append(parsed)
        for actor_actions in by_actor.values():
            has_flop_raise = any(a["street"] == "flop" and a["action"] in {"raise", "all_in"} for a in actor_actions)
            has_turn_raise = any(a["street"] == "turn" and a["action"] in {"raise", "all_in"} for a in actor_actions)
            for action in actor_actions:
                if (
                    has_flop_raise
                    and has_turn_raise
                    and action["street"] == "river"
                    and action["action"] == "fold"
                    and action["facing_bet"]
                    and action["board_texture_category"] in {"paired_two_tone_static", "unpaired_two_tone_static"}
                ):
                    _record_fingerprint(fingerprints, "postflop_barrel_then_river_trap_fold_like", action)

    def render_frequency(bucket: dict[str, int]) -> dict[str, Any]:
        total = int(bucket["total"])
        raises = int(bucket["raise"] + bucket["all_in"])
        return {
            "total": total,
            "raise": raises,
            "fold": int(bucket["fold"]),
            "call": int(bucket["call"]),
            "raise_frequency": raises / total if total else 0.0,
            "fold_frequency": int(bucket["fold"]) / total if total else 0.0,
            "call_frequency": int(bucket["call"]) / total if total else 0.0,
        }

    total_postflop = max(postflop_records, 1)
    top_by_frequency = []
    for key, count in cluster_counts.most_common(top_n):
        item = dict(cluster_details[key])
        item["count"] = int(count)
        item["share_of_postflop_actions"] = count / total_postflop
        top_by_frequency.append(item)

    top_by_impact = []
    for key, impact in cluster_impacts.items():
        item = dict(cluster_details[key])
        item.update({
            "chip_impact": impact["chip_impact"],
            "impact_records": impact["impact_records"],
            "average_chip_impact": impact["chip_impact"] / impact["impact_records"] if impact["impact_records"] else 0.0,
            "examples": impact["examples"],
        })
        top_by_impact.append(item)
    top_by_impact.sort(key=lambda item: abs(item["chip_impact"]), reverse=True)

    parse_quality = {
        "failures": dict(sorted(failures.items())),
        "schema_keys": schema,
        "source_quality": {source: dict(counter) for source, counter in sorted(source_quality.items())},
    }
    return {
        "input": str(input_path),
        "total_records_found": len(records),
        "records_successfully_parsed": records_successfully_parsed,
        "postflop_action_records": postflop_records,
        "river_action_records": river_records,
        "amount_records_parsed": amount_records,
        "chip_impact_records": outcome_records,
        "top_clusters_by_frequency": top_by_frequency,
        "top_clusters_by_chip_impact": top_by_impact[:top_n],
        "chip_impact_available": bool(top_by_impact),
        "river_can_check_raise_frequency": {
            "unpaired_two_tone_static": render_frequency(river_can_check["unpaired_two_tone_static"]),
            "wet_flush_draw": render_frequency(river_can_check["wet_flush_draw"]),
            "paired_two_tone_static": render_frequency(river_can_check["paired_two_tone_static"]),
        },
        "river_facing_bet_fold_call_frequency": {
            "paired_two_tone_static": render_frequency(river_facing["paired_two_tone_static"]),
            "unpaired_two_tone_static": render_frequency(river_facing["unpaired_two_tone_static"]),
        },
        "action_sequence_fingerprints": dict(sorted(fingerprints.items())),
        "parse_quality": parse_quality,
    }


def render_text_report(result: dict[str, Any]) -> str:
    lines = [
        "# Postflop Trap Prevalence Report",
        "",
        f"Input: {result['input']}",
        f"Total records found: {result['total_records_found']}",
        f"Records successfully parsed: {result['records_successfully_parsed']}",
        f"Postflop action records parsed: {result['postflop_action_records']}",
        f"River action records parsed: {result['river_action_records']}",
        f"Chip impact available: {result['chip_impact_available']}",
        "",
        "## River can_check raise frequency",
    ]
    for name, data in result["river_can_check_raise_frequency"].items():
        lines.append(f"- {name}: {data['raise']}/{data['total']} = {data['raise_frequency']:.3f}")
    lines.extend(["", "## River facing-bet fold/call frequency"])
    for name, data in result["river_facing_bet_fold_call_frequency"].items():
        lines.append(
            f"- {name}: fold {data['fold']}/{data['total']} = {data['fold_frequency']:.3f}; "
            f"call {data['call']}/{data['total']} = {data['call_frequency']:.3f}"
        )
    lines.extend(["", "## Top clusters by frequency"])
    for item in result["top_clusters_by_frequency"][:10]:
        lines.append(
            f"- {item['cluster_key']}: count={item['count']} "
            f"share={item['share_of_postflop_actions']:.3f}"
        )
    lines.extend(["", "## Top clusters by chip impact"])
    if result["top_clusters_by_chip_impact"]:
        for item in result["top_clusters_by_chip_impact"][:10]:
            lines.append(
                f"- {item['cluster_key']}: chip_impact={item['chip_impact']:.1f} "
                f"records={item['impact_records']}"
            )
    else:
        lines.append("- no hand-outcome chip deltas found")
    lines.extend(["", "## Toby/Mehedi-like fingerprints"])
    if result["action_sequence_fingerprints"]:
        for name, data in result["action_sequence_fingerprints"].items():
            lines.append(f"- {name}: count={data['count']}")
    else:
        lines.append("- none")
    failures = result["parse_quality"]["failures"]
    lines.extend(["", "## Parse quality", f"Failures: {json.dumps(failures, sort_keys=True)}"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "--in", dest="input", required=True, help="History file or directory")
    parser.add_argument("--json-out", default=None, help="Optional path for machine-readable JSON")
    parser.add_argument("--report", default=None, help="Optional path for text report")
    parser.add_argument("--top-n", type=int, default=20)
    args = parser.parse_args(argv)

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"FAIL: input not found: {input_path}", file=sys.stderr)
        return 2
    result = analyze_path(input_path, top_n=args.top_n)
    text = render_text_report(result)
    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
