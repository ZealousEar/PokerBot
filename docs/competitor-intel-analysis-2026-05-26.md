# Intel analysis: what the Codex recon actually buys us

## Bottom line

Mixed signal. The intel is real evidence about the **public, early-merged field** — the left tail of the entrant distribution. It tells us almost nothing about the **private, late-merging field**, which is where the strongest entrants typically live and where qualifier outcomes likely get decided. Trust the public-field architectural pattern; don't extrapolate to the unseen field.

## The math that matters — first principles

Qualifier mechanic: Swiss format, 400-hand matches, top 64 by cumulative chip delta advance.

```
Expected qualifier finish = Σ_rounds  edge(opponent_type) × hands_per_round
```

You do **not** need to beat each opponent. You need to outscore the field median across all rounds. So our finish is driven by `edge × frequency` over the opponent-type distribution. The Codex intel characterizes one slice of that distribution (visible public bots) and leaves the other slice (private bots) invisible.

Implication: if 80% of qualifier opponents end up matching the public archetype and we have +30 bb/100 vs them, that's where most of our chip delta comes from. The marginal gain from optimizing vs the strong unknowns is small in expectation — but the variance/downside from a poor matchup against them can wipe out many rounds of edge. The blueprint + bounded overlay shape addresses exactly this asymmetry. The architecture is correct; this intel does not change that.

## What the intel reliably tells us

1. **A common public architecture exists and is repeated independently across 4+ bots:** preflop range table → eval7 Monte Carlo postflop → pot-odds calls → fixed-threshold value bets → late-position semi-bluff. None show evidence of solver training, exploitability measurement, trained model heads at runtime, or LBR guards.
2. **Beating bundled reference bots is no longer a meaningful acceptance bar.** Multiple public bots clear it comfortably in 300-hand smokes. Our `template +71.82` etc. numbers measure performance against a population the field has already saturated.
3. **The exploit surface is predictable:** overfold to large bets near required-equity thresholds; overvalue raw equity multiway/wet-board; predictable preflop blind defense; brittle river guards. These are testable hypotheses, not just generic poker advice.

## What the intel cannot tell us

1. **Selection bias is severe.** Stargazers (32) ≠ entrants. Public forks ≠ submitted bots. The strongest hackathon entrants typically don't publish before the deadline. The Codex sample is dramatically over-weight on simple/early bots and silent on solver-driven private attempts.
2. **300-hand smoke samples have CI half-widths north of 5000 chips.** The reported `+16287`, `+12821`, `+8270` ranking is statistically noisy — ordering is loosely meaningful, magnitudes are not. Cannot be compared to our 10k paired-seed numbers.
3. **No information about the qualifier field size or composition.** We don't know if 100 entrants compete for top 64, or 1000. The "top 64" cutoff depends on field size in ways the intel doesn't address.

## Recommended intel hunts (this week only)

Two tiers are ROI-positive in the 6 days before qualifier. Everything else is nice-to-have that competes for the same time.

**Spike (30 min, before anything else):**
- Clone one public bot — start with `agrawalneel25/fullhouse-engine:neel-work` (compact, no exotic deps).
- Place under `ext/public-bots/neel/bot.py` (READ-ONLY; not packaged in our submission).
- Run a 1k-hand headless smoke vs our `v_final` via the engine.
- If it integrates cleanly, proceed to Tier 1. If not, scope down before committing the full matrix. The intel doc shows `vladimirfilip` fails validator and `famadeo` has `runtime_enabled=false` — integration friction is real.

**Tier 1 — Direct adversary measurement (~1 day if spike passes):**
- Clone the 3 strongest public bots (`agrawalneel25`, `Linglingletsgo`, `famadeo`).
- Paired-seed h2h vs `v_final`, 10k hands each, seeds 42-51, 6-player table.
- Output: bb/100 + bootstrap 95% CI per opponent. Logged to STATUS under a new heading; not gating any artifact change.
- Deliverable: actual edge numbers vs visible competitors, not inferred from refs.

**Tier 2 — Build the archetype suite (~1.5 days, parallelizable with Tier 1):**
- Implement the 5 archetypes the intel doc recommends (`range_mc_pot_odds`, `blueprint_threshold_exploit`, `risk_gated_conservative`, `stage_variant_anti_punt`, `monte_carlo_basic`).
- Behavior-matched, not code-copied. Lives in `ext/fullhouse-engine/bots/archetype_*` for benchmarking only — not packaged.
- Add as opponent options in `tools/benchmark.py`. Run 50k-hand paired-seed runs vs `v_final`.
- Stable benchmark surface that doesn't drift if competitor public state changes.

## Out of scope for this analysis

- **Strategy tuning of `v_final`** is a downstream user decision, not implicit in the intel plan. The artifact is locked at SHA `e4b4a8f1…598`. Any tuning re-opens the full G1-G11 gauntlet and the artifact SHA. Worth doing if Tier 1/2 surfaces a sharp weak matchup, but that's a fresh authorization call, not part of "gather intel."
- **Architecture pivot.** Blueprint + bounded overlay is the right shape for the dual qualifier/finals problem. Don't second-guess based on this intel.
- **Organizer contact / format clarification.** Real lever (Swiss rules and field size shift our prep priorities), but it's an external-surface action — your call, not part of an internal intel plan.
- **Fork-network monitoring, profile snooping.** Plausible but low ROI in 6 days vs Tier 1+2 doing real work.
- **2026-06-02 patch window** is the **finals** update day, not qualifier. Qualifier artifact is frozen by 2026-06-01 morning — Tier 1/2 intel can inform finals tuning even if we don't change the qualifier ship.

## What I need from you to proceed

One of:
- **A.** Run the spike + Tier 1 + Tier 2 (intel-only, no artifact changes). Findings go to STATUS for your review.
- **B.** A + pre-authorize overlay re-tuning if Tier 1/2 finds a matchup where we're below +0 bb/100 with CI excluding zero (and re-run the full gauntlet before any new artifact promotion).
- **C.** Defer — ship `v_final` as-is on 2026-06-01, treat Tier 1/2 as post-qualifier finals prep instead.

Default if no preference stated: **A**, scoped to the 30-min spike first.
