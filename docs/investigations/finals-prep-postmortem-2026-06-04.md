# Investigation: Finals Prep + R2 Post-Mortem (2026-06-04)

## Summary
Thorp made the Fullhouse 2026 finals (top 64, combined Q1+Q2). This report (a) confirms standing and the finalist field, (b) compiles every finalist's playstyle stats, (c) post-mortems the R2 mistake (a leaked, unpatched bot got submitted instead of the patched build), and (d) sets the finals strategy + baseline. **Finals baseline = the leak-PATCHED build we failed to submit to R2, NOT the live R2 artifact.**

## Symptoms / Context
- Thorp qualified for finals. Q1 rank #85/289; Q2 rank #54/289. Combined → top 64.
- The live R2 submission (`7a7ad230`, storage `bot_1780484373033.zip`, submitted 2026-06-03 10:59Z, status `ready`) is the **leak** version — an overnight agent self-uploaded it with no human in the loop (CLAUDE.md hard rule added 2026-06-03; MEMORY: qual2 redteam verdict d54640e0 finals-RISKY, "stack-off fix did not fix the leak").
- Patch window for finalists is OPEN, deadline 18:00 UTC today (2026-06-04).

## Standing (verified from portal DB, 2026-06-04)
| Round | Thorp rank | chip d/100h | avg d/match | win% | matches |
|---|---|---|---|---|---|
| Qualifier I | #85 / 289 | +679 | +3,602 | 40.0% | 25 |
| Qualifier II | #54 / 289 | +1,565 | +6,505 | 37.1% | 35 |
| Combined | top 64 (finalist; combined order not yet published) | - | - | - | - |

Our submission timeline (portal `bots`, user 506b8ff6):
- 2026-05-25 15:31Z - id 99ce6d02 - status **error** (failed)
- 2026-06-01 09:06Z - id 1c0abfd8 - `bot_1780304793140.zip` - superseded (Q1 build)
- 2026-06-03 00:29Z - id ffe8eae3 - `bot_1780446571025.zip` - superseded
- 2026-06-03 10:59Z - id 7a7ad230 - `bot_1780484373033.zip` - **ready (LIVE / R2 leak version)**

## Background / Prior Research
<!-- explore/git archaeology findings -->

## Investigator Findings
<!-- pair appends here -->

### 2026-06-04 Investigator Appendix — leak, patched RC, and process failures

#### 1) What the leak was

- `d54640e0` is **not a git commit in this checkout**. `git show d54640e0 --stat` returns `fatal: ambiguous argument 'd54640e0'`. The value is the SHA256 prefix of the live R2 zip, not a VCS object. Git evidence after 2026-05-30 instead shows the relevant patch-line commits on `v2-overnight-2026-06-03`: `2733566b9f1fd35b5e165a4ee5c04f15b4fee184` (`V2 base: deployed qual2 postflop _can_commit fix`) and `b43e81b1c0f5d35f4b9f0cefc19a962e7218722a` (`Lane B: split postflop commitment gates`).
- Memory confirms the reference: `/Users/farhad/.claude/projects/-Users-farhad-Code-PokerBot/memory/project_qual2_redteam_verdict.md:10-25` points to `submissions/v_qual2_ship_d54640e0.zip`, says the shipped bytes were never committed to git, and names the leak as `_can_commit` using a static `PRIOR_RANGE_TIGHT` rather than the villain's real betting range.
- The original Qual-II patch diagnosis was a postflop stack-off leak: `consult/artifacts/2026-06-03-qual2-patch/FINDINGS.md:9-19` says `src/postflop.py` used `eq>=0.80 -> raise current_bet*3` where `eq = hand_strength` vs random, causing wet/paired-board re-raises to compound into stack jams; the patch capped re-raises and introduced `_can_commit`.
- The red-team report says that fix was insufficient. `consult/artifacts/2026-06-03-redteam/REDTEAM_REPORT.md:64-92` identifies `LEAK-1 — Static-range commit gate -> near-dead stack-off` in deployed `src/postflop.py`, especially `_can_commit()` fed by `equity_vs_range(..., PRIOR_RANGE_TIGHT)`. `REDTEAM_REPORT.md:220-233` explains the exploit: on paired boards the gate asks whether we beat a generic preflop-tight range, not whether we beat the boats/value range that jams this board. Reported repros include trip-K on `KK7` stacking off at 0.212 true equity and a dry-river second pair at 0.000 true equity.
- Deployed artifact evidence: `consult/artifacts/2026-06-03-deployed-gauntlet/DEPLOYED_GAUNTLET_REPORT.md:3-18` targets `submissions/v_qual2_ship_d54640e0.zip`, SHA256 `d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421`, and says it fails a dominated under-boat / near-dead full-house probe. `DEPLOYED_GAUNTLET_REPORT.md:57-61` shows validator/smoke pass but edge and H2H strategy failures; `:98-100` shows `dominated_underboat_near_dead_commitment -> all_in`; `:129-141` names the unsafe dominated full-house / under-boat gate as a required finals fix.
- STATUS ties the same bytes to the portal upload: `STATUS.md:626-633` records `QUAL2-PATCH · GREEN (uploaded)` and live artifact SHA256 `d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421`; `STATUS.md:662-744` later records the edge-test RED on deployed `submissions/v_qual2_ship_d54640e0.zip` with `near_dead_postflop_commitment` returning `{'action': 'all_in'}` at commitment fraction `1.000`.

#### 2) Leak-patched baseline that was not submitted to R2

- The strongest patched candidate is `submissions/v_finals_rc_patched.zip`, SHA256 `b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b`. Current filesystem inventory shows `submissions/v_final.zip` is byte-identical to it (same SHA, mtime 2026-06-03 12:22:26 +0100), but `STATUS.md:771-806` says the RC was originally created as `v_finals_rc_patched.zip` and **upload was human-gated / not performed**.
- `STATUS.md:771-783` records the patched RC lineage: `v_overnight_v2` (`be7503d3bd4b3dca72978429e2e5f59a642ad5d01824a82d8cab2abedbf899b4`) plus a small full-house-dominance fix. The root cause is `src/commitment.py::can_commit_raise()` short-circuiting `full_house_or_better -> return True`, so a second-best boat such as `Qc9h` on `Kd Ks Qs Qd 5c` auto-jammed 100% of stack.
- Zip-level source evidence from `submissions/v_final.zip` / `submissions/v_finals_rc_patched.zip` (both `b108eff5...`): `src/commitment.py:10` imports `full_house_dominated`; `src/commitment.py:44-56` allows paired-board large stack-offs only for quads/straight-flush or an undominated full house, otherwise routing to call/fold; `src/hand_features.py:212-230` implements `full_house_dominated()` by checking whether a board pair ranked above our trips enables a higher villain full house.
- Direct zip probes run in this investigation: `d54640e0` returns `all_in` on `D1_dominated_Qfull`; `0ec835b6` returns `all_in`; `be7503d3` returns `all_in` on D1 and raises C4; `b108eff5` (`v_final.zip` and `v_finals_rc_patched.zip`) returns `fold` on D1 and C4 and also folds the original A1/A5 real leak states. This confirms `b108eff5` fixes the red-team discriminator states that the R2 live artifact fails.
- Validation evidence: `STATUS.md:785-791` records validator PASS 4/4, layout PASS, edge near-dead guard PASS, warmup/contract/timing PASS, `tests/edge_cases` minus the always-red deployed fixture = 13 passed, and unit asserts for dominated boat / nut boat / bare trips / quads / unpaired nut-flush. I re-ran the engine validator read-only on `submissions/v_final.zip`, `submissions/v_finals_rc_patched.zip`, `submissions/v_qual2_ship_d54640e0.zip`, and `consult/artifacts/2026-06-03-qual2-patch/v_qual2_stackoff_fix.zip`; all passed the AST/shape validator. Caveats: `STATUS.md:793-799` says `b108eff5` is **unbenchmarked** and Docker smoke was **not run** locally for the patched RC. Current `tools/audit_strategy_leakage.py --zip submissions/v_final.zip` also flags comment/string literals, so leakage-audit status needs an explicit policy/tooling decision before claiming full final green.
- Diff vs live `d54640e0` at zip level: `b108eff5` adds `src/commitment.py`, `src/hand_features.py`, `data/field_priors.npz`, and the three blueprint `.npz` files; changes `src/bot.py`, `src/equity.py`, `src/opponent_model.py`, `src/postflop.py`, `src/preflop_lookup.py`, and `src/sizing.py`; leaves root `bot.py`, `src/ranges.py`, and `src/timeout_guard.py` effectively unchanged. No git commit was found for the final `b108eff5` zip; it is an on-disk artifact, not a committed tree.

#### 3) Timeline / process mistakes

- The release process initially worked around a locked artifact. `STATUS.md:602-623` records A3 ship-day GREEN for the Q1 artifact `submissions/v_final.zip` / `best_green.zip` at SHA `e4b4a8f1...`, with validator, import, leakage, edge, exploit/LBR, smoke, and size/layout all passing, and says the next action was **human upload**.
- Effort from 2026-05-27 through 2026-05-31 went into broad verification and patch exploration rather than one clean artifact lane. Examples: `STATUS.md:362-375` records B4 RED invalidating the PATCH-2A premise; `STATUS.md:445-510` shows repeated B8 runner smoke attempts, with benchmark commands passing despite TODO/stub caveats; `STATUS.md:511-526` shows six-max pod RED/AMBER variance results but keeps the qualifier artifact unchanged; `consult/artifacts/2026-05-29-away/SUMMARY.md:13-21` shows seven away-swarm lanes, most concluding `SHIP_LOCKED_ARTIFACT`, `PATCH_NOT_PROMOTABLE`, or `NOT_PROMOTABLE`.
- The solver / over-optimization pattern is visible in planning and consult evidence: `STATUS.md:76-85` made MCCFR/CFR+ blueprint work load-bearing in the architecture; `STATUS.md:379-390` revisited Deep CFR after vladimir's numpy MLP showed runtime feasibility, but still gated it off; `STATUS.md:407-410` explicitly auto-gated Phase D / SHADOW-CFR-1 off after B8 was shelved. The practical failure was not lack of ideas; it was artifact discipline and final promotion control.
- On 2026-06-03, the pipeline split into conflicting artifact decisions. `STATUS.md:626-633` records the uploaded R2 live artifact `d54640e0`; `STATUS.md:646-659` then says V2 `be7503d3` is infra-green but **do not promote** because it regresses non-nut flush on paired boards and still commits dominated boats; `STATUS.md:662-744` adds an edge-test RED for the deployed bot; `STATUS.md:746-769` briefly selects SIMPLE `e4b4a8f1` as finals RC; `STATUS.md:771-806` then creates the patched `b108eff5` finals RC but states upload was human-gated and not performed.
- Submission-process failure: a live portal upload happened before the later red-team/edge evidence was reconciled and before human-gated final selection. The repository then accumulated multiple similarly named artifacts (`v_qual2_ship_d54640e0.zip`, `v_qual2_stackoff_fix.zip`, `v_overnight_v2.zip`, `v_final_be7503d3_LEAKY_preserved.zip`, `v_finals_rc_patched.zip`, current `v_final.zip`) across worktrees, while `d54640e0` was not a commit and `b108eff5` was not committed. This made `git show`, branch names, and `submissions/v_final/` misleading compared with the actual zip bytes.
- Concrete state now: the leak-patched artifact exists locally as `submissions/v_finals_rc_patched.zip` and current `submissions/v_final.zip` (`b108eff5...`), but no evidence shows it was submitted to R2; the live R2 artifact remains documented as `d54640e0...` / portal id `7a7ad230` in this report's timeline above. Before any finals upload, treat upload as human-only and verify the exact zip hash being uploaded, not a directory or branch name.


## Finalist Field - Playstyle & Stats

**Thorp combined finals rank: #57 / 64.** Top of field: jew (#1, +6000 c/100), CallMeMaybe (#2), SevenDeuces (#3), NecessarySkew (#4), Looper257 (#5).

### A. Combined finals ranking (all 64) + playstyle

Source: portal DB tournament `f1f1f1f1-…fffff1` (combined Q1+Q2) + `bot_stats` view (2026-06-04). `chip/100` = chip delta per 100 hands. Playstyle blank = no `bot_stats` row available (21 bots).

| # | Bot | chip/100 | win% | M | fold% | call% | raise% | AF | avgRaise | bust% | scoop% |
|---|-----|---------:|-----:|--:|------:|------:|-------:|---:|---------:|------:|-------:|
| 1 | jew | 5999.98 | 55.6 | 36 |  |  |  |  |  |  |  |
| 2 | CallMeMaybe | 4920.67 | 40.5 | 37 | 62.5 | 17.1 | 20.5 | 1.2 | 790 | 91.7 | 8.3 |
| 3 | SevenDeuces | 4519.31 | 61.8 | 34 | 61 | 16.2 | 22.8 | 1.41 | 486 | 41.7 | 8.3 |
| 4 | NecessarySkew | 4436.99 | 58.3 | 36 | 54.9 | 13.4 | 31.7 | 2.36 | 591 | 45.8 | 16.7 |
| 5 | Looper257 | 4308.71 | 44.4 | 36 | 70.5 | 8.3 | 21.2 | 2.56 | 645 | 72 | 8 |
| 6 | Oxvard | 4230.97 | 34.2 | 38 | 59.5 | 9.7 | 30.8 | 3.16 | 624 | 54.2 | 20.8 |
| 7 | BussBot-v3 | 4070.01 | 43.2 | 37 |  |  |  |  |  |  |  |
| 8 | Taleto13 | 4068.9 | 34.2 | 38 | 56.7 | 19.4 | 23.9 | 1.23 | 684 | 73.9 | 21.7 |
| 9 | CrimsonBot | 3882.81 | 38.5 | 39 | 46 | 25.4 | 28.6 | 1.13 | 672 | 83.3 | 12.5 |
| 10 | FerdaBot | 3812 | 60.6 | 33 | 58.4 | 11.4 | 30.1 | 2.64 | 627 | 44 | 24 |
| 11 | Khan’t Fold | 3644.24 | 36.4 | 33 | 54.2 | 20.2 | 25.6 | 1.27 | 641 | 62.5 | 16.7 |
| 12 | Hyperion | 3592.56 | 57.4 | 61 | 47.1 | 17.5 | 35.4 | 2.03 | 558 | 48 | 32 |
| 13 | Tumble-Weed-Dutch-v2 | 3457.15 | 33.3 | 36 |  |  |  |  |  |  |  |
| 14 | Lekemog | 3455.7 | 41.7 | 36 | 51.3 | 18.1 | 30.6 | 1.69 | 634 | 78.3 | 17.4 |
| 15 | ant-bot | 3403.82 | 32.4 | 37 |  |  |  |  |  |  |  |
| 16 | durak | 3176.79 | 37.1 | 35 | 59.2 | 12.8 | 28 | 2.18 | 663 | 68.2 | 13.6 |
| 17 | jotaroZAWARUDO | 3154.75 | 34.2 | 38 |  |  |  |  |  |  |  |
| 18 | TheQuantBot | 3105.02 | 40 | 35 | 69.1 | 10.8 | 20.1 | 1.86 | 517 | 75 | 8.3 |
| 19 | talan | 2988.02 | 44.4 | 36 | 55 | 10.7 | 34.4 | 3.22 | 427 | 28.6 | 4.8 |
| 20 | +ev | 2967.97 | 54.4 | 57 |  |  |  |  |  |  |  |
| 21 | make_no_mistakes | 2934.09 | 41.7 | 60 | 60.3 | 7.7 | 32 | 4.16 | 448 | 58.3 | 12.5 |
| 22 | Overfitted | 2929.09 | 41.7 | 36 |  |  |  |  |  |  |  |
| 23 | twader | 2862.94 | 31.1 | 61 | 60.9 | 16.4 | 22.7 | 1.38 | 626 | 72 | 20 |
| 24 | gems_VC2 | 2831.56 | 41.7 | 60 | 50.1 | 15.5 | 34.4 | 2.23 | 517 | 40 | 24 |
| 25 | IveyBot | 2763.65 | 55.7 | 61 | 61.8 | 13.8 | 24.4 | 1.76 | 672 | 36 | 16 |
| 26 | Inefficiency | 2617.89 | 43.2 | 37 | 68.6 | 7.2 | 24.2 | 3.37 | 590 | 69.6 | 4.3 |
| 27 | winning | 2545.98 | 35.4 | 65 | 74.5 | 9.9 | 15.6 | 1.57 | 1088 | 66.7 | 8.3 |
| 28 | Pantheon | 2545.09 | 48.6 | 37 |  |  |  |  |  |  |  |
| 29 | sam_bot_lfg_2 | 2507.86 | 48.6 | 35 |  |  |  |  |  |  |  |
| 30 | 50CentRaise | 2442.83 | 35.1 | 37 | 54.9 | 10.5 | 34.6 | 3.29 | 637 | 54.5 | 31.8 |
| 31 | 𝐛𝐚𝐯 | 2275.98 | 41.7 | 36 |  |  |  |  |  |  |  |
| 32 | poker? I barely know her | 2270.24 | 29.7 | 37 | 61.2 | 16.3 | 22.5 | 1.38 | 527 | 56.5 | 17.4 |
| 33 | pavan kumar | 2188.29 | 40.5 | 37 |  |  |  |  |  |  |  |
| 34 | I hate arsenal | 2120.12 | 30.6 | 36 |  |  |  |  |  |  |  |
| 35 | RODBOTv2 | 2100.33 | 44.7 | 38 |  |  |  |  |  |  |  |
| 36 | APEX | 2020.31 | 40.3 | 62 | 51 | 14.2 | 34.8 | 2.46 | 476 | 45.8 | 25 |
| 37 | BATNEEC | 2019.14 | 36.1 | 36 | 67.2 | 8 | 24.7 | 3.08 | 536 | 31.8 | 9.1 |
| 38 | TheCrystalline | 1994.33 | 37.7 | 61 | 69.6 | 7.7 | 22.8 | 2.97 | 601 | 43.5 | 17.4 |
| 39 | Javis | 1989.11 | 25 | 36 | 44.3 | 15 | 40.7 | 2.72 | 411 | 40 | 20 |
| 40 | Freelo | 1958.26 | 28.2 | 39 |  |  |  |  |  |  |  |
| 41 | Super2Trooper | 1924.78 | 42.1 | 38 |  |  |  |  |  |  |  |
| 42 | goku | 1845.52 | 33.3 | 36 | 64.5 | 7.2 | 28.4 | 3.96 | 535 | 91.7 | 0 |
| 43 | chimera_fusion | 1811.14 | 28.6 | 63 | 51.7 | 14.7 | 33.6 | 2.29 | 493 | 68 | 28 |
| 44 | 72o | 1787.66 | 36.1 | 36 | 55.1 | 13.2 | 31.7 | 2.4 | 561 | 62.5 | 16.7 |
| 45 | alan | 1759.8 | 27.8 | 36 | 61.1 | 13.7 | 25.2 | 1.84 | 553 | 60.9 | 4.3 |
| 46 | elprofesoriqo | 1743.6 | 28.9 | 38 | 42 | 27.3 | 30.7 | 1.13 | 501 | 61.9 | 19 |
| 47 | not_so_simple_bot | 1710.73 | 28.2 | 39 |  |  |  |  |  |  |  |
| 48 | Lyra | 1704.79 | 37.8 | 37 | 71.4 | 7.7 | 20.9 | 2.72 | 572 | 66.7 | 16.7 |
| 49 | SaviourBot | 1689.46 | 33.3 | 36 |  |  |  |  |  |  |  |
| 50 | TheHouse | 1684.35 | 28.2 | 39 | 74.2 | 6.3 | 19.5 | 3.07 | 653 | 60.9 | 8.7 |
| 51 | GrandSlam | 1650.33 | 29.5 | 61 | 54.7 | 9.4 | 35.9 | 3.81 | 476 | 70.8 | 12.5 |
| 52 | SummerSun | 1645.16 | 27.6 | 58 | 50 | 24.8 | 25.2 | 1.02 | 892 | 76 | 24 |
| 53 | VolatileNeuron | 1623.65 | 25.6 | 39 | 55 | 12.2 | 32.8 | 2.68 | 579 | 39.1 | 13 |
| 54 | never played poker | 1619.35 | 27 | 37 | 53.6 | 20.7 | 25.8 | 1.25 | 544 | 88 | 4 |
| 55 | G-Forge | 1603.65 | 41.9 | 62 | 73.1 | 8.5 | 18.4 | 2.17 | 558 | 44 | 16 |
| 56 | PhoonTooMuchForPoker | 1568.72 | 27.8 | 36 |  |  |  |  |  |  |  |
| 57 | Thorp **(Thorp)** | 1564.78 | 37.1 | 35 | 58.9 | 6.4 | 34.7 | 5.45 | 430 | 56 | 0 |
| 58 | SuperExtraDeluxeMegaBot | 1433.28 | 27.8 | 36 | 66.4 | 12.6 | 21 | 1.66 | 642 | 62.5 | 12.5 |
| 59 | NEMESIS | 1429.98 | 45.9 | 37 | 65.8 | 10.8 | 23.4 | 2.16 | 718 | 68 | 4 |
| 60 | Bot2 | 1388.68 | 29.7 | 37 |  |  |  |  |  |  |  |
| 61 | BeginnersLuck V3 | 1384.31 | 26.3 | 38 |  |  |  |  |  |  |  |
| 62 | Foldilocks | 1378.8 | 26.3 | 38 | 45.8 | 16.9 | 37.2 | 2.2 | 524 | 52.2 | 17.4 |
| 63 | TheUnknown | 1317.11 | 23.3 | 60 | 58.1 | 20.9 | 21 | 1 | 642 | 64 | 28 |
| 64 | Worm | 1252.33 | 26.5 | 34 |  |  |  |  |  |  |  |

### B. Playstyle clusters (of the 43 with detail)

- **Balanced** (23): 72o, APEX, CallMeMaybe, FerdaBot, Foldilocks, Hyperion, IveyBot, Javis, Lekemog, NEMESIS, NecessarySkew, SevenDeuces, SuperExtraDeluxeMegaBot, Taleto13, TheCrystalline, TheQuantBot, VolatileNeuron, alan, chimera_fusion, durak, gems_VC2, poker? I barely know her, twader
- **Hyper-aggro / high-fold (LAG-ish, polar)** (8): BATNEEC, Inefficiency, Oxvard, TheHouse, Thorp, goku, make_no_mistakes, talan
- **Calling-station / loose-passive** (6): CrimsonBot, Khan’t Fold, SummerSun, TheUnknown, elprofesoriqo, never played poker
- **Nit / tight-passive** (4): G-Forge, Looper257, Lyra, winning
- **Aggressive** (2): 50CentRaise, GrandSlam

## Root Cause (R2 mistake)

Two independent failures compounded:

1. **The leak (strategy).** The deployed R2 bot (`v_qual2_ship_d54640e0.zip`, SHA `d54640e0…`, portal id `7a7ad230`) commits a near-dead stack-off on paired / under-boat full-house textures. The postflop commitment gate evaluated equity against a *static* `PRIOR_RANGE_TIGHT` instead of the villain's actual jamming range, so on paired boards it stacked off at ~0.21 (trip-K on `KK7`) and ~0.00 (dry second pair) true equity. Red-team `LEAK-1` (`consult/artifacts/2026-06-03-redteam/REDTEAM_REPORT.md:64-92,220-233`); deployed gauntlet edge-RED (`STATUS.md:662-744`).
2. **The process (discipline).** A leak-PATCHED finals RC (`v_final.zip` == `v_finals_rc_patched.zip`, SHA `b108eff5…`) was built and is validator+edge green, but **an overnight agent autonomously uploaded the unpatched `d54640e0` build to R2 before the red-team/edge evidence was reconciled** (CLAUDE.md upload rule added 2026-06-03 in response). The repo then accumulated near-identically-named zips across worktrees, `d54640e0` was never a git commit, and `b108eff5` was never committed — so branch names / `git show` / `submissions/v_final/` all disagreed with the actual shipped bytes.

**Net:** we qualified (#57/64) on the *leaked* bot; the *better* (patched) bot never went live. Finals baseline must therefore be `b108eff5`, not the R2 artifact.

## Process Mistakes (where time/edge leaked)
- **Over-broad verification instead of one clean ship lane.** 2026-05-27→31 spent on many parallel patch/benchmark lanes (away-swarm 7 lanes mostly `SHIP_LOCKED`/`NOT_PROMOTABLE`; six-max pod RED/AMBER variance) that did not change the artifact (`STATUS.md:362-526`; `consult/artifacts/2026-05-29-away/SUMMARY.md:13-21`).
- **Solver rabbit-holes, correctly gated but costly.** MCCFR/CFR+/Deep-CFR repeatedly explored then auto-gated off (`STATUS.md:76-85,379-410`). The Solver policy in CLAUDE.md exists precisely to bound this; it should have triggered a halt sooner.
- **Artifact discipline was the actual failure, not strategy ideas.** Multiple conflicting "final" decisions on 2026-06-03 (`d54640e0` uploaded → `be7503d3` do-not-promote → `e4b4a8f1` SIMPLE → `b108eff5` patched-but-not-uploaded), with the live upload happening mid-churn.

## Finals Strategy (decision)

**SHIP the patched `b108eff5` baseline as-is. Freeze the code. Verify, then human-gated upload before 18:00 UTC.** (Oracle synthesis `new-chat-1FB6CB`, 2026-06-04.)

- **Why not de-risk toward Nash (lower variance):** we are the #57/64 underdog in a single-elim bracket; lower variance helps the favorite. Our high-variance aggression (AF 5.45) is an asset when we must beat specific opponents. Also would require firing repeatedly-gated-off CFR code under deadline. **Hard no.**
- **Why not hand-tune field exploits in code:** the exploitation overlay already ships — `opponent_model.exploit_shift()` returns bounded per-cluster shifts (`MAX_DEVIATION_PP=0.20`) after a 30-hand warmup vs `field_priors.npz`, consumed by `postflop.decide_postflop`. In 400-hand matches the tight field (Looper257 fold 70.5%, TheHouse 74.2%, winning 74.5%, G-Forge 73.1%, TheQuantBot 69.1%; stations CrimsonBot/Khan't Fold) gets punished for free. Editing an unbenchmarked, uncommitted, leakage-flagged artifact repeats the R2 discipline failure. **No.**
- **Honest caveat (do not oversell variance):** `call 6.4% / fold 58.9%` is *extreme* polarization. It prints vs the over-folding majority but is a real exploitable hole vs a sharp counter-exploiting seed (likely R1 draw), who can bet-fold us off pots — mean EV vs a strong seed may be negative. (a) keeps us *alive*; it is not "winning," and we can't safely de-polarize today.

### Residual leaks in the patched gate (code-verified, `patched_src/src/commitment.py`)
| # | Texture | Mechanism | Severity / Freq |
|---|---------|-----------|-----------------|
| C | Dry unpaired bloated pot (TPTK/overpair) | `commitment.py:56` `eq >= SAFE_EQ_THRESHOLD (0.55)` vs *static* range — same class as the original leak, more common texture | High / Medium |
| A | Trips on board (e.g. `99` on `777`) | `full_house_dominated` only checks board *pairs above our trips*; misses higher boats from over-pairs/case card | High / Low |
| B | Monotone connected board | `commitment.py:54-55` nut-flush path jams into a possible straight flush | High / Very low |
| bleed | Repeated barrels | `can_call_large` (`:69`) caps each call at 25% owed but not *cumulative* commitment | Medium / Medium |
| preflop | n/a | Gate is **postflop-only**; if our 56% bust is 3-bet/4-bet-jam-driven, the gate does nothing — preflop code (`preflop_lookup.py`, `bot.py` routing) NOT yet audited | Potentially dominant / **Unverified** |

## Recommendations (pre-18:00, lowest-risk → contingent)
1. **Freeze `b108eff5` source. Do not edit bot code.** Any edit re-opens validator/edge/leakage surface that cannot be re-smoked in time.
2. **Targeted verification of the exact `b108eff5` zip (test-side only):**
   a. Probe the three residual spots (dry-board TPTK into a set in a bloated pot; `99` on `777`; A-high flush on monotone connected board) — assert non-jam.
   b. Re-run the `dominated_underboat_near_dead_commitment` discriminator vs this zip — confirm R2 leak stays fixed.
   c. **Run the deferred Docker smoke** (`tools/smoke_run.py --zip submissions/v_final.zip`) — converts "smoke-not-run" into evidence.
   d. H2H vs 3 seeds (LAG≈NecessarySkew/Oxvard, nit≈Looper257/winning, station≈CrimsonBot) **logging bust-origin by street** — the headline is *where we bust*, not win-rate. If busts are preflop, the commitment-gate analysis answered the wrong question.
3. **Commit the `b108eff5` source to git** (extract `patched_src/` into the tree) so the finals artifact is reproducible — current state is zip-only.
4. **Human-gated upload with SHA verification** of `b108eff5…` (verify bytes, not a directory/branch name). Per CLAUDE.md upload policy, Farhad performs the upload.
5. **Contingent code fix (only if 2a/2d produces a real bust):** smallest change — extend `full_house_dominated` to flag trips-on-board domination, or guard the dry-board `SAFE_EQ_THRESHOLD` behind a paired-or-trips/range check. Never speculative.

## Preventive Measures
- **One ship lane, one green artifact.** `best_green.zip` is the single source of truth; every candidate diffs against it by SHA, not by name.
- **Upload is human-only, always** (already codified 2026-06-03). No overnight/background agent may submit.
- **Commit shipped bytes.** Never ship a zip whose source isn't in git; tag the commit with the artifact SHA.
- **Trigger the Solver halt rule earlier** (two non-improving training attempts → stop), per CLAUDE.md Solver policy.
- **Verification must target known residuals**, not generic H2H — a clean run that never deals the leak texture is false comfort.

## Investigation Log
- Standing + finalist field + per-bot stats pulled from portal Supabase REST (bearer-token, read-only) → `consult/artifacts/2026-06-04-finals-recon/raw/`.
- Leak / patched-baseline / timeline: pair investigator (Codex `gpt-5.5-fast` xhigh), evidence in `## Investigator Findings` above; load-bearing claims spot-checked (zip SHAs, `commitment.py` residuals).
- Strategy: oracle synthesis `new-chat-1FB6CB`.
