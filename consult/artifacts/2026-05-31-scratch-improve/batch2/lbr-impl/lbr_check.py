"""Trustworthy Local Best Response (LBR) exploitability estimator.

Implements a MATCH-PLAY LBR in the spirit of Lisy & Bowling 2017
(arXiv:1612.07547). Unlike the prior synthetic-spot stub, this drives full
heads-up hands through the REAL Fullhouse engine
(`ext/fullhouse-engine/engine/game.py`) and pits the bot-under-test (HERO,
fixed strategy via its packaged `decide`) against an LBR opponent (VILLAIN)
that, at each of its own decision nodes, plays a one-step local best response:

  for each candidate villain action a in {fold, call/check, raise@sizes, all_in}:
      EV(a) = Monte-Carlo estimate of villain's terminal chip value, assuming
              * hero keeps playing its real `decide` strategy for hero's
                future decisions (so hero's real fold/call/raise frequencies
                drive the result), and
              * villain plays a fixed PASSIVE continuation (call / check-down)
                for all of villain's *future* decisions after a
                (this is LBR's depth-limited "wpsa"/check-down rollout tail).
  villain plays argmax_a EV(a).

Exploitability = villain's average net chips won per hand over many seeded
hands, expressed in milli-big-blinds per game (mbb/g). A near-Nash hero leaks
very little, so this number is small for a well-built bot. This is a LOWER
BOUND on true exploitability (LBR only deviates one step + passive tail; a
fuller best response could win more), which is exactly the guarantee LBR is
designed to give.

Why match-play (not isolated synthetic spots): exploitability must be a
zero-sum chip flow measured against the actual game value. Scoring isolated
spots and subtracting an arbitrary "baseline action" EV double-counts dead
money already in the pot (a hero fold on the turn looks like the villain
"winning" hero's prior-street investment for free), which inflates the number
by orders of magnitude. The shipped v_final historically passed an LBR gate at
preflop 18.0 / aggregate 7.4 mbb/g; this match-play formulation reproduces
small numbers for v_final, the synthetic-spot formulation does not.

Streets:
  * aggregate : villain best-responds on EVERY street (preflop+flop+turn+river).
  * preflop   : villain best-responds ONLY on preflop nodes; postflop villain
                plays the fixed passive continuation. Isolates preflop leak.

Usage:
    python lbr_check.py --bot submissions/v_final.zip \
        --hands 4000 --rollouts 80 --max-preflop-mbb 100 --max-aggregate-mbb 200

# Source: Lisy & Bowling 2017 -- Local Best Response, arXiv:1612.07547
# Source: [[Engine-Fullhouse]] (engine semantics, heads-up rules, showdown)
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import random
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import eval7

# --- Engine import (read-only; canonical clone) ----------------------------
ENGINE_ROOT = Path("/Users/farhad/Code/PokerBot/ext/fullhouse-engine")
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))
from engine.game import PokerEngine, BIG_BLIND, SMALL_BLIND, STARTING_STACK  # noqa: E402

RANKS = "23456789TJQKA"
SUITS = "shdc"
FULL_DECK = tuple(r + s for r in RANKS for s in SUITS)

HERO_ID = "hero"
VILLAIN_ID = "villain"

# eval7 LUT warm-up
eval7.evaluate([eval7.Card(c) for c in ("As", "Ks", "Qs", "Js", "Ts", "2c", "3d")])


# ---------------------------------------------------------------------------
# Bot loading (mirror of the engine/codex zip loader)
# ---------------------------------------------------------------------------

def _extract_zip(zip_path: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="fh_lbr_"))
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(tmp)
    if not (tmp / "bot.py").is_file():
        shutil.rmtree(tmp, ignore_errors=True)
        raise ValueError("zip must contain bot.py at archive root")
    return tmp


def load_decide(zip_path: Path):
    """Load decide() from a packaged bot.zip into this process. Returns
    (decide, cleanup). Isolates sys.modules so successive loads of different
    zips do not collide on the `bot`/`src` module names."""
    mount = _extract_zip(zip_path)
    old_path = list(sys.path)
    old_data_dir = os.environ.get("BOT_DATA_DIR")
    old_modules = {
        name: sys.modules[name]
        for name in list(sys.modules)
        if name == "bot" or name == "src" or name.startswith("src.")
    }
    for name in old_modules:
        sys.modules.pop(name, None)
    sys.path.insert(0, str(mount))
    os.environ["BOT_DATA_DIR"] = str(mount / "data")
    module = importlib.import_module("bot")

    def cleanup():
        sys.path[:] = old_path
        for name in list(sys.modules):
            if name == "bot" or name == "src" or name.startswith("src."):
                sys.modules.pop(name, None)
        sys.modules.update(old_modules)
        if old_data_dir is None:
            os.environ.pop("BOT_DATA_DIR", None)
        else:
            os.environ["BOT_DATA_DIR"] = old_data_dir
        shutil.rmtree(mount, ignore_errors=True)

    return module.decide, cleanup


# ---------------------------------------------------------------------------
# Hand-strength helper (used by the LBR rollout tail; engine uses eval7 too)
# ---------------------------------------------------------------------------

def _showdown_winner(hero_cards, villain_cards, board) -> float:
    """Return villain's share in [0,1]: 1.0 villain wins, 0.5 tie, 0.0 hero."""
    hero_eval = eval7.evaluate([eval7.Card(c) for c in hero_cards] +
                               [eval7.Card(c) for c in board])
    vill_eval = eval7.evaluate([eval7.Card(c) for c in villain_cards] +
                               [eval7.Card(c) for c in board])
    if vill_eval > hero_eval:
        return 1.0
    if vill_eval == hero_eval:
        return 0.5
    return 0.0


# ---------------------------------------------------------------------------
# LBR opponent
# ---------------------------------------------------------------------------
#
# The villain is a player inside the real engine. We cannot edit the engine to
# inject a custom agent, so we re-implement the (small) heads-up control loop:
# at each step the engine hands us a state for the seat to act; if it is the
# hero seat we query the hero's real decide(); if it is the villain seat we run
# the LBR policy below. The engine remains the source of truth for legality,
# pot/side-pot math, street advancement, and showdown.

RAISE_POT_FRACTIONS = (0.5, 1.0, 2.0)  # sizing tree for the local best response


class LBRPlayer:
    """One-step local best response opponent.

    Belief model (documented LBR approximation): the villain does NOT know
    hero's exact hole cards. At a decision node it samples hero hole cards
    uniformly from the cards not visible to the villain (its own cards + the
    board are removed). For each candidate villain action it Monte-Carlo
    estimates villain terminal chip value by:
        - dealing hero a hand from that belief,
        - asking hero's real decide() how hero reacts to the candidate action,
        - then PASSIVELY playing the remainder (villain checks/calls; hero
          continues with decide()) to a terminal node, rolling out the board.
    It chooses the action with the highest mean villain value.

    `respond_streets` restricts on which streets the villain best-responds; on
    other streets the villain plays the fixed passive continuation (call/check).
    """

    def __init__(self, decide, rng: random.Random, rollouts: int,
                 respond_streets=("preflop", "flop", "turn", "river")):
        self.decide = decide
        self.rng = rng
        self.rollouts = rollouts
        self.respond_streets = set(respond_streets)

    # -- public: produce a villain action dict for an engine state -----------
    def act(self, engine: PokerEngine, state: dict) -> dict:
        street = state.get("street")
        owed = int(state.get("amount_owed") or 0)
        can_check = bool(state.get("can_check"))

        if street not in self.respond_streets:
            # passive continuation: check if free else call
            return {"action": "check"} if can_check else {"action": "call"}

        candidates = self._candidate_actions(state)
        if len(candidates) == 1:
            return candidates[0]

        best_action = None
        best_ev = None
        for cand in candidates:
            ev = self._evaluate_candidate(engine, state, cand)
            if best_ev is None or ev > best_ev:
                best_ev = ev
                best_action = cand
        return best_action

    # -- candidate action set ------------------------------------------------
    def _candidate_actions(self, state: dict) -> list:
        can_check = bool(state.get("can_check"))
        owed = int(state.get("amount_owed") or 0)
        stack = int(state.get("your_stack") or 0)
        bet_this = int(state.get("your_bet_this_street") or 0)
        current_bet = int(state.get("current_bet") or 0)
        min_raise_to = int(state.get("min_raise_to") or 0)
        pot = int(state.get("pot") or 0)
        stack_total = stack + bet_this  # max raise-to the villain can post

        out = []
        # passive leg
        if can_check:
            out.append({"action": "check"})
        else:
            # fold and call are both available facing a bet
            out.append({"action": "fold"})
            if owed < stack:  # can actually call without being all-in via call
                out.append({"action": "call"})
            else:
                out.append({"action": "call"})  # call clamps to all-in in engine
        # aggressive legs: raise to pot fractions, plus all-in
        for frac in RAISE_POT_FRACTIONS:
            # pot after villain calls the outstanding amount, then bets frac*pot
            call_amt = max(0, current_bet - bet_this)
            pot_after_call = pot + call_amt
            raise_to = current_bet + int(round(frac * pot_after_call))
            raise_to = max(raise_to, min_raise_to)
            if raise_to >= stack_total:
                continue  # collapses into all-in, added below
            if raise_to <= current_bet:
                continue
            out.append({"action": "raise", "amount": raise_to})
        # all-in is always a legal aggressive option (distinct from raise)
        if stack_total > current_bet or can_check:
            out.append({"action": "all_in"})

        # de-dup by (action, amount)
        seen = set()
        uniq = []
        for a in out:
            key = (a["action"], a.get("amount"))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(a)
        return uniq

    # -- evaluate one candidate via Monte-Carlo rollout ----------------------
    def _evaluate_candidate(self, engine: PokerEngine, state: dict,
                            candidate: dict) -> float:
        villain_seat = int(state["seat_to_act"])
        hero_seat = 1 - villain_seat
        board = list(engine.community_cards)  # eval7.Card list
        board_str = [str(c) for c in board]
        villain_cards = [str(c) for c in engine.players[villain_seat].hole_cards]
        dead = set(board_str) | set(villain_cards)
        avail = [c for c in FULL_DECK if c not in dead]

        total = 0.0
        n = max(1, self.rollouts)
        for _ in range(n):
            total += self._one_rollout(engine, villain_seat, hero_seat,
                                       candidate, avail)
        return total / n

    def _one_rollout(self, engine: PokerEngine, villain_seat: int,
                     hero_seat: int, candidate: dict, avail: list) -> float:
        """Clone the engine state, deal hero a sampled hand, apply the villain
        candidate, then play the depth-limited passive tail. Return villain's
        net chip delta for the hand (final villain stack minus villain stack at
        the START of this hand)."""
        sim = _clone_engine(engine)
        # Deal hero a sampled hand from villain's belief (uniform over avail).
        hero_hand = self.rng.sample(avail, 2)
        sim.players[hero_seat].hole_cards = [eval7.Card(c) for c in hero_hand]
        # Fix the remaining deck for the runout so the board completes from
        # cards consistent with this sample (avoid dealing hero/villain cards).
        used = set(str(c) for c in sim.players[hero_seat].hole_cards)
        used |= set(str(c) for c in sim.players[villain_seat].hole_cards)
        used |= set(str(c) for c in sim.community_cards)
        runout_pool = [c for c in avail if c not in used]
        self.rng.shuffle(runout_pool)
        sim._deck_cards = [eval7.Card(c) for c in runout_pool]
        sim._deck_idx = 0

        villain_start_stack = sim._starting_stacks.get(VILLAIN_ID, STARTING_STACK)

        # Apply the villain's candidate action for real in the sim.
        state = sim.apply_action(villain_seat, candidate)

        # Play to terminal: hero uses decide(); villain plays passive tail.
        steps = 0
        while isinstance(state, dict) and state.get("type") == "action_request":
            seat = state["seat_to_act"]
            if seat == hero_seat:
                action = self._safe_decide(state)
            else:
                action = ({"action": "check"} if state.get("can_check")
                          else {"action": "call"})
            state = sim.apply_action(seat, action)
            steps += 1
            if steps > 400:
                break

        final_villain = sim.players[villain_seat].stack
        return float(final_villain - villain_start_stack)

    def _safe_decide(self, state: dict) -> dict:
        try:
            a = self.decide(_public_state_for_hero(state))
            if isinstance(a, dict) and "action" in a:
                return a
        except Exception:
            pass
        return {"action": "check"} if state.get("can_check") else {"action": "fold"}


# ---------------------------------------------------------------------------
# Engine cloning + state shaping
# ---------------------------------------------------------------------------

def _clone_engine(engine: PokerEngine) -> PokerEngine:
    """Deep-ish clone of the engine sufficient to roll a hand out. eval7.Card
    is immutable so card lists can be shallow-copied by reference."""
    import copy
    clone = PokerEngine.__new__(PokerEngine)
    clone.players = []
    for p in engine.players:
        np = type(p)(seat=p.seat, bot_id=p.bot_id, stack=p.stack)
        np.hole_cards = list(p.hole_cards)
        np.is_folded = p.is_folded
        np.is_all_in = p.is_all_in
        np.bet_this_street = p.bet_this_street
        np.total_invested = p.total_invested
        clone.players.append(np)
    clone.n = engine.n
    clone.dealer_seat = engine.dealer_seat
    clone.hand_id = engine.hand_id
    clone.seed = engine.seed
    clone.pot = engine.pot
    clone.community_cards = list(engine.community_cards)
    clone.street = engine.street
    clone.action_log = [dict(a) for a in engine.action_log]
    clone.events = []  # not needed for rollout value
    clone.current_bet = engine.current_bet
    clone.min_raise = engine.min_raise
    clone._last_aggression_size = engine._last_aggression_size
    clone._needs_to_act = set(engine._needs_to_act)
    clone._deck_cards = list(engine._deck_cards)
    clone._deck_idx = engine._deck_idx
    clone._starting_stacks = dict(engine._starting_stacks)
    return clone


def _public_state_for_hero(state: dict) -> dict:
    """The engine already builds a hero-facing public state via _build_state;
    when the seat_to_act is the hero this dict is exactly what the hero's bot
    sees in a real match. We pass it through unchanged (it already hides
    villain hole cards)."""
    return state


# ---------------------------------------------------------------------------
# Match driver
# ---------------------------------------------------------------------------

def _inject_match_log(state: dict, match_log: list) -> dict:
    if isinstance(state, dict) and state.get("type") == "action_request":
        state["match_action_log"] = match_log[-200:]
    return state


def play_lbr_match(hero_decide, n_hands: int, rollouts: int, seed_base: int,
                   respond_streets) -> dict:
    """Play n_hands heads-up between hero (decide) and the LBR villain.
    Alternate the dealer each hand (matches engine convention). Reset stacks to
    STARTING_STACK each hand so a single bust does not end the measurement and
    every hand is an i.i.d. exploitability sample (per-hand chip flow is what
    mbb/g measures). Returns aggregate stats."""
    villain_net = 0.0
    hero_net = 0.0
    n_played = 0
    villain_busts = 0
    hero_busts = 0
    rng = random.Random(seed_base ^ 0xA5A5A5)
    match_action_log: list = []

    for hand_num in range(n_hands):
        # Reset to even stacks each hand: isolates per-hand exploit, avoids
        # absorbing-state bias where one bust freezes the measurement.
        dealer = hand_num % 2
        bot_ids = [HERO_ID, VILLAIN_ID]
        hand_seed = seed_base * 1000003 + hand_num
        engine = PokerEngine(
            hand_id=f"lbr_h{hand_num:05d}",
            bot_ids=bot_ids,
            dealer_seat=dealer,
            starting_stacks={HERO_ID: STARTING_STACK, VILLAIN_ID: STARTING_STACK},
            seed=hand_seed,
        )
        villain = LBRPlayer(hero_decide, rng, rollouts, respond_streets)

        state = _inject_match_log(engine.start_hand(), match_action_log)
        steps = 0
        while isinstance(state, dict) and state.get("type") == "action_request":
            seat = state["seat_to_act"]
            bot_id = bot_ids[seat]
            if bot_id == HERO_ID:
                action = _safe_hero(hero_decide, state)
            else:
                action = villain.act(engine, state)
            match_action_log.append({
                "hand_num": hand_num, "seat": seat, "bot_id": bot_id,
                "action": action.get("action"), "amount": action.get("amount"),
            })
            state = _inject_match_log(engine.apply_action(seat, action),
                                      match_action_log)
            steps += 1
            if steps > 1000:
                break

        final = state.get("final_stacks", {}) if isinstance(state, dict) else {}
        v_final = final.get(VILLAIN_ID, STARTING_STACK)
        h_final = final.get(HERO_ID, STARTING_STACK)
        villain_net += (v_final - STARTING_STACK)
        hero_net += (h_final - STARTING_STACK)
        if v_final <= 0:
            villain_busts += 1
        if h_final <= 0:
            hero_busts += 1
        n_played += 1

    return {
        "hands": n_played,
        "villain_net_chips": villain_net,
        "hero_net_chips": hero_net,
        "villain_chips_per_hand": villain_net / max(1, n_played),
        # mbb/g: chips-per-hand / BB * 1000
        "villain_mbb_g": (villain_net / max(1, n_played)) / BIG_BLIND * 1000.0,
        "villain_busts": villain_busts,
        "hero_busts": hero_busts,
    }


def _safe_hero(decide, state: dict) -> dict:
    try:
        a = decide(state)
        if isinstance(a, dict) and "action" in a:
            return a
    except Exception:
        pass
    return {"action": "check"} if state.get("can_check") else {"action": "fold"}


# ---------------------------------------------------------------------------
# Top-level: compute preflop + aggregate exploitability
# ---------------------------------------------------------------------------

def compute_lbr(hero_decide, n_hands: int, rollouts: int, seed_base: int) -> dict:
    t0 = time.time()
    aggregate = play_lbr_match(
        hero_decide, n_hands, rollouts, seed_base,
        respond_streets=("preflop", "flop", "turn", "river"),
    )
    t1 = time.time()
    preflop = play_lbr_match(
        hero_decide, n_hands, rollouts, seed_base,
        respond_streets=("preflop",),
    )
    t2 = time.time()
    return {
        "n_hands": n_hands,
        "rollouts": rollouts,
        "seed_base": seed_base,
        "preflop_mbb_g": round(preflop["villain_mbb_g"], 2),
        "aggregate_mbb_g": round(aggregate["villain_mbb_g"], 2),
        "preflop_detail": preflop,
        "aggregate_detail": aggregate,
        "elapsed_aggregate_s": round(t1 - t0, 1),
        "elapsed_preflop_s": round(t2 - t1, 1),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bot", type=Path,
                   default=Path("/Users/farhad/Code/PokerBot/submissions/v_final.zip"))
    p.add_argument("--hands", type=int, default=4000)
    p.add_argument("--rollouts", type=int, default=80,
                   help="Monte-Carlo rollouts per villain candidate action")
    p.add_argument("--seed-base", type=int, default=42)
    p.add_argument("--max-preflop-mbb", type=float, default=100.0)
    p.add_argument("--max-aggregate-mbb", type=float, default=200.0)
    p.add_argument("--json-out", type=Path, default=None)
    args = p.parse_args()

    bot_path = args.bot.resolve()
    if not bot_path.is_file():
        print(f"FAIL: bot not found: {bot_path}")
        return 2

    decide, cleanup = load_decide(bot_path)
    try:
        result = compute_lbr(decide, args.hands, args.rollouts, args.seed_base)
    finally:
        cleanup()

    result["bot"] = str(bot_path)
    result["max_preflop_mbb"] = args.max_preflop_mbb
    result["max_aggregate_mbb"] = args.max_aggregate_mbb
    result["preflop_pass"] = result["preflop_mbb_g"] <= args.max_preflop_mbb
    result["aggregate_pass"] = result["aggregate_mbb_g"] <= args.max_aggregate_mbb
    result["passed"] = result["preflop_pass"] and result["aggregate_pass"]

    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"\nLBR preflop={result['preflop_mbb_g']:.1f} mbb/g "
          f"(cap {args.max_preflop_mbb:.0f}) "
          f"aggregate={result['aggregate_mbb_g']:.1f} mbb/g "
          f"(cap {args.max_aggregate_mbb:.0f}) over {args.hands} hands x {args.rollouts} rollouts")
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True))
    print("exploit_check PASS" if result["passed"] else "exploit_check FAIL")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
