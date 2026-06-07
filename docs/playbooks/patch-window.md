# Patch Window Playbook — 2026-06-02 → 2026-06-03

24-hour window between qualifier results (released 2026-06-02 morning, London time) and finals submission cutoff (2026-06-03 evening). Goal: ingest the qualifier hand histories, derive population priors, and ship at most one updated artifact for the finals bracket.

**Hard rule:** if any post-patch gate fails, the finals submission **reverts to the qualifier `v_final.zip`** (sha `e4b4a8f1…598`). A new artifact ships only if every gate the qualifier artifact passed, the patched artifact also passes — at the same or better numeric levels.

**Wall-clock budget:** 5 hours 45 minutes of work spread across the 24-hour window. Sleep is allowed between phases. Step times below sum to that budget; pad each by ~10% for I/O.

---

## Phase 0 — Pre-window readiness check (10 min, evening of 2026-06-01 after qualifier upload)

Run once the qualifier upload is confirmed. Goal: enter the patch window with a clean baseline, not from cold.

```bash
cd ~/Code/PokerBot
# 1. Tree is clean and on the canonical ship state.
git status
sha256sum submissions/v_final.zip submissions/best_green.zip
# Expected: both = e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598

# 2. The analyzer tool is present and importable.
python -c "import importlib.util as u; print(u.find_spec('tools.analyze_hand_histories'))"
ls -la tools/analyze_hand_histories.py
# Expected: file exists; spec resolves; per AGENTS.md it lives under tools/.

# 3. Synthetic-priors fallback is reachable.
ls -la consults/2026-05-27-overnight-D/priors/V*_priors.npz 2>/dev/null \
  || ls -la ../PokerBot-claude/consults/2026-05-27-overnight-D/priors/V*_priors.npz
# Expected: 5 .npz files (V1..V5). At least one must be readable.

# 4. data/ slot ready to receive finals_priors.npz.
ls -la data/
# Expected: directory exists, no stale finals_priors.npz.
```

If any of (1)–(4) fails, fix it tonight, not during the patch window. The window is for analysis, not infra repair.

---

## Phase 1 — Download hand histories (15 min, 2026-06-02 ~08:00)

Hand histories are released as JSON via the Fullhouse Hackathon platform. Schema is **unknown until release** — do not hardcode field names; the analyzer in Phase 3 introspects from the first record.

```bash
mkdir -p data/qualifier_histories_2026-06-02/
cd data/qualifier_histories_2026-06-02/

# 1. Download the bundle from the platform (manual — drag from portal,
#    or curl with whatever auth token they issue).
#    Expected: one .zip or .tar.gz containing N .json files, one per match.

# 2. Extract.
unzip -o <downloaded-bundle>.zip
ls -la *.json | wc -l
# Record the count; you will need it for Phase 3 sanity-check.

# 3. Inspect ONE record's schema before processing the rest.
python -c "import json; d=json.load(open('$(ls *.json | head -1)')); print(list(d.keys())[:10]); print(json.dumps(d, indent=2)[:2000])"
```

**Sanity gate:** Confirm the bundle contains records for **at least 30 matches** (you played at least 30 rounds in a Swiss qualifier of any non-trivial field). If you see < 5 records, the download is incomplete — re-download before continuing. If the JSON is well-formed but missing your bot's match results, contact the organizers; the patch-window window does not extend.

---

## Phase 2 — Manual inspection of the schema (20 min)

Before unleashing the analyzer, read one full record by hand. Goal: understand which fields carry the population behavior signal.

```bash
# Look for these signal-carrying fields. Names will vary; the analyzer
# detects from the first record, but a 20-minute eyeball lets you spot
# weird encodings (e.g., actions as strings vs ints, sizings as bb vs chips,
# pot percentages vs raw amounts).
python -m json.tool $(ls data/qualifier_histories_2026-06-02/*.json | head -1) | less

# Specifically check:
#   - Per-hand action sequence (preflop, flop, turn, river)
#   - Action representation (raise amounts as total chips? as % pot? as bb?)
#   - Player identification (anonymized? real names?)
#   - Position labels (UTG/MP/CO/BTN/SB/BB? numeric seat?)
#   - Hand outcomes (chip delta? showdown cards?)
```

Note any unexpected encoding in a scratch file. If the schema diverges meaningfully from what `tools/analyze_hand_histories.py` expects, **skip to Phase 2.5 fallback** below.

---

## Phase 2.5 — Fallback if analyzer cannot parse (only if Phase 2 reveals incompatible schema)

If the analyzer fails to extract priors (silent zero-valued output, or exceptions), do not block the finals on it. Use the **Lane D synthetic priors** as a baseline.

```bash
# Pick the synthetic prior that best matches the observed schema family.
# Lane D ran 5 variants (V1..V5) covering snake_case, camelCase, partial
# fields, alt action names, and nested schemas.
ls ../PokerBot-claude/consults/2026-05-27-overnight-D/priors/
cat ../PokerBot-claude/consults/2026-05-27-overnight-D/RESULTS.md

# Pick the one whose source synthetic JSON looks closest to the real
# downloaded schema.
cp ../PokerBot-claude/consults/2026-05-27-overnight-D/priors/V<n>_priors.npz \
   data/finals_priors.npz

# Record the substitution in STATUS.md verbatim:
#   "Phase 2.5 fallback engaged: analyzer failed on real schema; using
#    Lane D synthetic V<n> priors as data/finals_priors.npz."
```

Then jump to Phase 4 (re-package). **Do not** attempt to retro-fit the analyzer during the patch window — schema reverse-engineering is a 4+ hour task and burns the budget.

---

## Phase 3 — Run the analyzer (45 min)

```bash
cd ~/Code/PokerBot

python tools/analyze_hand_histories.py \
  --input data/qualifier_histories_2026-06-02/ \
  --output data/finals_priors.npz \
  --report data/finals_priors_report.txt

# Expected:
#   - Exit 0, non-degenerate .npz file written.
#   - data/finals_priors.npz size > 1 KB and < 10 MB
#     (Lane D synthetic outputs were ~5–50 KB).
#   - data/finals_priors_report.txt lists, per field:
#       * population VPIP, PFR, aggression-fraction
#       * fold-to-c-bet
#       * average sizing percentiles by street
#       * common preflop action sequences (top 10)
#       * any bot-cluster fingerprints the analyzer flagged
```

### Sanity gate on extracted priors

| Field | Expected range | Action if outside |
|---|---|---|
| Population VPIP | 18–40% | Outside → likely schema mis-parse. Inspect `data/finals_priors_report.txt`; consider Phase 2.5 fallback. |
| PFR | 12–30% | Outside → same diagnosis. |
| Aggression-fraction | 0.3–0.7 | Outside → same diagnosis. |
| Fold-to-c-bet | 30–65% | Outside → schema mismatch on action labels. |
| Distinct opponent clusters | 2–8 | < 2 → analyzer over-pooled; > 10 → fragmenting. |

If two or more fields are outside their expected ranges, **assume schema mismatch and use Phase 2.5 fallback**. Do not ship priors derived from a misread schema — they would actively hurt the overlay rather than tune it.

---

## Phase 4 — Update only the overlay; do NOT touch baseline strategy (60 min)

The shipped overlay reads from `data/finals_priors.npz` at module-import (warmup) time. Per AGENTS.md and the existing patch-window contract:

- **Allowed edits:** `src/opponent_model.py` threshold tweaks, range adjustments in `src/preflop_lookup.py` *if* the priors show a population VPIP very different from our baseline assumption, and the analyzer's `data/finals_priors.npz` itself.
- **Forbidden edits:** `src/postflop.py` flop strategy, `src/bot.py` blueprint logic, `src/equity.py` Monte Carlo wiring, `src/sizing.py` sizing tree, any solver re-training.
- **Forbidden:** introducing new env-var branches, opponent-identity strings, or shim flags. These trip `audit_strategy_leakage` and disqualify the artifact.

```bash
# Inspect what the new priors imply for overlay tuning.
python - <<'PY'
import numpy as np
p = np.load("data/finals_priors.npz", allow_pickle=True)
for k in p.files:
    print(f"{k}: {p[k]}")
PY

# Edit src/opponent_model.py thresholds to align with the observed
# population statistics. Keep MAX_DEVIATION_PP at 0.20 unless Lane A's
# overnight sweep promoted a different value into the qualifier artifact
# (see consults/2026-05-27-overnight-A/SUMMARY.md).

# Run leakage audit IMMEDIATELY after each edit, not at the end.
python tools/audit_strategy_leakage.py --src src/
# Expected: PASS, 0 hits.
```

Wall-clock budget for this phase: 60 min. If you find yourself rewriting `decide_blueprint_only` or the postflop module, you are out of scope — revert and ship the qualifier `v_final.zip` unchanged.

### Patch-window freeze lanes (HARD — added 2026-06-06 post-finals)

Classify every proposed edit before touching code:

1. **STRATEGY-SHAPE changes** — polarization level, calling-range width, bluff/value mix, sizing-tree shape, overlay cap, or any change that alters the strategic distribution — must be locked early after early verification. These reopen the full verification surface: validator/import/edge/smoke, all-template paired benchmarks, LBR/exploitability, mechanism-matched counter-exploiter probes, and manual rationale review. They are not safe late-window edits. The Thorp over-fold shape (call 6.4% / fold 58.9%) could not be safely de-polarized in the 2026-06-04 90-minute window because widening the calling range is a strategy-shape change, not a hotfix.
2. **HOTFIXES** — specific, narrowly-scoped bug fixes with an identified failing behavior and minimal blast radius — may be considered late if they have a targeted failing probe, pass the smallest relevant regression suite, and do not change strategy shape outside the bug path.

If an edit cannot be classified cleanly, treat it as STRATEGY-SHAPE and require early-lock/full-gauntlet treatment.

---

## Phase 5 — Re-package and validate (15 min)

```bash
cd ~/Code/PokerBot

# 1. Build the finals artifact.
python tools/package.py --output submissions/v_finals.zip --strict

# 2. Engine-authoritative validator (AST + size).
python ext/fullhouse-engine/sandbox/validator.py submissions/v_finals.zip
# Expected: ✅ PASSED, 4/4 TEST_STATES.

# 3. Size check.
du -h submissions/v_finals.zip
unzip -l submissions/v_finals.zip
# Expected: total ≤ 250 MB; bot.py at root ≤ 5 MB; data/ ≤ 200 MB;
#           no other .py at root; no .py inside data/; no symlinks.

# 4. Compute and record the SHA.
sha256sum submissions/v_finals.zip
# Record this in STATUS.md; it replaces e4b4a8f1…598 for finals.
```

If validator FAILS, **revert immediately**: `rm submissions/v_finals.zip && git checkout -- src/` (and `data/finals_priors.npz` if it was just regenerated). Ship qualifier `v_final.zip` instead.

---

## Phase 6 — Sandbox smoke + import audit (20 min)

```bash
# 1. Cold-start import budget.
python tools/import_audit.py --max-seconds 1.5 --max-mb 400
# Expected: cold < 1.5s, RSS < 400 MB, zero forbidden imports.
#   data/finals_priors.npz must load inside the 30s warmup budget; if
#   import_audit shows the new priors push cold-start over 1.5s, the
#   priors file is too big — slim it down before continuing.

# 2. Real Docker sandbox smoke.
python tools/smoke_run.py --zip submissions/v_finals.zip --hands 200
# Expected: 200/200 hands, 0 hero_errors, chip delta > 0 vs reference bot.

# 3. Edge cases.
pytest tests/edge_cases -x
# Expected: 25/25.

# 4. Leakage audit on the packaged artifact.
python tools/audit_strategy_leakage.py --zip submissions/v_finals.zip
# Expected: PASS, 0 hits across 14 tokens.
```

If any of 1–4 fails, **revert and ship qualifier `v_final.zip`**. The finals artifact must clear every gate the qualifier artifact cleared.

---

## Phase 7 — Regression benchmark (90 min — longest single step)

This is the load-bearing acceptance gate. The patched artifact must not regress on any of the canonical reference templates, must hold its own against the LBR exploitability bound, and must include at least one adaptive/sharp counter-exploiter in the gauntlet — not only maniacs, fixed templates, and reference bots. Before any promote or ship-as-is decision, every named exploitable hole must have a mechanism-matched probe result logged, or the gate is AMBER.

```bash
# 1. All-templates benchmark, artifact-bound.
python tools/benchmark.py --all-templates --hands 10000 \
  --paired-seed-base 42 --paired-seed-count 10 \
  --zip submissions/v_finals.zip \
  | tee logs/finals_benchmark.log

# Acceptance per-template (qualifier baseline numbers):
#   template     >= +71.82 - 1.5*SE     CI low > 0
#   aggressor    >= +112.63 - 1.5*SE    CI low > 0  (wide CI tolerated; baseline CI [+61.70, +158.19])
#   mathematician>= +144.60 - 1.5*SE    CI low > 0
#   shark        >= +70.16 - 1.5*SE     CI low > 0
#   ref_bot_2    >= +144.60 - 1.5*SE    CI low > 0
# Hard rule: NO template may regress with statistical significance — i.e.,
# the difference (candidate_mean - qualifier_mean) must have CI excluding
# a negative value. Use paired-seed bootstrap for the CI estimate.
# This matches the Lane A acceptance gate in docs/morning-promotion-checklist.md
# Section 1 — same SE framing, same gate semantics.

# 2. Overlay ablation (must show non-trivial overlay value).
python tools/benchmark.py --ablate-overlay --hands 10000 \
  --zip submissions/v_finals.zip \
  | tee logs/finals_ablate.log

# Acceptance: gain >= +3 bb/100 (qualifier baseline posted +32.53).

# 3. LBR exploitability guard.
python tools/exploit_check.py --zip submissions/v_finals.zip \
  --max-preflop-mbb 100 --max-aggregate-mbb 200 \
  | tee logs/finals_lbr.log

# Acceptance: preflop <= 100 mbb/g, aggregate <= 200 mbb/g.
# Qualifier baseline posted preflop=18.0, aggregate=7.4.
```

### Acceptance criteria for the finals artifact (must hold all)

| Gate | Threshold | Qualifier value |
|---|---|---|
| All-templates bb/100 mean | ≥ qualifier − 1.5×SE (per template), paired-seed bootstrap | template +71.82, aggressor +112.63, math +144.60, shark +70.16, ref_bot_2 +144.60 |
| All-templates regression CI | `(candidate − qualifier)` CI low > 0 (every template) | n/a — same artifact |
| All-templates CI low (absolute) | > 0 every template | all > 0 currently |
| Overlay ablation gain | ≥ +3 bb/100 | +32.53 |
| LBR preflop | ≤ 100 mbb/g | 18.0 |
| LBR aggregate | ≤ 200 mbb/g | 7.4 |
| Adaptive/sharp counter-exploiter | >=1 gauntlet opponent attacks named holes adaptively or sharply; maniacs/fixed templates/reference bots alone do not satisfy this | n/a |
| Mechanism-matched probes | Every named "potentially dominant" / "exploitable hole" / "unverified" risk has a logged result artifact and numeric gate; otherwise AMBER | n/a |
| Validator | PASSED 4/4 | PASSED |
| Smoke | 200/200, 0 errors | 200/200, +14 500 chips |
| Edge cases | 25/25 | 25/25 |
| Import audit | < 1.5 s / < 400 MB | 0.079 s / 33.8 MB |
| Leakage audit | PASS, 0 hits | PASS |

### Mechanism-matched counter-exploiter gate (HARD — added 2026-06-06 post-finals)

The gauntlet must include at least one **adaptive/sharp counter-exploiter** opponent so that over-folding, polarization, and other exploitable-shape risks are measurable. A named hole is not "known", "handled", or "covered" until its mechanism-matched probe is committed and the result is logged with an artifact path and numeric outcome.

Mechanism match is literal: a maniac/value-spewer does **not** discharge an over-folding risk; the probe must attack the low-call/high-fold mechanism. A postflop disaster-spot probe does **not** discharge a preflop risk; the probe must exercise the preflop path. Before any ship-as-is entry, if any named exploitable hole lacks a mechanism-matched probe result, mark the entry AMBER.

### Worked gate entry — Thorp over-fold risk (template)

```text
## GATE: THORP-OVERFOLD-PREMISE/PROBE 2026-06-07
STATUS: PROBE COMMITTED (git tag overfold-probe-2026-06-07). Mechanism CONFIRMED; net-negative NOT reproduced by a fixed HU exploiter -> diagnosis PARTIALLY VALIDATED, flagged for a stronger/adaptive/multiway exploiter before the hole is treated as fully characterized.

PREMISES:
- FORMAT=swiss-cumulative [VERIFIED: portal 2026-06-04 20:00-deadline announcement; mirrored in AGENTS.md Finals FORMAT]
- OBJECTIVE=max-extraction [VERIFIED: finals Phase 1 ranks by cumulative chip performance in AGENTS.md Finals FORMAT]
- NAMED-HOLE=sharp seed bet-folds a 6.4%-caller off pots [VERIFIED: docs/investigations/why-predicted-risk-shipped-2026-06-06.md §7; bleed magnitude MEASURED -12.43 bb/100 isolated, 1023 flop/turn pressure-folds]

PROBE PAIRING:
- Required mechanism: over-fold exploiter that bets/bluffs/bet-folds to profit from Thorp's low call frequency.
- Non-discharging evidence: aggressor/maniac/value-spew wins, fixed templates, reference bots, and postflop disaster-spot probes; these do not exercise the over-fold mechanism.
- Probe artifact location: consult/artifacts/2026-06-07-overfold-probe/REPORT.md [VERIFIED; run vs b108eff5 sha b108eff5..., 25 paired seeds x2 HU, 9998 hands]
- Result: isolated fold-to-pressure bleed -12.43 bb/100 (CI-backed), BUT net Thorp delta +18.85 bb/100 vs this fixed HU exploiter. The mechanism is real and quantified; the fixed HU policy does not make it dominate Thorp's EV.
- Disposition: PARTIAL. The over-fold mechanism is now measurable and confirmed present; the original 'mean EV vs a strong seed may be negative' claim is NOT reproduced by a fixed HU exploiter and remains OPEN -- a fully adaptive and/or 6-max multiway exploiter is the next mechanism-matched escalation. Per Rule 4, the hole stays AMBER (not 'known/handled') until an adaptive/multiway probe either reproduces net-negative or bounds it.
- Decision rule (demonstrated): ship-as-is cannot be GREEN while a named hole's mechanism-matched probe is missing OR inconclusive on the dominant regime (here: 6-max multiway, which this HU probe did not cover).
```

If **any** acceptance criterion fails, including a missing mechanism-matched probe for a named hole, the rollback rule fires (Phase 9).

---

## Phase 8 — Manual review (30 min)

Before promoting, sit with the logs for half an hour.

```bash
# Read the benchmark in full, not just the summary line.
less logs/finals_benchmark.log
less logs/finals_ablate.log
less logs/finals_lbr.log

# Look at the priors report once more, against the live overlay behavior.
cat data/finals_priors_report.txt
```

Specifically, look for:

1. **Suspicious wins.** If `aggressor` jumps from +112.63 to +400+, the overlay is now over-fitting the aggressor pattern in a way that may not generalize to finals opponents. Investigate before promoting.
2. **Quiet regressions.** A template dropping from +71.82 to +69 looks safe on the threshold, but if the CI shifted left meaningfully, that's a real signal. Prefer the qualifier artifact when in doubt.
3. **Ablation gain collapse.** Overlay gain < +5 (vs baseline +32.53) means the new priors are not actually pushing the overlay anywhere useful. Don't ship dead-weight changes.
4. **LBR creep.** Aggregate going from 7.4 to 90 mbb/g (still under cap) is a 12× exploitability increase. Under cap but worth pausing — investigate which spots got worse.

If any of (1)–(4) raises a concrete concern, default to **rollback** (Phase 9). The 1-line standard: *"would I confidently bet £4 000 on this patch over the locked qualifier artifact?"* If no, revert.

---

## Phase 9 — Promote OR rollback (15 min)

### 9a. PROMOTE (only if Phases 7 + 8 are both clean)

```bash
# Verify SHAs once more.
sha256sum submissions/v_finals.zip
sha256sum submissions/v_final.zip   # qualifier still present

# Promote v_finals.zip to ship; preserve qualifier.
cp submissions/v_finals.zip submissions/best_green.zip
# Do NOT overwrite v_final.zip — it's the qualifier record.

# Append to STATUS.md: "## FINALS RESUBMITTED 2026-06-02"
# with the patched SHA, every benchmark number with CI, the priors
# report summary, and the qualifier-vs-finals delta per template.

# Upload submissions/v_finals.zip to the finals portal.
```

### 9b. ROLLBACK (if any gate failed or Phase 8 raised a concern)

```bash
# 1. Discard the patched artifact and any src/data changes.
rm submissions/v_finals.zip
git checkout -- src/
rm -f data/finals_priors.npz
sha256sum submissions/v_final.zip
# Expected: still e4b4a8f1…598.

# 2. Ship the qualifier artifact for finals as well.
#    The platform accepts the same bot.zip for finals; just re-upload v_final.zip.

# 3. Append to STATUS.md: "## FINALS ROLLBACK 2026-06-02"
#    with the reason (validator fail | regression on template X | LBR creep |
#    Phase 8 concern), the gate output that triggered it, and the
#    qualifier SHA confirmation.
```

The rollback is **always available** and **always safe**. There is no penalty for shipping the same artifact twice. There is a real penalty for shipping a patched artifact that regresses.

---

## Risk register

Mitigation column is what you do *now* (before 06-02), not what you discover during the window.

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hand-history JSON schema differs from what the analyzer expects | **HIGH** — schema is unknown until release | Analyzer outputs degenerate priors; overlay tunes on noise | Phase 2.5 fallback (Lane D synthetic priors) is pre-validated against 5 schema variants. Have it tested and copy-paste-ready. |
| Priors file pushes cold-start over the 1.5 s import budget | Medium | Artifact fails Phase 6 step 1; no time to recompress | Keep priors ≤ 200 KB by emitting only summary statistics, not raw histograms. Validate in Lane D that V<n>_priors.npz sizes are all < 100 KB. |
| Engine validator changes between qualifier and finals | Low (no announcement) | Patched artifact rejected; qualifier might also be invalidated | Re-run validator against qualifier `v_final.zip` at Phase 0; if it fails, the org has changed the rules — contact them. |
| New overlay introduces label-leak (opponent names) | Medium — analyzer may emit cluster IDs that look like names | Leakage audit fail; artifact disqualified by AST scan | Phase 4 mandates `audit_strategy_leakage` after each edit, not just at the end. |
| One template benchmark passes mean but loses CI low | Medium — variance at 10k is real | Statistically indistinguishable from qualifier, but visible regression in logs | Phase 7 acceptance is mean-AND-CI-low. Mean above threshold with CI low ≤ 0 fails. |
| Vladimir-class Deep CFR opponent inferred from priors but our overlay can't exploit | Low | Wasted hour in Phase 4; potentially worse against him after | Pre-commit: in Phase 4, only edit `MAX_DEVIATION_PP` and threshold values, never add new opponent-archetype labels. The overlay shape is fixed; only its parameters tune. |
| Patch overruns the 24-h window because a phase took too long | Low if budget held | Finals upload deadline missed; you ship qualifier `v_final.zip` by default | Phase 9b is the explicit no-op rollback. The default outcome of "I ran out of time" is shipping the qualifier — that's a SAFE failure mode. |
| Phase 8 reviewer overconfidence — promote a marginal gain | Medium (human factor) | Finals artifact regresses on unseen opponents | Phase 8 ends with the "£4 000 confidence" gate. Below confident → rollback. |

---

## Total wall-clock budget

| Phase | Budget | Cumulative |
|---|---|---|
| 0 — Pre-window readiness (eve of 06-01) | 10 min | n/a (separate session) |
| 1 — Download | 15 min | 0:15 |
| 2 — Manual schema inspection | 20 min | 0:35 |
| 2.5 — Fallback (only if 2 reveals mismatch) | 10 min | 0:45 max |
| 3 — Analyzer | 45 min | 1:30 |
| 4 — Overlay edits | 60 min | 2:30 |
| 5 — Re-package | 15 min | 2:45 |
| 6 — Smoke + import + edge + leakage | 20 min | 3:05 |
| 7 — Regression benchmark | 90 min | 4:35 |
| 8 — Manual review | 30 min | 5:05 |
| 9 — Promote or rollback | 15 min | 5:20 |
| Buffer | 25 min | 5:45 |
| **Total** | **5:45** | within 24-h window |

Sleep, eat, and read between Phases 3 and 7 if useful — these are the longest individual steps. Do not skip the manual review (Phase 8); the rollback rule depends on it.

---

## Cross-references

- `docs/morning-promotion-checklist.md` — 06-01 ship-day checklist; produces the qualifier artifact this playbook patches.
- `docs/finals-strategy-2026-05-27.md` — strategic frame for finals; decides whether the patch is worth doing at all.
- `docs/playbooks/hardening.md` — gate definitions used by Phases 5–7.
- `consults/2026-05-27-overnight-D/RESULTS.md` — Lane D synthetic prior variants (Phase 2.5 fallback inventory).
- `docs/tournament-spec.md` — sandbox invariants, validator rules, action grammar.
