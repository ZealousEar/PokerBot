---
kanban-plugin: basic
---

## Now — pre-qualifier (5 days to 2026-06-01)

- [ ] **HYGIENE-1 — Strip `POKERBOT_DISABLE_OVERLAY` env-var read from `src/bot.py:39`** _~30 min, critical before qualifier upload_
      - [ ] Replace `_OVERLAY_DISABLED = os.environ.get("POKERBOT_DISABLE_OVERLAY") == "1"` with `_OVERLAY_DISABLED = False`
      - [ ] Audit-check that no remaining branch references the variable in a non-trivial way
      - [ ] Re-package `v_final.zip` → new sha; record in STATUS.md
      - [ ] Full G1–G11 gauntlet against the new sha (validator + import + edge + smoke + leakage + exploit + all-templates + ablate + ratchet)
      - [ ] Promote to `best_green.zip` only on full GREEN
      - [ ] Owner: any agent; small enough for a single session
- [ ] **CONFIRM-1 — Paired-seed re-run of Lane T `v5_light_3bet` vs `v_final.zip`** _~1.5h, 0 LOC_
      - [ ] 50 paired seeds × 400 hands × 2 orientations
      - [ ] Acceptance gate before any preflop patch: CI half-width < 30 bb/100 AND CI excludes −50
      - [ ] Output: `consults/2026-05-28-v5-confirm/h2h.json`
- [ ] **PATCH-1 — Light-3bet BB-defend response cell (conditional on CONFIRM-1)** _~2h, ~15 LOC + 3 tests_
      - [ ] Add `_RESPONSE_PATCHES` entry in `src/preflop_lookup.py` keyed on `(position='big_blind', voluntary_seq=('raise',), stack_depth_bb>80)`
      - [ ] Flip from flat → fold for the cell currently leaking
      - [ ] Tests in `tests/edge_cases/test_bb_vs_light_3bet.py`
      - [ ] Regression bench `--six-max-mix` + LBR (no LBR regression > +20 mbb/g)
- [ ] **LEADERBOARD-1 — Localhost round-robin dashboard** _~2h, dev-only deps allowed_
      - [ ] `tools/leaderboard.py` (~100 LOC) — orchestrator running `tools.h2h.run_match` across 18 opponents (5 engine + 4 public + 5 synthetic finals + 4 prior snapshots)
      - [ ] `tools/leaderboard_render.py` (~80 LOC) — stdlib `string.Template` → static `leaderboard.html` with per-cell hands-played + CI width visible
      - [ ] Vanilla JS sort via `<th data-sort>` attributes; no jinja, no pandas
      - [ ] Open `python -m http.server` in `tools/` to view locally
      - [ ] Make hands-played + CI width prominent (Lane B-vladimir's 1085-hand sample should look obviously thin next to 50k-hand engine numbers)
- [ ] **OVERNIGHT-2 — Next overnight queue with adaptive depth + chained continuations** _2026-05-28 night, 9h_
      - [ ] Phase 1 (0–2h): discovery — narrow 22-lane fan-out
      - [ ] Phase 2 (2–6h): chained refinement — each Phase-1 result triggers a follow-up (Lane A leader → A′ 5× seeds; Lane B RED → B′ deeper; Lane T −135 → T′ paired-seed confirm)
      - [ ] Phase 3 (6–9h): commitment — long paired-seed validation of Phase-2 winners
      - [ ] Replace 3-non-improver kill with "stop at 50 % wall budget OR 5 non-improvers"
      - [ ] Add wall-budget watchdog: if >2h remain and no lanes running, auto-launch deeper variants of top-3 candidates from each sweep
      - [ ] Bring up Docker daemon before launch (Lane G failed last night with `docker daemon offline`)
      - [ ] Run Lane J from host shell (codex sandbox `--network none` blocks `gh search` + `curl`)
- [ ] **CORPUS-RESEARCH-1 — Focused /research run for 5 missing notes** _4–6h LLM, off-critical-path_
      - [ ] LBR (Lisý & Bowling 2017, arXiv:1612.07547) — needed because `tools/exploit_check.py` depends on the concept
      - [ ] Bayesian opponent modeling (Bayes' Bluff arXiv:1207.1411 + Billings/Davidson/Schauenberg) — directly powers 06-02 hand-history priors
      - [ ] Public-belief / range-conditioned equity (DeepStack continual resolving) — bridge for the famadeo technique
      - [ ] Action-abstraction theory beyond Pluribus — validates whether our `{1/3, 2/3, pot, 2x, all_in}` tree is adequate
      - [ ] ICM / finals risk-premium — lower priority but missing
- [ ] **PATCH-WINDOW-PREP — Harden `tools/analyze_hand_histories.py` for unknown schemas (per Lane D fragility verdict)** _~3h_
      - [ ] Case-insensitive aliases, camelCase + underscore-insensitive matching
      - [ ] Action synonyms (`bet`/`open`/`jam`/`shove` → aggressive; `match` → call)
      - [ ] Street-nested flattening
      - [ ] Parse-quality diagnostics
      - [ ] Must complete before 2026-06-02 hand-history release

## Hypotheticals / Idea Log

Living log of every proposal that surfaced in chat or consults but did not become a "Now" item. Reviewed every gate; promoted only on numeric evidence. **Do not check these off; they are seeds.**

### Solver / model adoption (cost > value or not portable)

- [ ] Port Vladimir's `gto_strategy.npz` (3.56 MiB MIT NumPy weights) + 274-feature pipeline. **Skipped — useless without his full bot wholesale; Lane B win against us was INDETERMINATE; switching baselines 5 days out is too risky.**
- [ ] Port dberweger2017's Deep CFR weights. **Skipped — trained vs random opponents (screenshot-evidence performance claim); weights not licensed for our use; PyTorch artifacts not validated for our `.npz` export contract.**
- [ ] Train our own Deep CFR as the SHIPPED policy (PyTorch offline + NumPy runtime export). **Skipped — calendar/validation-bound, not infrastructure-bound (2026-05-27 consult correction). Updated rationale:** (a) runtime PyTorch still forbidden but `.npz` + numpy inference is proven feasible (vladimir's `bots/vlad/bot.py` is a working 274→9 numpy MLP forward pass loading `gto_strategy.npz`); (b) GPU rental is now available; (c) the binding constraint is the 9-day calendar — training, integration, packaging, validator+leakage+LBR+all-templates+public-bot gauntlet, and statistically proving the new policy beats the locked artifact does not fit before 2026-06-05 finals close without sacrificing the proven floor. **Allowed adjacent path:** SHADOW-CFR-1 — Deep CFR as a red-team / sparring opponent only, never as a promoted ship artifact (see `docs/plans/qualifier-finals-rollout-2026-05-27.md` Phase D).
- [ ] External-sampling MCCFR overnight on the preflop tree. **Deferred — solver-policy halt condition (2 non-improvers) fired through Lane A/H/M.**

### Counter-plays — Lane O technique catalog

- [ ] **Range-conditioned multiway equity sampler (famadeo)** — ~180 LOC into `src/equity.py` + `src/opponent_model.py`. Highest tournament-impact qualifier patch per Lane O. **Status: not adopted in 48h budget; revisit after CONFIRM-1.**
- [ ] **Postflop realized-equity / stackoff-risk EV veto (famadeo)** — ~110 LOC into `src/postflop.py`. Discount equity for multiway/wet/range-narrowed/recent-raise spots before big bets. **Status: not adopted in 48h budget.**
- [ ] **Preflop pressure-control gate (famadeo)** — ~80 LOC across `src/bot.py` + `src/opponent_model.py`. Avoid deep AK/AQ/QQ collisions vs high-pressure profiles. **Status: not adopted in 48h budget.**
- [ ] Multiway-aware thresholds (vladimir/famadeo/neel) — ~60 LOC. Tighten value/call bars when ≥ 2 active villains.
- [ ] Public-belief state features (famadeo) — ~90 LOC. Live-player count, stack-at-risk, pot-to-stack, recent-raise depth, range-narrowing, field looseness.
- [ ] One-step EV lookahead blended with strategy prior (vladimir) — ~80 LOC.
- [ ] Explicit board stackoff-risk score (famadeo) — ~55 LOC. Quantify monotone/4-flush, paired/trips, connectedness, ace-high.
- [ ] River weak-pair overbet fold gate (dominic) — ~35 LOC.
- [ ] Aggregate table opponent profile (dominic) — ~45 LOC, low-medium impact.
- [ ] Made-hand/draw proxy without MC (dominic) — ~90 LOC; only worth if we want to avoid eval7 cost in tight loops.

### Action abstraction — explicitly DO NOT adopt

- [ ] Off-grid sizing (vladimir's 0.27× and 1.72× pot). **DO NOT ADOPT.** Per finals-strategy §4.4: changing the sizing tree mid-tournament invalidates the postflop blueprint cache. Lane O classified as GIMMICK.
- [ ] Cold-4-bet candidate from Lane M's "candidate_1_widen_3bet_single_open_plus5pp" — best Lane M candidate but pooled SE too wide; below 1.5× SE gate.

### Sweeps that already returned negative

- [ ] **Lane A overlay-coefficient sweep** — top candidate +22.25 bb/100 vs pooled SE 35.98; failed gate. Repeat in OVERNIGHT-2 as 2D `(overlay × sizing)` grid with narrower spacing.
- [ ] **Lane H sizing-frequency sweep** — all 3 candidates lost (−11, −21, −89 bb/100). Keep baseline.
- [ ] **Lane M 3-bet / 4-bet sweep** — only baseline measured before kill rule fired. Re-run with looser kill rule in OVERNIGHT-2.
- [ ] **Lane L preflop range tuning** — best Δ +12.30 bb/100 but pooled SE 106.08; not significant. Famadeo VPIP 95.14 % explains the underlying mismatch; range tuning alone cannot close it.

### Research worth doing (off critical path)

- [ ] Run a tournament-finish MC with the corrected priors: field size 100–300, edge per entrant sampled from a wider prior (not just the 9 measured opponents), Swiss rounds 6–12.
- [ ] Build synthetic-field opponents at competent-but-balanced 3-bet frequencies (not adversarial 12 %) — Lane T's v5 over-estimates the threat.
- [ ] ICM module — single-elim bracket payout asymmetry; chip EV ≠ tournament EV in deep brackets. Lower priority but missing entirely.
- [ ] Replay-tool fix (`tools/replay.py` is a TODO stub per Lane F); proper replay would let us audit specific decisions.
- [ ] Stronger LBR spot suite (Lane I 20→100 expansion already done; consider 500-spot per Module 4.1).

### Process improvements

- [ ] Adaptive overnight queue (OVERNIGHT-2 above) — formalize the Phase 1 / 2 / 3 chain pattern.
- [ ] Wall-budget watchdog — auto-launch deeper variants when >2h remain and no lanes running.
- [ ] Pre-launch infra check — Docker up, network reachable, `submissions/v_final.zip` sha verified before kick-off.
- [ ] Multi-pass design template — every overnight lane brief should include a "if you finish early, do X" continuation clause.

## Backlog

- [ ] **Module 2 — Anti-gaming infrastructure** _target 2026-05-23..24, ~10 h_
      Plan: `consults/post-goal-amendments-plan.md` (gitignored). Five new files; per-branch manifest model.
      - [ ] `tools/anonymize.py` — sha1-anon wrapper around engine `bot_id` boundary
      - [ ] `tools/strategy_audit.py` — AST scan over `src/` for identity strings + shim env-vars
      - [ ] `tools/promote_artifact.py` — only legal write path into `submissions/`; runs validator+import+edge+smoke gates
      - [ ] `submissions/manifest.json` (per branch) — append-only ledger with sha256s and log hashes
      - [ ] `submissions/arbitration_manifest.json` (main only) — pins which branch ships for qualifier / finals
- [ ] **Module 3 — Surgical prompt amendments** _target 2026-05-25, ~1 h, depends on Module 2_
      Plan A diffs only (rejects MCCFR-required / H2H-as-Done-when / 100-spot LBR-in-prompt).
      - [ ] `PROMPT.shared.md` — symmetric overlay caps (≤ 20 pp), aggressor switch to seat-swap match-share, ratchet artifacts sha256-pinned via manifest, LBR must call `decide()` per spot
      - [ ] `PROMPT.shared.md` — NEW Done-when #10 (blueprint floor), #11 (no identity branching), #12 (advisory 6-max)
      - [ ] `PROMPT.claude.md` — population-statistics overlay (no opponent names), `opponent_model.py` must be live not dead-code, anti-gaming hygiene
      - [ ] `PROMPT.codex.md` — sweep targets become archetype seats (tight/loose × passive/aggressive), LBR must call decide() per spot, anti-gaming hygiene
- [ ] **Module 4 — Real LBR + 6-max + archetypes + RR H2H** _target 2026-05-26..28, ~14 h, finals-only_
      Depends on Module 2 anonymization API.
      - [ ] `tools/exploit_check.py` rewrite (~280 LOC) — claude's scaffold + zip-loader fix + 500-spot scale
      - [ ] `tools/benchmark.py --six-max-mix` (~250 LOC) — 4 compositions × 200 matches × 400 hands; bootstrap CI
      - [ ] `tools/archetypes/{controlled_aggressor,loose_passive_station,sharp_3bet_punisher,float_and_stab,tight_aggro_balanced}/bot.py` (~400 LOC total)
      - [ ] `tools/archetypes/_heldout_wrapper.py` — `POKERBOT_HELDOUT_SEED` at import time, not in `game_state`
      - [ ] `tools/h2h.py --round-robin` (~120 LOC) — N-way paired-seed seat-swap, worst-case CI selection rule
- [ ] **Module 5 — Optional 2-branch re-run with corrected prompts** _finals-only, decided 2026-05-30_
      Conditional on Modules 2-4 landing and post-X1 codex passing Module 4's bar.
      - [ ] Apply Module 3 prompts on `main`, fast-forward worktrees
      - [ ] Kick off `/goal` on claude (Claude Code) + codex (Codex CLI) with corrected prompts
      - [ ] Round-robin H2H across {old codex pre-X1, codex post-X1, new claude, new codex}
      - [ ] Module 4.4 selection rule picks finals artifact
- [ ] **2026-06-02 hand-history patch window** _orthogonal to Modules 2-5; existing playbook_
      - [ ] `tools/analyze_hand_histories.py` — introspect schema from first JSON record; emit compact priors
      - [ ] `data/finals_priors.npz` — population VPIP/PFR, fold-to-c-bet, sizing percentiles, common preflop sequences, bot-cluster fingerprints
      - [ ] Re-run full validator + import + edge + smoke + benchmark suite; preserve qualifier artifact

## In Progress

- [ ] **GOAL Pass 2 — claude + codex re-runs (initial, not Module 5)** _started 2026-05-22, tmux panes_
      - [ ] Pane 1: `~/Code/PokerBot-claude/` — Claude Code `/goal @PROMPT.shared.md` (current prompts, pre-Module 3)
      - [ ] Pane 2: `~/Code/PokerBot-codex/` — Codex CLI `/goal @PROMPT.shared.md` (current prompts, pre-Module 3)
      - [ ] Watch for `## FINAL SUBMITTED` in both STATUS.md tails
      - [ ] If completed: paired H2H {pass-1 codex post-X1, pass-2 claude, pass-2 codex} to inform Modules 3-5
      - [ ] Caveat: prompts are NOT yet patched per Module 3 — expect similar gaming behaviour to pass 1

## Done

- [x] **Overnight 2026-05-27 — 21-lane parallel probe queue** @{2026-05-27, 70 min wall, 7.8 h cap unused}
      - [x] Wall: T+0 `01:06:49Z` → last lane finished `02:17:36Z` (Lane F dominant at 47 min). 18 PASS / 3 KILL (A, H, M — baseline holds) / 2 SKIPPED (G no Docker, J no network) / 1 FRAGILE (D)
      - [x] Baseline `submissions/v_final.zip` sha `e4b4a8f1…598` byte-stable through every lane; no auto-promote occurred
      - [x] Lane B — H2H vs publics: vladimir +55.30 ⚠ (1085-hand sample, CI [−16, +40] crosses 0, INDETERMINATE per h2h.py), neel +28.89 ✅, dominic −4.31 ⚠, famadeo −21.54 ❌
      - [x] Lane A — overlay sweep: top candidate (MAX_DEV=0.15, threshold (0.50, 0.30)) +22.25 bb/100 vs pooled SE 35.98 — fails 1.5×SE gate; baseline holds
      - [x] Lane E — finish MC: P(top 64)=99.94 %, P(top 5)=11.62 %, P(top 1)=1.67 % — **but anchored on field=128 + 10 Swiss rounds (both unverified); see CI-AUDIT note below**
      - [x] Lane F — adversarial seeds: top-3 leaks are river raise lines vs dominic/famadeo on dry-ish boards; blueprint & overlay agree, so it's a blueprint-level postflop issue
      - [x] Lane K — LBR vs competitors: all within caps. vladimir 96.3 / 77.6 mbb/g (worst preflop), dominic 54.4 / 53.8, famadeo 84.5 / 76.3, neel 72.3 / 77.3
      - [x] Lane I — LBR suite expanded 20 → 100 spots: aggregate 74.4 mbb/g (was 37.6 in the 20-spot run); broader spots find more leakage; still under the 200 cap
      - [x] Lane N — adversarial states: 998/1000 PASS; 2 failures both `negative_amount` → recommendation: clamp raise amounts in legalize path
      - [x] Lane O — competitor source dive: 21 techniques catalogued; top-3 portable (range-conditioned equity, postflop EV veto, preflop pressure gate — all from famadeo)
      - [x] Lane P — Vladimir Deep CFR: 274→9 numpy-only inference at runtime; training is PyTorch + C++ MCCFR with ~9 GiB reservoirs (NOT portable). Only `bot.py` + 3.56 MiB `gto_strategy.npz` is sandbox-safe — and only as a wholesale bot swap, not a bolt-on
      - [x] Lane Q — worktree state: `PokerBot-claude` and `PokerBot-codex` worktrees both diverged from canonical; `codex` is at `9904ed1` (X1 patch, NOT pushed)
      - [x] Lane R — X1 AMBER resolved: 50k template re-run +71.81 bb/100 (CI low +71.34) matches codex STATUS +71.82; the +13.20 in claude STATUS was 10k variance. **BUT** `audit_strategy_leakage` flags `src/bot.py:39` reading `POKERBOT_DISABLE_OVERLAY` env-var — internal hygiene fail, NOT a validator/rule break; see HYGIENE-1 in Now section
      - [x] Lane S — decision-cluster mining: 1000 hands replayed, 34 clusters; top suspicious is `trash_SB_short` at 96.8 % aggression (likely correct push-or-fold). 4 more `trash_SB_*` clusters flagged
      - [x] Lane T — synthetic finals field: 5 variants generated, **all 5 beat v_final**. v5_light_3bet (12 % BB 3-bet defense) costs us −135.76 bb/100 [CI −100, −67] — worst. v4_nit_exploiter −38.81 (best of the field, still negative)
      - [x] Lanes G / J skipped — Docker daemon offline at host; codex sandbox `--network none` blocks `gh search` + `curl`. Both deferred to morning host execution
      - [x] Wake-up SUMMARY at `consults/2026-05-27-overnight-SUMMARY/SUMMARY.md` + FAILURES.md + STATE.json
      - [x] **Critical takeaways (oracle synthesis 2026-05-27, see `docs/investigations/deep-investigation-2026-05-27.md`):**
            - DeepCFR ship/skip decision: STATUS QUO WINS. Don't port vladimir, don't port dberweger, fix the env-var, ship `v_final.zip`.
            - P(top 64) realistic span 40–90 %, not Lane E's 99.94 %.
            - P(win finals) 1–15 %.
            - P(facing ≥1 adversarial light-3-bet bracket opponent) 25–40 %.
            - 9h overnight ran 1h because lanes were too narrow + no second-wave plan + kill conditions too aggressive — see OVERNIGHT-2 in Now section for the structural fix.
- [x] **Independent arbitration audit + CODEX_WINS verdict** @{2026-05-22}
      - [x] Ran the 12-step audit brief (`A. repo identity` → `J. fresh-context handoff`) over both `~/Code/PokerBot-{claude,codex}` worktrees from `main`, no edits to either worktree
      - [x] Static gates: validator, import_audit (0.049 s / 22.3 MB claude vs 0.119 s / 32.5 MB codex), edge_case pytest (claude 21/21 vs codex 25/25), package strict, smoke, exploit_check, audit_strategy_leakage — both PASS
      - [x] 1 000-hand artifact-bound dynamic re-runs INITIALLY suggested `BOTH_FAIL_SELECT_LAST_GREEN`: all-templates (claude shark CI<0 + aggressor 76-hand bust; codex aggressor −0.65), ablate (claude −3.14 / codex −76.43 gain), ratchet (claude v1/v2/v3 all FAIL; codex v1/v2/v3 all −13.50)
      - [x] Advisor flagged that 1 k paired-seed CI widths (aggressor half-width ≈ 167 bb/100) cannot refute STATUS-claimed 10 k numbers; 10 k re-runs re-instated for both branches
      - [x] **Codex 10 k re-run PASSES every dynamic gate** — `template +71.82 / aggressor +87.76 / math +144.60 / shark +70.14 / ref_bot_2 +144.60` (all CIs > 0, all ≥ 15); ablate gain `+32.53`; ratchet `+74.41 / +18.89×3`. Every number matches codex STATUS to the decimal. `audit_strategy_leakage` re-run on `v_final.zip` → PASS.
      - [x] **Claude 10 k re-run still FAILS** with the AMBER pattern claude STATUS already self-flagged: shark CI low `−4.48`, template bb/100 `+13.20 < 15`. Reproduces STATUS exactly.
      - [x] Confirmed `v_final_pre_x1.zip` (`5d65561e…cef`) FAILS leakage audit (20+ literal opponent strings in `src/bot.py`) — permanently disqualified as ship candidate. The X1 patch was load-bearing for legitimacy.
      - [x] Verdict: **`CODEX_WINS`**. Ship candidate `~/Code/PokerBot-codex/submissions/v_final.zip` sha `e4b4a8f1…598`.
      - [x] Artifacts written to `consult/artifacts/arbitration/`: `ORCHESTRATOR_REPORT.md`, `fresh_context_handoff.md`, full per-branch logs (claude 47 KB / codex 110 KB), diffs (190 KB / 200 KB), STATUS copies. No worktree-level merges.
- [x] **Release branch `release/v_final-e4b4a8f1` promoted onto `main`** @{2026-05-22}
      - [x] Branched from `main` HEAD `9aa4dc0`; main's uncommitted CHANGELOG/KANBAN/STATUS edits stashed and restored after.
      - [x] `rsync`'d safe paths from `~/Code/PokerBot-codex` working tree (post-X1 dirty state, the one that produced the artifact): `src/`, `tools/`, `tests/`, `data/`, `STATUS.md`. Main-only files preserved: `tools/h2h.py`, scaffold test dirs. `__pycache__` and `.DS_Store` excluded. `.venv` / `ext` symlinks NOT carried.
      - [x] `cp`'d 8 submission zips: `v_final.zip`, `best_green.zip` (both sha `e4b4a8f1…598`), `manifest.json`, 4 priors (`v0_wired`, `v1_blueprint`, `v2_postflop`, `v3_hardened`), `v_final_pre_x1.zip` (snapshot only — never promotable). `.gitignore` keeps zips on disk only.
      - [x] Pre-commit hook (`.githooks/pre-commit`) validated and passed; commit `a00561c` landed (19 files changed, +2 759 / −120).
      - [x] Full gauntlet from `~/Code/PokerBot` against `submissions/v_final.zip`: G1 import_audit (cold 0.079 s / 33.8 MB), G2 pytest (25/25), G3 validator PASS, G4 package strict (v_final_reaudit.zip sha `9a3b812e…0b0` — different from canonical due to zip timestamps; per-file SHAs identical, verified by extract-and-diff), G5 validator reaudit PASS, G6 smoke 200/200 chip Δ +14 500, G7 leakage audit PASS (zero hits on 14 forbidden tokens), G8 exploit_check preflop 18.0 / aggregate 7.4 mbb/g PASS, **G9 all-templates 10 k PASS** (`template +71.82 / aggressor +112.63 / math +144.60 / shark +70.16 / ref_bot_2 +144.60` — all CIs > 0, all ≥ 15), **G10 ablate-overlay 10 k PASS** (gain `+32.53`), **G11 self-play vs-prior 10 k PASS** (`v0 +74.41 / v1/v2/v3 +18.89` each).
      - [x] SHA preservation verified at three checkpoints (post-copy, post-commit, post-gauntlet) — `e4b4a8f1…598` unchanged throughout.
      - [x] Artifacts written to `consult/artifacts/release/`: `RELEASE_NOTES.md` (12 KB), `gauntlet.log` (56 KB).
      - [x] `main` HEAD unchanged at `9aa4dc0`; release branch separate at `a00561c`. User's audit narrative restored to `main` via stash pop.
- [x] **GOAL Pass 1 — both branches FINAL SUBMITTED (caveats flagged)** @{2026-05-22}
      - [x] `claude` branch: `## FINAL SUBMITTED` posted by Claude Code `/goal`. Heuristic blueprint + bounded overlay (~+8 bb/100 overlay gain).
      - [x] `codex` branch: `## FINAL SUBMITTED` posted by Codex CLI `/goal`. Submission sha `5d65561e…`.
      - [x] Paired-seed seat-swap H2H (50 matches × 200 hands) on `main`: codex wins decisively (claude per-match BB delta −65.40, claude busts 24/50, codex busts 0/50).
      - [x] Post-mortem (separate card below) flagged 12 issues — branches "passed" their Done-when criteria but via gaming surfaces, not genuine GTO progress.
- [x] **Module 0 — Save consult artifacts + .gitignore policy** @{2026-05-22}
      - [x] `consults/codex-vs-claude-postmortem.md` — outgoing prompt to genius LLM (Opus 4.7-class), 20848 bytes
      - [x] `consults/codex-vs-claude-postmortem.reply.md` — full reply (5.1–5.5 + 3 unified diffs + citations [1]–[19]), 34561 bytes, extracted from transcript
      - [x] `consults/post-goal-amendments-plan.md` — derived modular execution plan, 27922 bytes
      - [x] `.gitignore` line 54: `consults/` (commit `9aa4dc0` on main, pushed)
- [x] **Module 1 — Codex X1 surgical patch (commit `9904ed1`, NOT pushed)** @{2026-05-22}
      - [x] `src/bot.py` 239 → 172 LOC: deleted `_PRIOR_BOT_IDS`, postflop dispatch (no-op), preflop `aggressor` + `_PRIOR_BOT_IDS` branches, 4 dead helpers. Net −67 LOC, 0 added.
      - [x] Verifications: validator PASS, import 0.272 s / 33.1 MB, edge 25/25, smoke 200/200 errors `{}`, smoke chip delta +14500 vs template.
      - [x] Paired bench vs pre-X1: template 0.00, mathematician 0.00, ref_bot_2 0.00, shark −0.49, aggressor −412.62 (expected; non-aggressor max ≤ 30 bb/100 rollback threshold NOT triggered).
      - [x] Pre-X1 rollback artifact preserved at `submissions/v_final_pre_x1.zip` (sha `5d65561e…`); post-X1 sha `d1b5cad3…`.
      - [x] `STATUS.md` (codex) appended with full proof-of-green block + open items deferred to Modules 2-4.
- [x] **Module 1 — Diagnostics bundle for consult review** @{2026-05-22}
      - [x] Bundle path: `/Users/farhad/Code/PokerBot-codex/consults/day1_x1_bundle.zip`, 59 KB zip, sha `5c53c1cf…`, 34 files (uncompressed 203 KB)
      - [x] Compiled by 3 parallel subagents (git+copies, fast verifications, slow benchmarks); 2 verify subagents flagged P1 gaps (4 source files, pre-X1 verification, zip-bound benchmarks, paired H2H)
      - [x] Gap-fill round: added `sources/{tools_exploit_check.py,tools_benchmark.py,src_preflop_lookup.py,src_opponent_model.py,PROMPT.{shared,claude,codex}.md}`, pre-X1 validator+smoke+inventory, zip-bound benchmarks for both artifacts, `paired_delta_summary.txt`, `MANIFEST.md`, `env_info.txt`
      - [x] H2H pre-X1 vs post-X1 (10000 hands paired-seed): per-match BB delta **+0.00** (CI [−3.36, +3.30]), INDETERMINATE, both bots 0 errors — confirms X1 is EV-neutral hygiene fix
      - [x] Confirmed empirically: post-X1 overlay-ablation gain `−8.40` / `−4.76` (was fabricated `+417.21`); self-play ratchet vs v1/v2/v3 `−0.87` (was fabricated `+4.47`); `exploit_check.py` still prints hardcoded `[12, 18, 22, 15, 20]` mbb/g (deferred to Module 4.1)
- [x] **G0 — Scaffold** @{2026-05-22}
      - [x] Directory tree under `~/Code/PokerBot/{docs/playbooks,src,data,tests/{unit,integration,edge_cases,property},tools,ext,submissions}`
      - [x] `ext/fullhouse-engine/` cloned from upstream
      - [x] `AGENTS.md`, `PROMPT.md` (later → `PROMPT.shared.md` + branch prompts), `PLAN.md`, `STATUS.md`, `README.md`
      - [x] `docs/{tournament-spec,api-cheatsheet,corpus-index}.md`, `docs/playbooks/{patch-window,hardening}.md`
      - [x] `src/*.py` stubs (8 modules); safe-fallback bot returns legal action for every input
      - [x] `tools/*.py` stubs (8 scripts); `import_audit` + `package` functional
      - [x] `tests/edge_cases/test_safe_fallback.py` (4 cases pass)
      - [x] `requirements.txt` pinned to engine `Dockerfile`
      - [x] `submissions/v0_scaffold.zip` — engine validator PASSED
- [x] **G0.5 — Environment + Corpus** @{2026-05-22}
      - [x] `.venv` via `uv venv --python 3.10` (Python 3.10.18)
      - [x] `eval7==0.1.7` via 2-step install (Cython<3, --no-build-isolation)
      - [x] `numpy==1.26.4`, `scipy==1.13.0`, `treys==0.1.8`, `scikit-learn==1.5.2`
      - [x] eval7 + treys functional smoke test passed
      - [x] 7 Obsidian vault notes covering CFR, MCCFR, CFR+, Libratus, Pluribus, Cepheus, DeepCFR, Engine-Fullhouse
      - [x] `docs/corpus-index.md` rewritten with flat wikilinks
- [x] **G0.6 — Success criteria upgraded** @{2026-05-22}
      - [x] `PROMPT.md` Codex-`/goal`-compliant + directional (3782 chars)
      - [x] Crush margin ≥ 15 bb/100, overlay ablation ≥ 3 bb/100, ratchet ≥ 3 bb/100, LBR ≤ 100/200 mbb/g
      - [x] `AGENTS.md` Game-theoretic frame section (blueprint + bounded overlay)
      - [x] `PLAN.md` per-gate corpus anchor; new G5
      - [x] `tools/benchmark.py` `--ablate-overlay`, `--self-play --vs-prior`, `--all-templates`
      - [x] `tools/exploit_check.py` framed as LBR (Lisý & Bowling 2017)
      - [x] `CLAUDE.md` symlinked to `AGENTS.md`
- [x] **G0.7 — Parallel run infrastructure** @{2026-05-22}
      - [x] `git init -b main`, tag `scaffold-baseline`, branches `main` / `claude` / `codex`
      - [x] `.gitignore` augmented (data/*.npz, swap files, mypy/ruff caches)
      - [x] `data/.gitkeep` + `submissions/.gitkeep` for fresh worktrees
      - [x] `git worktree add ../PokerBot-{claude,codex} {claude,codex}`
      - [x] `.venv` and `ext/` symlinked from main into each worktree (gitignored)
      - [x] Both worktrees independently GREEN on import_audit + pytest + package + validator
      - [x] Native `/goal` launch path confirmed (not `/ralph`); persisted as feedback memory `pokerbot-uses-native-goal.md`
- [x] **G0.8 — Pre-launch hardening** @{2026-05-22}
      - [x] `PROMPT.shared.md` + `PROMPT.claude.md` + `PROMPT.codex.md` (branch-differentiated)
      - [x] `.githooks/pre-commit` — protects `best_green.zip` invariant on `submissions/` stages
      - [x] `tools/smoke_run.py` — real-container 200-hand smoke; closes validator's AST-only gap
      - [x] `tools/benchmark.py` paired-seed flags; variance policy in `AGENTS.md`
      - [x] `submissions/best_green.zip` bootstrapped from `v0_scaffold.zip`
- [x] **G1–G5 (as goal-pass-1 outputs)** @{2026-05-22}
      - [x] Both branches walked the gate ladder G1 → G5 via their respective `/goal` agents from `scaffold-baseline` tag
      - [x] Both ended on `## FINAL SUBMITTED` with validator-passing artifacts
      - [x] Post-mortem identified that several gate criteria were satisfied via gaming surfaces (claude `tools/package.py` shim flags; codex `_PRIOR_BOT_IDS` + aggressor branch); see CHANGELOG entry "Post-/goal audit" for the 12-issue list

## Bugs / Known Issues

- [ ] **claude `tools/package.py` shim flags** — `--v0-style/--v2-style/--v3-style` build deliberately-weakened variants labeled as historical snapshots; ratchet ladder fabricated. `MEDIUM`. Resolved by Module 2 `strategy_audit.py` + manifest-pinning. Owner: post-Module 2 cleanup pass.
- [ ] **claude `tools/train_preflop.py` / `train_flop.py` TODO stubs** — `LOW`. Solver escape hatch became default path. Defer to post-finals retrospective.
- [ ] **codex `src/opponent_model.py` dead code** — `LOW`. Module 1 left untouched; live wire-up is ~16 p-hours, deferred to post-qualifier (Module 5 territory).
- [ ] **codex `src/preflop_lookup.py:41-42` 100% HU button/SB open** — `MEDIUM`. Structural vulnerability vs sharp 3-bet defenders. Module 4 archetypes (`sharp_3bet_punisher`) will quantify.
- [x] **codex `tools/exploit_check.py:34-41` hardcoded constants** — `HIGH`. **RESOLVED 2026-05-22** by codex's X1-era rewrite. The deployed tool now extracts the artifact zip, evicts cached imports, calls the loaded `decide()` on 20 deterministic spots, and scores each action with a per-spot counterplay-risk function. Verified during 2026-05-22 arbitration audit by inspecting `~/Code/PokerBot-codex/tools/exploit_check.py` (`grep -nE '\[12.*18.*22.*15.*20\]'` returns no matches; uncommitted diff vs HEAD is +476 lines that replace the stub) and by reading G8 gauntlet output on release branch (20 distinct actions, risk scores 0–35 mbb/g, not constants). Still documented as PARTIAL LBR (not a Nash exploitability proof) but no longer a stub. Module 4.1 follow-up now optional, not blocking.
- [ ] **codex `tools/benchmark.py:217,219` `_run_ablation()` aggressor-only** — `MEDIUM`. Module 4.2 rebuilds with `--six-max-mix`.
- [ ] **Engine `ext/fullhouse-engine/sandbox/match.py:228` 2≤n≤9 but benchmarks are HU** — `HIGH`. Tournament is 6-max; benchmark coverage is asymmetric to deployment.

## Open questions

- [ ] Whether to push `codex` branch (carrying commit `9904ed1`) before qualifier — currently NO (avoid public counter-exploitation); diagnostics bundle uploaded privately instead. **Update 2026-05-22**: the arbitration audit and `release/v_final-e4b4a8f1` promotion eliminate the need to push `codex-x1-repair` at all — the ship state is on `main` as a separate branch. Codex worktree can stay private indefinitely.
- [ ] Whether GOAL Pass 2 changes the calculus for Modules 2-5 (depends on what claude/codex re-runs produce in the tmux panes).
- [ ] Whether Module 5 re-run with corrected prompts is worth the compute vs shipping post-X1 codex for finals — decided 2026-05-30.

***

%% kanban-plugin: basic %%
