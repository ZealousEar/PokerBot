# LANE 2A — Recalibrated Pod-Gate Operating Point + Decision-Grade Codex Verdict (2026-05-31)

**gate_clearer = FALSE.** Codex does NOT clear the full gate. On the calibrated, low-noise,
decision-grade field, codex shows a REAL, systematic median chip regression vs locked.
NOTHING auto-promoted; locked `v_final.zip` remains the upload target. Candidate flagged for
human MODIFY review only.

Protected SHA `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` verified for
`submissions/{v_final,best_green}.zip` at lane START and END (unchanged; never touched). No
`release/` dir exists; nothing written to `submissions/`. Canonical `src/` and sibling worktrees
not edited (all work artifact-local under this subdir; candidate run through engine as a zip).

Candidate: `sibling-gate/codex.zip` sha256 `e2ba542b79ca6a026fdbad30274e818d71ad75d0e2cfdef499afaa0b4e5fa296`
(byte-identical to batch-1; SHA-confirmed).

---

## STEP 1 — Calibrated operating point

**Chosen seed base = 900** (only non-saturating base found in 18 scanned). All pods run at
**jobs=1, 400 hands** (jobs>1 corrupts pairing per harness README).

### Seed-base scan (locked-only C0 = [hero, template, aggressor, mathematician, shark, ref_bot_2])
18 bases scanned (142,200,300,400,500,600,700,800,900–1800), 14 seeds each:

| base | locked C0 bust | locked C0 p50 | off −10000 floor? |
| ---: | ---: | ---: | :-: |
| **900** | **5/14 (35.7%)** | **+6617** | **YES** |
| 300 / 800 / 1300 / 1400 / 1600 | 57% | −10000 | no |
| 142 (batch-1 gate base) | 64% | −10000 | no (BROKEN) |
| 400 / 500 / 1000 | 86% | −10000 | no |

Base 142 confirmed broken: locked busts 64%, p50 pinned at the −10000 floor. Base 900 is the
single base where locked's C0 p50 escapes the floor.

### CRITICAL FINDING — C0 has NO stable operating point (answers Step-2(a) on its own)
Locked-only C0 on the EXACT same 14 seeds (900–913), three independent runs, jobs=1:
bust = **5/14 → 9/14 → 7/14**, and **4 of 14 seeds (900, 905, 906, 911) FLIP their bust
outcome run-to-run**. Same seed, same hero, same jobs=1. Cause: `aggressor` uses unseeded
`random.random()`; the engine seeds only card dealing, not opponent RNG. At 24 seeds base-900
C0 bust climbs to 79% (the favorable 14-seed window was sampling luck). **Conclusion: locked C0
floors at ~every base because aggressor is unseeded — a field property, not a sampling gap. The
"<50% bust base" target is not a reliable point; C0/C1 are directional-only, never decision-grade.**

### Decision-grade field confirmed: C0D = [hero, template, mathematician, shark, ref_bot_2]
This is the A/B for any no-regression claim. Reproducibility re-measured at base 900 (NOT assumed
from Lane B): locked-vs-locked, 40 seeds, jobs=1 → **33/40 seeds byte-identical**, paired-diff
**median = 0**, mean = −165, stdev = 714, all |noise| ≤ 2000.
- **Correction to the task/Lane-B premise:** C0D is LOW-noise, NOT zero-noise. `shark/bot.py:49`
  fires unseeded `random.random() < 0.4` when `position > 0.6`, perturbing ~7/40 seeds.
  (`template` imports random but makes 0 random.* calls on the decision path; mathematician /
  ref_bot_2 have no RNG.) The residual noise floor (median 0, stdev 714) is small enough that the
  paired median remains a decision-grade signal — but it is a floor, not exactly 0.

---

## STEP 2 — Codex vs locked at the calibrated point (base 900, jobs=1)

### (DECISION-GRADE) C0D_DETERMINISTIC_SUBSET — 40 paired seeds
| hero | chip-delta p50 | mean | bust |
| --- | ---: | ---: | ---: |
| locked v_final | +11500 | +11424 | 0/40 |
| codex | +10125 | +9039 | 1/40 |

- **Paired diff (codex − locked): median = −1750, mean = −2385, stdev = 4060, range [−20850, +3562].**
- **Robust to the locked draw:** vs an independent 2nd locked pass, median = −1725, mean = −2550.
- **Sign test: codex worse than BOTH locked passes on 32/40 seeds, better on only 5/40** (0 ties
  vs pass1). Only ONE seed (926) is a bust cascade (−20850); excluding it the regression persists
  (31/39 non-bust seeds favor locked, diffs tightly clustered ~−1500 to −2200).
- **Signal ≫ noise:** regression median −1750 vs noise-floor median 0 / stdev 714 (≈2.5σ); the
  32/40 sign split is overwhelming. **This is real systematic signal, not noise.**
- Tell: codex makes consistently MORE decisions/match (510–573 vs locked 454–484) — it plays more
  marginal spots (its "LBR spot corrections" call/continue where the blueprint folds), bleeding
  small EV vs this passive field.
- **C0D POD_PASS = FALSE** (p50 regression −1750; bust delta +2.5pp is within tolerance — the
  regression is on chips, not busts).

### (DIRECTIONAL-ONLY) C0_BASELINE — answers (a) — 40 paired seeds
| hero | p50 | mean | bust |
| --- | ---: | ---: | ---: |
| locked | −10000 (floored) | −5569 | 30/40 (75%) |
| codex | +18165 | +16061 | 5/40 (12.5%) |
- Paired diff median +24385; codex bust 12.5% vs locked 75% (−62.5pp).
- **(a) ANSWER: codex's survival improvement is directionally REAL and LARGE — it persists even on
  a NON-fully-floored locked baseline here (locked mean −5569, not pinned to −10000).** BUT it is
  NOT decision-grade: this field is aggressor-RNG-dominated (locked C0 bust swings 35–79%
  run-to-run, see Step 1), so the magnitude is an estimate, not a measurement. The gain is an
  anti-aggressor effect; C0D (aggressor removed) shows codex is actually slightly WORSE — so the
  C0 gain does NOT generalize to the clean field.

### (DIRECTIONAL-ONLY) C1_SINGLE_TOBY_WEAK_FIELD — answers (b) — 40 paired seeds
| hero | p50 | mean | bust |
| --- | ---: | ---: | ---: |
| locked | +7545 | +10976 | 15/40 (37.5%) |
| codex | −10000 | +4095 | 21/40 (52.5%) |
- Paired diff median = 0, mean = −6881, stdev = 19056 (bimodal, tail-driven by a few −60000 seeds).
- **(b) ANSWER: the C1 toby effect is a bust-rate worsening (+15pp, 21 vs 15 ≈ 2σ) that is
  ZERO-MEDIAN and TAIL-DRIVEN in the noisy unseeded-toby regime — same shape batch-1 saw.** Cannot
  be cleanly classified as "real regression" vs "tail noise" because toby_master is unseeded
  (paired differencing cannot cancel its mixed-strategy RNG). DIRECTIONAL-ONLY; not decision-grade.
  This is a real human-MODIFY flag (possible toby-shaped hole) but it does NOT and must not gate.

---

## STEP 3 — Verdict

**gate_clearer = FALSE.** `gate_clearer = static ∧ edge ∧ smoke ∧ (C0D no p50/bust regression)`:
- Static (validator / canonical leakage / import_audit): **PASS** (re-run this lane, all exit 0).
- Edge (73 passed) + smoke (docker, vs template, 200 hands, 0 hero/bot errors): **PASS by
  SHA-identity** — codex.zip sha == batch-1's `e2ba542b…`, so batch-1's verdicts transfer.
- **C0D decision-grade: FAIL** — real systematic median regression −1750/match (≈2.5σ over noise
  floor, 32/40 seeds worse, robust to locked draw).

### Resolution of the two batch-1 questions
- **(a) Did codex's survival improvement persist on a NON-floored baseline, or was it a floor
  artifact?** BOTH, in different senses. The C0 (anti-aggressor) survival gain is directionally
  real and large and is NOT purely a floored-locked artifact (it holds vs a partly-floored locked).
  BUT it is field-specific to the unseeded aggressor and does NOT carry to the clean field: with
  aggressor removed (C0D), codex is slightly WORSE (−1750 median). So batch-1's headline "+19546 C0
  gain" WAS measurement-inflated by locked being pinned to −10000 at base 142 — the true clean-field
  effect is a small negative, not a large positive.
- **(b) Is the C1 toby effect a real regression or tail noise?** UNRESOLVABLE at decision grade —
  toby is unseeded, so the +15pp bust / zero-median / high-variance signal cannot be isolated from
  mixed-strategy RNG. Directionally it looks like a modest bust-rate worsening worth a human look,
  not a clean collapse. It does not gate.

### Honest shape (vs batch-1)
Recalibration changed the verdict's BASIS, not its outcome. Batch-1 gated codex on a broken base
(142, locked floored): apparent large C0 gain + ambiguous C1 loss, both measurement-invalid.
At the calibrated point, the clean-field truth is the opposite of the C0 headline: **codex is a
small but REAL and SYSTEMATIC regression on the decision-grade field (−1750 median/match), with a
field-specific anti-aggressor survival gain that does not generalize, plus an unresolved
directional toby bust concern.** Codex is NOT a clearer. Not junk either — a human could investigate
whether the LBR spot corrections can keep the anti-aggressor robustness without bleeding EV vs
passive fields (C0D), but as-is it regresses the gate.

## Human flags
1. C0D is low-noise not zero-noise (shark RNG, ~7/40 seeds); the floor median is still 0 so the
   paired median is decision-grade, but do not call C0D "exactly deterministic."
2. C0/C1 are structurally non-decision-grade (unseeded aggressor/toby). Any future gate must use
   C0D (or another all-seeded field) for no-regression claims; report C0/C1 as effect-size-vs-noise
   directional reads only.
3. Locked v_final busts the aggressor reference field 57–86% at almost every seed base — a known
   property of the shipped artifact vs that specific bot, not a defect introduced here.

## Artifacts (all under this subdir)
- `run_pods.py` (scratch copy), `paired_analysis.py`, `seedbase_scan.py`
- `seedbase_scan_results.json`, `seedbase_scan2_results.json`, `seedbase_900_24seed.json`,
  `seedbase_900_14seed_run3.json` (operating-point + C0-instability evidence)
- `gate_locked/`, `gate_codex/`, `gate_locked_pass2/` (matches.jsonl, protected-sha guards)
- `repro_A/`, `repro_B/`, `repro_codex/` (C0D determinism probes)
- `paired_analysis.json` (full per-pod paired distributions + per-seed C0D diffs)
- `static_{validator,leakage,import_audit}.log`
