# POKERBOT_CONTEXT_REFRESH_2026-06-03

**Purpose.** Compact, high-signal forensic context bundle for an external reviewer (no access to today's chats or the full local repo) to decide which Claude Ultracode / Claude Code / Codex `/goal` runs to launch for **failure-mode discovery and rigorous testing** before finals (2026-06-05).

**Method.** Read-only multi-agent workflow over the **main worktree** `/Users/farhad/Code/PokerBot` @ `tooling/postflop-trap-extractor-2026-05-29` (`050b058`), 2026-06-03. Eight investigators (sections 1–8) + two synthesizers (9–10); raw fragments preserved in `consult/artifacts/2026-06-03-context-refresh/`. No code edited; no benchmarks/Docker re-run. Numbers are harvested from `STATUS.md` + `consult/artifacts/**` unless marked otherwise; missing evidence is marked **NOT AVAILABLE** / **NOT RUN**.

> ### ⚠ Orchestrator reconciliation — read first; this block governs on any conflict with a section below
> The workflow's pre-fetched ground-truth payload failed to inject (`args` arrived `undefined`), so each section agent harvested lineage/metrics independently from `STATUS.md` and disk. The orchestrator then **verified the load-bearing claims by direct `shasum` / file inspection this session.** Two corrections result:
>
> 1. **The deployed Qualifier-II bot IS preserved.** Some fragments inherited a stale "`d54640e0` not preserved in `submissions/`" premise. **Corrected:** `submissions/v_qual2_ship_d54640e0.zip` exists, sha256 `d54640e0…4421` (verified; equals the STATUS-recorded deployed sha; byte-identical copy at `PokerBot-claude/submissions/v_qual2_ship.zip`). **Caveat:** it is **gitignored/untracked** and dated **06:48 today** — produced by a concurrent session, preserved as a local file only, absent from git history.
> 2. **This worktree's `src/` is a STUB, not the live bot.** Verified: `src/bot.py` is 48 lines — `decide()` returns warmup→`check`, else a fold/check `_safe_fallback`; all strategy wiring is commented out (L23–26 "Codex wires these during G2/G3"); peer modules are 7–37 lines; **no `data/*.npz` is loaded.** **Section 4 therefore maps this stub.** The actual shipped strategy (both SIMPLE and DEPLOYED) lives only inside the packaged `.zip` artifacts and other worktrees — do **not** read `src/` here as the tournament bot. (Consistent with the STATUS A3 drift note: packaged `bot.py d33484ed` ≠ current-main `f38cbb67`.)

## Bot lineage (structural invariant — every metric in this report is tagged to one of these)

| tag | artifact(s) | sha256 (short) | build | tournament role | result |
|---|---|---|---|---|---|
| **SIMPLE** | `submissions/v_final.zip` **==** `submissions/best_green.zip` (byte-identical) | `e4b4a8f1…9598` | simple hand-tuned | Qualifier I ship | **#85/300+**, +679 chip Δ/100H (top-64 cutoff ~+1,355) — **missed cut** |
| **DEPLOYED** | `submissions/v_qual2_ship_d54640e0.zip` (== `PokerBot-claude/…/v_qual2_ship.zip`) | `d54640e0…4421` | elaborate = best_green + postflop `_can_commit` fix | **Qualifier II — LIVE** (uploaded 2026-06-03) | no live result yet; portal bytes unverifiable |
| ALT | `PokerBot-claude/submissions/v_qual2_stackoff_fix.zip` | `0ec835b6…bac7` | alternate stack-off-fix candidate | not deployed | this is the "0ec835b6" mismatch some fragments flag |
| (stub) | this worktree `src/` | `bot.py f38cbb67` | fold/check scaffold | never shipped | — |

Gate snapshots (self-play ratchet, all gitignored): v0_scaffold `7df4e702`, v0_wired `0792be72`, v1_blueprint `f729b9ad`, v2_postflop `34872304`, v3_hardened `7caa4f63`, v_final_pre_x1 `5d65561e`, v_final_reaudit `9a3b812e`.

## Orchestrator-verified ground truth (npz / sizes / tests — gathered in main thread; did not reach the agents)

- **Blueprints** (`data/*.npz`, gitignored; coarse abstraction): `preflop_blueprint.npz` 2,147 B — `hands(169,)<U3`, `scores(169,)int16`, `pair`/`suited` bool, `high`/`low_rank` int8; `flop_buckets.npz` 582 B — `bucket_ids(64,)int16`; `flop_strategy.npz` 17,029 B — **`strategy(64,32,3)float32`** (64 buckets × 32 hand-bins × 3 actions). Import cost (harvested): SIMPLE 0.107 s / 33 MB (A3 06-01); DEPLOYED 0.040 s / 25 MB (QUAL2 06-03). **NB (corrected — see §5.3, verified via `unzip -l` + grep):** these npz are **vestigial scaffolding** — *neither* bot loads them (`preflop_blueprint.npz` even records `requested_iters=0`, never trained), and the **DEPLOYED zip bundles no npz at all** (its `data/` holds only `.gitkeep`). The shipped strategy is the hand-tuned tables in `src/ranges.py`; the import costs above reflect eval7 LUTs + Python tables, not npz loads.
- **`data/portal_histories/`**: 56 files / 9.3 MB, but **only 18 are real hand-history JSON — 38 are failed-download stubs** (`{"error":"Sign in required"}` / `Match not found`), including 9 truncated-UUID fragments (`-.json`, `2.json`, `46-a921-…json`; §5.4b). The on-disk pull is **partial**; STATUS's 16-match / 9,058-hand reconstruction used a fuller pull processed elsewhere.
- **Submission sizes (bytes):** v_final/best_green 28,208; **v_qual2_ship_d54640e0 18,492**; v2_postflop/v3_hardened 28,110; v_final_reaudit 28,208; v_final_pre_x1 28,534; v1_blueprint 9,289; v0_wired 5,682; v0_scaffold 5,098.
- **Tests in THIS worktree (verified `pytest --collect-only`, 2026-06-03):** `tests/edge_cases` = **4** (`test_safe_fallback.py`); `tests/integration` = **4** (`test_analyze_postflop_trap_prevalence.py`). STATUS's "25 / 48 edge tests" come from other builds/worktrees — this worktree's test surface is thin.
- **Runtime:** `.venv` = CPython 3.10.18 (sandbox-matched); host `python3` 3.14.3 (not for the bot).

---