# Scratch-improve Batch 2 — Report (2026-05-31)

**Outcome: NO gate-clearer. `submissions/v_final.zip` remains the active upload, unchanged.**
Locked artifact verified intact post-batch (both zips sha256 `e4b4a8f1...598`, identical,
canonical `src/`+`submissions/` clean). Nothing promoted; all lanes verified locked SHA start/end.

Operationally: 3 lanes launched; 2A and 2B hit the headless **stall detector** on their long pod/LBR
compute — but 2A had ALREADY produced its full decision-grade analysis before stalling (salvaged from
`recalib-codex/VERDICT.md` + `paired_analysis.json`), and 2B left a complete LBR implementation
(`lbr-impl/lbr_check.py`, scoring now running in background). 2C completed cleanly.

---

## KEY METHODOLOGY RESULT — resolves the "operating point" question
- **There is NO stable noisy-field operating point.** Seed base 142 (batch-1) was broken (locked C0
  floored). Lane 2A scanned 18 seed bases; base 900 was the ONLY one where locked C0 escaped the
  −10000 floor (35.7% bust) — but re-running base-900 C0 swings **36%→79% bust run-to-run** because
  `aggressor`/`toby_master` use UNSEEDED RNG (the engine seeds only card dealing).
- **The only decision-grade six-max field is the all-seeded deterministic subset**
  **`C0D = [hero, template, mathematician, shark, ref_bot_2]`** (locked-vs-locked: 33/40 byte-identical,
  paired median 0, noise stdev 714 — low-noise, not zero; `shark` has one minor unseeded branch).
  ALL no-p50/bust-regression claims must use C0D; C0/C1 (toby/aggressor) are **directional-only**
  effect-size reads. **This is the answer to the operating-point steer: use C0D, not a seed-base hunt.**

## Lane 2A — codex decision-grade verdict. NOT A CLEARER (small real regression).
- `sibling-gate/codex.zip` on C0D, 40 paired seeds, base 900, jobs=1:
  - locked p50 **+11500** (bust 0/40); codex p50 **+10125** (bust 1/40).
  - paired-diff **median −1750**, mean −2385; codex worse on **32/40**, better on 5/40 (~2.5σ over the
    714 noise floor). Bust delta +2.5pp (within tol). **C0D POD_PASS = FALSE** (chip regression).
- Batch-1 questions resolved: (a) codex's C0 "survival gain" was INFLATED by locked being floored at
  base 142 — it's a field-specific **anti-aggressor** effect that does NOT generalize; on the clean
  field codex is slightly WORSE (−1750/match), playing more marginal spots (510–573 decisions/match vs
  454–484) and bleeding small EV vs passive opponents. (b) the C1 toby bust worsening (+15pp) is
  zero-median, tail-driven, unresolvable at decision grade (toby unseeded) — human-MODIFY flag, not a gate signal.
- Disposition: NOT a clearer. Not junk — future work could try to keep the anti-aggressor robustness
  without the passive-field EV bleed.

## Lane 2C — claude vladimir-audit (re-scrubbed) decision-grade verdict. NOT A CLEARER (tradeoff).
- Re-scrubbed the 19 cosmetic leakage strings (18 comment/shim + 1 behavior-preserving rename
  `_stable_seed`->`_stable_hash`, value-verified identical) in a SCRATCH COPY; leakage now PASSES.
  Full gate: validator/import/leakage PASS, edge PASS, smoke PASS (200/200, +5700 vs template).
- C0D, 24 paired seeds, base 700, jobs=1: locked p50 12000 (bust 1/24); claude p50 **13900** (bust 2/24).
  Paired-diff **p50 +2250** (claude better on 14/24). **CHIP guard PASSES; BUST guard FAILS** (2/24 vs
  1/24 — on the noiseless field even +1 bust is real divergence, n_byte_identical=0).
- Disposition: a genuine **risk/reward TRADEOFF** (chip-competitive-to-better, fatter left tail) flagged
  for human MODIFY — NOT a dominated reject, but does not clear the no-bust-regression bar as-is.

## Lane 2B — trustworthy LBR. TOOL BUILT; scoring in progress.
- `lbr-impl/lbr_check.py` (537 LOC) implements **match-play LBR** (Lisy & Bowling 2017): drives full
  HU hands through the real engine with one-step EV best-response + passive tail (the principled
  formulation; the prior synthetic-spot stub double-counted dead money and exploded the number).
- Scoring v_final (sanity anchor) + codex + claude_rescrubbed running in BACKGROUND (hands=400,
  rollouts=20); numbers pending. Sanity target: v_final near historical preflop ~18 / aggregate ~7.4
  mbb/g (well within caps 100/200) would validate the tool.
- Until validated+promoted by a human, canonical `tools/exploit_check.py` stays a stub — the gate's
  exploit arm is still officially unmeasured.

---

## Net after batch 2
No candidate clears; locked ships unchanged. Two **near-miss candidates** flagged for human MODIFY:
- **codex** (LBR spot corrections): small but real clean-field regression (−1750/match); strong but
  non-generalizing anti-aggressor robustness.
- **claude** (vladimir-audit): chip-up / bust-up **tradeoff** (+2250 p50, +1 bust on 24 seeds).

Gate infra hardened: **decision-grade field identified (C0D)**; **LBR implementation built** (scoring
pending); the six-max gate's fundamental limit (unseeded opponents → noisy C0/C1) is now characterized.

**Promotion bar unchanged:** no artifact replaces `v_final.zip` without clearing the FULL gate
(incl. six-max no p50/bust regression on C0D) and only via explicit human MODIFY.
