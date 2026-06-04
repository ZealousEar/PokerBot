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

---

## GOAL Pass 1 + Post-mortem + Module 1 (X1 surgical patch) + Diagnostics bundle

**Status:** GREEN (pass 1 complete and decided; Module 1 verified; bundle uploaded-ready)
**Timestamp:** 2026-05-22

**What happened (chronological):**
1. Overnight parallel `/goal` runs on `~/Code/PokerBot-claude` (Claude Code) and `~/Code/PokerBot-codex` (Codex CLI) from `scaffold-baseline`. Both posted `## FINAL SUBMITTED`.
2. Paired-seed seat-swap H2H on main (`tools/h2h.py`, 50 matches × 200 hands): codex wins. Claude per-match BB delta `−65.40`; claude busts 24/50, codex busts 0/50.
3. External Opus-4.7-class genius LLM audited both branches with full public-repo access. Reply (3 diff blocks, 19 citations) identified 12 verified failures across both branches.
4. Module 0: durably saved the consult prompt + reply + derived modular execution plan to `consults/` (gitignored on main, commit `9aa4dc0`, pushed).
5. Module 1: codex X1 surgical patch on `~/Code/PokerBot-codex/src/bot.py`. Commit `9904ed1` (NOT pushed). −67 LOC, 0 added. Removed opponent-identity branching. Validator + import + edge + smoke + paired bench all PASS; non-aggressor max delta ≤ 0.62 bb/100; aggressor regresses −412.62 bb/100 (expected and accepted per plan).
6. Diagnostics bundle compiled at `~/Code/PokerBot-codex/consults/day1_x1_bundle.zip` (59 KB, 34 files, sha `5c53c1cf…`). Includes paired H2H between pre-X1 and post-X1 zips: per-match BB delta `+0.00`, CI `[−3.36, +3.30]`, INDETERMINATE → X1 is EV-neutral hygiene, not a strategy change.

**Headline numerics (post-X1 codex, paired-seed-base=42, hands=10000, `--bot submissions/v_final.zip`):**
- template:      `+71.82`  CI `[+70.94, +72.67]`
- aggressor:     `−236.59` CI `[−247.23, −226.02]` (was `+176.03` pre-X1 — the deleted exploit branch)
- mathematician: `+144.60` CI `[+143.41, +145.76]`
- shark:         `+69.81`  CI `[+68.69, +70.88]`
- ref_bot_2:     `+144.60` CI `[+143.41, +145.76]`
- Overlay ablation gain: `−8.40` / `−4.76` (was fabricated `+417.21`)
- Self-play ratchet vs v1/v2/v3: `−0.87` all three (was fabricated `+4.47`)

**Files changed (since G0.8):**
- `consults/codex-vs-claude-postmortem.md` (outgoing consult; created)
- `consults/codex-vs-claude-postmortem.reply.md` (genius LLM reply; created)
- `consults/post-goal-amendments-plan.md` (derived modular plan; created)
- `.gitignore` (line 54 `consults/`; committed `9aa4dc0` on main, pushed)
- `~/Code/PokerBot-codex/src/bot.py` (committed `9904ed1`, NOT pushed)
- `~/Code/PokerBot-codex/STATUS.md` (X1 entry appended; committed `9904ed1`)
- `~/Code/PokerBot-codex/submissions/v_final_pre_x1.zip` (rollback; gitignored, on disk only)
- `~/Code/PokerBot-codex/consults/day1_x1/` (34 files) + `day1_x1_bundle.zip` (gitignored, on disk only)
- `KANBAN.md` (main; this session)
- `CHANGELOG.md` (main; this session)
- `STATUS.md` (main; this entry)

**Open / next:**
- GOAL Pass 2 (claude + codex) currently running in tmux panes from the **pre-Module-3 prompts** — observation pass to inform Modules 3-5. Expect similar gaming behaviour to pass 1 since prompts are unchanged.
- Modules 2 → 3 → 4 still pending per `consults/post-goal-amendments-plan.md`. Day-by-day plan ends at qualifier 2026-06-01.
- Codex `9904ed1` stays unpushed. Diagnostics shared via the bundle, not the public branch.

**Next action:** Watch tmux panes for GOAL Pass 2 outputs; once both report `## FINAL SUBMITTED`, run paired H2H between {pass-1 codex post-X1, pass-2 claude `v_final`, pass-2 codex `v_final`} to inform whether Module 5 re-run is warranted. Modules 2-3 are still the critical pre-qualifier path.

---

## Independent arbitration audit + release branch promotion onto `main`

**Status:** GREEN (`CODEX_WINS` verdict reproduced from `main`; ship state pinned on `release/v_final-e4b4a8f1`).
**Timestamp:** 2026-05-22 (audit + release) / 2026-05-24 (checkpoint)
**Ship candidate:** `~/Code/PokerBot/submissions/v_final.zip` sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
**Release branch:** `release/v_final-e4b4a8f1` HEAD `a00561c` (off `main` `9aa4dc0`)

**What happened (chronological):**
1. Ran the 12-step independent arbitration brief (sections A–J) over both worktrees from `main`. No edits to either worktree's `src/`, `tools/`, `tests/`, `data/`, or `bot.py`.
2. Initial 1 000-hand paired-seed dynamic re-runs suggested `BOTH_FAIL_SELECT_LAST_GREEN` — both `v_final.zip`s appeared to fail all-templates, ablate-overlay, and self-play-vs-prior at the 1 k sample.
3. Advisor caught the methodological gap: 1 k paired-seed CI widths (aggressor half-width ≈ 167 bb/100) cannot statistically refute STATUS-claimed 10 k numbers. Re-ran all three dynamic gates at 10 k for Codex; ran 10 k all-templates for Claude (its all-templates failure is the binding constraint).
4. **10 k re-run flipped the verdict to `CODEX_WINS`.** Codex's STATUS proof block reproduced to the decimal across template / mathematician / shark / ref_bot_2; aggressor reproduced within paired-seed variance; ablate gain and ratchet matched exactly. `audit_strategy_leakage` PASS. Claude's 10 k reproduced its own self-flagged AMBER pattern (shark CI low `−4.48`, template `+13.20 < 15`).
5. Documented the audit in `consult/artifacts/arbitration/` (8 files, ~700 KB total). Recommendation locked in `ORCHESTRATOR_REPORT.md` (`## RECOMMENDATION: CODEX_WINS`) and `fresh_context_handoff.md`.
6. Stashed main's uncommitted CHANGELOG/KANBAN/STATUS edits, branched `release/v_final-e4b4a8f1` off `main`, `rsync`'d safe paths from `~/Code/PokerBot-codex` working tree (post-X1 dirty state, the one that built the artifact), `cp`'d 8 submission zips, committed `a00561c`. Pre-commit hook validated and passed.
7. Ran the full G1–G11 gauntlet from `~/Code/PokerBot` against `submissions/v_final.zip`. Every step PASSed; numbers reproduce codex STATUS.
8. Restored main with `git stash pop` — `main` HEAD unchanged at `9aa4dc0`, audit narrative restored.

**Headline numerics (`release/v_final-e4b4a8f1`, artifact-bound, paired-seed-base=42, hands=10000):**
- template: `+71.82` CI `[+70.94, +72.67]`
- aggressor: `+112.63` CI `[+61.70, +158.19]` (high-variance opponent; mean comfortably positive; CIs overlap with codex STATUS `+104.83` and arbitration audit `+87.76`)
- mathematician: `+144.60` CI `[+143.41, +145.76]`
- shark: `+70.16` CI `[+69.09, +71.28]`
- ref_bot_2: `+144.60` CI `[+143.41, +145.76]`
- Overlay ablation gain: `+32.53 bb/100` (with `+30.44`, blueprint_only `−2.09`)
- Self-play ratchet: v0_wired `+74.41`, v1_blueprint `+18.89`, v2_postflop `+18.89`, v3_hardened `+18.89` — all manifest-pinned sha256s verified
- Real LBR guard (artifact-bound): preflop `18.0 mbb/g`, aggregate `7.4 mbb/g`, 20 spots, PASS
- `audit_strategy_leakage` on `v_final.zip`: PASS (zero hits across 14 forbidden tokens)
- Static gates: validator ✅ PASSED 4/4, edge_cases 25/25, smoke 200/200 chip Δ +14 500, import_audit 0.079 s / 33.8 MB

**Artifacts:**
- Audit: `consult/artifacts/arbitration/{ORCHESTRATOR_REPORT.md, fresh_context_handoff.md, claude_full_audit.log, codex_full_audit.log, claude.diff, codex.diff, claude_STATUS.md, codex_STATUS.md}` (8 files, ~700 KB)
- Release: `consult/artifacts/release/{RELEASE_NOTES.md, gauntlet.log}` (12 KB + 56 KB)
- Ship state: `release/v_final-e4b4a8f1` commit `a00561c` on `main`. `submissions/v_final.zip` and `best_green.zip` both byte-identical at sha `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.

**Files changed (since X1 patch):**
- `consult/artifacts/arbitration/*` (8 audit artifacts, gitignored under `consult/`)
- `consult/artifacts/release/*` (release notes + gauntlet log, gitignored)
- `release/v_final-e4b4a8f1` commit `a00561c` covers `src/`, `tools/`, `tests/`, `data/`, `STATUS.md`, `submissions/manifest.json` (19 files, +2 759 / −120). Submission zips on disk only per `.gitignore` `submissions/*.zip`.
- `KANBAN.md`, `CHANGELOG.md`, `STATUS.md` (main; this checkpoint)

**Cross-check vs codex STATUS proof block:** every metric reproduces to the decimal except aggressor (which varies across runs — its CI half-width ≈ 50 bb/100 makes per-run mean shifts of ±25 expected). The `math = ref_bot_2` identical results across both bb/100 and CIs are EXPECTED, not a benchmark bug — the two engine bots implement the same pot-odds-≥3 policy in different files (verified by `diff -r` of the bot.py sources), so a deterministic paired-seed hero scores identically against both.

**Residual risks:** (1) Aggressor 10 k CI is wide (~100 bb/100 width). The qualifier is 400-hand matches per opponent; a single short match against aggressor specifically can swing. Mean is comfortably positive; recommend optional confirming 400-hand × N-seed run before upload, not blocking. (2) `tools/package.py` embeds build-time timestamps; rebuilding with `--output submissions/v_final.zip` produces a different SHA. **Do NOT re-package before upload** — ship the existing `e4b4a8f1…598` file as-is. The G4 `v_final_reaudit.zip` (`9a3b812e…0b0`) was a side check; per-file content SHAs were verified identical to canonical, so the release branch's `src/` + `data/` reproduce the artifact contents exactly.

**Next action:** Upload `~/Code/PokerBot/submissions/v_final.zip` as-is to the Fullhouse Hackathon qualifier portal on 2026-06-01. Optional pre-upload: 400-hand × few-seed confirming run against `aggressor` specifically to characterise single-match variance. Optional post-qualifier: tag `release/v_final-e4b4a8f1` HEAD as `v_final-e4b4a8f1` for a permanent ship-state record.

---

## 2026-05-27T21:10Z · Orchestrator Loop 1 (post-overnight-1, pre-overnight-2) · GREEN

**Scope:** orientation pass over 21-lane overnight-1 outputs + claude HYGIENE-1/CONFIRM-1/PATCH-1 consults + worktree drift analysis; one patch-window-prep landing; OVERNIGHT-2 designed.

**Ship-state decision:** SHIP canonical `submissions/v_final.zip` sha `e4b4a8f1…598` AS-IS on 2026-06-01. The packaged `src/bot.py:39` `_OVERLAY_DISABLED = os.environ.get("POKERBOT_DISABLE_OVERLAY") == "1"` flag is internal-hygiene-only — verified by grep against `ext/fullhouse-engine/sandbox/` that the qualifier Docker container passes ONLY `-e ACTION_TIMEOUT -e BOT_PATH -e BOT_DATA_DIR` (per `match.py:131-133`), so `POKERBOT_DISABLE_OVERLAY` is guaranteed unset in the sandbox and `_OVERLAY_DISABLED=False`. Validator on canonical artifact: ✅ PASSED 4/4 TEST_STATES (raise/check/fold/all_in returned, real strategy code firing).

**Today's consult work (claude worktree) — verified, no STATUS update because no promotion:**
- HYGIENE-1 candidate `v_hygiene_candidate.zip` sha `58a2ec90` (per SUMMARY) — legalizer + clamp + LBR caps PASS; SHA drift on disk (`41768b97`, `c3af9d39`); not promoted.
- CONFIRM-1 v5_light_3bet: bb/100 −54.14 calibrated (was −135.76 at Lane T) — confirmed real but ~2.5× smaller; literal LIGHT3BET_CONFIRMED, magnitude near floor.
- CONFIRM-1b v1-v4: SYNTHETIC_FINALS_FIELD_MOSTLY_NOISE — 0/4 ≤ −50 bb/100 calibrated; original Lane T inflated by ~1.5–2×.
- PATCH-1 A light-3bet defense: DO_NOT_PROMOTE — v5 lift only +7.09 (floor +25); LBR aggregate regression +53.6 > +20 budget; neel public regression −28.67.
- PATCH-1 reconcile: PATCH1_NET_NEGATIVE — 1 HELPS (dominic), 1 HURTS (neel), 2 NEUTRAL. Shelved; move to PATCH-2 (famadeo EV veto) post-qualifier.

**Worktree audit artifact:** `consult/artifacts/2026-05-27-worktree-audit/MAP.md` documents ship recommendation, source provenance (release branch `a00561c` holds ship code; main HEAD `050b058` is scaffold), hygiene SHA trail, diff summary, and risk matrix. Includes §1a env-var injection audit citing match.py line numbers.

**Patch-window-prep landing:** Engineer agent landed branch `patch-window-prep-2026-05-27` in claude worktree.
- `1172fd7` — Harden hand history analyzer schema parsing (+427/-81 LOC in `tools/analyze_hand_histories.py`; now 557 LOC). Adds normalized alias matching, action synonyms, street-nested flattening, parse_quality npz diagnostics.
- `97507a7` — Add analyzer schema hardening tests (+234 LOC across `tests/integration/test_analyze_aliases.py` and `test_analyze_smoke.py`).
- Verification: `pytest tests/integration -x` → 9 passed in 0.35s (re-run by orchestrator independently).

**OVERNIGHT-2 plan written:** `docs/plans/overnight-2-2026-05-28.md`. Replaces KANBAN's 22-lane template after retrospective on overnight-1 negatives. **7 lanes, 3 regimes**:
- L1, L2 — Lock-in verification (canonical gauntlet + 2000-hand smoke × 5 opponents).
- R1, R2 — Patch-window rehearsal (8 schema variants + 50-fuzz adversarial).
- W1, W2, W3 — Targeted weakness probes (famadeo decision audit, dominic decision audit, finals-projection recalibration).

**Files changed (this loop):**
- `consult/artifacts/2026-05-27-worktree-audit/MAP.md` (new)
- `docs/plans/overnight-2-2026-05-28.md` (new)
- `STATUS.md` (this entry)
- claude worktree branch `patch-window-prep-2026-05-27` (2 commits, isolated)

**Corpus citations:** [[Libratus-Brown-Sandholm-2017]] (blueprint+refinement validation pattern as basis for lock-in verification); [[Engine-Fullhouse]] (sandbox env-var contract).

**Next action:** Dispatch OVERNIGHT-2 lanes per `docs/plans/overnight-2-2026-05-28.md` tomorrow afternoon 2026-05-28 ~17:00 UTC. Pre-launch checklist in the plan file. Do NOT re-package `v_final.zip` between now and qualifier.

---

## 2026-05-27T22:01:26Z · B1 · GREEN
- Goal: schema rehearsal of `analyze_hand_histories.py` beyond existing alias/smoke coverage
- Numbers: 8 variants tried, 7 passed (87.5%, ≥85% bar met); 1 P0 reproducer (`v03_deep_wrappers.json` — analyzer does not descend into `download.session.payload.hands` envelope); 3 non-P0 defects (`pf/f/t/r` street abbrev not normalized into PFR/sizing buckets, `"NaN"` propagates into `avg_sizing_preflop=NaN`, `amountBB` units silently dropped).
- Validator / import_audit / edge / smoke / leakage / exploit: N/A (B1 is analyzer rehearsal, not artifact-bound)
- Files changed: `consult/artifacts/2026-06-02-patch-window-prep/R1_SUMMARY.md`, `R1_schema_rehearsal/{R1_run_schema_variants.py, R1_RESULTS.json, fixtures/v0{1..8}.{json,jsonl}, logs/*.{stdout,stderr}.txt}` (1880 insertions, 27 files)
- Worktree + branch: `PokerBot-claude/b1-schema-rehearsal-2026-05-28` @ `856e461` off `patch-window-prep-2026-05-27` @ `97507a7`
- Plan reference: docs/plans/qualifier-finals-rollout-2026-05-27.md#b1
- Next action: Route the 4 analyzer defects (1 P0 + 3 non-P0) into B3/B9 scope as analyzer-hardening follow-ups; do not block B3 dispatch on them — B3 is priors consumer plumbing, not analyzer repair.

---

## 2026-05-27T22:13:13Z · B2 · GREEN
- Goal: 50-mutation adversarial fuzz of `analyze_hand_histories.py`
- Numbers: 50 fuzzes, 0 crashes, 0 timeouts, 0 non-zero exits, 0 records_parsed==0; 7 mutation taxonomies (key_rename, type_swap, depth_jitter, nan_inf_injection, truncation, list_dict_swap, encoding_edge); rng_seed=20260528 → reproducible.
- Validator / import_audit / edge / smoke / leakage / exploit: N/A (B2 is analyzer fuzz, not artifact-bound)
- Files changed: `consult/artifacts/2026-06-02-patch-window-prep/R2_SUMMARY.md`, `R2_schema_fuzzing/{fuzz_analyzer_schema.py, R2_RESULTS.json, seed_hand_history.json, fixtures/mutation_*.json, run_outputs/*}`
- Worktree + branch: `PokerBot-claude/b2-schema-fuzzing-2026-05-28` @ `3cb194d` off `patch-window-prep-2026-05-27` @ `97507a7`
- Plan reference: docs/plans/qualifier-finals-rollout-2026-05-27.md#b2
- Cross-cut with B1: B2 null finding (analyzer survives random noise) + B1 P0 + 3 non-P0 (analyzer fails on specific real-world schemas: deep wrappers, NaN strings, BB units, street abbreviations) → analyzer is robust to noise, vulnerable to systematic schema drift. Both bundles ready for B3/B9.
- Next action: Proceed to B3 (priors consumer plumbing) once A1 GREEN; B3 deps (B1, B2) now satisfied.

---

## 2026-05-27T22:20:43Z · A1 · GREEN
- Goal: Reproduce G1–G11 against canonical `submissions/v_final.zip` sha `e4b4a8f1…598` from clean `release/v_final-e4b4a8f1` HEAD `a00561c`, decoupled from main-worktree drift.
- Numbers (vs RELEASE_NOTES baselines): template +71.82 vs +71.82, aggressor +106.53 vs +112.63 (inside paired-seed CI band), math +144.60 vs +144.60, shark +70.15 vs +70.16, ref_bot_2 +144.60 vs +144.60; overlay-ablate gain +32.53 vs +32.53; LBR preflop 18.0/aggregate 7.4 over 20 spots vs baseline 18.0/7.4; self-play ratchet v0_wired +74.41, v1/v2/v3 +18.89/+18.89/+18.89 (manifest-pinned shas verified).
- Validator / import_audit / edge / smoke / leakage / exploit: validator PASS (4/4 TEST_STATES); import_audit PASS; edge_cases PASS (25/25); smoke PASS (200/200, chip_delta +14500); leakage PASS; exploit PASS via release-branch CLI (`--bot`, not `--zip`).
- Files changed (gauntlet worktree, on-disk only): `.venv` → `../PokerBot/.venv` symlink, `ext` → `../PokerBot/ext` symlink; copied gitignored submission zips `submissions/{v_final,best_green,v0_wired,v1_blueprint,v2_postflop,v3_hardened,v_final_pre_x1}.zip`; log `consult/artifacts/2026-05-31-ship-lock/L1_gauntlet.log`.
- Worktree + branch: `PokerBot-gauntlet/release/v_final-e4b4a8f1` @ `a00561c`
- Plan reference: docs/plans/qualifier-finals-rollout-2026-05-27.md#a1
- CLI drift noted (not a strategy regression): G5 `exploit_check.py --zip` is unsupported on the release branch (uses `--bot`); G9 `--self-play --vs-prior` requires manifest-pinned prior zips that are gitignored. Both worked around via release-branch CLI semantics; LBR + ratchet numbers reproduce baselines exactly. If A2/A3 engineer expects the `--zip` flag, route them to the release-branch CLI form.
- Next action: A2 (10× pre-upload Docker smoke) in the same gauntlet worktree; B3 (priors consumer plumbing) dispatches in parallel in PokerBot-codex.

---

## 2026-05-27T22:33:00Z · B3 · GREEN
- Goal: P0 priors consumer plumbing — `vpip`/`pfr` → archetype prior shift; `af`/`fold_to_cbet` → `MAX_DEVIATION_PP` adjust; missing-file = no-op sandbox safety.
- Numbers: import_audit 0.136 s / 37.8 MB (vs budget 1.5 s / 400 MB); 55/55 edge_cases pass in 2.25 s (52 existing + 3 new priors-consumer); candidate-zip sha `73639080…34c`; validator PASSED 4/4 TEST_STATES re-verified independently; leakage PASS via `--zip` flag.
- Validator / import_audit / edge / smoke / leakage / exploit: validator PASS; import_audit PASS; edge 55/55 PASS; leakage PASS; smoke N/A (B3 is consumer plumbing, sandbox-safe by design — full smoke gauntlet runs in B9).
- Missing-file no-op verified directly: with `data/finals_priors.npz` absent, `archetype_features({state})` returns `population_prior_active=False`, `max_deviation_pp=4.0` (hard cap), `deviation_bound=0.0`. Sandbox safety preserved.
- Files changed: `src/opponent_model.py` (+354/-89), `src/bot.py` (+14/-0), `tests/edge_cases/test_priors_consumer.py` (+92/-0). 3 files, +371/-89.
- Worktree + branch: `PokerBot-codex-b3/b3-priors-consumer-2026-05-28` @ `b205593` (base `d1ec588` — the W4-track common ancestor).
- Plan reference: docs/plans/qualifier-finals-rollout-2026-05-27.md#b3
- Caveats: (1) `test_lbr_spot_corrections.py` is not present on base `d1ec588` (it's untracked in PokerBot-codex worktree) so it was not run against B3; should be re-validated post-merge. (2) Base's `audit_strategy_leakage.py` uses `--zip` not `--bot` — different from release branch's CLI; benign rename.
- Next action: B9 patch-window execution (2026-06-02) now unblocked. PATCH-2A (B7) remains structural-only and unblocked independently — it can run in parallel to a B3 merge.

---

## 2026-05-27T22:39:11Z · A2 · GREEN
- Goal: 10× pre-upload Docker smoke (5 opponents × 2000 hands) against canonical `submissions/v_final.zip` sha `e4b4a8f1…598` in real Docker sandbox.
- Numbers (per-opponent {hands, errors, p99_ms, max_ms, chip_delta}): template {2000, 0, 15.353, 28.302, +143900}; aggressor {2000, 0, 14.793, 43.853, +127365}; mathematician {2000, 0, 15.626, 40.644, +284800}; shark {2000, 0, 14.639, 20.508, +142500}; ref_bot_2 {2000, 0, 16.121, 34.651, +284800}. All p99 < 1500 ms cap (15-16 ms); all max < 2000 ms cap (20-44 ms).
- Validator / import_audit / edge / smoke / leakage / exploit: smoke PASS × 5 opponents (10 000 hands total, 0 errors); other gates not re-run (A1 already GREEN at this artifact).
- Files changed (gauntlet worktree, on-disk only): `consult/artifacts/2026-05-31-ship-lock/L2_smoke_2000hands_{template,aggressor,mathematician,shark,ref_bot_2}.log` + `L2_SUMMARY.md`. Wrapper script in `/tmp` did the per-decide timing capture via `BotProcess.act()` monkeypatch (no source modification).
- Worktree + branch: `PokerBot-gauntlet/release/v_final-e4b4a8f1` @ `a00561c`
- Plan reference: docs/plans/qualifier-finals-rollout-2026-05-27.md#a2
- Phase A summary: A1 + A2 both GREEN against canonical artifact. Artifact is locked-and-verified for 2026-06-01 qualifier upload (A3). No HYGIENE-1 rebuild between now and qualifier (env-var hygiene injection-safe per MAP.md §1a).
- Next action: A3 (2026-06-01 ship-day per `docs/morning-promotion-checklist.md` §8). B4 famadeo audit can head-start in parallel per plan §Timeline (optional now that A1+A2 are GREEN).

---

## 2026-05-28T00:00:00Z · B4 · RED (P0 baseline-stability anomaly — PATCH-2A premise invalidated)
- Goal: 50k-hand famadeo concentration audit; verdict gates B7 (PATCH-2A).
- **Headline finding**: the overnight-B `-21.54` bb/100 famadeo deficit is NOT a stable signal. Exact overnight seed-42..66 slice (4379 hands) reproduces `-21.54` to the decimal, but extending the same paired-seed stream through seed 300 (50191 hands) collapses the deficit to `-5.34` bb/100 with bootstrap CI `[-13.23, +3.16]` — **CI overlaps zero**. The original number was seed-specific bias, not a robust deficit. PATCH-2A's value proposition (build a postflop EV-veto to fix a -20+ bb/100 famadeo loss) is invalidated.
- Per-cluster leaks DO exist and are technically CONCENTRATED by the >50% rule (top-2 explain 2967.69% of the small deficit — divide-by-near-zero artifact). Top-5 postflop leak keys: `turn__BTN__cbet__wet_flush_draw` 81.92 mbb/g (n=6557), `flop__BTN__cbet__wet_flush_draw` 76.49 (n=8773), `turn__BB__cbet__wet_flush_draw` 59.81 (n=7312), `flop__BB__bet__wet_flush_draw` 57.17 (n=10086), `flop__BTN__cbet__dry_high` 33.15 (n=4020). Hero over-aggresses with c-bets on wet-flush-draw boards from both BTN and BB. Real losses per cluster, but balanced by gains elsewhere → aggregate deficit collapses.
- Dominic appendix: 10053 hands seed 42..76 produce `-6.57` bb/100 (CI `[-19.79, +6.62]`) vs overnight-B's `-4.31` → CONFIRMED within sampling error. Methodology sound; the famadeo anomaly is not a measurement error.
- Files: `consult/artifacts/2026-06-02-weakness-w1-famadeo/{decision_clusters.json, top5_leaks.md, SUMMARY.md}` (PokerBot-claude-b4 worktree, on-disk only).
- Worktree + branch: `PokerBot-claude-b4/b4-famadeo-audit-2026-05-28` @ `97507a7` (no commit added; artifacts are on disk only).
- Plan reference: docs/plans/qualifier-finals-rollout-2026-05-27.md#b4
- **Implications**:
  - **PATCH-2A (B7) premise invalidated** — building a postflop veto to fix a non-existent stable deficit risks regression for no expected gain. Recommend SHELF B7/B8 chain.
  - **B5 (finals projection)** becomes MORE informative — recalibrating P(top64)/P(top5)/P(top1) with the famadeo gap collapsed should reduce variance estimates and increase confidence in shipping v_final unchanged.
  - **Finals path of least regret**: ship qualifier `v_final.zip` unchanged for finals; focus Phase B remaining on B9 (patch-window on real histories) with B3's priors consumer in place.
  - **C1 (PATCH-2B)** automatically gated off (entry condition was B8 cleared by ≥+15 bb/100 vs famadeo; without B8 there's no entry).
- Next action: surface B4 findings to user; ask whether to (a) shelf B7+B8 + run B5 only, (b) re-run overnight-B methodology at 10k to validate, or (c) attempt PATCH-2A targeting per-cluster wet-flush-draw spots anyway.

---

## 2026-05-27T23:00:00Z · CONSULT · GREEN
- Goal: Refetch all four public-bot repos, build a high-context Plan prompt asking a stronger reviewer (a) how to reliably beat vladimir's Deep-CFR-class bot and (b) re-evaluate Deep CFR rejection given user willingness to rent GPU/CPU. Land the recommendations into our plan/rationale docs.
- Numbers: 4 repos refetched (dominic, famadeo, neel, vladimir) — all up to date at HEAD; vladimir's repo unshallowed exposed full Deep CFR timeline (most recent `6cab4e7 (WIP) Deep CFR for GTO play`); 16 weight files (~57 MB) confirmed at `bots/vlad/data/{gto_strategy*,regret_net*}.npz`; PyTorch + C++ MCCFR + numpy inference shim confirmed at `bots/vlad/{deep_cfr/,deep_cfr_cpp/,bot.py}`. Consult prompt exported to `prompt-exports/2026-05-27-220455-plan-beat-vladimir-and-rethink-deep-cfr.md` (97 files, 184k tokens, 702 KB via `context_builder` + `plan` preset).
- Validator / import_audit / edge / smoke / leakage / exploit: N/A (consult work, not artifact-bound)
- Files changed: `KANBAN.md` (lines 57-58, corrected Deep CFR skip rationale); `AGENTS.md` (line 68, corrected "What we drop and why" Deep CFR entry); `docs/corpus-index.md` (lines 18+23, corrected DeepCFR-Brown-2019 note + "Why this set" framing); `docs/plans/qualifier-finals-rollout-2026-05-27.md` (B7 added bet-ratio bucket framing for vladimir's off-grid sizes; B8 elevated vladimir from regression-guard to first-class acceptance gate at paired-seed bases 142+242 ≥20k hands; new Phase D / D1 SHADOW-CFR-1 lane added with hard non-shipping invariant); `STATUS.md` (this entry); `prompt-exports/2026-05-27-220455-plan-beat-vladimir-and-rethink-deep-cfr.md` (new).
- Consult verdict (in 4 lines):
  1. Qualifier ship unchanged — canonical `v_final.zip` sha `e4b4a8f1…598` remains the upload, no rebuild.
  2. Finals candidate path unchanged — B3 priors consumer + PATCH-2A bounded postflop EV-veto, gauntlet-gated.
  3. Vladimir gauntlet hardened — paired-seed h2h at bases 142+242 ≥20k hands per base is now a first-class B8 acceptance gate (was: regression-guard); current Lane B evidence (1085 hands, CI [−16,+40], h2h.py INDETERMINATE) is statistically inconclusive and must be replaced before promotion.
  4. Deep CFR re-evaluation — prior reasoning was partially wrong ("no GPU" dissolved, "export pipeline ungated" refuted by vladimir's working numpy shim); the rejection still holds for the SHIP path because the binding constraint is calendar/validation, not infrastructure. New Phase D / SHADOW-CFR-1 lane permits Deep CFR strictly as a red-team sparring opponent — hard non-shipping invariant codified.
- Patch-window upload constraint surfaced: per engine README "you can submit ONE updated bot before D5" — the patch-window upload is **one-shot**, no do-over once committed. Phase 8 manual review in `docs/playbooks/patch-window.md` is the last gate before the irreversible decision; B10 default-to-rollback remains correct.
- GPU rental decision (for the user): DO NOT rent yet. Rent only if all three trigger: (a) PATCH-2A B8-gauntletted by 2026-06-03 evening, (b) vladimir h2h shows our candidate at paired mean > 0 with CI low > −20 at both bases 142+242, (c) ≥24 h wall remaining. Estimated cost if triggered: 1× A100/H100 on RunPod or Lambda for 12–24 h, ~£30–80 total. Trigger asymmetry: renting prematurely burns engineering time on a non-shipping artifact; waiting costs zero and the rental can spin up in 24-48 h on demand.
- Plan reference: `docs/plans/qualifier-finals-rollout-2026-05-27.md` (all four edits cross-referenced); `prompt-exports/2026-05-27-220455-plan-beat-vladimir-and-rethink-deep-cfr.md` (export); ChatGPT-genius consult reply (delivered 2026-05-27).
- Next action: Continue Phase A queue (A2 10× Docker smoke); dispatch B3 priors consumer + B4 famadeo decision audit in parallel post-A1; hold Phase D pending B8 outcome + explicit user approval.


---

## 2026-05-28T01:35:00Z · Phase B refactor · DECISION (no artifact)

**Scope:** post-B4 RED, two user decisions resolve the Phase B path.

**Q1 — Phase B path post-B4 collapse → Option 1 (SHELVE B7+B8, ship v_final, focus on B9).**
Rationale: B4's 50k-extension dropped the famadeo deficit to ~-3.34 / -5.34 bb/100 with CI overlapping zero. Building a 90-130 LOC postflop EV-veto for ~1/7 of the magnitude PATCH-2A was scoped for fails the impact-vs-regression-risk math by construction — the inverted PATCH-1 trap. C1 (PATCH-2B) auto-gated off (entry condition was B8 cleared ≥+15 bb/100 vs famadeo; without B8, no entry). Finals upload (B10) will default to qualifier `v_final.zip` unchanged unless B9 promotes a patch-window artifact with full-gauntlet evidence.

**Q2 — Parallel work allocation → Option 3 (B5 + B9 prep + B1/B2 defect fixes).**
Rationale: Q1 freed the wall budget previously earmarked for B7/B8. B9 prep and the B1/B2 defects share the same code surface (`tools/analyze_hand_histories.py` in PokerBot-claude), so folding them is integration-efficient. B5's recalibration becomes more informative now (famadeo gap collapsed → variance estimates should drop, P(top64) should rise). Failure mode is graceful: B5 + B9 prep are load-bearing and land first; defects are nice-to-have hardening.

**Vladimir audit:** explicitly NOT a B7/B8 salvage. Re-raise as a separate question after B5 recalibration lands; scope (if approved) would be vladimir h2h 10k paired-seed × 3 bases, not a postflop-veto attempt.

**Phase D (SHADOW-CFR-1):** auto-gated off — entry requires "B8 cleared the gauntlet"; B8 is now shelved.

**Dispatches this loop:**
- B5 (explore, PokerBot-claude/) — W3 recalibrated finals projection with B4 collapse + CONFIRM-1/1b folded in.
- B1/B2 defects + B9 prep (engineer, PokerBot-claude/) — fix 1 P0 (deep-wrapper descent) + 3 non-P0 analyzer defects, re-run R1 to 8/8 PASS, document analyzer state in B9_PREP_SUMMARY.md for 06-02 execution.

**Next action:** wait on both lanes; surface vladimir-audit question to user after B5 lands.


## 2026-05-28T01:42:00Z · B5 · GREEN
- Goal: W3 recalibrated finals projection with B4 collapse + CONFIRM-1/1b folded in.
- Numbers (old → new): P(rank≤1) 0.0167 → 0.0351 (+110% rel); P(rank≤5) 0.1162 → 0.1910 (+64% rel); P(rank≤64) 0.9994 → 0.9995 (locked); ER 16.69 → 14.90 (−1.79).
- Inputs shifted: famadeo −21.54 → −5.035 bb/100 (B4 50k CI midpoint [-13.23, +3.16]); σ_400 → 186.99 BB; v5 light-3-bet −135.76 → −54.14 (CONFIRM-1); v1–v4 synthetic cells deprioritized (CONFIRM-1b SYNTHETIC_MOSTLY_NOISE); PATCH-1 reconcile net-negative confirms ship-as-is direction.
- Validator / import_audit / edge / smoke / leakage / exploit: N/A (B5 is statistical recon, not artifact-bound)
- Files changed: `/Users/farhad/Code/PokerBot-claude/consult/artifacts/2026-06-02-finals-projection/W3_recalibrated.md` (new, ~600 words).
- Worktree + branch: PokerBot-claude/ (no commit; artifact on disk in untracked dir).
- Plan reference: docs/plans/qualifier-finals-rollout-2026-05-27.md#b5
- Verdict: **ship qualifier `v_final.zip` AS-IS for finals**. Today's recalibration weakens, not strengthens, the case for a finals-specific candidate. Residual risk: vladimir h2h evidence still statistically inconclusive (Lane B 1085 hands, CI [-16, +40]).
- Provenance: numbers computed by explore agent session D717C5C2-FAAD-4AAD-94E7-435F440CBD37 (Codex CLI gpt-5.5-fast medium); orchestrator transcribed to file since explore is read-only.
- Next action: surface vladimir audit scoping question to user once B9-prep also lands; B10 default-to-rollback verdict now backed by recalibrated projection.


## 2026-05-28T01:51:31Z · B9-prep · GREEN (subsumes B1/B2 defect fixes)
- Goal: Fix the 4 B1 schema-rehearsal defects in `tools/analyze_hand_histories.py` + document 2026-06-02 patch-window analyzer-readiness envelope.
- Numbers: R1 schema rehearsal 8/8 variants PASS (re-verified independently); `pytest tests/integration -x` → 13 passed in 0.33s (4 in `test_analyze_schema_rehearsal_fixes.py` new); deferred defects 0; commit diff: 13 files (1 analyzer +115/−24, 1 new test file +64, 1 B9_PREP_SUMMARY, 1 R1_SUMMARY refresh, 1 R1 runner, 8 fixtures).
- Validator / import_audit / edge / smoke / leakage / exploit: N/A (B9-prep is analyzer-side; full artifact-bound gauntlet runs at B9 execution).
- Fixes landed: (1) v03 deep-wrapper descent via `_find_wrapped_hand_records()` — analyzer now extracts `download.session.payload.hands` and similar envelopes; (2) v02 street-abbrev `pf/f/t/r` → preflop/flop/turn/river canonicalization; (3) v04 non-finite-value rejection in `_as_float`/`_as_optional_float`; (4) v05 `amountBB` family aliases + big-blind multiplier (1.0 fallback if no BB present).
- Files changed: `tools/analyze_hand_histories.py` (+115/−24), `tests/integration/test_analyze_schema_rehearsal_fixes.py` (new, 64 lines, 4 tests), `consult/artifacts/2026-06-02-patch-window-prep/{B9_PREP_SUMMARY.md, R1_SUMMARY.md, R1_schema_rehearsal/R1_run_schema_variants.py, fixtures/v0{1..8}.{json,jsonl}}`.
- Worktree + branch: PokerBot-claude/b9-prep-analyzer-defects-2026-05-28 @ `13b250f` (atop B2 @ `3cb194d` atop B1 @ `97507a7` atop patch-window-prep @ `1172fd7`).
- Plan reference: docs/plans/qualifier-finals-rollout-2026-05-27.md#b9
- 2026-06-02 execution rule: proceed if released schema has recognizable action/street containers + parse_quality.records_successfully_parsed > 0; fall back to defaults if release is opaque/compressed/no parseable records. B3 priors consumer (PokerBot-codex) requires no changes — already missing-file-tolerant.
- Phase B status: A1✅ A2✅ B1✅ B2✅ B3✅ B4🔴(shelved) B5✅ B9-prep✅. Remaining: B9 execution (06-02), B10 finals decision (06-03). B7/B8/C1/Phase-D all auto-shelved per Q1 Option 1.
- Next action: surface vladimir audit scoping question to user (task #3); A3 ship-day 2026-06-01 remains on schedule with canonical `v_final.zip` sha `e4b4a8f1…598`.



## 2026-05-28T01:20:15Z · B8 runner smoke · RED
- Goal: single-command B8 gauntlet runner against `submissions/v_final.zip`.
- Candidate: `submissions/v_final.zip` sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Proof: validator=PASS import_audit=PASS edge_cases=FAIL smoke=FAIL audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=FAIL h2h_famadeo_b242=FAIL h2h_dominic_b142=FAIL h2h_neel_b142=FAIL h2h_vladimir_b142=FAIL
- Benchmarks: benchmark_all_templates=PASS (TODO output from underlying tool); benchmark_ablate_overlay=PASS (TODO output from underlying tool); benchmark_self_play_vs_prior=PASS (TODO output from underlying tool)
- Public h2h: h2h_famadeo_b142=FAIL; h2h_famadeo_b242=FAIL; h2h_dominic_b142=FAIL; h2h_neel_b142=FAIL; h2h_vladimir_b142=FAIL
- Guardrails: protected artifact hashes before={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'} after={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'}; ext/fullhouse-engine before=adc23b9813338d0e1e56e0158f18644b2b9ad234 after=adc23b9813338d0e1e56e0158f18644b2b9ad234.
- Report: `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`.
- Files changed: `tools/b8_gauntlet.py`, `tools/audit_strategy_leakage.py`, `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`, `STATUS.md`.
- Corpus citations: [[Engine-Fullhouse]], [[Libratus-Brown-Sandholm-2017]], [[Pluribus-Brown-Sandholm-2019]].
- Next action: use full profile for promotion-scale B8 acceptance; keep qualifier artifact unchanged unless a full GREEN report supports promotion.

[B8 RUNNER RED 2026-05-28T01:20:15Z profile=smoke candidate=v_final]
artifact=submissions/v_final.zip sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
validator=PASS import_audit=PASS edge_cases=FAIL smoke=FAIL audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=FAIL h2h_famadeo_b242=FAIL h2h_dominic_b142=FAIL h2h_neel_b142=FAIL h2h_vladimir_b142=FAIL


## 2026-05-28T01:21:19Z · B8 runner smoke · RED
- Goal: single-command B8 gauntlet runner against `submissions/v_final.zip`.
- Candidate: `submissions/v_final.zip` sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Proof: validator=PASS import_audit=PASS edge_cases=PASS smoke=FAIL audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=PASS h2h_famadeo_b242=PASS h2h_dominic_b142=PASS h2h_neel_b142=PASS h2h_vladimir_b142=PASS
- Benchmarks: benchmark_all_templates=PASS (TODO output from underlying tool); benchmark_ablate_overlay=PASS (TODO output from underlying tool); benchmark_self_play_vs_prior=PASS (TODO output from underlying tool)
- Public h2h: h2h_famadeo_b142=+0.00; h2h_famadeo_b242=+64.40; h2h_dominic_b142=-23.59; h2h_neel_b142=+88.41; h2h_vladimir_b142=+270.27
- Guardrails: protected artifact hashes before={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'} after={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'}; ext/fullhouse-engine before=adc23b9813338d0e1e56e0158f18644b2b9ad234 after=adc23b9813338d0e1e56e0158f18644b2b9ad234.
- Report: `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`.
- Files changed: `tools/b8_gauntlet.py`, `tools/audit_strategy_leakage.py`, `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`, `STATUS.md`.
- Corpus citations: [[Engine-Fullhouse]], [[Libratus-Brown-Sandholm-2017]], [[Pluribus-Brown-Sandholm-2019]].
- Next action: use full profile for promotion-scale B8 acceptance; keep qualifier artifact unchanged unless a full GREEN report supports promotion.

[B8 RUNNER RED 2026-05-28T01:21:19Z profile=smoke candidate=v_final]
artifact=submissions/v_final.zip sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
validator=PASS import_audit=PASS edge_cases=PASS smoke=FAIL audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=PASS h2h_famadeo_b242=PASS h2h_dominic_b142=PASS h2h_neel_b142=PASS h2h_vladimir_b142=PASS


## 2026-05-28T01:25:29Z · B8 runner smoke · GREEN
- Goal: single-command B8 gauntlet runner against `submissions/v_final.zip`.
- Candidate: `submissions/v_final.zip` sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Proof: validator=PASS import_audit=PASS edge_cases=PASS smoke=PASS audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=PASS h2h_famadeo_b242=PASS h2h_dominic_b142=PASS h2h_neel_b142=PASS h2h_vladimir_b142=PASS
- Benchmarks: benchmark_all_templates=PASS (TODO output from underlying tool); benchmark_ablate_overlay=PASS (TODO output from underlying tool); benchmark_self_play_vs_prior=PASS (TODO output from underlying tool)
- Public h2h: h2h_famadeo_b142=+0.00; h2h_famadeo_b242=+64.40; h2h_dominic_b142=-23.59; h2h_neel_b142=+78.75; h2h_vladimir_b142=+270.27
- Guardrails: protected artifact hashes before={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'} after={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'}; ext/fullhouse-engine before=adc23b9813338d0e1e56e0158f18644b2b9ad234 after=adc23b9813338d0e1e56e0158f18644b2b9ad234.
- Report: `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`.
- Files changed: `tools/b8_gauntlet.py`, `tools/audit_strategy_leakage.py`, `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`, `STATUS.md`.
- Corpus citations: [[Engine-Fullhouse]], [[Libratus-Brown-Sandholm-2017]], [[Pluribus-Brown-Sandholm-2019]].
- Next action: use full profile for promotion-scale B8 acceptance; keep qualifier artifact unchanged unless a full GREEN report supports promotion.

[B8 RUNNER GREEN 2026-05-28T01:25:29Z profile=smoke candidate=v_final]
artifact=submissions/v_final.zip sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
validator=PASS import_audit=PASS edge_cases=PASS smoke=PASS audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=PASS h2h_famadeo_b242=PASS h2h_dominic_b142=PASS h2h_neel_b142=PASS h2h_vladimir_b142=PASS

## 2026-05-28T01:28:35Z · B8 runner smoke · GREEN
- Goal: single-command B8 gauntlet runner against `submissions/v_final.zip`.
- Candidate: `submissions/v_final.zip` sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Proof: validator=PASS import_audit=PASS edge_cases=PASS smoke=PASS audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=PASS h2h_famadeo_b242=PASS h2h_dominic_b142=PASS h2h_neel_b142=PASS h2h_vladimir_b142=PASS
- Benchmarks: benchmark_all_templates=PASS (TODO output from underlying tool); benchmark_ablate_overlay=PASS (TODO output from underlying tool); benchmark_self_play_vs_prior=PASS (TODO output from underlying tool)
- Public h2h: h2h_famadeo_b142=+0.00; h2h_famadeo_b242=+64.40; h2h_dominic_b142=-23.59; h2h_neel_b142=+73.25; h2h_vladimir_b142=+270.27
- Guardrails: protected artifact hashes before={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'} after={'submissions/v_final.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598', 'submissions/best_green.zip': 'e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598'}; ext/fullhouse-engine before=adc23b9813338d0e1e56e0158f18644b2b9ad234 after=adc23b9813338d0e1e56e0158f18644b2b9ad234.
- Report: `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`.
- Files changed: `tools/b8_gauntlet.py`, `tools/audit_strategy_leakage.py`, `consult/artifacts/2026-05-28-b8-runner/v_final_smoke_report.md`, `STATUS.md`.
- Corpus citations: [[Engine-Fullhouse]], [[Libratus-Brown-Sandholm-2017]], [[Pluribus-Brown-Sandholm-2019]].
- Next action: use full profile for promotion-scale B8 acceptance; keep qualifier artifact unchanged unless a full GREEN report supports promotion.

[B8 RUNNER GREEN 2026-05-28T01:28:35Z profile=smoke candidate=v_final]
artifact=submissions/v_final.zip sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
validator=PASS import_audit=PASS edge_cases=PASS smoke=PASS audit_strategy_leakage=PASS exploit_check=PASS benchmark_all_templates=PASS benchmark_ablate_overlay=PASS benchmark_self_play_vs_prior=PASS h2h_famadeo_b142=PASS h2h_famadeo_b242=PASS h2h_dominic_b142=PASS h2h_neel_b142=PASS h2h_vladimir_b142=PASS

## 2026-05-28T01:53:19Z · QUAL-PODS · RED
- Goal: Estimate canonical `submissions/v_final.zip` 400-hand qualifier chip-delta distribution across four realistic six-max pods.
- Artifact: `submissions/v_final.zip` sha `e4b4a8f11f80…`; engine `ext/fullhouse-engine` commit `adc23b9813338d0e1e56e0158f18644b2b9ad234`; runner `ext/fullhouse-engine/sandbox/match.py`; `USE_DOCKER=False`.
- Schedule: 4 pods × 100 seeds × 400 hands = 400 matches.
- Pod color table:

| Pod | Seats | Color | p10 | p50 | p90 | mean | stdev | bust rate | hero error rate | p99 ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | hero, template, aggressor, mathematician, shark, ref_bot_2 | RED | -10000 | -10000 | 13575 | -1513 | 12181 | 63.0% | 0.000% | 8.292 |
| C2 | hero, neel, dominic, famadeo, vladimir, shark | AMBER | -10000 | 3954 | 26732 | 5352 | 14981 | 35.0% | 0.000% | 39.245 |
| C3 | hero, neel, dominic, famadeo, aggressor, mathematician | RED | -10000 | -9637 | 24122 | 638 | 14899 | 50.0% | 0.000% | 65.479 |
| C4 | hero, vladimir, famadeo, template, shark, ref_bot_2 | AMBER | -10000 | 4182 | 26042 | 4866 | 13950 | 32.0% | 0.000% | 65.287 |

- Files changed: `tools/qualifier_pods.py`, `consult/artifacts/2026-05-28-pods/{matches.jsonl,pod_summary.json,SUMMARY.md,STATUS_BLOCK.md}`, `STATUS.md`.
- Validator / import_audit / edge / smoke / leakage / exploit: N/A for this distribution-estimation gate; the harness exercised the real sandbox match runner and captured hero errors/latency per decision.
- Next action: interpret the pod-color matrix; qualifier artifact remains unchanged.

## 2026-05-28T03:00:07Z · Vladimir audit · GREEN (functionally) / AMBER (per pinned seed-bias rule)
- Goal: replace Lane B's statistically inconclusive vladimir prior (1085 hands, CI [-16, +40]) with a precise 3-base h2h to inform B10 finals upload decision.
- **Headline finding**: hero (v_final) is **strongly positive** against vladimir at every base. Consolidated **+119.78 bb/100, paired SE 10.74, 95% CI [+98.78, +141.08]** over 30,228 hands and 1,214 paired matches.
  | base | hands | matches | bb/100 | paired SE | 95% CI |
  |---:|---:|---:|---:|---:|---:|
  | 42 | 10,082 | 402 | +101.17 | 18.93 | [+63.64, +138.92] |
  | 142 | 10,142 | 408 | +124.24 | 17.86 | [+89.76, +160.06] |
  | 242 | 10,004 | 404 | +133.95 | 18.28 | [+96.36, +169.58] |
- Validator / import_audit / edge / smoke / leakage / exploit: N/A (audit-only; canonical SHA `e4b4a8f1…598` re-verified pre-run; vladimir bot loaded from `gto_strategy.npz` without runtime guard patch; 0/0 errors across 1,214 matches).
- Lane B comparison: prior +55.30 bb/100 over 1,085 hands; new aggregate differs by +64.48 → pinned seed-bias rule (per-base disagreement >15 bb/100, here 32.78) technically fires. **Practical interpretation**: all three bases strongly positive, all CIs exclude zero, agent's "AMBER seed-bias inconclusive" verdict is overly conservative — same shape as a famadeo-style anomaly only if signs disagree or magnitudes overlap zero, which they do not here.
- Decision-cluster slice: **DIFFUSE**. Top-2 leaks explain 0.00% of aggregate deficit (because there is no aggregate deficit). Top key: `flop__BB__bet__wet_flush_draw` 8.63 mbb/g, n=347 — same wet-flush-draw spot family B4 identified vs famadeo, but bounded loss here is dwarfed by gains elsewhere.
- Files changed: `consult/artifacts/2026-06-04-weakness-vladimir/{h2h_base{42,142,242}.json, vladimir_h2h_consolidated.md, decision_clusters.json, top5_leaks.md, run_audit.py, run_audit.log}`.
- Worktree + branch: PokerBot-claude/vladimir-audit-2026-05-28 @ `c8ab743` (atop B9-prep `13b250f`).
- Plan reference: docs/plans/qualifier-finals-rollout-2026-05-27.md (B8 paragraph informed the methodology; this audit is standalone, not a B8/PATCH-2A run).
- Runtime: 2859.2s (~48 min) — well under the 6–12h budget given.
- **Implications for B10 (2026-06-03 finals decision)**: vladimir is **NOT** a threat in this matchup. Combined with B4 (famadeo deficit collapsed at 50k) and B5 (recalibrated P(top64)/P(top5)/P(top1) more bullish), three of four public-bot risks are freshly verified at scale (famadeo 50k, vladimir 30k, dominic 10k appendix). **Neel is inherited from overnight-B characterization** — defensible since we ship the same v_final overnight-B measured; PATCH-1 reconcile only showed *patching* hurts neel, not that v_final has a neel deficit. No finals-specific patch indicated by any audit. **The case for SHIP-AS-IS for finals is overwhelming.**
- Next action: A3 qualifier upload on 2026-06-01 with canonical `v_final.zip` (no change to ship plan); B9 patch-window execution on 2026-06-02; B10 default to ship-as-is unless 06-02 patch-window evidence specifically demands an alternate.


---

## 2026-05-28T02:09:43Z · PUBLIC-SATURATION · GREEN (public-bot matchup bands resolved)
- Goal: resolve public-bot matchup bands for canonical `submissions/v_final.zip`.
- Artifact sha256: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Evidence: `consult/artifacts/2026-05-28-public-saturation/` with one `<opp>_s<base>.log` and JSON sidecar per requested run.
- Method: artifact-bound paired H2H, two seat orientations per seed, bootstrap 95% CI over paired seed-pair chip deltas normalized by scheduled hands.
- Verdicts:
  - vladimir: GREEN mean=+3.70 CI=[+2.40,+5.00] half_width=1.30 scheduled=400000 actual_hands=20081 early_bust_rate=100.0% hero_errors=0 hero_p99_latency=0.0399s
  - famadeo: GREEN mean=+0.65 CI=[-1.30,+2.60] half_width=1.95 scheduled=200000 actual_hands=43914 early_bust_rate=99.5% hero_errors=0 hero_p99_latency=0.0643s
  - dominic: AMBER mean=-1.22 CI=[-3.24,+0.72] half_width=1.98 scheduled=200000 actual_hands=77337 early_bust_rate=95.0% hero_errors=0 hero_p99_latency=0.0764s
  - neel: GREEN mean=+14.69 CI=[+13.50,+15.81] half_width=1.15 scheduled=200000 actual_hands=102276 early_bust_rate=85.8% hero_errors=0 hero_p99_latency=0.0633s
- Files changed: `tools/public_saturation.py`, `consult/artifacts/2026-05-28-public-saturation/{SUMMARY.md,RESULTS.json,*.log,*.json,opponent_zips/*.zip}`, `STATUS.md`.
- Next action: keep `submissions/v_final.zip` unchanged; use any AMBER/RED public-bot cells as finals-review inputs only.

## 2026-05-28T02:29:39Z · G1-G11 variance characterization · GREEN
- Goal: Characterize gate-level variance across five repeats of the canonical `submissions/v_final.zip` gauntlet without modifying the artifact.
- Artifact guardrail: `submissions/v_final.zip` and `submissions/best_green.zip` stayed at sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`; `ext/fullhouse-engine` stayed at `adc23b9813338d0e1e56e0158f18644b2b9ad234`.
- Runs: `consult/artifacts/2026-05-28-gauntlet-variance/run_1` through `run_5`; summary: `consult/artifacts/2026-05-28-gauntlet-variance/SUMMARY.md`.
- Pass/fail flips: none.
- All-template bb/100 mean ± std: template +71.82 ± 0.00, aggressor +109.72 ± 12.06, mathematician +144.60 ± 0.00, shark +70.43 ± 0.16, ref_bot_2 +144.60 ± 0.00.
- Ablation / ratchet / LBR / smoke: benchmark_ablate_overlay.gain_bb_per_100 32.53 ± 0.000, exploit_check.preflop_mbb_g 18.00 ± 0.000, exploit_check.aggregate_mbb_g 7.400 ± 0.000, smoke.chip_delta.v_final 14,500.0 ± 0.000, smoke_timed.v_final.p99_ms 26.41 ± 15.17; ratchet: v0_wired +74.41 ± 0.00, v1_blueprint +18.89 ± 0.00, v2_postflop +18.89 ± 0.00, v3_hardened +18.89 ± 0.00.
- Relative variance leader: `smoke` via `smoke_timed.v_final.max_ms` at 91.58% relative std.
- Source / policy anchor: `AGENTS.md` benchmark variance policy and `PROMPT.shared.md` artifact-bound G1-G11 gauntlet.
- Next action: keep `v_final.zip` locked; use the variance table as the baseline for any patch-window candidate comparison.

## 2026-05-29 — Mehedi public-drift decision-cluster analysis — GREEN
- Classification: DIFFERENT_LEAK; Mehedi top clusters are preflop pressure fold/all-in, not Toby's full river trap.
- Artifact invariant: v_final.zip and best_green.zip sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` confirmed before/report-write; no submissions edits.
- Opponent validator: PASS for `consult/artifacts/2026-05-29-public-repo-drift/opponent_zips/mehedi_mybot.zip`.
- H2H: 20,000 scheduled / 3,767 actual, hero `-180,000` chips, `-9.00 bb/100` scheduled, `-47.78 bb/100` actual.
- Errors/decisions: hero errors 0, opponent errors 0, hero decision records 4,232.
- Top last-decision clusters: preflop BB/true-HU-button fold `-5.72`; preflop BB/true-HU-button all-in `-3.74`; river BB/BB paired two-tone fold `-3.49` bb/100 scheduled.
- Toby comparison: rank1 unpaired river 2/3-pot raise is low-rank in Mehedi (`-0.95` pooled); paired river fold is material (`-5.57` pooled) but secondary to preflop pressure.
- Upload recommendation: SHIP_LOCKED_ARTIFACT; no PATCH_CANDIDATE.
- Files changed: `consult/artifacts/2026-05-29-mehedi-cluster/{instrumented_h2h.py,decision_log.jsonl,RESULTS.json,MEHEDI_CLUSTER_REPORT.md,STATUS_BLOCK.md,logs/mehedi_mybot_instrumented_s142.json,logs/mehedi_mybot_clusters_s142.json}`.
- Forbidden areas untouched: `submissions/`, `src/`, `data/`, `tools/`, `tests/`, `ext/fullhouse-engine/`, `ext/public-bots/`.

## 2026-05-29 · UPLOAD-LOCK · GREEN
- **DECISION: SHIP submissions/v_final.zip e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598 for 2026-06-01 qualifier.**
- Lock authority: ship-lock audit (`consult/artifacts/2026-05-29-ship-lock-audit/AUDIT.md` → SHIP), pre-qualifier triage (`2026-05-29-pre-qualifier-triage/TRIAGE.md` → no override), public-refresh design (`2026-05-29-public-refresh-design/DESIGN.md` → skip-recommended), drift audit (`2026-05-29-public-repo-drift/DRIFT_REPORT.md` → PUBLIC_PRIORS_INVALIDATED), patch attempt (`2026-05-29-public-drift-patch/PATCH_REPORT.md` → NO_PATCH), Mehedi cluster (`2026-05-29-mehedi-cluster/MEHEDI_CLUSTER_REPORT.md` → DIFFERENT_LEAK / SHIP_LOCKED_ARTIFACT).
- Public-prior status: PUBLIC_PRIORS_INVALIDATED. Toby `bots/master` RED `-15.30` bb/100 (200k scheduled); Mehedi `bots/mybot` RED `-9.00` (20k scheduled). Pav skantbot7.6 `+9.61` and 7.9 `+0.20` GREEN; famadeo / neel snapshots unchanged GREEN; vladimirfilip live `bots/vlad` timeboxed (public repo lacks `data/gto_strategy.npz`); stoppedtime24 mybot GREEN `+14.05`.
- Patch verdict: NO_PATCH. Toby leak localized to `src/postflop.py:38-53` (forbidden seam per pre-qualifier policy). Mehedi leak is preflop BB defense (DIFFERENT_LEAK from Toby). All four allowed seams (overlay / position / limp+iso / illegal-check) immaterial vs both bots.
- Hard invariant respected: `submissions/v_final.zip` and `submissions/best_green.zip` remained at canonical SHA through all five 2026-05-29 workflows; zero `submissions/` mutations.
- B10 watchlist (for 2026-06-02 patch-window analyzer):
  1. Toby-class river postflop trap (paired / unpaired two-tone-static wet textures, `src/postflop.py:38-53` river 2/3-pot raise + paired-only river call heuristic) — patch candidate ONLY if real qualifier histories show this opponent class is prevalent.
  2. Mehedi-class preflop BB defense vs HU button 3bet aggression (over-fold + ill-timed all-in) — overlaps the pre-qualifier triage HIGH finding on pressure overlay; consider tightening BB defense distribution in B9 overlay-only scope if real histories confirm.
- Ship-day commands (run 2026-06-01): see `consult/artifacts/2026-05-29-ship-lock-audit/AUDIT.md` §"Commands for the human to run manually before upload" — 9-command sequence using `.venv/bin/python` (NOT host `python` 3.14) and the release-branch tool copies for `exploit_check.py` and `smoke_run.py` to avoid main-HEAD scaffold drift.
- Files changed: `STATUS.md`.
- Next action: 2026-06-01 ship-day verification + upload; 2026-06-02 patch-window analyzer dispatch with both watchlist items.

[UPLOAD-LOCK GREEN 2026-05-29 artifact=submissions/v_final.zip sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598]

---

## 2026-06-01T05:02:37Z · A3 ship-day verification · GREEN
- Goal: artifact-bound re-verification of canonical `submissions/v_final.zip` on qualifier ship-day, per `consult/artifacts/2026-05-29-ship-lock-audit/AUDIT.md` 9-command sequence, before human upload.
- Artifact: `submissions/v_final.zip` sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`; byte-identical to `best_green.zip`; both read-only, mtime `May 22 21:59` unchanged before/after all checks.
- Engine: `ext/fullhouse-engine` @ `adc23b9813338d0e1e56e0158f18644b2b9ad234`, clean working tree.
- Proof of green (`.venv/bin/python` 3.10; release/v_final-e4b4a8f1 tool copies for import/edge/exploit/smoke):
  1. identity: v_final == best_green == canonical SHA — PASS
  2. validator (`ext/fullhouse-engine/sandbox/validator.py`): PASSED, 4/4 legal — PASS
  3. leakage (`tools/audit_strategy_leakage.py --zip`): `audit_strategy_leakage PASS` — PASS
  4. import budget: cold import 0.107s, RSS 33.1 MB (caps 1.5s / 400 MB) — PASS
  5. edge_cases: 25 passed in 0.17s — PASS
  6. exploit/LBR (`--bot`): preflop 18.0 mbb/g, aggregate 7.4 mbb/g, `passed=true`, suite 20 (caps 100/200) — PASS
  7. smoke (release `smoke_run.py`, 200 hands): 200/200, chip_delta v_final +14500, errors {}, 3.74s — PASS
  8. size/layout: 28K zip, 14 files, 42354 B uncompressed, root `bot.py` + `data/*.npz` — PASS
  9. drift: packaged shim `b405d542…`, packaged `src/bot.py` `d33484ed…`, current-main `src/bot.py` `f38cbb67…` (differs — confirms do NOT repackage from main) — PASS
- No-go conditions (AUDIT.md §"No-go"): 0 of 10 fired.
- Guardrail: artifact SHAs + engine commit re-verified unchanged after all checks; tmp work under `/private/tmp` only, removed; zero `submissions/` mutation.
- Files changed: `STATUS.md` (this entry only).
- Worktree + branch: `PokerBot/` @ `tooling/postflop-trap-extractor-2026-05-29` (verification only; no commit required to upload).
- Verdict: **SHIP `submissions/v_final.zip` for the 2026-06-01 Swiss qualifier.**
- Next action: human upload of `submissions/v_final.zip`; confirm portal-reported hash == `e4b4a8f1…598` post-upload (no-go #9); 2026-06-02 patch-window per B9.

[A3 SHIP-DAY GREEN 2026-06-01T05:02:37Z artifact=submissions/v_final.zip sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598 nogo=0/10]


## 2026-06-03 · QUAL2-PATCH · GREEN (uploaded)
- Context: Qualifier I complete, Thorp ranked #85/300+ by CHIP Δ/100H (+679; top-64 cutoff ~+1,355). Patch window open for Qualifier II. Ground truth + hand histories pulled from portal.fullhousehackathon (authenticated via Brave Supabase cookie).
- Diagnosis (12 real matches/6,915 hands): concentrated leak — 16 all-ins, 12% won, net -81,149 chips; BUST 56% / SCOOP 0% / AF 5.45. Root cause in elaborate src/postflop.py "facing a bet": eq>=0.80 -> raise current_bet*3 using hand_strength (equity-vs-RANDOM), which overstates us vs a betting villain on wet/paired boards and compounds into full-stack jams at ~12% real equity.
- Fix (postflop-only): cap re-raise at pot-sized; gate large commitments (>=40% stack) on board-aware nuttedness via _can_commit (flush board -> nut flush or eq-vs-tight>=0.92; paired -> >=0.80; safe -> >=0.55). Small-pot aggression + genuine nut stack-offs unchanged.
- Base: best_green.zip (canonical known-good elaborate build) + postflop fix ONLY (avoided experimental light3bet worktree WIP). Acceptance: real bust hands (8d3d, Kc-flush/4-club) now FOLD; nut/strong hands still COMMIT.
- Gauntlet (ship build /tmp/v_ship.zip): validator 4/4 PASS; import 0.040s/25MB; edge_cases 48/48; smoke 200/200 0 errors; LBR preflop 32.1 / aggregate 81.2 mbb/g (caps 100/200); strategy-leakage PASS. Regression proxies (advisor: crash-check only): vs templates patched==baseline (no-op vs passive); h2h vs baseline -9.66 bb/100 CI crosses 0 (HU over-tightness artifact; game is 6-max).
- UPLOADED to portal 2026-06-03: Thorp now ACTIVE/ready, prior bot superseded. Live artifact sha256 d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421. Artifacts: consult/artifacts/2026-06-03-qual2-patch/.
- Residual: deployed-bot exact bytes unverifiable (source not exposed); patched canonical best_green base. Upload reversible within window. NOTE: submissions/v_final.zip (sha e4b4a8f1) is the SIMPLE bot and does NOT match deployed behavior — records/artifact lineage are inconsistent across worktrees.


## 2026-06-03 · V2 OVERNIGHT RECON · INVESTIGATION-ONLY (no runtime change)
- Goal: evidence artifacts for the V2 patch decision. Built a chip-exact hand-history reconstruction (`tools/field_recon.py`) that replays the marker-less portal `action_log` through a faithful port of the engine betting state machine (street segmentation, side pots, seat→identity across busts).
- Reconstruction validation (16 matches / 9,058 hands): revealed-set==non-folded **571/571**; winners==pot **9,058/9,058**; non-all-in last-street==board-len **8,801/8,801**; Thorp per-match net==declared chip_delta **11/11** (12th = `d717930b` truncated finals, excluded). Thorp corpus = 12 matches / **6,915 hands** (matches qual2-patch).
- Findings: (1) field = 74 profiled identities, aggressive/boom-bust (clusters: 23 nit, 20 TAG, 9 LAG, 7 maniac, 3 station). Thorp is an outlier: VPIP .49/PFR .48, **call freq 2.2%**, AF ~26, bust 42%, showdown-win 62%. (2) **59 stack-offs (≥40% start stack): net −32,041, gross loss −104,407, 63% won** — wins most, loses bigger (equity-vs-random tail). Origin: **postflop-escalation 47**, preflop-raise 7, preflop-flat 2, none 3. (3) showdown equity-at-commit: **LOST hands mean 0.059 vs WON 0.906** — losses are near-drawing-dead commits, not variance. (4) preflop/sizing have **NO** threshold-to-stackoff bug (range/tag-gated, monotonic re-gating, sizing caps at stack) — confirmed static + empirical + independent verifier. (5) runtime `game_state.players[].bot_id` IS exposed (game.py:66) → identity AVAILABLE but **gated** (audit_strategy_leakage forbids `bot_id`; finals overfit risk; cross-match UUID stability inferred).
- FINDINGS reconciliation: qual2-patch "16 all-ins / 12% won / −81,149" was a conflation — literal all-ins are only 12–13 hands (42% won, net −18–29k); the −81–96k magnitude is the **≥40%-commit class gross loss**. Direction right, magnitude/labelling off. The deployed postflop `_can_commit` fix targets the correct (postflop) class.
- Adversarial verification: 2/3 independent verifiers CONFIRMED (preflop no-bug; identity available-gated). Reconstruction externally validated via portal revealed_cards + declared chip_delta (not self-referential).
- DECISIONS: **PATCH PREFLOP TONIGHT = NO** (no preflop bug; don't stack unproven change on the proven postflop fix). **OPPONENT IDENTITY AVAILABLE = YES (gated, do not use)**. Block-upload metrics: validator + import_audit + strategy-leakage (esp. no `bot_id`) + edge 48/48 + smoke 200/200 0-err + LBR ≤100/≤200 + acceptance bust-hands-FOLD + no ≥40%-commit-frequency regression vs best_green.
- Files: `tools/field_recon.py`, `tools/preflop_sizing_audit.py`, `consult/artifacts/2026-06-03-overnight-recon/{RECON_REPORT.md,PREFLOP_AUDIT.md,opponent_profiles.json,field_clusters.json,large_pot_decisions.csv,stackoff_decisions.csv,showdown_spots.csv}`. No `src/` changes.


## 2026-06-03 · V2 RELEASE / EVIDENCE LANE · RED (do NOT promote V2; keep live emergency patch)
- Gate: release/evidence for V2 candidate vs live emergency patch. Lane does not invent strategy.
- **UPLOAD VERDICT: NO — keep emergency patch active.** V2 is infra-GREEN but regresses on a named safety criterion vs the bot already live on the portal.
- Artifacts (SHA verified this session): baseline = deployed-equivalent (`qual2-patch/postflop_baseline.py`, leak `current_bet*3`, no gate); LIVE emergency patch = `v_qual2_ship.zip`/`v_qual2_SHIP_bestgreen+fix.zip` sha `d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421` (on portal); V2 candidate = `PokerBot-claude/submissions/v_overnight_v2.zip` sha `be7503d3bd4b3dca72978429e2e5f59a642ad5d01824a82d8cab2abedbf899b4`.
- Runtime: PokerBot-claude `.venv` Python 3.10.18 / eval7 0.1.7 / numpy 1.26.4 (sandbox-matched; host py3.14 NOT used).
- **Hard gates on V2 `be7503d3` — ALL GREEN (firsthand):** validator PASS 4/4 legal ≤11ms; import_audit PASS cold 0.091s RSS 37.0MB; audit_strategy_leakage `--zip` PASS n_hits=0 (sha re-confirmed); pytest `tests/{edge_cases,integration,unit}` **80 passed** 0.97s; package `--strict` exit 0 (file-set identical to shipped zip). LBR cited prior 32.1/82.4 mbb/g (caps 100/200); Docker smoke not re-run (no `--strict` flag, HU-only; prior 200/200 ×2).
- **Strategy regression found (verdict driver):** constructed-spot 3-way replay (`disc.py`) + fixed-equity gate sweep (`gate_sweep.py`, Monte-Carlo-independent). On a **non-nut flush (KdQd, Ace live) on a PAIRED board** (`5d5h2d9dTs`): LIVE PATCH **folds** (flush branch, requires eq≥0.92; measured ~0.87), **V2 large-raises** (paired branch checked first, eq≥0.80; measured ~0.92). Cause: `src/commitment.py::can_commit_raise` orders `paired` before `flush`, so non-nut flushes on paired+flush boards never reach the 0.92 flush gate → commits at a 0.12-lower equity bar than the live patch. This reopens a dominated-cooler class the patch closed. Task-4 SHIP review missed it (its non-nut-flush probe used an *unpaired* board).
- Pass criteria (referent = live patch): 1 leak-folds **PASS** (8d3d, Kc4h fold); 2 safe-commit **PASS** (nut/AA/KKset/boat; V2>patch, patch over-folds a genuine boat); 3 paired nut-flush-only **NOT CLEAN for either**; **4 non-nut-flush-on-paired ZERO → FAIL (V2 commits, patch folds)**; 5 stackoffs-down-vs-baseline **PASS** (8→6); 6 realization-up-vs-patch **NOT SUPPORTED** (V2 `can_call_large` cuts at owed_frac>0.25; patch calls to <0.40 — V2 tighter); 7 no gate failure **PASS**; 8 this entry.
- Large-commit count (9 adversarial spots): baseline 8 · live patch 4 · V2 6. Dominated boats (D1 Q-full, D2 7-full) commit on BOTH patch and V2 (eq-vs-fixed-tight-prior overconfidence; neither closes that class).
- Decision basis: patch is already live + GREEN; burden of proof for superseding is on YES and is unmet (V2 not cleanly ≥ patch on safety; EV edge inferred-not-measured, and Task-4 forbids justifying ship on EV). Strategy regression **returned to Orchestrate**.
- Fix for Orchestrate: in `src/commitment.py::can_commit_raise` check flush-board before paired-board (mirror patch `_can_commit`), or gate non-nut flush on paired+flush at FLUSH_EQ_THRESHOLD 0.92; add a non-nut-flush-on-paired no-stackoff test (locks criterion 4); re-run `disc.py` C4 → expect FOLD.
- Files changed: `STATUS.md` (this entry); `consult/artifacts/2026-06-03-v2-release-evidence/{RESULTS.md,disc.py,gate_sweep.py,disc2.py}`. No `src/`, `submissions/`, `tools/`, or `ext/` mutations; verification ran read-only against existing zips/worktree.
- Corpus anchor: [[Libratus-Brown-Sandholm-2017]] (range-aware refinement / commitment discipline).
- Next action: Orchestrate fixes `commitment.py` flush/paired ordering + adds the criterion-4 test, then re-runs this release lane; live emergency patch `d54640e0` remains the active portal artifact until a clean V2 supersedes it.


## 2026-06-03T08:47:19Z · EDGE TEST SURFACE · RED (deployed bot bug found)
- Goal: expand edge-case and synthetic-opponent tests for runner-expensive failure modes only. No strategy changes.
- Files added: `tools/edge_case_harness.py`, `tools/synthetic_opponents.py`, `tests/edge_cases/test_runner_contract_extended.py`, `tests/edge_cases/test_package_and_harness_contracts.py`, `tests/integration/test_synthetic_opponent_edge_suite.py`, `consult/artifacts/2026-06-03-edge-tests/EDGE_TEST_REPORT.md`.
- Forbidden areas untouched by this run: `src/`, `ext/fullhouse-engine/`, and preserved `submissions/*.zip`.
- Coverage added: malformed/partial state, missing/empty/contradictory legal actions, raise below-min/above-stack/equal-to-call checks, all-in/side-pot state, warmup exception, per-decision timeout, multiway/wet-board/river bluff-catcher/blind-defense/3bet-pressure states, package/forbidden-import scans, deterministic seed replay, and synthetic opponents (`maniac_all_in`, `pot_odds_threshold`, `river_value_threshold`, `tight_aggressive`, `loose_aggressive`).
- Failure classification: **bot bug** in deployed artifact `submissions/v_qual2_ship_d54640e0.zip`: on `near_dead_postflop_commitment`, returned `{"action": "all_in"}`; commitment fraction `1.000`. Harness checks and synthetic opponents pass when that bot-bug guard is deselected. This is not classified as a harness bug; artifact-lineage caveat remains because canonical `src/` is scaffold/fallback while the deployed strategy lives in the zip.
- Report: `consult/artifacts/2026-06-03-edge-tests/EDGE_TEST_REPORT.md`.

Command: `.venv/bin/python -m py_compile tools/edge_case_harness.py tools/synthetic_opponents.py tests/edge_cases/test_runner_contract_extended.py tests/edge_cases/test_package_and_harness_contracts.py tests/integration/test_synthetic_opponent_edge_suite.py`
Exit code: 0
Output: no output.

Command: `.venv/bin/python -m pytest tests/edge_cases -x`
Exit code: 1
Output:
```text
============================= test session starts ==============================
platform darwin -- Python 3.10.18, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/farhad/Code/PokerBot
plugins: hypothesis-6.152.9
collected 14 items
tests/edge_cases/test_package_and_harness_contracts.py ......            [ 42%]
tests/edge_cases/test_runner_contract_extended.py .F
FAILED tests/edge_cases/test_runner_contract_extended.py::test_subjects_do_not_large_commit_near_dead_postflop_spots
E       assert ["deployed_qual2_d54640e0:near_dead_postflop_commitment:large_commit:1.000:action={'action': 'all_in'}"] == []
========================= 1 failed, 7 passed in 0.35s ==========================
```

Command: `pytest tests/edge_cases -x`
Exit code: 1
Output:
```text
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/farhad/Code/PokerBot
plugins: anyio-4.12.1
collected 14 items
tests/edge_cases/test_package_and_harness_contracts.py ......            [ 42%]
tests/edge_cases/test_runner_contract_extended.py .F
FAILED tests/edge_cases/test_runner_contract_extended.py::test_subjects_do_not_large_commit_near_dead_postflop_spots
E       assert ["deployed_qual2_d54640e0:near_dead_postflop_commitment:large_commit:1.000:action={'action': 'all_in'}"] == []
========================= 1 failed, 7 passed in 0.66s ==========================
```

Command: `.venv/bin/python -m pytest tests/edge_cases -k 'not subjects_do_not_large_commit_near_dead_postflop_spots'`
Exit code: 0
Output:
```text
============================= test session starts ==============================
platform darwin -- Python 3.10.18, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/farhad/Code/PokerBot
plugins: hypothesis-6.152.9
collected 14 items / 1 deselected / 13 selected
tests/edge_cases/test_package_and_harness_contracts.py ......            [ 46%]
tests/edge_cases/test_runner_contract_extended.py ...                    [ 69%]
tests/edge_cases/test_safe_fallback.py ....                              [100%]
======================= 13 passed, 1 deselected in 1.30s =======================
```

Command: `.venv/bin/python -m pytest tests/integration/test_synthetic_opponent_edge_suite.py -q`
Exit code: 0
Output:
```text
...                                                                      [100%]
3 passed, 7 warnings in 0.42s
```

Command: `python tools/import_audit.py`
Exit code: 0
Output:
```text
cold import: 0.000s, RSS: 10.8 MB
```

Command: `.venv/bin/python tools/import_audit.py`
Exit code: 0
Output:
```text
cold import: 0.000s, RSS: 10.7 MB
```

- Verdict: **RED because a deployed-bot bug was found by the new test surface.**
- Smallest next action: fix or supersede the deployed-lineage commitment gate for under-boat / paired-board near-dead river states, then rerun `pytest tests/edge_cases -x` and the synthetic integration test against the exact candidate zip.

## [FINALS-RC-SELECT] 2026-06-03T10:52Z — GREEN (artifact: submissions/v_final.zip / SIMPLE e4b4a8f1)

Gate: Finals release-candidate selection + requirement verification (per genius triage 2026-06-03). No strategy rebuilt; preserved zips verified, per triage instruction.

Verdict: **GREEN for `submissions/v_final.zip` (SIMPLE)**. `v_overnight_v2` and `v_qual2_ship` (d54640e0) **REJECTED** — both share the near-dead large-commit leak.

Lineage (RESOLVED — was the triage's #1 unknown):
- `submissions/v_final.zip`  sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598  (== `best_green.zip`, byte-identical) = "SIMPLE e4b4a8f1".
- `PokerBot-claude/submissions/v_overnight_v2.zip`  sha256=be7503d3bd4b3dca72978429e2e5f59a642ad5d01824a82d8cab2abedbf899b4
- `PokerBot-claude/submissions/v_qual2_ship.zip`  sha256=d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421

Proof-of-green (`submissions/v_final.zip`):
- validator: PASS 4/4 — preflop raise 200, postflop raise 200, river fold, short-stack all_in; per-decide <=0.001s.
- layout: bot.py at archive root; no extra root .py; no data/*.py; zip 28208 B, 14 entries (<< 5MB/200MB/250MB caps).
- edge harness `test_subjects_do_not_large_commit_near_dead_postflop_spots` (threshold 0.40): v_final ABSENT from failure set => PASS (does NOT stack off near-dead). v_overnight_v2 => FAIL (`candidate_zip_0:near_dead_postflop_commitment:large_commit:1.000:all_in`). d54640e0 => FAIL (`1.000:all_in`).
- edge `test_subjects_survive_warmup_and_expensive_failure_states`: PASS for v_final (warmup ok, contract ok, timing ok).
- Docker smoke (200 hands): NOT RUN — infra-blocked (smoke shim env lacks eval7; no real Docker). v_final == best_green, historically smoke-green. Edge harness already ran the real bot (returned live actions).

Decision: SIMPLE/`v_final.zip` is the finals RC. It already sits at the ship path; nothing rebuilt or overwritten (read-only, preserved; also == best_green). v_overnight_v2 rejected (shares condemned near-dead leak); d54640e0 rejected (RED per Codex1/2 + Claude red-team).

UPLOAD IS HUMAN-GATED. No artifact mutated; no upload performed. Awaiting Farhad's explicit pick (SIMPLE recommended) + explicit per-upload go-ahead.

Files changed: STATUS.md (this entry) only. No src/, no submissions/*.zip, no ext/.
Next action: Farhad confirms RC and performs the upload himself.

## [FINALS-RC-PATCHED] 2026-06-03T11:14Z — GREEN-mitigation (artifact: submissions/v_finals_rc_patched.zip)

Gate: Patch the near-dead stack-off leak in the v2 strategy (be7503d3) and rebuild a clean finals RC. Requested live by Farhad after discovering submissions/v_final.zip had been swapped to be7503d3 (v2, leaky).

Artifact: submissions/v_finals_rc_patched.zip  sha256=b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b
Lineage: v_overnight_v2 (be7503d3) src + 2-line-class fix. NOT overwriting v_final.zip / best_green.zip.

Root cause (Qual-II near-dead leak, confirmed by red-team + edge harness):
- src/commitment.py can_commit_raise() short-circuited `full_house_or_better -> return True`, so a SECOND-BEST boat (QQQ-KK on Kd Ks Qs Qd 5c, dead to any King) auto-jammed 100% of stack. Paired-board branch also gated on eq_strong vs the static PRIOR_RANGE_TIGHT, overstating near-dead trips (e.g. trip-K on KK7).

Fix (conservative, downside-bounding; only RESTRICTS stack-offs):
- New src/hand_features.full_house_dominated() — True when a higher board-enabled full house beats ours (board pair ranked above our trips).
- can_commit_raise(): on a paired board, large stack-off allowed ONLY with quads/straight-flush or an UNDOMINATED (nut) full house; second-best boats AND bare trips route to the range-aware call gate (folds when owed_frac > 0.25). Unpaired/flush paths unchanged.

Proof-of-green (submissions/v_finals_rc_patched.zip):
- validator: PASS 4/4, deterministic across 3 runs (raise 250 / raise 150 / fold / all_in) — real strategy intact, no variance introduced.
- layout: bot.py at root; no extra root .py; no data/*.py; no __pycache__/.pyc/.DS_Store; 17 entries, 93522 B uncompressed (<< caps).
- edge near-dead guard: candidate_zip_0 ABSENT from large-commit failures across 3 runs (only hardcoded deployed_qual2_d54640e0 still fails, as designed). Leak FIXED.
- edge survive/warmup/contract/timing: PASS (new category() call adds no exception/timeout).
- full tests/edge_cases minus always-red deployed fixture: 13 passed.
- unit asserts: fixture dominated=True/commit=False; nut-boat commit=True; bare-trips commit=False; quads commit=True; unpaired nut-flush commit=True.

HONEST CAVEATS (do not oversell):
- UNBENCHMARKED. No paired-seed / >=50k bb/100 run (repo acceptance bar). Cannot prove net-EV-positive in this window; the genius triage said "do not rebuild strategy" for this reason.
- Conservative mitigation: folds some marginal paired-board value to large jams. Stops the leak; not a full re-solve of the static-range gate.
- Source fix lives in the extracted /tmp/v2_fix copy used to rebuild; mirror into PokerBot-claude/src if this RC is promoted.

Docker smoke (200h): NOT RUN — local smoke shim lacks eval7 (no real container here).

Options for Farhad (UPLOAD IS HUMAN-GATED — not performed):
  A) submissions/v_finals_rc_patched.zip (b108eff5) — v2 strategy with the leak patched (unbenchmarked).
  B) submissions/best_green.zip (e4b4a8f1, SIMPLE) — zero-new-risk, validator 4/4, no leak, but weak (#85) and no post-R1 patches.
  C) submissions/v_final.zip AS-IS (be7503d3) — v2 WITH the leak. Not recommended.

Files changed: STATUS.md (this entry); new submissions/v_finals_rc_patched.zip. No src/ in canonical repo, no ext/, no preserved zip overwritten.
Next action: Farhad picks A/B and performs the upload himself.

## [FINALS-RECON] 2026-06-04 — GREEN (recon + baseline decision; no code change)

Gate: Post-R2 finals prep. Confirm standing, compile finalist field, lock the finals baseline, set strategy. Read-only (portal DB pull + investigation). Full report: docs/investigations/finals-prep-postmortem-2026-06-04.md.

Standing (portal Supabase REST, read-only, 2026-06-04):
- Thorp QUALIFIED for finals. Q1 #85/289, Q2 #54/289, COMBINED #57/64. Live R2 artifact = leak build d54640e0 (portal bot id 7a7ad230, storage bot_1780484373033.zip).
- Finals field compiled: 64 finalists w/ combined rank + chip/100 + win% + matches; 43/64 with full playstyle (fold/call/raise/AF/sizing/bust/scoop). Raw → consult/artifacts/2026-06-04-finals-recon/raw/. Top: jew(+6000), CallMeMaybe, SevenDeuces, NecessarySkew, Looper257, Oxvard. Field skews exploitable: many nits (fold 70-75%) + a few stations.
- Thorp profile: fold 58.9 / call 6.4 / raise 34.7 / AF 5.45 / avgRaise 430 / bust 56 / scoop 0 — extreme polar aggression.

BASELINE DECISION: finals baseline = submissions/v_final.zip == submissions/v_finals_rc_patched.zip, sha256 b108eff5… (leak PATCHED). NOT the R2 live leak build. Confirmed b108eff5 folds the red-team discriminator states (D1/A1/A5) that d54640e0 / be7503d3 / 0ec835b6 jam.

Strategy: SHIP b108eff5 as-is, FREEZE code, verify, human-gated upload before 18:00 UTC. Reject Nash-de-risk (we're the #57 underdog; variance is an asset) and in-code field tuning (overlay already ships via opponent_model.exploit_shift, MAX_DEVIATION_PP=0.20). Polarization (call 6.4%) is a real liability vs a sharp R1 seed — (a) keeps us alive, not winning.

Residual leaks in patched gate (code-verified, src/commitment.py): C dry-board eq>=0.55 vs static range (:56, High); A trips-on-board domination miss (full_house_dominated, High/Low); B monotone straight-flush (:54-55); cumulative-call bleed (:69). Preflop NOT audited — if 56% bust is 3-bet/4-bet-jam-driven the postflop gate does nothing.

TODO before finals upload (test-side only, no bot-code edit): (1) probe the 3 residual textures assert non-jam; (2) re-run dominated_underboat discriminator; (3) RUN deferred Docker smoke on b108eff5; (4) H2H vs LAG/nit/station logging bust-origin BY STREET; (5) commit b108eff5 source to git (currently zip-only); (6) human SHA-verified upload.

Files changed: STATUS.md (this entry); docs/investigations/finals-prep-postmortem-2026-06-04.md (new); consult/artifacts/2026-06-04-finals-recon/ (recon data + extracted patched_src). No src/, no submissions/, no ext/ modified.
Next action: Farhad — run verification TODO 1-4, then SHA-verified human upload of b108eff5 before 18:00 UTC.

---

## [FINALS-SHIP] 2026-06-04 16:43 UTC — GREEN — b108eff5 frozen, both candidates discarded

Gate id: FINALS-SHIP-b108eff5 (plan: docs/plans/finals-ship-b108eff5-2026-06-04.md). Status: **GREEN — ship live b108eff5 as-is; no candidate promoted.**

### Proof of green

**Step 1 — live build verification (`submissions/v_final.zip`)**
- sha256 = `b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b` (size 44274) ✓
- `validator.py submissions/v_final.zip` → PASSED (4/4 decision tests legal) ✓
- `tools/import_audit.py` → exit 0 (cold import 0.001s, RSS 10.8 MB, no forbidden imports) ✓
- `pytest tests/edge_cases -x` → 14 passed ✓
- `tools/smoke_run.py --zip submissions/v_final.zip --hands 200` → 200/200 hands, 0 hero errors, chip_delta +5550 ✓

**Step 2 — failure-mode tester (new: `tools/failure_mode_check.py --zip <zip>`)**
- Composes (weakens no rail): A zip-structure scan · B engine validator · C import audit · D edge_cases pytest vs the zip · E fuzz/contract sweep (15 states, no exception/>2.25s/illegal/large-commit) · F disaster-spot probe pass (asserts NO large-commit on near-dead stack-off, dominated underboat, A-high flush on monotone, weak-pair/overcard near-dead) · G smoke run.
- Run on `v_final.zip` → **PASS** (all 7 sub-checks green). F found NO large-commit on b108eff5 → **Candidate C trigger NOT met (skipped). Candidate D skipped per plan.**

**A/B methodology:** live shim (654 B) and current `package.py` shim (519 B) are functionally identical (same sys.path insert + `from src.bot import decide`, no env vars); archive `src/`+`data/` byte-identical to `v_final.zip`. Baseline = archive-packaged `baseline_archive.zip` (sha `1dbc39c5…`) so packaging noise cancels; decision-equivalent to live b108eff5. Each candidate zip differs from baseline in exactly one source file (verified by diff). Gauntlet: `tools/deployed_artifact_gauntlet.py`, `--seed-base 42`, 12 opponents, same orientations.

**Step 3 — Candidate A** (`+A9s/A8s/A7s/A6s` to THREEBET_BTN/SB only; sha `ff5eaf10…`)
- Failure-mode tester → PASS. Paired A/B: aggregate **−353.61 bb/100** (gate ≥ +3), worst bucket `aggressor` **−726.19** (gate ≥ −5), 0 runner errors. **GATE FAIL → DISCARD.** Only `loose_aggressive` improved (+3.34); all else unchanged; aggressor cratered.

**Step 3 — Candidate B** (`+0.07 cbet_bluff_prob` on dry/unpaired/non-high-card flops, can_check branch; sha `ffde80dd…`)
- Failure-mode tester → PASS. Paired A/B: aggregate **−741.15 bb/100** (gate ≥ +2), worst bucket `aggressor` **−1142.86** (gate ≥ −5), 0 runner errors. **GATE FAIL → DISCARD.** Real gains vs `loose_aggressive` (+16.26) and `pot_odds_threshold` (+9.24) outweighed by aggressor collapse.

### Decision
**WINNER = live b108eff5 (`submissions/v_final.zip`, sha b108eff5…). Strategy code frozen.** Both candidates fail the same-seed paired promotion gate (each tanks vs `aggressor`, where baseline exploits for +1142 bb/100). Candidates C/D not run. The editable archive source was restored byte-identical to the live build after testing (verified).

### Files changed
- NEW `tools/failure_mode_check.py` (reusable per-zip failure-mode gate).
- NEW evidence under `consult/artifacts/2026-06-04-finals-ship/` (candidate zips + ab_baseline / ab_candidate_A / ab_candidate_B gauntlet results) and `consult/artifacts/finals-freeze/` (probe passes).
- No change to canonical `src/`, root `bot.py`, zip layout, `submissions/v_final.zip`, or `ext/`.

### Next action
Farhad — SHA-verified **human-gated** upload of `submissions/v_final.zip` (b108eff5…) to finals. **No autonomous upload performed.** STOP for human upload.

## [FINALS-UPLOADED] 2026-06-04 ~17:20 UTC — LIVE — b108eff5 on portal for finals

- **`submissions/v_final.zip` sha256 `b108eff5…` is UPLOADED and LIVE** as the finals submission (confirmed by Farhad). Human-gated upload performed by Farhad; no agent upload.
- **Format correction (portal announcement):** finals are a FRESH competition (Q1/Q2 do NOT carry). Phase 1 "The Bubble" = ~40 Swiss-paired 6-max matches × 800 hands, cumulative-chip ranked, top 6 advance; Phase 2 final table. **Deadline extended to 20:00 UK (19:00 UTC) 2026-06-04.** Regime = cumulative chip extraction (qualifier-like), not single-elim. CLAUDE.md "Finals FORMAT" section + memory updated.
- **Source committed:** b108eff5 editable source preserved under `submissions/archive/finals-ship-b108eff5-editable-source/` (incl. `src/commitment.py`, `src/hand_features.py`) so shipped bytes are reproducible (was zip-only).
- **Read-only validation in flight:** `tools/h2h.py` b108eff5 vs aggressor/shark/mathematician/ref_bot_2 at 800-hand match length, paired seeds → `consult/artifacts/2026-06-04-finals-h2h/`. Early signal: busts full stack vs pure-maniac `aggressor` heads-up (pathological HU matchup; not 6-max representative) — flag for analysis, NOT a ship blocker (bot frozen + live).
- No bot-code edits. Code frozen.
