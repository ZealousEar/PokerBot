# PATCH-2A: Bounded postflop EV-veto — Design

**Date:** 2026-05-28
**Scope:** `PokerBot-codex/src/postflop.py` only.
**Parent plan:** [`docs/plans/qualifier-finals-rollout-2026-05-27.md`](../plans/qualifier-finals-rollout-2026-05-27.md) §B7.
**Status:** Design ready for B7 implementation; gated on B4 "concentrated" verdict + B5 supportive verdict.

## Goal

Add a bounded EV-veto inside two existing postflop decision seams so that on (wet board) ∨ (multiway) ∨ (low SPR) ∨ (deep recent raises) ∨ (large bet-ratio bucket) spots, hero refuses commitments where realized equity under a discount stack falls below a passive-EV baseline + a tax-loaded safety cap. The veto fires only after the fixed-response cells and the flop blueprint have had a chance to act — neither is bypassed.

## Background

### The two seams (primary source: `PokerBot-codex/src/postflop.py`)

| Seam | Lines | Has equity? | Trigger condition | Current outputs that veto must filter |
|---|---|---|---|---|
| `_equity_turn_river_action()` | 333–365 | **yes** (`_equity_for_state` already ran; cached) | `street ∈ {turn, river}` and equity available within 200 ms budget | check / value-raise (2/3 pot) / call / fold |
| `_heuristic_postflop_action()` | 154–176 | **no** (equity unavailable / over budget / flop fallback) | invoked when blueprint and equity both return `None` | check / 2/3-pot raise / paired-board call / fold |

Both feed through `decide_postflop()` (367–380), whose order is **fixed**: `_patched_response_action()` → `_blueprint_flop_action()` → `_equity_turn_river_action()` → `_heuristic_postflop_action()`. The veto lives **inside** each of the two target functions, so the fixed-response cells (`_RESPONSE_FOLD_CELLS`, `_RESPONSE_CHECK_CELLS` at lines 67–98) and the flop blueprint (`_blueprint_flop_action` at lines 263–283) are never bypassed.

### The reference pattern (primary source: `ext/public-bots/famadeo/bots/codex_holdem/bot.py:2169–2232`)

Famadeo's `postflop_ev_veto(state, equity, bet_amount, owed, pot, stack, opponents, spr, wet)` shape:

1. Gate on `POSTFLOP_EV["enabled"]` and `equity < never_veto_equity` (0.82).
2. Compute `bet_ev` via fold-equity-weighted realized-equity model with discount stack: `multiway_equity_discount` (per extra opponent), `range_narrowing_discount` (from `pbs_range_narrowing`), `recent_raise_discount` (from `pbs_recent_raise_depth_s`), `wet_equity_discount`, `stackoff_equity_discount` (bet ≥ 0.75 × stack).
3. Compute `passive_ev` (check or call) using the same discount stack with `passive=True` (×0.45).
4. Required edge: `min_bet_edge + multiway_tax × (opponents−1) + wet_tax + low_spr_tax (spr ≤ 1.5)`.
5. Veto fires when `bet_ev + required_edge < passive_ev`; fallback action = check (if `owed=0`) or call/fold (sign of `call_ev`).
6. `postflop_call_veto(...)` is a thinner sibling for call-only decisions: realized-equity call-EV + multiway tax + large-call tax (pressure ≥ 0.32) + min_call_edge.

PATCH-2A adopts the **shape**, not the **constants**. Bucket-driven thresholds replace the fixed `min_bet_edge` / `min_call_edge`; the bet-ratio bucket replaces the single `stackoff` threshold so vladimir's off-grid sizings (0.27×, 1.72× pot per `ext/public-bots/vladimir/bots/vlad/deep_cfr_cpp/src/config.hpp`) bucket cleanly without copying his sizing tree.

### Helpers that postflop.py does NOT currently have

| Helper PATCH-2A needs | Closest existing | Why "closest" isn't enough |
|---|---|---|
| `multiway_count(game_state)` | `len(game_state["players"])` inline at 128–138 | Raw player count ignores active/folded status |
| `board_wetness(community_cards)` | `_flop_bucket()` at 190–200 | Hash-based; no semantic wet/dry distinction |
| `made_hand_class(hero, community_cards)` | `_hand_strength_bin()` at 205–248 | Mixes made-hand + draw bonuses into one float; veto needs them separable |
| `draw_proxy(hero, community_cards)` | `_hand_strength_bin()` lines 239–245 add texture bonuses | Same — needs separate axis |
| `recent_raise_depth(game_state)` | `game_state["action_log"]` present but unused in `postflop.py` | Shape exists (`[{"seat": int, "action": str}]` per `tests/edge_cases/test_overlay_bounded.py:129`); never consumed here |
| `bet_ratio_bucket(bet_or_owed, pot)` | none | Plan §B7 declares the bucket boundaries; veto routing depends on them |

### The load-bearing asymmetry between the two seams

`_equity_turn_river_action` has an equity number cached at entry, so the veto is a near-direct port of famadeo's `bet_ev` vs `passive_ev` comparison — cheap, no extra `equity_vs_range` call.

`_heuristic_postflop_action` runs **when equity is unavailable or over-budget**. The veto here MUST NOT call `equity_vs_range` again (that's why we're in the heuristic fallback — budget already exceeded or upstream returned `None`). Instead, the veto uses semantic proxies: `made_hand_class` and `draw_proxy` together stand in for equity in the EV compare, gated on bucket + multiway + wetness signals. This is **why §B7 lists both `made_hand_class` and `draw_proxy` as separate helpers** — they are the equity-free decision basis for seam 2.

### Existing tests the veto must not break

See parent plan §B7 for the canonical list. Fixture convention to mirror in new tests: `state(**overrides)` returning a dict with `action_log=[]`, `players=[]` defaults (see `test_postflop_wiring.py:11–28`).

## Approach

**Two veto functions, one bucket helper, four semantic helpers.** `_postflop_ev_veto_with_equity(...)` handles seam 1 (turn/river with cached equity). `_postflop_ev_veto_heuristic(...)` handles seam 2 (no equity; uses semantic proxies). Both consume the same bucket + multiway + wetness + recent-raise signals; they differ only in their EV basis (real equity vs. semantic proxy).

**Veto fires only on outputs that move chips beyond a free-option threshold.** A `{"action": "check"}` exit needs no veto (no chips committed). A `{"action": "fold"}` exit needs no veto (already passive). A `{"action": "call"}` or `{"action": "raise", ...}` exit is the veto target. The veto's fallback is always check/fold — never an alternative aggressive action.

**Blueprint outputs are NOT vetoed.** The flop blueprint at `_blueprint_flop_action()` (263–283) feeds through `decide_postflop()` before reaching the equity seam; per §B7's seam list, PATCH-2A does not intercept blueprint actions. Rationale: blueprint is trained against the abstracted game and is flop-only. If post-2A evidence shows blueprint raises into wet/multiway boards leak EV, that's PATCH-2B territory.

**Bet-ratio bucket is the vladimir-robustness primitive.** All decisions that flow through the veto first classify the bet (or owed amount, for facing-bet decisions) into one of five ratio buckets. Tax weights and `safety_cap_mbb` are bucket-keyed, so vladimir's 0.27× and 1.72× sizes route to the existing ≤0.33 and ≥1.5 buckets without copying his sizing tree.

**Heuristic-seam EV source is pinned to a closed-form per-`made_hand_class` heuristic.** `_semantic_ev_estimate(...)` (engineer-owned body, signature pinned below) returns `(action_ev, passive_ev)` from a closed-form mapping over `(made, draws, multiway, wet, spr, raise_depth, bucket)`. **No precomputed `.npz` table is shipped** (would breach the "no new `data/*.npz`" adjacent rule and risks the 4–6 h budget). **No runtime `equity_vs_range` call** is allowed inside the heuristic seam — entry to this seam means equity already returned `None` or was over budget; recomputing it defeats the seam's purpose.

## Veto pseudocode

### Seam 1 — `_equity_turn_river_action` (turn/river, equity available)

Insertion point: between equity computation and each chip-committing return (the value-raise return path at line 353 and the call return at lines 363–364 in the current implementation). The check/fold returns are untouched.

```python
# ... existing code through equity computation and pot-odds setup unchanged ...

# Compute veto signals ONCE per call (cheap; no further equity_vs_range).
mw = multiway_count(game_state)
wet = board_wetness(game_state.get("community_cards") or ())
raise_depth = recent_raise_depth(game_state)
spr = stack_total / max(pot, 1)

if game_state.get("can_check"):
    value_threshold = 0.36 if street == "turn" else 0.42
    if equity >= value_threshold:
        raise_action = _raise_two_thirds_pot(pot, min_raise_to, already_in, stack_total)
        if raise_action is not None:
            bucket = bet_ratio_bucket(raise_action["amount"] - already_in, pot)
            vetoed = _postflop_ev_veto_with_equity(
                game_state, equity=equity, action_chips=raise_action["amount"] - already_in,
                pot=pot, owed=0, stack=stack_total, multiway=mw, wet=wet,
                spr=spr, raise_depth=raise_depth, bucket=bucket,
            )
            if vetoed is not None:
                return vetoed                                # {"action": "check"}
            return raise_action
    return {"action": "check"}

owed = int(game_state.get("amount_owed") or 0)
if owed <= 0:
    return {"action": "check"}
pot_odds = owed / max(1, pot + owed)
margin = 0.08 if street == "turn" else 0.04
call_threshold = min(0.72, pot_odds + margin)
if equity >= call_threshold:
    bucket = bet_ratio_bucket(owed, pot)
    vetoed = _postflop_ev_veto_with_equity(
        game_state, equity=equity, action_chips=owed,
        pot=pot, owed=owed, stack=stack_total, multiway=mw, wet=wet,
        spr=spr, raise_depth=raise_depth, bucket=bucket,
    )
    if vetoed is not None:
        return vetoed                                        # {"action": "fold"}
    return {"action": "call"}
return {"action": "fold"}
```

`_postflop_ev_veto_with_equity` body (sketch — engineer owns the discount-stack constants and `safety_cap_mbb` values, but the shape is pinned):

```python
def _postflop_ev_veto_with_equity(game_state, *, equity, action_chips,
                                  pot, owed, stack, multiway, wet, spr,
                                  raise_depth, bucket):
    # never-veto floor — equivalent of famadeo's never_veto_equity = 0.82
    if equity >= _NEVER_VETO_EQUITY:
        return None
    realized_equity = _apply_realized_equity_discounts(
        equity, multiway=multiway, wet=wet, raise_depth=raise_depth,
        stackoff=(action_chips >= 0.75 * stack),
    )
    action_ev = realized_equity * (pot + action_chips) - (1 - realized_equity) * action_chips
    passive_ev = _passive_ev(equity, pot, owed, stack, multiway=multiway, wet=wet,
                             raise_depth=raise_depth)
    safety_cap = _SAFETY_CAP_MBB_BY_BUCKET[bucket]
    multiway_tax = max(0, multiway - 1) * _MULTIWAY_TAX_MBB
    wet_tax = _WET_TAX_MBB if wet else 0
    low_spr_tax = _LOW_SPR_TAX_MBB if spr <= 1.5 else 0
    required_edge = safety_cap + multiway_tax + wet_tax + low_spr_tax

    if action_ev + required_edge < passive_ev:
        if owed > 0:
            return {"action": "fold"}
        return {"action": "check"}
    return None
```

### Seam 2 — `_heuristic_postflop_action` (no equity available)

Insertion point: replaces (or wraps) the paired-board call return at the current line 176 and gates the value-raise return path at lines 161–163.

```python
def _heuristic_postflop_action(game_state: dict) -> dict:
    pot = int(game_state.get("pot") or 0)
    min_raise_to = int(game_state.get("min_raise_to") or 0)
    already_in = int(game_state.get("your_bet_this_street") or 0)
    stack_total = int(game_state.get("your_stack") or 0) + already_in

    mw = multiway_count(game_state)
    wet = board_wetness(game_state.get("community_cards") or ())
    made = made_hand_class(game_state.get("your_cards") or (),
                           game_state.get("community_cards") or ())
    draws = draw_proxy(game_state.get("your_cards") or (),
                      game_state.get("community_cards") or ())
    raise_depth = recent_raise_depth(game_state)
    spr = stack_total / max(pot, 1)

    if game_state.get("can_check"):
        raise_action = _raise_two_thirds_pot(pot, min_raise_to, already_in, stack_total)
        if raise_action is not None:
            bucket = bet_ratio_bucket(raise_action["amount"] - already_in, pot)
            vetoed = _postflop_ev_veto_heuristic(
                game_state, made=made, draws=draws, action_chips=raise_action["amount"] - already_in,
                pot=pot, owed=0, stack=stack_total, multiway=mw, wet=wet,
                spr=spr, raise_depth=raise_depth, bucket=bucket,
            )
            if vetoed is not None:
                return vetoed                                # {"action": "check"}
            return raise_action
        return {"action": "check"}

    owed = int(game_state.get("amount_owed") or 0)
    cards = tuple(game_state.get("your_cards") or ())
    board = tuple(game_state.get("community_cards") or ())
    paired = False
    if _valid_unique_cards(cards + board):
        ranks = [str(c)[0] for c in cards] + [str(c)[0] for c in board]
        paired = any(ranks.count(rank) >= 2 for rank in {str(c)[0] for c in cards})
    if paired and owed <= max(100, pot // 3):
        bucket = bet_ratio_bucket(owed, pot)
        vetoed = _postflop_ev_veto_heuristic(
            game_state, made=made, draws=draws, action_chips=owed,
            pot=pot, owed=owed, stack=stack_total, multiway=mw, wet=wet,
            spr=spr, raise_depth=raise_depth, bucket=bucket,
        )
        if vetoed is not None:
            return vetoed                                    # {"action": "fold"}
        return {"action": "call"}
    return {"action": "fold"}
```

`_postflop_ev_veto_heuristic` body (sketch — engineer owns the EV-by-(made, draws) lookup or formula):

```python
def _postflop_ev_veto_heuristic(game_state, *, made, draws, action_chips,
                                pot, owed, stack, multiway, wet, spr,
                                raise_depth, bucket):
    # Semantic-proxy EV: no equity_vs_range call. Pure made_hand_class + draw_proxy
    # mapped to a small lookup that yields (action_ev, passive_ev) given the
    # current multiway/wet/raise_depth/spr context. Engineer owns the table shape.
    action_ev, passive_ev = _semantic_ev_estimate(
        made=made, draws=draws, action_chips=action_chips, pot=pot, owed=owed,
        stack=stack, multiway=multiway, wet=wet, spr=spr, raise_depth=raise_depth,
    )
    safety_cap = _SAFETY_CAP_MBB_BY_BUCKET[bucket]
    multiway_tax = max(0, multiway - 1) * _MULTIWAY_TAX_MBB
    wet_tax = _WET_TAX_MBB if wet else 0
    low_spr_tax = _LOW_SPR_TAX_MBB if spr <= 1.5 else 0
    required_edge = safety_cap + multiway_tax + wet_tax + low_spr_tax

    if action_ev + required_edge < passive_ev:
        if owed > 0:
            return {"action": "fold"}
        return {"action": "check"}
    return None
```

### `decide_postflop()` is unchanged

The veto attaches inside the two seam functions, so the orchestrator at 367–380 stays as-is. This is the wiring promise: fixed-response cells and the flop blueprint reach their return statements before the veto can run.

## Helper signatures

Pinned. Engineer owns helper *bodies* and any internal constants, but the names and signatures are load-bearing for testability and seam interop.

```python
def multiway_count(game_state: dict) -> int:
    """Count of active (non-folded, non-busted) opponents + hero.

    Source-of-truth: game_state['players'] filtered by status. Returns 1 for HU.
    Schema note: per-player status fields are NOT guaranteed by every engine
    callback — production fixtures (`test_postflop_wiring.py:24`) ship
    `players=[]`. Required fallback: when status fields absent OR list empty,
    derive count from action_log presence (≥1 non-fold action this hand
    implies ≥2 players) and treat as HU otherwise. Never returns 0.
    """

def board_wetness(community_cards: Sequence[str]) -> bool:
    """Coarse wet/dry classifier.

    Semantic dimensions (engineer chooses weighting): two-tone or monotone,
    connected (≤4 gaps across all three flop cards), paired board.
    Returns True if any of {monotone, two-tone-connected, paired-with-flush-draw,
    three-to-straight} are present.
    """

def made_hand_class(hero: Sequence[str], community_cards: Sequence[str]) -> str:
    """One of {"air", "weak_pair", "mid_pair", "top_pair", "overpair",
    "two_pair", "set", "straight", "flush", "full_house_plus"}.

    Engineer owns the exact pair-rank cutoff between mid_pair and top_pair
    (e.g. via board-top-rank comparison). Returns "air" when input is malformed
    so callers can route safely.
    """

def draw_proxy(hero: Sequence[str], community_cards: Sequence[str]) -> str:
    """One of {"none", "gutshot", "oesd", "flush_draw", "combo_draw"}.

    'combo_draw' = oesd + flush_draw (8+9 outs). Engineer chooses how to count
    backdoor draws; recommended: backdoor returns "none".
    """

def recent_raise_depth(game_state: dict) -> int:
    """Count of raise actions in the current hand's action_log (this street + prior).

    Reads game_state['action_log']: list of dicts with at least {'action': str}.
    Returns 0 when log absent or empty. Used as a coarse aggression proxy in
    the veto's discount stack.
    """

def bet_ratio_bucket(bet_chips: int, pot: int) -> int:
    """Map bet/pot ratio to a bucket index (0..4).

    Buckets (load-bearing — see §B7 vladimir-robustness rationale):
       0 →  ratio ≤ 0.33
       1 →  0.33 <  ratio ≤ 0.66
       2 →  0.66 <  ratio ≤ 1.25
       3 →  1.25 <  ratio ≤ 1.49
       4 →  1.49 <  ratio
    pot ≤ 0 → returns 4 (treat as max-aggression bucket; rare degenerate case).
    bet_chips ≤ 0 → returns 0.
    """


def _semantic_ev_estimate(*, made: str, draws: str, action_chips: int,
                          pot: int, owed: int, stack: int,
                          multiway: int, wet: bool, spr: float,
                          raise_depth: int) -> tuple[float, float]:
    """Return (action_ev, passive_ev) for the heuristic seam — equity-free.

    Pinned signature; engineer owns the body. MUST NOT call equity_vs_range
    or any other equity-recomputation path; entry to the heuristic seam
    implies upstream equity returned None or was over-budget. Body shape
    pinned to a closed-form per-(made_hand_class, draw_proxy) lookup with
    context multipliers — no shipped data file, no runtime sampling.

    Output units match the rest of the veto's EV arithmetic (chips, not mbb).
    """
```

## Bet-ratio bucket boundaries (load-bearing)

Boundaries are inclusive-upper / exclusive-lower (`a < ratio ≤ b`); the user-brief notation `0.34–0.66` collapses to `0.33 < ratio ≤ 0.66` (a `0.333334` bet falls into bucket 1, not bucket 0).

| Bucket | Ratio (bet / pot) | Intent | vladimir touchpoint |
|---|---|---|---|
| 0 | `ratio ≤ 0.33` | Probe / blocker / small c-bet | covers his 0.27× pot probes |
| 1 | `0.33 < ratio ≤ 0.66` | Standard c-bet, polarized small | covers his 0.50× pot |
| 2 | `0.66 < ratio ≤ 1.25` | Standard value / commit zone | covers his 0.75× and 1.0× pot |
| 3 | `1.25 < ratio ≤ 1.49` | Overbet shading | covers his 1.33× pot |
| 4 | `1.49 < ratio` | Pure overbet / polarized big | covers his 1.72× pot and overbet jams |

Engineer owns `_SAFETY_CAP_MBB_BY_BUCKET` (and any per-bucket `villain_range` tightening). Bucket boundaries themselves are pinned — they implement the vladimir-robustness commitment from §B7 (we route his off-grid sizes into our existing buckets rather than expanding the action tree).

## Test naming schema

New file: `tests/edge_cases/test_postflop_veto.py`.

Test names follow `test_<street>__<position>__<hero_action>__<board_texture_bucket>` per the §B4 leak-key schema. Double-underscore separators are intentional — they map test cases 1:1 to entries in `consult/artifacts/2026-06-02-weakness-w1-famadeo/top5_leaks.md` once B4 produces it.

Examples (the exact set depends on B4's top-5 leaks; minimum 2 per §B7 acceptance):

```python
def test_turn__btn__cbet__wet_paired_multiway_vetoes_2_3_pot_raise():
    """When B4 surfaces a 'turn / BTN / cbet / wet_paired' leak,
    this test asserts the veto fires on the 2/3-pot raise path and falls
    back to check."""

def test_river__bb__call__wet_three_to_flush_vetoes_overbet_call():
    """When B4 surfaces a 'river / BB / call / wet_three_to_flush' leak,
    this test asserts the veto folds against an overbet (bucket 4) where
    the heuristic seam previously called paired-low-overbet."""

def test_flop__co__cbet__dry_rainbow_does_not_veto():
    """Negative-space test: dry-rainbow flop with top-pair-top-kicker
    must NOT fire the veto. Guards against over-triggering."""

def test_turn__sb__raise__multiway_oesd_only_vetoes_above_bucket_3():
    """Vladimir-robustness regression: oesd-only on multiway turn must
    veto when sizing lands in bucket 3+ but not in buckets 0–2."""
```

Each test references the `<street>__<position>__<hero_action>__<board_texture_bucket>` leak key it covers in its docstring's first line. `assert_legal` from `test_postflop_wiring.py:31–39` is the legality oracle.

## Do-not-touch list

Strict scope boundary for B7 implementation. Edits to any of these files invalidate the PATCH-2A gauntlet contract.

- `PokerBot-codex/src/bot.py` — entry point and overlay glue
- `PokerBot-codex/src/preflop_lookup.py` — preflop blueprint
- `PokerBot-codex/src/equity.py` — equity API (consumed as-is via `equity_vs_range`)
- `PokerBot-codex/src/opponent_model.py` — runtime archetype features and posterior

Intra-file (`src/postflop.py`) do-not-modify regions:

- `_RESPONSE_FOLD_CELLS` / `_RESPONSE_CHECK_CELLS` (lines 67–98) — fixed-response cells preserve the famadeo-killer 9s8s/Ah7d2c hand and other locked spots.
- `_patched_response_action()` (lines 140–151) — the dispatch into those cells.
- `_blueprint_flop_action()` (lines 263–283) — flop blueprint; veto explicitly does not intercept it.
- `_raise_two_thirds_pot()` (lines 102–110) and `_action_from_blueprint()` (lines 250–271) — sizing primitives; reused, not edited.
- `decide_postflop()` (lines 367–380) — the orchestrator; veto attaches INSIDE the two seam functions, not here.

Adjacent rules:
- No new `data/*.npz` artifacts (PATCH-2A is structural, not data-driven).
- No environment-variable branches (validator allows them but PATCH-2A is sandbox-pure).
- No opponent-identity strings or fingerprints (per §B7 explicit rule).
- No `ext/fullhouse-engine/` edits.
- No new `equity_vs_range` call inside `_heuristic_postflop_action` or `_semantic_ev_estimate` (see Approach).

## Open Questions

- **Should the veto record telemetry?** Decision currently silent. If post-2A debugging needs per-spot veto-fire counts, a one-line append to `STATUS.md` of `(leak_key, fired_count)` after the B8 gauntlet would surface drift. Engineer's call — adds zero runtime cost if behind a `_DEBUG` constant.
- **Veto interaction with the `paired and owed <= max(100, pot // 3)` short-circuit.** Current seam-2 logic calls on paired-board + cheap-owed. The veto can now veto that call. Is the empty-owed `check` exit also at risk under the wrong call? Current draft says no (check needs no veto), but if B4 surfaces a check-by-error leak, revisit.

## References

- Parent plan: [`docs/plans/qualifier-finals-rollout-2026-05-27.md`](../plans/qualifier-finals-rollout-2026-05-27.md) §B7.
- Veto reference pattern: `ext/public-bots/famadeo/bots/codex_holdem/bot.py:2169–2232` (bet veto), :2235–2253 (call veto).
- Seam 1 surface: `PokerBot-codex/src/postflop.py:333–365` (`_equity_turn_river_action`).
- Seam 2 surface: `PokerBot-codex/src/postflop.py:154–176` (`_heuristic_postflop_action`).
- Orchestrator (untouched): `PokerBot-codex/src/postflop.py:367–380` (`decide_postflop`).
- Fixed-response cells (preserved): `PokerBot-codex/src/postflop.py:67–98`.
- vladimir off-grid sizing source: `ext/public-bots/vladimir/bots/vlad/deep_cfr_cpp/src/config.hpp`.
- Existing test conventions: `PokerBot-codex/tests/edge_cases/test_postflop_wiring.py:11–39`.
- Action-log shape: `PokerBot-codex/tests/edge_cases/test_overlay_bounded.py:129` (list of `{"seat": int, "action": str}`).
- Leak-key schema origin: parent plan §B4 (`top5_leaks.md`).
