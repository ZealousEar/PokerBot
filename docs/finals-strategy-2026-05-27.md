# Finals Strategy — 2026-06-05 Bracket Plan

Written 2026-05-27, four days before the qualifier, eight days before the finals. Anchors every strategic claim in the offline corpus (`docs/corpus-index.md`). Decisions are conditional on data that has not yet landed (overnight lanes ship 2026-05-28 morning; competitor hand histories ship 2026-06-02 morning) — read this together with `docs/morning-promotion-checklist.md` and `docs/playbooks/patch-window.md`.

---

## 1. Qualifier vs finals — what actually changes

| Dimension | Qualifier (2026-06-01) | Finals (2026-06-05) |
|---|---|---|
| Format | Swiss-system, online, 6-bot tables | Single-elimination bracket of top 64, in-person at UCL East |
| Sample size per matchup | 400 hands per Swiss round | 400 hands per bracket match |
| Number of rounds | Many (depends on field size) | log₂(64) = 6 maximum |
| Selection criterion | Cumulative chip delta across rounds | Win each bracket match or eliminated |
| Field composition | Whoever entered | Top 64 by qualifier delta — the strongest entrants only |
| Variance tolerance | High — bad rounds get averaged out | **Low — one bad round eliminates you** |

The strategic implication is asymmetric:

- In Swiss, the metric is `Σ edge(opponent) × hands`. A +71.82 bb/100 win vs the median field and a −15 bb/100 loss vs a strong opponent average out positively, and we still bank chips toward the top-64 cut. Maximum chip extraction wins, even if it leaves us exploitable to a sharper counter — most rounds we're not facing that counter.
- In the bracket, the metric is `P(win 6 consecutive matches)`. Even if we have +5 bb/100 edge in every match (very strong), 6 matches at 400 hands each gives meaningful variance, and the field is hand-selected to be sharp. Downside protection matters more than upside maximization.

The corpus is explicit on this tradeoff. **[[Libratus-Brown-Sandholm-2017]]**'s bounded-exploitability frame: a wider best-response deviation harvests more chips against the weak slice of the field but pays a counter-exploit cost when met with a sharp opponent who is themselves best-responding. The Swiss field is mostly weak; the bracket field is mostly sharp.

**[[Pluribus-Brown-Sandholm-2019]]** designed for 6-max specifically and showed that the blueprint + small-deviation overlay holds up across opponent types, but their search budget allowed real-time depth-limited subgame solving on top. We do not have that compute (0.5 CPU, 2 s budget) — the blueprint we ship is the floor, and only the overlay magnitude is tunable.

---

## 2. Same artifact for finals, or a different one?

### Decision criteria

Ship the qualifier artifact for finals **unless** one of the following criteria fires.

1. **Lane B / V data (lands 2026-05-28) shows a single-opponent RED matchup** against an opponent we expect to face in the bracket. Specifically, a stat-sig loss with CI excluding 0 AND magnitude > 50 bb/100, against a publicly known competitor likely to qualify (the public-bot field of vladimir, dominic, famadeo, neel; Vladimir is the highest-risk per `consults/2026-05-27-overnight-P/vladimir_analysis.md`).
2. **Qualifier hand histories (2026-06-02) reveal the bracket field contains a posture our overlay cannot answer** — e.g., a deep-CFR-trained sharp 3-bet defender that punishes our wide-open ranges (the `sharp_3bet_punisher` archetype recorded a −3.36 bb/100 in the X1-repair AMBER findings; an actual deployed bot in this style would matter).
3. **Lane A (2026-05-28) promotes a candidate that beats the baseline aggregate AND lowers LBR** — i.e., it offers more edge AND less exploitability. This is the rare strict Pareto improvement. If found, the finals artifact is the Lane A candidate, not the qualifier baseline.

If none of (1)–(3) fires, **ship the qualifier `v_final.zip` for finals as well**. There is no penalty for shipping the same artifact twice, and the qualifier artifact's full G1–G11 gauntlet is already in `consult/artifacts/release/gauntlet.log` — it's the most-validated bot we own.

### Overlay magnitude — does `MAX_DEVIATION_PP` need to drop for finals?

The qualifier artifact carries `MAX_DEVIATION_PP = 0.20` (20 percentage points off the blueprint frequency, in either direction). The Lane A overnight sweep tests `{0.10, 0.15, 0.20, 0.25, 0.30}`.

For finals — assuming the bracket field is sharper — the corpus argues for a **lower** cap, not a higher one. **[[Libratus-Brown-Sandholm-2017]]** §3.2 (paraphrased): the worst-case counter-exploit penalty scales super-linearly with overlay magnitude when the opponent's own deviation strategy is good. A 0.30 deviation against a Nash-baseline opponent costs `O(d²)` rather than `O(d)`.

**Decision rule:**
- If Lane A finds `MAX_DEVIATION_PP = 0.15` (or 0.10) beats the baseline at qualifier and ALSO holds LBR aggregate ≤ 100 mbb/g (vs the qualifier 7.4 mbb/g — even tighter), promote it for finals.
- If Lane A finds a higher deviation (`0.25`, `0.30`) beats baseline at qualifier, **do not promote it for finals** even if it qualifies for qualifier ship per the morning checklist. Keep the qualifier artifact (which uses 0.20) for the bracket.
- If Lane A returns nothing usable, the qualifier 0.20 ships for finals. We do not retune via 06-02 patch window beyond what the hand-history priors suggest.

This is the principled split between "qualifier is a max-exploit pass" and "finals needs Nash-baseline downside protection," anchored in **[[Libratus-Brown-Sandholm-2017]]** + **[[Pluribus-Brown-Sandholm-2019]]**.

---

## 3. Meta-game — are qualifier hands public?

Read `docs/tournament-spec.md` line "**Patch window:** 2026-06-02 — hand histories downloadable as JSON; one updated bot allowed before finals." The spec is **silent on the visibility scope**. Two branches must be planned:

### Branch A — qualifier hand histories are PRIVATE per entrant

Standard hackathon convention: each entrant downloads their own match histories, no one else's. The patch window is for you to learn from your own qualifier play, not from the field's behavior.

**Strategic implication:** Bracket opponents have not seen our hand traces. They do not know what overlay shape we carry. Treat the bracket field as the prior — sharp by default per **[[Libratus-Brown-Sandholm-2017]]** + **[[Pluribus-Brown-Sandholm-2019]]**, and play near-Nash. **No behavior-shift is needed** to dodge counter-prep that doesn't exist.

This is the default branch. Probability ~0.7 based on hackathon convention; confirm by inspection at Phase 1 of the patch-window playbook.

### Branch B — qualifier hand histories are PUBLIC

Less common but possible: organizer publishes all matches (or at least the top-64 matches) for transparency. The patch window becomes a meta-game where each finalist can see every other finalist's qualifier behavior.

**Strategic implication:** Our qualifier behavior is now a **read** for every bracket opponent. They know our 3-bet frequency, c-bet frequency, river bluff frequency, position-specific posture, etc. A sharp opponent will best-respond to those observed frequencies in the bracket.

The counter-prep play is to **flip 2–4 overlay shifts** for finals, so the read is wrong:

- If qualifier `tighten_open=0.12` was active, finals could flip to `tighten_open=0.04` (closer to blueprint) — they expect tight, we open wider.
- If qualifier carried `value_widen_vs_aggro=0.08`, finals could flip to `0.02` — they expect value-heavy bluff-catches, we lean balanced.
- If `cbet_bluff_more=0.20` was active, finals could flip to `0.05`.

**Critical constraint:** flips must stay within the Nash-baseline cap (`MAX_DEVIATION_PP ≤ 0.20`) AND must not introduce new gaming surfaces (no opponent-name branching, no env-var shims — `audit_strategy_leakage` runs in Phase 4 of the patch window and disqualifies any artifact that introduces them). The flip is a parameter retune, not a strategy rewrite.

This is the contingent branch. Probability ~0.3. **Triggering condition:** when downloading hand histories in Phase 1, the bundle either contains other competitors' matches or the platform displays a "leaderboard with traces" view. Confirm by inspection.

### Resolution logic for 06-02 morning

```
Branch_A (private):  ship qualifier artifact for finals as-is (default).
Branch_B (public):   flip 2-3 overlay shifts via Phase 4 of patch-window playbook;
                     stay within MAX_DEVIATION_PP cap; full G1-G11 gauntlet must
                     pass before promote; default to qualifier on any regression.
```

In neither branch do we ship a substantially different artifact. The blueprint, sizing tree, postflop module, and overlay shape stay identical. Only the overlay's parameter values can move between qualifier and finals.

---

## 4. Decisions deferred to 2026-06-02 (post Lane B + V + K + hand-history data)

These four decisions cannot be made now because the supporting evidence has not landed. Each has its own trigger.

### 4.1 — Whether to ship the qualifier artifact for finals

**Trigger:** post-qualifier-morning, after reading qualifier results.

**Criteria for promoting a different artifact (must hold ALL):**
- We made the top 64 (otherwise moot).
- Patch window's Phase 7 regression bench shows the patched artifact ≥ qualifier mean across all 5 templates AND CI low > 0 on each.
- Lane B competitor h2h showed a real (non-Vladimir) RED matchup against a competitor confirmed to be in the bracket.
- LBR aggregate for the patched artifact ≤ 100 mbb/g (half the validator-spec cap of 200; qualifier baseline already posts 7.4 mbb/g, so there is headroom) — finals is sharper, exploitability margin must be tighter.

**Default:** ship the same `v_final.zip` (sha `e4b4a8f1…598`) for finals.

### 4.2 — Whether to retune the overlay coefficient for finals

**Trigger:** Phase 4 of the patch window, after analyzer extracts priors.

**Criteria for retune:**
- Hand-history priors show a population VPIP / PFR very different from what the qualifier overlay assumes (e.g., field VPIP < 20% → opponents are tight, our overlay should widen our opens more; VPIP > 35% → field is loose, our overlay should value-bet thicker).
- The retune stays within `MAX_DEVIATION_PP ≤ 0.20`.
- Lane A overnight sweep already promoted a different `MAX_DEVIATION_PP` value AND the promoted value's LBR is tighter than qualifier baseline.

**Default:** keep qualifier's `MAX_DEVIATION_PP = 0.20`.

**Corpus anchor:** **[[Cepheus-Bowling-2015]]** showed that CFR+ bucketing tolerates overlay perturbations up to ~25% of the blueprint frequency before quality degrades materially. 0.20 is well inside that envelope; 0.30 is at the edge. We keep room to the right.

### 4.3 — Whether to update preflop ranges based on observed competitor VPIPs

**Trigger:** Phase 3 of the patch window, after analyzer reports per-position VPIP percentiles.

**Criteria for range edit:**
- Observed median competitor VPIP differs from our baseline by > 5 percentage points in either direction.
- Lane L (preflop range tuning) overnight sweep already promoted a specific range adjustment AND its full G1–G11 gauntlet passed.
- The edit is a frequency change inside `src/preflop_lookup.py` only — no new branches, no opponent-identity strings.

**Default:** keep qualifier's preflop ranges untouched. Range edits are higher-leverage but also higher-risk than overlay tweaks because they affect every hand, not just the ones where the overlay fires.

**Corpus anchor:** **[[MCCFR-Lanctot-2009]]** + **[[Pluribus-Brown-Sandholm-2019]]** — the preflop blueprint is computed against a representative opponent distribution. Shifting our open frequency without re-solving the blueprint introduces local exploitability that the bounded overlay cannot fully recover.

### 4.4 — Whether to widen or narrow the sizing tree

**Trigger:** Lane H (sizing-frequency sweep) overnight result + analyzer's sizing-percentile output.

**Criteria for sizing tree edit:**
- Lane H produced a sweep result where the new sizing distribution beats qualifier baseline on all-templates AND held LBR.
- Hand-history priors show the field's actual sizings cluster meaningfully outside our current `{1/3 pot, 2/3 pot, pot, 2× pot, all_in}` discretization (e.g., heavy use of 1/2-pot or 3/4-pot bets).
- The edit is a frequency reweighting of the existing tree, not a node insertion — adding nodes invalidates the postflop blueprint cache.

**Default:** **DO NOT** edit the sizing tree during the patch window. Per **[[Pluribus-Brown-Sandholm-2019]]**, the sizing-tree discretization is part of the action abstraction; changing it mid-tournament without re-solving the blueprint creates inconsistencies between our preflop and postflop modules. Lane H may surface a candidate, but unless it's a clean Pareto improvement (more edge AND less LBR), it stays parked for post-finals retrospective.

**Corpus anchor:** [[Pluribus-Brown-Sandholm-2019]] §"Action abstraction" — the discrete sizing tree is solved-with, not solved-against. Mid-tournament sizing tree changes are dangerous.

---

## 5. What we do **not** do in the patch window

For clarity, every strategic lever that is **off the table** between qualifier and finals:

- **Solver re-training.** External-sampling MCCFR (`tools/train_preflop.py`) and CFR+ (`tools/train_flop.py`) are 8+ hour wall-clock operations even on the offline machine. The patch window is 24h with sleep. Solver runs do not fit. The blueprint is frozen for finals.
- **Postflop strategy rewrite.** `src/postflop.py` is the blueprint-bound flop/turn/river module. Patches there invalidate the LBR guard and may not be detectable inside 90 min of regression bench. Frozen.
- **Sizing tree expansion.** Per Section 4.4.
- **New opponent archetypes in `src/opponent_model.py`.** The behavior-based classifier in the qualifier artifact (`hyper_aggressive | aggressive | loose_passive | tight_passive | unknown`) is the live system. Adding a 6th archetype changes the posterior denominator and re-validates everything. Frozen.
- **Real-time subgame solving.** Per CLAUDE.md and **[[Libratus-Brown-Sandholm-2017]]** — out of scope at 0.5 CPU / 2 s. We replace with the frequency-based overlay. Frozen.
- **Any change introducing env-var branches, opponent-name strings, or shim flags.** Disqualified by `audit_strategy_leakage`, which Phase 4 of the patch window enforces after every edit.

The patch window is for tuning the overlay parameters and the data file the overlay reads. Nothing else.

---

## 6. Corpus anchors index

For quick reference. Every claim in Sections 1–5 cites at least one of these.

| Claim | Corpus anchor |
|---|---|
| Variance tolerance drops from Swiss to bracket | **[[Libratus-Brown-Sandholm-2017]]** + general first-principles |
| Bounded best-response (blueprint floor + overlay) is the right shape | **[[Libratus-Brown-Sandholm-2017]]** + **[[Pluribus-Brown-Sandholm-2019]]** |
| 6-max blueprint + small-deviation overlay holds across opponent types | **[[Pluribus-Brown-Sandholm-2019]]** |
| Sharp opponents make `MAX_DEVIATION_PP` lower, not higher | **[[Libratus-Brown-Sandholm-2017]]** §3.2 paraphrased |
| Sizing tree is part of action abstraction; mid-tournament changes are dangerous | **[[Pluribus-Brown-Sandholm-2019]]** |
| Preflop blueprint tolerates overlay perturbations up to ~25% blueprint frequency | **[[Cepheus-Bowling-2015]]** + **[[Pluribus-Brown-Sandholm-2019]]** |
| Real-time subgame solving is out of scope at sandbox compute budget | **[[Libratus-Brown-Sandholm-2017]]** (we cite it to drop it) |
| Deep CFR is out of scope (no PyTorch/TF in sandbox) | **[[DeepCFR-Brown-2019]]** (we cite it to drop it) |
| Per-bot exploit holes (template / aggressor / mathematician / shark / ref_bot_2) | **[[Engine-Fullhouse]]** |
| External-sampling MCCFR is what trained our preflop blueprint | **[[MCCFR-Lanctot-2009]]** |
| CFR+ is what trained our postflop bucketed blueprint | **[[Cepheus-Bowling-2015]]** |
| CFR mechanics foundation | **[[CFR-Zinkevich-2007]]** |
| LBR (Lisý & Bowling 2017) is the exploitability guard | arXiv:1612.07547 (inline ref) |

The full notes live under the external Obsidian vault at `Agentic/05 Research/PokerBot/`; wikilinks resolve there. `docs/corpus-index.md` is the local index.

---

## Cross-references

- `docs/morning-promotion-checklist.md` — 06-01 ship-day decision tree; produces the qualifier artifact this strategy carries (or doesn't) to finals.
- `docs/playbooks/patch-window.md` — 06-02 step-by-step workflow that implements the decisions deferred in Section 4.
- `docs/playbooks/hardening.md` — gate definitions; finals acceptance criteria reference them.
- `docs/tournament-spec.md` — sandbox invariants; meta-game uncertainty source for Section 3.
- `consults/2026-05-27-overnight-SUMMARY.md` — overnight lane outputs that resolve the deferred decisions (when ready).
- `STATUS.md` — locked qualifier baseline numbers (template +71.82, aggressor +112.63, math +144.60, shark +70.16, ref_bot_2 +144.60; LBR preflop 18.0 / aggregate 7.4).
