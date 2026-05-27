# Finals R&D Loop Plan — Critique (2026-05-26)

Scope: `docs/plans/finals-rd-loop-2026-05-26.md` vs context_builder export
`prompt-exports/oracle-plan-2026-05-26-153333-finals-rd-plan-404d8-6b13.md`.
6 days remain to qualifier (2026-06-01).

## 1. Top 3 under-specified seams

1. **W3 `magnitude_pp` semantic.** `archetype_features()` returns
   `magnitude_pp: float`; bot caps it at 20 pp (qualifier) / 10 pp (finals). What
   "pp" denominates is referenced four times and defined zero. Spot-checked
   `PokerBot-codex/src/*.py` — `magnitude` does not appear in any source file.
   Without semantics, W3 Done-when "≥ +3 bb/100 ablation" has nothing to ablate.
2. **W3 LBR rewrite.** "≥ 500 deterministic public states ... depth-limited
   rollout ... against the bot's randomized `decide()` policy." Depth, sampling
   method for the 500 states, chance-node sampler, and the source of policy
   randomization (`decide()` is currently deterministic) are all unspecified.
   Two agents will produce two non-comparable LBR scores.
3. **W1 "behavior-matched" archetype seats.** `tools/archetypes/<name>/bot.py`
   must "validator-PASS" and be "behavior-matched (not code-copied)" — but no
   calibration target, reference policy, or accept-distance metric is named.
   Different agents will produce different `range_mc_pot_odds` bots and W5/W7
   gates against them won't reproduce.

## 2. Specificity balance

**Over-specified (should be the implementing agent's call):**
- W3 "per-call cost ≤ 5 ms" for equity — wrong gate. The constraint is the 2 s
  decision budget; per-call cost belongs to the implementer (caching, batching).
- W3 forbids merge unless all 5 sub-deliverables PASS — a 4-of-5 wave produces
  zero artifact. Should allow partial merges with sub-deliverable rollback.
- W6 hardcodes `{3,5,7} rounds × {120,300,600,1200} field-sizes = 12 cells`
  with no rationale. Sweep design belongs to the simulator owner.
- W3 commits "qualifier 20 pp, finals 10 pp" — tuning numbers that should be
  derived from R1 numbers, not legislated up front.

**Dropped useful framing from the export:**
- Export's LBR paragraph said *"the `[12,18,22,15,20]` constants are already
  gone per KANBAN 2026-05-22; residual proxy is the per-spot risk table."* The
  plan dropped this and now reads as if the constants are still the target — an
  agent will hunt the wrong artifact.
- Export's footer specified the **hard cutoff 2026-05-31 23:59 UTC** triggering
  `## STOPPED AT <gate>`. Plan keeps the protocol reference but loses the
  trigger time — operationally weaker.

## 3. Contradictions / missing dependencies

- **W3 `POKERBOT_REGIME` is dead code.** Spot-checked: the symbol appears only
  in plan + export, never in source. W5/W7/W9/W10 never set it or assert
  finals behavior. Finals is 2026-06-05; the plan only gates the 06-01 zip.
  The toggle ships unused unless a later finals plan exists — none referenced.
- **W7 `mystery_strong` ambiguity.** "Combine techniques the R2 swarm proved
  most damaging" — damaging *to us* (red-team future counter-exploit) or
  *by us* (compose our winners as an adversary)? Different bots, different
  threat model. Pick one.
- **W9 N calibration vs gate population mismatch.** N is fixed against the
  *easiest tier-1 archetype seat* (`monte_carlo_basic`); the gate then applies
  the same N to ≥ 3 of 4 *R3 top-tier seats* (Vladimir, Famadeo-on, Saroop,
  mystery_strong). N tuned on the soft tail almost certainly understates
  "decent margin" against the hard tail.
- **`manifest.json:competitor_clones` schema is never spec'd.** W1 says
  "extend with `competitor_clones` block"; W2 reads it; W7 adds `debug_fork`.
  Field names, types, ordering nowhere defined. First implementer freezes a
  schema; second implementer breaks it.

## 4. Risk of over-planning (6 days to qualifier)

**Cut or compress:**
- **W2 (cron, ~6 p-hr)** — installed today gives ≤ 5 firings before qualifier;
  marginal alert value vs build cost. Replace with one manual SHA check on
  2026-05-31 morning. **Cut.**
- **W6 (simulator, ~10 p-hr)** — validates near-guarantee but does not change
  the submission. R1 per-opponent CIs already tell us if we beat the field.
  **Defer to finals prep (post 06-02).**
- **W4 (loop infra, ~8 p-hr)** — collapse to a 1-page playbook; skip the
  dry-run swarm. **Half.**

**Timeline sanity at stated cadence:** W5 (3-5 waves × 6 h) + W7 (2-4 waves
× 6 h) + W9 (2-3 waves × 6 h) = **42-72 wall-hours of overnight time.** Five
nights × ~10 h/night = 50 h **just barely** holds the lower bound, and W1+W3
prep time (≥ 1 wall-day) is not included. **Triage**: ship v_R2 by
2026-05-29, skip dedicated R3 waves, attempt R3+R4 as one wave 2026-05-30→31.
Treat W6/W2 as out of qualifier scope.

## 5. Order-changing questions

1. **Has the organiser confirmed Swiss round count?** If 3 rounds confirmed,
   W6 sweep collapses to 1 cell — most of the simulator vanishes. Ask now;
   the answer reshapes W6 from "build" to "skip."
2. **Do Neel/Dominic memo numbers (+16287 / +12821 vs v_final) reproduce on
   the first paired-seed run?** If yes, R2 may already be near-green — climb
   R3 immediately, skip dedicated R2 waves. If no, the field is softer than
   feared and W5 collapses to a single wave.
3. **Is Vladimir's Deep CFR beatable in 50k hands?** If not, R3/R4 are
   impossible — ship v_R2 with margin against the rest and book Vladimir as
   a loss. Re-orders to "lock R2 hardening day 3, spend remaining days on
   Saroop/Famadeo specifically."
4. **Is `release/v_final-e4b4a8f1` actually stronger than current `main`?**
   If worse, the rollback floor is dead weight. If better, base W1's R1 run
   on it directly and drop the `main`-comparison step.
