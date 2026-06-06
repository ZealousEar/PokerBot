# Morning Promotion Checklist — 2026-05-28 ~08:00 BST

You wake up. The 21-lane overnight queue in `~/Code/PokerBot-claude/` has finished or hit its 9-h kill switch. This document is the single decision tree between you and one of three outputs:

- **SHIP** — qualifier upload runs against `submissions/v_final.zip` sha `e4b4a8f1…598` exactly as it sits, 2026-06-01.
- **HOLD** — defer 24 h, gather a second seed-base or a missing lane re-run, decide again 2026-05-29 morning.
- **MODIFY** — promote a specific Lane A candidate, rebuild the artifact, re-run the full G1–G11 gauntlet from scratch, and only then upload.

Do not "use judgment." Every branch below is keyed to numeric evidence. If a lane file is missing or unreadable, that lane defaults to FAIL for the purposes of this checklist.

---

## 0. Pre-flight (60 s)

1. `cd ~/Code/PokerBot && git status` — confirm clean tree on `main`, HEAD unchanged from last night.
2. `sha256sum submissions/v_final.zip submissions/best_green.zip` — both **must** read `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`. If either differs, you have a contamination event; STOP and read `consults/2026-05-26-r1-baseline/W3_postmortem.md` before continuing.
3. Open `~/Code/PokerBot-claude/consults/2026-05-27-overnight-SUMMARY.md` (or `MONITORING.log` + `STATE.json` if SUMMARY did not get written before the kill switch fired). Identify which lanes completed.

If anything in step 0 fails — and especially if the two SHAs disagree — the answer is **HOLD**. Investigate first.

---

## 1. Lane A — overlay-coefficient sweep acceptance

Lane A produces up to 15 candidates under `consults/2026-05-27-overnight-A/candidate_<i>/` plus a `LEADERBOARD.json` and `SUMMARY.md`. Each candidate already had baseline-vs-candidate paired-seed bench, LBR, edge, import, validator gates run against it.

### Pre-committed acceptance gate (ALL of these must hold for a candidate to be promotable)

| Gate | Requirement | Source |
|---|---|---|
| **Aggregate bb/100** | candidate mean − baseline mean ≥ **1.5 × pooled SE** across the 5 reference templates (template, aggressor, mathematician, shark, ref_bot_2) | `candidate_<i>/benchmark.log` |
| **Per-template floor** | candidate beats **≥ 4 of 5** reference templates with CI low > 0 | `candidate_<i>/benchmark.log` |
| **LBR preflop** | ≤ **100 mbb/g** (baseline `v_final` posts 18.0) | `candidate_<i>/lbr.log` |
| **LBR aggregate** | ≤ **200 mbb/g** (baseline `v_final` posts 7.4) | `candidate_<i>/lbr.log` |
| **Edge cases** | 25/25 PASS, no warnings | `candidate_<i>/edge.log` |
| **Import audit** | cold < 1.5 s, RSS < 400 MB, zero forbidden imports | `candidate_<i>/import_audit.log` |
| **Validator** | engine validator PASSED on all 4 TEST_STATES | `candidate_<i>/validator.log` |
| **Leakage audit** | `audit_strategy_leakage` PASS, zero hits on 14 tokens | log under same dir |

### Tie-breakers (only if 2+ candidates clear the gate)

Apply in strict order; the first criterion that separates wins.

1. **LBR aggregate** — lower wins. Tighter bound on counter-exploit cost.
2. **Aggregate bb/100 mean** — higher wins.
3. **Aggressor CI low** — higher wins. (Aggressor is the highest-variance opponent; a tighter CI low is a robustness signal.)
4. **MAX_DEVIATION_PP value** — *lower* wins. Closer to Nash baseline is safer for finals carry-over.

### Disqualifiers (immediate rejection regardless of mean)

- Any test or validator fails.
- LBR preflop > 100 mbb/g **or** LBR aggregate > 200 mbb/g.
- Leakage audit returns ≥ 1 hit.
- `benchmark.log` shows any opponent with CI low < `−20 bb/100` (catastrophic matchup hidden inside the mean).
- Per-template floor unmet (loses to ≥ 2 of the 5 references with CI excluding 0).

### Note on finals carry-over

A Lane A candidate clearing this gate ships the qualifier (06-01). It does **not** automatically carry to the finals (06-05). Per `docs/finals-strategy-2026-05-27.md` §2 + §4.1, the finals-promote bar is stricter: LBR aggregate ≤ **100** mbb/g (not 200), and the candidate must beat the baseline on aggregate AND lower LBR (strict Pareto). Record the Lane A candidate's LBR numbers here so the 06-02 patch-window decision has them in hand.

### Output of Section 1

Exactly one of:
- **`LANE_A_PASS=<i>`** — candidate `i` cleared every gate and won the tie-break.
- **`LANE_A_NONE`** — no candidate cleared the gate; promotion is not on the table from Lane A.

---

## 2. Lane B — H2H vs public competitor bots

Lane B runs paired-seed-base 42, count 10, 10 000 hands per opponent, 6-max table, against each of {vladimir, dominic, famadeo, neel} under `consults/2026-05-27-overnight-B/<opponent>/`.

### Reading the per-opponent numbers

Read `<opponent>/h2h.json` and the `SUMMARY.md`. For each opponent record:

```
mean_bb_per_100  ci_low  ci_high  errors  notes
```

### Per-opponent acceptance bands

| Band | Definition | Implication |
|---|---|---|
| **GREEN** | mean > 0 AND CI low > 0 | Real edge. No action needed. |
| **AMBER** | mean > 0 BUT CI low ∈ (−20, 0] | Indeterminate edge. Acceptable for ship; flag for finals re-evaluation on 06-02. |
| **AMBER-LOSS** | mean ≤ 0 AND CI low > −20 | Soft loss within variance. Acceptable for qualifier ship if 3 of 4 opponents are GREEN; flag for finals tuning. |
| **RED** | CI high < 0 AND CI low ≤ −50 | Demonstrated heavy loss. **MODIFY trigger** if matched against finals field. |

### Special case — Vladimir's Deep CFR

If `vladimir/h2h.json` shows mean ≤ **−50 bb/100** with CI excluding 0:

1. This is the strongest plausible opponent in the public field per `consults/2026-05-27-overnight-P/vladimir_analysis.md`.
2. Vladimir is **one bot in a 6-max table** — at most one seat out of five villains per 400-hand match. Even a 50 bb/100 loss against him costs roughly `−50 × (400/600) × (1/5) ≈ −6.7` chips per match in expectation, before the wins against weaker seats.
3. Action: **proceed with SHIP** for the qualifier. Tag the result for **finals MODIFY consideration** on 2026-06-02 once we see actual qualifier hand histories.
4. Do **not** branch to MODIFY for the qualifier based on a single Vladimir result. The qualifier rewards median-field edge, not head-to-head against the strongest entrant.

If `vladimir/h2h.json` did not finish (timeout, load failure — Vladimir is flagged-risk in KANBAN), record `vladimir=UNKNOWN`. Treat as AMBER, not RED. Do not extrapolate.

### Output of Section 2

A 4-line ledger written to scratch:
```
vladimir = <GREEN|AMBER|AMBER-LOSS|RED|UNKNOWN>  mean=<x>  ci_low=<y>
dominic  = ...
famadeo  = ...
neel     = ...
```

---

## 3. Lane V — 6-max mixed-table per-composition

Lane V is `tools/benchmark.py --six-max-mix` style output across the 4 standard compositions (C1–C4), per `PokerBot-codex/consults/2026-05-26-r1-baseline/lane_a2_candidate/SUMMARY.md` for the schema. The artifact-bound JSON lives under the relevant lane dir; check `consults/2026-05-27-overnight-A/candidate_<i>/` for the winning Lane A candidate's six-max output, and also `consults/2026-05-27-overnight-T/synthetic_finals_field/` if Lane T ran.

### Per-composition acceptance

For each of C1, C2, C3, C4 record:

```
comp  mean_bb_per_100  ci_low  ci_high
```

A composition is **GREEN** if `mean > 0` AND `ci_low > 0`.
A composition is **NEUTRAL** if `ci_low ≤ 0 ≤ ci_high` (indeterminate).
A composition is **RED** if `ci_high < 0`.

**Decision rule:**
- **3 or 4 of 4 GREEN** → ship signal.
- **2 GREEN + 2 NEUTRAL** → ship signal; flag the neutral comps.
- **Any single RED** with CI excluding 0 AND magnitude > 15 bb/100 → **MODIFY trigger**. Read the position-stratified per-seat lines (the SUMMARY.md tables list per-seat bb/100 by opponent). If a **specific seat or position** is the source (e.g., "famadeo-C2-seat-3 −30.10"), record that and consult Lane A leaderboard for a candidate that fixes the position.

### Position-stratified diagnosis

If a comp is RED, slice per-seat:
- **UTG/MP losing** → preflop range issue. Most likely candidate fix is a Lane L (preflop range tuning) result, if Lane L ran.
- **BTN/SB/BB losing** → 3-bet / 4-bet response issue. Most likely Lane M (3bet/4bet sweep) result.
- **Multiple seats with the same opponent losing** → opponent-specific overlay regression, e.g., the Famadeo-C2 −21.31 / Famadeo-C4 +20.03 split documented in PokerBot-codex/STATUS.md from the W3 holdout. A Lane A candidate is the right lever, not Lane L/M.

### Output of Section 3

```
C1 = <GREEN|NEUTRAL|RED>  mean=<x>  ci_low=<y>
C2 = ...
C3 = ...
C4 = ...
diagnosis = <"clean" | "position:<UTG|BTN|...>" | "opponent:<name>-comp<n>">
```

---

## 4. Lane G — RSS + decision latency hard caps

Lane G is the cold-start + 400-hand sandbox stress under `consults/2026-05-27-overnight-G/`. Read `rss_timeseries.csv`, `decide_latency_histogram.json`, and `SUMMARY.md`.

### Hard caps (any breach → forced HOLD, not MODIFY)

| Metric | Cap | Baseline (v_final) |
|---|---|---|
| RSS peak | **≤ 700 MB** | 33.8 MB |
| `decide()` p99 wall clock | **≤ 1.8 s** | well under (no logged failures) |
| `decide()` max wall clock | **< 2.0 s** | well under |
| 400-hand stability | 0 timeouts, 0 OOM | 0/0 |

If any cap is breached **for the current `v_final.zip`** (i.e., the *baseline*, not a candidate), the artifact itself is suspect and we do not ship anything until the issue is diagnosed. This is a **HOLD trigger, not a MODIFY** — promoting a Lane A candidate doesn't fix an artifact-bound RSS/latency issue caused by data loading or import cost.

If any cap is breached **for a Lane A candidate but not for the baseline**, that candidate is disqualified (back to Section 1 tie-breaker). Baseline still ships.

### Output of Section 4

One of:
- **`LANE_G_PASS`** — baseline well under all caps, candidate (if any) also under.
- **`LANE_G_HOLD`** — baseline breached a cap, ship is paused.
- **`LANE_G_CAND_FAIL`** — only the Lane A candidate breached; disqualify candidate.

---

## 5. Lane Y — backup artifacts recovery sequence

"Lane Y" is the contingency check: if our primary artifact is somehow unshippable on 06-01 morning, which alternate ships?

### Artifact inventory (current state, by sha256)

| File | sha256 | Ship-eligible? | Notes |
|---|---|---|---|
| `submissions/v_final.zip` | `e4b4a8f1…598` | **YES — primary** | Locked, byte-identical to `best_green.zip` |
| `submissions/best_green.zip` | `e4b4a8f1…598` | YES (= v_final) | Identical; do not re-package |
| `submissions/v_w3_candidate.zip` | `d78a4c6b…` | NO | Declined 2026-05-26; loses s142 holdout aggregate by −2.67 bb/100 |
| `submissions/v_final_pre_x1.zip` | `5d65561e…cef` | **NO — disqualified** | Fails `audit_strategy_leakage` (20+ opponent strings in src). Permanently ineligible. |

### Recovery sequence (only if primary `v_final.zip` is unshippable)

If `sha256sum submissions/v_final.zip` does not return `e4b4a8f1…598`:

1. Confirm `submissions/best_green.zip` SHA. If it matches `e4b4a8f1…598`, copy it back: `cp submissions/best_green.zip submissions/v_final.zip` and re-verify SHA. **Do NOT use `tools/package.py`** — repackaging produces a different SHA because zip timestamps shift (see G4 reaudit note in STATUS.md). Per-file content SHAs would be identical, but the artifact SHA you ship must be the one previously gauntletted.
2. If neither `v_final.zip` nor `best_green.zip` carry the canonical SHA, restore from git: the release branch `release/v_final-e4b4a8f1` at commit `a00561c` contains the source tree that built the artifact, but **not the zip itself** (zip is gitignored). You would have to rebuild — and a rebuild does not reproduce the SHA bit-for-bit. This is a **HOLD**, not a SHIP, because the rebuilt artifact has not been gauntletted at that SHA.
3. The Lane Q worktree-state report (`consults/2026-05-27-overnight-Q/worktree_state.md`) should confirm no uncommitted main-branch edits have touched `submissions/`. If it shows otherwise, treat as a contamination event and HOLD.

`v_w3_candidate.zip` is **not** an emergency ship candidate. It was explicitly declined; promoting it to qualifier ship reverses a recorded user decision (2026-05-27T00:30Z, Option A).

### Output of Section 5

One of:
- **`LANE_Y_PRIMARY_OK`** — sha matches, primary ships.
- **`LANE_Y_RESTORE_OK`** — restored from `best_green.zip`, sha now matches, primary ships.
- **`LANE_Y_HOLD`** — primary unshippable, no SHA-matching backup, defer.

---

## 6. Final decision matrix

Read your five outputs (Sections 1–5) and apply the table below. There are no other branches. If a row does not match exactly, drop to the next.

| Lane A | Lane B (worst opp.) | Lane V | Lane G | Lane Y | **Decision** |
|---|---|---|---|---|---|
| any | any | any | `HOLD` | any | **HOLD** — baseline RSS/latency regression |
| any | any | any | any | `HOLD` | **HOLD** — artifact integrity broken |
| `LANE_A_NONE` | not RED | not RED | `PASS` | OK | **SHIP** — baseline as-is |
| `LANE_A_NONE` | RED (single, non-vladimir) | not RED | `PASS` | OK | **SHIP** — qualifier; tag for finals review |
| `LANE_A_NONE` | RED (≥ 2 opponents) | any | `PASS` | OK | **HOLD** — gather second-seed Lane B; re-decide 05-29 |
| `LANE_A_NONE` | any | RED (1 comp, magnitude < 15) | `PASS` | OK | **SHIP** — qualifier; tag composition for finals review |
| `LANE_A_PASS=<i>` | not RED | not RED | `PASS` | OK | **MODIFY** — promote candidate `i`; full gauntlet before SHIP (see Section 7) |
| `LANE_A_PASS=<i>` | RED | any | `PASS` | OK | **HOLD** — Lane A candidate beats baseline on templates but Lane B reveals real loss; need to verify candidate doesn't make it worse against the same opponent. Re-run Lane B against candidate before MODIFY. |
| any | any | RED (any comp, magnitude ≥ 15) | `PASS` | OK | **MODIFY if Lane A_PASS exists and fixes the comp**, else **HOLD** |

### One-line decision

Write exactly one of:

```
DECISION: SHIP v_final.zip e4b4a8f1...598 — qualifier 2026-06-01
DECISION: HOLD — reason=<one of: RSS_breach | latency_breach | sha_mismatch | lane_B_red_multi | lane_V_red_no_candidate | contamination>
DECISION: MODIFY — candidate=<i> sha=<computed> — full gauntlet before ship
```

---

## 7. MODIFY branch — full G1–G11 gauntlet before SHIP

Only execute this section if the decision matrix in Section 6 outputs `MODIFY`. Wall-clock budget: ~45 minutes. Do not skip steps.

Working directory: `~/Code/PokerBot/` (canonical). Do **not** ship a candidate that lives only under `PokerBot-claude/` — it must be merged into main first.

1. `cd ~/Code/PokerBot && git status` — clean tree.
2. Copy the winning candidate's `opponent_model.py` (and any other src diffs) from `PokerBot-claude/consults/2026-05-27-overnight-A/candidate_<i>/` into `~/Code/PokerBot/src/`. Diff against current HEAD.
3. `python tools/audit_strategy_leakage.py --src src/` — must PASS.
4. `python tools/import_audit.py --max-seconds 1.5 --max-mb 400` — must PASS.
5. `pytest tests/edge_cases -x` — must be 25/25.
6. `python tools/package.py --output submissions/v_final_modify.zip --strict` — produces a fresh zip; compute and record SHA. **This SHA replaces `e4b4a8f1…598` for the rest of this run.**
7. `python ext/fullhouse-engine/sandbox/validator.py submissions/v_final_modify.zip` — must PASSED.
8. `python tools/smoke_run.py --zip submissions/v_final_modify.zip --hands 200` — must be 200/200, 0 hero errors.
9. `python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42 --paired-seed-count 10 --zip submissions/v_final_modify.zip` — every template CI > 0; aggregate ≥ baseline (`+71.82 / +112.63 / +144.60 / +70.16 / +144.60`) − 1.5 × pooled SE.
10. `python tools/benchmark.py --ablate-overlay --hands 10000 --zip submissions/v_final_modify.zip` — gain ≥ +3 bb/100.
11. `python tools/exploit_check.py --zip submissions/v_final_modify.zip --max-preflop-mbb 100 --max-aggregate-mbb 200` — must PASS.
12. Append a new STATUS.md section with the proof-of-green block.
13. If any step fails, **abort MODIFY**, ship the baseline `v_final.zip` instead, record the failure under `consults/2026-05-28-modify-aborted/`.
14. Only on full GREEN: `cp submissions/v_final_modify.zip submissions/v_final.zip && cp submissions/v_final_modify.zip submissions/best_green.zip`. Compute SHAs; confirm both match.

The MODIFY artifact only ships after step 14 succeeds.

---

## 8. SHIP-day command sequence — 2026-06-01

Copy-paste from here. Numbers in `[]` are the locked baseline values; if MODIFY ran, substitute the MODIFY SHA and your candidate's bench numbers.

```bash
# 1. Verify the artifact is the one we intend to ship.
cd ~/Code/PokerBot
sha256sum submissions/v_final.zip
# Expected: e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598

# 2. Final sandbox dry-run (real Docker, 200 hands vs shark).
python tools/smoke_run.py --zip submissions/v_final.zip --hands 200
# Expected: 200/200, 0 hero_errors, chip delta > 0

# 3. Final validator pass (engine-authoritative).
python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip
# Expected: ✅ PASSED, 4/4 TEST_STATES

# 4. Final import audit (cold-start budget within sandbox limits).
python tools/import_audit.py --max-seconds 1.5 --max-mb 400
# Expected: cold < 1.5s, RSS < 400 MB, zero forbidden imports

# 5. Final leakage audit.
python tools/audit_strategy_leakage.py --zip submissions/v_final.zip
# Expected: PASS, 0 hits on 14 tokens

# 6. Confirm size envelope.
du -h submissions/v_final.zip
unzip -l submissions/v_final.zip | tail -5
# Expected: total ≤ 250 MB; bot.py at root ≤ 5 MB; no other .py at root; no .py in data/

# 7. Record the SHIP entry in STATUS.md.
# Append a new section: "## QUALIFIER SUBMITTED 2026-06-01"
# with the SHA, bench summary, and upload timestamp.

# 8. Upload to the Fullhouse Hackathon qualifier portal.
# Manual step — drag submissions/v_final.zip to the upload form.
# Record the portal-side confirmation hash if displayed; cross-check it
# against the local SHA (e4b4a8f1…598).

# 9. Tag the release commit for permanent record.
git tag -a v_final-e4b4a8f1 release/v_final-e4b4a8f1
git tag -l v_final-e4b4a8f1
# Push to origin only after qualifier is over (avoid public counter-prep).
```

If any step from 2–6 fails on ship day, **do not upload**. The artifact is unshippable; revert to the HOLD recovery sequence in Section 5. The 24-hour patch window opens 2026-06-02 — a missed qualifier upload cannot be patched.

---

## Cross-references

- `docs/playbooks/patch-window.md` — 06-02 finals patch workflow (orthogonal to this checklist).
- `docs/finals-strategy-2026-05-27.md` — finals strategic plan; informs whether the qualifier artifact carries to 06-05.
- `docs/playbooks/hardening.md` — full gate definitions used by Section 7.
- `consults/2026-05-26-r1-baseline/W3_postmortem.md` — the methodology fix (holdout-seed-vs-current-champion is mandatory). Lane A acceptance gate in Section 1 already encodes this.
- `docs/tournament-spec.md` — sandbox invariants and validator rules.
