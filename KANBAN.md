---
kanban-plugin: basic
---

## Backlog

- [ ] **G2 — Preflop blueprint** _target Day 3-4_
      Corpus: [[MCCFR-Lanctot-2009]] + [[Pluribus-Brown-Sandholm-2019]] + [[CFR-Zinkevich-2007]]
      Exit: `tools/benchmark.py --opponent template --hands 10000` reports ≥ 15 bb/100, 95% CI > 0
      - [ ] `tools/train_preflop.py` — external-sampling MCCFR over 6-max preflop tree
      - [ ] `data/preflop_blueprint.npz` saved via `numpy.savez_compressed`
      - [ ] `src/preflop_lookup.py` — eager load at module import
      - [ ] `src/ranges.py` — opening / 3-bet / 4-bet ranges by position + stack depth
      - [ ] `src/sizing.py` wired into blueprint output
      - [ ] `src/postflop.py` minimal — check-call with hand-strength threshold
      - [ ] `tools/benchmark.py` — bootstrap 95% CI
      - [ ] `submissions/v1_blueprint.zip`, engine validator PASSED
- [ ] **G3 — Postflop + Exploit overlay** _target Day 5-6_
      Corpus: [[Cepheus-Bowling-2015]] + [[Libratus-Brown-Sandholm-2017]] + [[Engine-Fullhouse]] + [[Pluribus-Brown-Sandholm-2019]]
      Exit: ≥ 15 bb/100 vs each of `template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2`
      - [ ] `tools/train_flop.py` — CFR+ over ≤200 buckets × ≤50 hand bins
      - [ ] `src/postflop.py` — flop bucket lookup
      - [ ] `src/equity.py` — eval7 MC equity ≤ 5 ms/call
      - [ ] `src/opponent_model.py` — VPIP/PFR/AF/FoldToCBet, 30-hand warmup, bounded shift
      - [ ] `src/bot.py` — route preflop/postflop + apply overlay
      - [ ] Seed overlay priors from [[Engine-Fullhouse]] per-bot exploit holes
      - [ ] `submissions/v2_postflop.zip`, engine validator PASSED
- [ ] **G4 — Hardening** _target Day 7_
      Corpus: [[Engine-Fullhouse]]
      Exit: All edge cases pass, ≤ 250 MB, cold import < 1.5 s, 10k-hand crash-free integration
      - [ ] `tools/import_audit.py` — verify thresholds across all `src/*.py`
      - [ ] `tests/edge_cases/` — side-pot, all-in, raise-below-min, raise-above-stack, timeout, malformed input, warmup
      - [ ] 10000-hand integration run vs engine harness
      - [ ] `timeout_guard.run_with_budget` fallback paths tightened
      - [ ] `submissions/v3_hardened.zip`, engine validator PASSED
- [ ] **G5 — Game-theoretic verification** _target Day 7-8_
      Corpus: [[Libratus-Brown-Sandholm-2017]] + [[Pluribus-Brown-Sandholm-2019]] + Lisý & Bowling 2017 LBR (arXiv:1612.07547)
      Exit: Ablation ≥ 3 bb/100, ratchet ≥ 3 bb/100 per prior gate, LBR ≤ 100 mbb/g preflop + ≤ 200 mbb/g aggregate
      - [ ] `tools/benchmark.py --ablate-overlay --hands 10000` over biased-opponent suite
      - [ ] `tools/benchmark.py --self-play --vs-prior` vs all gate snapshots
      - [ ] `tools/exploit_check.py` — local best-response over 20-spot suite (5 per street)
      - [ ] `tests/integration/test_biased_opponents.py` — synthetic tight/loose × passive/aggressive seats
      - [ ] Preserve `submissions/v{0..3}_*.zip` snapshots
      - [ ] `submissions/v_final.zip`, engine validator PASSED
      - [ ] `STATUS.md` ends with `## FINAL SUBMITTED`

## In Progress

- [ ] **G1 — Wired** _target Day 1-2_
      Corpus: [[Engine-Fullhouse]]
      Exit: `tools/self_play.py --opponent template --hands 100 --strict` exits 0; validator PASSED on `submissions/v0_wired.zip`; zero crashes / illegal / timeouts
      - [ ] `src/bot.py` — `decide()` returns legal action for every input including `type=="warmup"`
      - [ ] `src/timeout_guard.py` — `run_with_budget()` wall-clock tracker (threading is forbidden)
      - [ ] `tools/self_play.py` — drives N hands vs `ext/fullhouse-engine/bots/<opponent>/bot.py` via `sandbox/match.py`
      - [ ] `tests/edge_cases/test_legal_actions.py` — every code path returns action ∈ `{fold, check, call, raise, all_in}` with `amount` when raising
      - [ ] `submissions/v0_wired.zip` built, validator PASSED
      - [ ] STATUS.md G1 entry with verification output + `# Source: [[Engine-Fullhouse]]`

## Done

- [x] **G0 — Scaffold** @{2026-05-22}
      - [x] Directory tree under `~/Code/PokerBot/{docs/playbooks,src,data,tests/{unit,integration,edge_cases,property},tools,ext,submissions}`
      - [x] `ext/fullhouse-engine/` cloned from `https://github.com/uzlez/fullhouse-engine`
      - [x] `AGENTS.md`, `PROMPT.md`, `PLAN.md`, `STATUS.md`, `README.md`
      - [x] `docs/{tournament-spec,api-cheatsheet,corpus-index}.md`, `docs/playbooks/{patch-window,hardening}.md`
      - [x] `src/*.py` stubs (8 modules); `bot.py` safe-fallback returns legal action for every input
      - [x] `tools/*.py` stubs (8 scripts); `import_audit` + `package` functional
      - [x] `tests/edge_cases/test_safe_fallback.py` (4 cases pass)
      - [x] `requirements.txt` pinned to `ext/fullhouse-engine/sandbox/Dockerfile`
      - [x] `submissions/v0_scaffold.zip` — engine validator PASSED
- [x] **G0.5 — Environment + Corpus** @{2026-05-22}
      - [x] `.venv` via `uv venv --python 3.10` (Python 3.10.18)
      - [x] `eval7==0.1.7` via 2-step install (Cython<3, --no-build-isolation)
      - [x] `numpy==1.26.4`, `scipy==1.13.0`, `treys==0.1.8`, `scikit-learn==1.5.2`
      - [x] eval7 + treys functional smoke test passed (royal-flush ranks 135004160, 1)
      - [x] 7 Obsidian vault notes: `CFR-Zinkevich-2007`, `Libratus-Brown-Sandholm-2017`, `Pluribus-Brown-Sandholm-2019`, `Cepheus-Bowling-2015`, `MCCFR-Lanctot-2009`, `DeepCFR-Brown-2019`, `Engine-Fullhouse`
      - [x] `docs/corpus-index.md` rewritten with flat wikilinks
- [x] **G0.6 — Success criteria upgraded** @{2026-05-22}
      - [x] `PROMPT.md` — Codex `/goal`-compliant + directional, 3782 chars (Goal · Context · Scope · Constraints · Done when · Verification · If blocked)
      - [x] Crush margin ≥ 15 bb/100 (was 5), overlay ablation ≥ 3 bb/100, self-play ratchet ≥ 3 bb/100, LBR ≤ 100/200 mbb/g
      - [x] `AGENTS.md` — Game-theoretic frame section (blueprint + bounded overlay; abstraction = leverage; exploitability = safety metric)
      - [x] `PLAN.md` — per-gate corpus anchor; new G5 (Game-theoretic verification)
      - [x] `tools/benchmark.py` — `--ablate-overlay`, `--self-play --vs-prior` modes; `--all-templates` covers all 5 reference bots
      - [x] `tools/exploit_check.py` — reframed as LBR (Lisý & Bowling 2017, arXiv:1612.07547) over 20-spot suite
      - [x] `CLAUDE.md` symlinked to `AGENTS.md`
- [x] **G0.7 — Parallel run infrastructure** @{2026-05-22}
      - [x] `git init -b main`, tag `scaffold-baseline`, branches `main` / `claude` / `codex`
      - [x] `.gitignore` augmented: `data/*.npz`, `.mypy_cache/`, `.ruff_cache/`, swap files
      - [x] `data/.gitkeep` + `submissions/.gitkeep` so dirs survive in fresh worktrees
      - [x] `git worktree add ../PokerBot-claude claude` + `git worktree add ../PokerBot-codex codex`
      - [x] `.venv` and `ext/` symlinked from main repo into each worktree (gitignored, shared source of truth)
      - [x] Both worktrees independently GREEN on import_audit + pytest + package + validator
      - [x] Both worktrees fast-forwarded to include this checkpoint so they share a single post-setup baseline
      - [x] Launch path confirmed: **Claude Code's native `/goal`** in `PokerBot-claude`, **Codex CLI's `/goal`** in `PokerBot-codex`. `/ralph` is not part of this toolchain — persisted as feedback memory at `~/.claude/projects/-Users-farhad-Code/memory/pokerbot-uses-native-goal.md`
      - [x] Infra summary (1960 chars) copied to clipboard for downstream genius-consult

## Bugs / Known Issues

- (none yet)

## Open questions

- [ ] Hackathon registration confirmed for `3000.farhad@gmail.com` — user confirmed 2026-05-22
- [ ] Whether Codex CLI `/goal` is installed locally or whether `/ralph @PROMPT.md` is the path — user has `/ralph` skill; either works

***

%% kanban-plugin: basic %%
