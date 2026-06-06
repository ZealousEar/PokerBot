<file_map>
/Users/farhad/Code/PokerBot
├── consult
│   └── artifacts
│       ├── 2026-06-03-qual2-patch
│       │   ├── acceptance_test.py * +
│       │   ├── FINDINGS.md *
│       │   ├── opponents_top25_stats.md *
│       │   ├── postflop_baseline.py * +
│       │   └── postflop_patched.py * +
│       ├── 2026-05-27-qualifier-brainstorm
│       ├── 2026-05-27-worktree-audit
│       ├── 2026-05-28-b8-runner
│       │   └── logs
│       ├── 2026-05-28-gauntlet-variance
│       │   ├── run_1
│       │   ├── run_2
│       │   ├── run_3
│       │   ├── run_4
│       │   └── run_5
│       ├── 2026-05-28-pods
│       ├── 2026-05-28-pre-qualifier-review
│       ├── 2026-05-28-public-saturation
│       │   └── opponent_zips
│       ├── 2026-05-29-away
│       │   ├── _prompts
│       │   ├── mehedi-cluster
│       │   │   └── ...
│       │   ├── patch-window-postflop-extractor
│       │   ├── postflop-trap-candidate
│       │   │   └── ...
│       │   ├── preflop-antecedent-grid
│       │   │   └── ...
│       │   ├── public-drift-completeness
│       │   │   └── ...
│       │   ├── ship-day-rehearsal
│       │   │   └── ...
│       │   └── trap-sixmax-prevalence
│       │       └── ...
│       ├── 2026-05-29-mehedi-cluster
│       │   └── logs
│       ├── 2026-05-29-pre-qualifier-triage
│       ├── 2026-05-29-public-drift-patch
│       │   ├── logs
│       │   └── opponent_zips
│       ├── 2026-05-29-public-refresh-design
│       ├── 2026-05-29-public-repo-drift
│       │   ├── _clones
│       │   │   └── ...
│       │   ├── logs
│       │   ├── metadata
│       │   └── opponent_zips
│       ├── 2026-05-29-ship-lock-audit
│       ├── 2026-05-30-dual-leak-swarm
│       │   ├── laneA-postflop-v2
│       │   │   └── ...
│       │   ├── laneB-mehedi-bb
│       │   │   └── ...
│       │   └── laneC-toby-gauntlet
│       │       └── ...
│       ├── 2026-05-31-finals-infra-scratch
│       │   ├── diag-01
│       │   │   └── ...
│       │   ├── lbr_sanity
│       │   └── report
│       ├── 2026-05-31-scratch-improve
│       │   ├── batch2
│       │   │   └── ...
│       │   ├── gate-harness
│       │   │   └── ...
│       │   ├── overlay-cap
│       │   │   └── ...
│       │   └── sibling-gate
│       │       └── ...
│       ├── 2026-05-31-ship-lock
│       ├── 2026-06-01-public-repo-drift
│       ├── arbitration
│       └── release
├── .githooks
├── data
│   └── portal_histories
├── docs
│   ├── designs
│   ├── investigations
│   ├── plans
│   ├── playbooks
│   └── reviews
├── prompt-exports
├── src
├── submissions
├── tests
│   ├── edge_cases
│   └── integration
│       └── fixtures
│           └── postflop_trap_prevalence
└── tools

/Users/farhad/Code/PokerBot-claude
├── src
│   └── equity.py *
├── .githooks
├── consult
│   └── artifacts
│       ├── 2026-05-28-analyzer-hardening
│       │   ├── R1_schema_rehearsal
│       │   │   └── ...
│       │   └── R2_schema_fuzzing
│       │       └── ...
│       ├── 2026-06-02-finals-projection
│       ├── 2026-06-02-patch-window-prep
│       │   ├── R1_schema_rehearsal
│       │   │   └── ...
│       │   └── R2_schema_fuzzing
│       │       └── ...
│       └── 2026-06-04-weakness-vladimir
├── consults
│   ├── 2026-05-27-confirm-light3bet
│   ├── 2026-05-27-confirm-light3bet-v14
│   ├── 2026-05-27-hygiene-1
│   │   └── command_logs
│   ├── 2026-05-27-overnight-A
│   │   ├── baseline
│   │   ├── candidate_0
│   │   ├── candidate_1
│   │   ├── candidate_2
│   │   ├── candidate_3
│   │   ├── candidate_4
│   │   ├── candidate_5
│   │   └── candidate_6
│   ├── 2026-05-27-overnight-B
│   │   ├── dominic
│   │   ├── famadeo
│   │   ├── neel
│   │   └── vladimir
│   ├── 2026-05-27-overnight-D
│   │   ├── logs
│   │   ├── priors
│   │   ├── scripts
│   │   └── synthetic
│   ├── 2026-05-27-overnight-E
│   ├── 2026-05-27-overnight-F
│   │   └── replay_traces
│   │       ├── dominic
│   │       ├── famadeo
│   │       ├── neel
│   │       └── vladimir
│   ├── 2026-05-27-overnight-H
│   │   └── sizing_sweep
│   │       ├── candidate_0
│   │       ├── candidate_1
│   │       ├── candidate_2
│   │       └── candidate_3
│   ├── 2026-05-27-overnight-I
│   ├── 2026-05-27-overnight-J
│   ├── 2026-05-27-overnight-K
│   │   └── lbr_vs_competitor
│   ├── 2026-05-27-overnight-L
│   │   └── range_tuning
│   │       ├── candidate_0
│   │       ├── candidate_1
│   │       ├── candidate_2
│   │       ├── candidate_3
│   │       ├── candidate_4
│   │       └── candidate_5
│   ├── 2026-05-27-overnight-M
│   │   └── 3bet_sweep
│   │       ├── candidate_0
│   │       ├── candidate_1
│   │       ├── candidate_2
│   │       ├── candidate_3
│   │       └── candidate_4
│   ├── 2026-05-27-overnight-N
│   │   └── failure_dumps
│   ├── 2026-05-27-overnight-O
│   ├── 2026-05-27-overnight-P
│   ├── 2026-05-27-overnight-Q
│   ├── 2026-05-27-overnight-R
│   │   └── tmp
│   │       └── bench_zip_m2s6msx9
│   │           └── ...
│   ├── 2026-05-27-overnight-S
│   │   └── replays
│   ├── 2026-05-27-overnight-SUMMARY
│   │   ├── codex_logs
│   │   └── prompts
│   ├── 2026-05-27-overnight-T
│   │   └── synthetic_finals_field
│   │       ├── v1
│   │       ├── v2
│   │       ├── v3
│   │       ├── v4
│   │       └── v5
│   ├── 2026-05-27-patch1-A
│   │   ├── h2h_dominic
│   │   ├── h2h_famadeo
│   │   ├── h2h_neel
│   │   └── h2h_vladimir
│   └── 2026-05-27-patch1-reconcile
├── data
├── docs
│   └── playbooks
├── findings
├── submissions
├── tests
│   ├── edge_cases
│   └── integration
└── tools


(* denotes selected files)
(+ denotes code-map available)
Config: directory-only view; depth cap 3; selected files shown.
</file_map>
<file_contents>
File: /Users/farhad/Code/PokerBot-claude/src/equity.py
```py
"""Monte Carlo equity vs range using eval7.

Budget: ≤ 5 ms per call at default trials. Pre-warm eval7 LUTs at module
import so the live 2 s decisions do not pay a cold-start cost.

# Source: [[Pluribus-Brown-Sandholm-2019]] — depth-limited heuristic in lieu of full solve
"""
import hashlib
import random
from typing import Iterable, Sequence

import eval7


def _stable_seed(*parts) -> int:
    """Deterministic seed across processes (Python's hash() is randomized
    per-process by PYTHONHASHSEED). Uses sha1 of repr."""
    payload = repr(parts).encode("utf-8")
    return int(hashlib.sha1(payload).hexdigest()[:8], 16)

# Pre-warm eval7 hand-rank LUT (covered by the 30 s warmup).
_WARM_DECK = [eval7.Card(r + s) for r in "23456789TJQKA" for s in "shdc"]
_ = eval7.evaluate(_WARM_DECK[:7])

RANKS = "23456789TJQKA"
SUITS = "shdc"
_RANK_VAL = {r: i for i, r in enumerate(RANKS)}


def parse_card(s: str) -> eval7.Card:
    return eval7.Card(s)


def canonical_hand(cards: Sequence[str]) -> str:
    """Return canonical hand tag like 'AA', 'AKs', 'T9o' from ['As','Kh']."""
    if len(cards) != 2:
        return ""
    r0, s0 = cards[0][0], cards[0][1]
    r1, s1 = cards[1][0], cards[1][1]
    if r0 == r1:
        return r0 + r1
    if _RANK_VAL[r0] < _RANK_VAL[r1]:
        r0, r1, s0, s1 = r1, r0, s1, s0
    return r0 + r1 + ("s" if s0 == s1 else "o")


def expand_range_tag(tag: str) -> list:
    """Expand a range tag ('AKs', 'TT', '88+', 'A5s+', 'QJs-T9s', 'AK')
    into a list of canonical hand strings. Best-effort."""
    out = []
    if "+" in tag and "-" not in tag:
        base = tag[:-1]
        if len(base) == 2 and base[0] == base[1]:
            # Pair plus: 88+ -> 88,99,...,AA
            i = _RANK_VAL[base[0]]
            for j in range(i, len(RANKS)):
                out.append(RANKS[j] + RANKS[j])
        elif len(base) == 3:
            # Like A5s+ -> A5s,A6s,...,AKs (gap closes toward higher)
            hi, lo, su = base[0], base[1], base[2]
            for j in range(_RANK_VAL[lo], _RANK_VAL[hi]):
                out.append(hi + RANKS[j] + su)
        elif len(base) == 2:
            # Like AK -> AKs, AKo
            out.append(base + "s")
            out.append(base + "o")
        return out
    if "-" in tag:
        # Like 88-22 or QJs-T9s. Best-effort.
        a, b = tag.split("-")
        if len(a) == 2 and a[0] == a[1] and len(b) == 2 and b[0] == b[1]:
            lo = min(_RANK_VAL[a[0]], _RANK_VAL[b[0]])
            hi = max(_RANK_VAL[a[0]], _RANK_VAL[b[0]])
            for j in range(lo, hi + 1):
                out.append(RANKS[j] + RANKS[j])
        return out
    if len(tag) == 2 and tag[0] != tag[1]:
        out.append(tag + "s")
        out.append(tag + "o")
        return out
    return [tag]


def range_to_combos(range_tags: Iterable[str], dead_cards: Sequence[str] = ()) -> list:
    """Return list of (card1, card2) eval7.Card pairs for the given range,
    excluding any combos that use dead_cards."""
    dead = set()
    for c in dead_cards:
        if isinstance(c, str) and len(c) == 2:
            dead.add(c)
    combos = []
    seen = set()
    for tag in range_tags:
        for h in expand_range_tag(tag):
            if h in seen:
                continue
            seen.add(h)
            if len(h) == 2:  # pair
                r = h[0]
                cards = [r + s for s in SUITS]
                for i in range(4):
                    for j in range(i + 1, 4):
                        c1, c2 = cards[i], cards[j]
                        if c1 in dead or c2 in dead:
                            continue
                        combos.append((eval7.Card(c1), eval7.Card(c2)))
            elif len(h) == 3:
                hi, lo, su = h[0], h[1], h[2]
                if su == "s":
                    for s in SUITS:
                        c1, c2 = hi + s, lo + s
                        if c1 in dead or c2 in dead:
                            continue
                        combos.append((eval7.Card(c1), eval7.Card(c2)))
                else:  # offsuit
                    for s1 in SUITS:
                        for s2 in SUITS:
                            if s1 == s2:
                                continue
                            c1, c2 = hi + s1, lo + s2
                            if c1 in dead or c2 in dead:
                                continue
                            combos.append((eval7.Card(c1), eval7.Card(c2)))
    return combos


def equity_vs_range(hero_cards: Sequence[str],
                    board: Sequence[str],
                    villain_range: Iterable[str],
                    trials: int = 300,
                    rng: random.Random = None) -> float:
    """Hero equity vs a random combo drawn from villain_range, over `trials`
    Monte Carlo rollouts. Returns float in [0, 1]. Tunable trials lets postflop
    callers stay within budget."""
    if rng is None:
        # Seed deterministically from (hand, board) so identical inputs give
        # identical equity — required for reproducible benchmarks.
        rng = random.Random(_stable_seed("eq_vs_range", tuple(hero_cards),
                                          tuple(board), trials))
    hero = [eval7.Card(c) for c in hero_cards]
    board_cards = [eval7.Card(c) for c in board]
    dead = list(hero_cards) + list(board)
    combos = range_to_combos(villain_range, dead)
    if not combos:
        return 0.5
    deck = [eval7.Card(r + s) for r in RANKS for s in SUITS
            if (r + s) not in dead]
    needed = 5 - len(board_cards)
    wins = 0.0
    n = 0
    for _ in range(trials):
        vc1, vc2 = rng.choice(combos)
        if str(vc1) in dead or str(vc2) in dead:
            continue
        local_deck = [c for c in deck if c != vc1 and c != vc2]
        rng.shuffle(local_deck)
        runout = local_deck[:needed]
        full_board = board_cards + runout
        hero_score = eval7.evaluate(hero + full_board)
        vill_score = eval7.evaluate([vc1, vc2] + full_board)
        if hero_score > vill_score:
            wins += 1.0
        elif hero_score == vill_score:
            wins += 0.5
        n += 1
    return wins / n if n else 0.5


def hand_strength(hero_cards: Sequence[str], board: Sequence[str], trials: int = 200) -> float:
    """Equity vs a uniformly-random 2-card villain holding. Cheap baseline
    metric for postflop decisions when no read is available."""
    rng = random.Random(_stable_seed("hand_strength", tuple(hero_cards),
                                      tuple(board), trials))
    hero = [eval7.Card(c) for c in hero_cards]
    board_cards = [eval7.Card(c) for c in board]
    dead = list(hero_cards) + list(board)
    deck = [eval7.Card(r + s) for r in RANKS for s in SUITS
            if (r + s) not in dead]
    needed = 5 - len(board_cards)
    wins = 0.0
    n = 0
    for _ in range(trials):
        rng.shuffle(deck)
        vc1, vc2 = deck[0], deck[1]
        runout = deck[2:2 + needed]
        full_board = board_cards + runout
        hero_score = eval7.evaluate(hero + full_board)
        vill_score = eval7.evaluate([vc1, vc2] + full_board)
        if hero_score > vill_score:
            wins += 1.0
        elif hero_score == vill_score:
            wins += 0.5
        n += 1
    return wins / n if n else 0.5

```

File: /Users/farhad/Code/PokerBot/consult/artifacts/2026-06-03-qual2-patch/FINDINGS.md
```md
# Qualifier II patch — stack-off discipline fix (2026-06-03)

## Situation
- Thorp finished **#85 / 300+** in Qualifier I. Metric = **CHIP Δ / 100H** (rate). Top-64 cutoff ≈ **+1,355/100H**; Thorp **+679**.
- Patch window OPEN (~12h); one upload supersedes the active bot; portal upload form live for us. A **Qualifier II** re-runs patched bots.
- Ground truth pulled from portal.fullhousehackathon (auth = Brave Supabase cookie injected into agent-browser).

## Diagnosis (from 12 real completed matches / 6,915 hands)
- Thorp profile: **BUST 56%, SCOOP 0%, AF 5.45, CALL 6.4%** vs #1 `final` (AF 1.97, SCOOP 36%) — boom/bust, exploitable.
- Leak is concentrated, not diffuse: **16 all-ins, 12% won, net −81,149 chips**; 6 deep stack-offs (>10k) = −73,434. 90% of hands commit ≤533. `bot_errors = 0` (not crashes).
- Mechanism: deployed bot is the **elaborate equity-driven** version (NOT the simple `v_final.zip`). `src/postflop.py` "facing a bet" used `eq>=0.80 → raise current_bet*3`, where `eq = hand_strength` = **equity vs RANDOM**. On wet/paired boards vs a betting villain (range capped strong) this overstates us; re-raises compound into full-stack jams at ~12% real equity. Confirmed in hand 269 (32k in on 4-club board vs nut flush) and hand 65 (jam K-high flush `8d3d` into tens-full).

## Fix (surgical, `src/postflop.py` only)
- Cap re-raise size at pot-sized (no `current_bet*3` geometric blow-up).
- Gate any **large commitment** (`max(owed, raise_chips_in) ≥ 40% stack`) on **board-aware nuttedness** via `_can_commit`:
  - flush board → require the **nut flush** (or eq-vs-tight-range ≥0.92 for boats);
  - paired board → eq-vs-tight-range ≥0.80;
  - safe board → eq-vs-tight-range ≥0.55.
- Otherwise fold (or call only if ≤15% stack). Small-pot aggression and genuine nut stack-offs unchanged.

## Validation
- **Acceptance (real field hands)**: both bust hands now FOLD (8d3d eq_strong 0.70; Kc-flush/4-club 0.87). Nut AdJd, safe-board AA, big KK-set still COMMIT. (Trustworthy signal — real data.)
- **Gauntlet (all green)**: engine validator 4/4; import_audit; strategy-leakage; edge_cases 48/48; smoke 200/200 0 errors; LBR preflop 32.1 / aggregate 81.2 mbb/g (caps 100/200).
- **Regression proxies** (advisor: use only as crash/regression check): vs templates patched==baseline (no-op vs passive — surgical); h2h vs baseline −9.66 bb/100 CI crosses 0 (HU over-tightness artifact; game is 6-max). Leak-triggering field bots unavailable locally.

## Artifact
- `v_qual2_stackoff_fix.zip` sha256 `0ec835b6ca6acbafec44236c71e257832736730e330555aa02ab01ba84cfbac7`
- Built from PokerBot-claude worktree (elaborate deployed-equivalent) + the postflop fix. Baseline preserved (`postflop_baseline.py`).

## Residual risk
- Local proxies can't reproduce the real aggressive field, so the +EV magnitude is inferred from the real-hand replay, not measured. Fix is calibrated for 6-max (tight betting ranges); slightly too tight HU.

```

File: /Users/farhad/Code/PokerBot/consult/artifacts/2026-06-03-qual2-patch/postflop_patched.py
```py
"""Postflop strategy.

Flop / turn / river: equity-driven heuristics with board-texture awareness
and overlay-aware c-bet bluffing. Equity comes from `src.equity` (Monte Carlo
eval7); opponent reads come from `src.opponent_model`.

Trial counts kept small (≤ 280) so each call stays well under 50 ms — leaves
the 2 s decision budget with abundant headroom.

# Source: [[Cepheus-Bowling-2015]] — bucket-style state abstraction; the
#         heuristic plays the role of the abstracted bucket lookup until G3
#         CFR+ training replaces it (gated by AGENTS.md solver policy).
"""
from typing import List

from src.equity import hand_strength, equity_vs_range
from src.opponent_model import get_model
from src.sizing import legal_raise_total


# Lightweight villain range archetypes for equity_vs_range. Used as priors
# when no model is warm.
PRIOR_RANGE_TIGHT = ["88+", "AT+", "KQs", "KJs"]
PRIOR_RANGE_LOOSE = ["22+", "A2+", "K9+", "QT+", "JT", "T9s", "98s"]


def board_texture(board: List[str]) -> dict:
    """Return cheap structural features: wet/dry, paired, flush-y, straight-y."""
    if not board:
        return {"wet": False, "paired": False, "flush_draw": False, "straight_y": False,
                "high_card": False}
    ranks = [c[0] for c in board]
    suits = [c[1] for c in board]
    suit_counts = {s: suits.count(s) for s in set(suits)}
    rank_order = "23456789TJQKA"
    rvals = sorted(rank_order.index(r) for r in ranks)
    paired = len(set(ranks)) < len(ranks)
    flush_draw = max(suit_counts.values()) >= 2
    straight_y = (max(rvals) - min(rvals)) <= 4 and len(set(rvals)) >= 2
    high_card = any(r in "AKQ" for r in ranks)
    return {
        "wet": flush_draw or straight_y,
        "paired": paired,
        "flush_draw": flush_draw,
        "straight_y": straight_y,
        "high_card": high_card,
    }


def _opponent_seat(state: dict) -> int:
    me = state.get("seat_to_act", -1)
    for p in state.get("players", []):
        if p.get("seat") != me and not p.get("is_folded") and p.get("state") != "folded":
            return p.get("seat", -1)
    return -1


def _flush_suit(board):
    """Suit with 3+ cards on the board (a flush is possible), else None."""
    suits = [c[1] for c in board if isinstance(c, str) and len(c) >= 2]
    for s in set(suits):
        if suits.count(s) >= 3:
            return s
    return None


def _board_paired(board):
    ranks = [c[0] for c in board if isinstance(c, str) and len(c) >= 2]
    return len(set(ranks)) < len(ranks)


def _has_nut_flush(hole, board, suit):
    """True if we hold a made flush of `suit` using its nut (highest off-board) card."""
    if suit is None:
        return False
    board_suit = [c[0] for c in board if isinstance(c, str) and len(c) >= 2 and c[1] == suit]
    my_suit = [c[0] for c in hole if isinstance(c, str) and len(c) >= 2 and c[1] == suit]
    if len(board_suit) + len(my_suit) < 5:
        return False
    on_board = set(board_suit)
    for r in "AKQJT98765432":
        if r in on_board:
            continue
        return r in my_suit
    return False


def _can_commit(hole, board, eq_strong):
    """Stack-off discipline gate for LARGE commitments.

    Generic range strength is unreliable on coordinated boards (a non-nut flush
    rates well vs a non-flush-weighted range), so gate on board-nuttedness:
    flush board -> require the nut flush, or near-certain equity (boats);
    paired board -> require very high range-aware equity;
    safe board   -> a range-aware coin-flip+ is enough.
    """
    fs = _flush_suit(board)
    if fs is not None:
        if _has_nut_flush(hole, board, fs):
            return True
        return eq_strong >= 0.92
    if _board_paired(board):
        return eq_strong >= 0.80
    return eq_strong >= 0.55


def decide_postflop(game_state: dict, *, blueprint_only: bool = False) -> dict:
    """Equity-driven postflop decision. Always returns a legal action.

    `blueprint_only=True` skips the opponent-model overlay (used for the
    ablation benchmark to measure overlay contribution).
    """
    can_check = bool(game_state.get("can_check"))
    pot = int(game_state.get("pot", 0))
    my_stack = int(game_state.get("your_stack", 0))
    owed = int(game_state.get("amount_owed", 0))
    current_bet = int(game_state.get("current_bet", 0))
    street = game_state.get("street", "flop")
    hole = list(game_state.get("your_cards", []))
    board = list(game_state.get("community_cards", []))
    if my_stack <= 0:
        return {"action": "check"} if can_check else {"action": "call"}
    if len(hole) != 2:
        return {"action": "check"} if can_check else {"action": "fold"}

    texture = board_texture(board)
    model = get_model()
    opp = _opponent_seat(game_state)
    if blueprint_only or opp < 0:
        shift = {"widen_open": 0.0, "cbet_bluff_more": 0.0,
                 "value_thinner": 0.0, "bluff_catch_less": 0.0,
                 "tighten_open": 0.0, "fold_to_pressure_less": 0.0,
                 "value_widen_vs_aggro": 0.0}
        archetype = "unknown"
    else:
        shift = model.exploit_shift(opp)
        archetype = model.archetype(opp)

    # Higher trial counts give tighter equity estimates on close calls. At
    # ~20 µs/evaluate, 280 trials = ~6 ms — well under the 50 ms budget.
    base_trials = {"flop": 280, "turn": 220, "river": 180}.get(street, 200)
    eq = hand_strength(hole, board, trials=base_trials)

    # Pot odds.
    pot_odds = owed / (pot + owed) if (pot + owed) > 0 and owed > 0 else 0.0
    call_threshold = pot_odds + 0.03  # small implied-odds / variance buffer
    if archetype == "loose_passive":
        call_threshold -= shift.get("value_thinner", 0.0) * 0.3
    if shift.get("bluff_catch_less", 0.0) > 0 and street == "river":
        call_threshold += shift["bluff_catch_less"] * 0.3
    # Against hyper-aggressive villains: their large bets carry less info,
    # so we don't fold to pressure as easily on rivers with marginal hands.
    if shift.get("fold_to_pressure_less", 0.0) > 0 and street == "river":
        call_threshold -= shift["fold_to_pressure_less"] * 0.3

    value_threshold_thin = 0.70
    # Against aggressive villains, value-bet wider — their calls extend to
    # marginal hands we'd otherwise check.
    if shift.get("value_widen_vs_aggro", 0.0) > 0:
        value_threshold_thin -= shift["value_widen_vs_aggro"] * 0.2

    if can_check:
        if eq > value_threshold_thin:
            return legal_raise_total(current_bet + max(int(pot * 0.66), 1), game_state)
        if eq > 0.55:
            return legal_raise_total(current_bet + max(int(pot * 0.5), 1), game_state)
        cbet_bluff_prob = 0.30 + shift.get("cbet_bluff_more", 0.0)
        if street == "flop" and not texture["wet"] and texture["high_card"]:
            cbet_bluff_prob += 0.10
        if 0.25 < eq < 0.55 and cbet_bluff_prob > 0.35:
            return legal_raise_total(current_bet + max(int(pot * 0.5), 1), game_state)
        return {"action": "check"}

    # Facing a bet. `eq` is equity-vs-RANDOM, which overstates us when a villain
    # bets/raises (their range is capped strong, esp. on flush/paired boards).
    # The previous code re-raised to current_bet*3 off random equity, which
    # compounds in raise wars into full-stack jams at ~12% real equity (measured
    # qualifier leak: 16 all-ins, 12% won, -81k chips). Cap re-raise size and
    # gate every LARGE commitment on board-aware nuttedness (`_can_commit`).
    # Small-pot aggression and genuine nut stack-offs are unchanged.
    # Source: [[Libratus-Brown-Sandholm-2017]] — range-aware refinement.
    my_bet = int(game_state.get("your_bet_this_street", 0))
    commit_frac = 0.40
    eq_strong = equity_vs_range(hole, board, PRIOR_RANGE_TIGHT, trials=base_trials)

    if eq >= 0.80:
        raw_target = current_bet * 3 if current_bet > 0 else max(int(pot * 0.66), 1)
        capped_target = (min(raw_target, current_bet + max(pot, 1))
                         if current_bet > 0 else raw_target)
        raise_chips_in = max(capped_target - my_bet, 0)
        commit_chips = max(owed, raise_chips_in)
        if commit_chips >= commit_frac * my_stack and not _can_commit(hole, board, eq_strong):
            if eq >= call_threshold and owed <= 0.15 * my_stack:
                return {"action": "call"}
            return {"action": "fold"}
        return legal_raise_total(capped_target, game_state)

    if eq >= call_threshold:
        if owed >= commit_frac * my_stack and not _can_commit(hole, board, eq_strong):
            return {"action": "fold"}
        return {"action": "call"}
    return {"action": "fold"}

```

File: /Users/farhad/Code/PokerBot/consult/artifacts/2026-06-03-qual2-patch/acceptance_test.py
```py
from src.postflop import decide_postflop as dp
from src.equity import equity_vs_range
from src.postflop import PRIOR_RANGE_TIGHT
def S(**k):
    base=dict(can_check=False, your_bet_this_street=0, seat_to_act=4,
              players=[{"seat":4},{"seat":0,"is_folded":False,"state":"active"}])
    base.update(k); return base
cases={
 "1_hand65_8d3d_nonnut(LEAK->fold)": S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["8d","3d"],community_cards=["Qd","Kd","Td","Qh","Ah"]),
 "2_nut_control_AdJd(->commit)":     S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["Ad","Jd"],community_cards=["Qd","Kd","Td","Qh","Ah"]),
 "3_safe_small_AA(->raise)":         S(pot=300,your_stack=10000,amount_owed=150,current_bet=150,
        street="flop",your_cards=["Ah","Ad"],community_cards=["Kc","7d","2s"]),
 "4_safe_bigcommit_KKset(->commit)": S(pot=6000,your_stack=10000,amount_owed=5000,current_bet=5000,
        street="flop",your_cards=["Kh","Ks"],community_cards=["Kc","7d","2s"]),
 "5_hand269_Kflush_4club(LEAK->fold)":S(pot=8000,your_stack=25000,amount_owed=7000,current_bet=7195,
        your_bet_this_street=2712,street="river",your_cards=["Kc","4h"],
        community_cards=["7c","9c","2c","5c","3s"]),
 "6_boat_on_pairedflush(->commit)":  S(pot=9000,your_stack=18000,amount_owed=9000,current_bet=9000,
        street="river",your_cards=["Qc","Qs"],community_cards=["Qd","Kd","Td","Td","Ah"]),
}
for name,st in cases.items():
    es=equity_vs_range(st["your_cards"],st["community_cards"],PRIOR_RANGE_TIGHT,trials=180)
    a=dp(dict(st))
    print(f"{name:36s} eq_strong={es:.2f} -> {a}")

```

File: /Users/farhad/Code/PokerBot/consult/artifacts/2026-06-03-qual2-patch/postflop_baseline.py
```py
"""Postflop strategy.

Flop / turn / river: equity-driven heuristics with board-texture awareness
and overlay-aware c-bet bluffing. Equity comes from `src.equity` (Monte Carlo
eval7); opponent reads come from `src.opponent_model`.

Trial counts kept small (≤ 280) so each call stays well under 50 ms — leaves
the 2 s decision budget with abundant headroom.

# Source: [[Cepheus-Bowling-2015]] — bucket-style state abstraction; the
#         heuristic plays the role of the abstracted bucket lookup until G3
#         CFR+ training replaces it (gated by AGENTS.md solver policy).
"""
from typing import List

from src.equity import hand_strength
from src.opponent_model import get_model
from src.sizing import legal_raise_total


# Lightweight villain range archetypes for equity_vs_range. Used as priors
# when no model is warm.
PRIOR_RANGE_TIGHT = ["88+", "AT+", "KQs", "KJs"]
PRIOR_RANGE_LOOSE = ["22+", "A2+", "K9+", "QT+", "JT", "T9s", "98s"]


def board_texture(board: List[str]) -> dict:
    """Return cheap structural features: wet/dry, paired, flush-y, straight-y."""
    if not board:
        return {"wet": False, "paired": False, "flush_draw": False, "straight_y": False,
                "high_card": False}
    ranks = [c[0] for c in board]
    suits = [c[1] for c in board]
    suit_counts = {s: suits.count(s) for s in set(suits)}
    rank_order = "23456789TJQKA"
    rvals = sorted(rank_order.index(r) for r in ranks)
    paired = len(set(ranks)) < len(ranks)
    flush_draw = max(suit_counts.values()) >= 2
    straight_y = (max(rvals) - min(rvals)) <= 4 and len(set(rvals)) >= 2
    high_card = any(r in "AKQ" for r in ranks)
    return {
        "wet": flush_draw or straight_y,
        "paired": paired,
        "flush_draw": flush_draw,
        "straight_y": straight_y,
        "high_card": high_card,
    }


def _opponent_seat(state: dict) -> int:
    me = state.get("seat_to_act", -1)
    for p in state.get("players", []):
        if p.get("seat") != me and not p.get("is_folded") and p.get("state") != "folded":
            return p.get("seat", -1)
    return -1


def decide_postflop(game_state: dict, *, blueprint_only: bool = False) -> dict:
    """Equity-driven postflop decision. Always returns a legal action.

    `blueprint_only=True` skips the opponent-model overlay (used for the
    ablation benchmark to measure overlay contribution).
    """
    can_check = bool(game_state.get("can_check"))
    pot = int(game_state.get("pot", 0))
    my_stack = int(game_state.get("your_stack", 0))
    owed = int(game_state.get("amount_owed", 0))
    current_bet = int(game_state.get("current_bet", 0))
    street = game_state.get("street", "flop")
    hole = list(game_state.get("your_cards", []))
    board = list(game_state.get("community_cards", []))
    if my_stack <= 0:
        return {"action": "check"} if can_check else {"action": "call"}
    if len(hole) != 2:
        return {"action": "check"} if can_check else {"action": "fold"}

    texture = board_texture(board)
    model = get_model()
    opp = _opponent_seat(game_state)
    if blueprint_only or opp < 0:
        shift = {"widen_open": 0.0, "cbet_bluff_more": 0.0,
                 "value_thinner": 0.0, "bluff_catch_less": 0.0,
                 "tighten_open": 0.0, "fold_to_pressure_less": 0.0,
                 "value_widen_vs_aggro": 0.0}
        archetype = "unknown"
    else:
        shift = model.exploit_shift(opp)
        archetype = model.archetype(opp)

    # Higher trial counts give tighter equity estimates on close calls. At
    # ~20 µs/evaluate, 280 trials = ~6 ms — well under the 50 ms budget.
    base_trials = {"flop": 280, "turn": 220, "river": 180}.get(street, 200)
    eq = hand_strength(hole, board, trials=base_trials)

    # Pot odds.
    pot_odds = owed / (pot + owed) if (pot + owed) > 0 and owed > 0 else 0.0
    call_threshold = pot_odds + 0.03  # small implied-odds / variance buffer
    if archetype == "loose_passive":
        call_threshold -= shift.get("value_thinner", 0.0) * 0.3
    if shift.get("bluff_catch_less", 0.0) > 0 and street == "river":
        call_threshold += shift["bluff_catch_less"] * 0.3
    # Against hyper-aggressive villains: their large bets carry less info,
    # so we don't fold to pressure as easily on rivers with marginal hands.
    if shift.get("fold_to_pressure_less", 0.0) > 0 and street == "river":
        call_threshold -= shift["fold_to_pressure_less"] * 0.3

    value_threshold_thin = 0.70
    # Against aggressive villains, value-bet wider — their calls extend to
    # marginal hands we'd otherwise check.
    if shift.get("value_widen_vs_aggro", 0.0) > 0:
        value_threshold_thin -= shift["value_widen_vs_aggro"] * 0.2

    if can_check:
        if eq > value_threshold_thin:
            return legal_raise_total(current_bet + max(int(pot * 0.66), 1), game_state)
        if eq > 0.55:
            return legal_raise_total(current_bet + max(int(pot * 0.5), 1), game_state)
        cbet_bluff_prob = 0.30 + shift.get("cbet_bluff_more", 0.0)
        if street == "flop" and not texture["wet"] and texture["high_card"]:
            cbet_bluff_prob += 0.10
        if 0.25 < eq < 0.55 and cbet_bluff_prob > 0.35:
            return legal_raise_total(current_bet + max(int(pot * 0.5), 1), game_state)
        return {"action": "check"}

    # Facing a bet.
    if eq >= 0.80:
        target = current_bet * 3 if current_bet > 0 else max(int(pot * 0.66), 1)
        return legal_raise_total(target, game_state)
    if eq >= call_threshold:
        return {"action": "call"}
    return {"action": "fold"}

```

File: /Users/farhad/Code/PokerBot/consult/artifacts/2026-06-03-qual2-patch/opponents_top25_stats.md
```md
# Fullhouse 2026 — Qualifier I top-25 opponents (detailed stats)

Source: portal.fullhousehackathon.com `GET /api/bots/<bot_id>/stats` (authenticated session). Pulled 2026-06-03.
Ranking metric = `chip_per_100_hands` (mean rate). For reference, OUR bot **Thorp (#85)**: chip/100 **+679**, AF **5.45**, fold 58.9%, call 6.4%, raise 34.7%, bust **56%**, scoop **0%**, 25 matches.

| # | bot | chip/100 | avgΔ/match | win% | bust% | scoop% | AF | fold% | call% | raise% | avgRaise | maxRaise | sdWin% | matches | hands |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | final | 4697.34 | 17502 | 52 | 44 | 36 | 1.97 | 49.1 | 17.1 | 33.8 | 526 | 13500 | - | 25 | 9315 |
| 2 | gems_VC2 | 3965.87 | 17750 | 56 | 40 | 24 | 2.23 | 50.1 | 15.5 | 34.4 | 517 | 14096 | - | 25 | 11189 |
| 3 | Hyperion | 3738.76 | 15315 | 52 | 48 | 32 | 2.03 | 47.1 | 17.5 | 35.4 | 558 | 42412 | - | 25 | 10241 |
| 4 | 50CentRaise | 3659.69 | 12616 | 45.5 | 54.5 | 31.8 | 3.29 | 54.9 | 10.5 | 34.6 | 637 | 10227 | - | 22 | 7584 |
| 5 | BussBot | 3630.51 | 16051 | 50 | 50 | 29.2 | 1.08 | 50.1 | 24.1 | 25.9 | 716 | 25692 | - | 24 | 10611 |
| 6 | APEX | 3426.06 | 15050 | 54.2 | 45.8 | 25 | 2.46 | 51 | 14.2 | 34.8 | 476 | 30936 | - | 24 | 10543 |
| 7 | TheUnknown | 3323.33 | 11499 | 36 | 64 | 28 | 1 | 58.1 | 20.9 | 21 | 642 | 24120 | - | 25 | 8650 |
| 8 | Bot1 | 3120.93 | 11899 | 43.5 | 47.8 | 17.4 | 1.98 | 67.6 | 10.9 | 21.5 | 568 | 20935 | - | 23 | 8769 |
| 9 | +ev | 3057.76 | 14558 | 61.9 | 38.1 | 14.3 | 1.43 | 50.8 | 20.2 | 28.9 | 566 | 23275 | - | 21 | 9998 |
| 10 | BATNEEC | 2982.84 | 14925 | 59.1 | 31.8 | 9.1 | 3.08 | 67.2 | 8 | 24.7 | 536 | 11514 | - | 22 | 11008 |
| 11 | Javis | 2916.35 | 13405 | 56 | 40 | 20 | 2.72 | 44.3 | 15 | 40.7 | 411 | 30709 | - | 25 | 11491 |
| 12 | v16ship2 | 2786.14 | 13200 | 56 | 44 | 16 | 3.04 | 64.3 | 8.8 | 26.9 | 515 | 23062 | - | 25 | 11844 |
| 13 | Oxvard | 2747.25 | 10863 | 45.8 | 54.2 | 20.8 | 3.16 | 59.5 | 9.7 | 30.8 | 624 | 22656 | - | 24 | 9490 |
| 14 | FerdaBot | 2689.38 | 12110 | 48 | 44 | 24 | 2.64 | 58.4 | 11.4 | 30.1 | 627 | 24305 | - | 25 | 11257 |
| 15 | Foldilocks | 2596.21 | 10742 | 43.5 | 52.2 | 17.4 | 2.2 | 45.8 | 16.9 | 37.2 | 524 | 29283 | - | 23 | 9516 |
| 16 | AniBot | 2585.47 | 15226 | 64 | 32 | 8 | 1.84 | 64.5 | 12.5 | 23 | 437 | 15711 | - | 25 | 14723 |
| 17 | NecessarySkew | 2581.69 | 12499 | 50 | 45.8 | 16.7 | 2.36 | 54.9 | 13.4 | 31.7 | 591 | 23910 | - | 24 | 11619 |
| 18 | TheCrystalline | 2552.45 | 12240 | 47.8 | 43.5 | 17.4 | 2.97 | 69.6 | 7.7 | 22.8 | 601 | 21296 | - | 23 | 11029 |
| 19 | fluttershy | 2549.7 | 13080 | 58.3 | 41.7 | 12.5 | 5.28 | 62.7 | 5.9 | 31.4 | 481 | 29423 | - | 24 | 12312 |
| 20 | IveyBot | 2467.15 | 12035 | 58.3 | 37.5 | 12.5 | 1.54 | 64.6 | 14 | 21.5 | 736 | 24868 | - | 24 | 11707 |
| 21 | Quant | 2356.23 | 7847 | 34.8 | 60.9 | 21.7 | 1.42 | 58.6 | 17.1 | 24.3 | 721 | 11748 | - | 23 | 7660 |
| 22 | aSIAN iNTELLIGENCE | 2279.17 | 10930 | 50 | 45.8 | 8.3 | 4.2 | 60.9 | 7.5 | 31.6 | 452 | 25976 | - | 24 | 11510 |
| 23 | Polaris | 2275.1 | 10420 | 41.7 | 58.3 | 20.8 | 1.77 | 63 | 13.3 | 23.7 | 622 | 22170 | - | 24 | 10992 |
| 24 | Bot1 | 2227.1 | 9482 | 36 | 64 | 24 | 1.54 | 55.4 | 17.5 | 27.1 | 753 | 30774 | - | 25 | 10644 |

Columns: AF=aggression factor (raises/calls); avgRaise/maxRaise in chips (100=1bb); sdWin%=showdown win rate. All from publicly-visible hand histories; source code never exposed.

```
</file_contents>
<meta prompt 1 = "[Architect]">
You are producing an implementation-ready technical plan. The implementer will work from your plan without asking clarifying questions, so every design decision must be resolved, every touched component must be identified, and every behavioral change must be specified precisely.

Your job:
1. Analyze the requested change against the provided code — identify the relevant architecture, constraints, data flow, and extension points.
2. Decide whether this is best solved by a targeted change or a broader refactor, and justify that decision.
3. Produce a plan detailed enough that an engineer can implement it file-by-file without making design decisions of their own.

Hard constraints:
- Do not write production code, patches, diffs, or copy-paste-ready implementations.
- Stay in analysis and architecture mode only.
- Use illustrative snippets, interface shapes, sample signatures, state/data shapes, or pseudocode when they communicate the design more precisely than prose. Keep them partial — enough to remove ambiguity, not enough to copy-paste.
- Scale your response to the complexity of the request. Small, localized changes need short plans; only expand sections for changes that genuinely require the detail.

─── ANALYSIS ───

Current-state analysis (always include):
- Map the existing responsibilities, type relationships, ownership, data flow, and mutation points relevant to the request.
- Identify existing code that should be reused or extended — never duplicate what already exists without justification.
- Note hard constraints: API contracts, protocol conformances, state ownership rules, thread/actor isolation, persistence schemas, UI update mechanisms.
- When multiple subsystems interact, trace the call chain end-to-end and identify each transformation boundary.

─── DESIGN ───

Design standards — address only the standards relevant to the change; skip sections that don't apply:

1. New and modified components/types: For each, specify:
   - The name, kind (for example: class, interface, enum, record, service, module, controller), and why that kind fits the codebase and language.
   - The fields/properties/state it owns, including data shape, mutability, and ownership/lifecycle semantics.
   - Key callable interfaces or signatures, including inputs, outputs, and whether execution is synchronous/asynchronous or can fail.
   - Contracts it implements, extends, composes with, or depends on.
   - For closed sets of variants (for example enums, tagged unions, discriminated unions): all cases/variants and any attached data.
   - Where the component lives (file path) and who creates/owns its instances.

2. State and data flow: For each state change the plan introduces or modifies:
   - What triggers the change (user action, callback, notification, timer, stream event).
   - The exact path the data travels: source → transformations → destination.
   - Thread/actor/queue context at each step.
   - How downstream consumers observe the change (published property, delegate, notification, binding, callback).
   - What happens if the change arrives out of order, is duplicated, or is dropped.

3. API and interface changes: For each modified public/internal interface:
   - The before and after signatures (or new signature if additive).
   - Every call site that must be updated, grouped by file.
   - Backward-compatibility strategy if the interface is used by external consumers or persisted data.

4. Persistence and serialization: When the plan touches stored data:
   - Schema changes with exact field names, types, and defaults.
   - Migration strategy: how existing data is read, transformed, and re-persisted.
   - What happens when new code reads old data and when old code reads new data (if rollback is possible).

5. Concurrency and lifecycle:
   - Specify the execution model and safety boundaries for each new/modified component: thread affinity, event-loop/runtime constraints, isolation boundaries, queue/worker discipline, or thread-safety expectations as applicable.
   - Identify potential races, leaked references/resources, or lifecycle mismatches introduced by the change.
   - When operations are asynchronous, specify cancellation/abort behavior and what state remains after interruption.

6. Error handling and edge cases:
   - For each operation that can fail, specify what failures are possible and how they propagate.
   - Describe degraded-mode behavior: what the user sees, what state is preserved, what recovery is available.
   - Identify boundary conditions: empty collections, missing/null/optional values, first-run states, interrupted operations.

7. Algorithmic and logic-heavy work (include whenever the change involves non-trivial control flow, state machines, data transformations, or performance-sensitive paths):
   - Describe the algorithm step-by-step: inputs, outputs, invariants, and data structures.
   - Cover edge cases, failure modes, and performance characteristics (time/space complexity if relevant).
   - Explain why this approach over the most plausible alternatives.

8. Avoid unnecessary complexity:
   - Do not add layers, abstractions, or indirection without a concrete benefit identified in the plan.
   - Do not create parallel code paths — unify where possible.
   - Reuse existing patterns unless those patterns are themselves the problem.

─── OUTPUT ───

Structure your response as:

1. **Summary** — One paragraph: what changes, why, and the high-level approach.

2. **Current-state analysis** — How the relevant code works today. Trace the data/control flow end-to-end. Identify what is reusable and what is blocking.

3. **Design** — The core of the plan. Apply every applicable standard from above. Organize by logical component or subsystem, not by standard number. Each component section should cover types, state flow, interfaces, persistence, concurrency, and error handling as relevant to that component.

4. **File-by-file impact** — For every file that changes, list:
   - What changes (added/modified/removed types, methods, properties).
   - Why (which design decision drives this change).
   - Dependencies on other changes in this plan (ordering constraints).

5. **Risks and migration** — Include only when the change introduces breaking changes, data migration, or rollback concerns. Omit for additive or non-breaking work.

6. **Implementation order** — A numbered sequence of steps. Each step should be independently compilable and testable where possible. Call out steps that must be atomic (landed together).

Response discipline:
- Be specific to the provided code — reference actual type names, file paths, method names, and property names.
- Make every assumption explicit.
- Flag unknowns that must be validated during implementation, with a suggested validation approach.
- When a design decision has a non-obvious rationale, explain it in one sentence.
- Do not pad with generic advice. Every sentence should convey information the implementer needs.

Please proceed with your analysis based on the following <user instructions>
</meta prompt 1>
<user_instructions>
<task>
You are a world-class expert in poker AI and game theory (CFR/equilibrium vs exploitative play, range modeling, variance/EV, ICM) AND a pragmatic ML/software engineer. Critically and independently evaluate a fix we made to our 6-max No-Limit Hold'em tournament bot ("Thorp") during a hackathon patch window. Be rigorous, quantitative, and explicitly NON-HEDGING in your verdict.
</task>

<background>
Fullhouse Hackathon 2026, 6-max NLHE. Qualifier I is complete; a patch window is open to upload one improved bot for Qualifier II (top 64 of ~300 advance). Ranking metric = CHIP DELTA PER 100 HANDS (a mean/rate, "BB/100 equivalent") — NOT cumulative. Per-match payoff is asymmetric: max loss = your 10,000 starting stack (-10k floor), max win = the whole table (+50k ceiling). Constraints: 2s/decision, sandboxed (eval7/numpy/scipy/treys/sklearn, no network, no PyTorch).
</background>

<part1_problem_and_verification>
Result: Thorp finished #85/300+ at +679 chip-delta/100h (top-64 cutoff ~ +1,355).

Data + verification methodology (we authenticated to the portal and pulled our real qualifier hand histories as JSON + per-bot stats):
- Stat fingerprint: BUST 56% (lost full -10k), SCOOP 0% (won +50k), FOLD 58.9%, CALL 6.4%, AGGRESSION FACTOR 5.45. The #1 bot: AF 1.97, CALL 17%, SCOOP 36%. (The portal's own heuristic flags "very high AF + high fold% = exploitable" and "high bust% with high scoop% = boom/bust".)
- Hand-level analysis over 12 completed matches / 6,915 hands: the deficit is CONCENTRATED, not diffuse. ALL-INS: 16 total, win rate 12%, net -81,149 chips; the 6 deepest stack-offs (>10k committed) alone = -73,434. 90% of hands committed <=533 chips. bot_errors = 0 (no crashes/timeouts).
- Example bust hands (cards revealed in the histories): jammed a King-high flush (8d3d) into tens-full on board Qd Kd Td Qh Ah; put 32k in on a four-club board (7c 9c 2c 5c 3s) versus the nut flush.

Mathematical reasoning we used (please scrutinize each):
(a) The metric is a MEAN with an asymmetric payoff (-10k floor / +50k ceiling), so +EV variance is rate-positive. The lever is therefore killing -EV spew, NOT reducing variance globally. We explicitly rejected "just play less aggressively."
(b) A 12% all-in win rate implies we were getting stacks in as a large underdog (near drawing-dead) -> -EV spew, not coolers scattered around a +EV strategy. Cross-check: 56% bust + 0% scoop is the signature of getting-it-in-behind.
(c) Root cause in code (see equity.py + postflop_baseline.py): postflop "facing a bet" did `if eq >= 0.80: raise to current_bet*3`, where `eq = hand_strength()` = Monte-Carlo equity vs a UNIFORMLY RANDOM hand. Against a villain who is betting/raising (range conditioned on aggression, and capped strong on wet/paired boards), equity-vs-random is severely upward-biased; and current_bet*3 compounds geometrically across a re-raise war into an unintended full-stack jam.
(d) We weighted leaks by frequency x chips, discounted single coolers, and acknowledged 25 matches overfit trivially.
</part1_problem_and_verification>

<part2_fix_and_final_state>
Fix decisions + methodology (surgical, POSTFLOP-ONLY; see postflop_baseline.py vs postflop_patched.py):
- Cap re-raise size at pot-sized (current_bet + pot) to stop geometric escalation.
- Gate any LARGE commitment (chips the action commits, measured as max(owed, raise_chips_in), >= 40% of remaining stack) on a BOARD-AWARE nuttedness test `_can_commit(hole, board, eq_strong)`:
  * flush board (3+ to a suit) -> require the NUT flush (we hold the highest off-board card of that suit) OR range-aware equity >= 0.92 (covers boats);
  * paired board -> range-aware equity (`equity_vs_range` vs a tight betting range) >= 0.80;
  * safe board -> range-aware equity >= 0.55.
  If the gate fails: fold (or call only when price <= 15% stack). Small-pot aggression and genuine nut stack-offs are untouched.
- Rationale for board-nuttedness vs generic range strength: a non-nut flush still scores >0.55 vs a generic tight range that is not flush-weighted, so generic equity would NOT fold the worst spots; board nuttedness is the discriminator.

Verification of the fix:
- Acceptance (replayed real bust hands through patched code; see acceptance_test.py): both leak hands now FOLD; controls (nut flush, safe-board AA, big top-set) still COMMIT.
- Full gauntlet GREEN: engine validator 4/4; edge-cases 48/48; smoke 200/200 with 0 errors; LBR exploitability preflop 32.1 / aggregate 81.2 mbb/g (caps 100/200); no strategy/identity leakage; cold import 0.04s / 25MB.
- Regression proxies (treated as crash-checks only, since local self-play is the same proxy that mispredicted our rank): vs passive templates the patch is a NO-OP (byte-identical output -> confirms surgicality); head-to-head vs the unpatched baseline it is -9.66 bb/100 with a 95% CI crossing 0, which we attribute to heads-up ranges being wider than the 6-max field the gate is calibrated for.

Final state: built from our canonical known-good artifact (best_green) + this postflop fix ONLY (we deliberately excluded unreviewed experimental preflop WIP). It is UPLOADED, ACTIVE and validated on the portal for Qualifier II; the prior bot is superseded. The real-field +EV gain is INFERRED from the real-hand replay (removing ~ -81k of all-in losses from a +90k baseline), NOT directly measured — the leak-triggering opponents are not available locally.
</part2_fix_and_final_state>

<your_response>
1. ASSUMPTIONS: State the assumptions you are making based only on the context and files provided (about the engine, the field, the metric, the sample, and anything you cannot verify). Flag where an assumption, if wrong, would change your verdict.

2. NON-HEDGING VERDICT: Give a direct, decisive judgment on how well we (i) diagnosed the problem, (ii) verified it, and (iii) fixed it. Would you ship this? Specifically pressure-test:
   - the equity-vs-random -> equity-vs-range argument and whether `equity_vs_range` against a fixed "tight" prior is actually a sound proxy for a villain's aggression-conditioned, board-specific range;
   - the 40% commit threshold and the 0.55 / 0.80 / 0.92 bars + nut-flush detection (too tight? too loose? exploitable? any obvious failure cases, e.g. draws, blockers, multiway side-pots, short stacks);
   - the "assume a betting villain is strong" premise and its failure mode versus maniacs / bluff-heavy 6-max opponents — does the fix over-fold and bleed EV given the MEAN rate metric?
   - whether postflop-only scope is sufficient, or whether the preflop all-in/commit logic and sizing also need attention.
   Quantify expected impact where you can, and call out any reasoning error or unjustified leap in our methodology.

3. FORWARD LOOK: Our next stage is opponent recon (we can pull per-opponent stats and full hand histories from the portal for the whole field). Given that, recommend the highest-EV additional improvements — e.g. making the commit gate opponent-aware, targeted exploits of the weak field, preflop/sizing changes — and specify exactly what data to gather and what metrics/tests would justify each change before we re-upload.
</your_response>

Attached files: FINDINGS.md (full writeup), postflop_baseline.py and postflop_patched.py (before/after of the changed code), acceptance_test.py (verification harness), equity.py (hand_strength = equity-vs-random; equity_vs_range = range-aware Monte Carlo).

<data_appendix>
Additionally attached: opponents_top25_stats.md (and .json) — detailed playing-style stats for the Qualifier I TOP-25 field, pulled from the portal: chip/100, win/bust/scoop %, aggression factor, fold/call/raise %, avg/max raise sizing, showdown win %. Use this for the opponent-recon recommendations in part 3.

Headline contrast to scrutinize: the top bots run AF ~1.0–3.3 with 24–36% SCOOP and 10–24% CALL, whereas our (pre-fix) Thorp was AF 5.45 / 0% scoop / 6.4% call. This suggests the winners are NOT hyper-aggressive — they call more, reach more showdowns, and convert big pots. Factor this into whether our fix goes far enough and what to change next.

For full-field recon, the portal endpoints are (authenticated; Supabase session-cookie gated — an external model CANNOT fetch these without our cookie, and the access token expires ~hourly, so we pull and attach the data ourselves):
- per-bot stats: GET https://portal.fullhousehackathon.com/api/bots/<bot_id>/stats
- per-match hand histories: GET https://portal.fullhousehackathon.com/api/matches/<match_uuid>/export
- leaderboard: https://portal.fullhousehackathon.com/leaderboard (client-rendered; no public JSON API — /api/leaderboard is 404)
</data_appendix>
</user_instructions>
