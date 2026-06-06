# Overnight Thorp V2 — Field-Aware Commitment, Showdown Capture & Recon — Implementation Contract

**Date:** 2026-06-03 · **Mode:** Plan-only (no code/diffs) · **Target tree:** `~/Code/PokerBot-claude` worktree (see §0)

> Implementation contract for Repo Prompt worker chats. The eight required sections are the spine: **§1** current-state call-chain analysis · **§2** file-by-file plan · **§3** new interfaces & data schemas · **§4** test matrix · **§5** verification commands · **§6** merge order · **§7** rollback plan · **§8** work packets for Orchestrate. A short framing preamble (§0), Open Questions, and References bracket them.

---

## §0. Framing — verified tree reality (resolved decision)

Six read-only recon probes (2026-06-03) establish where the real bot lives, correcting the PRD's assumption of a live `src/` stack:

- **Canonical `~/Code/PokerBot/src` is SCAFFOLD-BASELINE.** `decide_postflop` returns check/fold ("Placeholder — Codex implements during G3"); `equity_vs_range` raises `NotImplementedError("G3")`; `sizing` has only `sizing_to_amount`; `opponent_model.features`→`{}`. `git`: canonical HEAD `src/` == tag `scaffold-baseline`. **Do not build V2 here.**
- **The REAL baseline is `~/Code/PokerBot-claude/src`** — byte-exact (SHA) match to `consult/artifacts/2026-06-03-qual2-patch/v_qual2_stackoff_fix.zip` for `equity.py`/`opponent_model.py`/`sizing.py`/`postflop.py`. The qual2 emergency patch (`_can_commit`, `commit_frac=0.40`, capped reraise) is **already integrated** at `PokerBot-claude/src/postflop.py:88,107`. **This worktree is the V2 working tree.**
- `~/Code/PokerBot-codex/src` is a divergent API (`sizing_to_amount`, `archetype_features`, no `legal_raise_total`/`hand_strength`) — not the baseline. `submissions/best_green.zip` is an older G2 baseline missing the patched APIs — not the baseline.
- **Decision (resolved):** all V2 source/tool/test edits land in the **`PokerBot-claude`** worktree; tools may *read* canonical `PokerBot/data/portal_histories/` and `consult/artifacts/2026-06-03-qual2-patch/`. This plan document lives in canonical `docs/plans/`. Locked rollback artifacts = the two qual2 zips (§7). The one unresolved provenance question (which qual2 zip actually shipped) is **Q1**, gated by **WP-0** before WP-3/WP-4.

---

## §1. Current-state call-chain analysis

### 1.1 Runtime `game_state` schema (verified — `postflop_patched.py`, `acceptance_test.py`, engine `to_public_dict`)
Decision-time keys read by strategy: `can_check`(bool), `pot`(int), `your_stack`(int), `amount_owed`(int), `current_bet`(int), `street`("preflop"|"flop"|"turn"|"river"), `your_cards`(list[str] len 2), `community_cards`(list[str]), `your_bet_this_street`(int), `seat_to_act`(int), `min_raise_to`(int), `players`(list of `{seat, bot_id, stack, is_folded?, state?}`).
**Opponent identity IS available**: `players[].bot_id` is a stable string (`docs/api-cheatsheet.md:28`; `ext/fullhouse-engine/engine/game.py:63-67`). `action_log` entries are only `{seat, action, amount}` (no bot_id) — bot_id is resolved by seat→bot_id mapping through `players[]`. The real `THORP_BOT_ID` (`1c0abfd8-c355-471b-8c7b-e5e75800ce04`) and 56 portal-history files confirm bot_ids are present and stable in histories.

### 1.2 Live call chain (`PokerBot-claude/src`)
```
bot.decide(gs)                                   bot.py:291   non-dict→fold; warmup→check; import-fail→_safe_fallback
  └─ run_with_budget(_strategy,_safe_fallback,gs) timeout_guard.py:25  soft-deadline; on exc/over-budget→fallback
       └─ _strategy(gs)                           bot.py:267   warmup→check; street routing
            ├─ get_model().observe_log(match_action_log, hand_id)  opponent_model.py:46          ← L4
            ├─ street=="preflop" → _preflop_action(gs)  bot.py:205
            │     └─ preflop_lookup.lookup(pos,hand,seq,widen_open,tighten_open,facing_bb_3bet_deep)  :42  ← L5
            │           └─ legal_raise_total(target, gs)  sizing.py:26  → {"action":"raise"/"all_in"/...}
            └─ else → decide_postflop(gs, *, blueprint_only=False)  postflop.py:107               ← L3 core
                  ├─ board_texture(board)          postflop.py:27   (→ moves to hand_features, L2)
                  ├─ _opponent_seat(gs)            postflop.py:50   (→ _opponent_key, L4)
                  ├─ model.exploit_shift(opp)/archetype(opp)  opponent_model.py:134/:117          ← L4 contract
                  ├─ eq = hand_strength(hole,board,trials)  equity.py:173   (equity-vs-RANDOM)
                  ├─ eq_strong = equity_vs_range(hole,board,PRIOR_RANGE_TIGHT)  equity.py:127  (eq_action)
                  │     └─ range_to_combos → expand_range_tag  equity.py:47   (parser defects, L2)
                  ├─ SITE A (eq≥0.80): capped raise (raw=current_bet*3, cap current_bet+pot), gated by _can_commit :88   → allow_raise (L3)
                  └─ SITE B (eq≥call_threshold): call, gated by _can_commit :88                                          → allow_call (L3)
  └─ _legalize_action(gs, action)                 bot.py:55   final legality backstop (UNCHANGED)
```

### 1.3 Defect map driving V2 (all `PokerBot-claude/src`, verified file:line)
1. **`_can_commit` texture order** (`postflop.py:88`): tests **flush before paired**, and overloads *both* raise- and call-permission through one predicate. A paired+flush board with a non-boat nut flush is mis-gated as committable. (NB: qual2 acceptance **case 2** `Ad Jd` on `Qd Kd Td Qh Ah` is a **royal flush** — `Ad Kd Qd Jd Td` — so it commits *correctly*; it is **not** the defect example. The genuine defect needs a constructed non-boat nut-flush-on-paired-flush spot — see §4.)
2. **`expand_range_tag` broad-plus/dash broken** (`equity.py:47-83`): `AT+`→only `ATs,ATo` (want AT,AJ,AQ,AK ×{s,o}); `K9+`→only `K9s,K9o`; `A2+`→only `A2s,A2o`; **`QJs-T9s`→`[]`** (dash branch handles pairs only). Working: `88+`, `A5s+`, bare `AK`→`AKs,AKo`, `88-22`. Corrupts `eq_action`.
3. **Determinism seed omits range** (`equity.py:138-142`): `_stable_seed("eq_vs_range", hero, board, trials)` excludes `villain_range` → different ranges reuse the same draw.
4. **Shift-contract gap** (`opponent_model.py:134-170`): `exploit_shift` emits only `{widen_open,cbet_bluff_more,value_thinner,bluff_catch_less}`, but `postflop.py` reads `value_widen_vs_aggro` & `fold_to_pressure_less` and `_preflop_action` reads `tighten_open` → **three silent no-op adjustment paths** (`.get(...,0.0)`).
5. **Seat-keyed, not bot_id** (`opponent_model.py:26,32` `defaultdict` by seat; global `_MODEL` `:175`): counters persist across matches on a process-global singleton; `bot_id` never read → cross-match state bleed. `observe_log` updates VPIP/PFR/bets/calls (`:84-96`); `fold_to_cbet` counters declared but never updated (no street in `match_action_log`). `archetype` is 5-way (`:117`: unknown/tight_aggressive/tight_passive/loose_aggressive/loose_passive; tight=vpip<0.22, agg=af>2.0|pfr>0.18; `WARMUP_HANDS=30`).
6. **Preflop tags by hand-membership only** (`preflop_lookup.lookup` `:42-136`): returns tags (open/iso_raise/threebet/fourbet/**all_in**) with no stack/SPR check; chip conversion happens in `bot._preflop_action`→`legal_raise_total`. `ranges.py` uses exact frozensets via `hand_in` (`:338`); `_expand` does not parse shorthand (`:20-24`) — independent of `expand_range_tag`. → L5 audit target.

### 1.4 Reused, not rebuilt (load-bearing — do NOT re-touch semantics)
`legal_raise_total` (`sizing.py:26`: reads `your_stack`/`your_bet_this_street`/`min_raise_to`; snaps below-min to `min_raise_to`; `chips_needed=target-my_bet`; `chips_needed≥stack`→`{"action":"all_in"}`; nonpositive→check/fold; else `{"action":"raise","amount":int(target)}` — `amount` is the engine TOTAL); `_legalize_action` (`bot.py:55`, final backstop); `run_with_budget`; `eval7` pre-warm at `equity.py:21-23`; `board_texture`. Tooling: **`tools/field_recon.py` already EXISTS and works** (770 lines, canonical PokerBot) — faithful engine-port reconstruction + `validate` + `emit` (writes `opponent_profiles.json`, `field_clusters.json`, `stackoff_decisions.csv`, `large_pot_decisions.csv`, `showdown_spots.csv`; clusters into maniac_boombust/LAG/loose_passive_station/TAG/nit_tight_passive). `tools/analyze_postflop_trap_prevalence.py` (schema-flexible loader). `replay.py` is a placeholder (`events`-based) → real portal replay in L6.

### 1.5 Targeted-vs-refactor stance
L2 (correctness) and L4 (model) are surgical edits to existing files. L3 is the **only** new pure module (`commitment.py`): the qual2 patch overloaded `_can_commit` across two call sites with different intents; V2 must (a) split call- from raise-permission, (b) make gating dynamic on stack/SPR, (c) keep gating **out of the overlay** so the ablation stays meaningful. A pure controller with unit tests is cheaper to verify than more `decide_postflop` branches. New module `hand_features.py` centralizes board/hand classification (today scattered as `_flush_suit`/`_board_paired`/`_has_nut_flush`/`board_texture`).

---

## §2. File-by-file implementation plan

### NEW — `src/hand_features.py`  *(L2 · WP-2)*
- **Why:** centralize board/hand classification; give `commitment.py` a made-hand category so the paired+flush rule can test "full-house-or-better."
- **Adds:** `classify_board(board)->BoardFeatures`, `classify_hand(hole,board)->HandFeatures` (§3). `made_category` via `eval7.handtype(eval7.evaluate(...))`. **WP-2 step 0 (blocking):** verify `eval7.handtype` exists in eval7 0.1.7; if absent, a manual rank/suit-count + straight detector is in-scope **here in WP-2** (do not discover this in L3).
- **Moves in:** `board_texture` (verbatim behavior, re-exported so `postflop` call sites are unchanged). Pure; no Monte-Carlo, no I/O.

### MODIFIED — `src/equity.py`  *(L2 · WP-2)*
- `expand_range_tag` (`:47`): fix the plus/dash branches — (a) **bare broad-plus** `XY+` → `XY,X(Y+1)…X(X-1)` each ×{s,o} (`AT+`→AT,AJ,AQ,AK; `K9+`→K9..KQ; `A2+`→A2..AK); (b) **offsuit-plus** `XYo+` → same ladder restricted to `o` (`K9o+`→K9o,KTo,KJo,KQo), mirroring the already-working suited-plus `A5s+` branch; (c) **suited/offsuit dash** `QJs-T9s`/`87o-54o` → decrement **both** ranks per step; (d) leave working cases (`88+`, `A5s+`, bare `AK`, `88-22`) byte-stable.
- `equity_vs_range` (`:127`): add `tuple(villain_range)` to the `_stable_seed("eq_vs_range",…)` args so range identity drives the draw. No behavior change otherwise (eval7 warmup, trials default preserved).

### NEW — `src/commitment.py`  *(L3 · WP-3)*
- **Why:** the dynamic, texture-aware stack-off controller. **Pure, deterministic, NO rollouts** — consumes the single `eq_action` (`eq_strong`) `decide_postflop` already computes (budget-neutral; protects the 2 s budget test).
- **Adds:** `stack_regime`, the `COMMIT_FRAC`/`SPR_CAP`/`EQ_FLOOR_*` tables, `allow_raise(...)`, `allow_call(...)` (§3). Encodes corrected texture priority (paired+flush → full-house-or-better OR `eq_action≥0.92`) and the short-regime bypass.
- **Invariant:** `allow_call ⊇ allow_raise` (whenever a raise is permitted, a call is too) — deny the raise, never invert.

### MODIFIED — `src/postflop.py`  *(L3 core · WP-3; L4 touch · WP-4)*
- Replace `_can_commit` **SITE A** (`eq≥0.80` raise branch): `commitment.allow_raise(...)`; on denial, downgrade to call iff `commitment.allow_call(...)` else fold (keep the existing `owed ≤ SHORT_CALL_ESCAPE_FRAC*stack` small-call escape).
- Replace `_can_commit` **SITE B** (`eq≥call_threshold` call branch): `commitment.allow_call(...)`.
- **Add `_effective_context(game_state, opp_seat) -> (effective_stack, spr, pot)`** in `postflop` (feeds `commitment` — resolves critique seam #1): `pot = game_state["pot"]` (decision-time, incl. villain's bet); `villain_stack = players[opp_seat]["stack"]` if present else `my_stack`; `effective_stack = min(my_stack, villain_stack)`; `spr = effective_stack / max(pot,1)`. `opp_seat` from `_opponent_key` (the existing `_opponent_seat` first-non-folded choice; multiway disambiguation is handled by passing `num_active_opponents` to `commitment`, which requires a nut class for any raise when `>1`). **Missing `players`/`stack` → `effective_stack = my_stack` (conservative; Q4).**
- Remove `_can_commit`, `_flush_suit`, `_board_paired`, `_has_nut_flush` (superseded); import `board_texture`/classifiers from `hand_features`.
- Hoist sizing magics to named constants (`VALUE_BET_THICK_FRAC=0.66`, `VALUE_BET_THIN_FRAC=0.50`, `CBET_BLUFF_FRAC=0.50`) — **values unchanged** to stay regression-safe.
- **L4 touch (WP-4):** `_opponent_seat`→`_opponent_key` (resolve `bot_id` from `players[]`); replace the hardcoded zero-shift literal with `from src.opponent_model import ZERO_SHIFT`; apply `model.risk_buffer(opp_key, street)` to `call_threshold` — **only when `not blueprint_only and opp known`**.
- **Blueprint invariant:** commit gating runs in **both** `blueprint_only` and overlay modes; `risk_buffer`/`exploit_shift` run only in overlay mode.

### `src/sizing.py`  — **NO CHANGE** *(L3 · WP-3)*
- Reuse existing helpers: `legal_raise_total` (`:26`) and **`pot_size_bet(pot, state, fraction)` (`:62`, already present)**. No new wrapper (critique §4: a `commit_raise_total` would duplicate `pot_size_bet`). `legal_raise_total` semantics stay frozen (hardening tests protect them).

### MODIFIED — `src/opponent_model.py`  *(L4 · WP-4)*
- Add `SHIFT_KEYS`/`ZERO_SHIFT` module constants (the 7-key contract — single source of truth, imported by `postflop`).
- `archetype` (`:117`): 5→10 taxonomy (§3), split **known-bot_id (rich, from `field_priors`)** vs **unknown (coarse vpip/pfr/af)**; keep `WARMUP_HANDS=30`, `unknown` pre-warmup.
- `exploit_shift` (`:134`): start from `dict(ZERO_SHIFT)`, fill per-archetype; **emit all 7 keys**, each bounded `|v|≤MAX_DEVIATION_PP`; populate the three currently-dead keys; **adjacent archetypes get near-identical vectors** (no action flip across a boundary).
- Add `risk_buffer(opp_key, street)->float` (per-archetype × street, bounded, `0.0` fallback).
- `__init__`/`observe_log` (`:26`/`:46`): key counters by `_identity(seat,players)=bot_id or f"seat:{seat}"`; add `players` arg to `observe_log`; seed counters from `field_priors` on first sight of a known `bot_id` (pseudo-hand blend, weight `PRIOR_PSEUDO_HANDS=20`).
- **Fallback (Q2):** missing/unstable `bot_id`→`seat:` keying + `_field_default`; never raises.

### MODIFIED — `src/bot.py`  *(L4 · WP-4)*
- `_strategy` (`:267`): pass `game_state.get("players")` into `observe_log(...)`.
- `_preflop_action` (`:205`): resolve opp `seat→identity` before `exploit_shift`; the now-live `tighten_open` activates the existing `preflop_lookup` tighten-vs-3bettor branch.
- **No change** to `decide`/`_legalize_action`/`decide_blueprint_only` control flow.

### NEW — `data/field_priors.json`  *(L4 · WP-4)*
- Derived in WP-1 from `field_recon emit` (`opponent_profiles.json`/`field_clusters.json`) + `opponents_top25_stats.json`. Schema §3. Loaded at import via `BOT_DATA_DIR` with `try/except→{}` fallback. Within `data/` ≤200 MB; copied by `package.py` (rglob); validator-clean (no `.py` in `data/`).

### MODIFIED — `tools/field_recon.py`  *(L1 · WP-1)* — **EXTEND the existing 770-line tool (not new)**
- It already does engine-faithful reconstruction + `validate` + `emit` (5 artifacts + clustering). **Add:** (a) `RECON_REPORT.md` writer (Thorp-vs-top-field fingerprint comparison) and (b) `replay_labels.json` (per-hand outcome/reveal labels for L6 replay). **Add** a `field_priors` derivation step that maps the existing 5-way clusters → the 10-archetype taxonomy (§3 mapping table) and writes `data/field_priors.json` candidate. **Reconcile** the hardcoded `THORP_BOT_ID` into a CLI/const. Bring a copy into `PokerBot-claude/tools/` so the worktree is self-contained. **No bot behavior change.**

### NEW — `tools/preflop_sizing_audit.py`  *(L5 · WP-5)*
- Replays portal spots / synthetic grids through `preflop_lookup.lookup`+`legal_raise_total` to detect the threshold→stack-off pattern preflop. **Audit-only.** Any preflop/sizing patch is gated on a high-confidence finding and mirrors the existing `_facing_bb_3bet_deep` PATCH-1 template (structural signal + bounded override + dedicated test). Writes `consult/artifacts/2026-06-03-preflop-sizing-audit/PREFLOP_AUDIT.md`.

### MODIFIED — `tools/replay.py`  *(L6 · WP-6)*
- Replace the `events` placeholder with real portal replay: reuse WP-1 reconstruction to rebuild decision-time `game_state`s from `hands[].action_log`, call `src.bot.decide`, print `action_under_test` vs `action_in_history` (+ `commitment` reason code). Supports baseline / patch / V2 three-way comparison via importable `decide`.

### NEW — tests (placement mirrors existing dirs)
`tests/edge_cases/`: `test_expand_range_tag.py`, `test_equity_seed.py`, `test_hand_features.py`, `test_commitment.py`, `test_commitment_acceptance.py`, `test_exploit_shift_contract.py`, `test_archetype_taxonomy.py`, `test_opponent_model_keying.py`, `test_blueprint_invariant.py`, `test_preflop_audit_guard.py` (only if WP-5 patches). `tests/integration/`: `test_field_recon.py`, `test_replay_portal.py`.

---

## §3. New interfaces & data schemas

### `hand_features.py`
```
# Only fields with a live consumer are materialized (critique §4 — trimmed from the PRD's full texture list).
BoardFeatures = {paired:bool, flush_possible:bool, flush_suit:str|None,   # commitment
                 wet:bool, straight_y:bool, high_card:bool, n_cards:int}   # postflop c-bet/value logic (board_texture parity)
HandFeatures  = {made_category:str,            # eval7.handtype label "Straight Flush".."High Card" (or manual fallback)
                 full_house_or_better:bool,    # commitment paired/paired-flush gate; handtype Quads/Straight-Flush ⇒ True (NOT just Full House) — case-2 royal commits through this
                 is_nut_flush:bool,            # commitment flush gate (reuses existing _has_nut_flush logic)
                 is_non_nut_flush:bool}        # allow_call "dominated non-nut" check
classify_board(board:list[str]) -> BoardFeatures      # pure; safe defaults on malformed cards
classify_hand(hole:list[str], board:list[str]) -> HandFeatures
active_opponent_count(game_state:dict) -> int         # players not folded, != hero → feeds num_active_opponents
```

### `commitment.py` (pure; no rollouts)
```
SHORT_STACK_CUTOFF = 2500 ; DEEP_STACK_CUTOFF = 10000
COMMIT_FRAC = {"medium":0.40, "deep":0.33}     # "short" has NO entry — it bypasses the strict gate (below)
SPR_CAP     = {"medium":2.0,  "deep":2.5}
EQ_FLOOR_PAIRED_FLUSH = 0.92 ; EQ_FLOOR_FLUSH = 0.92 ; EQ_FLOOR_PAIRED = 0.80 ; EQ_FLOOR_SAFE = 0.55
RISK_BUFFER_DEFAULT = 0.0
# (SHORT_CALL_ESCAPE_FRAC=0.15 lives in postflop.py, where the small-call escape branch is — not here.)

stack_regime(my_stack:int) -> "short"|"medium"|"deep"
# (effective_stack, spr, pot) are computed by postflop._effective_context (§2) and PASSED IN — commitment never reads game_state.
allow_raise(board_f, hand_f, eq_action, *, regime, spr, commit_chips, my_stack, call_threshold, num_active_opponents) -> bool
allow_call (board_f, hand_f, eq_action, *, regime, spr, owed,        my_stack, call_threshold, num_active_opponents) -> bool
```
**Corrected texture priority** inside the *strict* branch — fires only when `large == (commit_chips ≥ COMMIT_FRAC[regime]*my_stack)` **and** `spr > SPR_CAP[regime]`:
```
if board_f.paired and board_f.flush_possible:  return hand_f.full_house_or_better or eq_action >= EQ_FLOOR_PAIRED_FLUSH
if board_f.flush_possible:                      return hand_f.is_nut_flush        or eq_action >= EQ_FLOOR_FLUSH
if board_f.paired:                              return eq_action >= EQ_FLOOR_PAIRED
return eq_action >= EQ_FLOOR_SAFE
```
- Non-large or low-SPR raises bypass the strict gate (existing small-pot aggression unchanged). **Short** regime bypasses the strict branch entirely (pot-odds/`eq_action` only) — implements the PRD's "don't apply deep-stack non-nut folds to trivial-SPR short spots."
- **Multiway (`num_active_opponents > 1`):** `allow_raise` requires a nut class for the texture (`full_house_or_better`, or `is_nut_flush` on a flush board) — the `eq_action ≥ EQ_FLOOR` escape is disabled (PRD: multiway non-nut → fold/call only). `allow_call` still runs on pot-odds.
- `allow_call` on a **paired+flush** board with a bare nut flush is **permitted** when `eq_action ≥ call_threshold` (pot-odds + profile) — call yes, auto-stack no. Invariant `allow_call ⊇ allow_raise` enforced and property-tested.

### `opponent_model` shift contract (fixed 7-key dict; every archetype emits every key)
```
ZERO_SHIFT = {"widen_open":0.0,"tighten_open":0.0,"cbet_bluff_more":0.0,"value_thinner":0.0,
              "value_widen_vs_aggro":0.0,"bluff_catch_less":0.0,"fold_to_pressure_less":0.0}
SHIFT_KEYS = frozenset(ZERO_SHIFT)        # postflop.py IMPORTS this — no re-declared literal
MAX_DEVIATION_PP = 0.20                    # |any shift value| ≤ this
```

### 10-archetype taxonomy (observability-split; adjacency-stable vectors)
| group | archetypes | classifier source | shift family (illustrative) |
|---|---|---|---|
| neutral | `unknown` (pre-warm), `top_field_default` | live vpip/pfr/af or field default | ≈ zero |
| tight | `nit_value`, `fit_or_fold` | live (vpip<0.22, high fold-to-bet) | `widen_open`↑, `cbet_bluff_more`↑ |
| tight-aggro | `standard_TAG` | live (af 2–3.3, pfr>0.18) | `tighten_open`↑, `bluff_catch_less`↑ |
| loose-passive | `loose_passive_station` | live/field (call%↑, af<1.5) | `value_thinner`↑, `value_widen_vs_aggro`↑ |
| loose-aggro | `hyper_aggro`, `raise_monkey`, `overbluff_river` | live af↑ / field raise% / river_raise_freq↑ | `fold_to_pressure_less`↑, `value_widen_vs_aggro`↑ |
| structural | `short_stack_punter` | effective stack ≤ SHORT_STACK_CUTOFF + high all-in_freq | call-threshold only; **no raise-gate loosening** |

**Single-source enum (critique §3):** `ARCHETYPES = (...)` is ONE module constant in `opponent_model.py` (like `ZERO_SHIFT`), imported by `field_recon` so stored labels and runtime `archetype()` returns can never drift.

**Two-stage assignment (resolves the WP-1→WP-4 handoff):**
- **OFFLINE (`field_recon`, full histories):** rich inputs — AF, call/raise/fold%, river_raise_freq, large_bet_freq, showdown_reached/win_rate, allin_freq, allin_showdown_win_rate, scoop/bust — are computed per `bot_id` from the already-reconstructed per-decision records (street + action + all_in are present in `field_recon` today), and the resulting label is **stored** in `field_priors.json`.
- **RUNTIME:** known `bot_id` → use the **stored** label directly (no recompute). Unknown opponent → coarse live classification from `features()` only (vpip, pfr, af, fold_to_cbet) into the live-reachable subset {`unknown`(pre-warm), `top_field_default`, `nit_value`, `standard_TAG`, `loose_passive_station`, `hyper_aggro`}; the rich-only archetypes (`overbluff_river`, `raise_monkey`, `fit_or_fold`) need a stored prior, and `short_stack_punter` is assigned at runtime when effective stack ≤ `SHORT_STACK_CUTOFF` with high all-in frequency.
- **field_recon cluster → archetype map:** `maniac_boombust`→`hyper_aggro`; `LAG`→`hyper_aggro`(af≥2.5) else `standard_TAG`; `TAG`→`standard_TAG`; `loose_passive_station`→`loose_passive_station`; `nit_tight_passive`→`nit_value`; `insufficient_data`→`top_field_default`.

### `risk_buffer(opp_key, street)` — bounded additive equity buffer on `call_threshold`
Per-archetype × street, `|x| ≤ MAX_DEVIATION_PP`, `0.0` for `unknown`/`top_field_default`/exception. Defaults (river/turn/flop):
`top_field_default/unknown`: +0.06/+0.04/+0.03 · `nit_value`/`fit_or_fold`: +0.12/+0.08/+0.05 · `hyper_aggro`/`overbluff_river`: −0.05/−0.03/0.0 (lowers **call** threshold only; raise-gate untouched) · `loose_passive_station`: 0.0 calls, but enables thinner value bets (postflop value-threshold side).

### `data/field_priors.json`
```
{ "schema_version": 1, "generated_at": "2026-06-03",
  "_field_default": {"vpip":0.27,"pfr":0.20,"af":1.4,"call_pct":13.7,"raise_pct":29.1,"fold_pct":57.2,
                     "river_raise_freq":0.0,"large_bet_freq":0.0,"archetype":"top_field_default"},
  "<bot_id>": {"bot_name":str, "archetype":str,        # archetype is AUTHORITATIVE at runtime for a known bot_id
               "vpip":f,"pfr":f,"af":f,"call_pct":f,"raise_pct":f,"fold_pct":f,
               "river_raise_freq":f,"allin_freq":f,"big_commit_rate":f,"showdown_win_pct":f,
               "scoop_pct":f,"bust_pct":f,"chip_per_100":f,"prior_hands":int} }
```
Stored `archetype` is authoritative at runtime (assigned offline where the rich signals exist); the raw fields support warm-start blending + audit. Only fields `field_recon` actually emits — no invented metrics. `PRIOR_PSEUDO_HANDS=20` blend weight (decays as live hands accrue). If identity unstable (Q2/Q4), ship `_field_default` only and rely on live per-seat counters.

### Consolidated threshold ledger (value · home · validating metric · protecting test · fail-safe)
| Threshold | Default | Home | Validated by | Protected by | Fail-safe |
|---|---|---|---|---|---|
| stack regime cutoffs *(default; retune only if a regime is degenerate)* | short≤2500, deep>10000 | `commitment.py` | replay: every regime fires & buckets known spots correctly (not just firing rate) | `test_commitment` boundary | clamp → medium |
| `COMMIT_FRAC` *(inherits current `commit_frac`)* | medium 0.40, deep 0.33 | `commitment.py` | replay stackoff chips preserved (Gate E) | `test_commitment_acceptance` | deny-raise on uncertainty |
| `SPR_CAP` *(default; retune if degenerate)* | medium 2.0, deep 2.5 | `commitment.py` | LBR aggregate + bb/100 (correctness, not firing rate) | `test_commitment` | strict branch → deny |
| `EQ_FLOOR_*` | 0.92/0.92/0.80/0.55 | `commitment.py` | acceptance cases 1–6 + new spots | `test_commitment_acceptance` | higher floor = safer |
| `SHORT_CALL_ESCAPE_FRAC` | 0.15 | `postflop.py` | replay short-stack call-offs | `test_commitment` | small escape only |
| value-bet fractions | 0.66/0.50/0.50 | `postflop.py` | benchmark bb/100, fingerprint | reuse legality tests | `legal_raise_total` clamps |
| `WARMUP_HANDS` | 30 | `opponent_model.py` | ablation overlay delta | `test_archetype_taxonomy` | `unknown` pre-warm |
| `MAX_DEVIATION_PP` | 0.20 | `opponent_model.py` | LBR ≤100/≤200 mbb/g | `test_exploit_shift_contract` | clamp all keys |
| `risk_buffer[arch][street]` | table above | `opponent_model.py` | fingerprint call% + LBR | `test_archetype_taxonomy` (no action flip) | `0.0` on unknown/exc |
| `PRIOR_PSEUDO_HANDS` | 20 | `opponent_model.py` | recon vs live convergence | `test_opponent_model_keying` | live counters dominate |

---

## §4. Test matrix
| Area · WP | Test | Concrete acceptance |
|---|---|---|
| `expand_range_tag` · WP-2 | `test_expand_range_tag.py` | `AT+`→{ATs,ATo,AJs,AJo,AQs,AQo,AKs,AKo}; `K9o+`→{K9o,KTo,KJo,KQo}; `K9+`→K9..KQ ×{s,o}; `A2+`→A2..AK ×{s,o}; `QJs-T9s`→{QJs,JTs,T9s}; `88+`/`A5s+`/`AK`/`88-22` byte-unchanged; empty/garbage tag → `[]` (no raise) |
| equity seed · WP-2 | `test_equity_seed.py` | same `(hero,board,range,trials)` reproduces; two different ranges → independently seeded draws (not identical); dead-card removal after expansion |
| hand_features · WP-2 | `test_hand_features.py` | royal/SF, boat, nut-flush, 2nd-nut, non-nut flush, two-pair categorized; `full_house_or_better` true for case-2 (`AdJd` royal) & case-6 (`QcQs` boat) hands; malformed card → safe defaults; eval7.handtype-or-fallback verified |
| commitment · WP-3 | `test_commitment.py` | regimes at 2500/10000 boundaries; strict fires iff `large and spr>cap`; **paired+flush non-boat nut flush → `allow_raise=False, allow_call=True`**; `allow_call ⊇ allow_raise` property over random spots; short regime bypasses strict |
| acceptance · WP-3 | `test_commitment_acceptance.py` | **case 2 `AdJd`/`Qd Kd Td Qh Ah` → COMMIT** (royal); case 6 boat → COMMIT; cases 3,4 safe → raise/commit; cases 1,5 leak → fold; **NEW** non-boat nut flush on paired+flush (`AdKd`/`Qd 7d 2d Qh 5c`) → call/no-stack; **NEW** unpaired nut flush (`AdKd`/`Qd 7d 2d 9c 5h`) → COMMIT; **NEW** multiway non-nut flush → fold/call only |
| budget · WP-3 | reuse existing 2 s budget test | stays green (no new rollouts; `commitment` consumes existing `eq_action`) |
| shift contract · WP-4 | `test_exploit_shift_contract.py` | `set(exploit_shift(a))==SHIFT_KEYS` ∀ 10 archetypes; `|v|≤0.20` ∀ values; `postflop` imports `ZERO_SHIFT` (no literal drift) |
| taxonomy stability · WP-4 | `test_archetype_taxonomy.py` | 10 archetypes reachable; **no single archetype-boundary crossing changes the action** on a fixed stack-off spot suite |
| keying/fallback · WP-4 | `test_opponent_model_keying.py` | counters keyed by `bot_id`; missing `bot_id`→`seat:` key; field-prior warm-start blends; never raises across malformed `players` |
| blueprint invariant · WP-4 | `test_blueprint_invariant.py` | `decide` vs `decide_blueprint_only` identical on a stack-off spot with no overlay; commit gate fires identically in both modes |
| field_recon · WP-1 | `test_field_recon.py` | `validate` chip-conservation/reveal/segmentation OK on fixtures; `emit` writes per-`bot_id` aggregates + archetype; `field_priors.json` candidate deterministic across runs |
| replay · WP-6 | `test_replay_portal.py` | a portal `hands[].action_log` reconstructs ≥1 hero decision; prints under-test vs in-history + reason code without raising |
| edge cases · all | existing `tests/edge_cases/*` + new malformed-state cases (§ Error handling) | `pytest tests/edge_cases -x` exit 0 throughout |

**Gate mapping (PRD §5) → tests above:** A = the 6 qual2 cases · **B = ≥40 postflop spot tests (PRD floor)** in `test_commitment_acceptance.py` — the ~17 listed cases (paired-flush nut-only, four-flush 2nd-nut/nut, monotone non-nut draw, paired trips weak kicker, dry top-set, overpair vs small/huge, straight non-nut vs value, multiway non-nut, short-stack TP/nut-draw, river maniac/nit overbet bluffcatcher, station thin-value/river-raise) are the **required core**, expanded to ≥40 across {texture} × {stack regime: short/medium/deep} × {profile: nit_value/standard_TAG/loose_passive_station/hyper_aggro} × {facing size: small/pot/overbet} — this also supplies the regime/SPR cutoffs their *correctness* coverage · C = `test_expand_range_tag.py` · D = `test_field_recon.py` · E = WP-6 replay · F = §5 fingerprint · G = §5 gauntlet.

---

## §5. Verification commands
Run from the `PokerBot-claude` worktree (tools read canonical histories via `../PokerBot/...`).
```
# correctness (per WP)
pytest tests/edge_cases -x
pytest tests/integration -x
python tools/field_recon.py validate --hist ../PokerBot/data/portal_histories            # WP-1
python tools/field_recon.py emit --hist ../PokerBot/data/portal_histories --out consult/artifacts/2026-06-03-overnight-recon  # WP-1
python tools/preflop_sizing_audit.py --hist ../PokerBot/data/portal_histories            # WP-5
python tools/replay.py --hand ../PokerBot/data/portal_histories/<complete>.json          # WP-6

# import / package / sandbox (authoritative per CLAUDE.md)
python tools/import_audit.py
python tools/package.py --output submissions/v_overnight_candidate.zip --strict
python ext/fullhouse-engine/sandbox/validator.py submissions/v_overnight_candidate.zip
python tools/smoke_run.py --zip submissions/v_overnight_candidate.zip --hands 200

# strength / safety (paired seeds — benchmark variance policy)
python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42
python tools/benchmark.py --ablate-overlay --hands 10000 --paired-seed-base 42           # protects blueprint invariant
python tools/exploit_check.py                                                            # LBR ≤100 mbb/g preflop, ≤200 aggregate (CLAUDE.md caps)

# promote only if fully green (gate-H; overwrites best_green.zip)
python tools/promote_artifact.py --candidate submissions/v_overnight_candidate.zip \
  --destination submissions/best_green.zip --promote \
  --holdout-comparator-sha256 <current best_green sha256> --holdout-aggregate-delta-bb-per-100 <Δ≥0>
```
**Done-when floors (restore explicit bars — per `PROMPT.shared.md`/`AGENTS.md`):** each template **≥15 bb/100 with 95% CI lower-bound >0**; overlay-ablation **≥+3 bb/100**; self-play vs prior **≥+3 bb/100**; LBR within the CLAUDE.md caps above (≤100/≤200 mbb/g). **Fingerprint (Gate F):** AF<4.0, call%>9%, raise%≥20% from smoke/replay action mix. **Latency (PRD P0):** per-`decide()` <50 ms on ordinary postflop paths, <150 ms on rare large-commit paths — checked via `smoke_run` timing (sound by construction: no new rollouts; `commitment` reuses the existing `eq_action`). Append exact outputs to `STATUS.md` (append-only) + emit the proof-of-green block to the transcript.

---

## §6. Merge order
```
WP-0  Provenance & rebase gate (Q1)              ── blocks WP-3, WP-4
WP-1  field_recon extend + field_priors (L1)     ── independent; feeds WP-4, WP-6
WP-2  equity fixes + hand_features (L2)           ── independent; own green checkpoint; blocks WP-3
WP-3  commitment.py + postflop rewire (L3)        ── ATOMIC; needs WP-0, WP-2
WP-4  opponent_model + bot.py + field_priors (L4) ── ATOMIC; needs WP-0, WP-1; lands after WP-3 (shared postflop file)
WP-5  preflop/sizing audit (+ gated patch) (L5)   ── audit anytime after WP-2; patch only on high-confidence leak, after WP-4
WP-6  replay + gauntlet + package + promote (L6)  ── last; needs all
```
**Atomic bundles:** WP-3 (`postflop` cannot half-import `commitment`); WP-4 (7-key contract + `bot_id` keying + `ZERO_SHIFT` import are mutually dependent). WP-1 and WP-2 are independently shippable green checkpoints. WP-3 then WP-4 serialize because both edit `postflop.py`.

---

## §7. Rollback plan
- **Locked artifacts:** the two qual2 zips (`consult/artifacts/2026-06-03-qual2-patch/v_qual2_stackoff_fix.zip`, `…/v_qual2_SHIP_bestgreen+fix.zip`) + current `submissions/best_green.zip`. `best_green.zip` is overwritten **only** via the promote path (Gate-H); `.githooks/pre-commit` refuses verification-breaking `submissions/` commits (`FORCE_COMMIT=1` only for explicit rollback).
- **Per-bundle:** each atomic WP is one revertible commit guarded by acceptance + edge + LBR. `best_green.zip` stays untouched until WP-6 promotes a fully-green build, so reverting any WP cannot regress the shipped artifact.
- **WP-3/WP-4 specific:** if `--ablate-overlay` delta ≤ floor (blueprint invariant broken) or LBR breaches the band, revert that bundle; correctness WPs (WP-1/WP-2) remain.
- **Regression protocol (PRD §12):** append a `REGRESSION` entry to `STATUS.md` with the exact failing command, candidate sha, rollback-artifact sha; stop strategy changes until the cause is isolated.
- **Worst case:** ship the WP-0-confirmed qual2 zip unchanged. **Do not upload any V2 candidate that fails a P0 gate, even if a local benchmark improves.**

---

## §8. Work packets for Orchestrate
> Each packet: Goal · Done-when (concrete) · Key files (baseline file:line) · Dependencies · Size. Threshold defaults live in §3's ledger.

### WP-0 — Provenance & rebase gate *(S)*
- **Goal:** pin which qual2 zip actually shipped; rebase V2 baseline if it differs from `PokerBot-claude/src`.
- **Done-when:** the `STATUS.md` qual2 ship entry is identified; `unzip -l` + per-file diff of both zips' `src/` vs `PokerBot-claude/src` recorded; decision logged ("baseline = `v_qual2_stackoff_fix.zip` (==claude)" OR "rebase onto SHIP `opponent_model.py`/`sizing.py`, re-anchor WP-3/WP-4 line refs").
- **Key files:** `STATUS.md`, both qual2 zips, `opponent_model.py:1`, `sizing.py:1`. **Deps:** none. **Blocks:** WP-3, WP-4.

### WP-1 — field_recon extend + field_priors *(M)*
- **Goal:** produce the recon artifact set + runtime `field_priors.json`; **no bot behavior change**.
- **Done-when:** `field_recon.py validate` passes chip-conservation/reveal/segmentation on portal histories; `emit` additionally writes `RECON_REPORT.md` (Thorp-vs-top-field) + `replay_labels.json` + per-`bot_id` `river_raise_freq`/`allin_freq`/`big_commit_rate`/`showdown_win_pct` **aggregated from the existing per-decision records** (street+action+all_in are already reconstructed — no new parsing); a deterministic `data/field_priors.json` candidate (5-cluster→10-archetype mapped, §3) with the stored `archetype` per bot_id; `tests/integration/test_field_recon.py` green; a copy of the tool exists under `PokerBot-claude/tools/`.
- **Key files:** `tools/field_recon.py` (extend `emit`/`build_profiles`/`cluster_field`; `THORP_BOT_ID` const→CLI), reuse loaders from `analyze_postflop_trap_prevalence.py`; inputs `data/portal_histories/`, `opponents_top25_stats.json`. **Deps:** none. **Blocks:** WP-4 (data), WP-6 (replay reuse).

### WP-2 — Equity correctness + hand_features *(M)*
- **Goal:** correct `eq_action`; centralized made-hand classifier.
- **Done-when:** `test_expand_range_tag.py`, `test_equity_seed.py`, `test_hand_features.py` green; `eval7.handtype` validated (or manual fallback landed in `hand_features`); `import_audit` budget unchanged.
- **Key files:** `equity.py:47` `expand_range_tag`, `equity.py:127` `equity_vs_range` seed, `equity.py:85` `range_to_combos`; new `hand_features.py`; `postflop.py:27` `board_texture` (move + re-export). **Deps:** none. **Blocks:** WP-3.

### WP-3 — Commitment controller + postflop rewire *(L · ATOMIC)*
- **Goal:** split call- from raise-permission; fix paired+flush priority; dynamic stack/SPR gates; named sizing fractions.
- **Done-when:** `test_commitment.py` + `test_commitment_acceptance.py` green (case 2 & 6 COMMIT; new non-boat-nut-flush paired → call/no-stack; new unpaired-nut-flush → COMMIT; Gate-B suite); `_can_commit`/3 helpers removed from `postflop`; 2 s budget test green; `pytest tests/edge_cases -x` exit 0; LBR within band.
- **Key files:** new `commitment.py`; `postflop.py:107` SITE A/B + new `_effective_context` + `:88` removal + `commit_frac` deletion; `hand_features.py`; `sizing.py` (reuse `pot_size_bet`/`legal_raise_total`, **no edit**). **Deps:** WP-0, WP-2. **Blocks:** WP-4, WP-6.

### WP-4 — Opponent model: 10 archetypes + bot_id keying + contract sync *(L · ATOMIC)*
- **Goal:** complete 7-key shift contract; 10 archetypes (observability-split); `bot_id` keying + field priors; `risk_buffer`.
- **Done-when:** `test_exploit_shift_contract.py`, `test_archetype_taxonomy.py`, `test_opponent_model_keying.py`, `test_blueprint_invariant.py` green; `--ablate-overlay` delta ≥ floor; `postflop` imports `ZERO_SHIFT`; preflop `tighten_open` path reachable; `data/field_priors.json` packaged + validator-clean; fingerprint moves toward target (AF<4.0, call%>9%).
- **Key files:** `opponent_model.py:16/:26/:46/:101/:117/:134/:178` — **`_counts` key type seat(int)→identity(str) switches in lockstep across `observe_log`/`features`(:101)/`is_warm`/`archetype`/`exploit_shift`**; `bot.py:205/:267`; `postflop.py:50` `_opponent_seat`→`_opponent_key` + `ZERO_SHIFT` import; `data/field_priors.json` (from WP-1). **Deps:** WP-0, WP-1; serialize after WP-3.

### WP-5 — Preflop/sizing audit (+ gated patch) *(audit S; patch M)*
- **Goal:** detect the stack-off pattern preflop; patch **only** on a high-confidence leak.
- **Done-when:** `tools/preflop_sizing_audit.py` + `PREFLOP_AUDIT.md` report per-spot leak metrics (all preflop all-ins by hand/position/effective stack; 3bet/4bet freqs; call-3bet/4bet outcomes; SPR after line; chip delta by class); **if** a leak clears the confidence bar, a bounded override (PATCH-1 `_facing_bb_3bet_deep` template) lands with a dedicated test and no regression to `test_facing_bb_3bet.py`; **else** a documented "no-change" rationale.
- **Key files:** new `tools/preflop_sizing_audit.py`; `preflop_lookup.py:42`, `bot.py:205`, `sizing.py:26`, `ranges.py` (read). **Deps:** WP-2 (reuses WP-1 reconstruction); any patch after WP-4.

### WP-6 — Replay + gauntlet + package + promote *(M)*
- **Goal:** real portal replay (baseline/patch/V2); full verification; promote if green.
- **Done-when:** `tools/replay.py` replays portal hands vs `src.bot.decide` (`test_replay_portal.py` green) and emits the PRD §6 replay comparison (large_commit_count/chips, raise-to-stackoff count, non-nut-flush stackoffs, paired-board non-boat stackoffs, multiway large commits, short-stack call-offs) for the three policies; **Gate E** met (≥90% qual2 stackoff chips preserved on leak labels; zero non-nut-flush paired-board large stackoffs; zero paired-board nut-flush-only large raises; raise-to-stackoff count down vs baseline; call/check-call opportunities up vs patch); §5 gauntlet green on one `v_overnight_candidate.zip`; promote path passes; `STATUS.md` + proof-of-green appended.
- **Key files:** `tools/replay.py`; `tools/{benchmark,exploit_check,package,import_audit,smoke_run}.py` + promote path. **Deps:** all prior.

---

## Open Questions (load-bearing; each has a resolution method)
- **Q1 — provenance (blocks WP-3/WP-4):** which qual2 zip actually shipped — `v_qual2_stackoff_fix.zip` (==`PokerBot-claude/src`) or `v_qual2_SHIP_bestgreen+fix.zip` (different `opponent_model.py` 9214 B / `sizing.py` 2602 B)? **Method:** grep `STATUS.md` for the qual2 ship entry + `unzip -l`/diff both zips. **Branch:** if SHIP differs, rebase V2 onto SHIP `src/` and re-anchor line refs before WP-3. **(WP-0.)**
- **Q2 — bot_id stability:** does the live tournament expose the same `bot_id` strings seen in `portal_histories` (real `THORP_BOT_ID` confirmed present)? **Method:** confirm in `docs/tournament-spec.md`/engine. **Branch:** WP-4's `(bot_id or seat)` + `_field_default` fallback makes either answer safe; if unstable, ship `_field_default`-only priors.
- **Q4 — live villain stack + seat-stability (shapes WP-3 SPR & WP-4 keying):** does the live decision `game_state` expose `players[].stack` and a match-stable seat→`bot_id`? **Method:** `docs/tournament-spec.md` + `ext/fullhouse-engine/engine/game.py`. **Branch:** if `stack` absent → `commitment` effective_stack collapses to `my_stack` (SPR uses `my_stack` only); if seat→bot_id is not match-stable → WP-4 ships `_field_default`-only + resets live per-seat counters on `hand_num` reset.
- **Q5 — field_recon rich-stat coverage (may reorder WP-1↔WP-4):** does `field_recon.build_profiles` already expose per-`bot_id` river/all-in frequencies? **Method:** it already tracks `post_raise`/`all_ins`/`showdowns` per id and has per-decision `street`+`action`, so `river_raise_freq`/`allin_freq` are aggregations of existing data. **Branch:** WP-1 adds these aggregations in `emit`; if infeasible pre-qualifier, restrict the runtime taxonomy to the 6 live-reachable archetypes and store only those.
- **Q3 — resolved:** qual2 case 2 (`AdJd`/`Qd Kd Td Qh Ah`) is a **royal flush** → COMMIT (not the paired-flush defect). The genuine reclassification is the **new** non-boat nut-flush-on-paired-flush spot (call/no-stack) added in §4.

## References
- PRD: *Overnight Thorp V2* (this conversation). Baseline source: `PokerBot-claude/src/{bot,postflop,equity,opponent_model,sizing,preflop_lookup,ranges,timeout_guard}.py`.
- Artifacts: `consult/artifacts/2026-06-03-qual2-patch/{FINDINGS.md,postflop_baseline.py,postflop_patched.py,acceptance_test.py,opponents_top25_stats.json}`.
- Tooling: `tools/field_recon.py` (existing), `tools/analyze_postflop_trap_prevalence.py`, `tools/replay.py`. Engine: `ext/fullhouse-engine/{engine/game.py,sandbox/{validator.py,match.py}}`.
- Conventions/limits: `CLAUDE.md`, `docs/api-cheatsheet.md`, `docs/tournament-spec.md`, `AGENTS.md`, `PROMPT.shared.md`.
