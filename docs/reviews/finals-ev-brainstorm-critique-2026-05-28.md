# Critique — Finals-EV Brainstorm (2026-05-27)

Reviewed `docs/plans/finals-ev-brainstorm-2026-05-27.md` against `prompt-exports/oracle-plan-2026-05-28-001156-finals-ev-brainstorm-bd2c.md`. The plan is ~95% verbatim from the export (only an Open Questions block + References were added, and section A's idea-count header was corrected 12→15). Calibration: plan locks decisions/seams; the implementing agent owns tactical constants.

## 1. Top 3 under-specified seams

- **S1 — `_villain_combos_from_canonical` algorithm is missing (A-T2).** The plan names the signature `(canon_set: frozenset[str], known_cards: set[str]) -> tuple[tuple[str,str], ...]` and says it "expands `ranges.py` PREMIUM/STRONG_CONTINUE to concrete two-card combos compatible with `equity_vs_range`" — but the expansion rules (`"AKs"` → 4 suited combos, `"AKo"` → 12 offsuit, `"AA"` → 6 pair combos, with blocker exclusion against `known_cards`) are nowhere stated. A-T2's entire exploit value rides on this expansion: if it returns 169 unique strings or skips blocker filtering, the tightened-range equity is garbage and `min(equity_random, equity_tight)` is noise. **Minimum addition:** 4-line pseudocode for canonical→combos with blocker filter, or an explicit citation of an existing expander in `ranges.py`.

- **S2 — `_bet_ev`'s `fold_prob` source is undefined (A-T1).** Idea #7 declares `_bet_ev(equity, bet, pot, fold_prob)` and A-T1's check-branch sketch compares `_bet_ev(equity, bet=⅔ pot, ...) < _passive_ev(equity, owed=0, pot) + safety_cap_mbb[bucket]`. Neither location says where `fold_prob` comes from. The famadeo reference at `ext/public-bots/famadeo/bots/codex_holdem/bot.py:2140-2161` derives it from range bucket inference — exactly the surface PATCH-2A drops to stay inside 90–130 LOC. Without a `fold_prob` model, the comparison collapses to `equity*pot - bet*(1−equity)` (zero-fold pessimism) and `safety_cap_mbb` becomes the only knob. **Minimum addition:** either name a static fold_prob table keyed by `bucket` (e.g., `{tiny:0.55, small:0.45, mid:0.30, large:0.20, huge:0.10}`), or drop the parameter and document the no-fold-equity simplification.

- **S3 — C-T2's `_LAST_POSTERIOR` has no in-plan consumer.** C-T2 is sold as "structural enabler for C-T1 modulation, B-T3, A-T1 veto sharpening." Inspection: C-T1 modulates inside `opponent_model.py` before reaching postflop, B-T3 uses only bet-ratio/wet/multiway, A-T1's `safety_cap_mbb` is static (C-T3 modulates via `_FINALS_PRIORS`, not posterior). The only actual posterior consumer is section C idea **#11 ("Posterior-bounded veto strength") which did not make top-3**. The plan lands hidden module-level state with no top-3 reader. **Minimum addition:** either promote #11 into A-T1's veto block (`safety_cap_mbb *= (1.0 + 0.3*(top_probability−0.5))`) and cite the read site, or cut C-T2 from the top-3 entirely.

## 2. Specificity balance

- **Over-specified (engineer should own):** `safety_cap_mbb = {tiny:40, small:80, mid:120, large:180, huge:260}` — exact mbb thresholds with rationale "¼ of famadeo's `:2210-2218`"; these belong in a calibration sweep, not a plan. Same for A-T2's `80 + 80` trial split (depends on venv MC variance) and C-T3's VPIP cutoffs `< 0.22 ⇒ 2.0` / `> 0.30 ⇒ 3.0` (priors shape unknown until 2026-06-02 morning).
- **Misleading "reuse" claim (A-T1 idea #4):** says `_board_wetness(board)` reuses the suit/rank vectors at `postflop.py:239-245`, but those vectors are computed over **hero+board combined cards** inside `_hand_strength_bin`, not board-alone — `_board_wetness` is new code, not a refactor.
- **Dropped nothing material from the export:** the plan is near-verbatim; the only net additions (Open Questions, C-T1's #15 steelman note) are improvements. No useful framing was lost.

## 3. Contradictions / missing dependencies

- **A-T2 silently extends A-T1's helper set.** A-T1's migration list enumerates six helpers and excludes `_villain_combos_from_canonical`; A-T2 requires it but never declares it as additive. If A-T1 ships first and A-T2 stalls in review, the migration plan is silently incomplete.
- **A-T2 + B-T1 stack equity discounts unbounded.** A-T2 takes `min(equity_random, equity_tight)`; B-T1 subtracts `0.04*max(0, mw−3)` from equity in the call branch. Compound effect at `mw=5` against a large-bucket bet: equity is *both* lower-bounded by the tight range *and* taxed by 0.12. Plan does not say which adjustment fires first or whether they stack. Likely turns marginal calls into reflex folds.
- **B-T2 and A-T1 dispatch order is undefined.** Both fire inside `_equity_turn_river_action`. B-T2 raises with `strong_pair` "regardless of equity" when `raise_count == 4`; A-T1's veto folds weak hands. They don't conflict on identical hands, but the plan never says whether B-T2's 4-raise guard precedes A-T1's veto check. If A-T1 lands first and B-T2 inserts later, ordering must be specified in the patch.
- **B-T2's 5th-raise-pressure "regardless of equity" violates the bounded-deviation spirit C-T1 enforces.** Not a hard conflict (B-T2 is postflop, C-T1 narrows the preflop overlay), but the asymmetry is worth a sentence: C-T1 tightens us toward Nash while B-T2 raises off the equity grid.

## 4. Risk of over-planning

- **D3 should be cut.** Its own risk section calls module-level rolling state "the strongest red flag in the sandbox model" and the LBR proxy "a weak signal." Listing it as a wildcard wastes review surface — drop or relegate to a one-liner in Open Questions.
- **15-idea brainstorm lists across A/B/C are theatre.** A-T1 already bundles 8 of section A's 15 ideas; the residual is helper-list padding, not real alternatives. Collapse each section to ~6 distinct ideas + the top-3.
- **C-T3 is three orthogonal modulations in one item** (loader + VPIP cap + fold-to-cbet scale). Split into "loader-only P0" and two follow-up modulations so the fold-to-cbet scaling can land or not-land independently of A-T1's `safety_cap_mbb`.

## 5. Questions that would change implementation order

1. **Should C-T2 land BEFORE A-T1, or be cut?** If section C idea #11 is promoted into A-T1's veto block, C-T2's `_LAST_POSTERIOR` must exist when A-T1 ships — otherwise A-T1's static `safety_cap_mbb` becomes a v1 artifact and posterior-aware scaling is a v2 PR. This is the single biggest ordering decision and the plan is silent on it.
2. **Will `data/finals_priors.npz` be valid at A-T1 build time?** The patch-window Phase 3 sanity gate fires if VPIP ∉ [18%, 40%]. If priors are invalid/absent on 2026-06-02 morning, C-T3 silently no-ops via `try/except` — making its `safety_cap_mbb *= 1.3` a dead branch. Should C-T3 ship as a separate PR landing after Phase 3 confirms valid priors, or bundled with A-T1?
3. **Is the A-T1 helper bundle (`_bet_ratio_bucket`, `_multiway_count`, `_effective_spr`, `_board_wetness`, `_passive_ev`, `_bet_ev`) atomic, or splittable into a shared-infra PR landing before A-T1?** B-T1 / B-T2 / A-T3 all piggyback on these helpers; if A-T1 review stalls, three downstream items stall with it.
4. **Does `_LAST_POSTERIOR` module-level state pass the validator AST scan and the leakage audit?** Not on `FORBIDDEN_MODULES` or `FORBIDDEN_PATTERNS`, but the bot is documented stateless in `docs/tournament-spec.md`. Worth a 1-line spot-check before C-T2 lands.

---

**Verdict:** Implementable but needs one more pass — close the three seams (S1 combo expansion, S2 fold_prob source, S3 C-T2 consumer or cut), add a stacking-semantics line between A-T2 and B-T1, and answer ordering question #1 (C-T2 before or after A-T1). All are paragraph-sized additions, not a rewrite.
