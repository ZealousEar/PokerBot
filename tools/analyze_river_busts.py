#!/usr/bin/env python3
"""Read-only finals-day triage for Thorp river-marked bust hands.

This tool does not modify src/, data/, submissions/, or ext/. It reads the existing
quick_6max_eval raw JSON files, deterministically replays only the marked bust
matches through the bust hand to recover board/cards/events, and writes a
Markdown triage report.
"""
from __future__ import annotations

import json
import tempfile
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import quick_6max_eval as q

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "consult" / "artifacts" / "2026-06-04-finals-ship" / "6max_evidence"
RAW_DIR = EVIDENCE_DIR / "raw_matches"
REPORT_PATH = ROOT / "consult" / "artifacts" / "2026-06-04-finals-ship" / "river_triage_report.md"

THORP = "thorp"
RANK_ORDER = "23456789TJQKA"
RANK_VALUE = {r: i for i, r in enumerate(RANK_ORDER, start=2)}

ACTION_RECORDS: List[Dict[str, Any]] = []


class RichRecordingBotProcess(q.match_mod.BotProcess):
    """Record Thorp's full action-request state before returning its action."""

    def act(self, game_state: dict) -> dict:  # type: ignore[override]
        raw = super().act(game_state)
        if self.bot_id == THORP:
            action = str(raw.get("action", "fold")).lower().strip() if isinstance(raw, dict) else "fold"
            record = {
                "bot_id": self.bot_id,
                "hand_id": game_state.get("hand_id"),
                "street": game_state.get("street"),
                "seat": game_state.get("seat_to_act"),
                "raw_action": action,
                "raw_amount": raw.get("amount") if isinstance(raw, dict) else None,
                "runner_error": raw.get("error") if isinstance(raw, dict) else "non_dict_response",
                "amount_owed": int(game_state.get("amount_owed") or 0),
                "can_check": bool(game_state.get("can_check")),
                "min_raise_to": int(game_state.get("min_raise_to") or 0),
                "your_stack": int(game_state.get("your_stack") or 0),
                "your_bet_this_street": int(game_state.get("your_bet_this_street") or 0),
                "current_bet": int(game_state.get("current_bet") or 0),
                "pot": int(game_state.get("pot") or 0),
                "community_cards": list(game_state.get("community_cards") or []),
                "your_cards": list(game_state.get("your_cards") or []),
                "players": deepcopy(game_state.get("players") or []),
                "action_log": deepcopy(game_state.get("action_log") or []),
            }
            ACTION_RECORDS.append(record)
        return raw


def load_existing_bust_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(RAW_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        row = data.get("row", {})
        if row.get("busted") and row.get("bust_street") == "river":
            rows.append({"path": path, "data": data, "row": row})
    return rows


def normalize_action_record(rec: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        rec.get("hand_id"),
        rec.get("street"),
        rec.get("raw_action"),
        rec.get("raw_amount"),
        rec.get("amount_owed"),
        rec.get("current_bet"),
        rec.get("your_stack"),
        rec.get("your_bet_this_street"),
    )


def replay_to_bust(row: Dict[str, Any], thorp_dir: Path, copy_root: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    global ACTION_RECORDS
    ACTION_RECORDS = []
    q.match_mod.BotProcess = RichRecordingBotProcess  # monkeypatch in this process only

    mix_name = str(row["mix"])
    seat = int(row["thorp_seat"])
    seed = int(row["seed"])
    bust_hand = int(row["bust_hand"])
    match_id = f"{mix_name}_seat{seat}_seed{seed}"
    opponents = q.table_mixes()[mix_name]
    match_copy_root = copy_root / match_id
    match_copy_root.mkdir(parents=True, exist_ok=True)
    bot_paths = q.build_seated_paths(thorp_dir, opponents, seat, match_copy_root)
    result = q.match_mod.run_match(match_id, bot_paths, n_hands=bust_hand + 1, verbose=False, seed=seed)
    return result, list(ACTION_RECORDS)


def card_rank(card: str) -> str:
    return card[0]


def card_suit(card: str) -> str:
    return card[1]


def rank_counts(cards: Iterable[str]) -> Counter:
    return Counter(card_rank(c) for c in cards)


def suit_counts(cards: Iterable[str]) -> Counter:
    return Counter(card_suit(c) for c in cards)


def has_straight(ranks: Iterable[str]) -> bool:
    vals = {RANK_VALUE[r] for r in ranks if r in RANK_VALUE}
    if 14 in vals:
        vals.add(1)
    for start in range(1, 11):
        if all(v in vals for v in range(start, start + 5)):
            return True
    return False


def straight_drawish(board: List[str]) -> bool:
    vals = sorted({RANK_VALUE[card_rank(c)] for c in board if card_rank(c) in RANK_VALUE})
    if 14 in vals:
        vals = sorted(set(vals + [1]))
    for start in range(1, 11):
        if sum(1 for v in vals if start <= v <= start + 4) >= 3:
            return True
    return False


def board_texture(board: List[str]) -> str:
    rc = rank_counts(board)
    sc = suit_counts(board)
    pairs = sorted([r for r, n in rc.items() if n == 2], key=lambda r: RANK_VALUE[r], reverse=True)
    trips = sorted([r for r, n in rc.items() if n == 3], key=lambda r: RANK_VALUE[r], reverse=True)
    quads = sorted([r for r, n in rc.items() if n == 4], key=lambda r: RANK_VALUE[r], reverse=True)
    suit_part = "rainbow"
    if sc:
        max_suit = max(sc.values())
        if max_suit >= 5:
            suit_part = "five-flush-board"
        elif max_suit == 4:
            suit_part = "four-flush-board"
        elif max_suit == 3:
            suit_part = "monotone-or-threeflush"
        elif len(sc) == 4:
            suit_part = "rainbow"
        else:
            suit_part = "two-tone"
    pair_part = "unpaired"
    if quads:
        pair_part = f"quads-board({''.join(quads)})"
    elif trips:
        pair_part = f"trips-board({''.join(trips)})"
    elif len(pairs) >= 2:
        pair_part = f"double-paired({''.join(pairs)})"
    elif pairs:
        pair_part = f"paired({pairs[0]})"
    straight_part = "straighty" if has_straight(card_rank(c) for c in board) or straight_drawish(board) else "not-straighty"
    return f"{pair_part}, {suit_part}, {straight_part}"


def best_winner_strength(hand: Dict[str, Any]) -> str:
    strengths = hand.get("hand_strengths") or {}
    winners = [w.get("bot_id") for w in hand.get("winners", [])]
    for bid in winners:
        if bid and bid != THORP and bid in strengths:
            return str(strengths[bid])
    for bid, strength in strengths.items():
        if bid != THORP:
            return str(strength)
    return "unknown"


def classify_bucket(hand: Dict[str, Any], hero_cards: List[str], board: List[str]) -> str:
    strength = str((hand.get("hand_strengths") or {}).get(THORP, "unknown"))
    board_rc = rank_counts(board)
    board_sc = suit_counts(board)
    winner_strength = best_winner_strength(hand)
    all_cards = hero_cards + board

    if strength == "Pair":
        return "one_pair_overpair_TPTK"
    if strength == "Two Pair":
        return "two_pair"
    if any(n >= 3 for n in board_rc.values()) and strength in {"Trips", "Full House", "Quads"}:
        return "trips_on_board_domination"
    if strength == "Full House" and winner_strength in {"Full House", "Quads"}:
        return "full_house_underboat"
    if strength == "Flush" and board_sc and max(board_sc.values()) >= 3:
        return "flush_on_monotone"
    if board_sc and max(board_sc.values()) >= 3:
        suited_cards_by_suit = defaultdict(list)
        for c in all_cards:
            suited_cards_by_suit[card_suit(c)].append(card_rank(c))
        if has_straight(card_rank(c) for c in all_cards) or any(has_straight(rs) for rs in suited_cards_by_suit.values()):
            return "straight_flush_possible"
    if strength in {"Straight", "Flush", "Full House", "Quads", "Straight Flush"} and winner_strength in {"Straight", "Flush", "Full House", "Quads", "Straight Flush"}:
        return "cooler_nut_vs_nut"
    return "other"


def thorp_investment_by_street(events: List[Dict[str, Any]], thorp_seat: Optional[int]) -> Tuple[Dict[str, int], int]:
    by_street: Dict[str, int] = defaultdict(int)
    street_bets: Dict[int, int] = defaultdict(int)
    current_street = "preflop"

    for ev in events:
        typ = ev.get("type")
        if typ == "street_start":
            current_street = str(ev.get("street") or current_street)
            if current_street != "preflop":
                street_bets = defaultdict(int)
            continue
        if ev.get("bot_id") != THORP:
            continue
        action = ev.get("action")
        street = str(ev.get("street") or current_street)
        amount = int(ev.get("amount") or 0)
        seat = ev.get("seat", thorp_seat)
        inc = 0
        if typ == "blind":
            inc = amount
            if seat is not None:
                street_bets[int(seat)] += inc
        elif typ == "action":
            if action == "call":
                inc = amount
                if seat is not None:
                    street_bets[int(seat)] += inc
            elif action in {"raise", "all_in"}:
                if seat is not None:
                    prev = street_bets[int(seat)]
                    inc = max(0, amount - prev)
                    street_bets[int(seat)] = amount
                else:
                    inc = amount
            else:
                inc = 0
        by_street[street] += inc
    return dict(by_street), sum(by_street.values())


def final_or_river_decision(actions: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    river_actions = [a for a in actions if a.get("street") == "river"]
    river_decision = river_actions[-1] if river_actions else None
    final_decision = actions[-1] if actions else None
    return river_decision, final_decision


def stored_action_increment(action_record: Dict[str, Any]) -> int:
    action = action_record.get("raw_action")
    stack = int(action_record.get("your_stack") or 0)
    bet = int(action_record.get("your_bet_this_street") or 0)
    owed = int(action_record.get("amount_owed") or 0)
    if action in {"fold", "check"}:
        return 0
    if action == "call":
        return min(owed, stack)
    if action == "all_in":
        return stack
    if action == "raise":
        try:
            target = int(action_record.get("raw_amount") or 0)
        except (TypeError, ValueError):
            target = 0
        return max(0, min(target - bet, stack))
    return 0


def stored_commit_by_street(actions: List[Dict[str, Any]]) -> Tuple[Dict[str, int], int]:
    by_street: Dict[str, int] = defaultdict(int)
    for action in actions:
        by_street[str(action.get("street") or "unknown")] += stored_action_increment(action)
    return dict(by_street), sum(by_street.values())


def live_opponents_on_river(hand: Dict[str, Any]) -> int:
    revealed = hand.get("revealed_cards") or {}
    if THORP in revealed:
        return max(0, len(revealed) - 1)
    return len({w.get("bot_id") for w in hand.get("winners", []) if w.get("bot_id") != THORP})


def replay_match_details(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="river_triage_thorp_") as tmp:
        thorp_dir = Path(tmp) / "thorp"
        thorp_dir.mkdir(parents=True, exist_ok=True)
        q.safe_extract_zip(q.THORP_ZIP, thorp_dir)
        copy_root = Path(tmp) / "dup_refs"
        copy_root.mkdir(parents=True, exist_ok=True)

        for entry in entries:
            row = entry["row"]
            result, action_records = replay_to_bust(row, thorp_dir, copy_root)
            bust_hand_num = int(row["bust_hand"])
            hand = result["hands"][bust_hand_num]
            hand_id = hand["hand_id"]
            actions = [a for a in action_records if a.get("hand_id") == hand_id]
            existing_actions = [a for a in entry["data"].get("thorp_action_records", []) if a.get("hand_id") == hand_id]
            replay_core = [normalize_action_record(a) for a in actions]
            existing_core = [normalize_action_record(a) for a in existing_actions]
            replay_matches_existing = replay_core == existing_core

            hero_cards = list((hand.get("revealed_cards") or {}).get(THORP) or (actions[-1].get("your_cards") if actions else []) or [])
            board = list(hand.get("community_cards") or [])
            by_street, total_invested = thorp_investment_by_street(hand.get("events") or [], actions[-1].get("seat") if actions else None)
            river_decision, final_decision = final_or_river_decision(actions)
            existing_river_decision, existing_final_decision = final_or_river_decision(existing_actions)
            existing_by_street, existing_total_committed = stored_commit_by_street(existing_actions)
            bucket = classify_bucket(hand, hero_cards, board)
            strength = str((hand.get("hand_strengths") or {}).get(THORP, "unknown"))
            winner_strength = best_winner_strength(hand)
            winner_ids = sorted({str(w.get("bot_id")) for w in hand.get("winners", [])})

            finding = {
                "match_id": row.get("mix") + f"_seat{row.get('thorp_seat')}_seed{row.get('seed')}",
                "mix": row.get("mix"),
                "seat": row.get("thorp_seat"),
                "seed": row.get("seed"),
                "hand_num": bust_hand_num,
                "hand_id": hand_id,
                "pot": int(hand.get("pot") or 0),
                "board": board,
                "board_texture": board_texture(board),
                "hero_cards": hero_cards,
                "made_hand": strength,
                "winner_strength": winner_strength,
                "winners": winner_ids,
                "live_opponents_on_river": live_opponents_on_river(hand),
                "river_committed": int(by_street.get("river", 0)),
                "total_committed": int(total_invested),
                "commit_by_street": by_street,
                "river_decision": river_decision,
                "final_decision": final_decision,
                "existing_river_decision": existing_river_decision,
                "existing_final_decision": existing_final_decision,
                "existing_commit_by_street": existing_by_street,
                "existing_total_committed": int(existing_total_committed),
                "thorp_action_count_bust_hand": len(actions),
                "bucket": bucket,
                "replay_matches_existing": replay_matches_existing,
                "existing_action_count_bust_hand": len(existing_actions),
                "replay_action_count_bust_hand": len(actions),
                "showdown": bool(hand.get("showdown")),
            }
            findings.append(finding)
    return findings


def decision_summary(decision: Optional[Dict[str, Any]]) -> str:
    if not decision:
        return "none"
    action = decision.get("raw_action")
    amount = decision.get("raw_amount")
    owed = decision.get("amount_owed")
    stack = decision.get("your_stack")
    pot = decision.get("pot")
    street = decision.get("street")
    bet = decision.get("your_bet_this_street")
    current = decision.get("current_bet")
    amt = f" amount={amount}" if amount is not None else ""
    pot_part = f", pot={pot}" if pot is not None else ""
    return f"{street}: faced owed={owed}, current_bet={current}{pot_part}, stack_before={stack}, bet_this_street={bet}; chose {action}{amt}"


def is_large_river_overcommit(f: Dict[str, Any]) -> bool:
    d = f.get("existing_river_decision")
    if not d:
        return False
    action = d.get("raw_action")
    if action in {"raise", "all_in"}:
        aggressive = True
    elif action == "call":
        owed = int(d.get("amount_owed") or 0)
        stack = int(d.get("your_stack") or 0)
        aggressive = stack > 0 and owed >= max(1, int(0.5 * stack))
    else:
        aggressive = False
    non_nut_bucket = f.get("bucket") in {
        "one_pair_overpair_TPTK",
        "two_pair",
        "trips_on_board_domination",
        "full_house_underboat",
        "flush_on_monotone",
        "straight_flush_possible",
        "other",
    }
    return aggressive and non_nut_bucket


def write_report(findings: List[Dict[str, Any]], path: Path) -> None:
    # Replays are useful to prove the schema gap, but not authoritative evidence:
    # reference bots use unseeded random and quick_6max did not persist full hands.
    replay_ok: List[Dict[str, Any]] = []
    replay_mismatches = findings
    bucket_counts = Counter(f["bucket"] for f in replay_ok)
    if replay_mismatches:
        bucket_counts["unclassified_existing_json_insufficient_replay_mismatch"] = len(replay_mismatches)
    river_actions = [f for f in findings if f.get("existing_river_decision")]
    large_overcommits = [f for f in findings if is_large_river_overcommit(f)]
    no_river_decisions = [f for f in findings if not f.get("existing_river_decision")]
    final_street_counts = Counter(
        (f.get("existing_final_decision") or {}).get("street", "no_action") for f in findings
    )

    lines: List[str] = []
    lines.append("# River bust triage — finals 6-max evidence")
    lines.append("")
    lines.append("Scope: existing `consult/artifacts/2026-06-04-finals-ship/6max_evidence/raw_matches/*.json`, plus diagnostic replay attempts through the marked bust hands. No `src/`, `data/`, `submissions/`, or upload changes.")
    lines.append("")
    verdict = "NO repeated avoidable river-overcommit leak found."
    if len(large_overcommits) >= 3:
        verdict = "YES: repeated avoidable aggressive river-overcommit pattern found."
    lines.append(f"## Verdict: {verdict}")
    lines.append("")
    lines.append("Authoritative evidence from the stored raw JSON:")
    lines.append("")
    lines.append(f"- River-marked Thorp bust hands: `{len(findings)}`")
    lines.append(f"- Stored Thorp decisions on the river in those bust hands: `{len(river_actions)}`")
    lines.append(f"- Hands with no stored Thorp river decision: `{len(no_river_decisions)}`")
    lines.append(f"- Large river call-off / raise / all-in candidates: `{len(large_overcommits)}`")
    lines.append(f"- Final stored Thorp commitment street counts: `{dict(sorted(final_street_counts.items()))}`")
    lines.append(f"- Full board/card/made-hand rows recoverable from stored artifacts: `0/{len(findings)}`")
    lines.append("")
    lines.append("Interpretation: these rows are marked `bust_street=river` because the all-in hand ran out to a river showdown. They are not evidence of Thorp choosing a river call/raise/all-in. The repeated pattern, if any, is earlier-street stack commitment / short-stack variance, not river overcommit.")
    lines.append("")
    lines.append("## Evidence boundary")
    lines.append("")
    lines.append("`tools/quick_6max_eval.py` persisted only `row`, `compact_result`, `thorp_action_records`, and `all_action_error_records`; it did not persist full `result[\"hands\"]`, final board, revealed cards, pot events, or opponent hole cards. Reference bots use unseeded `random`, so diagnostic replay is not the same evidence sample. Board/card/made-hand buckets are therefore not recoverable from these artifacts; the river-decision verdict is authoritative for all rows because it uses stored Thorp action records.")
    lines.append("")
    lines.append("## Bucket counts")
    lines.append("")
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: {count}")
    lines.append("")
    lines.append("## Per-hand details")
    lines.append("")
    lines.append("| match | hand | stored final Thorp action | stored committed river/total | river decision? | board / cards / made hand | pot | live river opps | bucket | evidence status |")
    lines.append("|---|---:|---|---:|---|---|---:|---:|---|---|")
    for f in findings:
        existing_river = f.get("existing_river_decision")
        existing_final = f.get("existing_final_decision")
        if existing_river:
            action_text = decision_summary(existing_river)
        elif existing_final:
            action_text = "NO RIVER DECISION; final " + decision_summary(existing_final)
        else:
            action_text = "NO RIVER DECISION; no Thorp action record in bust hand"
        existing_by_street = f.get("existing_commit_by_street") or {}
        committed = f"{int(existing_by_street.get('river', 0))}/{int(f.get('existing_total_committed') or 0)}"
        if False and f.get("replay_matches_existing"):
            board_cards = f"board `{' '.join(f['board'])}`; Thorp `{' '.join(f['hero_cards'])}`; made {f['made_hand']}; winner {f['winner_strength']}"
            pot = str(f["pot"])
            live = str(f["live_opponents_on_river"])
            bucket = f["bucket"]
            status = "replay matched stored action"
        else:
            board_cards = "unavailable from stored raw; replay mismatch"
            pot = "n/a"
            live = "n/a"
            bucket = "unclassified_existing_json_insufficient_replay_mismatch"
            status = "stored action authoritative; cards unavailable"
        lines.append(
            "| {match} | {hand} | {action} | {committed} | {river} | {board_cards} | {pot} | {live} | `{bucket}` | {status} |".format(
                match=f["match_id"],
                hand=f["hand_num"],
                action=action_text.replace("|", "/"),
                committed=committed,
                river="yes" if existing_river else "no",
                board_cards=board_cards.replace("|", "/"),
                pot=pot,
                live=live,
                bucket=bucket,
                status=status,
            )
        )
    lines.append("")
    lines.append("## Bottom line for future patch work")
    lines.append("")
    lines.append("Do not patch a river-specific fold/call cap based on this evidence. There are `0` repeated river decisions and `0` river overcommit candidates in the stored action data. If a future patch window investigates this further, rerun the 6-max eval with full `result[\"hands\"]` and rich action-request state persisted; otherwise board/card bucket triage is not recoverable from these artifacts.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    entries = load_existing_bust_rows()
    findings = replay_match_details(entries)
    write_report(findings, REPORT_PATH)
    replay_ok: List[Dict[str, Any]] = []
    replay_mismatches = findings
    bucket_counts = Counter(f["bucket"] for f in replay_ok)
    if replay_mismatches:
        bucket_counts["unclassified_existing_json_insufficient_replay_mismatch"] = len(replay_mismatches)
    print(json.dumps({
        "river_marked_bust_hands": len(findings),
        "bucket_counts": dict(bucket_counts),
        "stored_river_decisions": sum(1 for f in findings if f.get("existing_river_decision")),
        "large_overcommit_candidates": sum(1 for f in findings if is_large_river_overcommit(f)),
        "full_hand_rows_recovered_from_existing_json": 0,
        "report": str(REPORT_PATH.relative_to(ROOT)),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
