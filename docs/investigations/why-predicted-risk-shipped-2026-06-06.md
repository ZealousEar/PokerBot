# Investigation: Why a Pre-Written Risk Got Shipped Anyway (Thorp finals, 2026-06-04)

**Author:** forensic decision analysis, 2026-06-06. Read-only. Primary sources = `STATUS.md` (timestamped gate log), `prompt-exports/2026-06-04-173203-plan-optimise-next-90min-finals-bot.md`, `consult/artifacts/2026-06-04-finals-recon/{finals_brief.md,field_meta.md,thorp_leak_report.md}`, `CLAUDE.md`. The dated post-mortem `docs/investigations/finals-prep-postmortem-2026-06-04.md` is treated as a SECONDARY source and is checked for rationalization.

---

## Summary

The risk that was written down — "extreme polarization (call 6.4%) is a real exploitable hole; a sharp seed can bet-fold us off pots; **mean EV vs a strong seed may be negative**" (`finals-prep-postmortem-2026-06-04.md:163`) — did not change the ship decision. But not for the single reason the prompt assumes (pure inertia). The record shows **two decision passes** on 2026-06-04 with the **same output (ship `b108eff5` as-is)** for **different reasons**, plus an upstream cause that made any other outcome impossible:

1. **Pass 1 (pre-format-correction, "FINALS-RECON"):** the warning was reclassified as a *feature* under a **false premise** ("we're the #57 underdog in a single-elim bracket; variance is an asset", `:161`). Here the prediction was genuinely inert — it read as support for the plan. **(H1, H6 confirmed.)**
2. **Pass 2 (post-format-correction, "FINALS-EXEC-6MAX"):** the premise was corrected (Swiss/cumulative, shrinkage penalizes variance) and the team *correctly re-recognized* the polarization as a liability — a premise-change review **did** fire. Ship-as-is survived anyway because the only staged fixes had already cratered and **no de-polarization fix existed to ship in the window.** **(H7 partly refuted; H4 refuted.)**
3. **The risk was structurally untestable in their harness — and the matching test was never built.** The written risk is an *over-folding bleed*: fold 58.9% / call 6.4% means a sharp opponent profitably bluffs us off medium pots ("bet-fold us off pots"). Refuting it needs a **sharp over-folding counter-exploiter** in the gauntlet. The gauntlet had a maniac (`aggressor`) + fixed-archetype templates + engine reference bots — **no adaptive exploiter**; the consult itself lists "what a sharp opponent does to a 6.4%-call bot" and "opponent bots that themselves adapt" as blind spots they *both missed* (`consult …:60`). So the one cheap test that targets the risk's mechanism was never run. **(H3 confirmed — primary, alongside H1/H6.)**

Note on the separate "unaudited preflop" thread: that is a *different* failure mode (over-committing → busting), not the over-folding-bleed risk under investigation. Its magnitude was never cleanly established and the two available audits **conflict** (see §2/§5 H5) — so it is a supporting finding, not the primary cause.

The post-mortem's own strategy section rationalizes ship-as-is with the dead single-elim premise and was never reconciled after the format flip (see §"What the post-mortem missed").

---

## 1. Causal chain: "risk identified" → "risk shipped"

All times UTC, from `STATUS.md` gate headers unless noted.

| # | Time | Event | Premise in force | Disposition of the risk |
|---|------|-------|------------------|--------------------------|
| 1 | 2026-06-03 | R2 leak `d54640e0` auto-uploaded by overnight agent; "human-only upload" rule codified into `CLAUDE.md`; MEMORY records qual2 redteam verdict "stack-off fix did not fix the leak" | single-elim (stale) | Leak concern is **postflop** stack-off only |
| 2 | 06-04 (FINALS-RECON) | Recon + baseline decision. Oracle synthesis `new-chat-1FB6CB`. **Ship `b108eff5` as-is.** | **single-elim, #57 underdog (WRONG)** | Polarization risk **reframed as asset**: "Reject Nash-de-risk (we're the #57 underdog; variance is an asset)" (`STATUS.md` FINALS-RECON; postmortem `:161`). Caveat at `:163` notes negative-EV-vs-strong but concludes "we can't safely de-polarize today." No owner, no test, no threshold. |
| 3 | 06-04 16:43 (FINALS-SHIP) | Candidate A (+wider 3bet) → **−353 bb/100**; Candidate B (+cbet bluff) → **−741 bb/100**; both DISCARD on paired-seed gate (≥+3). Ship `b108eff5`. | single-elim; deadline believed 18:00 UTC | The two staged code fixes both crater vs `aggressor`; freeze confirmed |
| 4 | 06-04 ~17:20 (FINALS-UPLOADED) | **Farhad uploads `b108eff5` LIVE.** Simultaneously: **portal format correction** — finals are a FRESH Swiss/cumulative competition, NOT single-elim; **deadline EXTENDED to 19:00 UTC.** `CLAUDE.md` "Finals FORMAT" section updated. | **PREMISE FLIPS HERE** | Live artifact now a fait accompli + valid fallback |
| 5 | 06-04 ~17:32 (consult export) | 90-min consult fired **on the corrected premise**: "NOT single-elimination. We previously (wrongly) assumed single-elim + 'embrace variance as the underdog.' Dead… shrinkage regresses high-variance lines toward the mean" (`2026-06-04-173203…:14`). Asks directly: "Does call 6.4% help or hurt vs the single-elim frame…especially MULTIWAY?" (`:59`) | **Swiss/cumulative (CORRECT)** | Risk **correctly re-recognized as liability**; flagged "ZERO 6-max evidence — likely our biggest unmeasured risk" (`:37`) and "Preflop is NOT audited" (`:39`) |
| 6 | 06-04 17:59 (FINALS-EXEC-6MAX) | Two lanes: (A) read-only 6-max evidence → net-positive chip/100, **0 crashes/illegal/timeout** over 7197 decisions; (B) data-only `field_priors.npz` retune → **+0.00 bb/100, CI [−25.82,+22.97]**, INDETERMINATE → REJECT. **DECISION: SHIP-AS-IS.** | Swiss/cumulative (correct) | No code fix justified by crash evidence; no data fix cleared acceptance |
| 7 | 06-04 18:25 (RIVER-TRIAGE) | Diagnostic only ("code-patch reship was already out-of-window, 18:15 start"). Finds **busts are preflop-dominated** (commitment-street counts `{preflop:6, flop:2}`; 0 river decisions). Confirms ship-as-is. | Swiss/cumulative | **Confirms the postflop gate answered the wrong question** — but out of window |

**The chain:** Pass-1 reframing (step 2) neutralized the warning by premise. Step 3 burned the staged candidates. Step 4 made the live bot the anchor *and* flipped the premise. Steps 5–7 correctly re-weighted the risk but found no buildable remedy, because (root cause) the preflop path was never audited or fixed during the entire prep.

---

## 2. Tracing every mention of the risk

| Where | Who/what | Quoted language | What happened next |
|-------|----------|-----------------|--------------------|
| postmortem `:161` | oracle synthesis `new-chat-1FB6CB` | "we are the #57/64 underdog in a single-elim bracket; lower variance helps the favorite. Our high-variance aggression (AF 5.45) is an asset… **Hard no.**" | **Reframed to asset.** Became the ship rationale. Never corrected after format flip. |
| postmortem `:163` | same | "`call 6.4% / fold 58.9%` is *extreme* polarization… a real exploitable hole vs a sharp counter-exploiting seed…**mean EV vs a strong seed may be negative**… we can't safely de-polarize today." | **Acknowledged, then deferred** with no owner/test/threshold. |
| postmortem `:172`, brief `§5 preflop` | pair investigator | "Gate is **postflop-only**… preflop code…**NOT yet audited** — Potentially dominant / **Unverified**" | **Flagged Unverified; never gated.** No blocking action. |
| brief `§6` | recon packet | "the **unverified preflop bust source** behind Thorp's 56% bust rate" named as a top decision input | Forwarded to reviewer; not converted to a test that blocks ship |
| consult `:60` | 90-min consult | lists "what a sharp opponent does to a 6.4%-call bot" and "opponent bots that themselves adapt" under **"Anything we BOTH missed"** | The adaptive/sharp-exploiter test (the one matching the risk's mechanism) is named as a blind spot and **never built** |
| `thorp_leak_report.md:35` | replay analysis (qualifier, n=20) | "**5 preflop / 15 postflop (25% / 75%). 3-of-4 Thorp busts are decided postflop.**" | A separate *busting* audit; **count-wise it AFFIRMS the postflop focus** (see contradiction below) |
| `STATUS.md` RIVER-TRIAGE | diagnostic (b108eff5, 6-max, n=9 river-subset, "cards unavailable") | "Busts are preflop-dominated… commitment street counts `{preflop 6, flop 2}`" | Out-of-window; conflicts with the larger qualifier audit |

**Unreconciled-contradiction finding (itself a process gap):** the two bust audits disagree and **nobody reconciled them.** The clean qualifier audit (`thorp_leak_report.md:35`, n=20) says **75% postflop**; the 9-hand RIVER-TRIAGE subset on the patched build says preflop-dominated. They are plausibly reconcilable — the postflop patch folds marginal jams, shifting *residual* busts toward preflop — but that is an inference from a tiny compact-data subset, not a settled fact. Either way, **the busting question is the wrong frame for the over-folding risk** under investigation (busting = over-commit; the risk = over-fold).

**Silence finding:** the over-folding-exploit risk — named "a real exploitable hole" and "potentially dominant" — has **zero confirming/refuting test run before ship.** Every *postflop commitment* residual got a disaster-spot probe (`finals-freeze/`); the over-folding bleed got prose and a blind-spot bullet. The harness could not have tested it: no over-folding counter-exploiter existed in the gauntlet.

---

## 3. Decision points: competing considerations and who won

**Pass 1 (FINALS-RECON):** Considerations = {Nash de-risk vs keep aggression; edit field priors in code vs not}. **Winner: keep aggression, freeze.** Stated rationale: single-elim underdog → variance is an asset (`:161`). **Owner:** "oracle synthesis `new-chat-1FB6CB`" — i.e. a synthesis output, not a named human/agent. Responsibility diffuse. **(H6 confirmed.)**

**Pass 2 (FINALS-EXEC-6MAX):** Considerations = {ship-as-is vs data-retune vs code-fix} — explicitly three options in the consult (`:5,:57,:62`). **Winner: ship-as-is.** Stated rationale: candidates A/B already −353/−741 (`STATUS.md` FINALS-SHIP); data retune indeterminate CI (FINALS-EXEC-6MAX Lane B); 6-max evidence shows zero crashes so no crash-justified code fix; live artifact is a verified fallback. **Owner:** the executing agent + human-gated freeze; decision logged GREEN. This pass had **numeric go/no-go gates** for candidates (≥+3 bb/100) — but **none for the polarization risk itself.**

The asymmetry is the finding: **staged candidates had thresholds and were correctly killed; the load-bearing risk had no threshold and could not bind anything.** **(H3 confirmed.)**

---

## 4. "No time" claims — genuine constraint vs risk-appetite in a time costume

| Claim | Verdict | Evidence |
|-------|---------|----------|
| "can't safely de-polarize today" (`:163`) | **Genuine for a *re-solve*; risk-appetite for a *cheap test*** | A blueprint re-solve (adding a calling range) needs gated-off CFR — genuinely not buildable in-window. But *confirming whether the risk is real* did not require a re-solve: a single sharp over-folding exploiter run through the existing `deployed_artifact_gauntlet.py` harness would have measured how much a bettor extracts vs call 6.4%. That opponent was never built. |
| "code-patch reship already out-of-window (18:15 start)" (RIVER-TRIAGE) | **Genuine at 18:15; self-inflicted earlier** | Deadline was 19:00 UTC; upload was ~17:20. There were ~100 post-upload minutes (steps 5–7), spent on 6-max crash-evidence + an indeterminate data retune — not on a sharp-exploiter probe of the named risk. |
| "candidates fail the gate, so freeze" (FINALS-SHIP) | **Genuine** | A (−353) and B (−741) are real paired-seed regressions vs `aggressor`. Correct to discard. |
| "build the de-polarization fix" | **Not buildable in window — genuine** | A calling-range fix needs the gated-off CFR path + full re-gate + human upload buffer; correctly judged infeasible in 90 min. The *measurement* of the risk, however, was feasible and skipped. |

**Cheapest on-target test that fit:** one sharp over-folding counter-exploiter added to the gauntlet (the harness already runs 12 opponents, `deployed_artifact_gauntlet.py`). This measures the exact mechanism the risk names — a bettor bluffing a 6.4%-caller off pots — which `aggressor` (a maniac that *value-spews into* us, the matchup we *win*) does not. Building one fixed-strategy exploiter is hours of work, not a re-solve; it was never attempted. (The preflop *bust* audit the consult `:39` references is a different, contested question — see §2/§5 H5 — and does not bear on the over-folding risk.)

---

## 5. Hypotheses — confirmed / refuted / unprovable

**H1 — wrong objective reclassified the warning as a feature. CONFIRMED (Pass 1).** `:161` literally converts AF 5.45 high variance into "an asset" via the single-elim underdog frame. The same-day `finals_brief.md §1` already had the *correct* Swiss/cumulative structure, and `consult …:14` explicitly disavows the single-elim assumption — so the premise was knowably wrong even within the day's own artifacts.

**H5 — patch window consumed by postflop work, starving the preflop path. PARTIALLY CONFIRMED, demoted to supporting.** Every patch lane targeted the postflop commitment gate (`commitment.py`, `_can_commit`, `full_house_dominated`); preflop is "NOT audited / Unverified / Potentially dominant" in three artifacts (`postmortem:172`, `brief §5/§6`, `consult :39`). **But the claim that preflop was the *dominant loss source* is contested and on a count basis refuted by the team's own clean audit:** `thorp_leak_report.md:35` (qualifier, n=20) is **75% postflop**; only the 9-hand RIVER-TRIAGE subset on the patched build reads preflop-dominated. So "they fixed the wrong problem" cannot be asserted as settled — on the larger sample the postflop focus was count-appropriate. What *is* solid: the preflop path was never audited, and the over-folding-bleed risk (a separate, postflop behavioral mechanism) was never tested. The real failure is **untested-risk**, not provably-misallocated effort.

**H6 — oracle synthesis delivered the ship call with the wrong premise baked in; responsibility diffuse. CONFIRMED (Pass 1).** Ship call attributed to "oracle synthesis `new-chat-1FB6CB`"; rationale internally coherent but premised on single-elim. No named owner re-checked the premise; the post-mortem carrying it was never reconciled.

**H3 — the prediction had no owner / no test / no go-no-go threshold. CONFIRMED.** The risk is a prose "honest caveat" (`:163`); candidates by contrast had explicit numeric gates. Asymmetry is documented in §3.

**H8 — sunk-cost / status-quo attachment to the recovered "clean" artifact. PARTIALLY CONFIRMED.** Post-upload every entry repeats "bot frozen + live", "not a ship blocker (bot frozen + live)" (FINALS-UPLOADED), anchoring all later reasoning on the live artifact. This is reinforced by H2.

**H2 — the fresh R2 "don't touch the artifact / human-only upload" rule outranked the older rule-less leak concern. PARTIALLY CONFIRMED.** The ~24h-old, painful R2 rule produced a strong freeze/status-quo bias (FINALS-SHIP "Strategy code frozen"; FINALS-UPLOADED "Code frozen"). It is the *correct* rule; it happened to lock in an artifact with a known un-fixed hole. It outranked the leak concern in *effect*, not by explicit deliberation.

**H4 — time pressure collapsed the option space to a false binary. REFUTED for Pass 2.** Three options were explicitly carried (ship-as-is / data-retune / code-fix, `consult :5,:62`) and the middle data-only path was actually built and tested (FINALS-EXEC-6MAX Lane B). The space was not collapsed; the middle option simply failed acceptance.

**H7 — no premise-change review fired when the format was announced. REFUTED as stated; REFRAMED.** A review *did* fire — the 17:32 consult is explicitly a premise-change review ("format changed TODAY — reason from THIS, not older assumptions", `:9`). **What did NOT fire is a re-derivation of the *prior* (Pass-1) decision's rationale.** The post-mortem's `:161` justification ("single-elim underdog → variance is an asset") was never rewritten even though its premise was now known false. The review re-decided the *action* under the new premise but never reconciled the *recorded rationale*, so the dead premise survives in the canonical post-mortem to this day.

---

## 6. Inertia mechanisms, ranked by strength of evidence

1. **Premise-driven reframing of the warning (H1/H6).** Strongest and on-target. The single-elim/underdog frame turned the named liability into an "asset" in Pass 1 (`:161`), contradicting the same-day Swiss structure (`finals_brief.md §1`); coherent oracle synthesis made it look settled.
2. **No test/threshold mapped to the risk's mechanism (H3).** Airtight. The over-folding-exploit risk had no go/no-go gate and — critically — **no opponent in the harness could even measure it** (gauntlet = maniac + fixed templates + reference bots; the adaptive exploiter was a named blind spot, `consult :60`). Prose caveats cannot block a ship; candidates with numeric gates could and did.
3. **Live-artifact anchoring + freeze discipline (H8/H2).** Post-upload status-quo bias; the (correct) human-only/freeze rule reinforced "don't touch it."
4. **Rationale-reconciliation gap (H7 reframed).** The premise-change review re-decided the action but never re-derived the prior recorded rationale, leaving a dead premise canonized in the post-mortem.
5. **Preflop unaudited + unreconciled bust-split (H5, supporting).** Preflop was never audited; its magnitude was never cleanly established and the two audits conflict (qualifier 75% postflop vs 9-hand triage). Supporting context, not a provable misallocation.

Refuted: H4 (false binary). Reframed: H7. Demoted: H5.

---

## 7. The single highest-leverage gate (would have fired with only then-available info)

**Premise-tagged decision gate.** Phrased as a checkable rule:

> Every ship/no-ship STATUS entry MUST list its load-bearing premises as named, checkable assertions (e.g. `FORMAT=single-elim`, `OBJECTIVE=survive-bracket`, `DOMINANT-LOSS=postflop`). A decision may be marked GREEN only when **each premise is (a) verified against the current portal announcement and (b) supported by at least one run test artifact**. If any premise is unverified, the gate is AMBER and the decision cannot ship until the cheapest confirming test for that premise has run.

Why it fires at the time:
- Premise `FORMAT=single-elim` is **contradicted by the same-day `finals_brief.md §1`** (Swiss) → AMBER → forces reconciliation before the rationale stands → "variance is an asset" collapses (under Swiss/shrinkage it is a liability).
- The named risk "a sharp seed bet-folds us off pots" has **no test whose mechanism matches it** → AMBER → forces adding one over-folding exploiter to the gauntlet before GREEN.

This needs no new information — the format contradiction was on disk the same day, and the missing-exploiter gap was self-identified (`consult :60`).

**Mechanism-match rule (the key clause):** a test only discharges a risk if it exercises the *same* mechanism. A maniac (`aggressor`) cannot discharge an over-folding-exploit risk; a postflop disaster-spot probe cannot discharge a preflop risk. The harness must contain an opponent that *attacks the named hole*.

---

## 8. Concrete institutionalizing diff

**`CLAUDE.md` — add under "Status protocol":**

```
## Premise-tagged decisions (HARD — added 2026-06-06 post-finals)
Every ship/no-ship STATUS entry MUST list its load-bearing premises as named,
checkable assertions, e.g.:
  PREMISES: FORMAT=swiss-cumulative [verified: portal 06-04];
            DOMINANT-LOSS=preflop  [verified: thorp_leak_report.md:24-35];
            OBJECTIVE=max-extraction [verified: CLAUDE.md Finals FORMAT]
Rules:
1. A decision is GREEN only if EVERY premise is (a) reconciled against the
   current portal announcement AND (b) backed by >=1 run test artifact path.
2. Any unverified or stale premise => decision is AMBER; it may not ship until
   the cheapest confirming test for that premise has run and is logged.
3. When a premise changes (format/scoring/deadline), open a PREMISE-CHANGE
   review that RE-DERIVES the rationale of every still-standing decision that
   cited the old premise, and edits the original STATUS/postmortem entry in
   place (strike + correct) — re-deciding the action is not sufficient.
4. A risk named "potentially dominant", "exploitable hole", or "unverified" in
   any artifact is a blocking AMBER until tested by a probe whose MECHANISM
   MATCHES the risk (an over-folding exploiter for an over-folding risk; a
   preflop probe for a preflop risk) — a maniac/value-spewer does not count.
   Same numeric-gate discipline as candidate promotions. Prose caveats do not
   gate; mechanism-matched tests gate.
```

**`docs/playbooks/patch-window.md` — add to the acceptance checklist:** the gauntlet must include at least one **adaptive/sharp counter-exploiter** opponent (not only maniacs + fixed templates + reference bots), so that over-folding / polarization risks are *measurable*. Before any "ship-as-is", every named exploitable hole must have a mechanism-matched probe result logged, or the entry is AMBER.

**`docs/investigations/finals-prep-postmortem-2026-06-04.md:159-163` — strike-correct in place:** mark the "single-elim underdog → variance is an asset" rationale OBSOLETE and replace with the Swiss/cumulative re-derivation (variance is a liability under shrinkage), citing the 17:32 consult. (Currently the canonical post-mortem still carries the dead premise — see §9.)

---

## 9. What the post-mortem itself missed or rationalized

1. **It canonizes a dead premise.** `finals-prep-postmortem-2026-06-04.md:161` justifies ship-as-is with "single-elim bracket / #57 underdog / variance is an asset" — a premise the team itself disavowed the same day (`consult …:14`; `CLAUDE.md` Finals FORMAT). The post-mortem was written in the FINALS-RECON pass and **never reconciled** after the format flip, so it reads as a coherent justification for a decision whose stated reason was already known false. Under the correct (Swiss/cumulative + shrinkage) regime, the *same* polarization is a **liability**, and the post-mortem's own `:163` caveat is the truer reading — but `:161` overrides it.

2. **It mis-ranks the cause.** The post-mortem's headline cause is "artifact discipline" / the R2 upload mistake (`:143-155`). That is real but is about the *wrong bytes going live on 06-03*. The finals *strategy* failure is different: the named over-folding-exploit risk was shipped **without any mechanism-matched test**, because the harness contained no opponent that attacks an over-folder. The post-mortem lists the residual hole only as a table row (`:172`) and a TODO (`:180`), not as the central finding, and never notes that its own gauntlet could not have measured the risk.

3. **It conflates two different failure modes.** `:163` ("we can't safely de-polarize today") slides between the over-folding *bleed* risk (the one written down) and preflop *busting* (a different mechanism). It also treats the bust question as settled while the team's own data is contradictory (`thorp_leak_report.md:35` = 75% postflop vs the 9-hand RIVER-TRIAGE = preflop). The honest reading: the de-polarization *fix* was genuinely infeasible in-window, but *measuring* the risk with a sharp exploiter was feasible and skipped — the post-mortem does not distinguish these.

4. **It under-credits the premise-change review.** The post-mortem (FINALS-RECON vintage) predates and omits the 17:32 premise-change consult and the 17:59/18:25 re-decisions entirely; a reader of only the post-mortem would conclude no review fired (the naive H7), when in fact the review fired but failed to back-correct the prior rationale.

---

## Investigation Log
- Timeline reconstructed from `STATUS.md` gates: FINALS-RECON, FINALS-SHIP (16:43), FINALS-UPLOADED (~17:20 + format correction), FINALS-EXEC-6MAX (17:59), FINALS-EXEC-RIVER-TRIAGE (18:25).
- Risk-mention trace: `finals-prep-postmortem-2026-06-04.md:161,163,172`; `finals_brief.md §5,§6`; `thorp_leak_report.md:24-35,42-46,61`; `2026-06-04-173203…:9,14,37,39,59`.
- Format-premise contradiction verified across `CLAUDE.md` (Finals FORMAT), `finals_brief.md §1`, stale `docs/tournament-spec.md:9,57` + `docs/finals-strategy-2026-05-27.md:11,16,21`.
- Large transcript `prompt-exports/2026-06-04-frozen-finals-strategy.md` (284 KB) exceeds read cap; decisions cross-checked against STATUS gate log, which is authoritative and timestamped.
