#!/usr/bin/env python3
"""Field reconnaissance for the V2 overnight patch (investigation-only).

Reconstructs full hand state from the *public* portal hand histories in
`data/portal_histories/`, which expose only seat-keyed `action_log` entries
(no street markers, no per-decision pot/stack). We replay each `action_log`
through a faithful port of the engine betting state machine
(`ext/fullhouse-engine/engine/game.py`) so that street segmentation, pot/stack
tracking and side pots are correct *by construction* rather than guessed.

Authoritative `amount` semantics (from game.py::_validate / _put_in):
  - raise / all_in : amount = CUMULATIVE bet_this_street total ("raise to")
  - call           : amount = INCREMENTAL chips owed (current_bet - bet_this_street)
  - small/big_blind: amount = INCREMENTAL chips posted
  - fold / check   : amount = 0
A short call (stack < owed) is logged as `call` with full owed but only pays
min(owed, stack); the running-stack tracker caps it.

Seat handling: the engine re-enumerates seats among the *alive* (stack>0) bots
each hand (game.py PokerEngine.__init__ over `alive`). We rebuild the alive set
per hand from a running-stack tracker and map seat->identity, then VALIDATE the
mapping against `revealed_cards` (showdown bot_id set must equal the
reconstructed non-folded set).

This module writes NOTHING to runtime strategy/data. Tooling only.

Usage:
    python tools/field_recon.py validate            # consistency report
    python tools/field_recon.py emit --out <dir>    # write recon artifacts
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HIST = ROOT / "data" / "portal_histories"
THORP_BOT_ID = "1c0abfd8-c355-471b-8c7b-e5e75800ce04"
THORP_NAME = "Thorp"

SMALL_BLIND = 50
BIG_BLIND = 100
STARTING_STACK = 10_000
STREETS = ("preflop", "flop", "turn", "river")
BOARD_LEN = {"preflop": 0, "flop": 3, "turn": 4, "river": 5}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_matches(hist_dir: Path) -> List[dict]:
    """Return parsed match dicts that actually contain hands."""
    out = []
    for p in sorted(hist_dir.glob("*.json")):
        if p.stat().st_size < 1000:
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if not isinstance(d, dict) or "error" in d:
            continue
        if not d.get("hands"):
            continue
        d["_file"] = p.name
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# Per-hand reconstruction
# ---------------------------------------------------------------------------

class HandRecon:
    """Reconstructed view of a single hand.

    decisions: list of dicts, one per *voluntary* (non-blind) logged action,
    with the decision-time context captured BEFORE the chips go in.
    invested: bot_id -> chips put in this hand.
    winnings: bot_id -> chips won this hand.
    showdown_bots: set of bot_ids that reached the end un-folded.
    """

    __slots__ = ("hand_num", "seat_to_bot", "decisions", "invested",
                 "winnings", "showdown_bots", "street_of_last_action",
                 "any_all_in", "ok_reveal", "ok_pot", "board")

    def __init__(self, hand_num):
        self.hand_num = hand_num
        self.seat_to_bot: Dict[int, str] = {}
        self.decisions: List[dict] = []
        self.invested: Dict[str, int] = defaultdict(int)
        self.winnings: Dict[str, int] = defaultdict(int)
        self.showdown_bots = set()
        self.street_of_last_action = "preflop"
        self.any_all_in = False
        self.ok_reveal: Optional[bool] = None
        self.ok_pot: Optional[bool] = None
        self.board: List[str] = []


def reconstruct_hand(hand: dict, alive_bots: List[str],
                     start_stacks: Dict[str, int]) -> HandRecon:
    """Replay one hand. `alive_bots` is the seat-ordered list of bot_ids with
    stack>0 entering the hand; seat i == alive_bots[i]. `start_stacks` maps
    bot_id -> stack entering the hand."""
    r = HandRecon(hand.get("hand_num"))
    n = len(alive_bots)
    r.seat_to_bot = {i: alive_bots[i] for i in range(n)}
    community = hand.get("community_cards", []) or []
    r.board = community

    # Per-seat mutable state
    stack = {i: int(start_stacks[alive_bots[i]]) for i in range(n)}
    bet = {i: 0 for i in range(n)}             # bet_this_street
    invested = {i: 0 for i in range(n)}        # total_invested this hand
    folded = {i: False for i in range(n)}
    all_in = {i: False for i in range(n)}

    pot = 0
    current_bet = 0
    min_raise = BIG_BLIND
    last_agg = BIG_BLIND
    street_idx = 0

    def active_seats():
        return {i for i in range(n)
                if not folded[i] and not all_in[i] and stack[i] > 0}

    def put_in(seat, amount):
        nonlocal pot, current_bet
        amount = max(0, min(amount, stack[seat]))
        stack[seat] -= amount
        bet[seat] += amount
        invested[seat] += amount
        pot += amount
        if bet[seat] > current_bet:
            current_bet = bet[seat]
        if stack[seat] == 0:
            all_in[seat] = True
        return amount

    log = hand.get("action_log", []) or []
    # --- blinds (leading small_blind/big_blind entries) ---
    idx = 0
    while idx < len(log) and log[idx].get("action") in ("small_blind", "big_blind"):
        e = log[idx]
        seat = e.get("seat")
        if seat is None or seat not in stack:
            idx += 1
            continue
        put_in(seat, int(e.get("amount") or 0))
        idx += 1
    current_bet = max(current_bet, 0)
    min_raise = BIG_BLIND
    last_agg = BIG_BLIND
    needs = active_seats()  # everyone active acts preflop (BB option included)

    def advance_street():
        nonlocal street_idx, current_bet, min_raise, last_agg
        for i in range(n):
            bet[i] = 0
        current_bet = 0
        min_raise = BIG_BLIND
        last_agg = BIG_BLIND
        street_idx += 1

    # --- voluntary actions ---
    for e in log[idx:]:
        act = e.get("action")
        seat = e.get("seat")
        if seat is None or seat not in stack:
            continue
        if act in ("small_blind", "big_blind"):
            continue
        # Lazy street advance: if nobody on the current street still needs to
        # act, move to the next street before attributing this action.
        guard = 0
        while not (needs & active_seats()) and street_idx < 3 and guard < 4:
            advance_street()
            needs = active_seats()
            guard += 1
        street = STREETS[min(street_idx, 3)]
        owed = max(0, current_bet - bet[seat])
        rec = {
            "hand_num": r.hand_num,
            "seat": seat,
            "bot_id": r.seat_to_bot.get(seat),
            "street": street,
            "action": act,
            "amount_logged": int(e.get("amount") or 0),
            "pot_before": pot,
            "owed": owed,
            "current_bet": current_bet,
            "stack_before": stack[seat],
            "bet_this_street_before": bet[seat],
            "invested_before": invested[seat],
        }

        prev_current = current_bet
        if act == "fold":
            folded[seat] = True
            chips_in = 0
        elif act == "check":
            chips_in = 0
        elif act == "call":
            # logged amount is incremental owed; cap by stack
            chips_in = put_in(seat, int(e.get("amount") or 0))
        elif act == "raise":
            # logged amount is cumulative bet-to; chips added = target - bet
            target = int(e.get("amount") or 0)
            chips_in = put_in(seat, target - bet[seat])
        elif act == "all_in":
            chips_in = put_in(seat, stack[seat])
            all_in[seat] = True
        else:
            chips_in = 0

        rec["chips_in"] = chips_in
        rec["bet_to_after"] = bet[seat]
        rec["invested_after"] = invested[seat]
        rec["stack_after"] = stack[seat]
        rec["pot_after"] = pot
        rec["all_in"] = all_in[seat]
        rec["street_idx"] = street_idx
        r.decisions.append(rec)
        r.street_of_last_action = street
        if all_in[seat] or act == "all_in":
            r.any_all_in = True

        needs.discard(seat)
        if act in ("raise", "all_in"):
            raise_size = current_bet - prev_current
            if raise_size >= last_agg:
                last_agg = raise_size
                min_raise = raise_size
                needs = {i for i in active_seats() if i != seat}

    # --- finalize ---
    for i in range(n):
        if invested[i] > 0:
            r.invested[alive_bots[i]] += invested[i]
    non_folded = {alive_bots[i] for i in range(n) if not folded[i]}
    r.showdown_bots = non_folded

    for w in hand.get("winners", []) or []:
        bid = w.get("bot_id")
        if bid is not None:
            r.winnings[bid] += int(w.get("amount") or 0)

    # validation flags
    revealed = set((hand.get("revealed_cards") or {}).keys())
    if revealed:
        # showdown happened: revealed set should equal non-folded set
        r.ok_reveal = (revealed == non_folded)
    pot_total = hand.get("pot")
    win_total = sum(int(w.get("amount") or 0) for w in (hand.get("winners") or []))
    if pot_total is not None:
        r.ok_pot = (win_total == int(pot_total))
    return r


def reconstruct_match(match: dict) -> Tuple[List[HandRecon], Dict[str, int], Dict[str, int]]:
    """Reconstruct all hands in a match in order.

    Returns (hand_recons, running_stacks_end, declared_final_stacks).
    Running stacks are tracked across hands from STARTING_STACK so per-hand
    starting stacks are correct (stacks carry over within a match)."""
    bots = match.get("bots", [])
    # seat-ordered identity list (initial enumerate order == bots[].seat)
    bots_by_seat = sorted(bots, key=lambda b: b.get("seat", 0))
    seat_order_ids = [b.get("bot_id") for b in bots_by_seat]
    running = {b.get("bot_id"): STARTING_STACK for b in bots_by_seat}

    recons = []
    hands = sorted(match.get("hands", []), key=lambda h: h.get("hand_num", 0))
    for hand in hands:
        alive = [bid for bid in seat_order_ids if running.get(bid, 0) > 0]
        if len(alive) < 2:
            break
        start_stacks = {bid: running[bid] for bid in alive}
        r = reconstruct_hand(hand, alive, start_stacks)
        recons.append(r)
        # apply chip flow
        for bid in alive:
            running[bid] -= r.invested.get(bid, 0)
        for bid, amt in r.winnings.items():
            if bid in running:
                running[bid] += amt
    declared = {b.get("bot_id"): b.get("final_stack") for b in bots_by_seat}
    return recons, running, declared


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(hist_dir: Path) -> int:
    matches = load_matches(hist_dir)
    print(f"# Loaded {len(matches)} matches with hands from {hist_dir}")
    tot_hands = 0
    reveal_ok = reveal_bad = 0
    pot_ok = pot_bad = 0
    seg_ok = seg_bad = 0
    chip_ok = chip_bad = 0
    bad_examples = []
    for m in matches:
        recons, running, declared = reconstruct_match(m)
        tot_hands += len(recons)
        # chip conservation: running end vs declared final_stack
        for bid, fin in declared.items():
            if fin is None:
                continue
            if running.get(bid) == fin:
                chip_ok += 1
            else:
                chip_bad += 1
                if len(bad_examples) < 12:
                    bad_examples.append(
                        f"CHIP {m['_file'][:8]} {bid[:8]} recon={running.get(bid)} declared={fin}")
        for r in recons:
            if r.ok_reveal is True:
                reveal_ok += 1
            elif r.ok_reveal is False:
                reveal_bad += 1
                if len(bad_examples) < 12:
                    bad_examples.append(
                        f"REVEAL {m['_file'][:8]} h{r.hand_num} reveal!=nonfolded")
            if r.ok_pot is True:
                pot_ok += 1
            elif r.ok_pot is False:
                pot_bad += 1
            # segmentation: non-all-in hands -> last betting street matches board len
            if not r.any_all_in and r.decisions:
                want = None
                bl = len(r.board)
                for s, l in BOARD_LEN.items():
                    if l == bl:
                        want = s
                if want is not None:
                    if r.street_of_last_action == want:
                        seg_ok += 1
                    else:
                        seg_bad += 1
                        if len(bad_examples) < 12:
                            bad_examples.append(
                                f"SEG {m['_file'][:8]} h{r.hand_num} last={r.street_of_last_action} board={bl}")
    print(f"# total hands reconstructed: {tot_hands}")
    print(f"# revealed-set match : ok={reveal_ok} bad={reveal_bad}")
    print(f"# winners==pot       : ok={pot_ok} bad={pot_bad}")
    print(f"# segmentation(board): ok={seg_ok} bad={seg_bad}")
    print(f"# chip conservation  : ok={chip_ok} bad={chip_bad}")
    if bad_examples:
        print("# sample discrepancies:")
        for b in bad_examples:
            print("   ", b)
    return 0


COMMIT_FRAC = 0.40            # stackoff threshold (matches postflop _can_commit gate)
LARGE_POT_CHIPS = 5000        # >= 50bb final pot == "large pot"


# ---------------------------------------------------------------------------
# Field fingerprints
# ---------------------------------------------------------------------------

def build_profiles(matches: List[dict]) -> Dict[str, dict]:
    """Per-identity action fingerprint across ALL matches with hands."""
    name_by_id = {}
    prof: Dict[str, dict] = {}

    def blank():
        return {
            "hands": 0, "vpip_hands": 0, "pfr_hands": 0,
            "raises": 0, "calls": 0, "checks": 0, "folds": 0, "all_ins": 0,
            "pf_raise": 0, "pf_call": 0, "post_raise": 0, "post_call": 0,
            "raise_chips": [], "raise_to": [], "big_commit_hands": 0,
            "showdowns": 0, "showdown_wins": 0,
            "matches": 0, "busted_matches": 0, "net_chips": 0,
        }

    for m in matches:
        for b in m.get("bots", []):
            name_by_id[b.get("bot_id")] = b.get("bot_name")
        recons, running, declared = reconstruct_match(m)
        seen_ids = set()
        # per-match presence + bust + net (skip truncated for net/bust accuracy)
        truncated = any(running.get(bid) != fin for bid, fin in declared.items()
                        if fin is not None) and m["_file"].startswith("d717930b")
        # per-hand stats
        hand_invest = defaultdict(int)
        for r in recons:
            present = set(r.seat_to_bot.values())
            for bid in present:
                prof.setdefault(bid, blank())
                prof[bid]["hands"] += 1
                seen_ids.add(bid)
            # start stacks per hand
            start = {}
            for d in r.decisions:
                bid = d["bot_id"]
                if bid not in start:
                    start[bid] = d["stack_before"] + d["bet_this_street_before"]
            pf_vo_by = set(); pf_raise_by = set()
            inv_by = defaultdict(int)
            for d in r.decisions:
                bid = d["bot_id"]; act = d["action"]; st = d["street"]
                p = prof[bid]
                inv_by[bid] += d["chips_in"]
                if act == "raise":
                    p["raises"] += 1
                    p["raise_chips"].append(d["chips_in"])
                    p["raise_to"].append(d["amount_logged"])
                    (p.__setitem__("pf_raise", p["pf_raise"]+1) if st == "preflop"
                     else p.__setitem__("post_raise", p["post_raise"]+1))
                elif act == "all_in":
                    p["all_ins"] += 1
                    if st == "preflop": p["pf_raise"] += 1
                    else: p["post_raise"] += 1
                elif act == "call":
                    p["calls"] += 1
                    if st == "preflop": p["pf_call"] += 1
                    else: p["post_call"] += 1
                elif act == "check":
                    p["checks"] += 1
                elif act == "fold":
                    p["folds"] += 1
                if st == "preflop" and act in ("call", "raise", "all_in"):
                    pf_vo_by.add(bid)
                if st == "preflop" and act in ("raise", "all_in"):
                    pf_raise_by.add(bid)
            for bid in pf_vo_by:
                prof[bid]["vpip_hands"] += 1
            for bid in pf_raise_by:
                prof[bid]["pfr_hands"] += 1
            for bid, inv in inv_by.items():
                if start.get(bid) and inv >= COMMIT_FRAC * start[bid]:
                    prof[bid]["big_commit_hands"] += 1
            # showdowns
            revealed = set((r.board and r.showdown_bots) or [])
            if r.ok_reveal:  # genuine showdown
                for bid in r.showdown_bots:
                    prof.setdefault(bid, blank())
                    prof[bid]["showdowns"] += 1
                # winners among showdown
                for w in m_winner_ids(r):
                    if w in r.showdown_bots:
                        prof[w]["showdown_wins"] += 1
        for bid in seen_ids:
            prof[bid]["matches"] += 1
            fin = declared.get(bid)
            if not m["_file"].startswith("d717930b"):
                if fin == 0:
                    prof[bid]["busted_matches"] += 1
                prof[bid]["net_chips"] += (running.get(bid, 0) - STARTING_STACK)

    # finalize derived metrics
    out = {}
    for bid, p in prof.items():
        hands = max(p["hands"], 1)
        calls = max(p["calls"], 1)
        out[bid] = {
            "bot_name": name_by_id.get(bid),
            "hands": p["hands"], "matches": p["matches"],
            "vpip": round(p["vpip_hands"]/hands, 4),
            "pfr": round(p["pfr_hands"]/hands, 4),
            "af": round((p["raises"]+p["all_ins"])/calls, 3),
            "post_af": round(p["post_raise"]/max(p["post_call"], 1), 3),
            "fold_freq": round(p["folds"]/max(p["folds"]+p["calls"]+p["checks"]+p["raises"]+p["all_ins"], 1), 4),
            "raise_freq": round((p["raises"]+p["all_ins"])/max(p["folds"]+p["calls"]+p["checks"]+p["raises"]+p["all_ins"], 1), 4),
            "call_freq": round(p["calls"]/max(p["folds"]+p["calls"]+p["checks"]+p["raises"]+p["all_ins"], 1), 4),
            "all_in_actions": p["all_ins"],
            "big_commit_hands": p["big_commit_hands"],
            "big_commit_rate": round(p["big_commit_hands"]/hands, 4),
            "avg_raise_to": round(sum(p["raise_to"])/max(len(p["raise_to"]), 1), 1),
            "max_raise_to": max(p["raise_to"]) if p["raise_to"] else 0,
            "showdowns": p["showdowns"],
            "showdown_win_pct": round(p["showdown_wins"]/max(p["showdowns"], 1), 4),
            "busted_matches": p["busted_matches"],
            "bust_rate": round(p["busted_matches"]/max(p["matches"], 1), 4),
            "net_chips": p["net_chips"],
        }
    return out


def m_winner_ids(r: "HandRecon"):
    return [bid for bid, amt in r.winnings.items() if amt > 0]


def cluster_field(profiles: Dict[str, dict], min_hands: int = 60) -> dict:
    """Rule-based archetype clustering on VPIP/PFR/AF. Bots with too few hands
    are bucketed as 'insufficient_data'."""
    clusters = defaultdict(list)
    for bid, p in profiles.items():
        if p["hands"] < min_hands:
            clusters["insufficient_data"].append(bid)
            continue
        vpip, pfr, af = p["vpip"], p["pfr"], p["af"]
        loose = vpip >= 0.30
        aggro = af >= 2.0 or pfr >= 0.20
        maniac = (vpip >= 0.40 and af >= 2.5) or p["big_commit_rate"] >= 0.05
        if maniac:
            tag = "maniac_boombust"
        elif loose and aggro:
            tag = "LAG"
        elif loose and not aggro:
            tag = "loose_passive_station"
        elif (not loose) and aggro:
            tag = "TAG"
        else:
            tag = "nit_tight_passive"
        clusters[tag].append(bid)
    summary = {}
    for tag, ids in clusters.items():
        ids_named = sorted(((profiles[i]["bot_name"], i) for i in ids))
        summary[tag] = {
            "count": len(ids),
            "members": [{"bot_name": n, "bot_id": i,
                         "vpip": profiles[i]["vpip"], "pfr": profiles[i]["pfr"],
                         "af": profiles[i]["af"], "bust_rate": profiles[i]["bust_rate"],
                         "big_commit_rate": profiles[i]["big_commit_rate"],
                         "hands": profiles[i]["hands"]} for n, i in ids_named],
        }
    return summary


# ---------------------------------------------------------------------------
# Equity (showdown-only; villain cards known)
# ---------------------------------------------------------------------------

def _equity(hero, villains, board, trials=1500):
    """Thorp equity vs revealed villain hand(s) given board-at-street."""
    try:
        import eval7, random as _r
    except Exception:
        return None
    rng = _r.Random(hash((tuple(hero), tuple(board), tuple(map(tuple, villains)))) & 0xffffffff)
    dead = set(hero + board)
    for v in villains:
        dead |= set(v)
    deck = [r+s for r in "23456789TJQKA" for s in "shdc" if (r+s) not in dead]
    need = 5 - len(board)
    h = [eval7.Card(c) for c in hero]
    vs = [[eval7.Card(c) for c in v] for v in villains]
    bc = [eval7.Card(c) for c in board]
    if need <= 0:
        wins = ties = 0.0
        hs = eval7.evaluate(h + bc)
        best_v = max(eval7.evaluate(v + bc) for v in vs)
        if hs > best_v: return 1.0
        if hs == best_v: return 0.5
        return 0.0
    wins = 0.0; n = 0
    for _ in range(trials):
        rng.shuffle(deck)
        run = [eval7.Card(deck[i]) for i in range(need)]
        full = bc + run
        hs = eval7.evaluate(h + full)
        bv = max(eval7.evaluate(v + full) for v in vs)
        if hs > bv: wins += 1
        elif hs == bv: wins += 0.5
        n += 1
    return round(wins/n, 4) if n else None


# ---------------------------------------------------------------------------
# Thorp decision CSVs
# ---------------------------------------------------------------------------

def _thorp_hand_rows(matches):
    """Yield per-hand Thorp records with origin attribution + outcome."""
    for m in matches:
        if not any(b.get("bot_id") == THORP_BOT_ID for b in m.get("bots", [])):
            continue
        recons, running, declared = reconstruct_match(m)
        for r in recons:
            td = [d for d in r.decisions if d["bot_id"] == THORP_BOT_ID]
            present = THORP_BOT_ID in r.seat_to_bot.values()
            if not present:
                continue
            start = None
            if td:
                start = td[0]["stack_before"] + td[0]["bet_this_street_before"]
            inv = r.invested.get(THORP_BOT_ID, 0)
            delta = r.winnings.get(THORP_BOT_ID, 0) - inv
            by_street = defaultdict(int)
            for d in td:
                by_street[d["street"]] += d["chips_in"]
            # preflop role
            pf = [d for d in td if d["street"] == "preflop"]
            pf_acts = [d["action"] for d in pf]
            if any(a in ("raise", "all_in") for a in pf_acts):
                # opener vs 3bettor: count raises before thorp's first raise
                role = "pf_raiser"
            elif "call" in pf_acts:
                role = "pf_caller"
            elif pf_acts:
                role = "pf_checkfold"
            else:
                role = "blind_only"
            # commit-cross street
            cum = 0; cross = None
            for st in STREETS:
                cum += by_street.get(st, 0)
                if start and cum >= COMMIT_FRAC * start and cross is None:
                    cross = st
            went_all_in = any(d["action"] == "all_in" for d in td) or (start and inv >= start-1)
            if cross is None:
                origin = "none"
            elif cross == "preflop":
                origin = "preflop-raise" if role == "pf_raiser" else (
                    "preflop-flat" if role == "pf_caller" else "preflop-blind")
            else:
                origin = "postflop-escalation"
            reached_sd = bool(r.ok_reveal) and THORP_BOT_ID in r.showdown_bots
            yield dict(
                file=m["_file"][:8], hand_num=r.hand_num, start_stack=start,
                invested=inv, commit_frac=round(inv/start, 3) if start else None,
                delta=delta, won=int(delta > 0), busted=int(start is not None and inv >= start-1 and delta < 0),
                pf_invested=by_street.get("preflop", 0), flop_invested=by_street.get("flop", 0),
                turn_invested=by_street.get("turn", 0), river_invested=by_street.get("river", 0),
                role=role, origin=origin, went_all_in=int(bool(went_all_in)),
                reached_showdown=int(reached_sd), final_pot=hand_pot(m, r.hand_num),
                board=" ".join(r.board), street_ended=street_ended(m, r.hand_num),
                recon=r, match=m,
            )


def hand_pot(m, hn):
    for h in m["hands"]:
        if h.get("hand_num") == hn:
            return h.get("pot")
    return None


def street_ended(m, hn):
    for h in m["hands"]:
        if h.get("hand_num") == hn:
            return h.get("street_ended")
    return None


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def emit(hist_dir: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    matches = load_matches(hist_dir)
    thorp_matches = [m for m in matches
                     if any(b.get("bot_id") == THORP_BOT_ID for b in m.get("bots", []))]

    # 1. field fingerprints
    profiles = build_profiles(matches)
    (out / "opponent_profiles.json").write_text(json.dumps(profiles, indent=2, sort_keys=True))
    clusters = cluster_field(profiles)
    (out / "field_clusters.json").write_text(json.dumps(clusters, indent=2))
    print(f"opponent_profiles.json: {len(profiles)} identities")
    print(f"field_clusters.json: {[(k, v['count']) for k, v in clusters.items()]}")

    # 2. Thorp per-hand records
    hand_rows = list(_thorp_hand_rows(matches))

    # stackoff_decisions.csv (commit >= 40% start stack)
    so = [r for r in hand_rows if r["commit_frac"] is not None and r["commit_frac"] >= COMMIT_FRAC]
    so_fields = ["file", "hand_num", "start_stack", "invested", "commit_frac",
                 "pf_invested", "flop_invested", "turn_invested", "river_invested",
                 "role", "origin", "went_all_in", "reached_showdown",
                 "board", "street_ended", "delta", "won", "busted", "final_pot"]
    write_csv(out / "stackoff_decisions.csv", so, so_fields)
    print(f"stackoff_decisions.csv: {len(so)} hands; "
          f"net={sum(r['delta'] for r in so):+d}, "
          f"grossLoss={sum(r['delta'] for r in so if r['delta']<0):+d}, "
          f"won={sum(r['won'] for r in so)}")
    # origin breakdown
    ob = defaultdict(lambda: [0, 0])
    for r in so:
        ob[r["origin"]][0] += 1
        ob[r["origin"]][1] += r["delta"]
    print("  origin:", {k: {"n": v[0], "net": v[1]} for k, v in ob.items()})

    # large_pot_decisions.csv (one row per Thorp DECISION in large-pot hands)
    lp_rows = []
    for hr in hand_rows:
        if (hr["final_pot"] or 0) < LARGE_POT_CHIPS:
            continue
        r = hr["recon"]
        for d in r.decisions:
            if d["bot_id"] != THORP_BOT_ID:
                continue
            lp_rows.append(dict(
                file=hr["file"], hand_num=hr["hand_num"], street=d["street"],
                action=d["action"], amount_logged=d["amount_logged"], chips_in=d["chips_in"],
                pot_before=d["pot_before"], owed=d["owed"], stack_before=d["stack_before"],
                invested_after=d["invested_after"], final_pot=hr["final_pot"],
                origin=hr["origin"], hand_delta=hr["delta"], won=hr["won"],
                reached_showdown=hr["reached_showdown"]))
    lp_fields = ["file", "hand_num", "street", "action", "amount_logged", "chips_in",
                 "pot_before", "owed", "stack_before", "invested_after", "final_pot",
                 "origin", "hand_delta", "won", "reached_showdown"]
    write_csv(out / "large_pot_decisions.csv", lp_rows, lp_fields)
    print(f"large_pot_decisions.csv: {len(lp_rows)} Thorp decisions in "
          f"{sum(1 for h in hand_rows if (h['final_pot'] or 0)>=LARGE_POT_CHIPS)} large-pot hands")

    # showdown_spots.csv (SHOWDOWN-ONLY; Thorp cards known)
    sd_rows = []
    for hr in hand_rows:
        if not hr["reached_showdown"]:
            continue
        m = hr["match"]; r = hr["recon"]
        hand = next((h for h in m["hands"] if h.get("hand_num") == hr["hand_num"]), None)
        if not hand:
            continue
        rev = hand.get("revealed_cards") or {}
        hero = rev.get(THORP_BOT_ID)
        if not hero:
            continue
        villains = [v for k, v in rev.items() if k != THORP_BOT_ID]
        board = r.board[:5]
        # commit street = street where Thorp put most chips in
        td = [d for d in r.decisions if d["bot_id"] == THORP_BOT_ID]
        cs = max(STREETS, key=lambda s: sum(d["chips_in"] for d in td if d["street"] == s)) if td else "river"
        board_at = board[:BOARD_LEN[cs]]
        eq = _equity(hero, villains, board_at) if villains else None
        eq_river = _equity(hero, villains, board) if villains else None
        sd_rows.append(dict(
            file=hr["file"], hand_num=hr["hand_num"], thorp_cards=" ".join(hero),
            board=" ".join(board), n_villains=len(villains),
            villain_cards=" | ".join(" ".join(v) for v in villains),
            commit_street=cs, equity_at_commit=eq, equity_river=eq_river,
            invested=hr["invested"], final_pot=hr["final_pot"], delta=hr["delta"],
            won=hr["won"], origin=hr["origin"], commit_frac=hr["commit_frac"]))
    sd_fields = ["file", "hand_num", "thorp_cards", "board", "n_villains", "villain_cards",
                 "commit_street", "equity_at_commit", "equity_river", "invested",
                 "final_pot", "delta", "won", "origin", "commit_frac"]
    write_csv(out / "showdown_spots.csv", sd_rows, sd_fields)
    print(f"showdown_spots.csv: {len(sd_rows)} Thorp showdown hands")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--hist", type=Path, default=DEFAULT_HIST)
    e = sub.add_parser("emit")
    e.add_argument("--hist", type=Path, default=DEFAULT_HIST)
    e.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.cmd == "validate":
        return validate(args.hist)
    if args.cmd == "emit":
        return emit(args.hist, args.out)
    return 1


if __name__ == "__main__":
    sys.exit(main())
