# Qualifier brainstorm — proof-before-patch version (genius-agent response)

**Captured:** 2026-05-27T23:06:59Z
**Source:** External "genius" agent (Opus-4.7-class) consulted by user against the rollout plan + STATUS context
**Verbatim:** yes — full text below, no edits
**Pairing:** A parallel Repo Prompt agent response is expected; log will be filed alongside this one for comparison
**Plan reference:** docs/plans/qualifier-finals-rollout-2026-05-27.md
**Status reference:** STATUS.md 2026-05-27T21:10Z entry

---

## Verbatim response

# Qualifier brainstorm — proof-before-patch version

I would not phrase the qualifier state as "done." The correct posture is:

```text
We have a strong artifact against reference bots.
We do not yet have reliable evidence that it beats every relevant public repo.
Therefore: verify public-field robustness first, patch only on concentrated evidence, and preserve rollback.
```

The official format makes this distinction important. The public engine README says the qualifier is Swiss-style, 400 hands per match, six-bot tables, ranked by cumulative chip delta, with the top 64 advancing; the official site says top 64 advance by chip EV. Treat those as equivalent enough for engineering, but precise enough to optimise for **short-horizon chip accumulation**, not pure H2H dominance. ([GitHub][1]) The same README also says the upload deadline is **31 May 2026, 23:59 UTC**, with the latest successful upload counting for the 1 June qualifier, so the working assumption should be: **deadline is 31 May 23:59 UTC; qualifier runs 1 June**. ([GitHub][1])

Current internal evidence supports caution. The release artifact has excellent reference-bot gauntlet numbers, validator pass, smoke pass, and LBR pass, but public-bot H2H is not clean: vladimir is indeterminate on a tiny sample, neel is positive, dominic is AMBER, and famadeo is the clearest deficit.  Patch-1 is the warning case: it helped dominic, hurt neel, was neutral/indeterminate elsewhere, and was shelved as net negative.  So the qualifier plan should not be "ship blindly"; it should be "earn the right to ship or earn the right to patch."

Repo Prompt should be used as a **context-controlled orchestration layer**, not as a broad agent dump. Its docs position it around codemaps, slicing, token budgets, and managed context selection, which is exactly what we need for surgical validation and patch review. ([Repo Prompt][2])

---

# Section A — Public-repo reliability proof

## 10+ ideas

1. **Fresh public-repo rescan:** update manifest SHAs for neel, dominic, famadeo, vladimir, and any newly found public forks before assuming local clones are current.
2. **Artifact-bound H2H only:** every public-bot result must run from `submissions/v_final.zip`, not loose `src/`.
3. **Same-seed paired baseline:** compare any candidate against baseline on identical seed/orientation rows; never compare to old Lane B point estimates.
4. **400-hand match distribution:** report not just bb/100, but per-400-hand chip delta distribution, bust rate, p10/p50/p90, and full-stack-loss frequency.
5. **6-max public pods:** build mixed six-bot tables using `{hero, neel, dominic, famadeo, vladimir, reference/synthetic}` because qualifier is six-max, not HU.
6. **Public-repo "red" threshold:** define RED as paired Δ CI excluding zero against us or per-400-hand downside tail likely to kill top-64 chances.
7. **Opponent-specific sample adequacy:** vladimir/famadeo early-bust H2H produces tiny hand counts; per-match BB delta is cleaner than bb/100.
8. **Local leaderboard with CI width:** make uncertainty visually unavoidable; a 1,085-hand vladimir result should not look comparable to 50k reference-bot runs.
9. **Runtime-error parity check:** any public-bot "win" is discarded if their bot errors or load fails; we need strategic evidence, not harness artefacts.
10. **Seat/position clustering:** for every loss, cluster by street, hero position, action, board texture, SPR, and bet bucket before patching.
11. **No "beat every repo" overfitting:** public repos are a threat sample, not the whole 500+ field; do not overfit to four public bots at the cost of reference/template edge.
12. **Saroop/unverified threat lane:** keep unresolved public claims as archetype tests, not as literal opponent branches.
13. **Qualifying-pod simulator:** Monte Carlo across public/references/synthetic archetypes to estimate top-64 probability bands from chip-delta distributions.
14. **No candidate without rollback SHA:** any patched artifact must have a named SHA, full gauntlet log, and explicit fallback to canonical baseline.

## Top 3

### A1. Artifact-bound public gauntlet, same seeds, two seed bases

**Pitch:** Stop treating public-bot strength as anecdotal; run a reproducible, paired-seed, artifact-bound gauntlet against all verified public repos before deciding ship/patch.

**Implementation sketch:** Create `consult/artifacts/2026-05-30-qualifier-public-gauntlet/`. For each public bot, run baseline from `submissions/v_final.zip` at two independent bases:

```bash
python tools/h2h.py \
  --bot-a submissions/v_final.zip \
  --bot-b ext/public-bots/<opp>/bots/<bot>/bot.zip \
  --hands 20000 \
  --paired-seed-base 142 \
  --match-len 200 \
  --label-a v_final \
  --label-b <opp> \
  | tee consult/artifacts/2026-05-30-qualifier-public-gauntlet/<opp>_s142.log

python tools/h2h.py \
  --bot-a submissions/v_final.zip \
  --bot-b ext/public-bots/<opp>/bots/<bot>/bot.zip \
  --hands 20000 \
  --paired-seed-base 242 \
  --match-len 200 \
  --label-a v_final \
  --label-b <opp> \
  | tee consult/artifacts/2026-05-30-qualifier-public-gauntlet/<opp>_s242.log
```

Then aggregate by paired per-match BB delta, actual hands, bust rate, and CI. H2H is not the tournament format, but it is the cleanest public-repo red-team isolation.

**Acceptance test idea:** A parser emits `SUMMARY.md` with rows:

```text
opp | seed_base | matches | hands | mean_match_BB | CI | bb/100 | hero_bust | opp_bust | verdict
```

Promotion blocker if ≥2 public bots are RED, or if one bot is RED and the loss clusters into a patchable high-frequency cell.

**Single biggest risk:** H2H can overstate threat because the qualifier is six-max. Mitigation: A2 six-max pods must be run before any code change.

---

### A2. Six-max public-pod gauntlet

**Pitch:** The qualifier is six-bot Swiss, so we need a pod-level chip-delta distribution, not only HU results.

**Implementation sketch:** Build or reuse a harness that runs 400-hand six-bot tables with hero plus combinations such as:

```text
P1: hero + template + aggressor + mathematician + shark + ref_bot_2
P2: hero + neel + dominic + famadeo + vladimir + shark
P3: hero + neel + dominic + famadeo + aggressor + mathematician
P4: hero + vladimir + famadeo + two references + one synthetic pressure bot
P5: hero + public-bot duplicate archetypes where legal locally, or synthetic lookalikes
```

Output should be **chip delta per 400-hand match**, not only bb/100. Use at least 50–100 seeds if wall-clock allows. The official engine README explicitly frames 400 hands as the qualifier match length and says 400 hands was chosen to reduce variance. ([GitHub][1])

**Acceptance test idea:** `tools/qualifier_pods.py --bot submissions/v_final.zip --seeds 100 --out ...` emits `pod_summary.json` with p10/p50/p90 chip deltas and `P(delta < -10000)`. Require no public-heavy pod with median < 0 and require p10 not catastrophically worse than baseline reference pods.

**Single biggest risk:** Local six-max harness may diverge from official Swiss pairings. Mitigation: use it for relative risk and tail detection, not as a precise top-64 probability.

---

### A3. Public-repo freshness and manifest audit

**Pitch:** Public repos can change before deadline, so lock the exact public bot versions used for testing.

**Implementation sketch:** Extend `submissions/manifest.json` or create `consult/artifacts/2026-05-30-public-repo-scan/MANIFEST.md` with:

```text
opponent | repo | branch | commit | bot_path | data_paths | validator_status | local_zip_sha | notes
```

The existing manifest already tracks known public clones and notes that saroop is unresolved, while vladimir, famadeo, dominic, and neel have specific bot paths/data paths.  Do one fresh web/GitHub check before the final decision.

**Acceptance test idea:** For every tested public bot, compute source file SHA and zip SHA. Refuse to cite a public-bot result unless it names the exact tested SHA.

**Single biggest risk:** Spending too much time scouting instead of benchmarking. Hard cap the scan; only current bot path, data path, branch, and SHA matter.

---

# Section B — Qualifier-safe patch ideas, only after RED evidence

## 10+ ideas

1. **PATCH-Q1: postflop stackoff veto lite** — fold weak one-pair/air versus large wet/multiway/low-SPR bets.
2. **Small-bet defend rule** — avoid overfolding to 0.25–0.33p public-bot probing bets.
3. **River overbet weak-pair fold** — dominic/famadeo-style pressure often punishes weak bluff-catches.
4. **Turn future-risk tax** — discount raw equity on wet turn boards where river realization is poor.
5. **Preflop light-3bet guard v2** — revisit only if the v5/public 3bet deficit reappears under same-seed public gauntlet.
6. **Deep-stack BB 3bet pot caution** — reduce flatting speculative hands when deep and out of position.
7. **No broad preflop rewrite** — PATCH-1 showed targeted preflop changes can regress neel; broad ranges are too risky.
8. **Legalizer hardening audit** — ensure canonical artifact actually clamps malformed raise/negative amount/all-in edge cases.
9. **Timeout fallback probe** — stress eval7 equity path under worst-case turn/river; if over-budget, force heuristic fallback earlier.
10. **Raise-size cap review** — avoid pot-building with medium-strength hands when `can_check=True` on volatile boards.
11. **Public-pressure table mode** — shrink overlay when table aggression is high; do not add opponent names.
12. **All-in commit threshold** — if call commits ≥65% stack, treat as all-in decision, not normal call.
13. **Donor-bot exploitation preservation** — any patch must still farm template/aggressor/mathematician/shark/ref_bot_2.
14. **Patch parking rule** — candidate lives under `submissions/v_qual_candidate.zip`; canonical baseline untouched until full promotion.

## Top 3

### B1. PATCH-Q1 postflop stackoff veto lite

**Pitch:** Add a bounded veto that prevents expensive weak one-pair/air calls against large wet/multiway/low-SPR pressure while leaving cheap calls and made hands alone.

**Implementation sketch:** Same seam as the finals PATCH-2A idea, but narrower for qualifier. Only touch `PokerBot-codex/src/postflop.py`; do not touch preflop, sizing, opponent model, or blueprint data. The existing plan identifies `_equity_turn_river_action()`, `_heuristic_postflop_action()`, and `decide_postflop()` as the intended postflop seams.

Veto scope:

```text
street in {turn, river}
AND facing bet
AND bet_ratio >= 0.67 OR owed/stack_total >= 0.18
AND (board_wet OR multiway_count >= 3 OR SPR <= 2.0 OR recent_raise_depth >= 1)
AND made_hand_class <= weak_top_pair
AND draw_proxy < strong_draw
```

Action:

```text
if effective_equity < pot_odds + safety_margin:
    fold
else:
    existing action
```

Keep ≤0.33p bets mostly immune.

**Acceptance test idea:** Add `tests/edge_cases/test_postflop_veto.py` with three tests:

```text
wet_multiway_turn_overbet_weak_top_pair -> fold
dry_heads_up_small_bet_pair -> call
wet_turn_combo_draw -> call
```

Then require:

```bash
pytest tests/edge_cases -x
python tools/exploit_check.py --zip submissions/v_qual_candidate.zip
python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42 --zip submissions/v_qual_candidate.zip
```

**Single biggest risk:** Overfold regression against neel-style pressure. This patch cannot promote unless same-seed public gauntlet shows **no neel HURTS**.

---

### B2. PATCH-Q2 small-bet anti-overfold bucket

**Pitch:** Public bots may exploit generic risk gates with tiny bets; defend enough versus ≤0.33p so we do not donate folds.

**Implementation sketch:** In postflop turn/river logic, classify:

```text
bet_ratio = amount_owed / max(1, pot)
small_bet = bet_ratio <= 0.33
```

For small bets:

```text
call any pair, overpair, top pair, flush draw, OESD, two overcards on turn
fold only pure air with no draw and bad equity
```

This is not an aggressive patch; it is an anti-overfold guard. It pairs naturally with B1 because B1 makes us tighter against large bets.

**Acceptance test idea:** Same mocked-equity state, weak pair facing 0.27p calls; weak pair facing 1.5p on wet multiway folds. This catches inverted threshold bugs.

**Single biggest risk:** Calling too wide versus value-heavy small bets. Keep it cheap-only and rely on pot odds.

---

### B3. HARDEN-Q canonical artifact edge-case audit

**Pitch:** Before any strategic patch, prove the artifact is operationally robust against side-pot, malformed, short-stack, and latency cases.

**Implementation sketch:** Run the hardening suite against **the actual zip**, not loose source:

```bash
python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip
python tools/import_audit.py --max-seconds 1.5 --max-mb 400
pytest tests/edge_cases -x
python tools/smoke_run.py --zip submissions/v_final.zip --hands 2000
python tools/audit_strategy_leakage.py --zip submissions/v_final.zip
```

The project's tournament spec lists validator rejection rules, forbidden imports/calls, action grammar, package limits, 2s timeout, 30s warmup, 768MB RAM, and data-read constraints.  The official README confirms the same operational envelope: 2s per action, no network, no file writes, 768MB RAM, 0.5 CPU, and data loaded at import time. ([GitHub][1])

**Acceptance test idea:** `L2_SUMMARY.md` rows:

```text
opponent | hands | hero_errors | p99_ms | max_ms | result
```

Require 0 errors and p99 < 1.5s.

**Single biggest risk:** Discovering the loose source passes but the canonical zip does not. That is exactly why this audit must run before patch work.

---

# Section C — Qualifier Swiss / chip-EV deployment logic

## 10+ ideas

1. **Target top-64, not undefeated H2H:** public-repo losses matter if they create table-level chip-delta risk, not because we need literal H2H dominance.
2. **400-hand downside tail:** use p10/p5 chip-delta as promotion criterion; not only mean.
3. **Bust-rate cap:** reject any candidate that increases hero full-stack bust rate materially.
4. **Donor preservation:** keep huge positive edge versus weak references; those chips matter in Swiss cumulative delta.
5. **Public-heavy pods:** assume later Swiss rounds contain stronger bots; stress-test public-heavy tables.
6. **First-round mixed field:** early pods likely include weak bots; avoid tightening so much we miss donor EV.
7. **Aggressor variance lens:** aggressor mean is high but CI is wide; assess short 400-hand variance specifically.
8. **Match-end censoring awareness:** early busts distort bb/100; use per-match chip delta.
9. **No finals survival logic pre-qualifier:** qualifier ranking is chip delta/chip EV, not bracket win probability.
10. **No experimental Deep CFR switch:** too much integration risk for a pre-qualifier artifact.
11. **Overlay shrink only if public-heavy pods show tail risk:** do not reduce exploit overlay just because finals will be sharper.
12. **Reference-pod floor:** every candidate must beat the five reference bots with CI low > 0.
13. **Synthetic archetype smoke:** include v5_light_3bet, nit_exploiter, and public-pressure lookalikes, but do not overfit them.
14. **No promotion on one metric:** require reference gauntlet, public gauntlet, LBR, validator, leakage, smoke, and edge tests together.

## Top 3

### C1. Qualifier chip-delta distribution model

**Pitch:** Convert all H2H and six-max results into a distribution of likely 400-hand chip deltas so we can decide whether the bot is top-64-safe.

**Implementation sketch:** Build `tools/qualifier_projection.py` consuming:

```text
reference_pods.json
public_h2h_summary.json
public_pods_summary.json
synthetic_archetype_summary.json
```

Model outputs:

```text
P(delta_total > cutoff_proxy)
P(any_round < -10000)
P(top64 under weak/medium/strong field)
sensitivity: public-heavy | reference-heavy | sharp-tail
```

Do not report fake precision. Use bands:

```text
GREEN: top64 band comfortably > 70%
AMBER: 45–70%
RED: <45% or catastrophic tail
```

**Acceptance test idea:** The tool must reproduce Lane E-style assumptions explicitly rather than burying them. Lane E's older projection was called out as assumption-sensitive, so this tool should show field-size/round-count sensitivity directly.

**Single biggest risk:** A projection can create false confidence. Require every output line to include assumptions and sensitivity.

---

### C2. Candidate promotion by tail-risk, not mean-only

**Pitch:** A patch that improves mean but increases bust variance is bad for qualification.

**Implementation sketch:** Candidate table:

```text
metric                         baseline       candidate      gate
reference aggregate bb/100      ...            ...            candidate >= baseline - tolerance
public-heavy pod median         ...            ...            candidate >= baseline
public-heavy pod p10            ...            ...            candidate >= baseline - 1000 chips
hero bust rate                  ...            ...            candidate <= baseline + 3pp
LBR aggregate                   ...            ...            delta <= +20 mbb/g
validator/leakage/import        PASS           PASS           required
```

PATCH-1 already demonstrated why this matters: it shifted variance, missed the v5 lift floor, increased LBR exploitability, and regressed neel.

**Acceptance test idea:** A candidate with +10 bb/100 mean but +15pp bust-rate increase is marked HOLD/NO-PROMOTE.

**Single biggest risk:** Tail metrics need enough seeds. Use paired 400-hand pods and bootstrap CIs.

---

### C3. Donor-EV preservation gate

**Pitch:** We cannot over-harden against public bots if it sacrifices the weak-field chip extraction needed for Swiss ranking.

**Implementation sketch:** Hard gate:

```bash
python tools/benchmark.py --all-templates --hands 10000 \
  --paired-seed-base 42 \
  --zip submissions/v_qual_candidate.zip
```

Acceptance:

```text
No reference template CI low <= 0.
No per-template statistically significant negative delta vs baseline.
Aggregate reference EV not lower by more than 1.5 pooled SE.
Overlay ablation gain remains >= +3 bb/100.
```

The release notes show the locked artifact's reference-bot baseline is very strong: template, aggressor, mathematician, shark, and ref_bot_2 are all comfortably positive, with ablation gain +32.53 and LBR pass.  That is an asset, not something to casually trade away.

**Single biggest risk:** We overweight reference bots because they are easy to beat. Mitigation: this is a **preservation** gate, not the only gate.

---

# Section D — Wildcards

### D1. Public-bot "antibody" synthetic pack

**Pitch:** Build tiny behavioural lookalikes of the public threats so we can run faster, broader tests than full public repos.

**Implementation sketch:** Under `tools/archetypes/qualifier_public/`, create:

```text
neel_like_pot_odds_mc
dominic_like_blueprint_threshold
famadeo_like_pressure_veto
vladimir_like_offgrid_pressure_bucket
v5_light_3bet
```

Use these only for diagnostic breadth; do not let them replace real public-repo H2H.

**Acceptance test idea:** Candidate must not regress against any synthetic antibody by CI-excluding negative paired delta.

**Single biggest risk:** Self-fulfilling overfit. Keep the pack simple and behavioural.

---

### D2. Decision-cluster "patch permission" file

**Pitch:** Require a machine-readable `PATCH_PERMISSION.json` before any code patch.

**Implementation sketch:**

```json
{
  "opponent": "famadeo",
  "evidence": "public_gauntlet_s142_s242",
  "cluster": "turn__BTN__call__wet_multiway_large",
  "share_of_loss": 0.57,
  "patch_scope": "src/postflop.py only",
  "required_tests": [
    "test_wet_multiway_large_bet_folds_weak_pair",
    "test_small_bet_pair_still_calls",
    "test_neel_no_hurts"
  ]
}
```

No permission file, no patch.

**Acceptance test idea:** Repo Prompt patch agents must read the permission file and produce tests named after the leak key.

**Single biggest risk:** Bureaucracy. But this prevents "cool patch" drift before deadline.

---

### D3. Submission dry-run mirror

**Pitch:** Treat the portal validator as hostile: run exactly the package layout and Docker constraints locally before any upload attempt.

**Implementation sketch:** Use the official repo's validator/package assumptions: root `bot.py`, optional `data/`, no extra root `.py`, no `.py` in data, no symlinks, size caps, no forbidden imports/calls. The official README confirms the portal validates upload and rejects failing artifacts. ([GitHub][1])

**Acceptance test idea:** `SUBMISSION_READINESS.md` includes:

```text
sha256
zip listing
validator output
import audit output
smoke output
leakage output
size envelope
upload target filename
```

**Single biggest risk:** None material. This is cheap and mandatory.

---

# Repo Prompt workflows for the qualifier

## RP-Q0 — Official deadline/rules reconciliation

**Selection:**

```text
PokerBot/docs/tournament-spec.md
PokerBot/docs/morning-promotion-checklist.md
PokerBot/docs/plans/qualifier-finals-rollout-2026-05-27.md
PokerBot/STATUS.md
PokerBot/consult/artifacts/2026-05-27-worktree-audit/MAP.md
PokerBot/consult/artifacts/release/RELEASE_NOTES.md
PokerBot/ext/fullhouse-engine/sandbox/validator.py
PokerBot/ext/fullhouse-engine/README.md
```

**Prompt:**

```text
Audit the qualifier submission assumptions.

Goal: reconcile local plan files with the official engine README and validator.
Specifically determine:
1. Hard upload deadline.
2. Qualifier run date.
3. Whether latest successful portal upload counts.
4. Package format and validator limits.
5. Which local checklist entries are stale or ambiguous.

Do not edit source. Produce:
- QUALIFIER_RULES_LOCK.md
- one red/yellow/green table
- exact command sequence for pre-upload validation
- any contradiction that requires user attention
```

## RP-Q1 — Current public repo manifest refresh

**Selection:**

```text
PokerBot-codex/submissions/manifest.json
PokerBot/ext/public-bots/neel/
PokerBot/ext/public-bots/dominic/
PokerBot/ext/public-bots/famadeo/
PokerBot/ext/public-bots/vladimir/
PokerBot/docs/deep-research-report.md
PokerBot/docs/investigations/deep-investigation-2026-05-27.md
```

**Prompt:**

```text
Refresh the public-bot threat manifest for qualifier testing.

Do not patch our bot.
For each public opponent:
- repo/branch/commit
- bot path
- data paths
- local source sha
- package zip sha if built
- validator pass/fail
- notes on strategic class

Also record unresolved claimed public repos separately; do not treat unresolved bots as tested evidence.

Output MANIFEST_PUBLIC_QUALIFIER.md and commands needed to rebuild each local public bot zip.
```

## RP-Q2 — Artifact-bound public H2H gauntlet

**Selection:**

```text
PokerBot/tools/h2h.py
PokerBot/tools/benchmark.py
PokerBot/ext/fullhouse-engine/sandbox/match.py
PokerBot/submissions/v_final.zip
PokerBot/ext/public-bots/neel/
PokerBot/ext/public-bots/dominic/
PokerBot/ext/public-bots/famadeo/
PokerBot/ext/public-bots/vladimir/
PokerBot-claude/consults/2026-05-27-overnight-B/SUMMARY.md
PokerBot-claude/consults/2026-05-27-patch1-reconcile/SUMMARY.md
```

**Prompt:**

```text
Design and run the qualifier public-bot H2H gauntlet.

Inputs:
- baseline artifact: submissions/v_final.zip
- public opponents from MANIFEST_PUBLIC_QUALIFIER.md

Run same-seed paired H2H at seed bases 142 and 242.
Use artifact zips only.

Output:
1. public_h2h_summary.json
2. SUMMARY.md table with mean per-match BB, CI, bb/100, actual hands, bust rates, errors
3. RED/AMBER/GREEN verdict per opponent
4. note when bb/100 is unreliable due to early bust / low actual hands
5. no patch recommendation unless a loss is both statistically robust and clusterable
```

## RP-Q3 — Six-max public-pod qualifier gauntlet

**Selection:**

```text
PokerBot/tools/benchmark.py
PokerBot/tools/h2h.py
PokerBot/ext/fullhouse-engine/sandbox/match.py
PokerBot/ext/fullhouse-engine/engine/
PokerBot/submissions/v_final.zip
PokerBot/ext/public-bots/
PokerBot/tools/smoke_run.py
```

**Prompt:**

```text
Build or adapt a six-max qualifier-pod harness.

Goal: estimate 400-hand chip-delta distribution for v_final.zip in pods containing public opponents and reference bots.

Constraints:
- artifact-bound hero only
- no source patching
- no opponent identity logic in our runtime
- output p10/p50/p90, mean, stdev, hero bust rate, hero error count
- use at least 50 seeds per pod if feasible

Produce:
- tools/qualifier_pods.py if needed
- consult/artifacts/.../pod_summary.json
- SUMMARY.md with promote/hold implications
```

## RP-Q4 — Leak clustering before patch permission

**Selection:**

```text
PokerBot/tools/h2h.py
PokerBot/tools/benchmark.py
PokerBot-codex/src/postflop.py
PokerBot-codex/src/bot.py
PokerBot-codex/src/equity.py
PokerBot-claude/consults/2026-05-27-overnight-B/famadeo/SUMMARY.md
PokerBot-claude/consults/2026-05-27-overnight-B/dominic/SUMMARY.md
PokerBot-claude/consults/2026-05-27-confirm-light3bet/SUMMARY.md
PokerBot-claude/consults/2026-05-27-patch1-reconcile/SUMMARY.md
```

**Prompt:**

```text
Cluster public-bot losses and decide whether any qualifier patch is permitted.

Do not patch.

For each RED or AMBER-LOSS opponent, cluster loss by:
street, position, hero_action, board_texture, bet_ratio_bucket, SPR_bucket, multiway_count, recent_raise_depth.

Output:
- top5_leaks.md
- decision_clusters.json
- PATCH_PERMISSION.json only if top-2 clusters explain >50% of loss and each cluster impact >5 mbb/g
- otherwise output NO_PATCH.md explaining why baseline remains safer
```

## RP-Q5 — Conditional qualifier patch

**Selection:**

```text
PokerBot-codex/src/postflop.py
PokerBot-codex/src/equity.py
PokerBot-codex/src/bot.py
PokerBot-codex/tests/edge_cases/test_postflop_wiring.py
PokerBot-codex/tests/edge_cases/test_equity_wiring.py
PokerBot-codex/tests/edge_cases/test_lbr_spot_corrections.py
PokerBot-codex/tests/edge_cases/test_hardening_cases.py
PokerBot-codex/tests/edge_cases/test_legal_actions.py
PokerBot-codex/tools/package.py
PokerBot-codex/tools/exploit_check.py
PokerBot/tools/h2h.py
```

**Prompt:**

```text
Implement a qualifier-safe patch only if PATCH_PERMISSION.json exists.

Scope:
- Prefer src/postflop.py only.
- No new sizing tree nodes.
- No preflop rewrite.
- No opponent names.
- No env-var strategy toggles.
- No Deep CFR / neural runtime.
- Preserve all fixed LBR response cells.

Add tests named after the leak keys.
Build candidate as submissions/v_qual_candidate.zip.
Do not overwrite v_final.zip.

Output:
- minimal diff
- tests added
- exact commands run
- candidate sha
- blocker list for promotion
```

## RP-Q6 — Final pre-upload promotion decision

**Selection:**

```text
PokerBot/docs/morning-promotion-checklist.md
PokerBot/docs/playbooks/hardening.md
PokerBot/consult/artifacts/release/RELEASE_NOTES.md
PokerBot/consult/artifacts/2026-05-31-ship-lock/
PokerBot/consult/artifacts/2026-05-30-qualifier-public-gauntlet/
PokerBot/submissions/
PokerBot/tools/package.py
PokerBot/tools/import_audit.py
PokerBot/tools/smoke_run.py
PokerBot/tools/benchmark.py
PokerBot/tools/exploit_check.py
```

**Prompt:**

```text
Decide the qualifier upload artifact.

Inputs:
- baseline v_final.zip
- optional v_qual_candidate.zip
- public H2H results
- six-max pod results
- full hardening gauntlet logs

Rules:
- If no candidate cleared every gate, upload baseline.
- If candidate regresses any public bot with paired CI excluding zero on negative side, reject.
- If candidate increases LBR aggregate by >20 mbb/g, reject.
- If candidate regresses any reference template statistically, reject.
- If validator/import/leakage/smoke fails, reject.
- If baseline artifact SHA is contaminated, HOLD.

Produce:
- QUALIFIER_DECISION.md
- STATUS.md append block
- exact upload filename and SHA
- rollback instruction
```

---

# Practical decision rule

Do **not** require "we beat every public repo reliably" as a literal gate; that is too strong and mismatched to six-max Swiss. Require this instead:

```text
1. No public-heavy six-max pod has negative median chip delta.
2. No verified public bot is a robust RED H2H loss unless the loss is diffuse/unpatchable and six-max pods still hold.
3. Any patch must improve the RED cell without creating any public-bot HURTS.
4. Baseline reference-bot EV and LBR must remain intact.
```

This respects your concern without overfitting to the public repo set.

---

# If I had to pick ONE patch before qualifier

It would **not** be a patch first; it would be the **artifact-bound public H2H + six-max pod gauntlet**.

If forced to pick one code patch after that, it would be **PATCH-Q1 postflop stackoff veto lite**, because famadeo/dominic-style pressure is the most credible public leak class and it can be isolated to `src/postflop.py`.

It ships only if same-seed public regression says: **famadeo/dominic improve, neel/vladimir do not hurt, reference bots hold, LBR creep stays within budget.**

[1]: https://github.com/uzlez/fullhouse-engine "GitHub - uzlez/fullhouse-engine: NLHE poker bot engine with sandbox, Swiss tournament system, and live demo UI. · GitHub"
[2]: https://repoprompt.com/docs?utm_source=chatgpt.com "Documentation – Repo Prompt"

---

## Orchestrator notes (added at capture time, do not collapse into the verbatim block above)

### Headline disagreement with current plan

The genius response **does not endorse** the current plan's posture of "ship canonical AS-IS on 2026-06-01" as the baseline assumption. It re-frames qualifier readiness as conditional on *public-field robustness evidence we do not yet hold*. This sharpens, rather than overturns, the Phase A protect-the-artifact posture — but it inserts a new gate (artifact-bound public H2H + six-max pods) *before* the SHIP decision rather than treating Phase B as purely post-qualifier.

Three substantive deltas vs `docs/plans/qualifier-finals-rollout-2026-05-27.md`:

1. **Public gauntlet timing.** Plan puts public-bot H2H inside B8 (PATCH-2A gauntlet, *post-qualifier*). Response wants an artifact-bound public H2H + six-max pod sweep **pre-qualifier** (slotted ~2026-05-30 between A1 and A3) as the input to the SHIP/HOLD/MODIFY decision matrix. Plan's `morning-promotion-checklist.md §1` Lane A gate is reference-bot centric; response wants a public-bot gate added.
2. **Promotion metric.** Plan uses paired-seed bb/100 + CI as the primary acceptance metric. Response argues bb/100 is unreliable under early-bust censoring (especially vladimir/famadeo) and requires per-400-hand chip-delta distributions (p10/p50/p90 + bust rate) for any qualifier-relevant promotion.
3. **Patch shape vs scope.** Plan's PATCH-2A is finals-only with a wide veto rule pinned. Response proposes a narrower qualifier-safe PATCH-Q1 with explicit small-bet anti-overfold companion (PATCH-Q2), gated by a `PATCH_PERMISSION.json` artifact derived from leak clustering. The structural seam is the same (`src/postflop.py` `_equity_turn_river_action`, `_heuristic_postflop_action`, `decide_postflop`) but the trigger evidence is stricter.

### Concrete external-source citations made

- Fullhouse engine README — qualifier is Swiss six-max, 400 hands per match, top 64 by cumulative chip delta; upload deadline 31 May 2026 23:59 UTC; sandbox is 2s decide / 30s warmup / 768MB / 0.5 CPU / no network / no writes; data loaded at import time. (Reference treated as primary source for deadline and format.)
- Repo Prompt docs — codemaps, slicing, token budgets, managed selection as the context-control story.

### Items that map directly into plan Open Questions

- **Open Q: A3 leaderboard tooling go/no-go** — already resolved DROPPED. Response neither contradicts nor revisits this. No action.
- **Open Q: PATCH-2A statistical band (B8)** — response strengthens it: paired CI excluding zero on negative side **plus** chip-delta p10 floor **plus** bust-rate cap. Recommend folding into B8 acceptance language when we dispatch B7/B8.
- **Open Q: PATCH-2B trigger thresholds (C1)** — response is silent on PATCH-2B; treat as no signal.
- **Open Q: 2026-06-02 hand-history release time (B9)** — response is silent; treat as no signal.
- **Open Q: B4 sample-size sufficiency** — response strongly implies B4's 5000-hand budget is thin and should jump to per-400-hand-distribution view at 50–100 seed minimum. Pair with the Repo Prompt response before resolving.

### Items the response *adds* that are not currently in the plan

- **Pre-qualifier public H2H + pod gauntlet** (slots ~2026-05-30, between A1 and A3). New work item if adopted: "A2b — artifact-bound public-field readiness gauntlet."
- **`tools/qualifier_pods.py`** — new tool, six-max chip-delta distribution harness.
- **`tools/qualifier_projection.py`** — new tool, top-64 probability bands.
- **`PATCH_PERMISSION.json` discipline** — new pre-patch artifact requirement.
- **`SUBMISSION_READINESS.md`** — new pre-upload artifact.
- **PATCH-Q2 small-bet anti-overfold companion** — explicit pairing requirement with PATCH-Q1 to avoid creating a one-sided overfold.

### Items the response *omits* from current plan

- Phase D SHADOW-CFR-1 red-team lane (sparring opponent, GPU rental). Response is silent — implicitly fine with non-shipping invariant; no contradiction.
- B3 priors-consumer plumbing. Response is silent (it focuses on qualifier shape, not patch-window producer/consumer wiring).
- B5 W3 recalibrated finals projection. Response is silent.

### Recommendation for orchestrator next-step

1. File this genius response.
2. Await Repo Prompt response (parallel task, same brief).
3. Diff the two responses for convergent vs divergent recommendations.
4. Surface the divergences via `ask_user` before dispatching A1 — these touch the SHIP/HOLD decision shape, which is load-bearing.
5. Specifically, ask user whether to adopt the pre-qualifier public gauntlet (A2b) as a hard gate before A3 SHIP, or whether to keep the plan's current Phase B (post-qualifier) timing.

### Provenance

- Captured into: `consult/artifacts/2026-05-27-qualifier-brainstorm/genius_response.md`
- Awaiting paired log: `consult/artifacts/2026-05-27-qualifier-brainstorm/repo_prompt_response.md`
- Diff target (after both arrive): `consult/artifacts/2026-05-27-qualifier-brainstorm/DIFF.md`
