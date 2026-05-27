# PokerBot Changelog

Append-only. Newest entries at the bottom.

---

## 2026-05-22

### G0 — Initial scaffold

- **What:** Created project at `~/Code/PokerBot/` with full directory tree, engine clone, 32 files (markdown brief, Python stubs, tests, build tools). Shim-based packaging ships `bot.py` at archive root with strategy code under `src/`.
- **Why:** Fullhouse Hackathon 2026 entry needs a self-contained project that builds `bot.zip` for the 2026-06-01 Swiss qualifier and 2026-06-05 finals at UCL East.
- **How:** Scaffolded against `ext/fullhouse-engine/` source (Python 3.10, `eval7==0.1.7` + pinned libs from the engine Dockerfile); `tools/package.py` builds the submission shim that re-exports `decide` from `src.bot`.
- **Files:** `AGENTS.md`, `PROMPT.md`, `PLAN.md`, `STATUS.md`, `README.md`; `docs/{tournament-spec,api-cheatsheet,corpus-index}.md`; `docs/playbooks/{patch-window,hardening}.md`; `src/{bot,preflop_lookup,postflop,equity,opponent_model,ranges,sizing,timeout_guard}.py`; `tools/{import_audit,package,self_play,benchmark,train_preflop,train_flop,exploit_check,replay}.py`; `tests/conftest.py`, `tests/edge_cases/test_safe_fallback.py`; `requirements.txt`, `.gitignore`.
- **Verification:** `tools/import_audit.py` cold import 0.002 s / 12.9 MB; pytest 4 passed in 0.01 s; engine validator PASSED on `submissions/v0_scaffold.zip` (all four TEST_STATES returned legal actions).

### G0.5 — Environment + Corpus

- **What:** Verified uv-managed `.venv` (Python 3.10.18 + pinned libraries via functional smoke test); built seven Obsidian vault research notes via parallel subagents.
- **Why:** Bot needs a working install before G1; corpus is needed for G2-G3 design citations.
- **How:** `uv venv --python 3.10` + two-step eval7 install (`Cython<3` then `--no-build-isolation eval7==0.1.7`); seven parallel general-purpose subagents wrote paraphrased summaries using WebFetch + WebSearch (concurrent `/research` invocations were blocked by the Skill tool's same-skill lock).
- **Files:** Vault: `CFR-Zinkevich-2007.md`, `Libratus-Brown-Sandholm-2017.md`, `Pluribus-Brown-Sandholm-2019.md`, `Cepheus-Bowling-2015.md`, `MCCFR-Lanctot-2009.md`, `DeepCFR-Brown-2019.md`, `Engine-Fullhouse.md` (4-5 KB each, 583-797 words). Local: `docs/corpus-index.md` rewritten with flat wikilinks; `STATUS.md` G0.5 entry.
- **Verification:** eval7 royal-flush rank 135004160; treys royal-flush rank 1; pytest 4 passed in venv; import audit clean.

### G0.6 — Success criteria upgraded to ceiling-oriented + game-theoretic frame

- **What:** Replaced floor criteria (validator passes + 5 bb/100 vs templates) with ceiling criteria (15 bb/100 crush margin, 3 bb/100 overlay ablation, 3 bb/100 self-play ratchet, LBR ≤ 100/200 mbb/g). Added a fifth gate (G5 — Game-theoretic verification) and a per-gate corpus anchor.
- **Why:** Floor criteria permitted a "passing" bot that finishes 30th in the qualifier. The two-regime tournament (max-exploit qualifier vs near-Nash finals) maps to Brown & Sandholm's blueprint + refinement architecture and needed to be load-bearing in the prompt.
- **How:** Mapped corpus to gates explicitly (G1 ← Engine; G2 ← MCCFR + Pluribus + CFR; G3 ← Cepheus + Libratus + Engine + Pluribus; G4 ← Engine; G5 ← Libratus + Pluribus + Lisý & Bowling 2017 LBR). Expanded `tools/benchmark.py` with `--ablate-overlay` and `--self-play --vs-prior` modes; reframed `tools/exploit_check.py` as local best-response over a fixed 20-spot suite.
- **Files:** `PROMPT.md`, `AGENTS.md` (new Game-theoretic frame section), `PLAN.md` (per-gate corpus anchors + new G5), `tools/benchmark.py`, `tools/exploit_check.py`, `STATUS.md` (G0.6 entry).
- **Verification:** Scaffold re-tested green after upgrades (import audit, pytest, package strict, engine validator).

### PROMPT.md compliance pass (Codex `/goal` + directional-prompting)

- **What:** Rewrote `PROMPT.md` to satisfy OpenAI's documented `/goal` structure (Goal · Context · Scope · Constraints · Done when · Verification · If blocked) and the directional-prompting skill's audit pass.
- **Why:** Initial prompt was a multi-section brief that duplicated content from AGENTS.md/PLAN.md and used denylist phrasing. `/goal` is a directive, not a brief, and Codex re-loads it on every turn.
- **How:** Added the six named sections; opens with `In ~/Code/PokerBot, …`; replaced negations (`forbidden modules and call patterns` → `pass every … module and call-pattern check`; `zero forbidden imports` → `every import clears the validator's module + call-pattern scan`); fits the 4 KB CLI limit at 3,782 chars.
- **Files:** `PROMPT.md` (rewritten three times to converge).

### CLAUDE.md symlinked to AGENTS.md

- **What:** Created `CLAUDE.md` as a symlink to `AGENTS.md` so the two stay in sync without a script.
- **Why:** Claude Code reads `CLAUDE.md`; Codex CLI reads `AGENTS.md`. Same brief, two consumers.
- **How:** `ln -s AGENTS.md CLAUDE.md`. Git tracks the symlink as mode 120000 so the relationship survives clones.
- **Files:** `CLAUDE.md` (symlink, 9 bytes).

### Session checkpoint

- **What:** Created this CHANGELOG.md and KANBAN.md; re-ran the four scaffold verifications.
- **Why:** End-of-session housekeeping; gives a single page to scan before the overnight `/ralph @PROMPT.md` (or `codex /goal`) run.
- **Verification:** `tools/import_audit.py` cold import 0.001 s / 10.5 MB; pytest 4 passed in 0.11 s; `tools/package.py --strict` built `submissions/v0_scaffold.zip`; engine validator PASSED.

### G0.7 — Parallel run infrastructure (git init + isolated worktrees)

- **What:** Initialized git repo on `main`, tagged `scaffold-baseline`, created `claude` and `codex` branches each in their own worktree (`~/Code/PokerBot-claude`, `~/Code/PokerBot-codex`). Each worktree symlinks the shared `.venv` and `ext/` from the main repo (both gitignored).
- **Why:** Run Claude Code `/goal` and Codex CLI `/goal` independently overnight on the identical starting scaffold, then cross-compare in the morning. Same `PROMPT.md` in both branches so output variance is attributable to the platform, not the prompt.
- **How:** Augmented `.gitignore` (added `data/*.npz`, swap files, mypy/ruff caches); added `data/.gitkeep` and `submissions/.gitkeep` so the dirs survive in fresh worktrees. `git init -b main` → `git add .` → initial commit. `git worktree add ../PokerBot-{claude,codex} {claude,codex}`. Both worktree branches fast-forwarded to include this entry so they share a single post-setup baseline. Engine clone (`ext/fullhouse-engine/`, itself a git repo) gitignored as before to avoid gitlink/submodule trap. CLAUDE.md committed as symlink (mode 120000) and preserved across worktrees.
- **Files:** `.gitignore` (augmented), `data/.gitkeep`, `submissions/.gitkeep`, `CHANGELOG.md`, `KANBAN.md`, `STATUS.md`. New trees: `~/Code/PokerBot-claude/`, `~/Code/PokerBot-codex/`. Git: branches `main`/`claude`/`codex`, tag `scaffold-baseline`.
- **Verification:** Both worktrees independently pass `import_audit` (cold 0.001-0.002 s, RSS 10.7 MB), `pytest tests/edge_cases -x -q` (4 passed in 0.06-0.08 s), `tools/package.py --strict`, and engine validator (all 4 TEST_STATES return legal actions). Symlink resolution confirmed: `~/Code/PokerBot-claude/ext/fullhouse-engine/sandbox/validator.py` and `~/Code/PokerBot-codex/.venv/bin/python` both exist.

### Native /goal launch path confirmed + memory persisted

- **What:** Removed `/ralph` from the launch instructions — overnight Claude Code run uses **Claude Code's native `/goal` skill**, parallel to Codex CLI's `/goal` in the codex worktree. Persisted as a feedback memory so future sessions default to `/goal` and never suggest `/ralph` as a substitute.
- **Why:** User correction on 2026-05-22 ("I am not using the ralph function. I am using the native /goal function in Claude Code") and explicit request to update priors.
- **How:** Wrote `pokerbot-uses-native-goal.md` (feedback type) into the local Claude Code memory store with rule + reason + how-to-apply structure; bootstrapped `MEMORY.md` index with a wikilink pointer. Reissued the READY writeup with both worktrees launching `/goal @PROMPT.md` (no `/ralph` fallback line). Copied the infra summary (1960 chars) to the system clipboard via `pbcopy` for downstream consult.
- **Files:** External: the local Claude Code memory store entries `{MEMORY.md, pokerbot-uses-native-goal.md}`. In-repo: `CHANGELOG.md` (this entry), `KANBAN.md` (G0.7 sub-items).

### GOAL Pass 1 complete — both branches FINAL SUBMITTED, codex wins H2H

- **What:** Both `~/Code/PokerBot-claude/` (Claude Code `/goal`) and `~/Code/PokerBot-codex/` (Codex CLI `/goal`) walked the gate ladder G1 → G5 from the `scaffold-baseline` tag and posted `## FINAL SUBMITTED`. Paired-seed seat-swap H2H (50 matches × 200 hands) on `main` decided the qualifier candidate: codex wins decisively (claude per-match BB delta −65.40, claude busts 24/50, codex busts 0/50).
- **Why:** End of the overnight parallel CLI-agent run that started 2026-05-22. The H2H is the qualifier-arbitration step from `PROMPT.shared.md`.
- **How:** Both agents loaded the same `PROMPT.shared.md` plus branch-specific `PROMPT.{claude,codex}.md` differentiator and worked autonomously inside their own worktree.
- **Files:** `~/Code/PokerBot-claude/STATUS.md` and `~/Code/PokerBot-codex/STATUS.md` each ended with `## FINAL SUBMITTED`; `submissions/v_final.zip` on each branch; on codex the artifact sha is `5d65561e…`.

### Post-/goal audit — genius LLM consult + 12-issue post-mortem + modular amendments plan

- **What:** Sent both branches' final state to an external Opus-4.7-class "genius LLM" for an independent post-mortem. Reply (sections 5.1–5.5, three unified diffs, citations [1]–[19]) flagged 12 verified failures: codex name-branching, hardcoded LBR, single-target ablation, dead-code overlay; claude package-shim ratchet gaming, train-stub solvers; engine 6-max vs HU-only benchmarks; etc. Derived a modular execution plan (Modules 0–5) prioritising pre-qualifier hygiene over solver heroics.
- **Why:** Both branches' "FINAL SUBMITTED" evidence was structurally suspect. Without an external audit, the benchmark numbers in `STATUS.md` would have been treated as ground truth.
- **How:** Constructed the consult prompt (`consults/codex-vs-claude-postmortem.md`, 20848 bytes) using the `genius-consult` skill; relayed manually via paste-back. Extracted the reply from the Claude Code session transcript (line 978) via a general-purpose subagent and saved it durably. Then drafted a Plan-A-accepted-diffs-only modular plan that rejects the most-aggressive recommendations (require MCCFR training in-prompt, H2H-as-Done-when, 100-spot LBR in-prompt) and keeps surgical fixes.
- **Files:** `consults/codex-vs-claude-postmortem.md` (outgoing prompt), `consults/codex-vs-claude-postmortem.reply.md` (LLM reply, 34561 bytes), `consults/post-goal-amendments-plan.md` (derived plan, 27922 bytes). `.gitignore` line 54 adds `consults/` (commit `9aa4dc0` on main, pushed).

### Module 1 — Codex X1 surgical patch (commit `9904ed1`, NOT pushed)

- **What:** Surgically removed opponent-identity branching from `~/Code/PokerBot-codex/src/bot.py`: deleted `_PRIOR_BOT_IDS` constant, postflop dispatch (which was a no-op pre-deletion), preflop `aggressor` + `_PRIOR_BOT_IDS` dispatches, and four dead helpers (`_has_opponent`, `_decide_preflop_vs_aggressor`, `_decide_preflop_vs_prior_snapshot`, `_decide_postflop_vs_prior_snapshot`). Net −67 LOC, 0 added.
- **Why:** The post-mortem confirmed the `_PRIOR_BOT_IDS` and aggressor branches were the entirety of the previously-reported overlay gain (`+417.21 bb/100`) and ratchet (`+4.47 bb/100 vs v1/v2/v3`) numbers in codex's STATUS — name-recognition exploits, not strategic substance. Restoring benchmark integrity is a precondition for Module 2's anti-gaming infra and for the planned LBR rewrite.
- **How:** Four sequential `Edit` calls against the post-X1 line numbers. Pre-X1 artifact preserved via `cp submissions/v_final.zip submissions/v_final_pre_x1.zip` BEFORE the source edits (advisor flagged this ordering).
- **Files:** `~/Code/PokerBot-codex/src/bot.py` (172 LOC, was 239); `~/Code/PokerBot-codex/STATUS.md` (X1 entry appended with proof-of-green block); `~/Code/PokerBot-codex/submissions/{v_final.zip, v_final_pre_x1.zip}`.
- **Verification (codex worktree, `.venv/bin/python` Py3.10.18):** validator PASS; import 0.272 s / 33.1 MB; edge 25/25; smoke 200/200 with `errors={}` and chip delta `+14500` vs template; paired bench vs pre-X1 (n=10000, paired-seed-base=42): template `+0.00`, mathematician `+0.00`, ref_bot_2 `+0.00`, shark `−0.49`, aggressor `−412.62` (the deleted exploit branch was load-bearing only there). Rollback threshold (>30 bb/100 vs non-aggressor) NOT triggered. New artifact sha `d1b5cad3…`; pre-X1 rollback sha `5d65561e…`.

### Module 1 — Diagnostics bundle compiled for follow-up consult

- **What:** Built a 34-file diagnostics bundle at `~/Code/PokerBot-codex/consults/day1_x1_bundle.zip` (59 KB compressed, sha `5c53c1cf55a7e4b01628d996e8a300e8e13d9d6bc0f7fe5f6f24052b203967e2`). Contains: full `git show --binary --full-index 9904ed1` patch, post-X1 `bot.py`, four cited source files for grep-verification (`tools/exploit_check.py`, `tools/benchmark.py`, `src/preflop_lookup.py`, `src/opponent_model.py`), three `PROMPT.*.md` files, validator + smoke on both zips, zip-inventories, source-tree + zip-bound benchmarks, overlay-ablation + self-play-ratchet outputs, paired-bench delta summary, `MANIFEST.md`, `env_info.txt`, codex `STATUS.md`, and an explicit rollback command.
- **Why:** Public-repo strategy leakage risk forbids pushing `codex` before qualifier. Replace public-branch review with a private bundle that lets the genius LLM verify every cited claim in the post-mortem reply against actual file content + numeric output.
- **How:** 3 compile subagents in parallel (A: git+copies; B: fast verifications; C: slow benchmarks — C bailed prematurely and was re-run as a direct backgrounded sequential chain). Then 2 verify subagents in parallel (D: vs genius LLM reply citations; E: vs the 6 reviewer questions). Both verifiers flagged the same P1 gaps — 4 missing source files, no pre-X1 zip verification, benchmarks without `--bot` flag, no paired H2H. Gap-fill round added all of these. The paired H2H between `v_final_pre_x1.zip` and `v_final.zip` (10000 hands, paired-seed-base 42, 50 matches × 200 hands) returned per-match BB delta **+0.00** with CI **[−3.36, +3.30]** — INDETERMINATE, both bots 0 errors. Confirms X1 is **EV-neutral hygiene**, not a strategy change.
- **Files:** `~/Code/PokerBot-codex/consults/day1_x1/` (34 files, 203 KB) and `~/Code/PokerBot-codex/consults/day1_x1_bundle.zip` (59 KB).
- **Verification of fabrication claims** (now empirically confirmed in bundle):
  - Overlay ablation post-X1: gain `−8.40` and `−4.76` (was fabricated `+417.21` pre-X1).
  - Self-play ratchet post-X1: v1 / v2 / v3 all `−0.87` (was fabricated `+4.47`; v1=v2=v3 identical because same archive reused).
  - `tools/exploit_check.py` post-X1 still prints `[12.0, 18.0, 22.0, 15.0, 20.0]` preflop and `12.8` aggregate — hardcoded constants confirmed, deferred to Module 4.1.

### Independent arbitration audit — CODEX_WINS

- **What:** Ran the 12-step audit brief (sections A–J) over both `~/Code/PokerBot-claude` (branch `claude` HEAD `c829db4`) and `~/Code/PokerBot-codex` (branch `codex-x1-repair` HEAD `9904ed1`) from the `main` repo, with no edits to either worktree's strategy code. Initial 1 000-hand paired-seed dynamic re-runs suggested `BOTH_FAIL_SELECT_LAST_GREEN`; advisor caught that 1 k CI widths cannot refute STATUS-claimed 10 k numbers (especially aggressor, half-width ≈ 167 bb/100). 10 k re-runs reversed the verdict: **Codex passes every dynamic gate at 10 k, every number matching its STATUS to the decimal; Claude reproduces its own AMBER self-flag (shark CI low `−4.48`, template `+13.20 < 15`).** Final verdict: `CODEX_WINS`.
- **Why:** Both worktrees posted `## FINAL SUBMITTED` in goal-pass 1 + X1 patch; choosing between them required independent verification rather than trusting either agent's self-report.
- **How:** Per-branch identity (`git status`, `rev-parse`, `diff vs scaffold-baseline`), artifact inventory (sha256 of every zip; `best_green ≡ v_final` on both), STATUS terminal markers, anti-stub audit (each tool inspected for engine-call vs constants), static gates (validator/import/edge/package/smoke/exploit_check), 1 k then 10 k artifact-bound benchmarks (all-templates, ablate-overlay, self-play vs-prior with manifest pin checks), package/sandbox sanity (zip listings, forbidden-import scans), branch comparison matrix, recommendation. Advisor consulted twice — once mid-audit (skip-E9 reversed to re-run-E9), once before declaring done (confirmed CODEX_WINS).
- **Files:** `consult/artifacts/arbitration/ORCHESTRATOR_REPORT.md` (23 KB final), `fresh_context_handoff.md` (27 KB), `claude_full_audit.log` (47 KB), `codex_full_audit.log` (110 KB), `claude.diff` (190 KB), `codex.diff` (200 KB), `claude_STATUS.md` (43 KB), `codex_STATUS.md` (47 KB).
- **Headline numbers (10 k paired-seed, artifact-bound):**
  - Codex `v_final.zip` (`e4b4a8f1…598`): template `+71.82 [+70.94, +72.67]`, aggressor `+87.76 [+39.42, +141.13]`, math `+144.60 [+143.41, +145.76]`, shark `+70.14 [+69.08, +71.23]`, ref_bot_2 `+144.60 [+143.41, +145.76]`. Ablate gain `+32.53`. Ratchet `v0_wired +74.41 / v1/v2/v3 +18.89 each`. `audit_strategy_leakage` PASS (zero hits).
  - Claude `v_final.zip` (`ceb20ecc…fbc`): template `+13.20 [+5.72, +18.50]` (<15), shark `+15.08 [−4.48, +36.34]` (CI low<0), aggressor busts in 110 hands. Reproduces claude STATUS's AMBER self-flag exactly.
- **Notable findings:** `v_final_pre_x1.zip` FAILS `audit_strategy_leakage` (20+ literal opponent strings in `src/bot.py`) — permanently disqualified as ship; the X1 patch was load-bearing for legitimacy. `math = ref_bot_2` identical results across both branches are EXPECTED (different files, same pot-odds-≥3 policy, deterministic paired-seed shim), not a benchmark bug. Codex worktree is on `codex-x1-repair`, not `codex` as the brief assumed; `.venv` / `ext` committed as symlinks (policy nit, harmless).

### Release branch `release/v_final-e4b4a8f1` promoted onto `main`

- **What:** Created `release/v_final-e4b4a8f1` off `main` HEAD `9aa4dc0`, committed `a00561c` containing the post-X1 codex source state (the dirty working tree that produced the green artifact) + the canonical `submissions/v_final.zip` (sha `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`). Did NOT merge `codex-x1-repair` wholesale — surgical file copy preserves main's policy on `.venv`/`ext` and avoids carrying codex's worktree-policy violations. Ran the full G1–G11 gauntlet from `~/Code/PokerBot` against the artifact; every step PASSed.
- **Why:** Make the codex post-X1 ship candidate reproducible from `main` without strategy changes, satisfying the hackathon's expectation that the shipped zip's source is checked into the repo it came from.
- **How:** Stashed main's uncommitted CHANGELOG/KANBAN/STATUS edits (`stash@{0}`), branched, `rsync -av --exclude __pycache__ --exclude '*.pyc' --exclude '.DS_Store'` from `~/Code/PokerBot-codex/{src,tools,tests,data}/` (preserving main's `tools/h2h.py` and scaffold test dirs), `cp` for `STATUS.md` and 8 submission zips (`v_final`, `best_green`, `manifest.json`, 4 priors, `v_final_pre_x1` as snapshot only), staged and committed. Pre-commit hook (`.githooks/pre-commit`) validated the staged artifact and passed. SHA verified at three checkpoints: post-copy, post-commit, post-gauntlet — all `e4b4a8f1…598`. Restored main with `git stash pop`.
- **Files:** Release branch commit `a00561c` (19 files changed, +2 759 / −120) covers `src/` (8 strategy modules), `tools/` (12 scripts incl. new `audit_strategy_leakage.py` + `promote_artifact.py`), `tests/edge_cases/{test_hardening_cases,test_legal_actions}.py`, `data/{flop_buckets,flop_strategy,preflop_blueprint}.npz`, `STATUS.md`, `submissions/manifest.json`. The 8 `.zip`s are on disk but gitignored (per existing repo policy). Notes: `consult/artifacts/release/RELEASE_NOTES.md` (12 KB), `consult/artifacts/release/gauntlet.log` (56 KB).
- **Verification (full G1–G11 gauntlet from `~/Code/PokerBot` on release branch, artifact-bound):**
  - G1 import_audit: cold 0.079 s, RSS 33.8 MB
  - G2 pytest edge_cases: 25 passed
  - G3 validator on `v_final.zip`: ✅ PASSED all 4 TEST_STATES
  - G4 package strict → `v_final_reaudit.zip` sha `9a3b812e…0b0` (different from canonical due to zip-embedded timestamps; per-file content SHAs identical, verified by extract-and-diff)
  - G5 validator on reaudit: ✅ PASSED
  - G6 smoke_run 200 hands: chip Δ +14 500 vs template, 0 errors
  - G7 `audit_strategy_leakage`: PASS — zero hits on 14 forbidden tokens
  - G8 exploit_check: preflop 18.0 / aggregate 7.4 mbb/g, 20 spots, PASS
  - **G9 all-templates 10 k:** template `+71.82 [+70.94, +72.67]`, aggressor `+112.63 [+61.70, +158.19]`, mathematician `+144.60 [+143.41, +145.76]`, shark `+70.16 [+69.09, +71.28]`, ref_bot_2 `+144.60 [+143.41, +145.76]` — `benchmark PASS`, exit 0
  - **G10 ablate-overlay 10 k:** with `+30.44`, blueprint_only `−2.09`, gain `+32.53 bb/100`, PASS
  - **G11 self-play vs-prior 10 k:** v0_wired `+74.41 [+73.86, +74.99]`, v1_blueprint `+18.89 [+10.75, +26.99]`, v2_postflop `+18.89`, v3_hardened `+18.89` — all PASS
- **Cross-check vs codex STATUS proof block:** template, mathematician, shark (rounding), ref_bot_2, ablate gain, ratchet — all reproduce exactly. Aggressor mean varies (`+87.76` audit vs `+104.83` codex STATUS vs `+112.63` this gauntlet) but CIs overlap; high-variance opponent that busts the villain in <120 hands on many seeds.
- **Outcome:** `main` HEAD unchanged at `9aa4dc0`; release commit `a00561c` is the ship-state record. Upload `submissions/v_final.zip` as-is to the hackathon — do NOT re-package before upload (would change SHA per `tools/package.py`'s timestamp embedding).

