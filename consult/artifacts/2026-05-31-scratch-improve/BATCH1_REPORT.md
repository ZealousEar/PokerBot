# Scratch-improve Batch 1 — Report (2026-05-31)

**Outcome: NO gate-clearer. `submissions/v_final.zip` remains the active upload, unchanged.**
Nothing promoted. Locked artifact verified intact AFTER the batch: both
`submissions/v_final.zip` and `submissions/best_green.zip` sha256 ==
`e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`, byte-identical,
`git status -- submissions/` clean. All three lanes reported `protected_sha_ok=true`.

Scope: one structured batch of the 24h finals scratch effort. Qualifier ships locked
regardless; this is finals/patch-window candidate development. Deliverables under
`consult/artifacts/2026-05-31-scratch-improve/{gate-harness,overlay-cap,sibling-gate}/`.

---

## Cross-cutting infrastructure findings (these matter more than any single candidate)

1. **Source-of-truth for the shipped strategy = commit `a00561c` (branch `release/v_final-e4b4a8f1`).**
   `v_final.zip` == `a00561c` byte-for-byte (Lane B). `a00561c:src/bot.py` is 196 LOC of
   real logic (opponent_model 111, ranges 76, postflop/preflop 53). BUT `main:src/bot.py`
   and the current checkout branch (`tooling/postflop-trap-extractor-2026-05-29`) are the
   **48-line G0 scaffold stub** — the `a00561c` commit message says "promote ... onto main"
   but that promote never actually landed on `main`. **Action for 06-02: branch the patch
   window from `a00561c` / `release/v_final-e4b4a8f1` (or a candidate worktree forked from it),
   NOT from canonical `main`/current checkout.** Separately, reconcile `main`.

2. **The six-max paired-pod gate is statistically noisy as specified.** Decisive-pod opponents
   `toby_master` and `aggressor` use **unseeded internal mixed-strategy RNG** (engine seeds only
   card dealing). Locked-vs-locked, same seed, jobs=1 swung bust -> +37k chips. Consequences:
   - **`jobs=1` is mandatory** (jobs>1 corrupts pairing outright).
   - Paired differencing **cannot isolate a sub-stack effect** when a pod contains a
     non-reproducible opponent (every decisive pod does).
   - At seed base 142, **C0 is saturation-blind** (locked busts ~70-100%, pinned to the -10000
     floor). C1 is the only real discriminator at that operating point.
   - **Default (0,0) tolerances FALSE-FAIL a byte-identical bot.** Calibrated discrimination
     band: `p50_tol=6000`, `bust_tol=0.15` (Lane A).
   - **Recommendation: before 06-02, a human picks a field/seed base that keeps locked OFF the
     bust floor and re-calibrates; prefer an exact-paired deterministic-subset field
     (hero+template+mathematician+shark+ref_bot_2) for low-noise A/B, reserving the full
     toby/aggressor field for directional signal only.**

3. **`tools/exploit_check.py` (LBR) is an unimplemented TODO stub** that prints and exits 0.
   The promotion gate's "exploit/LBR caps" arm therefore **cannot be affirmatively measured**
   today. Lane C also showed codex's *forensic* LBR suite is circular (locked v_final scores
   4883 mbb/g / 24x over cap on it, i.e. not the gate v_final actually passed). **LBR is a
   real gap in the gate itself** — implement a trustworthy LBR before relying on that arm.

---

## Lane A — gate harness (infra). DELIVERED.
- `gate_harness.py` + `README.md`: parameterized `--candidate/--locked/--pods/--seed-base/--seeds`,
  fail-fast (validator+import+leakage -> edge+smoke -> paired pods C0 then C1), paired-median
  PASS/FAIL on no-p50-regression AND no-bust-regression, protected-SHA guards start+end.
- Validated honestly: byte-identical no-op -> GATE_CLEAR; G0 scaffold -> GATE_FAIL (C1 Δp50 -11962).
- Caveats (carried into finding #2): jobs=1, calibrated tolerances, C0 saturation, C3/C4
  uncalibrated + slow (public bots hit the 2s timeout; ~tens of min for 40 seeds).
- `gate_clearer=false` (infra lane; no promotable candidate).

## Lane B — overlay-cap reduction. NEGATIVE.
- The premised `MAX_DEVIATION_PP ~0.20` scalar **does not exist** in the shipped artifact (it
  was superseded by the X1 discrete preflop-only `_pressure_preflop_overlay`). Thesis re-cast as
  a monotone shove-removal ladder: `cap015` (shoves -> premiums only), `cap010` (shoves removed).
- Both cleared every DETERMINISTIC gate (validator, import, leakage, edge, authoritative Docker smoke).
- The overlay fires ~1/1000 preflop decisions (peak ~11.5/1000 public field) and only ever
  REMOVES aggression (downside-only, thesis-aligned). Exact-paired deterministic-subset pod
  (24 seeds, zero sim noise): cap015 p50 -100, cap010 p50 -100 vs locked — **no distinguishable
  improvement OR regression**; the intervention bites almost only in the unmeasurable pods.
- `gate_clearer=false`. Disposition: **shelve** (near-no-op against the passive field).

## Lane C — in-flight sibling candidates. NEGATIVE, but codex carries a real signal.
- **claude (`vladimir-audit`): died at Stage 1** — authoritative (canonical) leakage audit FAIL,
  19 hits, **all comment/shim hygiene strings** (`branch`/`seed`/`snapshot`/`v_final`/`v3_hardened`/
  `aggressor`/`v1_blueprint`), NOT runtime identity branching. **VERIFIED post-hoc by reading the
  flagged lines**: `opponent_model.py:149-150` is an overlay-describing comment, `bot.py:307`
  literally disclaims env-branching, `branch` hits are code-structure terms in docstrings — no live
  identity branching. Strategy never evaluated.
  Disposition: **scrub the strings + package.py shim text, then re-gate** (its strategy diff is
  large and untested; claude's own leakage tool passes only because its forbidden-list is narrower).
- **codex (`w4-track-1-lbr` LBR spot corrections):** cleared static + edge (73 passed) +
  authoritative Docker smoke; LBR arm inconclusive (circular forensic suite). It then ran 40 paired
  seeds vs locked **at seed base 142 — which finding #2 proves is a BROKEN operating point** (C0
  saturation-blind: locked busts 75%, floored at -10000). **Both results below are therefore
  MEASUREMENT-INVALID for a gate decision** and must NOT be weighed against each other:
  - C0_BASELINE: codex bust 22.5% vs locked 75%, p50 +18875 vs -10000, 38/40 seeds >= locked,
    paired sum +781,857 — a real, consistent behavioral signal (codex survives an aggressor-heavy
    regime that floors locked) but measured against an artificially floored baseline.
  - C1_TOBY_WEAK_FIELD: codex bust 75% vs locked 45%, p50 -10000 vs -951; median paired diff 0,
    only 19/40 seeds worse, mean dragged by a few -60000 toby river-bust seeds — noisy/tail-driven,
    same miscalibrated point.
  - Disposition: **PROMISING BEHAVIORAL SIGNAL, MEASUREMENT-INVALID until re-run at a calibrated
    operating point** (deterministic-subset A/B + non-saturating seed base, finding #2). NOT a gate
    pass; the C0 "gain" and C1 "regression" cannot be compared off-calibration. Self-label
    "forensic, not for promotion" corroborated. -> resolved in batch 2.

---

## Recommended next batches (queued, not yet run)
- **B2a:** re-calibrate the pod gate operating point per finding #2 (field/seed base keeping locked
  off the bust floor; deterministic-subset A/B + directional toby field), then re-run codex C0/C1
  at higher seed count to resolve the Toby hole.
- **B2b:** implement a trustworthy `exploit_check.py` LBR so the gate's exploit arm is real.
- **B2c:** scrub claude `vladimir-audit` leakage strings and re-gate its (large, untested) strategy diff.
- **Patch-window prep:** confirm the 06-02 workflow branches from `a00561c`/`release/v_final-e4b4a8f1`,
  and reconcile `main` (advertises a promote that did not land).

**Promotion bar unchanged:** no artifact replaces `v_final.zip` unless it clears the FULL gate —
validator; import; leakage; edge; smoke; exploit/LBR caps; reference all-template benchmark;
public regression; trigger H2H; **six-max pods with no p50/bust regression** — and only via explicit human MODIFY.
