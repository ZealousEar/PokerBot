#!/usr/bin/env python3
"""Recompute Thorp's committing-street bust split from raw finals-recon replays.

This is an independent forensic helper for the 2026-06-07 bust-split
resolution. It intentionally reads only raw replay JSON and classifies each
clean Thorp bust by the street of Thorp's last non-blind chip commitment.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = ROOT / "consult" / "artifacts" / "2026-06-04-finals-recon" / "raw" / "hands"
DEFAULT_JSON_OUT = ROOT / "consult" / "artifacts" / "2026-06-07-overfold-probe" / "bust_split_recomputed.json"
THORP_ID = "7a7ad230-2b19-46ff-af11-5df254b6f078"
STREETS = ("preflop", "flop", "turn", "river")
BLIND_ACTIONS = {"small_blind", "big_blind"}
BLIND_AMOUNTS = {"small_blind": 50, "big_blind": 100}
COMMIT_ACTIONS = {"call", "raise", "all_in"}
POSITIVE_ACTIONS = BLIND_ACTIONS | COMMIT_ACTIONS


def int_or_none(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def thorp_entries(seats: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [seat for seat in seats if seat.get("bot_id") == THORP_ID]


def is_clean_thorp_match(seats: List[Dict[str, Any]]) -> Tuple[bool, str]:
    entries = thorp_entries(seats)
    if len(seats) != 6:
        return False, f"len(seats)={len(seats)}"
    if len(entries) != 1:
        return False, f"thorp_entries={len(entries)}"
    thorp_seat = entries[0].get("seat")
    seat_counts = Counter(seat.get("seat") for seat in seats)
    if seat_counts[thorp_seat] != 1:
        return False, f"thorp_seat_collision={thorp_seat}"
    return True, "clean_6max_unique_thorp_seat"


def action_seats(action_log: Iterable[Dict[str, Any]]) -> set[int]:
    seats: set[int] = set()
    for event in action_log:
        seat = int_or_none(event.get("seat"))
        if seat is not None:
            seats.add(seat)
    return seats


def round_closed(active: set[int], all_in: set[int], street_bets: Dict[int, int], current_bet: int, acted: set[int]) -> bool:
    if len(active) <= 1:
        return False
    eligible = active - all_in
    if not eligible:
        return False
    matched = all(street_bets.get(seat, 0) == current_bet for seat in eligible)
    everyone_acted = eligible.issubset(acted)
    return matched and everyone_acted


def increment_for_event(action: str, amount: int, seat: int, street_bets: Dict[int, int]) -> int:
    if action in {"fold", "check"}:
        return 0
    if action in BLIND_ACTIONS or action in {"call", "all_in"}:
        return max(0, amount)
    if action == "raise":
        return max(0, amount - street_bets.get(seat, 0))
    return 0


def assign_action_streets(action_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Assign a betting street to every action-log row.

    Raw replay action rows do not carry street names. This follows the report's
    stated convention: blinds are posted amounts; raise amount is total-to for
    the current street; call/all_in amount is an increment; street bets reset
    after all live non-all-in players have matched and acted.
    """
    active = action_seats(action_log)
    all_in: set[int] = set()
    street_bets: Dict[int, int] = defaultdict(int)
    current_bet = 0
    acted: set[int] = set()
    street_idx = 0
    assigned: List[Dict[str, Any]] = []

    for index, event in enumerate(action_log):
        seat = int_or_none(event.get("seat"))
        action = str(event.get("action") or "").lower()
        amount = int_or_none(event.get("amount")) or 0
        street = STREETS[min(street_idx, len(STREETS) - 1)]
        increment = increment_for_event(action, amount, seat if seat is not None else -1, street_bets)

        assigned.append(
            {
                "index": index,
                "seat": seat,
                "action": action,
                "amount": amount,
                "street": street,
                "increment": increment,
                "street_bet_before": street_bets.get(seat, 0) if seat is not None else 0,
            }
        )

        if seat is None:
            continue

        if action in BLIND_ACTIONS:
            street_bets[seat] += increment
            current_bet = max(current_bet, street_bets[seat])
            # The engine caps blinds at the player's remaining stack but still
            # logs them as blind posts. A below-nominal blind is therefore an
            # all-in blind and must not block betting-round closure.
            nominal = BLIND_AMOUNTS[action]
            if 0 <= amount < nominal:
                all_in.add(seat)
            continue

        if action == "fold":
            active.discard(seat)
            acted.add(seat)
        elif action == "check":
            acted.add(seat)
        elif action == "call":
            street_bets[seat] += increment
            acted.add(seat)
        elif action == "raise":
            previous_total = street_bets.get(seat, 0)
            street_bets[seat] = max(previous_total, amount)
            if street_bets[seat] > current_bet:
                current_bet = street_bets[seat]
                acted = {seat}
            else:
                acted.add(seat)
        elif action == "all_in":
            street_bets[seat] += increment
            all_in.add(seat)
            if street_bets[seat] > current_bet:
                current_bet = street_bets[seat]
                acted = {seat}
            else:
                acted.add(seat)
        else:
            acted.add(seat)

        if len(active) <= 1:
            continue
        if not (active - all_in):
            continue
        if round_closed(active, all_in, street_bets, current_bet, acted):
            street_idx = min(street_idx + 1, len(STREETS) - 1)
            street_bets = defaultdict(int)
            current_bet = 0
            acted = set()

    return assigned


def last_positive_thorp_action(match: Dict[str, Any], thorp_seat: int, actions: set[str]) -> Optional[Dict[str, Any]]:
    last: Optional[Dict[str, Any]] = None
    for hand in match.get("hands") or []:
        hand_num = int_or_none(hand.get("hand_num"))
        board = hand.get("community_cards") or []
        assigned = assign_action_streets(hand.get("action_log") or [])
        for event in assigned:
            if event.get("seat") != thorp_seat:
                continue
            if event.get("action") not in actions:
                continue
            if int(event.get("increment") or 0) <= 0:
                continue
            last = {
                "hand_num": hand_num,
                "hand_final_street": hand.get("street"),
                "board_cards": board,
                "action_index": event["index"],
                "action": event["action"],
                "amount": event["amount"],
                "increment": event["increment"],
                "committing_street": event["street"],
            }
    return last


def analyze(raw_dir: Path) -> Dict[str, Any]:
    paths = sorted(raw_dir.glob("*.json"))
    thorp_files: List[Dict[str, Any]] = []
    nonclean: List[Dict[str, Any]] = []
    clean_busts: List[Dict[str, Any]] = []
    clean_non_busts = 0
    total_thorp_bust_entries = 0
    excluded_bust_entries = 0

    for path in paths:
        match = load_json(path)
        seats = match.get("seats") or []
        entries = thorp_entries(seats)
        if not entries:
            continue

        clean, clean_reason = is_clean_thorp_match(seats)
        thorp_file_row = {
            "file": path.name,
            "match_id": match.get("match_id"),
            "seat_count": len(seats),
            "thorp_seats": [entry.get("seat") for entry in entries],
            "thorp_final_stacks": [entry.get("final_stack") for entry in entries],
            "clean": clean,
            "clean_reason": clean_reason,
            "hand_count": len(match.get("hands") or []),
        }
        thorp_files.append(thorp_file_row)

        bust_entries = [entry for entry in entries if int_or_none(entry.get("final_stack")) == 0]
        total_thorp_bust_entries += len(bust_entries)

        if not clean:
            excluded_bust_entries += len(bust_entries)
            nonclean.append(thorp_file_row)
            continue

        entry = entries[0]
        thorp_seat = int_or_none(entry.get("seat"))
        if thorp_seat is None:
            nonclean.append({**thorp_file_row, "clean": False, "clean_reason": "missing_thorp_seat"})
            continue

        if int_or_none(entry.get("final_stack")) != 0:
            clean_non_busts += 1
            continue

        last = last_positive_thorp_action(match, thorp_seat, COMMIT_ACTIONS)
        literal_last = last_positive_thorp_action(match, thorp_seat, POSITIVE_ACTIONS)
        clean_busts.append(
            {
                "file": path.name,
                "match_id": match.get("match_id"),
                "thorp_seat": thorp_seat,
                "final_stack": entry.get("final_stack"),
                "chip_delta": entry.get("chip_delta"),
                "hand_count": len(match.get("hands") or []),
                "last_positive_action": last,
                "literal_last_positive_action_including_blinds": literal_last,
                "blind_tail_after_commitment": bool(
                    literal_last
                    and last
                    and literal_last.get("action") in BLIND_ACTIONS
                    and literal_last.get("hand_num") != last.get("hand_num")
                ),
                "committing_street": last.get("committing_street") if last else "unknown",
            }
        )

    street_counts = Counter(row["committing_street"] for row in clean_busts)
    preflop = street_counts.get("preflop", 0)
    postflop = sum(street_counts.get(street, 0) for street in ("flop", "turn", "river"))
    clean_bust_count = len(clean_busts)

    blind_tail_count = sum(1 for row in clean_busts if row.get("blind_tail_after_commitment"))

    result = {
        "raw_dir": str(raw_dir),
        "raw_file_count": len(paths),
        "thorp_match_files": len(thorp_files),
        "clean_thorp_matches": sum(1 for row in thorp_files if row["clean"]),
        "clean_thorp_non_bust_matches": clean_non_busts,
        "nonclean_thorp_matches": nonclean,
        "total_thorp_bust_seat_entries": total_thorp_bust_entries,
        "excluded_nonclean_bust_entries": excluded_bust_entries,
        "clean_busts": clean_bust_count,
        "street_counts": dict(sorted(street_counts.items())),
        "preflop_count": preflop,
        "postflop_count": postflop,
        "preflop_percent": round(100.0 * preflop / clean_bust_count, 2) if clean_bust_count else None,
        "postflop_percent": round(100.0 * postflop / clean_bust_count, 2) if clean_bust_count else None,
        "postflop_breakdown": {street: street_counts.get(street, 0) for street in ("flop", "turn", "river")},
        "blind_tail_after_commitment_count": blind_tail_count,
        "clean_bust_rows": clean_busts,
    }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="Directory containing raw match JSON files")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT, help="Path to write full recomputation JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = analyze(args.raw_dir)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "raw_file_count": result["raw_file_count"],
        "thorp_match_files": result["thorp_match_files"],
        "clean_thorp_matches": result["clean_thorp_matches"],
        "total_thorp_bust_seat_entries": result["total_thorp_bust_seat_entries"],
        "excluded_nonclean_bust_entries": result["excluded_nonclean_bust_entries"],
        "clean_busts": result["clean_busts"],
        "street_counts": result["street_counts"],
        "preflop_count": result["preflop_count"],
        "postflop_count": result["postflop_count"],
        "preflop_percent": result["preflop_percent"],
        "postflop_percent": result["postflop_percent"],
        "blind_tail_after_commitment_count": result["blind_tail_after_commitment_count"],
        "json_out": str(args.json_out),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
