---
kanban-plugin: basic
---

## Overnight 2026-05-27 — Parallel multi-lane probe queue _10+ h, Codex-led, Claude orchestrator only_

Worktree: `~/Code/PokerBot-claude/`. Baseline artifact: canonical `submissions/v_final.zip` sha `e4b4a8f1…598`. **No auto-promote.** Acceptance criteria pre-committed before launch; logged to `consults/2026-05-27-overnight-<lane>/PRE_COMMIT.txt`. Global kill switch: 9 wall-hours. Per-lane kill switches inline.

### Tier 1 — must run (high ROI, well-spec'd)

- [ ] **Lane B — H2H vs public competitor bots** _⭐ primary missing data point, ~30 min wall_
      - [ ] Reuse `tools/h2h.py` against `ext/public-bots/{vladimir,dominic,famadeo,neel}/<bot>/bot.py`
      - [ ] Paired seeds 42–51, 10 000 hands per opponent, 6-max table
      - [ ] Per-opponent bb/100 ± 95 % bootstrap CI; flag any opponent that fails to load (vladimir / famadeo flagged risks)
      - [ ] Output: `consults/2026-05-27-overnight-B/{opponent}/h2h.json` + `SUMMARY.md`
      - [ ] Accept: mean > 0 AND CI low > −20 bb/100 per opponent; otherwise flag "exploitable matchup"
- [ ] **Lane A — Overlay-coefficient sweep** _~2–3 h wall, 1 core_
      - [ ] Tune `src/opponent_model.py` `MAX_DEVIATION_PP` × {`HYPER_AGG_THRESHOLD`, `AGG_THRESHOLD`}; 5 × 3 = 15 candidates
      - [ ] Grid: MAX_DEV ∈ {0.10, 0.15, 0.20, 0.25, 0.30}; thresholds ∈ {(0.50, 0.30), (0.55, 0.35), (0.60, 0.40)}
      - [ ] Per candidate: `tools/benchmark.py --all-templates --hands 50000 --paired-seed-base 42 --paired-seed-count 10` + LBR + edge + import + validator
      - [ ] Accept ALL: bb/100 > baseline + 1.5 × pooled SE; LBR pre ≤ 100; LBR agg ≤ 200; edge clean; import clean; validator PASS; beats ≥ 4 of 7 templates in H2H
      - [ ] Kill: 3 consecutive non-improving candidates OR 6 CPU-hours
      - [ ] Output: `consults/2026-05-27-overnight-A/{PRE_COMMIT.txt, LEADERBOARD.json, SUMMARY.md, candidate_<i>/}`
- [ ] **Lane D — Patch-window dry-run** _~30 min wall, 1 core_
      - [ ] Generate 5 synthetic hand-history JSON variants (snake_case, camelCase, partial fields, alt action names, nested schemas)
      - [ ] Run `tools/analyze_hand_histories.py` against each; pass if non-degenerate `.npz` produced
      - [ ] Output: `consults/2026-05-27-overnight-D/{synthetic/V<n>.json, priors/V<n>_priors.npz, RESULTS.md}`

### Tier 2 — high ROI, parallelizable

- [ ] **Lane E — Tournament-finish variance Monte Carlo** _~30 min, depends on Lane B_
      - [ ] MC sim: 400-hand Swiss matches, sample field bb/100 from Lane B + STATUS template numbers
      - [ ] Compute P(finish ≤ 1, ≤ 5, ≤ 64) at current edge across N = 10 000 simulated tournaments
      - [ ] Output: `consults/2026-05-27-overnight-E/{finish_distribution.json, plot.png}`
- [ ] **Lane F — Adversarial seed search** _~1–2 h, 1 core_
      - [ ] Run `tools/h2h.py` across seeds 1–500 vs each opponent; identify worst-10 by chip delta per matchup
      - [ ] Replay top 3 worst-seed hands with `tools/replay.py` per opponent; isolate culprit decision
      - [ ] Output: `consults/2026-05-27-overnight-F/{worst_seeds.json, replay_traces/}`
- [ ] **Lane G — Cold-start RSS + decision latency stress** _~30 min, requires Docker_
      - [ ] 400 hands inside real `fullhouse-sandbox:latest` container; log RSS time series via `docker stats`
      - [ ] Capture p50 / p99 / p999 / max `decide()` time
      - [ ] Output: `consults/2026-05-27-overnight-G/{rss_timeseries.csv, decide_latency_histogram.json, SUMMARY.md}`
      - [ ] Flag any RSS > 700 MB or any decide() > 1.8 s as red
- [ ] **Lane K — LBR vs specific public competitor bots** _~1 h, depends on Lane B_
      - [ ] Use each public bot as the best-responder approximation in `tools/exploit_check.py`
      - [ ] Per-spot mbb extraction vs each competitor
      - [ ] Output: `consults/2026-05-27-overnight-K/lbr_vs_competitor/{vladimir, dominic, famadeo, neel}.json`

### Tier 3 — ROI-positive, lower priority

- [ ] **Lane H — Sizing-frequency sweep** _~2–3 h, 1 core, STAGGER with A (same files)_
      - [ ] Sweep relative weights {1/3, 2/3, pot, 2x, all_in} per street × position bucket; CMA-ES or coarse grid
      - [ ] Per candidate: 50 k paired-seed benchmark + LBR + edge tests
      - [ ] Output: `consults/2026-05-27-overnight-H/sizing_sweep/`
      - [ ] DO NOT run concurrently with Lane A; run after A completes
- [ ] **Lane I — LBR suite expansion (20 → 100 spots)** _~1 h_
      - [ ] Stratified spots: street × position × stack depth × pot size
      - [ ] Re-run on `v_final.zip`; compare to existing 20-spot reading
      - [ ] Output: `consults/2026-05-27-overnight-I/lbr_expanded.json`
- [ ] **Lane J — Github rescan for new competitors** _~30 min, agent task_
      - [ ] Search `fullhouse`, `hackathon`, `quadrature`, `poker bot` repos updated in last 7 days
      - [ ] Report any new finds with stars / commit recency / first impression
      - [ ] Output: `consults/2026-05-27-overnight-J/new_competitors.md`
- [ ] **Lane N — Validator red-team / adversarial states** _~1 h_
      - [ ] Generate ~ 1 000 adversarial game states (malformed types, missing fields, edge stacks, 7-seat tables)
      - [ ] Confirm `decide()` returns legal action or safe fallback for every one
      - [ ] Output: `consults/2026-05-27-overnight-N/adversarial_results.json`

### Tier 4 — liberal stretch (only if everything above is queued or done)

- [ ] **Lane L — Preflop range tuning vs observed competitor VPIPs** _~2 h, depends on Lane B_
      - [ ] Estimate each public bot's VPIP from Lane B logs
      - [ ] Sweep `BORDERLINE_OPEN` / `CORE_OPEN_RANGES` adjustments via paired-seed benchmark
      - [ ] Output: `consults/2026-05-27-overnight-L/range_tuning/`
- [ ] **Lane M — 3bet / 4bet frequency sweep** _~2 h_
      - [ ] Same shape as L but on 3-bet and 4-bet rates
      - [ ] Output: `consults/2026-05-27-overnight-M/3bet_sweep/`
- [ ] **Lane O — Competitor source dive for unimported techniques** _~30 min, agent task_
      - [ ] `agent_run` reads `ext/public-bots/{vladimir,dominic,famadeo,neel}/` and lists techniques not in `PokerBot-claude/src/`
      - [ ] Output: `consults/2026-05-27-overnight-O/competitor_techniques.md`
- [ ] **Lane P — Vladimir Deep CFR pipeline analysis** _~45 min, agent task_
      - [ ] `agent_run` reads `ext/public-bots/vladimir/bots/vlad/deep_cfr*/` end-to-end; report architecture, training cost, any reusable artifacts (check rules first)
      - [ ] Output: `consults/2026-05-27-overnight-P/vladimir_analysis.md`
- [ ] **Lane Q — Worktree reconciliation** _~5 min, meta_
      - [ ] `git status` + `git log` across {PokerBot, PokerBot-claude, PokerBot-codex}; surface uncommitted work and branch divergence
      - [ ] Output: `consults/2026-05-27-overnight-Q/worktree_state.md`
- [ ] **Lane R — Resolve PokerBot-claude X1-repair AMBER** _~30 min_
      - [ ] 50 k paired-seed re-run of template-only on claude X1-repair branch; determine whether the +13.20 vs +71.82 gap is noise or regression
      - [ ] Output: `consults/2026-05-27-overnight-R/x1_amber_resolution.json`
- [ ] **Lane S — Replay-based decision-cluster mining** _~1 h_
      - [ ] 1 000-hand self-play replay; cluster decisions by hand type and flag potentially wrong patterns
      - [ ] Output: `consults/2026-05-27-overnight-S/decision_clusters.json`
- [ ] **Lane T — Synthetic finals-field generation** _~2 h_
      - [ ] Build 5–10 stronger "finals competitor" variants from public archetypes; benchmark `v_final.zip` against them
      - [ ] Output: `consults/2026-05-27-overnight-T/synthetic_finals_field/`

### Wake-up deliverable

- [ ] `consults/2026-05-27-overnight-SUMMARY.md` — one-page aggregate: per-lane status, kill-condition triggers, headline numbers, recommended morning actions, explicit "DO NOT auto-promote" reminder

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
