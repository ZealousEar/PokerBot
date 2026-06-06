# Dual-Leak Candidate Swarm — Orchestration Plan (2026-05-30)

Single source of truth for the Toby + Mehedi dual-leak candidate attempt. Every lane reads this
before working. **Read-only for sub-agents** (the orchestrator owns/edits this file).

## Mission
Attempt a promotable candidate fixing BOTH live leaks (Toby river postflop trap + Mehedi preflop
BB defense) under strict isolation. **Default outcome: ship the locked `submissions/v_final.zip`.**
A candidate replaces it ONLY after clearing the full promotion gauntlet AND explicit human sign-off.

## HARD INVARIANT (every lane)
- NEVER modify/rebuild/repackage/overwrite `submissions/v_final.zip` or `submissions/best_green.zip`.
  Both MUST stay sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
  Run `shasum -a 256` on both at lane START and lane END; abort the lane if either changed.
- Do NOT edit `ext/fullhouse-engine/`, `ext/public-bots/`, or any other agent's worktree.
- Do NOT infer ship behavior from canonical `main`/`tooling` `src/` — canonical is dirty and is NOT
  the ship source.
- Base ALL candidates on branch `release/v_final-e4b4a8f1` (the clean ship source; a worktree for it
  already exists at `~/Code/PokerBot-gauntlet`).
- Each lane works in its OWN fresh `git worktree` off `release/v_final-e4b4a8f1`
  (e.g. `git worktree add ~/Code/PokerBot-<lane> release/v_final-e4b4a8f1` then a new candidate branch).
  Use `~/Code/PokerBot-codex-postflop-trap` as a template for venv setup. Verify
  `.venv/bin/python --version` reports **3.10** before running gates. Do NOT run `pip install`.
- Candidate artifacts get NEW names; never the protected names. Use `.venv/bin/python`, not host python.
- Reuse the EXACT benchmark/H2H harness invocations from the prior runs' `command_logs/` under
  `consult/artifacts/2026-05-29-away/{postflop-trap-candidate,mehedi-cluster,preflop-antecedent-grid}/`
  rather than reinventing how to point the harness at a specific public bot.

## DECISION-GRADE SAMPLE SIZE (non-negotiable)
- A 10k-hand single-run bb/100 has ~20 bb/100 95% CI. It is NOT valid for any accept/reject/regression
  decision — it is monitoring only.
- ALL acceptance, regression, and arbitration numbers MUST use paired seeds
  (`tools/benchmark.py --paired-seed-base 42 --paired-seed-count 10`) OR `--hands >= 50000`.
- **Regression standard: a regression counts ONLY if its CI excludes zero.** A negative point estimate
  whose CI includes zero is noise, not a regression. Apply this uniformly to every opponent.

## Lanes (A ∥ B  →  C ;  D optional/parallel)

### Lane A — Toby postflop fix (clean)
Base `release/v_final-e4b4a8f1`. Suggested worktree `~/Code/PokerBot-laneA-postflop`,
branch `candidate/postflop-trap-v2-2026-05-30`.
- **STEP 1 (discriminating check — DO FIRST):** the P2 candidate
  (`consult/artifacts/2026-05-29-away/postflop-trap-candidate/zips/v_postflop_trap_candidate.zip` +
  `DIFF.patch`) showed **+17 (base142) / +15.6 (base242) bb/100 vs Toby** but was held back by a
  **Pav 7.9 −1.074 bb/100** "regression" + an aggressor mean drop — both ~1/20th of the 10k noise floor.
  RE-TEST P2 vs Pav 7.9 and the aggressor reference at paired-seed/≥50k. If the regression CI includes
  zero, **P2 is already clean → that diff IS the Lane A candidate; skip new patching** and go straight
  to the full eval. Verdict `P2_ALREADY_CLEAN`.
- **STEP 2 (only if a regression's CI excludes zero):** minimize the P2 diff in `src/postflop.py` until
  Toby stays materially up AND the offending regression's CI includes zero, with no reference/public
  regression. No preflop / overlay / opponent-name-branch changes.
- Allowed edits: `src/postflop.py`, `tests/edge_cases/test_postflop_trap_v2.py`.
- Eval (paired/50k, CI-excludes-zero): Toby H2H bases 142+242; Pav 7.9 + 7.6; famadeo; neel;
  stoppedtime24; reference templates; exploit_check (≤100 mbb/g preflop, ≤200 aggregate). Static:
  validator, smoke (200 hands), import_audit, edge tests, leakage audit.
- Output: `consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/` → REPORT.md, RESULTS.json,
  DIFF.patch, candidate zip, command_logs/. Verdict: `P2_ALREADY_CLEAN` / `POSTFLOP_V2_PROMOTABLE` /
  `POSTFLOP_V2_NOT_PROMOTABLE` / `NO_POSTFLOP_FIX`.

### Lane B — Mehedi preflop BB-defense fix
Base `release/v_final-e4b4a8f1`. Suggested worktree `~/Code/PokerBot-laneB-mehedi`,
branch `candidate/mehedi-bb-defense-2026-05-30`.
- Leak: HU big-blind defense — preflop BB fold (−9.13) + BB all_in (−6.74), confirmed DIFFERENT_LEAK.
  Do NOT reuse P3 button-open-tightening (it failed broadly: famadeo/neel/Pav/reference regressions).
- Patch: add a heads-up BB-vs-button-open defense band in `src/preflop_lookup.py` — premiums continue
  aggressively; medium/playable hands CALL (not fold/all-in); suited/connective defend at reasonable
  price; trash folds; avoid all-in with medium hands. Bucket by hand score, suitedness/connectivity,
  open size, amount owed, stack/pot. Count raise count (not voluntary actions). Do NOT globally loosen
  six-max BB defense or globally tighten button opens.
- Allowed edits: `src/preflop_lookup.py`, `tests/edge_cases/test_mehedi_bb_defense.py`. (Touch
  `src/bot.py` ONLY if HU BB state cannot be detected inside preflop_lookup — report if so.)
- Required unit tests: KTo/AJo/99 vs HU button min-open does NOT fold; 72o vs large open folds; premium
  stays aggressive/legal; six-max limp+iso behavior unchanged; all outputs legal.
- Eval (paired/50k, CI-excludes-zero): Mehedi H2H bases 142+242; Toby H2H (must not worsen); Pav 7.9/7.6;
  famadeo; neel; stoppedtime24; references; exploit_check.
- Output: `consult/artifacts/2026-05-30-dual-leak-swarm/laneB-mehedi-bb/` → REPORT.md, RESULTS.json,
  DIFF.patch, candidate zip, command_logs/. Verdict: `BB_DEFENSE_PROMOTABLE` / `BB_DEFENSE_NOT_PROMOTABLE`
  / `NO_BB_FIX`.

### Lane C — Dual merge + FULL promotion gauntlet  [HOLD until A & B return]
Merge only the components A/B marked materially-improving. The merged artifact is BRAND NEW —
A-clean + B-clean ≠ dual-clean (two strategic degrees of freedom, interactions matter). Run the FULL
gauntlet from scratch on the merged candidate.
- Gauntlet (paired/50k, CI-excludes-zero): validator, smoke, import_audit, edge tests, leakage audit,
  exploit_check, all-template benchmark, overlay ablation, Toby H2H, Mehedi H2H, public regression
  (Pav 7.9/7.6, famadeo, neel, stoppedtime24, vladimir if usable), AND **six-max pods (REQUIRED gate,
  not evidence)**: baseline public pod, Toby+Mehedi pod, public-nightmare pod — 400 hands/match, ~100
  seeds, SAME seeds baseline vs candidate; report p10/p25/p50/p75/p90, mean, bust rate, errors, p99
  latency, scheduled chip delta AND actual bb/100 separately.
- Verdict: `DUAL_PATCH_PROMOTABLE` ONLY if Toby AND Mehedi both materially improve, no regression gate
  fails (CI excludes zero), and six-max p50/bust rate do not worsen. Else `DUAL_PATCH_NOT_PROMOTABLE` /
  `NO_DUAL_PATCH_FOUND`.
- Every report ends: "Human promotion gate required; locked v_final.zip remains upload target unless
  explicitly overridden." Verify protected SHAs before & after.

### Lane D — Prevalence / threat evidence  [OPTIONAL, parallel, CANNOT promote]
Q5 public RED variant sweep (all TobyCoad + Mehedi custom-bot variants; classify leak class) + Q6
hidden-archetype fuzzer (build simple valid opponent bots stressing known seams; H2H vs baseline +
candidates). Build opponent zips under the artifact dir only; no ship-source edits. Output feeds the
promotion decision; it NEVER gates the critical path.

## Decision rule (after lanes)
- No candidate `*_PROMOTABLE` → **upload locked v_final.zip**.
- Dual candidate FULL-green → human reviews EVERY regression row before MODIFY; any ambiguous row → ship locked.
- Single-leak-only promotable → do NOT promote pre-qualifier unless six-max + prevalence show that leak
  class is large AND the other leak's risk is unchanged.
- Worsens any GREEN public bot (CI excludes zero) OR worsens six-max p50/bust rate → do NOT promote.

## Feasibility gate (orchestrator-owned, gates Lane C)
Confirm the exact 2026-06-01 submission cutoff and back-compute that a statistically-valid gauntlet
(≥13 regression opponents + six-max × ~100 seeds at paired/≥50k) actually FITS the window. If it does
not fit, the answer is "ship locked" regardless of what A/B find.

## Checklist — FINAL: SHIP LOCKED (see FINAL_DECISION.md)
- [x] Lane A — **P2_ALREADY_CLEAN** (blockers were noise; clean H2H candidate)
- [x] Lane B — **NO_BB_FIX** (Mehedi resists clean fix; session crashed pre-report, see CLOSEOUT_NO_BB_FIX.md)
- [x] Feasibility — internal freeze 2026-05-31 23:59 UTC; OFFICIAL cutoff still unconfirmed (human action)
- [x] Lane C — **SHIP_LOCKED**: clean H2H + decisive paired Toby win (+780k/+820k), BUT six-max pods net **−73,149** (Toby pods −94,096), C1 single-Toby −128,826, bust rate worse in C1. H2H edge does not generalize to pods.
- [x] Lane D — SKIPPED (moot: candidate failed pod bar; prevalence only sizes a non-existent benefit)
- [x] Final rollup — FINAL_DECISION.md written; recommendation = SHIP LOCKED, human sign-off + cutoff confirmation pending

## LIVE RESULTS (2026-05-30)

### Lane A = P2_ALREADY_CLEAN
The advisor's noise hypothesis confirmed: at 50k paired seeds the "blockers" vanish.
- Pav 7.9 -0.54 [-2.38,+1.28] (CI incl. zero), famadeo -1.21 [-4.20,+1.70] (clean), aggressor +2.0 (clean).
- Gains: Pav 7.6 +5.47, neel +19.3, stoppedtime24 +18.8, references capped +20. NO CI-excluding regression.
- Toby: locked -14.0 [-16.0,-12.0] vs candidate -0.8 [-4.4,+2.8] — non-overlapping CIs => real ~+7-13 gain (cross-run, not paired). Candidate ACTUAL (played-hand) Toby bb/100 still -6.5/-9.7.
- Static: leakage/import/edge/validator/smoke PASS; exploit 18.0 / 5.65 mbb/g (under caps). SHAs intact.
- Candidate (strategy bytes identical to vetted P2, repackaged off release):
  `consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/zips/v_postflop_trap_v2_p2_already_clean.zip` (sha `d042c977...`)

### Lane B ~ NO_BB_FIX
Mehedi BB leak (preflop fold -9.13 / all_in -6.74) resists a clean fix: any band wide enough to touch
Mehedi's 2.5x/3x pressure spots wrecks early stack trajectories / regresses the field; the safe
min-open-only band shows ~zero delta vs Mehedi. Honest negative. Default = ship locked stands for Mehedi.

### Structural consequence — dual collapses to Toby-only
No Mehedi component to merge => Lane C is no longer a dual merge. Decision rule (genius): a postflop-only
candidate is NOT auto-promotable; it needs (a) paired decision-grade Toby confirmation, (b) clean six-max
pods (the one untested dimension; qualifier scores cumulative chip delta over 6-bot pods), and (c) evidence
Toby-class behavior is prevalent in the field. Otherwise: ship locked.

### Lane C (REVISED) — Toby-only promotion gauntlet on Lane A's candidate
1. PAIRED locked-vs-candidate Toby 50k (same seeds, both bases) -> Toby delta WITH CI (settles the +13 claim).
2. Six-max pods (REQUIRED gate): C0 reference baseline, C1 +Toby, C3 Toby+Mehedi, C4 public-nightmare;
   ~100 seeds, same seeds baseline vs candidate; report p10/p50/p90, mean, BUST RATE, p99 latency,
   scheduled chip delta AND actual bb/100. Candidate must not worsen six-max p50 or bust rate.
3. Overlay ablation + all-template confirm. Reconcile the scheduled-vs-actual Toby gap via real pod chip delta.
4. Verdict: TOBY_ONLY_PROMOTABLE only if Toby paired-improves, zero CI-excluding regressions, six-max
   p50/bust not worse. Else ship locked.

### Lane D — Toby-class prevalence (now required, parallel to C)
Q5 public RED variant sweep: how many TobyCoad-family variants are RED vs locked, and is the river-trap
leak-class family-wide or a one-off? Feeds the (c) prevalence condition above. Cannot promote alone.

## CRITICAL FINDINGS (advisor reframe, 2026-05-30)

**Engine scoring = raw chip delta at bust.** `sandbox/match.py:277` records `chip_delta = stacks - STARTING_STACK`
at early stop (no normalization over scheduled N); `engine/tournament.py` ranks by cumulative chip delta.
A bot busting at 0 from a full stack scores the full negative; busting early is STRICTLY WORSE than
grinding a small loss. => Judge on RAW CHIP DELTA + BUST behavior, NOT bb/100. Lane A's "scheduled
-0.8 vs Toby" is a 50k-denominator artifact; matches busted at ~6k hands (actual -6.5/-9.7) => candidate
likely STILL loses real chips to Toby. The "+13 improvement" headline is NOT established; drop it pending
a paired chip-delta run.

**P2 had a SECOND shelving reason (not just noise blockers): it FAILED the repository smoke wrapper**
with `FAIL_HAND_COUNT_BASELINE_PARITY` (POSTFLOP_TRAP_CANDIDATE_REPORT.md:5,42,83). Lane A reported smoke
PASS on a (possibly looser) invocation despite byte-identical strategy. Lane C MUST run the EXACT
authoritative smoke wrapper, 3-5x for flakiness; an intermittent smoke-gate failure is a HARD BLOCKER.

**Reframed bar:** default = ship locked. Candidate is byte-identical strategy to the already-shelved P2.
Need a POSITIVE six-max chip-delta reason to replace a battle-tested artifact 1.5 days before the qualifier;
no-regression is necessary, not sufficient. Ship-locked is the most probable correct call.

**OFFICIAL CUTOFF still unconfirmed** (only internal freeze 2026-05-31 23:59 UTC known). It gates the
promotion decision, not the analysis. If a human cannot confirm the cutoff is later than the work
completes, bias to ship locked.
