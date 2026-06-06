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
