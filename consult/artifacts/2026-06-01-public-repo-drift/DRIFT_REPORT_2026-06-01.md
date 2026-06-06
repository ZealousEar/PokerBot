# Public-fork drift + activity report — 2026-06-01 (qualifier day)

Upstream: `uzlez/fullhouse-engine`. Baseline for this sweep: the 2026-05-29 public-repo-drift snapshot (`consult/artifacts/2026-05-29-public-repo-drift`). Output dir: `consult/artifacts/2026-06-01-public-repo-drift`.

## Method and scope (read this first)

- **Ranking/classification is by BOT-FILE change vs the 2026-05-29 baseline, NOT raw `pushed_at`.** A fork's `pushed_at` bumps whenever the owner syncs the upstream engine or pushes a side branch, even when no bot code changes. Three forks here (vladimir, Benjamin, Mehedi) carried fresh `pushed_at` timestamps of 2026-05-31; all three were verified by fetching the live HEAD and diffing the bot inventory, not assumed from the timestamp.
- **The staged orchestrator inputs for this run had an empty triage/deep-dive payload** (`TRIAGE: 0 targets`, `DEEP-DIVE: 0 repos`). That means the automated clone + head-to-head (H2H) phase cleared nothing into deep-dive this cycle — it is a finding, not a reason to skip classification. All 37 forks in `triage_targets.json` are still classified below.
- **What was actually used:** baseline bot inventories and the prior fork inventory from `inputs.json`; the 37-target list with `baseline_sha`/`pushed_at` from `triage_targets.json`; and a bounded set of read-only `gh api` calls made live on 2026-06-01 (current HEAD SHA, `contents/bots` listings, individual `bot.py` sizes, recursive tree search for `.npz`). No repository was cloned for this report; the 2026-05-29 local clones were reused only for the Vladimir `gto_strategy.npz` cross-check.
- **No benchmarks / no H2H were run in this sweep.** No files under `submissions/`, `src/`, `data/`, `ext/`, or `tests/` were touched. All writes are under `consult/artifacts/2026-06-01-public-repo-drift/`.
- Hero artifact referenced for re-benchmark scoping is the locked `submissions/v_final.zip` (sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` per the 05-29 run). This report does not authorize replacing it.

## Top-line summary

| Classification | Count | Repos |
|---|---:|---|
| **DRIFTED_BOT** | 3 | vladimirfilip, Mehedi-dev-2404, Pav1602 |
| **NEW_BOT** | 1 | Benjamin-Yu-Sheng-Chang |
| **UNCHANGED** | 5 | stoppedtime24, Con-TI, famadeo, agrawalneel25, TobyCoad |
| **LATENT_BOT** | 1 | Littleguygabe/fullhouse-poker (4 bots, pre-baseline, never benchmarked — see correction) |
| **MIRROR_NO_BOT** | 26 | (template-only forks — all live-verified 06-01; see appendix) |
| **GONE** | 1 | MatusGib (HTTP 404) |
| **TOTAL TARGETS** | **37** | |

Headline: **4 forks show real bot movement since the 05-29 baseline** (3 evolved an existing bot, 1 went from template-only to a full multi-bot submission). The other 33 are noise: 27 pristine template mirrors, 5 unchanged (their bots match the baseline, including the two prior GREEN reuses famadeo/neel and the prior RED TobyCoad), and 1 deleted. The single highest-value signal is **Mehedi `mybot`**, which was RED against `v_final` on 05-29 and has since been rewritten +40%.

Note on the `pushed_at` trap: stoppedtime24 (05-28), TobyCoad (05-16), Con-TI (05-25), famadeo (05-22) and agrawalneel25 (05-12) all carry post- or near-baseline activity, yet every one has an unchanged bot file vs baseline — they are correctly classified UNCHANGED, not drifted. Conversely the giant `20:04:02Z` / `12:20:27Z` / `19:22:11Z` timestamp clusters are upstream-sync waves across pristine forks.

## Post-synthesis verification correction (orchestrator pass, 2026-06-01)

The automated synthesis below classified 22 of the 27 `MIRROR_NO_BOT` forks from the **stale 05-29 baseline inventory** rather than a live check (it admits this in the appendix). A post-synthesis pass live-verified **all 27** (current HEAD SHA + `bots/` listing via `gh api`). Result: **26 confirmed genuinely template-only**, and **one was misclassified**:

- **`Littleguygabe/fullhouse-poker` — was `MIRROR_NO_BOT`, actually `LATENT_BOT` (4 non-template bots).** HEAD `338f3ec` carries `bots/mybot` (9,941 B, with preflop range data `RFI.json`/`FRFI.json`/`3BET.json`), `bots/ranger` (2,040 B, preflop range data), `bots/aof` (1,261 B), `bots/memoryTest` (888 B). Last bot commit is **2026-05-22 — before the 05-29 baseline** — so this is **not** new drift; it is a real opponent that **both** the 05-29 audit and this sweep's synthesis missed (its repo is named `fullhouse-poker`, not `fullhouse-engine`, which likely defeated the prior inventory scan). It has **never been benchmarked** against `v_final`.

The canary held: **`gonfdcg`** (the only genuinely-new active fork, pushed 05-29) and the other 4 new forks are confirmed **template-only** at live HEAD `a80b269` (= upstream) — no hidden bot.

**Corrected buckets:** 3 DRIFTED_BOT + 1 NEW_BOT + 5 UNCHANGED + 1 LATENT_BOT + 26 MIRROR_NO_BOT + 1 GONE = 37.

**Latent untested opponents** (real bots, no recent drift, never H2H'd): `Littleguygabe/fullhouse-poker` (`bots/mybot` 9,941 B is strongest) and `Con-TI/fullhouse-engine` (`bots/mybot` ~1,572 B near-template stub, low threat). Neither is an *active* qualifier-day threat (no movement since baseline), but Littleguygabe's `mybot` is non-trivial and unverified — optional low-priority H2H.

## Most active / real updates

| Repo | Classification | Current head (short) | Drifted since 05-29? | Changed bot files | One-line what-changed |
|---|---|---|---|---:|---|
| vladimirfilip/fullhouse-engine | DRIFTED_BOT | `0701e08` | YES | 1 canonical (+81 dirs) | HEAD `f8b8723`→`0701e08` ("fix oom in preflop cfr"); `bots/vlad/bot.py` 30,111→46,115 B; `bots/` exploded 6→**87** dirs (now a sparring gauntlet of rival bots + `neel_v6` sweeps + `vlad_gto_*` variants) |
| Pav1602/fullhouse-engine | DRIFTED_BOT | `d512bf4` | YES | 6 new variants | HEAD `555c84f`→`d512bf4` (pushed 05-30); canonical default advanced **skantbot7.9→7.13** (73,385→98,324 B); new `skantbot8` (100,483 B) / `skantbot8.1` (100,522 B) |
| Mehedi-dev-2404/fullhouse-engine | DRIFTED_BOT | `a30fd77` | YES | 1 (`bots/mybot/bot.py`) | HEAD `aa14a35`→`a30fd77` ("Add Axiom poker bot submission"); `mybot/bot.py` 25,993→36,278 B (**+40%**); was **RED** on 05-29 |
| Benjamin-Yu-Sheng-Chang/fullhouse-hackathon | NEW_BOT | `cd841b5` | YES | 12 new dirs | HEAD `725e898`→`cd841b5` ("add multiple bots"); went from **template-only → 17 bot dirs** incl `cfr` (8,103 B, has `trainer/`), `adaptive_hybrid`, `equity_position`, `trap_steal`, `position_bully` |
| TobyCoad/fullhouse-engine | UNCHANGED (prior RED) | `93516f3` | NO | 0 | HEAD == baseline; `bots/master` unchanged. Carried as a known threat — prior 05-29 H2H was **RED** at `-15.30` bb/100 scheduled and still applies |
| stoppedtime24/fullhouse-engine | UNCHANGED (prior GREEN) | `52951cb` | NO | 0 | HEAD == baseline; `mybot/bot.py` 13,890 B unchanged. Prior 05-29 H2H GREEN (`+14.05`) still applies |
| famadeo/fullhouse-engine | UNCHANGED (prior GREEN) | `c94dace` | NO | 0 | `bots/codex_holdem` (88,634 B + `data/model.json`) unchanged. Prior GREEN (`+0.65`) |
| agrawalneel25/fullhouse-engine | UNCHANGED (prior GREEN) | `071d54c` | NO | 0 | Tracked branch `neel-work`; `bots/neel` unchanged. Prior GREEN (`+14.69`) |

## Per-repo detail (deep-dived / verified repos)

> The automated deep-dive (clone + H2H) phase delivered 0 repos this cycle. The detail below is from the live read-only `gh api` verification done for this report on 2026-06-01. No H2H was run.

### vladimirfilip/fullhouse-engine — DRIFTED_BOT (heavy)

- **Commits since baseline:** HEAD moved `f8b8723…` → `0701e08097a2e7ad60b87581ad0b4be70ddbf90d` (2026-05-31T21:30:13Z, "fix oom issue in preflop cfr"). `pushed_at` 2026-05-31T21:30:19Z.
- **Canonical bot path:** `bots/vlad/bot.py` — grew 30,111 → **46,115 B** (+53%). Sibling self-variants now present: `bots/vlad_gto_150_iters/bot.py` (36,309 B), `bots/vlad_old_gto/bot.py` (36,295 B), `bots/anti_monte_carlo/bot.py` (4,240 B), and a separate `bots/cfr_equity_v28` (`bot.py` 20,881 B + `data/equity_matrix.npy` 114,372 B + `data/removal_weights.npy` 114,372 B + `data/preflop_cfr_strategy.json` 395,606 B).
- **What changed:** `bots/` ballooned from 6 dirs at baseline to **87 dirs**. The bulk are mirrored copies of *other competitors'* bots used as sparring partners — e.g. `Linglingletsgo_*` (8 styles), `Littleguygabe_aof`/`_mybot`, `Pav1602_skantbot{,2,3,4}`, `TobyCoad_*` (the full 11-bot template-styles set incl `TobyCoad_master`), `saroopjagdev_mybot`, `rexheng`, plus `neel_*` (a large profile/sweep family: `neel_v2…v6`, `neel_v6_sweep_000…029`, `patch_*`). This is Vladimir building an internal gauntlet, not 87 distinct ship candidates.
- **Threat assessment:** High-attention author, materially evolved canonical bot, but the 05-29 live H2H was **TIMEBOXED_PARTIAL** (only 270 hands, projected slow via Monte-Carlo fallback). No current bb/100 verdict exists. The bot.py rewrite invalidates the stale partial. Treat as an unresolved, evolving threat that needs a fresh H2H against `v_final` — see re-benchmark candidates.

### Vladimir `gto_strategy.npz` status callout (explicit)

**ABSENT at current HEAD `0701e08`.** A recursive git-tree search for `gto_strategy`/`*.npz`/`*.npy` at the current HEAD returns only `bots/cfr_equity_v28/data/equity_matrix.npy` and `bots/cfr_equity_v28/data/removal_weights.npy` — i.e. `.npy` files belonging to the *separate* `cfr_equity_v28` bot, **not** a `gto_strategy.npz` and **not** under `bots/vlad/`. `bots/vlad/` contains only `bot.py`. The 2026-05-29 local clone (also at the then-HEAD `f8b8723`) likewise had no `bots/vlad/data/` directory. Conclusion: the public `bots/vlad` bot still validates only via its slow Monte-Carlo fallback path; the `gto_strategy.npz` blueprint that the CLAUDE.md notes reference for Vladimir's numpy-MLP forward pass is **not** committed to the public fork at this HEAD. (`vlad_gto_150_iters` / `vlad_old_gto` exist as `bot.py`-only variants with no committed `.npz` either.)

### Pav1602/fullhouse-engine — DRIFTED_BOT

- **Commits since baseline:** HEAD moved `555c84f…` → `d512bf428ffcbae7ff036e2a7382dca1396dd2ce`; `pushed_at` 2026-05-30T06:47:22Z. (This repo is **not** returned by the upstream fork API — `in_fork_api=false` — and was inspected directly, exactly as in the 05-29 audit.)
- **Canonical bot path:** `play_human_hu.py` now defaults to **`skantbot7.13`** (baseline default was `skantbot7.9`). Canonical `bots/skantbot7.13/bot.py` = 98,324 B (vs `skantbot7.9` 73,385 B). Highest version is now `skantbot8.1` (`bot.py` 100,522 B; `skantbot8` 100,483 B).
- **What changed:** new variants appeared since baseline — `skantbot7.10` (78,145 B), `skantbot7.11` (81,686 B), `skantbot7.12` (94,609 B), `skantbot7.13` (98,324 B), `skantbot8` (100,483 B), `skantbot8.1` (100,522 B). The family grew by ~6 versions and the canonical size rose ~34%.
- **Threat assessment:** On 05-29 the then-canonical `skantbot7.9` was GREEN (`+0.20`, CI `[-2.24,+2.81]`) and the headline `skantbot7.6` was GREEN (`+9.61`). The bot has materially advanced (7.9→7.13, plus a v8 line) since those numbers, so the prior GREEN is stale for the new canonical. Moderate-priority re-benchmark candidate (prior trend favorable to us, but unverified at the new size).

### Mehedi-dev-2404/fullhouse-engine — DRIFTED_BOT (highest-value signal)

- **Commits since baseline:** HEAD moved `aa14a35…` → `a30fd7730d715e26baeec343c3d44179fab604ee` (2026-05-31T13:40:55Z, "Add Axiom poker bot submission"); `pushed_at` 2026-05-31T13:40:59Z.
- **Canonical bot path:** `bots/mybot/bot.py` — grew 25,993 → **36,278 B** (+40%). Despite the commit message naming an "Axiom" bot, no new top-level bot dir was added; the bot set is still `aggressor, mathematician, mybot, ref_bot_2, shark, template`, so the Axiom rework landed inside the existing `bots/mybot/bot.py` (single file, no `data/` subdir).
- **What changed:** a substantial (+40%) rewrite of the one bot that already beat us.
- **Threat assessment:** **Highest priority.** On 05-29 this exact bot was **RED** against `v_final` (`-9.00` bb/100 scheduled first pass, CI `[-14.0,-4.0]`; 100k escalation stayed negative at `-9.19` before time-boxing). A 40% rewrite on a bot that already had positive EV against us is the most likely place our locked artifact loses chips in the qualifier. Top re-benchmark candidate.

### Benjamin-Yu-Sheng-Chang/fullhouse-hackathon — NEW_BOT

- **Commits since baseline:** HEAD moved `725e898…` → `cd841b5e0fc37401f42b8be4acf944cbe8080a72` (2026-05-31T19:43:16Z, "add multiple bots"); `pushed_at` 2026-05-31T19:43:21Z.
- **Canonical bot path:** ambiguous — no single canonical entrypoint confirmed. The strongest-named candidate is `bots/cfr/bot.py` (8,103 B, ships a `trainer/` subdir and `README.md`). A `STRATEGY_COMPONENTS.md` doc was also added at `bots/` root.
- **What changed:** went from **template-only (0 non-template bots) to 17 bot dirs**. New non-template dirs: `abstract_control`, `abstract_pressure`, `abstract_value`, `adaptive_hybrid`, `anti_aggro`, `cfr`, `equity_guard`, `equity_position`, `hybrid_mix`, `position_bully`, `short_stack_survivor`, `trap_steal` (~12 distinct strategies). (Several of these dirs returned 404 on a direct `bots/<name>/bot.py` probe, so their internal layout may differ from the flat `bot.py` convention; the dir-level appearance is confirmed.)
- **Threat assessment:** A brand-new multi-strategy entrant that appeared in the final 48h before the qualifier, including an explicit `cfr` bot with a trainer. No prior H2H exists (it was template-only at baseline). Unknown strength; warrants a first-pass H2H on its strongest variant to size the threat. Medium-high priority re-benchmark candidate.

## Re-benchmark candidates

**No H2H was run in this sweep.** The following are the repos+paths that warrant a head-to-head against `submissions/v_final.zip`, in priority order. **Whether to run any of these is the user's decision** — this report only scopes them; it does not run benchmarks and does not authorize touching the locked artifact.

| Priority | Repo | Bot path | Why |
|---|---|---|---|
| 1 | Mehedi-dev-2404/fullhouse-engine | `bots/mybot/bot.py` (@ `a30fd77`) | Was **RED** vs `v_final` on 05-29 and rewritten +40% ("Axiom") on 05-31. Most likely active source of qualifier chip loss; prior RED verdict is now stale on a stronger bot. |
| 2 | vladimirfilip/fullhouse-engine | `bots/vlad/bot.py` (@ `0701e08`) | Canonical bot +53% since baseline; 05-29 H2H was only a 270-hand TIMEBOXED_PARTIAL, so we have **no real verdict**. High-attention author actively iterating. Note: validates via slow MC fallback (no `gto_strategy.npz`), so budget H2H runtime accordingly. |
| 3 | Benjamin-Yu-Sheng-Chang/fullhouse-hackathon | `bots/cfr/bot.py` (@ `cd841b5`) | Brand-new multi-bot entrant (0→17 dirs) with an explicit CFR bot + trainer, landed <48h pre-qualifier. No prior H2H exists; needs a first-pass sizing run on its strongest variant. |
| 4 | Pav1602/fullhouse-engine | `bots/skantbot7.13/bot.py` (canonical; also `skantbot8.1`) | Canonical advanced 7.9→7.13 (+34% size) plus a new v8 line since the prior GREEN reads. Prior trend favored us, but the current canonical is unverified at the new size. |

Repos explicitly **not** re-benchmark candidates from this sweep: famadeo, agrawalneel25/neel, stoppedtime24 (all UNCHANGED with valid prior GREEN H2Hs that still apply), and TobyCoad (UNCHANGED — its prior RED at `-15.30` already stands and needs no re-run unless the orchestrator wants a confirmation pass; no bot change to justify it).

## Noise / no-op appendix (full coverage audit)

All 37 targets are accounted for. The 33 below carry no actionable bot change.

### GONE (1)
- **MatusGib/fullhouse-engine** — `gh api repos/MatusGib/fullhouse-engine` returns **HTTP 404** (repo deleted or made private since the 05-29 baseline, where its last-known HEAD was `a80b269` and it was template-only). Dropped from the live field.

### UNCHANGED — bot present, matches baseline (5; covered above, listed here for completeness)
- TobyCoad/fullhouse-engine (`93516f3`, `bots/master`, prior RED) · stoppedtime24/fullhouse-engine (`52951cb`, `bots/mybot`, prior GREEN) · famadeo/fullhouse-engine (`c94dace`, `bots/codex_holdem`, prior GREEN) · agrawalneel25/fullhouse-engine (`071d54c`, `neel-work` → `bots/neel`, prior GREEN) · Con-TI/fullhouse-engine (`8c66033`, `bots/mybot` 1,572 B near-template stub, never deep-dived; low threat).

### MIRROR_NO_BOT — template-only forks, no non-template bot (26)
**All 26 were live-verified on 2026-06-01** (current HEAD SHA + `bots/` listing fetched fresh; full SHAs populated in `triage_table.tsv`) — confirmed template-only today, not inherited from the baseline inventory. Each carries only the upstream template bot set (`aggressor, mathematician, ref_bot_2, shark, template`). Most share the upstream-sync timestamp waves `2026-05-24T20:04:02Z`, `2026-05-14T12:20:27Z`, and `2026-05-07T19:22:11Z`. (The earlier draft classified 22 of these from the stale baseline; the orchestrator pass live-checked all of them and moved `Littleguygabe/fullhouse-poker` out — see the correction section near the top.)

- gonfdcg/fullhouse-engine **(new fork, verified 06-01)**
- joshmhc/fullhouse-engine **(new fork, verified 06-01)**
- avj26/fullhouse-engine **(new fork, verified 06-01)**
- Hebobeb0/fullhouse-engine-fork **(new fork, verified 06-01)**
- Akash1Siva/fullhouse-engine-akash **(new fork, verified 06-01)**
- lucashsu007-create/fullhouse-engine
- study9372/fullhouse-engine
- ds726/fullhouse-engine
- afinner/fullhouse-engine
- abayojumumichael/fullhouse-engine
- Yutongzhang20080108/fullhouse-engine
- RemiSeg/fullhouse-engine
- NovaIMario/fullhouse-engine
- Amine0411/fullhouse-engine
- Ganto23/fullhouse-engine
- BouillieAnonymous/fullhouse-engine
- sundubu04/fullhouse-engine
- jickzx/fullhouse-engine
- Linglingletsgo/fullhouse-engine
- navaneetham-aicomputing/fullhouse-engine
- krishypatel2007/fullhouse-engine
- chunyang-w/fullhouse-engine
- AyushGupta05/fullhouse-engine
- rishabhkarwal/fullhouse
- aemilani/fullhouse-engine
- Blessing-Emmanuel/fullhouse-engine

> Note on Linglingletsgo: its own fork is a pristine template mirror (MIRROR_NO_BOT) at this baseline, even though Vladimir's gauntlet now contains `Linglingletsgo_*` sparring copies. The copies live in Vladimir's repo, not Lingling's.

## Provenance

- Inputs: `consult/artifacts/2026-06-01-public-repo-drift/{inputs.json,triage_targets.json}`; prior baseline `consult/artifacts/2026-05-29-public-repo-drift/{DRIFT_REPORT.md,RESULTS.json}` and its `_clones/` (Vladimir npz cross-check only).
- TSV companion: `consult/artifacts/2026-06-01-public-repo-drift/triage_table.tsv` (37 rows).
- Classification script (auditable): `consult/artifacts/2026-06-01-public-repo-drift/build_triage_table.py`.
- Live verification: read-only `gh api` (commits, contents, git trees) on 2026-06-01 as account `ZealousEar`. No clones created for this report; no benchmarks; no H2H; no edits outside the artifact dir.
