# PokerBot — Live Status

Append-only audit log. Each gate appends a section with: id, GREEN/AMBER/RED, exact numeric evidence, files changed, next action.

---

## G0 — Scaffold complete

**Status:** GREEN
**Timestamp:** 2026-05-22

**Evidence (verified 2026-05-22):**
- Directory tree created under `~/Code/PokerBot/{docs/playbooks,src,data,tests/{unit,integration,edge_cases,property},tools,ext,submissions}`.
- `ext/fullhouse-engine/` cloned from `https://github.com/uzlez/fullhouse-engine` (Python 3.10 sandbox, `eval7==0.1.7`, `numpy==1.26.4`, `scipy==1.13.0`, `treys==0.1.8`, `scikit-learn==1.5.2` — pinned in `requirements.txt`).
- `AGENTS.md`, `PROMPT.md`, `PLAN.md`, `STATUS.md`, `README.md` present.
- `docs/tournament-spec.md`, `docs/api-cheatsheet.md`, `docs/corpus-index.md`, `docs/playbooks/{hardening,patch-window}.md` present.
- `src/{__init__,bot,preflop_lookup,postflop,equity,opponent_model,ranges,sizing,timeout_guard}.py` stubs present; `bot.py` returns a legal action for every input shape.
- `tools/{import_audit,package}.py` functional; `tools/{self_play,benchmark,train_preflop,train_flop,exploit_check,replay}.py` stubs present.
- `tests/conftest.py` and `tests/edge_cases/test_safe_fallback.py` cover the safe-fallback contract using engine-shaped game states.

**Verification run (2026-05-22):**
- `python tools/import_audit.py` → cold import 0.002 s, RSS 12.9 MB (limits 1.5 s / 400 MB), zero forbidden imports.
- `pytest tests/edge_cases -x -q` → 4 passed in 0.01 s.
- `python tools/package.py --output submissions/v0_scaffold.zip --strict` → built 7,239 B archive (bot.py shim + 9 src files, no data yet).
- `python ext/fullhouse-engine/sandbox/validator.py submissions/v0_scaffold.zip` → ✅ PASSED. All four validator TEST_STATES (preflop_call_or_fold, postflop_can_check, river_facing_large_bet, short_stack_all_in_decision) returned legal actions in 0.000 s each.

**Open items:**
- Corpus build (`/research` + `/obsidian`) is user-invocable — not run during G0. Run before G2 if strategic decisions need backing.
- Hackathon registration to confirm (registered account).
- `ref_bot_2` exists in `ext/fullhouse-engine/bots/` but is undocumented; treat as a wildcard during G3 benchmarks.

**Next action:** Execute G1 — wire `src/bot.py` and `src/timeout_guard.py`, build `tools/self_play.py`, run 100-hand smoke test vs `template`, build `submissions/v0_wired.zip`, run engine validator.

---

## G0.5 — Environment + Corpus

**Status:** GREEN
**Timestamp:** 2026-05-22

**Environment (uv venv):**
- `.venv/` exists with Python 3.10.18.
- Pinned libraries installed: `numpy==1.26.4`, `scipy==1.13.0`, `scikit-learn==1.5.2` (verified via `pip show`); `eval7==0.1.7` and `treys==0.1.8` import cleanly and pass a royal-flush evaluation smoke test (eval7 rank 135004160; treys rank 1).
- `.venv/bin/python -m pytest tests/edge_cases -x -q` → 4 passed in 0.37 s.
- `.venv/bin/python tools/import_audit.py` → cold import 0.000 s, RSS 11.0 MB, zero forbidden imports.

**Corpus (vault notes):**
Built 2026-05-22 via 7 parallel subagents writing into the external Obsidian vault under `Agentic/05 Research/PokerBot/`:
- `CFR-Zinkevich-2007.md` (4768 B, 647 words)
- `Libratus-Brown-Sandholm-2017.md` (4220 B, 619 words)
- `Pluribus-Brown-Sandholm-2019.md` (4305 B, 583 words)
- `Cepheus-Bowling-2015.md` (4665 B, 669 words)
- `MCCFR-Lanctot-2009.md` (4919 B, 682 words)
- `DeepCFR-Brown-2019.md` (4234 B, 642 words)
- `Engine-Fullhouse.md` (5572 B, 797 words)
`docs/corpus-index.md` wikilinks updated to the flat note names.

**Notes:**
- Subagents used WebFetch + WebSearch rather than the `/research` skill — concurrent slash-command invocations are blocked. Notes are paraphrased summaries (no verbatim paper content).
- `Engine-Fullhouse.md` characterises each of the five reference bots (`template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2`) with an exploit-overlay angle — directly feeds G3 targeting.
- Billings opponent-modeling note from the original plan was dropped; the engine note's per-bot exploit holes cover the same ground.

**Next action:** Same as G0 — start G1.

---

## G0.6 — Success criteria upgraded to ceiling-oriented + game-theoretic frame

**Status:** GREEN (planning artifact, not a code change)
**Timestamp:** 2026-05-22

**What changed and why:**
Original success criteria were floor-oriented (validator passes, beats weak templates by 5 bb/100, no crashes). They permitted a "passing" bot that finishes 30th in the qualifier — i.e., not winning. Rewritten to ceiling-oriented criteria that map directly to the corpus.

**Upgraded files:**
- `PROMPT.md` — eight ceiling criteria: crush margin ≥ 15 bb/100 vs each reference bot; overlay ablation ≥ 3 bb/100; self-play ratchet ≥ 3 bb/100 per prior gate; LBR ≤ 100/200 mbb/g; plus floor criteria (validator, edge tests, import audit, STATUS protocol with corpus citations).
- `AGENTS.md` — new "Game-theoretic frame" section: blueprint (Nash approximation on abstracted game) + bounded overlay (best-response refinement); abstraction as the leverage point; exploitability as the safety metric; explicit list of corpus techniques dropped (Libratus subgame solving, Deep CFR) with reasons.
- `PLAN.md` — each gate now names its **corpus anchor**; G2/G3 exit thresholds raised from ≥ 5 to ≥ 15 bb/100; **new G5 (Game-theoretic verification)** covers ablation + self-play ratchet + LBR.
- `tools/benchmark.py` — argparse flags `--ablate-overlay`, `--self-play --vs-prior`; `--all-templates` now targets all five reference bots (ref_bot_2 included).
- `tools/exploit_check.py` — reframed as LBR (Lisý & Bowling 2017) over a 20-spot suite; thresholds `--max-preflop-mbb 100`, `--max-aggregate-mbb 200`.

**Corpus thread (each gate → its driving paper):**
- G1 wiring ← [[Engine-Fullhouse]]
- G2 preflop blueprint ← [[MCCFR-Lanctot-2009]] (external sampling) + [[Pluribus-Brown-Sandholm-2019]] (blueprint shape + sizing tree) + [[CFR-Zinkevich-2007]] (foundation)
- G3 postflop + overlay ← [[Cepheus-Bowling-2015]] (CFR+, bucketing) + [[Libratus-Brown-Sandholm-2017]] (blueprint+refinement pattern) + [[Engine-Fullhouse]] (per-bot exploit priors)
- G4 hardening ← [[Engine-Fullhouse]] (pitfalls list)
- G5 game-theoretic verification ← [[Libratus-Brown-Sandholm-2017]] + [[Pluribus-Brown-Sandholm-2019]] + Lisý & Bowling 2017 (LBR, inline ref to arXiv:1612.07547)

**Verification (planning artifact passes scaffold checks):**
- `python tools/import_audit.py` still GREEN (no code paths changed, only tool argparse).
- `python tools/package.py --output submissions/v0_scaffold.zip --strict` rebuilds clean.
- `python ext/fullhouse-engine/sandbox/validator.py submissions/v0_scaffold.zip` still PASSED.

**Next action:** Start G1 — the architectural commitment is now load-bearing; gates execute against ceiling criteria.

---

## G0.7 — Parallel run infrastructure (git init + isolated worktrees)

**Status:** GREEN
**Timestamp:** 2026-05-22

**What changed:**
- `git init -b main` in `~/Code/PokerBot`. Initial commit `scaffold: G0-G0.6 (initial)` (35 files, 1 symlink).
- Tag `scaffold-baseline` marks the pre-divergence commit; both `claude` and `codex` branches forked from it.
- `git worktree add ../PokerBot-claude claude` and `git worktree add ../PokerBot-codex codex`. Each is a fully-functional working tree on its own branch sharing the parent's `.git` dir.
- `.venv/` and `ext/fullhouse-engine/` (both gitignored) symlinked from `~/Code/PokerBot/` into each worktree. Single source of truth; no duplication.
- `.gitignore` augmented (data/*.npz, *.swp, .mypy_cache/, .ruff_cache/); `data/.gitkeep` + `submissions/.gitkeep` added so the dirs persist in worktrees.

**Layout:**
```
~/Code/PokerBot/         [main]   ← canonical, hosts shared .venv + ext/
~/Code/PokerBot-claude/  [claude] ← target for Claude Code /goal run
~/Code/PokerBot-codex/   [codex]  ← target for Codex CLI /goal run
```

**Verification (run 2026-05-22, both worktrees):**
- `import_audit.py` → cold import 0.001-0.002 s, RSS 10.7 MB (both GREEN).
- `pytest tests/edge_cases -x -q` → 4 passed in 0.06-0.08 s (both GREEN).
- `tools/package.py --strict` → `submissions/v0_scaffold.zip` built in both.
- `validator.py submissions/v0_scaffold.zip` → ✅ PASSED on all 4 TEST_STATES in both.
- Symlink resolution: `~/Code/PokerBot-claude/ext/fullhouse-engine/sandbox/validator.py` and `~/Code/PokerBot-codex/.venv/bin/python` both reachable.

**Why this matters:**
- Two independent overnight `/goal` runs share the identical starting scaffold; output variance is attributable to platform (Claude Code vs Codex CLI), not to prompt or scaffold drift.
- Worktrees share `.git`, so commits in one branch are instantly visible from any other (good for morning comparison: `git diff scaffold-baseline..claude` vs `..codex`).
- Engine clone (`ext/fullhouse-engine/`, itself a git repo) is gitignored — avoids the gitlink/submodule trap and keeps it as a pure read-only reference.

**Next action:** Launch `/goal @PROMPT.md` in `~/Code/PokerBot-claude` (Claude Code) and in `~/Code/PokerBot-codex` (Codex CLI). Both run concurrently. Compare gate progress, code volume, benchmarks, and cross-play in the morning.

---

## G0.8 — Pre-launch hardening: differentiated prompts, pre-commit hook, smoke run, paired-seed benchmarks

**Status:** GREEN (infrastructure; refines G0.7)
**Timestamp:** 2026-05-22

**What changed:**
- `PROMPT.md` → `PROMPT.shared.md` (rename via `git mv`, preserves history). Added invariants: paired-seed benchmark for acceptance, smoke run before claiming gate green, `submissions/best_green.zip` preservation, compact proof-of-green format that survives `/goal` context summarisation.
- `PROMPT.claude.md` (new, ~40 lines): claude branch search bias — harness, hardening, exploit overlay, tournament tooling (P0..P5). Differentiator only; references `PROMPT.shared.md` for the contract.
- `PROMPT.codex.md` (new, ~40 lines): codex branch search bias — compact lookup tables, parameter sweeps, training pipelines, benchmark automation (P0..P5). Differentiator only.
- `AGENTS.md` — appended sections: **Artifact policy**, **Solver policy**, **Worktree policy**, **Benchmark variance policy**, **Patch-window policy**. Added `tools/smoke_run.py` to Build & verify commands. `CLAUDE.md` inherits via symlink.
- `.githooks/pre-commit` (new, executable): when a commit stages `submissions/`, runs `import_audit + edge_cases + validator(best_green.zip, v_final.zip)`; refuses on failure. `FORCE_COMMIT=1` overrides for explicit rollbacks. Activated via `git config core.hooksPath .githooks` (one config, applies to both worktrees via shared `.git`).
- `tools/smoke_run.py` (new): wraps `USE_DOCKER=true ext/fullhouse-engine/sandbox/match.py` against a reference bot for N hands inside the real container (`--network none --memory 768m --cpus 0.5 --read-only --no-new-privileges --user 1000:1000`). Builds `fullhouse-sandbox:latest` if missing. Catches runtime issues (timeout, OOM, slow imports) the AST-only validator cannot detect.
- `tools/benchmark.py` — docstring expanded with variance / paired-seed policy; `--paired-seed-base` and `--paired-seed-count` flags added (implementer wires the body during G2/G3).
- `submissions/best_green.zip` — bootstrapped locally from `v0_scaffold.zip` (already validator-PASSED in G0). Gitignored by design; agents regenerate.

**Why this matters (refines G0.7's launch infrastructure):**
- Identical prompts to both agents waste their differentiation; the split biases each agent's search toward its comparative advantage without weakening the shared contract.
- The validator is AST + size only; it does not run the bot. A bot can pass the validator and still timeout / OOM / crash in real matches. `smoke_run` closes that gap.
- At 10k hands, bb/100 variance ~20 bb/100. Selecting between branches on a single 10k run is selecting noise. Paired seeds drop variance ~5-10×.
- `/goal` evaluator reads only the chat transcript; auto-summarisation can erase STATUS.md evidence. The compact proof-of-green block survives summarisation.
- best_green.zip preservation is the single most important invariant for overnight runs (avoids overwriting good work with broken work).

**Verification (2026-05-22, in `~/Code/PokerBot/`):**
- `.venv/bin/python tools/import_audit.py` → cold import 0.000 s, RSS 10.2 MB. PASS.
- `.venv/bin/python -m pytest tests/edge_cases -x --quiet` → 4 passed in 0.07 s. PASS.
- `.venv/bin/python ext/fullhouse-engine/sandbox/validator.py submissions/best_green.zip` → ✅ PASSED on all 4 TEST_STATES.
- `git config --get core.hooksPath` → `.githooks`.
- `.githooks/pre-commit` mode 0755.

**Open items:**
- Worktrees inherit these files via `git merge main` (fast-forward) once this commit lands. Bootstrap their `submissions/best_green.zip` after merge.
- Both branches still need `findings/` directory created lazily by the first agent to write a finding.
- `tools/promote_best_green.py` (a verified-promotion helper) deferred — agents currently follow the prose protocol in AGENTS.md → Artifact policy.

**Next action:** Commit on `main`, fast-forward `claude` and `codex` branches, copy `best_green.zip` into each worktree, then launch `/goal` per branch-specific prompt.

---
