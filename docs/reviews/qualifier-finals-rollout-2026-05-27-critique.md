# Critique — Qualifier → Finals rollout plan (2026-05-27)

Reviewed `docs/plans/qualifier-finals-rollout-2026-05-27.md` against `prompt-exports/oracle-plan-2026-05-27-215645-rollout-plan-323b6c-04a6.md`. Calibrated to: plan locks decisions/seams; engineer owns tactics. Locked items (ship v_final AS-IS, skip HYGIENE-1, PATCH-2A first, PATCH-2B optional) are not relitigated.

## 1. Top 3 under-specified seams

- **S1 — B3 priors → overlay-bound mapping.** B3 says priors "shift overlay deviation bounds" inside `opponent_model.py:71-134` and `bot.py:153-159`, but never names which bound (light vs heavy overlay), the scaling function, or the warmup hook. The producer .npz exposes 12 keys (`vpip / pfr / af / fold_to_cbet / avg_sizing_{preflop,flop,turn,river} / top_preflop_sequences / ...`); plan picks no subset. That's strategy, not tactics — engineer would be inventing the policy.
- **S2 — B7 EV-veto rule.** B7 names five helpers (`multiway_count`, `board_wetness`, `made_hand_class`, `draw_proxy`, `recent_raise_depth`) but specifies neither return types nor the veto comparison itself. The famadeo template at `ext/public-bots/famadeo/bots/codex_holdem/bot.py:2169-2232` compares "realized equity under multiway/wet/low-SPR taxes < passive EV → fold"; the plan doesn't transcribe the inequality direction or the magnitude cap. Veto policy is the load-bearing decision — leave the helper shapes to the engineer, but pin the comparison.
- **S3 — B4 → B7 leak-naming schema.** B4 emits `decision_clusters.json` + `top5_leaks.md`; B7's "new edge-case tests cover the named famadeo top-2 leaks" presumes a stable naming convention that B4 never defines (and `board_texture` bucketing is unspecified). B7 acceptance becomes untestable unless B4 fixes a 1-line schema.

## 2. Specificity balance

**Over-specified (engineer should own):**
- B7's exact helper-function names + `~90–130 LOC budget` — name the semantic dimensions (multiway / board / hand class / draws / action depth), drop the names and LOC.
- B1's "8 schema variants" with the canonical list — number and exact list should follow from hardening rationale.

**Dropped useful framing from the export (1):**
- The export's closing note — *"LOC budgets and wall-clock budgets are guidance; the artifact-bound gauntlet is the load-bearing acceptance gate, not the budgets"* — was excluded. Restore one sentence so the plan can't be read as treating LOC/wall caps as hard.
- The export's B7 dependency line *"B3 (consumer must exist if veto reads priors)"* was simplified to unconditional. This drop is also the source of §3-C1.

## 3. Contradictions / missing dependencies

- **C1 (lead) — B7's hard dependency on B3 is over-coupled.** As currently scoped, B7's EV-veto uses only structural features; none of the five named helpers reads priors. The export's conditional ("if veto reads priors") was lost. If PATCH-2A is purely structural, B7 can run parallel to B3 and the finals timeline recovers ~3–4 h of wall.
- **C2 — B10 (06-03 evening) collides with the C2 6–8 h queue.** Chain on 06-02 → 06-03: B9 5–6 h + B4 90 m + B7 4–6 h + B8 3–4 h already saturates ~24 h of wall. C1 2 h + C2 6–8 h on top requires either pushing B10 to 06-04/06-05 or treating C2 as out-of-scope. Plan never acknowledges the queue density; either declare a B10 slip rule or drop Phase C from the timeline entirely.

## 4. Risk of over-planning

- **B5 (W2 dominic audit) — cut.** Done-when says "no patch designed regardless of verdict." If no downstream decision branches on the output, it's 60 min of informational work in a 96 h window. Fold into B4 as a one-line appendix or kill.
- **A3 (ship-eligibility dashboard) — cut.** Already conditional with "or drop." The work-item-level treatment is heavier than needed; degrade to a single line in Open Questions.
- **Phase C (C1 + C2) — collapse.** PATCH-2B fires only if B8 clears by ≥+15 bb/100 with zero regressions and ≤+10 mbb/g LBR creep — improbable. Two detailed work items pre-commit ~10 h of plan surface for a branch most likely never taken. One conditional line: *"if PATCH-2A clean, scope + run PATCH-2B before 06-04 EOD"* suffices; let the engineer plan C-details after B8 passes.

## 5. Questions that would change implementation order

1. **Does PATCH-2A's EV-veto read `finals_priors.npz` at runtime?** If no, B7 runs parallel to B3 (C1 is real). If yes, B3 must precede B7 *and* the priors→veto mapping needs pinning (resolves S1 + half of S2).
2. **What calendar time on 2026-06-02 do real hand histories release?** Determines whether B9's 5–6 h slot starts at 09:00 or 18:00 and whether C-branch has any wall to run.
3. **Is a 5000-hand sample in B4 enough to declare "concentrated" with paired-CI rules?** PATCH-1 reconcile showed cluster verdicts noisy at 10 k hands; if B4 needs ≥10 k, B4 wall doubles and B7→B8→C compresses further.
