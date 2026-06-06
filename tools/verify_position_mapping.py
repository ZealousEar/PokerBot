#!/usr/bin/env python
"""Read-only verification oracle for 6-max position-mapping correctness.

Compares the SHIPPED finals bot's ``_infer_position()`` (canonical lineage:
``submissions/archive/finals-ship-b108eff5-editable-source/src/bot.py``) against
the engine's ground-truth seat/blind/button semantics
(``ext/fullhouse-engine/engine/game.py``) across many 6-max hands.

This is a TOOLS-ONLY diagnostic. It does NOT edit, repackage, or upload the
shipped bot. It imports ``_infer_position`` read-only and drives the real,
frozen ``PokerEngine`` as the oracle.

Design note: ``_infer_position(state)`` is a PURE function of
``(state, state["seat_to_act"])`` and is independent of bot identity (it never
looks at bot_id). So driving the real engine with a uniform legal-action policy
and evaluating the function at every action_request produces inference inputs
identical to a real "Thorp + 5 refs" match, while covering every seat far more
efficiently. We still rotate the dealer each hand exactly like
``sandbox/match.py::run_match`` so the button/blind geometry is authentic.

Usage:
    .venv/bin/python tools/verify_position_mapping.py --hands 1500 --seed 42
"""
import argparse
import os
import random
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_ROOT = os.path.join(REPO_ROOT, "ext", "fullhouse-engine")
SHIPPED_SRC_ROOT = os.environ.get("BOT_SRC_ROOT") or os.path.join(
    REPO_ROOT, "submissions", "archive", "finals-ship-b108eff5-editable-source"
)

# Engine import (frozen oracle).
sys.path.insert(0, ENGINE_ROOT)
from engine.game import PokerEngine, STARTING_STACK, SMALL_BLIND, BIG_BLIND  # noqa: E402

# Shipped bot import, READ-ONLY. The package uses `from src.X import ...`, so the
# editable-source root must be on the path and we import it as `src.bot`.
sys.path.insert(0, SHIPPED_SRC_ROOT)
import src.bot as shipped_bot  # noqa: E402

_infer_position = shipped_bot._infer_position


def engine_true_position(dealer_seat: int, seat: int, n: int) -> str:
    """Canonical position from engine semantics (game.py).

    Engine: BTN = dealer_seat; SB = (dealer+1)%n; BB = (dealer+2)%n (n>2).
    UTG = first active seat after BB; the seat immediately to the right of the
    button (offset n-1) is the cutoff (CO). Middle seats are HJ/MP.

    We normalise HJ -> MP because the shipped bot deliberately aliases HJ to MP.
    So an HJ/MP mismatch is NOT counted; only genuinely wrong labels surface.
    """
    if n == 2:
        return "SB" if seat == dealer_seat else "BB"
    off = (seat - dealer_seat) % n
    if off == 0:
        return "BTN"
    if off == 1:
        return "SB"
    if off == 2:
        return "BB"
    if off == 3:
        return "UTG"
    if off == n - 1:
        return "CO"
    return "MP"


def normalise(label: str) -> str:
    return "MP" if label == "HJ" else label


def policy_action(state: dict, rng: random.Random) -> dict:
    """Mostly call/check with occasional raises and rare folds so action walks
    around the whole table and every seat (incl. BTN/CO) gets to act."""
    owed = state.get("amount_owed", 0)
    r = rng.random()
    if owed == 0:
        if r < 0.12:
            return {"action": "raise", "amount": state.get("min_raise_to", BIG_BLIND)}
        return {"action": "check"}
    if r < 0.08:
        return {"action": "fold"}
    if r < 0.20:
        return {"action": "raise", "amount": state.get("min_raise_to", BIG_BLIND)}
    return {"action": "call"}


def run(n_hands: int, n_seats: int, seed: int, strip_blinds: bool):
    rng = random.Random(seed)
    bot_ids = ["seat%d" % i for i in range(n_seats)]
    stacks = {bid: STARTING_STACK for bid in bot_ids}
    dealer = 0
    records = []

    for hand_num in range(n_hands):
        alive = [bid for bid in bot_ids if stacks[bid] > 0]
        if len(alive) < 2:
            stacks = {bid: STARTING_STACK for bid in bot_ids}
            alive = list(bot_ids)
        hand_seed = seed * 1000003 + hand_num
        engine = PokerEngine(
            hand_id="vpm_h%04d" % hand_num,
            bot_ids=alive,
            dealer_seat=dealer % len(alive),
            starting_stacks={bid: stacks[bid] for bid in alive},
            seed=hand_seed,
        )
        n = len(alive)
        dealer_seat = engine.dealer_seat

        state = engine.start_hand()
        steps = 0
        while state.get("type") == "action_request":
            seat = state["seat_to_act"]
            obs = state
            if strip_blinds:
                obs = dict(state)
                obs["action_log"] = [
                    e for e in state.get("action_log", [])
                    if e.get("action") not in ("small_blind", "big_blind")
                ]
            blinds_present = any(
                e.get("action") in ("small_blind", "big_blind")
                for e in obs.get("action_log", [])
            )
            inferred = normalise(_infer_position(obs))
            true = engine_true_position(dealer_seat, seat, n)
            records.append({
                "true": true,
                "inferred": inferred,
                "blinds_present": blinds_present,
                "off": (seat - dealer_seat) % n,
                "n": n,
            })
            action = policy_action(state, rng)
            state = engine.apply_action(seat, action)
            steps += 1
            if steps > 1000:
                break

        for bid, s in state.get("final_stacks", {}).items():
            stacks[bid] = s
        dealer += 1

    return records


def report(records, label):
    total = len(records)
    mism = [r for r in records if r["true"] != r["inferred"]]
    print("\n=== %s ===" % label)
    print("total decisions: %d" % total)
    print("mismatches:      %d" % len(mism))
    print("mismatch rate:   %.4f%%" % (100.0 * len(mism) / total if total else 0.0))

    print("\nby true position:")
    by_pos = {}
    for r in records:
        by_pos.setdefault(r["true"], [0, 0])
        by_pos[r["true"]][0] += 1
        if r["true"] != r["inferred"]:
            by_pos[r["true"]][1] += 1
    for pos in ["BTN", "SB", "BB", "UTG", "MP", "CO"]:
        if pos in by_pos:
            tot, mm = by_pos[pos]
            print("  %-4s decisions=%5d mismatch=%5d (%.2f%%)"
                  % (pos, tot, mm, 100.0 * mm / tot if tot else 0))

    print("\nmismatch label pairs (true -> inferred): count")
    pairs = {}
    for r in mism:
        k = "%s -> %s" % (r["true"], r["inferred"])
        pairs[k] = pairs.get(k, 0) + 1
    for k, v in sorted(pairs.items(), key=lambda x: -x[1]):
        print("  %-14s %d" % (k, v))

    print("\nby blinds_present:")
    for flag in (True, False):
        sub = [r for r in records if r["blinds_present"] == flag]
        mm = [r for r in sub if r["true"] != r["inferred"]]
        if sub:
            print("  blinds=%s decisions=%5d mismatch=%5d (%.2f%%)"
                  % (flag, len(sub), len(mm), 100.0 * len(mm) / len(sub)))
    return total, len(mism)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hands", type=int, default=1500)
    ap.add_argument("--seats", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("Engine SB/BB = %d/%d  starting_stack=%d" % (SMALL_BLIND, BIG_BLIND, STARTING_STACK))
    print("Shipped _infer_position from: %s" % shipped_bot.__file__)

    recs = run(args.hands, args.seats, args.seed, strip_blinds=False)
    report(recs, "NORMAL 6-MAX PLAY (blinds logged by engine)")

    recs_sb = run(max(300, args.hands // 4), args.seats, args.seed + 1, strip_blinds=True)
    report(recs_sb, "SYNTHETIC: blinds stripped from action_log (fallback path)")


if __name__ == "__main__":
    main()
