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

## 1. Executive state

**Git / worktree (canonical `~/Code/PokerBot` only).** Branch `tooling/postflop-trap-extractor-2026-05-29`; HEAD `050b058` ("status: log post-X1 audit results + R1 baseline verification"). Tree is **dirty**: 6 tracked files modified (`AGENTS.md`, `KANBAN.md`, `STATUS.md`, `docs/corpus-index.md`, `docs/playbooks/patch-window.md`, `tools/smoke_run.py`) plus ~40 untracked paths — almost all are `consult/artifacts/2026-06-0x-*`, `docs/{plans,reviews,investigations,designs}/`, `prompt-exports/`, and `data/portal_histories/`. **No `src/` edit is staged or uncommitted on canonical** (consistent with `docs/plans/overnight-thorp-v2-2026-06-03.md` §0: canonical `src/` == tag `scaffold-baseline`).

**Active "Chat 5" task:** **NOT AVAILABLE (no numbered-chat record in repo).** Searched `KANBAN.md` (In Progress = "GOAL Pass 2", a 2026-05-22 tmux item, stale), the `STATUS.md` tail, and `docs/plans/overnight-thorp-v2-2026-06-03.md` (nearest formal decomposition is plan-only work packets **WP-0…WP-6**, none executed in canonical). No `Chat 1..5` transcript set exists on disk. The real 2026-06-03 units of work are reconstructed as Workstreams A–D in sibling fragment **`02-chats.md`** (QUAL2 patch+upload; V2 overnight recon; V2 plan+critique; V2 candidate build+review).

**"Chats 1–4" completed tasks:** **NOT AVAILABLE** — same three sources, same reason (no numbered-chat ledger). See `02-chats.md` for the per-workstream breakdown.

**Latest packaged / deployed artifact + validator status — SIMPLE-vs-DEPLOYED lineage is explicit:**

| Lineage | SHA256 (head) | Artifact on disk | Role | Validator/gauntlet |
|---|---|---|---|---|
| **SIMPLE e4b4a8f1** | `e4b4a8f1…d9598` | `submissions/v_final.zip` (== `best_green.zip`, byte-identical) | **Qualifier I** ship (uploaded 2026-06-01) | A3 ship-day 2026-06-01 **GREEN**: validator 4/4, leakage PASS, import 0.107s/33.1 MB, edge **25/25**, LBR 18.0/7.4 mbb/g, smoke 200/200 Δ+14,500, 0/10 no-go (STATUS.md:602-623) |
| **DEPLOYED d54640e0** | `d54640e0…f4421` | `submissions/v_qual2_ship_d54640e0.zip` (18,492 B, mtime Jun 3 06:48) — **sha verified this session == STATUS-recorded deployed sha** | **Qualifier II** patch, **uploaded 2026-06-03** (Thorp ACTIVE, prior bot superseded) | QUAL2-PATCH 2026-06-03 **GREEN (uploaded)**: validator 4/4, import 0.040s/25 MB, edge **48/48**, smoke 200/200, LBR 32.1/81.2 mbb/g, leakage PASS (STATUS.md:626-633). **G9–G11 benchmark ladder NOT run**; only strength proxy is h2h vs baseline **−9.66 bb/100, CI crosses 0** |
| V2 be7503d3 (context) | `be7503d3…f899b4` | `PokerBot-claude/submissions/v_overnight_v2.zip` | reviewed **SHIP**, **NOT merged, NOT uploaded** | full gauntlet green in worktree; see `02-chats.md` Workstream D |

The two lineages are **different bots** built from different baselines: SIMPLE e4b4a8f1 is the canonical/release artifact (`src/bot.py` shim re-exporting the simple build); DEPLOYED d54640e0 was packaged in the **`PokerBot-claude`** worktree from the elaborate equity-driven build + a postflop-only `_can_commit` fix.

**Current highest GREEN gate (bot-tagged):** the **full G1–G11 gauntlet was GREEN only on SIMPLE e4b4a8f1** — release-branch promotion 2026-05-22 (G9 all-templates, G10 ablate +32.53, G11 self-play vs-prior; KANBAN "Done"), re-confirmed by A3 ship-day 2026-06-01. **DEPLOYED d54640e0 has NOT cleared the G9–G11 strength ladder** — it passed only the lighter qual2 gauntlet (validator/import/edge/smoke/LBR/leakage). So the bot now live in the tournament is at a *lower* verification tier than the bot it replaced.

**Known blockers / regressions:**
- **(a) v_final(SIMPLE e4b4a8f1) vs deployed(elaborate d54640e0) lineage split — REAL.** Two different bot lineages are live at once; STATUS.md:633 records verbatim that `v_final.zip` (e4b4a8f1) "is the SIMPLE bot and does NOT match deployed behavior — records/artifact lineage are inconsistent across worktrees." **Correction (verified on disk this session, supersedes the GROUND-TRUTH "not preserved" sub-clause):** d54640e0 **IS now preserved locally** at `submissions/v_qual2_ship_d54640e0.zip` (sha256 `d54640e0…f4421`, byte-matches the STATUS-recorded deployed sha). The QUAL2 STATUS entry was written when the ship build was the ephemeral `/tmp/v_ship.zip` (STATUS.md:631), so STATUS.md:633 ("exact bytes unverifiable", "does NOT match") is now **self-inconsistent with disk**. **Remaining teeth:** the d54640e0 zip is **gitignored / untracked** (on-disk only, recoverable from no commit); its **elaborate source is NOT in canonical `src/`** (canonical is scaffold-baseline — independently confirmed by blocker (c) below); the only genuinely unverifiable claim is the narrow one — the portal running byte-identical code (source not exposed by the portal).
- **(b) Qualifier I result — missed top-64.** Thorp finished **#85 / 300+** by chip Δ/100H with **+679**, vs a top-64 cutoff of **~+1,355** (STATUS.md:627; corroborated `consult/artifacts/2026-06-03-qual2-patch/FINDINGS.md`). **Tagged to SIMPLE e4b4a8f1** (the Qualifier-I upload per A3 verdict), *not* d54640e0. d54640e0 is the Qualifier-II patch with **no live result yet**.
- **(c) Thin test surface in this worktree — REAL.** Canonical `tests/edge_cases/` holds a single file `test_safe_fallback.py` = **4 test functions** (verified `grep -c "def test"` = 4; the scaffold's G0 cases). This is far below the **25/48** edge counts in STATUS: 25/25 is the SIMPLE/release build (A3, STATUS.md:611) and 48/48 is the DEPLOYED qual2 ship build (STATUS.md:631). Both higher counts come from the **`PokerBot-claude`** worktree, not canonical — direct confirmation that the strategy code (and its tests) live in `PokerBot-claude`, while canonical carries only scaffold + tooling + artifacts.

> Note: blockers (a) and (c) share one root fact — **canonical `src/` is scaffold-baseline; every elaborate/shipped bot lives in the `PokerBot-claude` worktree.** The deployed lineage is untracked, source-not-in-canonical, and never cleared the full benchmark ladder, while the active V2 plan targets a *third* base (`PokerBot-claude` + new modules).

**Exact next human decision needed:** *Before any V2 work proceeds, do we first reconcile the deployed elaborate lineage (d54640e0) into canonical and run it through the full G1–G11 gauntlet — or do we build/ship a V2 candidate (be7503d3) on top of an untracked, under-verified base whose source is not in `main`?*


---

## 2. Today's Chats 1–5 summary

**NOT AVAILABLE — the repo has no numbered chat transcripts.** There is no `Chat 1..5` artifact set anywhere on disk. The only literal "chat" reference found is `consult/artifacts/2026-06-03-overnight-recon/RECON_REPORT.md:9` ("the block **Chat 2** needs") — an informal cross-reference inside one workstream, not a numbered transcript series. I cannot map artifacts to specific chat numbers and will infer **nothing** about chat numbering.

Instead, below are the **distinct evidenced 2026-06-03 workstreams** (canonical `~/Code/PokerBot` worktree only), each labelled **"inferred workstream, not a confirmed chat number."** All timestamps are file mtimes / in-file dates; every number is tagged by bot lineage: **DEPLOYED d54640e0** (elaborate equity-driven build, uploaded to portal for Qualifier II), **SIMPLE e4b4a8f1** (`submissions/v_final.zip`, the qualifier-I artifact), and **V2 be7503d3** (`v_overnight_v2.zip`, reviewed-but-unmerged candidate).

### Lineage cross-check (verified on disk this session)
| Artifact | SHA256 (head) | Disk location | Status |
|---|---|---|---|
| DEPLOYED d54640e0 | `d54640e0…f4421` | `submissions/v_qual2_ship_d54640e0.zip` | **uploaded** to portal 2026-06-03 (STATUS.md:632) |
| qual2 stackoff fix | `0ec835b6…fbac7` | `PokerBot-claude/submissions/v_qual2_stackoff_fix.zip` | build artifact; FINDINGS.md:27 |
| V2 candidate | `be7503d3…f899b4` | `PokerBot-claude/submissions/v_overnight_v2.zip` | reviewed SHIP, **NOT uploaded, NOT merged** |
| SIMPLE e4b4a8f1 | `e4b4a8f1…d9598` | `submissions/v_final.zip` | qualifier-I artifact; "does NOT match deployed behavior" (STATUS.md:633) |

> Note (STATUS.md:633, QUAL2 entry, verbatim): *"submissions/v_final.zip (sha e4b4a8f1) is the SIMPLE bot and does NOT match deployed behavior — records/artifact lineage are inconsistent across worktrees."*

---

### Workstream A — QUAL2 stack-off-discipline patch + portal upload  *(inferred workstream, not a confirmed chat number)*
- **Objective:** Diagnose Thorp's Qualifier-I leak (finished **#85/300+**, +679 chip Δ/100H vs ~+1,355 top-64 cutoff — DEPLOYED) and ship a surgical postflop fix for Qualifier II within the patch window. Source: `consult/artifacts/2026-06-03-qual2-patch/FINDINGS.md:3-6`; STATUS.md:626-633.
- **Files changed:** `src/postflop.py` only (postflop-only fix), built from the `PokerBot-claude` elaborate baseline + the fix. Baseline preserved as `postflop_baseline.py`; patched as `postflop_patched.py`. No `src/` change landed in canonical `~/Code/PokerBot`. (FINDINGS.md:13-19,28)
- **Commands/tests run + exact pass/fail (DEPLOYED-class ship build):** engine validator **4/4 PASS**; `import_audit` cold **0.040s / 25 MB**; `edge_cases` **48/48 PASS**; smoke **200/200, 0 errors**; LBR `exploit_check` **preflop 32.1 / aggregate 81.2 mbb/g** (caps 100/200) PASS; strategy-leakage **PASS**. Regression proxies (advisor flagged crash-check only): vs templates **patched == baseline** (no-op vs passive); h2h vs baseline **−9.66 bb/100, CI crosses 0** (called an HU over-tightness artifact; game is 6-max). (STATUS.md:631; FINDINGS.md:21-24)
- **Acceptance (real field hands):** both real bust hands now **FOLD** — `8d3d` eq_strong 0.70; `Kc`-flush/4-club eq_strong 0.87. Nut `AdJd`, safe-board `AA`, big `KK`-set still **COMMIT**. (FINDINGS.md:22)
- **Strategic decisions:** Fix is postflop-only: cap re-raise at pot-sized (kill `current_bet*3` geometric blow-up); gate ≥40%-stack commitments on board-aware nuttedness via `_can_commit` (flush→nut flush or eq-vs-tight ≥0.92; paired→≥0.80; safe→≥0.55); else fold (call only if ≤15% stack). Deliberately built on `best_green.zip` canonical base **and avoided** the experimental light-3bet worktree WIP. (STATUS.md:630; FINDINGS.md:14-19)
- **Unresolved risks:** Local proxies cannot reproduce the real aggressive field, so the +EV magnitude is **inferred from real-hand replay, not measured** (FINDINGS.md:31). Deployed-bot **exact bytes unverifiable** (portal does not expose source); fix calibrated for 6-max, slightly too tight HU (STATUS.md:633). FINDINGS later **partly retracted** by Workstream B (see below).
- **Artifacts produced:** `consult/artifacts/2026-06-03-qual2-patch/{FINDINGS.md, postflop_baseline.py, postflop_patched.py, acceptance_test.py, opponents_top25_stats.{json,md}, v_qual2_stackoff_fix.zip, v_qual2_SHIP_bestgreen+fix.zip}`; `submissions/v_qual2_ship_d54640e0.zip`. Prompt-export: `prompt-exports/2026-06-03-014500-plan-qual2-stackoff-fix-review.md` (+ `…-022102-question-qual2-opponents-supplement.md`).
- **Branch/worktree:** built in `PokerBot-claude`; ship build packaged to canonical `submissions/`. Diagnosis ran on canonical (`tooling/postflop-trap-extractor-2026-05-29`).
- **Merged?** No `src/` merge to `main`. **Uploaded to the live portal 2026-06-03** (Thorp ACTIVE; prior bot superseded), live artifact **DEPLOYED d54640e0** (STATUS.md:632). Upload reversible within window.

### Workstream B — V2 overnight recon / `field_recon` (investigation-only)  *(inferred workstream, not a confirmed chat number)*
- **Objective:** Build chip-exact evidence for the V2 patch decision — answer "patch preflop tonight?" and "is opponent identity available?" via a faithful reconstruction of the marker-less portal `action_log`. (STATUS.md:636-637; RECON_REPORT.md:1-30)
- **Files changed:** `tools/field_recon.py` (new, ~770 lines), `tools/preflop_sizing_audit.py` (new). **No `src/` changes.** (STATUS.md:643)
- **Commands/tests run + exact pass/fail (reconstruction validation, DEPLOYED corpus):** 16 matches / 9,058 hands — revealed-set == non-folded **571/571 ✓**; winners == pot **9,058/9,058 ✓**; non-all-in last-street == board-len **8,801/8,801 ✓**; Thorp per-match net == declared chip_delta **11/11 ✓** (12th `d717930b` truncated finals, excluded). Thorp corpus = 12 matches / **6,915 hands**. Adversarial verification: **2/3 independent verifiers CONFIRMED** (preflop no-bug; identity available-gated). (STATUS.md:638,640; RECON_REPORT.md:54-60)
- **Findings (DEPLOYED, 12 matches / 6,915 hands):** field = **74 profiled identities** (clusters: 23 nit / 20 TAG / 9 LAG / 7 maniac / 3 station). Thorp outlier: VPIP .49 / PFR .48 / **call freq 2.2%** / AF ~26 / bust 42% / showdown-win 62%. **59 stack-offs (≥40% start stack): net −32,041, gross loss −104,407, 63% won**; origin postflop-escalation 47 / preflop-raise 7 / preflop-flat 2 / none 3. Showdown equity-at-commit: **LOST 0.059 vs WON 0.906** (near-drawing-dead, not variance). Preflop/sizing have **NO** threshold-to-stackoff bug. `game_state.players[].bot_id` **IS exposed** (game.py:66). (STATUS.md:639)
- **Strategic decisions:** **PATCH PREFLOP TONIGHT = NO** (no preflop bug; don't stack an unproven change on the proven postflop fix). **OPPONENT IDENTITY AVAILABLE = YES, but GATED — do not use** (trips `audit_strategy_leakage`; finals-overfit risk; cross-match UUID stability only inferred). (STATUS.md:641; RECON_REPORT.md:12-16)
- **Unresolved risks / reconciliation:** This workstream **partially retracted Workstream A's FINDINGS**: qual2's "16 all-ins / 12% won / −81,149" was a **conflation** — literal all-ins are only 12–13 hands (42% won, net −18k…−29k); the −81k…−96k magnitude is the **≥40%-commit class gross loss**. Direction right; magnitude/labelling off. The postflop `_can_commit` fix still targets the correct class. Cross-match UUID stability remains **inferred, not proven**. (STATUS.md:640,642; RECON_REPORT.md:13-16)
- **Artifacts produced:** `consult/artifacts/2026-06-03-overnight-recon/{RECON_REPORT.md, PREFLOP_AUDIT.md, opponent_profiles.json, field_clusters.json, large_pot_decisions.csv, stackoff_decisions.csv, showdown_spots.csv}`. (STATUS.md:643)
- **Branch/worktree:** canonical `~/Code/PokerBot` (`tooling/postflop-trap-extractor-2026-05-29`); `tools/field_recon.py` lives in canonical.
- **Merged?** N/A — investigation-only, **no runtime change**, never a ship candidate. (STATUS.md:636)

### Workstream C — Overnight Thorp V2 plan + critique (plan-only)  *(inferred workstream, not a confirmed chat number)*
- **Objective:** Produce the implementation contract for a field-aware V2 (split commitment gates, range-parser fixes, 10-archetype opponent model, `bot_id` keying), then adversarially critique it before any code. (`docs/plans/overnight-thorp-v2-2026-06-03.md:1-5`; `docs/reviews/critique-overnight-thorp-v2-2026-06-03.md:1-3`)
- **Files changed:** docs only — `docs/plans/overnight-thorp-v2-2026-06-03.md`, `docs/reviews/critique-overnight-thorp-v2-2026-06-03.md`. **Plan-only, no code/diffs** (plan §header).
- **Commands/tests run:** **NOT RUN** — explicitly "Mode: Plan-only (no code/diffs)." Six read-only recon probes are cited as establishing tree reality (plan §0); the critique spot-checks the defect map (`_can_commit` flush-before-paired at `postflop.py:88`; `expand_range_tag` `AT+`→`{ATs,ATo}`, `QJs-T9s`→`[]`; `exploit_shift` emits 4 keys, consumers read 3 more — critique:2).
- **Strategic decisions:** Resolved that the **real baseline is `PokerBot-claude/src`** (canonical `src/` is scaffold-baseline; codex `src/` is a divergent API) — all V2 edits land in `PokerBot-claude` (plan §0). Defined work packets **WP-0..WP-6** (plan §8). The plan's WP/Lane structure — not chat numbers — is the only formal decomposition; Workstream D's commits map to its Lanes A/B/C.
- **Unresolved risks (Open Questions, plan):** **Q1** which qual2 zip actually shipped (`v_qual2_stackoff_fix` ==claude vs `v_qual2_SHIP_bestgreen+fix`, different `opponent_model.py`/`sizing.py`) — gates WP-3/WP-4; **Q2** live `bot_id` stability; **Q4** live `players[].stack` + seat-stability; **Q5** `field_recon` rich-stat coverage. Critique flags regressions: dropped explicit done-when floors (≥15 bb/100 CI>0; ablation/self-play ≥3) and over-planned unused `HandFeatures` fields (critique:11,21-25).
- **Artifacts produced:** the two docs above; no zips.
- **Branch/worktree:** plan document lives in canonical `docs/plans/`; targets the `PokerBot-claude` worktree (plan §0).
- **Merged?** Docs are uncommitted on `main` (git status: both files untracked/`??`). No code to merge.

### Workstream D — V2 candidate build + Task-4 adversarial review  *(inferred workstream, not a confirmed chat number)*
- **Objective:** Execute the Workstream-C plan into a real V2 candidate and adversarially review it for SHIP/NO-SHIP. (`consult/artifacts/2026-06-03-overnight-candidate/TASK4_REVIEW_VERDICT.md:1-5`)
- **Files changed (V2 be7503d3, branch `v2-overnight-2026-06-03`):** new `src/hand_features.py`, new `src/commitment.py`, modified `src/postflop.py`, `src/opponent_model.py`; `data/field_priors.*`. Branch commits (verified): `5c7281c` "Lane A hand features and range expansion", `d05ab39` "Lane C field priors safe fallback", `b43e81b` "Lane B: split postflop commitment gates", on base `2733566` "V2 base: deployed qual2 postflop `_can_commit` fix." (git log; verdict:11-16)
- **Commands/tests run + exact pass/fail (V2 be7503d3, reproduced on the actual zip):** engine validator **4/4 PASS** (≤12 ms/state); `import_audit` cold **0.092s / 38.1 MB** PASS; strategy-leakage **PASS** (n_hits=0); `pytest tests/{edge_cases,integration,unit}` **80 passed / 0.93s**; smoke (HU) **200/200, hero_errors=[]** PASS; real **6-max** `match.py` vs 5 engine bots 2×400 hands seeds {42,7} — **HERO errors 0**, Thorp net **+35,280 / +13,050** (explicitly "not an EV claim"); LBR **preflop 32.1 / aggregate 82.4 mbb/g** (caps 100/200) PASS. (verdict:31-54)
- **Strategic decisions / verdict:** **SHIP**, **zero blockers**. Justify SHIP on the green gauntlet + sound commitment discipline + strictly-better-than-deployed — **explicitly NOT** on the EV number. Three-way fallback documented: narrower `v_qual2_stackoff_fix.zip`, or do-nothing keeps the leak live. (verdict:7-8,24-25,56-59)
- **Unresolved risks (WARNINGS, V2 be7503d3):** `hand_features.full_house_or_better` short-circuits the commit gate unconditionally → a **dominated under-boat** (e.g. `Qc9h` on `KdKsQsQd5c`) commits at ~10% equity (non-blocking: adjacent cooler, not the targeted leak class); `commitment.can_call_large` **hard-folds when `owed_frac>0.25`** ignoring pot odds (priced-in +EV call folded; bounded over-tightness); `_opponent_seat` reads only first live opponent (multiway-blind); EV magnitude **inferred from replays, not measured** — sole direct benchmark h2h vs baseline **−9.66 bb/100** (negative). Tests to add: multiway/side-pot legality, dominated-boat lock, flush-gate thresholds, overfold boundary, data-resilience. (verdict:11-22)
- **Artifacts produced:** `consult/artifacts/2026-06-03-overnight-candidate/TASK4_REVIEW_VERDICT.md`; `PokerBot-claude/submissions/v_overnight_v2.zip` (be7503d3).
- **Branch/worktree:** `v2-overnight-2026-06-03` in worktree `~/Code/PokerBot-claude` (HEAD `b43e81b`).
- **Merged?** **No.** Branch `v2-overnight-2026-06-03` is **NOT merged to `main`** (verified `git branch --merged main`), and STATUS.md has **no V2-ship/V2-upload entry** — only QUAL2 (DEPLOYED d54640e0) was uploaded. V2 be7503d3 remains a reviewed, unmerged, un-uploaded candidate as of this snapshot.

---

**Bottom line on "Chats 1–5":** the four workstreams above are the real 2026-06-03 units of work. Any "chat" granularity beyond the single informal "Chat 2" pointer in `RECON_REPORT.md:9` is **NOT AVAILABLE** in this repo (searched: `STATUS.md`, `KANBAN.md`, `docs/plans/`, `docs/reviews/`, `consult/artifacts/2026-06-03-*`, `prompt-exports/2026-06-03-*`).


---

## 3. Round 1 forensic summary

**Round 1 = Qualifier I (Swiss).** All numbers below measure the **DEPLOYED** bot, which the recon confirms was the *elaborate equity-driven* build, NOT the simple `v_final.zip` (RECON_REPORT.md L5 "Deployed source audited: `PokerBot-claude/src` (elaborate build that actually shipped)"; qual2-patch/FINDINGS.md L11 "deployed bot is the **elaborate equity-driven** version (NOT the simple `v_final.zip`)"). The SIMPLE/DEPLOYED hash→bot lineage table referenced in my assignment (`e4b4a8f1` / `d54640e0`) was **NOT PROVIDED** in this task; I therefore tag every figure as **[DEPLOYED]** with its source path and do not invent a hash mapping.

Two diagnoses exist for the same 6,915-hand dataset; **RECON_REPORT.md (2026-06-03 04:17) supersedes qual2-patch/FINDINGS.md (01:19)** because RECON is chip-exact-validated and FINDINGS' headline figures were a conflation (detailed in §3.4). I lead with RECON and present FINDINGS as the earlier, partly-corrected diagnosis.

### 3.1 Hand-history corpus / manifest (own spot-check of `data/portal_histories/`)
- **56 directory entries, 9.3 MB** (own `ls`/`du` of `data/portal_histories/`). Filenames are stable portal **UUIDs** (e.g. `0c18615c-cb01-4381-8a2b-b906eac65023.json`). The directory also holds the **truncated-fragment filenames** the spec flags — own listing shows `-.json`, `2.json`, `4.json`, `5.json`, `8.json`, `9.json`, `b.json`, `c.json`, and one UUID-fragment `46-a921-dffe25725f2a.json`; these are 27–28-byte stubs (empty payloads), not match data.
- **~16 large files (125 KB–877 KB)** carry real hands; their stems match the recon's "16 matches / 9,058 hands" (RECON_REPORT.md L54). Of these, **12 are Thorp's matches / 6,915 hands** (RECON L67, "exactly matches qual2-patch FINDINGS"). The 12 Thorp file-stems appearing in the CSVs: `0c18615c, 35272026, 3f055acd, 55a52ba6, 5ff29149, 60875d32, b03aa014, d717930b, e2272b43, f5a45e55` plus `18fc0a11` and `c5899b02` (the latter two are showdown-only in `showdown_spots.csv`). `e612f705 / 70ddeaab / ed36423c / f492174e` are additional with-hands field files (the 16-match field set).
- **Reconstruction validation [DEPLOYED, RECON_REPORT.md L56-61]:** showdown revealed-set match **571/571**; `winners` sum == `pot` **9,058/9,058**; non-all-in last-street == board length **8,801/8,801**; per-match net == declared `chip_delta` **11/11** (12th = `d717930b` "Final3", **truncated** — 100 hands stored but declares one bot holding all 60,000 chips; excluded from net aggregates only).

### 3.2 Thorp's own fingerprint & field archetypes [DEPLOYED, RECON_REPORT.md L72-92]
Thorp is an **extreme raise-or-fold outlier**: VPIP **0.49** / PFR **0.48**, **call freq 0.022 (2.2%)**, **AF ~26**, raise freq 0.57, fold 0.40, **bust rate 0.42 (42% of matches)**, **showdown-win 0.62**, big-commit rate 0.011 (RECON L90-92). Field = 74 identities, rule-clustered (RECON L78-82):

| cluster | n |
|---|---|
| nit_tight_passive | 23 |
| TAG | 20 |
| LAG | 9 |
| maniac_boombust | 7 |
| loose_passive_station | 3 |
| insufficient_data (<60 hands) | 12 |

Field is "**aggressive and boom/bust**" (top bots bust 31–64%, RECON L84-87; `qual2-patch/opponents_top25_stats.md`). Note `Bot1` is ambiguous — two distinct UUIDs share that name (RECON L88).

### 3.3 Stack-off / large-pot aggregates [DEPLOYED, RECON_REPORT.md L95-103]
- **211 large-pot hands** (final pot ≥ 5,000); **608 Thorp decisions** logged (`large_pot_decisions.csv`).
- **59 stack-offs** (≥40% start stack): **net −32,041**, **gross loss −104,407**, gross win +72,366, **won 37/59 (63%)**. Signature = wins most big pots but loses *bigger* on losers (asymmetric equity-vs-random tail, not variance).
- **Origin:** postflop-escalation **47 (−8,670)** · preflop-raise **7 (−8,086)** · preflop-flat **2 (−18,961)** · none **3 (+3,676)**. The leak is **overwhelmingly postflop** — the class the `_can_commit` fix gates.

### 3.4 Realization & the FINDINGS reconciliation [DEPLOYED]
- **Equity at commit street by outcome (RECON L113, `showdown_spots.csv`, 115 showdown hands):** WON mean **0.906**, LOST mean **0.059** → on losses Thorp was near-drawing-dead *when he committed*; this is committing dominated, not getting unlucky.
- **Raise-or-fold under-realization (RECON L117-121):** call ~2.2% forgoes pot-control / check-call lines on the medium/marginal class. Fold-side magnitude is **inferred from frequencies** — Thorp's folded cards are never revealed, so over-fold is not directly measurable (RECON L40-42, L121).
- **RECON corrects FINDINGS on TWO fronts (same bot, same dataset, different metric defs):**
  - **(a) The −81k headline.** FINDINGS.md L10 reported "**16 all-ins, 12% won, net −81,149**; 6 deep stack-offs = −73,434". RECON L105-110: chip-exact reconstruction shows **literal all-ins are only 12–13 hands, 38–42% won, net −18k to −29k**; the −81k/−96k magnitude is the **≥40%-stack commitment class measured as GROSS loss**, and "12% won" is not reproducible (Thorp wins 42% of true all-ins, 63% of ≥40% commits). Direction (postflop stack-off discipline) right; magnitude overstated by conflation.
  - **(b) The profile numbers.** FINDINGS.md L9: **AF 5.45, BUST 56%, CALL 6.4%, SCOOP 0%**. RECON: **AF ~26, bust 42%, call 2.2%**. Treat RECON's as authoritative (validated dataset); the gaps are metric-definition/subset artifacts.

### 3.5 Illegal actions / timeouts / crashes / warmup / validator (Round 1 play)
- **Hero errors = 0.** Source: qual2-patch/FINDINGS.md L10 — "`bot_errors = 0` (**not crashes**)." No illegal-action / timeout / warmup-error count is recorded *for Qualifier I live play* in either artifact beyond this. RECON_REPORT.md does not contradict it. **NOT AVAILABLE:** a per-hand timeout/validator-warning log for Round 1 (the recon replays portal `action_log`, which records no engine-side error events).
- The **smoke 200/200 (0 errors), edge 48/48, LBR preflop 32.1 / aggregate 81.2 mbb/g, validator 4/4** figures (FINDINGS.md L23; RECON L162-164) measure the **v_qual2 patch-candidate pre-upload gauntlet**, NOT Round 1 play — kept separate by design.

### 3.6 Failure-class spots [DEPLOYED]
- **Overbluff / over-commit on wet & paired boards** (the proven leak): RECON's named worst hands are postflop jams drawing dead — `2sKd` two-pair into a made straight (−11,500), `JhJs` into a flush board, `QhAc` two-pair into a set (RECON L103). Mechanism (FINDINGS L11): `eq>=0.80 → raise current_bet*3` where `eq = hand_strength = equity vs RANDOM`; on range-capped boards this re-raised into full-stack jams at ~12% real equity.
- **Multiway/wet-board:** stack-offs are essentially all heads-up at commit (every `showdown_spots.csv` stack-off row is `n_villains=1`); the wet-board failures are HU flush/straight/paired boards (see table §3.7).
- **3-bet-pot / blind-defense:** preflop-flat origin is the smallest count (2 hands) but the **worst net (−18,961)** — both are deep flats that bloated postflop (RECON L99-101; e.g. `e2272b43#56` JJ flat vs AA, `0c18615c#555` flat vs straight). The preflop audit found **no preflop/sizing threshold bug** (range-gated; all-in tag limited to `{AA,KK,AKs,AKo}` at `len(raises)>=3`; sizing caps at stack) — RECON §4 / PREFLOP_AUDIT.md.
- **River decision failures:** the dominant pattern — most large losers commit the bulk on the river (`stackoff_decisions.csv` shows the largest `river_invested` slices on the losing rows, e.g. `3f055acd#223` river 8,129; `0c18615c#81` river 4,630).
- **Overfold:** inferred only (frequencies), not directly measurable (see §3.4).

### 3.7 MANDATORY — 10 most diagnostic hands (individual)
Built by my own row-read of `showdown_spots.csv` (the only CSV with `thorp_cards` + `villain_cards` + `equity_at_commit`), cross-referenced to `stackoff_decisions.csv` for the **action / `went_all_in` / commit-street** fields. **Equity semantics:** river-commit equity is *realized* (all five cards out → 0.0/0.5/1.0); preflop/turn-commit equity is a genuine probabilistic all-in equity. Hands 1–3 are the RECON-named worst trio (RECON L103) — confirmed here against my own CSV read; hands 4–10 are my own selection of the highest-signal remaining spots.

| # | match/hand | board | Thorp cards | villain | commit street | Thorp action (stackoff CSV) | eq@commit | chip Δ | note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `3f055acd` #223 | `Kh Qs Tc Td Ah` | 2s Kd (two pair) | Jh As (Broadway) | river | river RAISE, not all-in (`went_all_in=0`, commit_frac 0.584) | **0.0** (realized) | **−11,500** | RECON worst loss; biggest single stack-off loss |
| 2 | `0c18615c` #81 | `8d Ah 2h 7c 3h` (3-flush) | Jh Js | Ad Qc | river | river RAISE, not all-in (`went_all_in=0`, frac 0.567) | **0.0** (realized) | **−7,988** | RECON-named "JhJs into flush board" |
| 3 | `3f055acd` #170 | `Qd Tc As 3h 8d` | Qh Ac (two pair) | Qs Qc (set) | river | river RAISE, not all-in (`went_all_in=0`, frac 0.53) | **0.0** (realized) | **−5,650** | RECON-named "QhAc two-pair into a set" |
| 4 | `b03aa014` #75 | `5d 2c 6s Js Th` | Kd Ad (A-high) | Td Ts (set) | river | river RAISE, not all-in (`went_all_in=0`, frac 0.619) | **0.0** (realized) | **−7,863** | own pick: jam with no pair, no draw |
| 5 | `55a52ba6` #149 | `Kh Ah 8s 9h Ac` (3-flush) | Td 6h (nothing) | 6s 6c | river | river RAISE, not all-in (`went_all_in=0`, frac 0.652) | **0.0** (realized) | **−3,710** | own pick: stack-off with air on wet board |
| 6 | `e2272b43` #56 | `As Ad 2h 8d 8h` | Jh Js | Ah Ks | preflop | preflop ALL-IN flat (`went_all_in=1`, frac 1.0, **preflop-flat**) | **0.592** (prob.) | **−8,350** | 3-bet-pot cooler; bust hand; flat vs AA |
| 7 | `0c18615c` #555 | `7s 3c Ac 4c 2s` | Ts 9c | Jd Th (straight) | preflop | preflop ALL-IN flat (`went_all_in=1`, frac 1.0, **preflop-flat**) | **0.262** (prob.) | **−10,611** | worst preflop-flat; bust; dominated all-in |
| 8 | `35272026` #143 | `9h 8s Kc Ah 7h` | Ks Qs | Ac Ad | preflop | preflop ALL-IN raise (`went_all_in=1`, frac 1.0, **preflop-raise**) | **0.162** (prob.) | **−8,966** | bust; KsQs jam into AA |
| 9 | `5ff29149` #100 | `4d 3s Tc 7d Ts` | Ad Ah | Qs Qh | river | river RAISE, not all-in (`went_all_in=0`, frac 0.546) | **1.0** (realized) | **+11,488** | biggest GAIN; correct nut stack-off (overpair holds) |
| 10 | `5ff29149` #43 | `Jd 3d 5c 4d 8c` | Qs Ac | Qc 2c | preflop | preflop ALL-IN raise (`went_all_in=1`, frac 1.0, **preflop-raise**) | **0.728** (prob.) | **+9,110** | 2nd-biggest GAIN; flips to 1.0 by river |

Field notes: `showdown_spots.csv` has **no action-verb column** — "Thorp action" is reconstructed from `stackoff_decisions.csv` (`went_all_in`, `origin`, per-street invested). The marquee **losses #1–#5 were river RAISES to showdown, NOT literal all-ins** (`went_all_in=0`), which is exactly the over-confident `current_bet*3` re-raise mechanism and the empirical basis for RECON's "−81k ≈ gross-loss-of-commit-class, not 16 literal all-ins" correction (§3.4). Biggest single GAIN = `5ff29149#100` (+11,488); biggest single LOSS = `3f055acd#223` (−11,500) — a near-symmetric pair that captures the whole thesis: same commit behaviour, opposite equity.


---

## 4. Current implementation map

**Scope:** `/Users/farhad/Code/PokerBot` (main worktree) ONLY. All file hashes below are sha256 truncated to 8 hex chars, computed live from disk this session.

### 4.0 Lineage verdict (READ FIRST) — current-main `src/` is the SCAFFOLD-BASELINE, not the shipped strategy

The presupposition that this worktree's `src/postflop.py` is "the SIMPLE or the ELABORATE build" is **false**. Verified evidence: every strategy module in current-main `src/` is an unimplemented stub from tag `scaffold-baseline`. The shipped bots (both SIMPLE `e4b4a8f1` and DEPLOYED `d54640e0`) were packaged from a *different* tree (the elaborate build), not from current-main `src/`.

Hard proof — `src/bot.py` sha256 = **`f38cbb67`**, which is byte-identical to the STATUS A3 drift hash:

> STATUS.md L615 (`2026-06-01T05:02:37Z · A3 ship-day`): "drift: packaged shim `b405d542…`, packaged `src/bot.py` `d33484ed…`, current-main `src/bot.py` `f38cbb67…` (differs — confirms do NOT repackage from main)"

Lineage table (from STATUS.md, in-scope main only):

| Bot | sha256 (8) | What it is | Source tree |
|---|---|---|---|
| SIMPLE | `e4b4a8f1` | `submissions/v_final.zip` == `best_green.zip`; Qualifier-I artifact | elaborate build (packaged `src/bot.py`=`d33484ed`), NOT current-main |
| DEPLOYED Qual-II | `d54640e0` | `best_green.zip` + postflop `_can_commit` fix only; uploaded 2026-06-03 | elaborate build + postflop fix; "exact bytes unverifiable (source not exposed)" (STATUS L633) |
| current-main `src/` | `bot.py`=`f38cbb67` | scaffold-baseline stubs (this worktree) | tag `scaffold-baseline` |

STATUS.md L633 states the inconsistency explicitly: "submissions/v_final.zip (sha e4b4a8f1) is the SIMPLE bot and does NOT match deployed behavior — records/artifact lineage are inconsistent across worktrees." The Qual-II `_can_commit` fix (STATUS L628–629) was applied to the **elaborate** `src/postflop.py` ("Root cause in elaborate src/postflop.py 'facing a bet'"), which does NOT exist in current-main — current-main `src/postflop.py` is the 25-line stub below.

**Implication:** Nothing in current-main `src/` is the running tournament strategy. To inspect deployed behavior, read the elaborate build (e.g. PokerBot-claude base `2733566` per `consult/artifacts/.../V2_PLAN.md` L7 — out of THIS scope) or unzip the deployed artifact. This section documents the scaffold that is physically present on main.

### 4.1 Import graph from `bot.py` (runtime)

Traced from `src/bot.py`. At runtime, `decide()` imports **nothing from `src/`** — the strategy wiring is commented out (L23–26):

```
# from src.preflop_lookup import lookup as _preflop_lookup
# from src.postflop import decide_postflop as _decide_postflop
# from src.timeout_guard import run_with_budget
```

So the live import graph is just: `bot.py → {os, sys}` (stdlib only). The other 7 modules (`postflop`, `preflop_lookup`, `equity`, `opponent_model`, `sizing`, `ranges`, `timeout_guard`, `__init__`) are present on disk but **not imported by the running code path**. `numpy`/`eval7` are referenced only in docstrings/TODOs; no module actually imports them yet.

Line counts: bot 48, timeout_guard 37, opponent_model 28, postflop 25, preflop_lookup 24, sizing 22, equity 11, ranges 7, `__init__` 0 (202 total).

### 4.2 File-by-file

#### `src/bot.py` (`f38cbb67`, 48 lines)
- **Purpose:** Engine entry; exports `decide(game_state) -> dict`. Shipped archive root has a shim that re-exports this.
- **Public API:** `decide(game_state: dict) -> dict` (L36); helper `_safe_fallback(game_state) -> dict` (L29). Sets `DATA_DIR` from `BOT_DATA_DIR` env or `../data` (L18–21).
- **Behavior:** warmup → `{"action":"check"}` (L41–42); else returns `_safe_fallback` (check if `can_check` else fold), wrapped in try/except → fold (L43–48). **This is a pure fold/check fallback bot — no strategy is wired.**
- **Runtime deps:** `os`, `sys` only (stdlib).
- **Data files loaded:** none (commented-out wiring; computes `DATA_DIR` but never reads it).
- **Failure modes:** none material — every path returns a legal action; non-dict input → fold; exceptions caught → fold. The risk is *strategic* (it folds/checks everything), not crash.
- **TODO/FIXME:** L23–26 commented wiring ("Codex wires these during G2/G3").
- forbidden-import scan: CLEAN

#### `src/postflop.py` (`37fcf9bb`, 25 lines)
- **Purpose (intended):** Postflop strategy — flop bucket lookup + turn/river heuristic. `# Source: [[PokerBot/Cepheus/Bowling-2015]]`.
- **Public API:** `decide_postflop(game_state: dict) -> dict` (L21).
- **Behavior:** **stub** — `check` if `can_check` else `fold` (L23–25). Module globals `_flop_buckets=None`, `_flop_strategy=None` (L17–18) — never loaded.
- **Runtime deps:** `os`, `pathlib.Path` only. (numpy intended, not imported.)
- **Data files loaded:** **none.** Intended to load `flop_buckets.npz` + `flop_strategy.npz` (both present on disk: 582 B and 17029 B) but the load is a TODO.
- **LINEAGE:** This is the **SCAFFOLD stub**, NOT the SIMPLE-bot postflop and NOT the ELABORATE build. The deployed Qual-II `_can_commit` board-aware commit gate (flush→nut/eq≥0.92, paired→≥0.80, safe→≥0.55; STATUS L629) lives in the *elaborate* `src/postflop.py` that is **absent from this worktree**. No `_can_commit`, no `current_bet*3` escalation, no `board_texture`/`_flush_suit` here — confirmed by the 25-line body.
- **Failure modes:** strategically inert (folds when it can't check). `game_state.get("can_check")` assumes dict input — would `AttributeError` on non-dict, but only ever called by wired code (none).
- **TODO/FIXME:** L16 "load flop_buckets.npz and flop_strategy.npz at import"; L22 "Placeholder — Codex implements during G3".
- forbidden-import scan: CLEAN

#### `src/preflop_lookup.py` (`2d6505fb`, 24 lines)
- **Purpose (intended):** Preflop blueprint lookup from `data/preflop_blueprint.npz`. `# Source: [[PokerBot/Pluribus/Brown-Sandholm-2019]]`.
- **Public API:** `lookup(position: str, hand: tuple, action_seq: tuple)` (L21).
- **Behavior:** **stub** — returns `None` (L24). `_blueprint=None` (L18); resolves `_BLUEPRINT_PATH = _DATA_DIR/"preflop_blueprint.npz"` (L15) but never opens it.
- **Runtime deps:** `os`, `pathlib.Path`. (numpy intended.)
- **Data files loaded:** **none.** Intended: `preflop_blueprint.npz` (present, 2147 B) — load is a TODO.
- **Failure modes:** none (always returns None → caller would fall through to blueprint-less play).
- **TODO/FIXME:** L17 "load blueprint eagerly here"; L23 "implement".
- forbidden-import scan: CLEAN

#### `src/equity.py` (`900f6cc5`, 11 lines)
- **Purpose (intended):** Monte-Carlo equity-vs-range using eval7, ≤5 ms/call, pre-warm LUTs at import.
- **Public API:** `equity_vs_range(hero, board, villain_range, trials=2000) -> float` (L9).
- **Behavior:** **stub** — `raise NotImplementedError("G3")` (L11).
- **Runtime deps:** none imported. eval7 intended (L6 TODO) but **not imported** — so no eval7 dependency is live anywhere in `src/`.
- **Data files loaded:** none.
- **Failure modes:** any call **raises** `NotImplementedError`. Safe only because nothing calls it (not wired into `bot.py`); if wired naively it would crash → engine fold.
- **TODO/FIXME:** L6 "import eval7, pre-warm LUTs"; L11 NotImplementedError.
- forbidden-import scan: CLEAN

#### `src/opponent_model.py` (`744ac64d`, 28 lines)
- **Purpose (intended):** Per-seat frequency tracker (VPIP/PFR/AF/FoldToCBet), exploit after 30-hand warmup. `# Source: [[PokerBot/OpponentModeling/Billings-Davidson-Schauenberg]]`.
- **Public API:** class `OpponentModel` (L11) with `__init__` (L14), `observe_hand(hand_event: dict)` (L18), `is_warm_for(seat_id) -> bool` (L22), `features(seat_id) -> dict` (L25). Module const `WARMUP_HANDS=30` (L8).
- **Behavior:** **stub** — only increments `self._hands_seen`; `features()` returns `{}` (L28); `is_warm_for` compares a *global* hand count, not per-seat (TODO).
- **Runtime deps:** none (pure Python).
- **Data files loaded:** none.
- **Failure modes:** none crash; `features()` returning `{}` means any consumer must handle empty dict.
- **TODO/FIXME:** L15 "per-seat dict of counters"; L27 "implement".
- forbidden-import scan: CLEAN

#### `src/sizing.py` (`0edb3f3d`, 22 lines)
- **Purpose:** Bet-sizing tree → chip amount. Discrete sizings per Pluribus action abstraction.
- **Public API:** `sizing_to_amount(sizing: str, pot: int, stack: int) -> int` (L10). Const `SIZINGS = ("third_pot","two_third_pot","pot","two_x_pot","all_in")` (L7).
- **Behavior:** **IMPLEMENTED** (the only non-stub strategy helper). Maps tag→`min(fraction·pot, stack)`; unknown tag → `raise ValueError` (L22).
- **Runtime deps:** none (pure Python).
- **Data files loaded:** none.
- **Failure modes:** `ValueError` on unknown sizing tag (defensive; caller must pass a valid tag). Integer floor division — `pot//3` truncates; for `pot<3` returns 0-chip "raise", which an engine would snap to `min_raise_to` or treat as invalid → fold. Not wired into `bot.py`, so no live exposure.
- **TODO/FIXME:** none.
- forbidden-import scan: CLEAN

#### `src/ranges.py` (`0d6da014`, 7 lines)
- **Purpose (intended):** Preflop ranges by position × stack depth → `frozenset[str]` of canonical hands.
- **Public API:** module dict `RANGES: dict = {}` (L7).
- **Behavior:** **empty** — `RANGES = {}`.
- **Runtime deps:** none.
- **Data files loaded:** none.
- **Failure modes:** none; any lookup yields KeyError/empty unless caller guards.
- **TODO/FIXME:** L6 "populate from a respected source".
- forbidden-import scan: CLEAN

#### `src/timeout_guard.py` (`bc2d818c`, 37 lines)
- **Purpose:** Advisory wall-clock budget tracker. Note (L1–7): the engine enforces the hard 2 s via its own daemon thread (`ext/fullhouse-engine/sandbox/runner.py::_call_with_timeout`); bot code cannot use `threading` (FORBIDDEN). This module only lets the pipeline check remaining budget and short-circuit.
- **Public API:** `@contextmanager deadline(seconds=SOFT_DEADLINE_S)` yielding `remaining()` (L18–22); `run_with_budget(decision_fn, fallback_fn, game_state, budget_s=SOFT) -> dict` (L25). Consts `SOFT_DEADLINE_S=1.20`, `HARD_FALLBACK_S=1.80` (L14–15).
- **Behavior:** **IMPLEMENTED.** `run_with_budget` runs `decision_fn`; if over budget OR exception → `fallback_fn` (L31–37). Uses `time.monotonic()`.
- **Runtime deps:** `time`, `contextlib.contextmanager`, `typing.Callable` (all stdlib).
- **Data files loaded:** none.
- **Failure modes:** **post-hoc only** — it checks elapsed *after* `decision_fn` returns (L33), so a `decision_fn` that hangs past 2 s is NOT interrupted by this guard (only the engine's daemon thread can). `HARD_FALLBACK_S` is defined but unused. Advisory, as documented. Not wired into `bot.py`.
- **TODO/FIXME:** none.
- forbidden-import scan: CLEAN — note this module *names* `threading` in a docstring (L4) explaining why bot code must NOT use it; no `import threading`.

#### `src/__init__.py` (`e3b0c442`, 0 lines)
- **Purpose:** Package marker. Empty (hash `e3b0c442…` is the sha256 of empty content).
- **Public API / deps / data / failures / TODO:** none.
- forbidden-import scan: CLEAN

### 4.3 Cross-reference: ground-truth `data/*.npz` vs loaders

| npz file | size (B) | mtime | Loaded by | Status |
|---|---|---|---|---|
| `preflop_blueprint.npz` | 2147 | May 22 04:26 | `preflop_lookup.py` (intended) | present, **never loaded** (TODO L17) |
| `flop_buckets.npz` | 582 | May 22 04:43 | `postflop.py` (intended) | present, **never loaded** (TODO L16) |
| `flop_strategy.npz` | 17029 | May 22 04:43 | `postflop.py` (intended) | present, **never loaded** (TODO L16) |

Assignment named `flop_strategy.npz`; on disk it is `flop_strategy.npz` (matches). `data/portal_histories/` also present (not a runtime npz; finals/recon input). No `data/finals_priors.npz` on disk yet (patch-window deliverable per CLAUDE.md).

### 4.4 Forbidden-module / sandbox-risk scan — whole `src/` tree

Live grep of `src/` for FORBIDDEN_MODULES (`socket`, `urllib*`, `requests`, `http`, `subprocess`, `multiprocessing`, `pickle`, `shelve`, `threading`, `ctypes`, `importlib`, `runpy`, `ftplib`, `smtplib`) and forbidden call patterns (`eval(`, `exec(`, `__import__(`, `compile(`, `os.system/popen/exec*/spawn*/fork/kill/remove/rename`): **0 matches** ("NONE FOUND"). Only `threading` appears as a *prose mention* in `timeout_guard.py` L4 documenting the prohibition; not an import.

**Tree-wide verdict — forbidden-import scan: CLEAN.** Caveat: this clears the *scaffold* on current-main only; it does NOT clear the deployed elaborate build (`d54640e0`), whose source is not in this worktree and is "unverifiable (source not exposed)" per STATUS.md L633. The authoritative validator gate for the shipped artifact is `ext/fullhouse-engine/sandbox/validator.py` run against the zip, logged GREEN for the SIMPLE artifact at STATUS A3 (L602–623) and for the Qual-II ship build at STATUS QUAL2-PATCH (L631, "validator 4/4 PASS").


---

## 5. Data/artifact manifest

Lineage tags used below: **SIMPLE e4b4a8f1** = qualifier-locked artifact (`best_green.zip` ≡ `v_final.zip`, identical sha256). **DEPLOYED d54640e0** = Qualifier-II patch (`v_qual2_ship_d54640e0.zip`), uploaded to portal 2026-06-03 per `STATUS.md:632`.

All sizes/sha256/shapes/gitignore/load-path facts below were harvested directly from disk in the main worktree (`shasum -a 256`, `git check-ignore`, `numpy.load`, `unzip -l`); GROUND TRUTH pre-fetch is corroborated and, where it diverges from current disk state, the divergence is flagged in the Notes.

### 5.1 `data/` manifest

| File | Size | sha256 (prefix) | npz keys → shape (dtype) | Provenance (`metadata`) | Git state | Loaded by which runtime file / how |
|---|---|---|---|---|---|---|
| `data/preflop_blueprint.npz` | 2,147 B | `74f30511…` | `hands`(169,)`<U3`; `scores`(169,)`int16`; `pair`(169,)`bool`; `suited`(169,)`bool`; `high_rank`(169,)`int8`; `low_rank`(169,)`int8`; `metadata`(3,)`<U80` | `deterministic_preflop_blueprint`; `source=Pluribus-Brown-Sandholm-2019,MCCFR-Lanctot-2009`; **`requested_iters=0`** | UNTRACKED — `.gitignore:39 data/*.npz` | **NONE.** See §5.3 — vestigial. |
| `data/flop_buckets.npz` | 582 B | `df32f635…` | `bucket_ids`(64,)`int16`; `metadata`(2,)`<U80` | `buckets=64`; `deterministic_texture_hash` | UNTRACKED (`.gitignore:39`) | **NONE.** See §5.3. |
| `data/flop_strategy.npz` | 17,029 B | `d3f8774d…` | `hand_bin_ids`(32,)`int16`; `strategy`(64,32,3)`float32`; `metadata`(2,)`<U80` | `buckets=64`; `hand_bins=32` | UNTRACKED (`.gitignore:39`) | **NONE.** See §5.3. |
| `data/portal_histories/` (dir, 56 `*.json`) | ~9.1 MB on disk; **only 18 are real** (>30 B), 38 are failed-download stubs | — | top-level dict keys: `match_id, tournament, round, status, started_at, completed_at, n_hands_target, seed, bots[], hands[]` | n/a | UNTRACKED dir (`?? data/portal_histories/`) | n/a — finals-patch corpus, not a runtime blueprint. See §5.4. |
| `data/.gitkeep` | 0 B | — | — | — | tracked | n/a |

Data-npz total = 2,147 + 582 + 17,029 = **19,758 B (~19.3 KB)**, far under the 200 MB `data/` cap.

### 5.2 `submissions/` manifest

| File | Size | sha256 (prefix) | Lineage tag | Git state | Notes |
|---|---|---|---|---|---|
| `v_qual2_ship_d54640e0.zip` | 18,492 B | `d54640e0…` | **DEPLOYED d54640e0** | UNTRACKED — `.gitignore:36 submissions/*.zip` | Live qualifier-II artifact. sha256 matches `STATUS.md:632` exactly. mtime Jun 3 06:48. |
| `best_green.zip` | 28,208 B | `e4b4a8f1…` | **SIMPLE e4b4a8f1** | UNTRACKED (`.gitignore:36`) | Read-only (`-r--r--r--`). Byte-identical sha to `v_final.zip`. |
| `v_final.zip` | 28,208 B | `e4b4a8f1…` | **SIMPLE e4b4a8f1** | UNTRACKED (`.gitignore:36`) | Read-only. ≡ `best_green.zip`. |
| `v_final_reaudit.zip` | 28,208 B | (== e4b4a8f1 by size) | SIMPLE (apparent) | UNTRACKED | Same size as SIMPLE; sha not re-hashed this pass. |
| `v_final_pre_x1.zip` | 28,534 B | NOT RUN | other | UNTRACKED | Pre-X1 snapshot. |
| `v3_hardened.zip` | 28,110 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `v2_postflop.zip` | 28,110 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `v1_blueprint.zip` | 9,289 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `v0_wired.zip` | 5,682 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `v0_scaffold.zip` | 5,098 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `.gitkeep` | 0 B | — | — | tracked | — |
| `.DS_Store` | 6,148 B | — | — | UNTRACKED | macOS cruft. |

DEPLOYED zip internals (`unzip -l`): `bot.py`(654 B root shim) + `src/*.py`(8 modules) + `data/.gitkeep`(0 B). **The shipped zip bundles NO npz** — its `data/` holds only the empty `.gitkeep`. Total uncompressed 52,234 B; `bot.py` 654 B (≪ 5 MB cap); whole zip 18 KB (≪ 250 MB total cap).

### 5.3 Which runtime file loads each npz, and how — RESOLVED: none

The assignment expected a cross-reference `preflop_lookup.py → preflop_blueprint.npz` and `postflop.py → {flop_buckets,flop_strategy}.npz`. Direct reading of both the working tree and the DEPLOYED zip shows **no such load path exists in either**:

- **Working tree** `src/preflop_lookup.py` (24 lines) and `src/postflop.py` (25 lines) are **stubs**. Loaders are nulled with TODOs:
  - `preflop_lookup.py:17-18` — `# TODO (G2): load blueprint eagerly here.` / `_blueprint = None`; `lookup(...)` returns `None` (`:24`).
  - `postflop.py:16-18` — `# TODO (G3): load flop_buckets.npz and flop_strategy.npz at import.` / `_flop_buckets = None` / `_flop_strategy = None`; `decide_postflop` returns check/fold placeholder.
  - `_DATA_DIR` is computed (`BOT_DATA_DIR` env → fallback) in both, but never used to `np.load`.
- **DEPLOYED zip** `src/preflop_lookup.py` (4,531 B — a *real* impl, unlike the working-tree stub) loads no npz: `grep` for `np.load|.npz|BOT_DATA_DIR` returns nothing; its docstring states *"Heuristic blueprint (per solver policy — hand-tuned tables ship before MCCFR training)"* and it imports ranges from `src.ranges` (pure Python: `OPEN_RANGES`, `THREEBET_VS_OPEN`, …). The shipped `postflop.py` (8,656 B) likewise has no npz load.
- A repo-wide check confirms `np.load`/`.npz` appears **only** in the two stub files' TODO comments; `src/equity.py` and the shipped `src/` tree contain zero npz loads.

**Conclusion:** `data/*.npz` are **vestigial scaffolding** from the original G2/G3 blueprint plan (`CLAUDE.md`: MCCFR preflop / CFR+ flop buckets). `preflop_blueprint.npz` even records `requested_iters=0` (never trained). Neither bot in the lineage consumes them; the DEPLOYED bot's strategy is the hand-tuned tables in `src/ranges.py`. Package-size impact of the npz is therefore moot for the shipped artifact (it bundles none) and negligible (~19 KB) for the working tree.

### 5.4 Notes / flagged gaps

**(a) Artifact-preservation gap — UPDATED vs GROUND TRUTH (partly resolved, residual remains).**
GROUND TRUTH stated the DEPLOYED bot d54640e0 is *not* preserved in `submissions/` (only `/tmp/v_ship.zip`, now gone). **That is now stale.** On disk, `submissions/v_qual2_ship_d54640e0.zip` (mtime Jun 3 06:48) exists and its sha256 is exactly `d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421` — byte-for-byte the live artifact per `STATUS.md:632`. So the binary IS preserved locally. **Residual gap:** it is **git-untracked** (`.gitignore:36 submissions/*.zip`; `git ls-files` empty; no commit history). Preservation is local-disk-only; a fresh clone or disk loss would still lose the DEPLOYED artifact. Same untracked status applies to the SIMPLE e4b4a8f1 zips.

**(b) `data/portal_histories/` — incomplete/partially-failed download confirmed.**
Of 56 `*.json`, **38 are failed-download stubs** (27–28 B) containing `{"error":"Sign in required"}` or `{"error":"Match not found"}`, not poker data. Only **18 files are real** (>30 B; up to 876 KB). Nine filenames are **truncated UUID fragments** — `-.json`, `2.json`, `4.json`, `5.json`, `8.json`, `9.json`, `b.json`, `c.json`, and `46-a921-dffe25725f2a.json` (a UUID mid-slice) — symptomatic of a broken download/rename loop that split UUIDs and persisted auth-error response bodies as files. *(Note: the Read tool and `cat` are intercepted on these paths, returning the same `{"error":"Sign in required"/"Match not found"}` strings; the file contents were read via `python json.load`, which is the authoritative source for the schema below.)*

**Schema (top-level + nested `hands[]`), documented not dumped.** Full file e.g. `c72169ca-…json` (a `status:"failed"` match, `hands:[]`) and `0c18615c-…json` (`status:"complete"`, `n_hands_target:800`, 556 hands actual):
- Top level: `match_id, tournament, round, status, started_at, completed_at, n_hands_target, seed, bots[], hands[]`.
- `bots[]` element: `bot_id, bot_name, seat, final_stack, chip_delta` (+ `bot_errors[]` on some). `"Thorp"` appears as a competing bot.
- `hands[]` element: `hand_num, street_ended, pot, community_cards[], action_log[], revealed_cards{}, winners[], my_decisions[]`.
  - `action_log[]` element: `seat, action, amount`.
  - `winners[]` element: `amount, bot_id`.

This corpus is the basis for the finals-patch priors (`tools/analyze_hand_histories.py` → `data/finals_priors.npz` per `CLAUDE.md` patch-window policy); the high stub/fragment ratio means the on-disk download is **partial** and should be treated as incomplete for prior-fitting. STATUS.md (`:638`) records a reconstruction over "16 matches / 9,058 hands" / "Thorp corpus = 12 matches / 6,915 hands" — implying a more complete pull was processed elsewhere than what currently sits in `data/portal_histories/`.


---

## 6. Verification evidence

**Bot lineage tags used below:** SIMPLE = `e4b4a8f1…598` (`submissions/v_final.zip`, qualifier-I ship artifact); DEPLOYED = `d54640e0…4421` (elaborate equity-driven build, QUAL2-PATCH live artifact uploaded 2026-06-03); OTHER = non-shipped branch numbers (e.g. Claude dual-leak-swarm losing branch, or fabricated-then-corrected values) — quarantined, never folded into the SIMPLE row.

**Freshness (read this first):** No command in this table was executed for this context refresh. This section is harvest-only: I ran `ls`/`grep`/`read` over files already on disk (read-only), nothing else — no benchmarks, no Docker/smoke, no pytest, no validator. Newest harvested **full** gauntlet = QUAL2-PATCH on the DEPLOYED bot, `STATUS.md` dated **2026-06-03**. The SIMPLE-bot benchmark / ablate / LBR / ratchet suite is **2026-05-28** (G1–G11 variance, ~6 days stale). SIMPLE ship-day re-verification = **2026-06-01** (A3). No `--collect-only` or any check was run today for this report.

**Sandbox vs local:** every row below is a **local** run (host `.venv/bin/python` 3.10), not the scored container. The engine `validator.py` is **local, AST + size only — it does not execute the bot** (`STATUS.md:150`). The single check that exercises the real Docker sandbox (`--network none --memory 768m --cpus 0.5 --read-only`) is `tools/smoke_run.py`, which is **not one of the 10 commands in this table** (see the out-of-table context block below for the harvested smoke results).

| # | Command | Last-run timestamp (source) | Key result (bot tag) | Exit/pass | Sandbox vs local | Caveats |
|---|---|---|---|---|---|---|
| 1 | `self_play --opponent template --hands 100 --strict` | 2026-05-26/27 G1-arbitration (`consult/artifacts/arbitration/codex.diff:596`) | **SIMPLE** (codex/v0_wired lineage): 100/100 hands, `bot_errors={}`, chip Δ both 0, 0.04s, seed 42 | exit 0 / PASS | local | Recorded as a G1 wiring smoke for `v0_wired.zip` (SIMPLE lineage), **not** re-run on the final artifact. OTHER (Claude losing branch, `claude.diff:473`): +2400 Δ, 100/100, 0.08s — do not attribute to SIMPLE. No A3/QUAL2 re-run of this exact command. |
| 2 | `benchmark --opponent template --hands 10000` | 2026-05-26/27 G1-arbitration (`consult/artifacts/arbitration/codex.diff:713`) | **SIMPLE**: nearest record is `self_play --opponent template --hands 10000 --strict` → 10000/10000, `bot_errors={}`, chip Δ **+721,600**, 16.46s | exit 0 / PASS | local | **No dedicated `benchmark --opponent template --hands 10000` run is recorded as such.** The `template +71.82 bb/100` headline comes from `--all-templates` (row 3), not a standalone single-opponent benchmark. The +721,600 figure is a self_play strict run, not a bb/100 benchmark. Treat row as effectively NOT RUN in benchmark form. |
| 3 | `benchmark --all-templates --hands 10000` | 2026-05-28T02:29:39Z (`consult/artifacts/2026-05-28-gauntlet-variance/STATUS_APPEND.md:6`; `STATUS.md:6,567`) | **SIMPLE**, 5-run mean±std: template +71.82±0.00, aggressor +109.72±12.06, mathematician +144.60±0.00, shark +70.43±0.16, ref_bot_2 +144.60±0.00 bb/100 | PASS (no flips across 5 runs) | local | math==ref_bot_2 identical is EXPECTED (same pot-odds policy in two files, `STATUS.md:257`). Aggressor CI wide (~100 bb/100 width); 400-hand single match can swing (`STATUS.md:259`). G3 ship-lock re-run reproduced to the decimal (`STATUS.md:327`). |
| 4 | `benchmark --ablate-overlay --hands 10000` | 2026-05-28T02:29:39Z (`STATUS.md:7,568`); ship-lock 2026-05-31 (`STATUS.md:240,327`) | **SIMPLE**: overlay gain **+32.53 bb/100** (±0.000 over 5 runs; with +30.44, blueprint_only −2.09) | PASS (≥3 bb/100 threshold) | local | **Do not confuse with OTHER values**: `STATUS.md:192` `−8.40 / −4.76` is the **Claude dual-leak-swarm losing branch**, and `+417.21` (`STATUS.md` arbitration) was **fabricated then corrected**. Shipped SIMPLE value is +32.53 (Codex won arbitration, `STATUS.md:228,240`). |
| 5 | `benchmark --self-play --vs-prior` | 2026-05-28T02:29:39Z (`STATUS.md:7,568`); ship-lock 2026-05-31 (`STATUS.md:241,327`) | **SIMPLE** ratchet: v0_wired +74.41, v1_blueprint +18.89, v2_postflop +18.89, v3_hardened +18.89 bb/100 (±0.00; manifest-pinned shas verified) | PASS (≥3 bb/100/gate) | local | Requires gitignored manifest-pinned prior zips; on release branch worked around via CLI semantics (`STATUS.md:332`). OTHER: `STATUS.md:193` `−0.87` (Claude branch) and `+4.47` (fabricated-then-corrected) — quarantined, not SIMPLE. |
| 6 | `exploit_check` (LBR) | **SIMPLE:** 2026-06-01T05:02:37Z A3 (`STATUS.md:612`) / 2026-05-28 variance (`STATUS.md:7`). **DEPLOYED:** 2026-06-03 QUAL2 (`STATUS.md:631`; `…/2026-06-03-qual2-patch/FINDINGS.md:23`) | **SIMPLE**: preflop **18.0**, aggregate **7.4** mbb/g, 20 spots, `passed=true`. **DEPLOYED**: preflop **32.1**, aggregate **81.2** mbb/g (caps 100/200) | PASS (both under caps) | local | DEPLOYED aggregate 81.2 mbb/g is the **LBR-suite** number — do **not** conflate with the 81.92 mbb/g `turn__BTN__cbet__wet_flush_draw` *cluster* leak (`STATUS.md:365`), a different metric that is coincidentally close. A3 used release-branch CLI form `--bot` (not `--zip`). |
| 7 | `import_audit` | **SIMPLE:** 2026-06-01T05:02:37Z A3 (`STATUS.md:610`); 2026-05-31 G3 (`STATUS.md:244`). **DEPLOYED:** 2026-06-03 QUAL2 (`STATUS.md:631`) | **SIMPLE**: cold import 0.107s, RSS 33.1 MB (A3) / 0.079s, 33.8 MB (G3); zero forbidden imports. **DEPLOYED**: **0.040s / 25 MB** | PASS (caps 1.5s / 400 MB) | local | Two SIMPLE timings differ by tool-copy/run (0.079–0.107s); both pass with huge margin. DEPLOYED is a different, smaller build. |
| 8 | `pytest tests/edge_cases -x` | **SIMPLE:** 2026-06-01 A3 (`STATUS.md:611`). **DEPLOYED:** 2026-06-03 QUAL2 (`STATUS.md:631`) | **SIMPLE**: **25 passed**, 0.17s. **DEPLOYED**: **48 passed** | PASS | local | **STALENESS / cross-branch divergence (flagged):** this worktree's working tree has only **1 test file** (`tests/edge_cases/test_safe_fallback.py`) with **4** `def test_` functions (verified `grep -c`), consistent with scaffold-era "4 passed" (`STATUS.md:23,44,119,157`). The **25** ran against `release/v_final-e4b4a8f1` tool/test copies (`STATUS.md:606`); the **48** ran in the elaborate worktree (QUAL2). Neither 25 nor 48 is reproducible from this checkout — different branches' test surfaces. |
| 9 | `package --output submissions/v_final.zip --strict` | **SIMPLE:** NOT re-run (policy). **DEPLOYED:** built 2026-06-03 (`STATUS.md:632`; `…/qual2-patch/FINDINGS.md:27`) | **SIMPLE**: historical artifact `e4b4a8f1…598`; **deliberately NOT repackaged** (`package.py` embeds build timestamps → SHA drifts; `STATUS.md:259,615`). **DEPLOYED**: packaged + uploaded | SIMPLE: NOT RUN (by policy) / DEPLOYED: built+shipped | local | **DEPLOYED SHA inconsistency:** live artifact `d54640e0…4421` (`STATUS.md:632`) ≠ FINDINGS artifact `0ec835b6…fbac7` (`FINDINGS.md:27`); `STATUS.md:633` states "deployed-bot exact bytes unverifiable… records/artifact lineage are inconsistent across worktrees." |
| 10 | `validator submissions/v_final.zip` | **SIMPLE:** 2026-06-01T05:02:37Z A3 (`STATUS.md:608`); G3 2026-05-31 (`STATUS.md:244`). **DEPLOYED:** 2026-06-03 QUAL2 (`STATUS.md:631`) | **SIMPLE**: ✅ PASSED **4/4** TEST_STATES, 0.000s each. **DEPLOYED**: validator **4/4** PASS | PASS | local (AST + size only) | Validator does **not** execute the bot (`STATUS.md:150`) — a 4/4 pass is not a runtime guarantee; runtime safety comes from `smoke_run` (Docker), not this command. DEPLOYED 4/4 inherits the row-9 SHA-lineage caveat (validated build ≠ confirmed-deployed bytes). |

**Other harvested verification context (not in the 10-command list, but load-bearing):**
- **G3 ship-lock full gauntlet (SIMPLE, 2026-05-31, `STATUS.md:328`):** validator 4/4, import_audit PASS, **edge_cases 25/25**, **smoke 200/200 chip_delta +14,500**, leakage PASS, exploit PASS (release CLI `--bot`). This is the SIMPLE bot's last full pre-qualifier gauntlet.
- **QUAL2 full gauntlet (DEPLOYED, 2026-06-03, `STATUS.md:631`):** validator 4/4, import 0.040s/25MB, edge 48/48, **smoke 200/200 0 errors**, LBR 32.1/81.2, **strategy-leakage PASS** (incl. no `bot_id`). Regression proxies are crash-checks only: vs-templates "patched==baseline (no-op vs passive)"; h2h vs baseline **−9.66 bb/100, CI crosses 0** (HU over-tightness artifact, game is 6-max — not a real loss signal).
- **A3 nine-command proof-of-green (SIMPLE, 2026-06-01T05:02:37Z, `STATUS.md:607-616`):** all 9 PASS, no-go 0/10. Includes the local smoke harness 200/200 chip_delta +14,500 in 3.74s.
- **Public-bot saturation (SIMPLE, 2026-05-28, `…/2026-05-28-public-saturation/SUMMARY.md`):** vladimir +3.70 [GREEN], famadeo +0.65 [GREEN], dominic −1.22 [AMBER], neel +14.69 [GREEN] bb/100; 0 hero errors across all. (Later public-prior refresh `STATUS.md:588` flagged PUBLIC_PRIORS_INVALIDATED: Toby −15.30, Mehedi −9.00 RED.)
- **Famadeo deficit retracted (SIMPLE, `STATUS.md:364`):** the overnight −21.54 bb/100 collapsed to −5.34 [CI crosses 0] at 50k hands — seed-specific bias, not a robust deficit.


---

## 7. Benchmark opponent coverage

**Lineage TAG key (verified by `shasum -a 256`, run 2026-06-03):**

| Tag | sha256 (prefix) | Artifact(s) | Role |
|---|---|---|---|
| **SIMPLE** | `e4b4a8f1…598` | `submissions/v_final.zip` **==** `submissions/best_green.zip` (byte-identical) | Qualifier I locked artifact. **Every bb/100 below is measured vs SIMPLE.** |
| **DEPLOYED** | `d54640e0…421` | `submissions/v_qual2_ship_d54640e0.zip` | Qualifier II patch, uploaded to portal 2026-06-03 (`STATUS.md` L632). |

**Lineage inconsistency (flagged, not adjudicated — belongs to another section).** `STATUS.md` L630 calls `best_green.zip` the "canonical known-good **elaborate** build," while L633 calls the byte-identical `v_final.zip` (`e4b4a8f1`) "the **SIMPLE** bot [that] does NOT match deployed behavior… records/artifact lineage are inconsistent across worktrees." Same sha, two contradictory descriptions, admitted in-record. Treat all "SIMPLE"-tagged numbers as "measured against the `e4b4a8f1` artifact" regardless of which label the prose uses.

---

### PART A — existing opponents

#### A.1 Bundled reference bots (`tools/benchmark.py --all-templates`)

Definitions: `ext/fullhouse-engine/bots/{template,aggressor,mathematician,shark,ref_bot_2}/bot.py` (read directly). `TEMPLATES` tuple at `tools/benchmark.py:31`. Result column harvested from the 5-repeat variance run `consult/artifacts/2026-05-28-gauntlet-variance/SUMMARY.md` (mirrored `STATUS.md` 2026-05-28T02:29:39Z L567) — **all vs SIMPLE `e4b4a8f1`**, paired-seed-base=42, 10k hands.

| Opponent | Path | Behavior | Exploit / failure mode tested | Result vs Thorp (bb/100, TAG) | Benchmark's own weakness |
|---|---|---|---|---|---|
| `template` | `…/template/bot.py` | Raise big only on AA/KK (`pot*3`); else check-if-free; call if `owed < 0.25*pot`; else fold. Loose-passive calling station. | Over-folds to aggression; pays off our value bets at ≤25%-pot price. | **+71.82 ± 0.00** (SIMPLE) | Pure passive — never raises; high bb/100 is "free chips," not a measure of our defense. Zero variance (±0.00) ⇒ deterministic, no signal on robustness. |
| `aggressor` | `…/aggressor/bot.py` | `random()<0.7` ⇒ raise to `min_raise*randint(2,4)`; else check/call. Maniac-ish (random sizing). | Our fold-to-aggression discipline + value-trapping vs constant barreling. | **+109.72 ± 12.06** (SIMPLE) | Randomized ⇒ highest variance of the suite. 10k CI half-width ~50–100 bb/100 (`STATUS.md` L259 "Aggressor 10 k CI is wide"); single 400-hand qualifier match against it is a coin-flip on stack-offs. NOT a true all-in shover (raises 2–4× min, not jam). |
| `mathematician` | `…/mathematician/bot.py` | Check if free; else call iff `pot/owed ≥ 3.0` (3:1); never raises. Tight-passive pot-odds caller. | Whether our sizing denies it correct odds; it can't punish thin value. | **+144.60 ± 0.00** (SIMPLE) | Never raises and never bluffs ⇒ trivially exploitable; +144.60 measures opponent passivity, not our skill. Deterministic (±0.00). |
| `shark` | `…/shark/bot.py` | Tight preflop (premiums raise 3×, medium calls in LP), position-aware postflop value bets (`pot*0.6` 40% of time in LP), tightening call thresholds. Tight-aggressive. | Closest "real player" proxy in the bundle; tests our play vs position-aware value betting. | **+70.43 ± 0.16** (SIMPLE) | Still simplistic (fixed rank set, no bluffs, `random()`-gated bets). Mild variance (±0.16). No 3-bet/4-bet tree, no board-texture logic. |
| `ref_bot_2` | `…/ref_bot_2/bot.py` | Identical logic to `mathematician` (check-if-free, call iff `pot/owed ≥ 3`, else fold). "For testing only." | Same as mathematician — a near-duplicate. | **+144.60 ± 0.00** (SIMPLE) | **Functional duplicate of `mathematician`** (number is identical for that reason). Adds no orthogonal coverage; documented "wildcard" at G0 (`STATUS.md` L30) but is just a pot-odds caller. |

> Note on values cited in the assignment ("+71.82 / +109.72 ±12.06 / +144.60 / +70.43 / +144.60"): all reproduced verbatim from `gauntlet-variance/SUMMARY.md`. An **earlier, post-X1 audit** snapshot (`STATUS.md` L187–191) records a different aggressor value `−236.59` (after the exploit branch was deleted) and `shark +69.81` — i.e. these numbers are run/build-sensitive for aggressor specifically; the +109.72 figure is the post-fix multi-run mean.

**No DEPLOYED-tag all-templates numbers exist.** `tools/benchmark.py --all-templates` was **NOT RUN** against `d54640e0`. The only relevant deployed evidence is the inference from `STATUS.md` L631: "vs templates **patched==baseline** (no-op vs passive)" — i.e. the postflop fix changes nothing against passive template bots, so DEPLOYED ≈ SIMPLE on this suite *by inference only*. Do not attribute the SIMPLE bb/100 values to DEPLOYED as measured.

#### A.2 Public-style bots

Two harvest sources: **saturation** `consult/artifacts/2026-05-28-public-saturation/SUMMARY.md` (artifact explicitly pinned to sha `e4b4a8f1…598` = **SIMPLE**, L3–4) and **drift** `consult/artifacts/2026-05-29-public-repo-drift/DRIFT_REPORT.md` (hero = `v_final.zip` `e4b4a8f1`, L11). Method: artifact-bound paired H2H, two seat orientations, bootstrap 95% CI, bb/100 over **scheduled** hands. **All vs SIMPLE.** Locally-vendored sources for 4 of them: `ext/public-bots/{dominic,famadeo,neel,vladimir}/`.

| Opponent | Source / repo | Behavior summary | Result vs Thorp (scheduled bb/100, TAG) | Verdict | Benchmark's own weakness |
|---|---|---|---|---|---|
| `vladimir` | `ext/public-bots/vladimir/`; live `vladimirfilip/…/bots/vlad` | Deep-CFR numpy shim loading `gto_strategy.npz`. | **+3.70** CI `[+2.40,+5.00]`, 400k sched (SIMPLE) | GREEN (saturation) | Only ~20,081 **actual** of 400k scheduled; **100% early-bust** ⇒ bb/100 dominated by all-in stack-off variance, not steady-state. Live drift unresolved: live repo lacks `data/gto_strategy.npz`, runs slow MC fallback; live H2H time-boxed `−37.04 actual` (DRIFT L22) = **TIMEBOXED_PARTIAL**, not a stable verdict. |
| `famadeo` | `ext/public-bots/famadeo/`; `…/bots/codex_holdem` | — | **+0.65** CI `[−1.30,+2.60]`, 200k sched (SIMPLE) | GREEN (CI crosses 0) | CI straddles zero ⇒ essentially break-even. 43,914 actual / 200k scheduled (99.5% early-bust). Live head == local snapshot ⇒ not drifted (DRIFT L23,38). |
| `dominic` | `ext/public-bots/dominic/`; live `…/bots/master` | Prior `bots/dominic` (AMBER). | **−1.22** CI `[−3.24,+0.72]`, 200k sched (SIMPLE) | **AMBER** (saturation) | **Prior flipped to RED on drift**: `bots/dominic` removed live; canonical bot is now `bots/master` → H2H **−15.30** CI `[−16.50,−14.00]` (DRIFT L25,42). The AMBER saturation number is **stale** vs the live repo. |
| `neel` | `ext/public-bots/neel/`; `…/bots/neel` (`neel-work`) | — | **+14.69** CI `[+13.50,+15.81]`, 200k sched (SIMPLE) | GREEN | 102,276 actual / 200k scheduled (85.8% early-bust). Unchanged on drift (DRIFT L24,40). Largest measured edge but still busty. |
| `toby` | live `TobyCoad/…/bots/master` (drifted; local snapshot `fc1cfb…` was AMBER `bots/dominic`-class) | Postflop trap / river value bot; "repeated early all-stack busts." | **−15.30** CI `[−16.50,−14.00]`, 200k sched; actual `−288.79` (SIMPLE) | **RED** | Drift-only evidence; DRIFT L25,30,75. Failure cluster = full river trap; hero lost −3,060,000 chips over 10,596 actual hands. ~26.5 actual hands per 500-hand orientation ⇒ near-pure stack-off dynamics. |
| `mehedi` | live `Mehedi-dev-2404/…/bots/mybot` (NEW) | Preflop pressure (fold/all-in), boom-bust. | **−9.00** CI `[−14.00,−4.00]`, 20k sched; actual `−47.78` (SIMPLE) | **RED; NEW-THREAT** | DRIFT L27,76; cluster analysis `consult/artifacts/2026-05-29-mehedi-cluster/`: classified **DIFFERENT_LEAK** from Toby (preflop pressure, not river trap). Only 3,767 actual / 20k scheduled; 100k escalation time-boxed (stayed `−9.19`). Small sample. |
| `pav` (`skantbot`) | live `Pav1602/…/bots/skantbot7.9` and `7.6` (NEW) | skantbot family (v7.9 = canonical per `play_human_hu.py`). | `7.9`: **+0.20** CI `[−2.24,+2.81]`; `7.6`: **+9.61** CI `[+6.23,+12.77]` (SIMPLE) | GREEN (not RED) | DRIFT L20–21,50–55. Only 20k scheduled / ~14–17k actual; `7.9` CI crosses 0. New family, not in prior matrix. |
| `stoppedtime` | live `stoppedtime24/…/bots/mybot` (NEW) | — | **+14.05** CI `[+9.09,+18.00]`, 20k sched; actual `+34.97` (SIMPLE) | GREEN; NEW-THREAT | DRIFT L26,65. 8,034 actual / 20k scheduled. Positive but small-sample. |

**Drift top-line verdict:** `PUBLIC_PRIORS_INVALIDATED` (DRIFT L5) — Toby flip-to-RED + Mehedi new-RED. **All public numbers are SIMPLE-tagged; none re-measured against DEPLOYED `d54640e0`.**

**Public-H2H benchmark weakness (suite-wide):** these are **heads-up** matches, but the live tournament is **6-max** — `STATUS.md` L631 explicitly attributes the deployed bot's `−9.66` HU result to a "HU over-tightness artifact; game is 6-max." Plus actual-hands ≪ scheduled-hands everywhere (high early-bust), so reported bb/100 reflects stack-off variance more than steady-state edge.

#### A.3 Self-play ratchet snapshots (`tools/benchmark.py --self-play --vs-prior`)

Snapshots present on disk: `submissions/{v0_wired,v1_blueprint,v2_postflop,v3_hardened}.zip` (all confirmed; `PRIOR_SNAPSHOTS` at `tools/benchmark.py:38-43`). Hero = SIMPLE `e4b4a8f1`. **Two conflicting recorded figures — both shown, neither adjudicated:**

| Source | Reported ratchet (bb/100 vs prior) |
|---|---|
| Release headline `STATUS.md` L241 | v0_wired **+74.41**, v1_blueprint **+18.89**, v2_postflop **+18.89**, v3_hardened **+18.89** (manifest sha-pinned) |
| Post-X1 audit `STATUS.md` L193 | **−0.87** for all three (annotated "was fabricated +4.47") |

The disagreement is in-record and unresolved here; the L193 entry flags a prior fabrication correction.

#### A.4 Adversarial / fuzz (SHADOW-CFR sparring)

**NOT RUN / AUTO-SHELVED.** SHADOW-CFR-1 (red-team Deep-CFR sparring opponent) is specified in `docs/plans/qualifier-finals-rollout-2026-05-27.md#D1` but **AUTO-SHELVED 2026-05-28** (`STATUS.md` L409: "Phase D … auto-gated off — entry requires 'B8 cleared the gauntlet'; B8 is now shelved"). No `consult/artifacts/2026-06-04-shadow-cfr/` exists. It was scoped as a sparring/validation opponent only, never a ship artifact (HARD non-shipping invariant, plan L232). Closest realized adversarial fuzz surface is the malformed-state edge fixtures (PART B §opaque_strings / mixed_casing), not an adversarial *opponent*.

---

### PART B — desired-archetype coverage MATRIX

Scope = main worktree (`/Users/farhad/Code/PokerBot`) only. Codex worktree paths cited as evidence of where coverage lives elsewhere.

| Archetype | Status (main) | Evidence path | Notes |
|---|---|---|---|
| `range_mc_pot_odds` | **MISSING** (in main) | `PokerBot-codex/tools/archetypes/range_mc_pot_odds/bot.py` (+`CALIBRATION.md`) | Exists only in codex worktree. `PokerBot/tools/archetypes` does **not exist** (verified `ls` → "No such file or directory"). Codex README: Neel-class proxy. |
| `blueprint_threshold_exploit` | **MISSING** (in main) | `PokerBot-codex/tools/archetypes/blueprint_threshold_exploit/bot.py` | Codex-only. Dominic-class proxy. |
| `risk_gated_conservative` | **MISSING** (in main) | `PokerBot-codex/tools/archetypes/risk_gated_conservative/bot.py` | Codex-only. Tight-nit / capital-preserving. |
| `stage_variant_anti_punt` | **MISSING** (in main) | `PokerBot-codex/tools/archetypes/stage_variant_anti_punt/bot.py` | Codex-only. Saroop-class proxy. |
| `monte_carlo_basic` | **MISSING** (in main) | `PokerBot-codex/tools/archetypes/monte_carlo_basic/bot.py` | Codex-only. Field-floor equity-only MC. |
| all-in / maniac pressure | **PARTIAL** | `ext/fullhouse-engine/bots/aggressor/bot.py` (measured +109.72 vs SIMPLE) | `aggressor` raises 2–4× min 70% of the time — pressure proxy, **not a pure all-in shover**. No dedicated jam-bot. `mehedi` (RED, A.2) is a live preflop-pressure/all-in proxy but external and small-sample. |
| tight-passive | **PARTIAL** | `ext/fullhouse-engine/bots/mathematician/bot.py` & `ref_bot_2/bot.py` (+144.60 vs SIMPLE) | Pot-odds callers, never raise/bluff — strong tight-passive proxies, implemented + measured. Dedicated synthetic seat is a stub (see below). |
| loose-passive | **PARTIAL** | `ext/fullhouse-engine/bots/template/bot.py` (+71.82 vs SIMPLE) | Calling-station proxy, implemented + measured. |
| tight-aggressive | **PARTIAL** | `ext/fullhouse-engine/bots/shark/bot.py` (+70.43 vs SIMPLE) | Position-aware value bettor — best TAG proxy in the bundle; no 3-bet/4-bet tree or bluffing. |
| loose-aggressive | **PARTIAL** | `ext/fullhouse-engine/bots/aggressor/bot.py` (+109.72 vs SIMPLE) | Aggressor doubles as LAG proxy (loose + aggressive). No dedicated LAG with realistic ranges. |

**Dedicated synthetic-seat status for the 4 T/L × P/A rows = stub / MISSING.** `tools/benchmark.py:35` *names* `BIASED_SUITE = ("tight_passive","loose_passive","tight_aggressive","loose_aggressive")`, but its only consumer is `--ablate-overlay`, which is an unimplemented **TODO that just prints** (`benchmark.py:74-76`: `print(f"TODO (G5): ablate overlay over {len(BIASED_SUITE)} biased seats…")`). The referenced test `tests/integration/test_biased_opponents.py` **does not exist** (verified). So: behavioral archetype coverage = PARTIAL via reference-bot proxies (above); a dedicated biased-seat implementation = absent.

**Assignment-note corrections (verified ground truth, opposite of the note):**

1. The `postflop_trap_prevalence` fixtures **EXIST in this (main) worktree** at `tests/integration/fixtures/postflop_trap_prevalence/` and are **ABSENT in `PokerBot-codex`** (verified `ls` → "No such file or directory" for the codex path). The assignment note stated the reverse.
2. Those fixtures are **NOT the five archetypes** — they are trap-replay / parser test inputs for `tests/integration/test_analyze_postflop_trap_prevalence.py`: `{toby_can_check_trap.json, toby_paired_river_fold.json, mehedi_early_bust.json, mixed_casing_stream.jsonl, opaque_strings.json, sixmax_multiway_anonymous.json}`. They exercise hand-history parsing/trap detection, not archetype opponents. The five named archetypes live as **directories** only in `PokerBot-codex/tools/archetypes/` (confirmed: 5 subdirs, each with `bot.py` + `CALIBRATION.md`).


---

## 8. Test coverage and missing tests

> Scope: main worktree at branch `tooling/postflop-trap-extractor-2026-05-29` (the on-disk tree at the time of writing). Lineage tags: **SIMPLE e4b4a8f1** = shipped `submissions/v_final.zip` sha `e4b4a8f1…598` (release branch `release/v_final-e4b4a8f1`); **DEPLOYED d54640e0** = qual2 postflop-stackoff-fix ship build (`/tmp/v_ship.zip`, the X1/qual2-patch lineage). Numbers are tagged to the build that produced them.
>
> **Output-path note:** my assignment passed the literal placeholder `undefined/08-tests.md` (the orchestrator's template variable for the report directory did not render). The intended report dir is undeterminable from disk — no context-refresh manifest or sibling fragments (`0[0-9]-*.md`) exist anywhere in the repo. This fragment is written to `consult/artifacts/2026-06-03-context-refresh/08-tests.md` (project convention for forensic artifacts). Relocate as needed.

### 8.1 What this worktree actually contains (CURRENT)

`git ls-files` for this branch tracks exactly **one** edge-case test source file and **one** integration test source file. The recursive tree:

| Path | Tests | Status |
|---|---|---|
| `tests/conftest.py` | — | Puts repo root on `sys.path` (so `from src.bot import decide` resolves). 10 lines, no assertions. |
| `tests/edge_cases/test_safe_fallback.py` | **4** | Tracked in HEAD. |
| `tests/integration/__init__.py` | — | Empty package marker. |
| `tests/integration/test_analyze_postflop_trap_prevalence.py` | **4** | Tracked in HEAD. Tests a *tool*, not the bot. |
| `tests/integration/fixtures/postflop_trap_prevalence/` | — | 6 fixture files (5 JSON/JSONL + `opaque_strings.json`). |

There is **no** `tests/unit/` and **no** `tests/property/` directory on disk in this worktree, despite `CLAUDE.md` listing `tests/{unit,integration,edge_cases,property}/` as the verification surface and STATUS.md line 13 recording their creation at scaffold. (Source: `git ls-files tests/`; recursive `ls tests/`.)

#### Ghost (stale-`.pyc`-only) edge tests — direct evidence of the thin worktree

`tests/edge_cases/__pycache__/` contains compiled `.pyc` for two test modules whose **source is absent** from this branch:
- `test_hardening_cases.cpython-310-pytest-9.0.3.pyc`
- `test_legal_actions.cpython-310-pytest-9.0.3.pyc`

`git ls-files tests/edge_cases/` returns only `test_safe_fallback.py`; `git log --diff-filter=D` shows no delete commit for either ghost file. They were compiled by a pytest run that imported test modules from *another build/worktree* (the richer SIMPLE/gauntlet trees) and left cache artifacts behind. **They do not run here** — pytest only collects from source files, which are gone. (Source: `ls tests/edge_cases/__pycache__/`; `git ls-files`; `git log --diff-filter=D`.)

### 8.2 What each present test ACTUALLY asserts

**`tests/edge_cases/test_safe_fallback.py` (4 tests)** — game states copied from `ext/fullhouse-engine/sandbox/validator.py::TEST_STATES`:

| Test | Asserts | Bot under test |
|---|---|---|
| `test_safe_fallback_checks_when_possible` | `bot._safe_fallback(flop, can_check=True)` returns exactly `{"action":"check"}` | this-tree `src.bot` |
| `test_safe_fallback_folds_facing_bet` | `bot._safe_fallback(preflop, can_check=False, amount_owed=100)` returns exactly `{"action":"fold"}` | this-tree `src.bot` |
| `test_decide_handles_warmup_without_raising` | `bot.decide({"type":"warmup"})` returns a `dict` with an `"action"` key (does not assert *which* action) | this-tree `src.bot` |
| `test_decide_returns_legal_action_on_garbage` | For `[{}, preflop, flop, {"random_garbage":True}, None, 42, []]`, `decide(...)` returns a dict whose `action ∈ {fold,check,call,raise,all_in}`; if `raise`, an `"amount"` key is present | this-tree `src.bot` |

Coverage character: this file verifies the **never-crash / always-legal contract** only. It does NOT assert strategic correctness, raise amount legality (only key *presence*), `min_raise_to` snapping, all-in vs raise distinction, or any street-specific decision. The garbage test exercises the *exception path* of `decide`, not its strategy.

**`tests/integration/test_analyze_postflop_trap_prevalence.py` (4 tests)** — exercises the **tool** `tools/analyze_postflop_trap_prevalence.py` against 6 synthetic fixtures; **zero** of these touch `src.bot` / `decide()`:

| Test | Asserts (abridged) |
|---|---|
| `..._counts_required_synthetic_families` | `total_records_found==6`, `records_successfully_parsed==6`, `postflop_action_records>=8`, `river_action_records>=5`; specific cluster keys present (`river__button__raise__…`, `river__big_blind__fold__…`); river can_check raise freqs (`unpaired_two_tone_static.raise>=2`, `wet_flush_draw.raise==1`); facing-bet fold/call freqs; three named Toby/Mehedi fingerprint counts |
| `..._reports_chip_impact_and_nonfinite_rejections` | `chip_impact_available is True`; a cluster appears in `top_clusters_by_chip_impact`; `nonfinite_amounts_rejected==1`; `"ROUNDS"` in detected top-level schema keys |
| `..._handles_opaque_string_fixture_without_crashing` | On `opaque_strings.json`: all counts 0, `top_clusters_by_frequency==[]` (no crash on unparseable input) |
| `..._text_report_contains_required_summary_fields` | Rendered text report contains `"Total records found: 6"`, `"Postflop action records parsed:"`, `"River can_check raise frequency"`, `"Toby/Mehedi-like fingerprints"` |

This is patch-window *extractor* coverage (schema-introspection, frequency tallying, non-finite rejection, opaque-input robustness) — valuable for the analyzer pipeline, but it is **not bot-behaviour coverage**.

### 8.3 DISCREPANCY — STATUS cites far richer edge suites from OTHER builds

STATUS.md records edge-test counts that **do not exist in this worktree's tree**. Tagged by lineage:

| STATUS line | Reported | Build / lineage | Present here? |
|---|---|---|---|
| 23, 44, 119, 157 | `edge_cases 4 passed` | scaffold / this-tree contract | **Yes (4)** — matches CURRENT |
| 244, 249, 328 | `edge_cases 25/25` | **SIMPLE e4b4a8f1** (`release/v_final-e4b4a8f1`, G11 / gauntlet reproduction) | **No** |
| 339, 342 | `55/55 edge_cases (52 existing + 3 new priors-consumer)`; adds `tests/edge_cases/test_priors_consumer.py (+92/-0)` | PokerBot-gauntlet release-branch build (priors-consumer) | **No** — `test_priors_consumer.py` absent |
| 631, 642 | `edge_cases 48/48` | **DEPLOYED d54640e0** ship build `/tmp/v_ship.zip` (qual2 postflop-stackoff fix) | **No** |

So STATUS reports **three** different edge counts (25, 48, 55) from three different artifact lineages; this worktree carries the original **4**-test scaffold contract plus a 4-test tool integration suite. The richer suites (`test_hardening_cases`, `test_legal_actions`, `test_priors_consumer`, and whatever brought 25→48→55) live on the SIMPLE/DEPLOYED/gauntlet branches and were never merged into `tooling/postflop-trap-extractor-2026-05-29`. The only fossil of them here is the two stray `.pyc` files in 8.1. **This worktree's bot-behaviour test surface is thin and stale relative to what shipped.** (Sources cited inline; counts harvested from STATUS.md.)

> Caveat: the 25/48/55 suite *contents* are not on disk in this tree, so the per-test assertions of those richer suites cannot be inspected here — only their pass-counts are harvestable from STATUS.md. The missing-test matrix below is judged against what is **provably present in this worktree**, and notes where STATUS evidence suggests another build already covers a row.

### 8.4 Relevant `tools/` (one line each)

All under `tools/`; first line of each module docstring (Source: docstring head of each file). Most invoke the real engine and/or Docker — out of scope to run here.

| Tool | One-line purpose |
|---|---|
| `self_play.py` | Runs N hands of our bot vs a named opponent via `match.py`; reports crashes, illegal actions, timeouts. |
| `benchmark.py` | bb/100 vs reference opponents (G2/G3) or GT verification suites (G5) with bootstrap 95% CIs. (Docstring also self-describes as a historical gate stub — see `public_saturation` note.) |
| `exploit_check.py` | Local best-response (LBR, Lisý & Bowling 2017) exploitability estimate over a fixed 20-spot suite; regression guard (caps 100/200 mbb/g). |
| `import_audit.py` | Verifies cold-start time, RSS, and absence of forbidden imports across **every** `.py` in `src/` (validator only AST-scans `bot.py`). |
| `package.py` | Builds the submission zip (root `bot.py` shim re-exporting `decide`) and validates structure. |
| `smoke_run.py` | Exercises a submission inside the real engine **sandbox container** vs a reference bot for a few hands; catches timeout/OOM/missing-data/slow-import the AST validator cannot. |
| `replay.py` | Replays a hand-history JSON through `src.bot.decide` for reproducible diagnosis (patch-window). |
| `h2h.py` | Paired-seed head-to-head between two bot artifacts (seats swapped); reports A's per-match BB delta + bootstrap CI. |
| `field_recon.py` | Investigation-only: reconstructs hand state from public portal histories in `data/portal_histories/`. |
| `audit_strategy_leakage.py` | Scans packaged strategy source for identity-leakage strings (opponent labels, artifact/branch names, seed-like values). |
| `analyze_postflop_trap_prevalence.py` | Patch-window postflop-trap extractor; schema-introspects JSON/JSONL histories, emits field-level Toby/Mehedi signals (tooling only). |
| `preflop_sizing_audit.py` | Investigation-only: checks whether PREFLOP/SIZING code shares the "threshold-to-stackoff" bug fixed in qual2-patch. |
| `b8_gauntlet.py` | Single-command gauntlet for candidate zips; orchestrates existing verification tools as subprocesses, emits STATUS-style block. |
| `public_saturation.py` | Public-bot saturation sweeps for artifact-bound H2H evidence; drives the engine directly (notes `benchmark.py` is "still a historical gate stub in this tree"). |
| `qualifier_pods.py` | Estimates 400-hand qualifier chip-delta distributions for six-max pods via the sandbox match runner. |
| `train_flop.py` | Offline flop bucket + strategy generation → `data/flop_buckets.npz` (training, unrestricted compute). |
| `train_preflop.py` | Offline preflop blueprint generation → `data/preflop_blueprint.npz` (`numpy.savez_compressed`). |

`field_recon` appears twice in the assignment list; it is a single tool, listed once above.

### 8.5 MISSING-TEST MATRIX (ranked by tournament risk)

Risk = consequence × likelihood at the 2 s/decision, fold-on-exception sandbox where an illegal/late action is silently converted to a fold (chips lost). "Covered here" = provably exercised by a test in *this* worktree. "STATUS-elsewhere" = a richer SIMPLE/DEPLOYED/gauntlet build plausibly covers it but the source is not in this tree (see 8.3 caveat).

| # | Capability under test | Risk | Covered in THIS worktree? | Justification |
|---|---|---|---|---|
| 1 | Raise below `min_raise_to` / above stack / **equal-to-call** ambiguity (legal amount, snap-up, all-in vs raise-to-stack) | **High** | **No** (garbage test asserts only that an `"amount"` key *exists*, never its legality vs `min_raise_to`/stack) | An illegal `amount` → runner converts to fold → direct chip loss every occurrence. Validator's `VALID_ACTIONS` checks shape, not numeric legality. STATUS-elsewhere: likely `test_legal_actions` (ghost `.pyc`). |
| 2 | Malformed / partial `game_state` (missing keys, wrong types, truncated dict) beyond the 7 garbage inputs already tried | **High** | **Partial** — `test_decide_returns_legal_action_on_garbage` covers `{}`, `None`, `42`, `[]`, `{"random_garbage":True}` | Real sandbox feeds engine-shaped dicts with occasional missing fields; the 5 garbage inputs are coarse. Missing: dicts with *some* required keys absent (e.g. `your_stack` missing, `community_cards` malformed). |
| 3 | All-in & **side-pot** states (multiple all-ins, capped pots, uneven stacks) | **High** | **No** | Side-pot math errors mis-size raises → illegal action or value leak; common in 400-hand qualifier pods with short stacks. No fixture or decide-test exercises a side-pot state. |
| 4 | Timeout under expensive equity call (decision > 2 s when equity/Monte-Carlo path is hit) | **High** | **No** | A single >2 s decision = forced fold. `timeout_guard.py` exists (per `CLAUDE.md` map) but **no test asserts the guard fires** or that worst-case equity stays under budget. smoke_run catches it only at runtime in Docker (not run here). |
| 5 | Warmup exception (`{"type":"warmup"}` raising, or blueprint load failing) | **Med** | **Yes (partial)** — `test_decide_handles_warmup_without_raising` asserts a dict-with-`action` is returned | Covered for the no-raise contract only; does NOT assert blueprints actually loaded, nor that a *broken* warmup payload is survived. Warmup has a 30 s budget so timeout risk is low; correctness-of-load is untested. |
| 6 | Missing / empty / contradictory legal actions (`can_check` False with `amount_owed` 0; check requested when illegal) | **Med** | **Partial** — `_safe_fallback` check-vs-fold branch tested for two consistent states | No test for *contradictory* inputs (e.g. `can_check:True` but `current_bet>0`). `_safe_fallback` is the right place; only the happy path is asserted. |
| 7 | River bluff-catcher thresholds (call/fold at marginal showdown equity) | **Med** | **No** | Strategic-strength row; mis-set threshold bleeds EV but never crashes → lower ops risk, real chip-EV risk. The trap-extractor fixtures describe river fold/call *populations*, but assert the **tool**, not `decide`. |
| 8 | Wet-board equity realization (draw-heavy flop/turn equity vs made hands) | **Med** | **No** | EV/correctness, not legality. Fixture taxonomy includes `wet_flush_draw`, but only as extractor input — `equity.py` realization is untested against `decide`. |
| 9 | Multiway pots (3+ live players; range/equity adjustments vs heads-up) | **Med** | **No** | Qualifier is 6-max; multiway is the common case. A `sixmax_multiway_anonymous.json` fixture exists but feeds the *extractor* test, not bot decisions. STATUS line 631 notes HU-tuning artifacts ("game is 6-max"), underscoring the gap. |
| 10 | Package structure & forbidden imports (root `bot.py` only, no `.py` in `data/`, no forbidden modules, size caps) | **Med** | **No (unit)** — enforced operationally by `tools/package.py --strict`, `import_audit.py`, the engine `validator.py`, and the `.githooks/pre-commit` hook, but **no pytest test** asserts it | Catastrophic if it regresses (whole submission rejected), but multiple non-pytest guards already cover it, so residual risk is Med not High. Not in the `pytest tests/edge_cases` surface. |
| 11 | Blind-defense & 3-bet-pot pressure (BB defend freq, 4-bet/jam thresholds) | **Med/Low** | **No** | Strategic EV row; fingerprint `mehedi_preflop_pressure_early_bust_like` is extractor-only. No `decide` test for preflop pressure spots. |
| 12 | Deterministic seed reproducibility (same seed → identical action stream) | **Low** | **No** | Harness/QA property, not a sandbox-scored path. `h2h.py`/`benchmark.py` rely on paired seeds; a regression here corrupts *measurement*, not the shipped bot. No test pins it. |
| 13 | Bootstrap CI correctness (the CI math in `benchmark.py`/`h2h.py`) | **Low** | **No** | Affects trust in acceptance numbers, not bot legality/EV. Per benchmark-variance policy the CIs gate decisions; an off-by math bug would mislead, but it is meta-tooling. No test covers the estimator. |

#### Cross-reference summary (already-covered vs genuinely missing, this worktree)

- **Already (partly) covered here:** warmup-no-raise (#5), garbage/malformed-input legality contract (#2, partial), `_safe_fallback` check-vs-fold for *consistent* states (#6, partial). All via `test_safe_fallback.py`.
- **Genuinely missing here, High risk:** raise-amount numeric legality / equal-to-call (#1), side-pot/all-in states (#3), equity-call timeout-guard (#4). These are the legality/ops failures that the fold-on-exception runner converts straight into chip loss and are the priority gaps.
- **Genuinely missing here, Med risk (EV/strategy or guarded-elsewhere):** contradictory legal-action inputs (#6 full), river bluff-catcher (#7), wet-board realization (#8), multiway (#9), package/forbidden-imports as pytest (#10, but operationally guarded), blind-defense/3-bet pressure (#11).
- **Genuinely missing here, Low risk (meta-tooling):** seed reproducibility (#12), bootstrap-CI correctness (#13).
- **Provably covered by another build, not here:** legal-action legality (#1) and input hardening (#2) map to the ghost `test_legal_actions.py` / `test_hardening_cases.py` and the priors-consumer suite that STATUS records as 25/48/55 — but their source is absent from this tree (8.3 caveat), so the assertions cannot be verified here.

**Bottom line:** the shipped artifacts (SIMPLE e4b4a8f1, DEPLOYED d54640e0) were verified against 25-/48-/55-test edge suites per STATUS, but `tooling/postflop-trap-extractor-2026-05-29` carries only the 4-test never-crash contract plus a 4-test extractor integration suite. The richest, highest-risk legality coverage (rows #1, #3, #4) is not reproducible in this worktree.


---

## 9. Agent-run recommendations

Up to 5 candidate runs (4 recommended; a 5th, weaker, is folded into Run 1's output rather than spending a row — see note). Ordered by consequence. **Read-only audit + test-authoring are favoured over any `src/` strategy rewrite** (canonical `src/` is scaffold-baseline and HIGH risk to touch pre-finals; §4.0). Hard invariants honoured: `ext/fullhouse-engine/` and `submissions/*.zip` are protected (no edit/repackage); the deployed bot `d54640e0` is git-untracked and its lineage is contested (§1, §5.4a).

**"Chat 5" does not exist** (§1, §2 — no numbered-chat ledger on disk). The interference column is therefore assessed against the *concrete active surfaces*: the dirty **tracked** set on canonical (`STATUS.md`, `KANBAN.md`, `AGENTS.md`, `docs/corpus-index.md`, `docs/playbooks/patch-window.md`, `tools/smoke_run.py` — §1) and the un-merged V2 branch `v2-overnight-2026-06-03` in `~/Code/PokerBot-claude` (§2 Workstream D). Rule: read-only audits collide with ~nothing; new files under `tests/edge_cases/` collide low; any `STATUS.md`/`docs/` write collides with the dirty tree.

| # | Title | Best tool | RO / edit | Files ALLOWED | Files FORBIDDEN | Verification commands | Stop condition | Expected output artifact | Risk of interfering w/ "Chat 5" surfaces |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **Resolve the SIMPLE/DEPLOYED lineage inconsistency (provenance audit)** | Claude Code | **Read-only** (writes ONE memo only) | READ: `submissions/v_qual2_ship_d54640e0.zip`, `submissions/v_final.zip`, `submissions/best_green.zip` (unzip-to-temp + inspect, do **not** modify); `~/Code/PokerBot-claude/src/*.py`; `~/Code/PokerBot-claude` git history incl. base tag/commit `2733566`; `STATUS.md` (read), `consult/artifacts/2026-06-03-qual2-patch/FINDINGS.md`. WRITE: only `consult/artifacts/2026-06-03-lineage-audit/AUDIT.md` | Any edit to `submissions/*.zip` (extract to `/tmp` only); any edit to `STATUS.md`/`AGENTS.md`/`KANBAN.md`/`docs/`; any `src/` edit in any worktree; `git commit` of the untracked zip (human-gated) | `unzip -l` + per-file `shasum -a 256` of the 3 zips; `diff -r <tmp-unzip-of-d54640e0>/src ~/Code/PokerBot-claude/src`; `git -C ~/Code/PokerBot-claude show 2733566 --stat`; `git -C ~/Code/PokerBot-claude log --oneline base..be7503d3` — **no benchmarks/Docker/pytest** | Memo answers: (a) is deployed `d54640e0` src byte-equal to `PokerBot-claude/src` @ base `2733566`+postflop fix? (b) which qual2 zip actually shipped (`d54640e0` vs FINDINGS `0ec835b6`, §6 row 9 / Workstream-C Q1)? (c) exact remediation steps (commit/tag the untracked zip; reconcile STATUS.md:633) — **steps recommended, not executed** | `consult/artifacts/2026-06-03-lineage-audit/AUDIT.md`: provenance verdict + sha table + recommended preservation/STATUS-correction actions | **~None** (read-only; sole write is a new artifact dir). Does **not** touch the dirty tracked set. |
| **2** | **Author edge/unit tests against canonical's *implemented* code (close the thin-suite legality gap)** | Claude Ultracode | **Edit** (new test files + run them) | WRITE/CREATE: `tests/edge_cases/test_sizing_amounts.py`, `tests/edge_cases/test_timeout_guard.py`, `tests/edge_cases/test_decide_contract.py`, optional `tests/edge_cases/fixtures/*.json`. READ: `src/sizing.py`, `src/timeout_guard.py`, `src/bot.py`, `ext/fullhouse-engine/sandbox/{validator.py,runner.py}` (for state shapes only) | Any edit to `src/*.py`, `ext/fullhouse-engine/**`, `submissions/**`, `STATUS.md`, `tools/smoke_run.py`; **must not** assert raise/all_in *strategy* (canonical `decide` is fold/check stub — those pass vacuously, §4.0/4.2) | `pytest tests/edge_cases -x` (host `.venv` py3.10, <60s) | New tests added **and** green; specifically: `sizing_to_amount("third_pot", pot<3, stack)` → asserts the **0-chip-raise** bug (§4.2); `two_third_pot` for `pot<2`; `ValueError` on unknown tag (`sizing.py:22`); `run_with_budget` returns fallback on exception **and** documents that it does **NOT** preempt a >2 s `decision_fn` (post-hoc check `timeout_guard.py:33`, §8.5 #4); `decide()` never-crash + always-legal on side-pot-shaped / partial-key dicts (§8.5 #2,#3) | A real, runnable edge suite (3 files) raising canonical's count above the 4-test scaffold contract; plus a one-paragraph note that **strategy-strength rows (§8.5 #7,#8,#9,#11) require the elaborate build and are out of canonical scope** | **Low.** New files only, under `tests/edge_cases/` (untracked dir today, §8.1). No tracked-file edit. |
| **3** | **Run DEPLOYED `d54640e0` through the strength/safety gauntlet it skipped (G9–G11 + smoke)** | Codex `/goal` | Edit (writes a STATUS-style block to its own artifact; **not** `STATUS.md`) | READ-ONLY on the artifact: `submissions/v_qual2_ship_d54640e0.zip`. RUN: `tools/{b8_gauntlet.py,smoke_run.py,benchmark.py,exploit_check.py,import_audit.py}` and `ext/fullhouse-engine/sandbox/validator.py` with `--zip`. WRITE: only `consult/artifacts/2026-06-03-deployed-gauntlet/RESULT.md` | Any repackage/modification of the zip; any `src/` edit; appending to canonical `STATUS.md` (propose the block, human pastes); editing `tools/smoke_run.py` (it is in the dirty tracked set) | `python ext/fullhouse-engine/sandbox/validator.py submissions/v_qual2_ship_d54640e0.zip`; `python tools/smoke_run.py --zip … --hands 200`; `python tools/benchmark.py --all-templates --paired-seed-base 42` (or `b8_gauntlet.py` on the zip) — **long-running; this is the only run that may exceed 60 s, hence Codex `/goal`, not this read-only session** | Gauntlet completes (or a hard fail is captured) for `d54640e0`: validator 4/4, smoke 200/200, all-templates bb/100 vs SIMPLE baseline, LBR under caps, self-play-vs-prior ratchet — the **G9–G11 ladder DEPLOYED never cleared** (§1) | `consult/artifacts/2026-06-03-deployed-gauntlet/RESULT.md` with measured numbers, closing "live bot at a *lower* verification tier than the bot it replaced" (§1) | **Low–Med.** Reads protected zip only; risk is the *human* later pasting results into the dirty `STATUS.md`. The run itself edits no tracked file. |
| **4** | **Validate the recon diagnosis + portal-history corpus integrity the live patch rests on** | Claude Code | **Read-only** (writes ONE memo only) | READ: `data/portal_histories/**` (via `python json.load`; note Read/`cat` are intercepted on stubs, §5.4b — use json.load); `tools/{field_recon.py,preflop_sizing_audit.py}`; `consult/artifacts/2026-06-03-overnight-recon/{RECON_REPORT.md,*.csv,*.json}`; `consult/artifacts/2026-06-03-qual2-patch/FINDINGS.md`. WRITE: only `consult/artifacts/2026-06-03-recon-validate/CHECK.md`. May RUN `tools/field_recon.py` read-only if <60s on the 12-match corpus | Any write under `data/`; any edit to `tools/*.py`; any `src/` edit; editing FINDINGS.md/RECON_REPORT.md (they are existing artifacts — do not mutate) | Re-derive the recon's own invariants from the CSVs: revealed-set 571/571, winners==pot 9,058/9,058, per-match-net==chip_delta 11/11 (§3.1); independently recount the all-in vs ≥40%-commit conflation (§3.4a: literal all-ins 12–13 hands vs the −81k gross-loss class) | Memo confirms-or-refutes: (a) RECON supersedes FINDINGS on the −81k headline (§3.4); (b) `bot_id` exposure + cross-match UUID stability (currently **inferred, not proven**, §2 Workstream B); (c) how many of 56 `portal_histories` json are real vs stubs (§5.4b: 18 real / 38 stubs) and whether the on-disk pull is too partial for finals priors | `consult/artifacts/2026-06-03-recon-validate/CHECK.md`: diagnosis-integrity verdict + corpus-completeness flag for the patch-window analyzer | **~None.** Read-only over data + artifacts; sole write is a new artifact dir. |

**Note on the 5th (dropped) row:** a standalone "reconcile `STATUS.md:633` self-inconsistency" run is **not** worth a separate row — STATUS.md is in the dirty tracked set (high interference) and the *correction text* is a direct output of Run 1's provenance verdict. Fold it into Run 1's recommended-actions section; a human applies the one-line STATUS edit.

**Per-row rationale (anchored to §1–§8):**

1. **Lineage audit — highest consequence.** §1 names this the *exact next human decision*; §1/§4.0/§6(row 9)/§7 all record the in-record contradiction: same sha `e4b4a8f1` is called both "SIMPLE … does NOT match deployed" (STATUS.md:633) and "canonical known-good **elaborate** build" (STATUS.md:630), and the deployed `d54640e0` src is **absent from canonical** (§4.0) yet **present inside the zip** (§5.2, verified this session: `src/postflop.py` 8,656 B). Provenance is resolvable **only** by unzipping the artifact and diffing cross-worktree against `PokerBot-claude/src` @ base `2733566` (confirmed resolvable this session) — hence the ALLOWED scope must span worktrees, or the run cannot answer.
2. **Edge tests against implemented code — the non-vacuous half of the thin-suite gap.** §8.1 proves canonical carries only the 4-test never-crash contract (25/48/55 suites live on other branches, §8.3). But §4.0 proves canonical `decide` is a fold/check stub, so §8.5's strategy rows would pass vacuously — the run must target the **only implemented** logic: `sizing.py` (the `pot<3 → 0-chip raise` bug + `ValueError`, verified at `sizing.py:13,22`) and `timeout_guard.py` (post-hoc, non-preempting semantics, verified at `timeout_guard.py:33`), plus the legality contract (§8.5 #2,#3). This closes real §8.5 High-risk rows (#3 side-pot legality, #4 timeout-guard) without Docker and without contradicting §4.
3. **DEPLOYED gauntlet — closes the verification-tier inversion.** §1 states the live bot `d54640e0` cleared only the lighter qual2 gauntlet and **never** the G9–G11 strength ladder, so "the bot now live … is at a *lower* verification tier than the bot it replaced." §6 confirms no `--all-templates`/ratchet/ablation row exists for `d54640e0` (§7 A.1: "No DEPLOYED-tag all-templates numbers exist"). The tools take `--zip` (§8.4), so source-not-in-canonical is no blocker; long runtime ⇒ Codex `/goal`.
4. **Recon validation — de-risks the basis of the shipped patch.** The live patch's +EV is **inferred from replay, not measured** (§2 Workstream A/D; §3.4), and Workstream B already **partially retracted** Workstream A's −81k headline as a metric conflation (§3.4a). §5.4b flags the corpus is a **partial download** (18 real / 38 stub json, truncated UUID fragments). Independently re-deriving the recon invariants (§3.1) and the conflation recount confirms whether the diagnosis the live bot rests on is sound, and whether the on-disk corpus is complete enough for the patch-window analyzer (`tools/analyze_hand_histories.py` → `data/finals_priors.npz`).


---

## 10. Minimal context bundle for reviewer

> Output-path note: my assignment passed the literal placeholder `undefined/10-bundle.md` (the orchestrator's report-dir variable did not render, same bug §8 flagged). This fragment is written to the canonical forensic dir `consult/artifacts/2026-06-03-context-refresh/10-bundle.md`, alongside siblings 01-05 and 08. Logistics aid for whoever assembles the full report: two siblings landed in stray locations from the same bug — `06-verification.md` is at `/Users/farhad/Code/PokerBot/undefined/06-verification.md` and `07-opponents.md` is at `/Users/farhad/Code/PokerBot/07-opponents.md` (read-only here, not moved).

This bundle is an index over sections 1-8; it introduces **no new claims** and harvests **no fresh numbers** — every row traces to a section (§ref). Lineage tags throughout: **SIMPLE e4b4a8f1** (`v_final.zip` == `best_green.zip`, Qualifier-I artifact) / **DEPLOYED d54640e0** (`v_qual2_ship_d54640e0.zip`, uploaded for Qualifier II 2026-06-03) / **V2 be7503d3** (`PokerBot-claude/.../v_overnight_v2.zip`, reviewed-SHIP but unmerged/un-uploaded).

Two task-prompt framings the sections correct, carried forward here:
- DEPLOYED d54640e0 is **NOT "unpreserved."** It IS preserved locally at `submissions/v_qual2_ship_d54640e0.zip` (sha byte-matches STATUS:632); the real gap is that it is **git-untracked and its source is not in canonical `src/`** (§1 blocker (a); §5.4(a)).
- The finals choice is **not binary** — it is a **trilemma** across SIMPLE / DEPLOYED / V2 (§1 "exact next human decision"; §2 WS-D).

### (a) Files the reviewer MUST read (smallest set)

| Path | 1-line why | §ref |
|---|---|---|
| `STATUS.md` (tail ~L600-643: A3 ship-day + QUAL2-PATCH entries) | Single harvest source for nearly every benchmark/validator number; both shipped-bot gauntlets and the lineage-inconsistency admission (L633) live here. | §1,§3,§6 |
| `consult/artifacts/2026-06-03-overnight-recon/RECON_REPORT.md` | Chip-exact Qualifier-I forensic on DEPLOYED (571/571, 9058/9058 validated); **supersedes** FINDINGS' conflated −81k headline; proves the leak is postflop stack-off discipline. | §3 |
| `consult/artifacts/2026-06-03-qual2-patch/FINDINGS.md` | The qual2 postflop `_can_commit` fix rationale + acceptance replays; earlier diagnosis, partly retracted by RECON (read second). | §2 WS-A,§3.4 |
| `consult/artifacts/2026-06-03-overnight-candidate/TASK4_REVIEW_VERDICT.md` | V2 be7503d3 SHIP verdict + the two non-blocking WARNINGS (dominated under-boat; owed_frac>0.25 hard-fold) — the V2 ship-risk record. | §2 WS-D |
| `docs/plans/overnight-thorp-v2-2026-06-03.md` + `docs/reviews/critique-overnight-thorp-v2-2026-06-03.md` | The only formal work decomposition (WP-0..WP-6) + its Open Questions (Q1 which qual2 zip shipped); establishes real baseline = `PokerBot-claude/src`. | §2 WS-C |
| `submissions/v_qual2_ship_d54640e0.zip` | The **only on-disk copy of the actually-shipped source** — canonical `src/` is scaffold-baseline (folds/checks everything), so this zip, not the worktree, is the live strategy. | §4.0,§5.2 |
| `CLAUDE.md` | The two-regime (qualifier max-exploit / finals near-Nash) frame + sandbox/validator invariants any ship decision must satisfy. | §1,§4.4 |

### (b) Command outputs the reviewer MUST see (smallest set)

> **Freshness caveat (read first):** **NOTHING in this table was run for this refresh.** All rows are harvested from on-disk artifacts (§6 states this explicitly). Newest full gauntlet = QUAL2-PATCH (DEPLOYED, 2026-06-03); SIMPLE's full G1-G11 suite is 2026-05-28/06-01 (~stale). Per-row bot tag is load-bearing.

| Command / artifact (harvested) | What it proves | §ref |
|---|---|---|
| SIMPLE A3 nine-cmd proof-of-green (`STATUS.md:607-616`): validator 4/4, edge **25/25**, LBR **18.0/7.4**, smoke 200/200 Δ+14,500, 0/10 no-go | SIMPLE e4b4a8f1 cleared the **full** ladder, incl. G9 all-templates / G10 ablate / G11 ratchet (2026-05-22, reconfirmed). The tier the replacement must match. | §1,§6 |
| DEPLOYED QUAL2 gauntlet (`STATUS.md:631`): validator 4/4, import 0.040s/25 MB, edge **48/48**, smoke 200/200, LBR **32.1/81.2** | DEPLOYED d54640e0 passed only the **lighter** gauntlet — **G9-G11 benchmark ladder NOT run**. Contrast with the row above = the live bot ships at a **lower verification tier** than the bot it replaced. | §1,§6 |
| DEPLOYED lone strength proxy: h2h vs baseline **−9.66 bb/100, CI crosses 0** | The *only* head-to-head number for the deployed bot is non-positive (called an HU over-tightness artifact; game is 6-max). No measured +EV for DEPLOYED. | §2,§6,§7 |
| `benchmark --all-templates` 5-run mean (`STATUS.md:567`, **SIMPLE only**): template +71.82, aggressor +109.72±12.06, math/ref_bot_2 +144.60, shark +70.43 bb/100 | SIMPLE's reference-bot edge; **no DEPLOYED-tag all-templates run exists** (DEPLOYED≈SIMPLE here is inference only, "patched==baseline"). | §6,§7 |
| `benchmark --ablate-overlay` **+32.53 bb/100** + ratchet (SIMPLE) | SIMPLE's exploit-overlay gain clears the ≥3 bb/100 floor; ratchet figure is in-record-disputed (L241 +74.41/+18.89 vs L193 −0.87 "was fabricated +4.47"). | §6,§7 A.3 |
| RECON reconstruction validation: revealed-set **571/571**, winners==pot **9058/9058**, net==chip_delta **11/11** | The Qualifier-I forensic (§3) is **chip-exact**, not inferred — trust the stack-off diagnosis and the FINDINGS −81k correction. | §3.1 |
| V2 be7503d3 gauntlet (`TASK4_REVIEW_VERDICT.md`): validator 4/4, import 0.092s/38.1 MB, **80 pytest pass**, smoke 200/200, LBR 32.1/82.4, match +35,280/+13,050 (**"not an EV claim"**) | V2 candidate is green on the widest reproduced suite; the +chip match numbers are explicitly **not** an EV claim. The only direct V2 EV proxy is the same −9.66 h2h. | §2 WS-D |

### (c) Too large to include — summarize, do not ship

| Item | Size / shape | Suggested summary instead | §ref |
|---|---|---|---|
| `data/portal_histories/` | ~9.3 MB, 56 `*.json` — **only 18 real** (>30 B), 38 are `{"error":"Sign in required"/"Match not found"}` stubs + 9 truncated-UUID fragments | Ship the recon's distilled CSVs/JSON instead (`opponent_profiles.json`, `stackoff_decisions.csv`, `showdown_spots.csv`); treat the raw pull as **partial/incomplete** for prior-fitting. | §3.1,§5.4(b) |
| `consult/artifacts/**` (~30 dirs) | Many MB across all dates | Point only to the **4 decision-critical 2026-06-03 dirs** named in (a); ignore the rest for this decision. | §2 |
| `STATUS.md` (full file) | Long running ledger; numbers from many lineages (incl. fabricated-then-corrected & losing-branch values) | Direct reviewer to the **tail (L600-643)** + the specific cited lines; do not read the whole file (OTHER-tagged rows are quarantined in §6). | §6 |
| `prompt-exports/2026-06-03-*` | Several prompt transcripts | Index only; the decisions they produced are already captured in WS-A..D (§2). | §2 WS-A |
| `PokerBot-claude` / `PokerBot-codex` worktrees | Full elaborate + divergent trees (out of canonical scope) | Note that the real shipped/candidate **source lives there**, not in canonical `src/`; inspect via the on-disk zips rather than shipping the trees. | §4.0,§7 PART B |

### (d) OPEN QUESTIONS for the reviewer (decision-oriented)

1. **(THE gate — §1 verbatim "exact next human decision")** Before any V2 work proceeds: do we **first reconcile the deployed elaborate lineage (d54640e0) into canonical and run it through the full G1-G11 gauntlet**, OR **build/ship a V2 candidate (be7503d3) on top of an untracked, under-verified base whose source is not in `main`?** (§1)
2. **Finals ship trilemma.** Which bot ships the finals (2026-06-05): **SIMPLE e4b4a8f1** (full-gauntlet-green but the Qualifier-I leak is unfixed), **DEPLOYED d54640e0** (postflop fix live, but **preserved-only-locally / git-untracked / source not in canonical**, and never cleared G9-G11), or **V2 be7503d3** (reviewed SHIP, widest green suite, but unmerged + 2 open WARNINGS + no measured +EV)? (§1,§2 WS-D)
3. **Which qual2 zip actually shipped?** STATUS:632 live artifact `d54640e0…f4421` vs FINDINGS:27 build `0ec835b6…fbac7` (SHA-divergent, different `opponent_model.py`/`sizing.py`); STATUS:633 admits "exact bytes unverifiable… lineage inconsistent across worktrees." This gates V2 WP-3/WP-4. Resolve before promoting any descendant. (§2 WS-C Q1,§6 row 9)
4. **Do V2's two WARNINGS block ship?** (i) `hand_features.full_house_or_better` short-circuits the commit gate → a dominated under-boat (e.g. `Qc9h` on `KdKsQsQd5c`) commits at ~10% equity; (ii) `commitment.can_call_large` **hard-folds when `owed_frac>0.25`**, ignoring pot odds (folds priced-in +EV calls). Reviewer ruled both non-blocking — confirm or gate. (§2 WS-D)
5. **Is the highest-risk legality coverage acceptable for finals?** Canonical carries only the 4-test never-crash contract; the rows the fold-on-exception runner turns straight into chip loss — **#1 raise-amount numeric legality / equal-to-call**, **#3 side-pot/multi-all-in states**, **#4 >2 s equity-call timeout-guard** — are **not reproducible in this worktree** (only STATUS-claimed on the 25/48/55 suites of other branches). Require these re-proven on whichever bot ships. (§8.5)
6. **(Does not block; surface only)** Which bot actually played Qualifier I? §1 tags the #85/+679 result to **SIMPLE e4b4a8f1**; §3 (RECON) audits the **elaborate/DEPLOYED-class** build as "the build that actually shipped." Unresolved here; folded into Q2/Q3 rather than independently adjudicated. (§1 blocker (b),§3 intro)
