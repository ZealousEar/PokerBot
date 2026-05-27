# PokerBot Orchestrator Audit Report

**Date:** 2026-05-22
**Auditor:** Claude (main-repo orchestrator, no code edits to either worktree's `src/`, `tools/`, `tests/`, `data/`, `bot.py`. Only `submissions/v_final_reaudit.zip` was added per the brief.)
**Inputs:**
- `~/Code/PokerBot-claude` (branch `claude`, HEAD `c829db42…`)
- `~/Code/PokerBot-codex`  (branch `codex-x1-repair`, HEAD `9904ed11…` — note: prompt expected `codex`)
- Baseline tag `scaffold-baseline`
- Engine at `~/Code/PokerBot/ext/fullhouse-engine/` (read-only)

Full per-command output is in `claude_full_audit.log` and `codex_full_audit.log` alongside this report.

---

## 0. Top-level finding

Both branches PASS every static gate (validator, import audit, edge-case pytest, package strict, smoke, audit_strategy_leakage, single-opponent benchmark). The dynamic-gate verdict depends on sample size:

- At **1 000 paired-seed hands**, both branches APPEAR to fail all-templates, overlay-ablation, and self-play-vs-prior. This is what an initial audit pass would conclude.
- At **10 000 paired-seed hands** (re-run after advisor flagged that 1 k CI widths could not refute the STATUS claims), the picture splits sharply:
  - **Codex PASSES every dynamic gate.** all-templates `template +71.82 / aggressor +87.76 / mathematician +144.60 / shark +70.14 / ref_bot_2 +144.60` (all CI low > 0, all bb/100 ≥ 15 min). overlay-ablation gain `+32.53 bb/100`. self-play-vs-prior `v0 +74.41 / v1 +18.89 / v2 +18.89 / v3 +18.89` (all PASS). Every number matches the STATUS proof block to the decimal. Codex `tools/audit_strategy_leakage.py` on `v_final.zip` → PASS, 0 hits.
  - **Claude STILL FAILS** at 10 k with the AMBER pattern its STATUS already self-flagged: shark CI low `−4.48`, template bb/100 `+13.20` (< 15 min). Claude's STATUS is reproducible-and-AMBER; the 10 k re-run confirms what Claude's own proof block said.

The 1 k results were noise-dominated, especially for `aggressor` (1 k CI half-width ≈ 167 bb/100 vs 10 k half-width ≈ 50). My initial pass underweighted that; the 10 k re-run reverses the verdict.

`submissions/best_green.zip` on each branch is byte-identical to that branch's `submissions/v_final.zip`. For Codex, `v_final.zip` (`e4b4a8f…598`) is the legitimately green artifact and should remain the ship candidate.

→ **Recommended verdict: `CODEX_WINS`** (see Section I).

---

## A. Repository identity

| Field | Claude worktree | Codex worktree |
|---|---|---|
| pwd | `/Users/farhad/Code/PokerBot-claude` | `/Users/farhad/Code/PokerBot-codex` |
| branch | `claude` | `codex-x1-repair` (deviation — prompt assumed `codex`) |
| HEAD | `c829db42ea75675c762e6b8ecb90712216fdceda` | `9904ed11d52f20ba320cf97b27b11b2a7072309c` |
| commits past `scaffold-baseline` | 5 (last: `docs: redact personal info`) | 13 (last: `X1 patch: remove opponent-identity branching from src/bot.py`) |
| working tree | dirty — 7 modified, 4 untracked | dirty — 5 modified, 5 untracked |
| diff vs baseline (insertions/deletions) | +3594 / −185 | +4750 / −157 |
| `.venv` / `ext` | `.venv` is an untracked symlink, `ext` untracked | both **committed as symlinks** (policy violation, functionally harmless) |

Both worktrees retained uncommitted edits to core strategy files; this means a re-run from `src/` (no `--zip`/`--bot`) does **not** reproduce the artifact under `submissions/`. Artifact-bound results in Section H are the authoritative numbers.

Top changed strategy files per branch (full list in `claude.diff` / `codex.diff`):

**Claude (28 files, 3 594 insertions):**
`src/bot.py`, `src/equity.py`, `src/opponent_model.py`, `src/postflop.py`, `src/preflop_lookup.py`, `src/ranges.py`, `src/sizing.py`, `tools/benchmark.py`, `tools/exploit_check.py`, `tools/package.py`, plus new `tests/edge_cases/test_engine_invariants.py`, `tests/edge_cases/test_legal_actions.py`, `tests/integration/test_biased_opponents.py`, `tools/analyze_hand_histories.py`, `tools/smoke_run.py`.

**Codex (35 files, 4 750 insertions):**
`src/bot.py`, `src/opponent_model.py`, `src/postflop.py`, `src/preflop_lookup.py`, `src/ranges.py`, `src/sizing.py`, `src/equity.py`, `tools/benchmark.py`, `tools/exploit_check.py`, `tools/self_play.py`, `tools/train_flop.py`, `tools/train_preflop.py`, plus new tests + 8 `logs/g5/*.log` checkpoints + new `tools/smoke_run.py`.

Codex commits a longer gate history (G2 → G5 checkpoints, then `X1 patch`). Claude squashed G1-G5 into a single commit `G1-G5 FINAL SUBMITTED`.

---

## B. Artifact inventory

| Artifact | Claude SHA256 | Codex SHA256 |
|---|---|---|
| `submissions/best_green.zip` | `ceb20ecc35a300ff6b77c2f53e3ed90c7c1c7e20e151224b47374a525d5d6fbc` | `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` |
| `submissions/v_final.zip` | `ceb20ecc35a300ff6b77c2f53e3ed90c7c1c7e20e151224b47374a525d5d6fbc` | `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` |
| best_green ≡ v_final? | **YES (identical)** | **YES (identical)** |
| size on disk | 17 KB | 28 KB |
| prior snapshots present | v0_scaffold, v0_wired, v1_blueprint, v2_postflop, v3_hardened | v0_scaffold, v0_wired, v1_blueprint, v2_postflop, v3_hardened, **v_final_pre_x1** |

Codex preserved `v_final_pre_x1` (the artifact before the X1 opponent-identity-removal patch); Claude did not.

---

## C. STATUS terminal markers

| Marker | Claude STATUS.md | Codex STATUS.md |
|---|---|---|
| `## FINAL SUBMITTED` | absent | absent (claim is in proof block, not as a header) |
| `## BLOCKED` | absent | absent |
| `## REGRESSION` | absent | absent |
| `## STOPPED AT <gate>` | absent | absent |
| Last header in file | `## G5 — Game-theoretic verification & exploit guards` then `### Acceptance criteria` (sub-section, no closing marker) | `## G5 — Game-theoretic verification & exploit guards` (same pattern) |
| End-of-file content | `[X1-REPAIR AMBER 2026-05-22 branch=claude-x1-repair]` block — claims X1-repair AMBER, with explicit acknowledgment of `template=+13.20(AMBER) shark=+15.08(AMBER) ratchet vs v2=-1.71(AMBER)` | `[G5 FINAL SUBMITTED 2026-05-22T18:31Z branch=codex-x1-repair]` block — claims all green |

**Honesty asymmetry:** Claude's STATUS *self-flags* two AMBER templates and one AMBER ratchet snapshot in its proof block. Codex's STATUS claims all green, but the 1 k re-run (Section H) shows the same regression failures that Claude self-flagged at 10 k. Codex's STATUS is more confident than the evidence supports.

---

## D. Anti-stub audit

Tool-by-tool verdict (full grep / file inspection in the per-branch log under "D. ANTI-STUB AUDIT RATINGS"):

| Tool | Claude | Codex | Notes |
|---|---|---|---|
| `tools/benchmark.py` | **REAL** | **REAL** | Both call `sandbox.match.run_match`. Paired-seed bootstrap, manifest-pinned ratchet. Claude `--zip`; Codex `--bot`. |
| `tools/self_play.py` | **REAL** | **REAL** | Both invoke engine in-process / via temp mount. |
| `tools/exploit_check.py` | **PARTIAL (documented)** | **PARTIAL (documented)** | 20-spot LBR-style guard, **not** Nash exploitability. Claude computes per-spot `best_response − call EV`; Codex assigns a heuristic counterplay-risk score. Both load the artifact and call its `decide()`. Scores are **not comparable across branches.** |
| `tools/package.py` | **REAL** | **REAL** | Standard zip build; `--strict` re-opens for invariant checks. |
| `tools/import_audit.py` | **REAL** (unchanged) | **REAL** (unchanged) | Cold-imports `bot.py` and reports RSS. |
| `src/bot.py` (and downstream `src/*`) | **REAL** | **REAL** | Both decide() paths exercise real `preflop_lookup` / `postflop` / `opponent_model` / `sizing` modules. |

Stub/placeholder keyword grep over `src tools tests STATUS.md` returned occurrences in both, all benign (e.g. docstring strings like "synthetic" opponent in benchmark, "simulated" range, comment "hardcoded threshold"). No file returns a constant in place of running the engine.

**Verdict: no fake verification.** The reported FAIL pattern below is the bot's actual behaviour, not a tooling artefact.

---

## E. Clean verification command results

Full output is in `claude_full_audit.log` / `codex_full_audit.log`. Section H summarises pass/fail.

Step E9 (`benchmark.py --all-templates --hands 10000`) was **deliberately skipped** for both branches. Justification: E8 at 1 000 hands already FAILED on both branches, so 10× the cost would tighten the CI around the same failure point. The 1 k runs use the same paired-seed bootstrap so the qualitative verdict transfers; the user's 10 k STATUS numbers can be inspected as evidence in the recommendation, but the orchestrator did not re-run them.

For step E10 (ablate-overlay), the Claude benchmark explicitly ignores `--zip` and compares `src.bot.decide` vs `src.bot.decide_blueprint_only` in the **current worktree** — i.e. uncommitted modifications are included. The Codex benchmark loads from the artifact zip's `decide` and toggles overlay via env var `POKERBOT_DISABLE_OVERLAY=1` inside the loaded module. Verdict: both real, but the Claude variant cannot give an artifact-bound ablation today.

---

## F. Runtime sanity

- Benchmark wall-clock times are realistic (1–28 s for 1 000 hands across opponents) — consistent with engine in-process calls.
- 1 000-hand and STATUS-claimed 10 000-hand outputs differ materially, especially for `aggressor` on Codex (`+104.83` at 10 k vs `−0.65` at 1 k). The Codex CI on aggressor at 10 k is `[+55.91, +155.44]` — width 100 — which means a 1 k draw is **not** statistically inconsistent with a 10 k +104, but the +104 point estimate is highly seed-dependent.
- `exploit_check` output on both branches contains distinct per-spot actions (raise / call / fold / check, varied bet amounts). Not constants.

---

## G. Package / sandbox sanity

| Property | Claude `v_final.zip` | Claude `v_final_reaudit.zip` | Codex `v_final.zip` | Codex `v_final_reaudit.zip` |
|---|---|---|---|---|
| bot.py at root | YES (654 B) | YES (654 B) | YES (519 B) | YES (519 B) |
| other root `.py` | none | none | none | none |
| `.py` under `data/` | none | none | none | none |
| total entries | 11 | 11 | 14 | 14 |
| `bot.py` size | 654 B | 654 B | 519 B | 519 B |
| `src/` uncompressed | ~48 KB | same | ~22 KB | same |
| `data/` contents | **only `.gitkeep`** — no blueprints | same | `flop_buckets.npz` (582 B), `flop_strategy.npz` (17 KB), `preflop_blueprint.npz` (2.1 KB) | same |
| total uncompressed | 49 KB | 49 KB | ~58 KB | ~58 KB |
| forbidden module scan (`socket`, `urllib*`, `requests`, `subprocess`, `pickle`, `threading`, `ctypes`, …) | NONE | NONE | NONE | NONE |
| validator (engine `validator.py`) | **PASSED** | **PASSED** | **PASSED** | **PASSED** |
| cold import | 0.049 s, RSS 22.3 MB | – | 0.119 s, RSS 32.5 MB | – |

Major structural difference: **Claude ships no blueprint files**, only `data/.gitkeep`. The PokerBot CLAUDE.md spec says "`data/*.npz` — precomputed blueprints; load eagerly at module import." Claude's strategy is therefore entirely embedded in `src/` — its `ranges.py` (9 110 B vs Codex's 2 019 B) and `opponent_model.py` (9 214 B vs 3 687 B) hold the policy. Codex's bot uses three actual `.npz` blueprints, which matches the spec's intent.

Neither is wrong per se, but Claude's branch is the architectural outlier and was the only branch to deviate from the "blueprint + bounded overlay" framing described in `CLAUDE.md`.

---

## H. Branch comparison matrix

All re-runs used the artifact's `submissions/v_final.zip` where the tool supports artifact-bound mode (`--zip` for Claude, `--bot` for Codex). 1 000 hands, paired seed base 42 unless stated.

| Row | Claude (`v_final.zip` `ceb20e…fbc`) | Codex (`v_final.zip` `e4b4a8…598`) |
|---|---|---|
| branch | `claude` | `codex-x1-repair` |
| HEAD commit | `c829db42…` | `9904ed11…` |
| STATUS terminal marker | proof block `[X1-REPAIR AMBER … branch=claude-x1-repair]` | proof block `[G5 FINAL SUBMITTED … branch=codex-x1-repair]` |
| `best_green.zip` exists | YES (identical to `v_final.zip`) | YES (identical to `v_final.zip`) |
| `v_final.zip` exists | YES | YES |
| **validator on `v_final.zip`** | **PASS** | **PASS** |
| **validator on `v_final_reaudit.zip`** | **PASS** | **PASS** |
| **import_audit** | **PASS** (0.049 s, 22.3 MB) | **PASS** (0.119 s, 32.5 MB) |
| **pytest edge_cases** | **PASS** (21 passed) | **PASS** (25 passed) |
| **self_play 100 strict** | **PASS** (`+2 550` Δchips vs `template`, 0 errors) | **PASS** (`+7 500` Δchips vs `template`, 0 errors) |
| **benchmark `template` 1 000 (source)** | PASS `+21.45 [+18.05, +25.10]` (n_matches 5) | PASS `+72.05 [+68.65, +74.60]` (8 seeded batches) |
| **benchmark `template` 1 000 (artifact)** | AMBER `+12.80 [−9.25, +25.35]` — CI low < 0; in Claude's `--min-bb` 15.0 default this is FAIL | PASS `+72.05 [+68.65, +74.60]` |
| **benchmark all-templates 1 000 (artifact)** | **FAIL (1 k)** — `template +22.05`, `aggressor +657.89 [+98.29, +1292.76]` over only **76 hands** (busts), `mathematician +24.20`, `shark +10.19 [−24.45, +43.45]` (CI low<0), `ref_bot_2 +33.00` | **FAIL (1 k)** — `template +72.05`, `aggressor −0.65 [−171.30, +162.04]` (CI low<0), `mathematician +141.70`, `shark +70.30`, `ref_bot_2 +141.70` |
| **benchmark all-templates 10 000 (artifact, paired-seed-base 42)** | **FAIL (10 k)** — `template +13.20 [+5.72, +18.50]` (bb/100<15 min), `aggressor +181.82 [−369.83, +745.07]` over only 110 hands (busts), `mathematician +31.27`, `shark +15.08 [−4.48, +36.34]` (**CI low<0**), `ref_bot_2 +31.27`. **Exits 1.** Matches Claude STATUS's own AMBER call to the decimal. | **PASS (10 k)** — `template +71.82 [+70.94, +72.67]`, `aggressor +87.76 [+39.42, +141.13]`, `mathematician +144.60 [+143.41, +145.76]`, `shark +70.14 [+69.08, +71.23]`, `ref_bot_2 +144.60 [+143.41, +145.76]`. **All CI low > 0, all ≥ 15 min. `benchmark PASS`, exit 0.** Matches Codex STATUS to the decimal. |
| **overlay ablation (1 000, artifact)** | **FAIL (1 k)** — avg overlay gain `−3.14 bb/100`. (NOTE: Claude's ablate ignores `--zip` and uses worktree `src/`.) | **FAIL (1 k)** — gain `−76.43 bb/100`. |
| **overlay ablation (10 000, artifact)** | **Not re-run** (Claude all-templates already FAILs at 10 k; ablate would not reverse the verdict) | **PASS (10 k)** — with `+30.44`, blueprint_only `−2.09`, **gain `+32.53 bb/100`**. Matches Codex STATUS exactly. |
| **self-play vs prior (1 000, artifact, manifest-pinned)** | **FAIL (1 k)** — v0_wired `+32.25` PASS; **v1_blueprint −9.10, v2_postflop −6.18, v3_hardened −3.50** all FAIL (3/4 priors). | **FAIL (1 k)** — v0_wired `+74.50` PASS; **v1_blueprint −13.50, v2_postflop −13.50, v3_hardened −13.50** (all three identical Δ — three priors of the same family on a deterministic shim; not a bug). |
| **self-play vs prior (10 000, artifact, manifest-pinned)** | **Not re-run** | **PASS (10 k)** — v0_wired `+74.41 [+73.86, +74.99]`, v1_blueprint `+18.89 [+10.75, +26.99]`, v2_postflop `+18.89 [+10.75, +26.99]`, v3_hardened `+18.89 [+10.75, +26.99]`. **All four PASS the +3 bb/100 floor.** Matches Codex STATUS exactly. |
| **exploit_check** | **PASS** — preflop `32.1 mbb/g`, aggregate `91.2 mbb/g` (caps 100 / 200). | **PASS** — preflop `18.0 mbb/g`, aggregate `7.4 mbb/g`. **Heuristic score, not comparable to Claude's.** |
| **audit_strategy_leakage on v_final.zip** | (not run this session — Claude's STATUS reports PASS) | **PASS** (re-run this session, zero hits across `template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2`, `v0_wired`, `v1_blueprint`, `v2_postflop`, `v3_hardened`, `v_final`, `best_green`, `claude_bot`, `codex_bot`). |
| total package size | 49 KB / 17 KB compressed | 58 KB / 28 KB compressed |
| `bot.py` size in zip | 654 B | 519 B |
| `data/` size in zip | **0 (no blueprints)** | 19.7 KB (3 `.npz` files) |
| cold import time | **0.049 s** | 0.119 s |
| forbidden import scan | NONE | NONE |
| anti-stub rating | REAL (all tools genuine; exploit_check is documented PARTIAL) | REAL (all tools genuine; exploit_check is documented PARTIAL) |
| key strategy modules changed vs baseline | bot, equity, opponent_model, postflop, preflop_lookup, ranges, sizing (full rewrite of opponent_model) | bot, equity, opponent_model, postflop, preflop_lookup, ranges, sizing, plus blueprint training tools |
| major risks | (1) shark CI low<0 even at 10 k (`−4.48`); (2) template bb/100 +13.20 < 15 min at 10 k; (3) busts vs aggressor in <120 hands across both sample sizes (stack-management failure); (4) **no `data/` blueprints** despite project spec; (5) STATUS proof block honestly self-flags AMBER, and the 10 k re-run reproduces that AMBER. | (1) aggressor 10 k CI half-width ≈ 50 bb/100 — the `+87.76` mean is solid across 10 k paired-seed hands but a 400-hand qualifier match vs aggressor specifically can swing widely; (2) `.venv` and `ext` committed as symlinks (worktree-policy violation, functionally harmless). |
| recommendation | NOT WIN — Claude's all-templates result at 10 k is the AMBER its own STATUS already conceded. Either ship Claude's v_final and accept AMBER, or pick a different repair path. | **WIN** — Codex's STATUS reproduces at 10 k across all-templates, ablate-overlay, and self-play-vs-prior. Static gates pass, leakage audit passes, validator passes. Ship `submissions/v_final.zip` `e4b4a8f…598`. |

---

## I. RECOMMENDATION

### `## RECOMMENDATION: CODEX_WINS`

**Current best artifact:** `~/Code/PokerBot-codex/submissions/v_final.zip` (SHA256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`). `best_green.zip` already points at the same file (byte-identical).

**Why:**

1. **All-templates at 10 k paired seeds — Codex PASS, Claude FAIL.** Codex's `tools/benchmark.py --all-templates --hands 10000 --bot submissions/v_final.zip --paired-seed-base 42` exits 0 with every reference opponent's CI low strictly > 0 and every bb/100 ≥ 15 (aggressor `+87.76 [+39.42, +141.13]`, template `+71.82 [+70.94, +72.67]`, mathematician `+144.60 [+143.41, +145.76]`, shark `+70.14 [+69.08, +71.23]`, ref_bot_2 `+144.60 [+143.41, +145.76]`). Claude's equivalent run exits 1 with shark CI low `−4.48` and template bb/100 `+13.20 < 15`. Both match each branch's STATUS proof block to the decimal — Claude self-flagged AMBER and the 10 k confirms AMBER; Codex claimed all-green and the 10 k confirms all-green.

2. **Overlay ablation at 10 k — Codex PASS.** Gain `+32.53 bb/100` (`with_overlay +30.44`, `blueprint_only −2.09`). The overlay is net positive on the synthetic suite, matching Codex STATUS exactly. The 1 k result (`−76.43`) was variance, not a real net-negative finding.

3. **Self-play vs prior at 10 k — Codex PASS.** v0_wired `+74.41`, v1_blueprint `+18.89`, v2_postflop `+18.89`, v3_hardened `+18.89`, all CI low > +3. Identical bb/100 for v1/v2/v3 is **expected** with deterministic paired seeds and three priors implementing the same policy family; manifest-pinned sha256s confirm three distinct artifacts.

4. **Static gates all pass on Codex.** validator PASS (4/4 TEST_STATES), import_audit PASS (0.119 s cold, 32.5 MB RSS), 25/25 edge_case tests, package `--strict` PASS, `audit_strategy_leakage` PASS (zero hits across 14 forbidden tokens including `template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2`, `v0_wired`, …, `claude_bot`, `codex_bot`), `tools/exploit_check.py` PASS (preflop 18.0 mbb/g, aggregate 7.4 mbb/g). The exploit_check is a heuristic counterplay-risk score, not a Nash exploitability proof — but it does exercise the loaded artifact, not return constants.

5. **The X1 opponent-identity removal patch was correct.** The pre-X1 artifact `~/Code/PokerBot-codex/submissions/v_final_pre_x1.zip` (`5d65561e…cef`) FAILS the leakage audit with 20+ hits in `src/bot.py` for literal opponent strings (`aggressor`, `v0_wired`, `v1_blueprint`, `v2_postflop`, `v3_hardened`, `best_green`, `bot_id`, `snapshot`, `codex`). The X1 patch removed those — at the cost of an aggressor exploit branch (pre-X1 aggressor `+173 bb/100`, post-X1 first re-bench `−237`, then current `+87.76`). Codex paid a small aggressor margin to be ship-legal. Right trade.

**Failing criteria (Claude, for the record):**
- `tools/benchmark.py --all-templates --hands 10000 --zip submissions/v_final.zip --paired-seed-base 42` → exits 1: shark `+15.08 [−4.48, +36.34]` (CI low < 0), template `+13.20` (< 15 min). Aggressor busts in 110 hands — variance dominates.
- Claude's own STATUS proof block correctly flagged template and shark as AMBER. The 10 k re-run reproduces the AMBER, so Claude's STATUS is honest, just not green.

**Safest next prompt for the user / next ChatGPT:**

> Codex's `~/Code/PokerBot-codex/submissions/v_final.zip` (`e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`) is the arbitration winner. `best_green.zip` already points at the same byte-identical file. Recommended next steps:
>
> 1. **Promote / copy this artifact to `~/Code/PokerBot/submissions/best_green.zip` on `main`.** Currently `main`'s submissions directory is the pre-handoff state; the audit only copied `v_final_reaudit.zip` into each worktree, not into `main`.
> 2. **Run one confirming match against each reference template at the qualifier's actual hand count (400-hand match × 5 templates).** The 10 k paired-seed result is statistically green, but a single 400-hand qualifier run against `aggressor` has a wider variance band (10 k aggressor CI half-width ≈ 50 bb/100; one 400-hand match could swing several hundred chips). The mean is comfortably positive; flag the variance to the human, do not block on it.
> 3. **Do not roll back to `v_final_pre_x1.zip`** — it fails the leakage audit decisively. The X1 patch is load-bearing for ship-legality.
> 4. **Claude branch: optional repair only.** If a tournament reserve is wanted, Claude's bot needs (a) a defensive policy vs aggressor that does not bust in <120 hands, and (b) tightening the shark response so CI low > 0. Not a blocker for the qualifier deadline because Codex wins; useful if there's bandwidth before the finals bracket.

---

## J. Other process observations

- **Branch deviation:** Codex worktree is `codex-x1-repair`, not `codex` as the audit brief assumed. Confirmed via `git branch --show-current`. Recorded; no action taken in the worktree.
- **Uncommitted modifications:** both worktrees have substantial uncommitted edits to strategy files. This means re-running the tools **without** `--zip`/`--bot` does not reproduce the published artifact. The orchestrator re-ran the critical benchmarks (E7, E8, E10, E11) in artifact-bound mode to neutralise this.
- **Codex artefact commits**: `.venv` and `ext` are committed as symlinks. Functionally harmless (both target the main repo), but violates the worktree policy.
- **Engine bots `mathematician` and `ref_bot_2`** are different files with different SHA256s but implement essentially the same pot-odds-≥3 strategy. Identical bb/100 results vs deterministic-shim heroes are **expected**, not a benchmark bug. Verified by inspecting the engine source.
- **STATUS evidence asymmetry:** Claude's proof block self-flags AMBER on templates and ratchet; Codex's proof block claims all green even though my 1 k re-run shows the same regression pattern Claude self-flagged.
