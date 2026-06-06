# Critique — Finals-Ship b108eff5 Plan

**Date:** 2026-06-04 · **Reviews:** `docs/plans/finals-ship-b108eff5-2026-06-04.md` · **Scope:** the 5 requested axes only; review-only, no rewrite.

**Posture:** The default (freeze-and-ship `v_final.zip` unchanged) is correct and the plan is well-grounded. Comments below are about plan *precision*, not direction.

**Spot-checks run (results inline):** (a) `diff -rq` proves the two editable copies **and** the extracted shipped `v_final.zip` are byte-identical across `src/`, `bot.py`, `data/`. (b) `deployed_artifact_gauntlet.py`: `--baseline` is passed only to `zip_inventory()` (`:892`), never matched; default `--bot` is the **leak** zip `v_qual2_ship_d54640e0.zip` (`:834`).

## 1. Top under-specified seams (implementer would guess)
- **A/B mechanics live only in the Background caveat, not the gate.** The Shared promotion gate says "candidate-zip vs exact b108eff5-zip on identical seeds/opponents," but the harness never runs them head-to-head — `--baseline` is inventory-only (`:892`). The actual method (run gauntlet twice vs a common opponent pool, diff aggregate) belongs *in* the gate. Footgun: default `--bot` is the leak zip (`:834`); every run must pass `--bot` explicitly or it benchmarks the wrong artifact.
- **No numeric bar for "probe pass green."** Item 0's `--skip-matches` "probe pass green" and Item 4's trigger ("only if b108eff5 actually large-commits") give no pass/fail threshold. The implementer invents one.
- **Acceptance seed/hands count unset** — Items inherit gauntlet defaults (`--seed-base 42`, 800 hands/opp). See §3; this contradicts repo policy.

## 2. Specificity balance
- **Over-specifies tuning magnitudes the experiment should own.** Candidate B's `cbet_bluff_prob` "+0.07", the split "+3 (A)/+2 (B) bb/100" gates, and Candidate C's exact constants (`≥0.40` stack, `eq_strong<0.70`) are knobs to sweep empirically, not pre-commit in prose. State the *direction*; let the gate pick the value.
- **Dropped framing — no exploitability guard in the gate.** The gate scores chip-EV vs a fixed opponent pool only. CLAUDE.md makes LBR/exploitability (`tools/exploit_check.py`, aggregate cap ≤200 mbb/g) the *finals* safety metric precisely because the finals field is sharper than the qualifier — which the plan accepts. Candidate A (widening 3-bet ranges) is the canonical exploitability-raising edit, yet nothing bounds counter-exploit risk. Add an LBR regression check to the gate for any preflop-range candidate.

## 3. Contradictions / missing dependencies
- **Source-reconciliation risk dissolves (evidence).** All three trees — both editable copies and the extracted shipped zip — are byte-identical. Item 1's "reconcile the two copies" and Open Question #1 are moot: the editable tree *is* the shipped source. Item 1 collapses to "commit this exact tree"; any rebuild delta is packaging-only by construction. The plan over-frames this as a blocking risk.
- **Unstated asymmetric reproduction risk** (the substance behind the "validator-equivalent" wording). Freeze ships existing bytes → reproduction fidelity is irrelevant. A *promoted candidate* requires a rebuild → fidelity becomes load-bearing. Item 1 proposes "validator-equivalent" proof, but the validator is AST+size only (CLAUDE.md) and cannot prove decision behavior. Given source is now proven identical the residual risk is small, but state it plainly: freeze needs no reproduction proof; a candidate rebuild needs a decision-diff on a fixed hand set, not the validator.
- **Gate threshold contradicts the repo variance policy.** +2/+3 bb/100 on default 800-hand / single-seed-base runs vs CLAUDE.md acceptance (paired-seed-count ≥10 **or** ≥50k hands). At 800 hands that threshold is inside the noise band — either bump hands/seeds or the gate is unsound.

## 4. Over-planning risk (default is freeze-and-ship)
The plan itself says freeze is "fully sufficient," yet Items 2–5 (all CONDITIONAL/CONTINGENCY/NOT-RECOMMENDED, ~30–45 min each against a closing deadline) occupy most of the document.
- **Cut Item 5 (Candidate D) to one line** — it is "do not touch"; a full work-item block is pure overhead.
- **Defer Item 4 (Candidate C)'s 6-clause predicate** — gated behind a failure the patched build likely won't reproduce. Keep the trigger; write the predicate only if triggered.
- **Subordinate Items 2–3 into one "optional upside" section** with a single gate, attempted only if Item 0+1 finish with hours to spare. Make the real critical path visually dominant: **Item 0 → Item 1 (trivial commit) → human upload.**

## 5. Questions that change order or the freeze-vs-edit call
- **How much time remains before finals close (2026-06-05)?** This single fact decides whether Items 2–5 are live at all; <~2 h slack after Item 0+1 → freeze-only, and §4's subordination becomes deletion. Listed as an Open Question but never answered, leaving half the plan's status undetermined.
- **Is Docker available for the deferred smoke run?** Item 0's "Deferred Docker smoke" is a hard done-when and the last unmet ship gate (it was *deferred*, not passed, in recon). If Docker is unavailable here, Item 0 cannot go fully green. Confirm/run the smoke harness **first** to de-risk — this reorders the plan.
- **Is the candidate work already done?** `STATUS.md` tail already lists `ab_candidate_A/ab_candidate_B` gauntlet results, `finals-freeze/` probe passes, and a freeze decision (next action = ship `v_final.zip` unchanged). If so, Items 2–5 are retrospective, not forward work — mark them done-and-rejected or cut them, rather than presenting them as pending.
- **Is Item 1 actually ship-blocking?** Source is proven identical and the ship artifact is the existing bytes (no rebuild), so committing source is audit hygiene, not a gate. If so it can follow the upload, shortening the critical path to Item 0 → upload. Confirm the "REQUIRED before ship" label is intentional.
