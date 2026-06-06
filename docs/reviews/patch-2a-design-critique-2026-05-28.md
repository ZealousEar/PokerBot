# PATCH-2A design critique — 2026-05-28

**Subject:** `docs/designs/patch-2a-design-2026-05-28.md` (~340 lines, blocks B7 ~4–6 h).
**Frame:** §B7 + pinned file:line refs. Seam choice fixed. Scope: critique only, no rewrites.
**Spot-checks:** `PokerBot-codex/src/postflop.py:152–176, 334–364, 367–380`; `ext/.../famadeo/bot.py:2169–2253`.

## 1. Top 3 under-specified seams

a) **`_semantic_ev_estimate` signature is not pinned** while less load-bearing helpers (`bet_ratio_bucket`, `multiway_count`) are. It is the entire EV basis for seam 2 (`_heuristic_postflop_action`) and appears only inside pseudocode (§"Veto pseudocode"). The user brief explicitly pins helper *signatures*; this one slips through. Open Question #2 then punts its data source (options a/b/c). Net: engineer owns both signature shape and data source for the load-bearing function. See §3 and §5 below.

b) **Intra-file do-not-touch is missing.** The "Do-not-touch list" pins other files (`bot.py`, `preflop_lookup.py`, `equity.py`, `opponent_model.py`) but does not say which regions inside `postflop.py` are off-limits. `_RESPONSE_FOLD_CELLS` / `_RESPONSE_CHECK_CELLS` (lines 65–95), `_blueprint_flop_action` (263–283), `_raise_two_thirds_pot` (118–125), and the fixed-response orchestrator path in `decide_postflop` (369–372) should be explicitly named as "preserve verbatim." Without that, an engineer mid-edit could "improve" `_raise_two_thirds_pot` and silently break the gauntlet contract.

c) **Line ranges are mostly correct but one is stale.** Spot-check of `PokerBot-codex/src/postflop.py`:
- `_heuristic_postflop_action`: def at **152** (doc says 154–176 → body window is right, def line off by 2). `161–163` value-raise path → **correct**. `174` paired-board call return → **incorrect**, actual return is at **line 176** (line 174 computes `paired`). Off by 2; the engineer will find it but the pseudocode's "current line 174" comment is misleading.
- `_equity_turn_river_action`: def at **334**, ends **364** (doc 333–365 → off by one each end). `348–352` value-raise range → covers lead-up; actual return is at line **353**. `363–364` call/fold pair → **correct**.
- `decide_postflop`: 367–380 → **correct**.

Two of four pseudocode insertion-point ranges (348–352, 174) describe the *neighborhood* rather than the return statement itself. Looks hand-counted from a single read, not stale per se — but the "line 174" reference for the paired-board call return should be corrected to 176 before B7 starts so the engineer doesn't have to second-guess.

## 2. Specificity balance

**Over-specified (per §B7 these are engineer-owned):**
- Pseudocode for `_postflop_ev_veto_with_equity` pre-commits the **additive shape** of `required_edge = safety_cap + multiway_tax + wet_tax + low_spr_tax`. §B7 explicitly gives the engineer "`safety_cap_mbb` value per bucket, exact `villain_range` construction." The famadeo reference (`bot.py:2215–2218`) uses exactly this additive shape, so it is defensible as pinning the structure, not the values — but the doc should say so explicitly. Currently reads as if the engineer just owns numbers.
- The full pseudocode bodies for both seams (~75 lines) restate surrounding code. A diff-style schematic ("insert veto call between line X and line Y; replace return Z") would be shorter and harder to drift from current code positions.

**Under-specified (load-bearing per user brief):**
- `_semantic_ev_estimate` signature (see §1a).
- The 0.34 / 0.67 / 1.26 bucket boundaries vs. the `0.33 < ratio ≤ 0.66` docstring style — the prose table is half-open intervals stated as decimals; the docstring uses strict inequalities. Bucket 0/1 split at `ratio = 0.34` is ambiguous between the two readings. Trivial fix; pin one form.
- Test-name schema is pinned (`<street>__<position>__<hero_action>__<board_texture_bucket>`) but the minimum-2 acceptance condition isn't tied to specific leak categories. §B7 says "≥2 new edge-case tests cover the leak names that B4 emitted" — that's the real anchor. The four example tests in §"Test naming schema" should be marked as illustrative, not minimum.

## 3. Contradictions / missing dependencies

a) **Veto vs `_patched_response_action` route — clean.** `decide_postflop` short-circuits on patched cells before reaching either seam (lines 369–371). All patched cells are exact-spot (turn/river `(cards, board, pot, current_bet, owed, can_check, players)` tuples), so the veto's class-based logic and the cell match never overlap. The doc's claim that fixed-response cells are preserved is correct.

b) **"No equity recomputation in seam 2" is intent-only, not enforceable.** The rule appears in prose at §"The load-bearing asymmetry" but is not restated as a banned operation in §"Do-not-touch" or in the `_postflop_ev_veto_heuristic` signature. Option (b) under Open Question #2 ("pre-computed offline via `equity_vs_range`") respects the rule because it ships as constants, but an over-eager engineer reading only the pseudocode could call `equity_vs_range` at runtime from `_semantic_ev_estimate`. **Add one line: "`_postflop_ev_veto_heuristic` and its callees MUST NOT call `equity_vs_range` at runtime."**

c) **`multiway_count` assumes a schema not verified.** Docstring says "filtered by status. Returns 1 for HU. Falls back to `len(game_state['players'])` when status fields absent." Existing `postflop.py` only reads `len(players)` (lines 128–138 are not present in current `postflop.py` — that range is the `_RESPONSE_FOLD_CELLS` tuples). The schema of per-player status fields is asserted but not cited. Either pin the fallback as the primary path or flag this as an assumption to verify in B7 implementation.

d) **No do-not-touch breach in the pseudocode.** All edits are intra-`postflop.py`. No reads from `equity.py` beyond the existing `equity_vs_range` import that `_equity_turn_river_action` already uses. Clean.

## 4. Risk of over-planning

For a ~4–6 h B7 budget, ~340 lines of design is heavy. Sections that can be **cut without losing the wiring promise:**

- §"Background → The reference pattern" (~35 lines): restates famadeo's `postflop_ev_veto` shape, which is already pinned at `bot.py:2169–2232` in §B7. Replace with one sentence + the file:line ref.
- §"Background → Helpers that postflop.py does NOT currently have" (~25 lines table): only the "why closest isn't enough" column is novel; the helper list is restated in §"Helper signatures." Cut the table; keep the signatures section.
- §"Background → The load-bearing asymmetry" (~20 lines): collapses to "Seam 1 has cached equity → direct EV port. Seam 2 has no equity → semantic proxies. That is why `made_hand_class` and `draw_proxy` are separate axes."
- §"Existing tests the veto must not break" (~5 lines): redundant with §B7's "all existing postflop/equity/LBR tests pass."

Estimated saving: ~85 lines (~25 %) without touching the load-bearing pseudocode, signatures, bucket boundaries, do-not-touch, or test schema. Recommend the engineer time-boxes themselves to the diff-shaped sections (§"Helper signatures", §"Bet-ratio bucket boundaries", §"Do-not-touch list", and the two pseudocode block insertion points) and treats the rest as reading material.

## 5. Open Questions that should be resolved here

- **Q1 (telemetry):** correctly punted. Zero-cost behind `_DEBUG`; doesn't change implementation order.
- **Q2 (`_semantic_ev_estimate` data source):** **should be resolved before B7 starts.** Option (b) "pre-computed offline via `equity_vs_range`" requires an extra offline precompute step that brushes against the "no new `data/*.npz` artifacts" adjacent rule (it would either ship as a Python-literal table in `postflop.py` or as an `.npz`). Option (c) "crude per-`made_hand_class` heuristic" fits the 4–6 h budget. Option (a) "hard-coded from textbook ranges" is in between. The doc recommends "start with (c)"; **promote that to a pinned decision** so the engineer doesn't waste budget evaluating (b). If (b) is later found necessary, that becomes PATCH-2B scope (parallel to §C1).
- **Q3 (veto interaction with paired-board shortcut):** correctly punted to B8 observation.

## 6. Re: skipping the workflow's Phase 4 `context_builder` pass

**Defensible substitution, with three small gaps to spot-check during B7 implementation:**
1. `game_state['players']` per-player status schema (referenced by `multiway_count` docstring) is asserted but not verified — engineer should confirm before writing the helper body.
2. `_blueprint_flop_action` downstream behavior on wet/multiway flop is referenced as "PATCH-2B territory" but never read; if its outputs include 2/3-pot raises into wet boards, the seam-1 veto cannot see them. Worth a one-line read.
3. Fixed-response cell coverage (lines 65–95) is enumerated only for `(turn, 8s6s, ...)` and `(river, Qs Kd, ...)` spots; the design says "cells are preserved" but doesn't enumerate which streets they cover. Spot-checked: cells exist only for turn/river spots in the current file. Safe; no overlap with seam-2 (`_heuristic_postflop_action` runs after blueprint, and patched cells short-circuit even earlier).

`context_builder` would likely have caught (1) and (2) at zero cost. (3) the design got right by luck of cited ranges. The substitution is acceptable for a structural patch with pinned file:line refs, but not for a wider-scope patch.

---

**Bottom line:** Design is implementable as-is, but three pre-B7 fixes would protect the 4–6 h budget:
1. Pin `_semantic_ev_estimate` signature in §"Helper signatures" and resolve Open Question #2 to option (c).
2. Correct the "line 174" reference (paired-board call return is at line 176).
3. Add `postflop.py` intra-file do-not-touch zones (`_RESPONSE_*_CELLS`, `_blueprint_flop_action`, `_raise_two_thirds_pot`, `decide_postflop` orchestrator path) and the "no runtime `equity_vs_range` in seam 2" rule.

Cut the ~85 lines of restated-from-§B7 background to reduce drift risk during implementation.
