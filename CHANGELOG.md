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
