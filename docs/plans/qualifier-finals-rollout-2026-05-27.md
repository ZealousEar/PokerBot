# Qualifier → Finals rollout plan (2026-05-27)

## Goal

Carry canonical `submissions/v_final.zip` sha `e4b4a8f1…598` intact through the 2026-06-01 qualifier upload, then convert the 2026-06-02 patch window + 4-day finals runway into a verified Famadeo-targeted candidate (PATCH-2A bounded EV veto in `src/postflop.py`) gated by the full artifact-bound gauntlet.

Split into:
- **Phase A (pre-qualifier, 2026-05-28 → 2026-06-01):** Protect the artifact. Verify lock-in. Optionally build promotion-risk-reduction tooling. No HYGIENE-1 rebuild. No speculative PATCH-2 promotion.
- **Phase B (post-qualifier, 2026-06-02 → 2026-06-05):** Wire the analyzer→overlay producer/consumer gap, execute the patch-window flow, design and gauntlet PATCH-2A; only attempt PATCH-2B (range-conditioned cross-module) if PATCH-2A is clean.

## Background

### Ship-state floor (decided pre-plan, recorded in `consult/artifacts/2026-05-27-worktree-audit/MAP.md`)

- Canonical artifact: `~/Code/PokerBot/submissions/v_final.zip` sha `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`. Byte-identical to `best_green.zip` and all three worktree copies.
- Audit-passed at 2026-05-22 release branch promotion (`release/v_final-e4b4a8f1` HEAD `a00561c`): template +71.82 / aggressor +112.63 / math +144.60 / shark +70.16 / ref_bot_2 +144.60 (paired-seed-base 42, hands 10000); overlay gain +32.53; ratchet v0 +74.41 / v1/v2/v3 +18.89; LBR preflop 18.0 / aggregate 7.4 mbb/g; validator 4/4; smoke 200/200.
- Re-validated 2026-05-27 by orchestrator on canonical worktree: validator ✅ PASSED 4/4 TEST_STATES, real strategy code firing (raise 200 / raise 200 / fold / all_in).
- `tools/package.py` embeds build-time timestamps → re-packaging changes the SHA. Treat the artifact as immutable through 2026-06-01.

### Env-var hygiene resolved without rebuild (`consult/artifacts/2026-05-27-worktree-audit/MAP.md §1a`)

- Packaged `src/bot.py:39` reads `_OVERLAY_DISABLED = os.environ.get("POKERBOT_DISABLE_OVERLAY") == "1"`. Flagged by `audit_strategy_leakage`.
- Engine sandbox `ext/fullhouse-engine/sandbox/match.py:131-133` passes only `-e ACTION_TIMEOUT -e BOT_PATH -e BOT_DATA_DIR` into the Docker container; the host's `os.environ` is NOT forwarded.
- `POKERBOT_DISABLE_OVERLAY` is absent from the entire `ext/fullhouse-engine/sandbox/` tree. Validator AST scan does not reject `os.environ.get(...)`.
- Therefore the env-var defaults `False` in the sandbox → overlay runs normally. The flag is internal-hygiene only, not a qualifier risk. HYGIENE-1 rebuild is **skipped** for Phase A.

### Today's failed-patch evidence (`PokerBot-claude/consults/2026-05-27-*/SUMMARY.md`)

- **CONFIRM-1**: v5 light-3-bet recalibrated to bb/100 −54.14 (was −135.76 at Lane T; 2.5× inflation from seed-42 bust cluster). Real but smaller; literal `LIGHT3BET_CONFIRMED` near the −50 floor.
- **CONFIRM-1b**: v1–v4 SYNTHETIC_FINALS_FIELD_MOSTLY_NOISE; 0/4 at −50 floor calibrated. Finals-field-specific patching deprioritized vs real-world matchups.
- **PATCH-1 A**: `DO_NOT_PROMOTE`. v5 lift only +7.09 bb/100 (floor +25); LBR aggregate regression +53.6 > +20 budget; neel public-bot regression −28.67 bb/100.
- **PATCH-1 reconcile**: `PATCH1_NET_NEGATIVE`. 1 HELPS (dominic), 1 HURTS (neel), 2 NEUTRAL (famadeo + vladimir indeterminate). Shelved. PATCH-2 famadeo EV veto is the next target.

### Famadeo exploit shape (from Phase 1.5 probe; refs in `ext/public-bots/famadeo/bots/codex_holdem/bot.py`)

- Range/pressure-aware tightening: classifies opponent postflop pressure → tightens ranges (`bot.py:690-729`).
- EV veto on big bets/calls when realized equity under multiway/wet/low-SPR taxes is worse than passive EV (`bot.py:2169-2232`).
- Real-world loss against famadeo: −21.54 bb/100 (`PokerBot-claude/consults/2026-05-27-overnight-B/famadeo/SUMMARY.md`).
- Watch-target risk vector for PATCH-2A: bots like neel that exploit our overfolds via slow-grind (PATCH-1 turned neel into a high-variance chip-flip and was a −27.46 bb/100 confirmed regression).

### Postflop seams for PATCH-2A (from Phase 2 probe; refs in `PokerBot-codex/src/postflop.py`)

- **Primary insertion seam**: `_equity_turn_river_action()` at `postflop.py:333-365` — has equity, pot, owed, stack, street, raise/check/call/fold routing.
- **Fallback insertion seam**: `_heuristic_postflop_action()` at `postflop.py:154-176` — used when equity unavailable/over-budget.
- **Orchestration**: `decide_postflop()` at `postflop.py:367-380` — current order: patched response → flop blueprint → turn/river equity → heuristic. Veto must not bypass fixed-response cells.
- Bot-side route: `src/bot.py:104-111` sends `flop|turn|river` directly into `_decide_postflop`.

### Helper functions PATCH-2A would need (absent in `postflop.py`)

| Helper | Status | Closest existing |
|---|---|---|
| `multiway_count()` | absent | raw `len(players)` inside `_response_patch_key()` at `postflop.py:128-138` |
| `board_wetness()` | absent | private `_flop_bucket()` hash at `postflop.py:190-200` (not semantic) |
| `made_hand_class()` | absent | `_hand_strength_bin()` at `postflop.py:205-248` mixes made + draw bonuses |
| `draw_proxy()` | absent | `_hand_strength_bin()` adds texture bonuses at `postflop.py:239-245` |
| `recent_raise_depth()` | absent | `action_log` present in state but unused inside `postflop.py` |

### Equity API surface (`PokerBot-codex/src/equity.py`)

- Single public API: `equity_vs_range(hero, board, villain_range, trials=2000)` at `equity.py:22-61`.
- Current postflop usage: `_equity_for_state()` at `postflop.py:309-330` calls with `trials=_EQUITY_TRIALS` (160; `postflop.py:25`).
- Budget-aware at call site (deadline wrapper `postflop.py:321-328`), NOT inside `equity.py`.

### Tests that must keep passing (PATCH-2A must NOT break)

| Test | Lines | What it asserts |
|---|---|---|
| `test_postflop_wiring.py` | 42-67 | blueprint/fallback postflop routing |
| `test_equity_wiring.py` | 28-88 | high-equity call + over-budget fold paths |
| `test_lbr_spot_corrections.py` | 38-67 | exact LBR spot actions incl. multiway/short-stack |
| `test_legal_actions.py` | — | legal action contract |
| `test_hardening_cases.py` | — | sizing legality, side-pot/all-in, budget fallback |
| `test_overlay_bounded.py` | — | preflop overlay bounds |

### Patch-window producer/consumer gap (Phase 2 probe)

- **Producer** (`PokerBot-claude/tools/analyze_hand_histories.py`, branch `patch-window-prep-2026-05-27`, +427/−81 LOC, 557 LOC total): `_aggregate()` (`:384`) + `main()` (`:459-492, :548`) write `np.savez_compressed(out, **stats)` with keys `vpip`, `pfr`, `af`, `fold_to_cbet`, `avg_sizing_{preflop,flop,turn,river}`, `top_preflop_sequences`, `top_preflop_counts`, `n_records`, `n_players`, `schema_keys`, `parse_quality`.
- **Consumer**: **NOT FOUND**. No `finals_priors`, `np.load`, or priors load function in `PokerBot-codex/src/bot.py` or `src/opponent_model.py`. The overlay is RUNTIME-only: `_pressure_preflop_overlay` (`bot.py:153-159`) reads from `OpponentModel.archetype_features` (`opponent_model.py:71-134`) which derives posterior from `match_action_log` / `action_log`, NOT from npz priors.
- **Fallback**: No `os.path.exists` / `try np.load` for finals priors. Missing file = no effect (because nothing reads it). General `decide()` safety: try/except → fold (`bot.py:282-295`).
- **Implication for Phase B**: 2026-06-02 patch-window plan-of-record is INCOMPLETE. We need to add a priors consumer before the priors can influence strategy. This is a P0 Phase B work item.

### Patch-window-prep landing (already complete)

- Branch `patch-window-prep-2026-05-27` in `PokerBot-claude` worktree:
  - `1172fd7` Harden hand history analyzer schema parsing (+427/−81 LOC).
  - `97507a7` Add analyzer schema hardening tests (+234 LOC).
- Verification: `pytest tests/integration -x` → 9 passed in 0.35s. Capabilities added: normalized alias matching, action synonyms, street-nested flattening, parse_quality npz diagnostics.

### Overnight-2 plan deprecation

- `docs/plans/overnight-2-2026-05-28.md` is **superseded** by this plan per user directive ("Refactor: dissolve OVERNIGHT-2 into the Phase A / Phase B structure"). Useful lanes (L1/L2 lock-in, R1/R2 patch-window rehearsal, W1 famadeo audit) are absorbed; W3 finals projection becomes a Phase B work item; the 22-lane KANBAN template is abandoned.

## Approach

**Phase A — Protect, verify, ship.** Treat `submissions/v_final.zip` sha `e4b4a8f1…598` as immutable through 2026-06-01. All verification runs against the existing byte sequence; nothing is repackaged (per MAP.md §1a — `tools/package.py` embeds timestamps and changes the SHA). Reproduce the G1–G11 gauntlet from a clean checkout of `release/v_final-e4b4a8f1` to neutralize main-worktree drift, then bracket the upload with a 10× sandbox smoke that the standard 200-hand smoke can't surface. HYGIENE-1 rebuild is explicitly skipped (the env-var hygiene flag does not fire in the Docker sandbox per MAP.md §1a). Leaderboard tooling is conditional: include only if it makes low-sample / wide-CI cells unmistakable; otherwise drop with a one-line rationale committed back into this plan.

**Phase B — Wire the gap, audit before patch, default to no-promote.** The patch-window playbook (`docs/playbooks/patch-window.md` §4) assumes the priors consumer exists; Background confirms it does not. The plan therefore lands the consumer (B3, P0) before the 2026-06-02 producer run is meaningful. Famadeo is the only confirmed real-world deficit at promotion magnitude (`PokerBot-claude/consults/2026-05-27-overnight-B/famadeo/SUMMARY.md`, −21.54 bb/100); audit it first to decide if the loss is concentrated enough for PATCH-2A scope (postflop-only EV-veto in `PokerBot-codex/src/postflop.py`). PATCH-2B remains optional and gated on PATCH-2A clearing every artifact-bound bar.

**Sequencing.** A1 anchors A2/A3 (no verified baseline → no qualifier upload). B1+B2 run parallel to Phase A. B3 is P0 and blocks **B9 only** (B7 is structural-only and runs parallel to B3, recovering 3–4 h of finals wall). B4 governs entry into PATCH-2A; if W1 verdict is "diffuse," skip B7/B8 and ship qualifier artifact unchanged for finals. B9 runs the patch-window playbook on real histories only after B3 is green. B10 defaults to the qualifier artifact unless B8 AND B9 both clear with stat-sig improvement.

**Artifact-bound gauntlet command set (promotion gate, per `consult/artifacts/release/RELEASE_NOTES.md` G1–G11):** `tools/import_audit.py --max-seconds 1.5 --max-mb 400`; `pytest tests/edge_cases -x`; `ext/fullhouse-engine/sandbox/validator.py <zip>`; `tools/package.py --strict`; `tools/smoke_run.py --hands 200`; `tools/audit_strategy_leakage.py --zip <zip>`; `tools/exploit_check.py --zip <zip>`; `tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42`; `--ablate-overlay --hands 10000`; `--self-play --vs-prior --hands 10000`. PATCH-2A adds famadeo paired-seed h2h (base 142 + 242) plus public-bot regression vs `{dominic, neel, vladimir}`.

**Worktree discipline.**
- `~/Code/PokerBot/` + new `gauntlet/` checkout of `release/v_final-e4b4a8f1`: ship verification, qualifier upload, A1/A2/A3.
- `~/Code/PokerBot-claude/`: analyzer rehearsal, schema fuzz, decision audits, finals projection, patch-window producer side (B1/B2/B4/B6 + B9 producer phases).
- `~/Code/PokerBot-codex/`: priors-consumer wiring, PATCH-2A postflop implementation + tests, PATCH-2A gauntlet (B3/B7/B8). Never modify canonical `submissions/v_final.zip` or `submissions/manifest.json` outside the documented promotion protocol.

**Budgets are guidance, not gates.** LOC budgets and wall-clock estimates in each item are sizing aids for the engineer; the artifact-bound gauntlet and acceptance-rule language are the load-bearing promotion gates.

## Work Items

### Phase A — Pre-qualifier protection (2026-05-28 → 2026-06-01)

#### A1 — Release-branch lock-in gauntlet
- **Goal:** Reproduce G1–G11 against canonical `submissions/v_final.zip` sha `e4b4a8f1…598` from a clean checkout of `release/v_final-e4b4a8f1` HEAD `a00561c` so a STATUS-formatted GREEN block exists that's independent of any uncommitted worktree state.
- **Done when:** STATUS-format block cites every actual metric vs `RELEASE_NOTES.md` baselines (template +71.82, aggressor +112.63, math +144.60, shark +70.16, ref_bot_2 +144.60; overlay gain +32.53; LBR preflop 18.0 / aggregate 7.4); paired-seed deltas inside variance band; log committed to `consult/artifacts/2026-05-31-ship-lock/L1_gauntlet.log`.
- **Key files:** `consult/artifacts/release/{RELEASE_NOTES.md,gauntlet.log}`, `consult/artifacts/2026-05-27-worktree-audit/MAP.md`, `docs/playbooks/hardening.md`.
- **Dependencies:** none.
- **Size:** ~75 min wall.

#### A2 — 10× pre-upload Docker smoke
- **Goal:** Run canonical `v_final.zip` through `tools/smoke_run.py --hands 2000` in the real Docker sandbox against `{template, aggressor, mathematician, shark, ref_bot_2}` — catches slow-leak / late-game failures the standard 200-hand smoke misses.
- **Done when:** 5 × 2000 hands, 0 errors per opponent, p99 `decide()` < 1.5 s, max < 2.0 s; `L2_SUMMARY.md` rows of `{opponent, hands, errors, p99_ms}`; logs at `consult/artifacts/2026-05-31-ship-lock/L2_smoke_2000hands_<opponent>.log`.
- **Key files:** `tools/smoke_run.py`, `ext/fullhouse-engine/sandbox/match.py`, `submissions/v_final.zip`.
- **Dependencies:** A1.
- **Size:** ~40 min wall.

#### A3 — Qualifier upload execution
- **Goal:** Execute `docs/morning-promotion-checklist.md` §8 ship-day sequence on 2026-06-01; upload canonical `v_final.zip` unchanged.
- **Done when:** portal confirmation hash matches `e4b4a8f1…598`; `STATUS.md` "## QUALIFIER SUBMITTED 2026-06-01" entry committed with timestamp and portal hash; release commit tagged `v_final-e4b4a8f1`.
- **Key files:** `docs/morning-promotion-checklist.md`, `STATUS.md`, `submissions/{v_final.zip,best_green.zip,manifest.json}`.
- **Dependencies:** A1, A2.
- **Size:** ~20 min wall.

### Phase B — Post-qualifier finals push (2026-06-02 → 2026-06-05)

#### B1 — Schema variant rehearsal of `analyze_hand_histories.py`
- **Goal:** Synthesize ≥6 schema variants beyond `tests/integration/test_analyze_{aliases,smoke}.py` coverage — engineer chooses the canonical set, drawing from: camelCase nested, abbreviated street names, deep wrapper levels, malformed/NaN amounts, BB-vs-chips sizing, 6-seat multiway, mixed casing, JSONL.
- **Done when:** ≥85 % of chosen variants succeed end-to-end (no crash, `parse_quality.records_parsed > 0`, ≥1 metric extracted); any failure logged as P0 reproducer; summary at `consult/artifacts/2026-06-02-patch-window-prep/R1_SUMMARY.md`.
- **Key files:** `PokerBot-claude/tools/analyze_hand_histories.py` (post-hardening, 557 LOC, lines 384/459–492/548), `tests/integration/test_analyze_aliases.py`.
- **Dependencies:** none; parallel to Phase A.
- **Size:** ~60 min wall.

#### B2 — Adversarial schema fuzzing
- **Goal:** Generate 50 randomly-mutated schema fuzzes from a seed JSON; run analyzer against each; surface any crash, infinite loop, or `parse_quality.records_parsed == 0`.
- **Done when:** zero crashes, ≤5 % records_parsed==0 outcomes; `R2_SUMMARY.md` (≤200 words) lists any non-zero exit; fuzzer script committed for future regression use.
- **Key files:** `PokerBot-claude/tools/analyze_hand_histories.py`.
- **Dependencies:** none.
- **Size:** ~30 min wall.

#### B3 — P0: Priors consumer plumbing
- **Goal:** Wire `data/finals_priors.npz` into the runtime overlay so a 2026-06-02 patch-window producer run actually influences strategy. Producer keys at `PokerBot-claude/tools/analyze_hand_histories.py:384,459-492,548`: `vpip / pfr / af / fold_to_cbet / avg_sizing_* / top_preflop_sequences / top_preflop_counts / n_records / n_players / schema_keys / parse_quality`. **Pin a minimum mapping**: `vpip` and `pfr` shift the per-archetype prior used by `OpponentModel.archetype_features` (`PokerBot-codex/src/opponent_model.py:71-134`); `af` and `fold_to_cbet` adjust the bounded deviation magnitude (`MAX_DEVIATION_PP`) used downstream in `_pressure_preflop_overlay` (`src/bot.py:153-159`). Engineer owns: scaling function shape, warmup-hook location, whether more keys are read. Patch-window playbook §4 assumes this exists.
- **Done when:** cold-import still <1.5 s / <400 MB; missing-file path is a no-op (engine sandbox MUST not crash if priors absent); existing tests pass (`test_overlay_bounded.py`, `test_legal_actions.py`, `test_hardening_cases.py`, `test_postflop_wiring.py`, `test_equity_wiring.py`, `test_lbr_spot_corrections.py`); ≥1 new unit test proves a known prior deterministically shifts a posterior bound in a documented direction; validator + leakage audit clean.
- **Key files:** `PokerBot-codex/src/opponent_model.py:71-134`, `src/bot.py:153-159`, `PokerBot-claude/tools/analyze_hand_histories.py:384`, `tests/edge_cases/test_overlay_bounded.py`.
- **Dependencies:** B1, B2.
- **Size:** ~3–4 h.

#### B4 — W1 famadeo decision audit (concentration verdict)
- **Goal:** Capture 5000-hand v_final vs famadeo replay; cluster losses by `(street, position, hero_action, board_texture)`; rank top-5 EV-loss spots by mbb/g; determine whether the −21.54 bb/100 deficit is concentrated (top-2 explain >50 %) or diffuse. Leak-naming schema for `top5_leaks.md`: `<street>__<position>__<hero_action>__<board_texture_bucket>` (e.g. `turn__BTN__cbet__wet_paired`). Engineer chooses the `board_texture_bucket` enumeration; B7 acceptance tests reference leak names from this output.
- **Done when:** `consult/artifacts/2026-06-02-weakness-w1-famadeo/{decision_clusters.json, top5_leaks.md, SUMMARY.md}` exists; each leak's mbb/g impact >5; SUMMARY emits a one-sentence concentration verdict that gates B7; one-line dominic-comparison appendix in SUMMARY confirms or refutes the −4.31 bb/100 baseline at the same paired-seed bases (folded in from former W2).
- **Key files:** `ext/public-bots/famadeo/bots/codex_holdem/bot.py:690-729, 2169-2232`, `PokerBot-claude/tools/h2h.py`, `PokerBot-claude/consults/2026-05-27-overnight-B/{famadeo,dominic}/SUMMARY.md`.
- **Dependencies:** A3 (qualifier upload completed).
- **Size:** ~100 min wall.

#### B5 — W3 recalibrated finals projection
- **Goal:** Patch the finish-distribution Monte Carlo in `PokerBot-claude/consults/2026-05-27-overnight-E/SUMMARY.md` using today's calibrated priors: v5 light-3bet 2.5× smaller (CONFIRM-1), Lane T mostly noise (CONFIRM-1b), famadeo confirmed worst real matchup. Emit updated P(top64) / P(top5) / P(top1).
- **Done when:** `consult/artifacts/2026-06-02-finals-projection/W3_recalibrated.md` (≤500 words) lists the three updated probabilities with one sentence per claim citing the today-evidence that shifted the prior, and recommends ship-as-is vs build-finals-candidate.
- **Key files:** `PokerBot-claude/consults/2026-05-27-overnight-E/SUMMARY.md`, `PokerBot-claude/consults/2026-05-27-confirm-light3bet/SUMMARY.md`, `PokerBot-claude/consults/2026-05-27-confirm-light3bet-v14/SUMMARY.md`, `PokerBot-claude/consults/2026-05-27-patch1-reconcile/SUMMARY.md`.
- **Dependencies:** B4.
- **Size:** ~20 min wall.

#### B7 — PATCH-2A design + implementation (conditional) [SHELVED 2026-05-28]

**SHELVED 2026-05-28** per user directive (Q1 Option 1) after B4 invalidated the premise. The famadeo deficit collapsed from −21.54 bb/100 (overnight-B 4379 hands) to −5.34 bb/100 (50191 hands, CI [−13.23, +3.16]) — ~1/7 the magnitude PATCH-2A was scoped for. Building a 90–130 LOC postflop EV-veto for that signal fails the impact-vs-regression-risk math (inverted PATCH-1 trap). See `STATUS.md` 2026-05-28T01:35:00Z Phase B refactor entry.
- **Goal:** If B4 verdict = "concentrated" AND B5 supports finals patching: implement bounded postflop EV-veto in `PokerBot-codex/src/postflop.py` only, plugging into `_equity_turn_river_action()` (lines 333–365) and `_heuristic_postflop_action()` (lines 154–176) routed through `decide_postflop()` (lines 367–380) AFTER the fixed-response cells. **Veto rule (load-bearing decision, pinned):** mirror famadeo's pattern at `ext/public-bots/famadeo/bots/codex_holdem/bot.py:2169-2232` — when (board is wet OR multiway OR effective SPR low) AND hero's made-hand class would commit a stack-meaningful chunk, fold IF `equity_vs_range(hero, board, villain_range, trials=160) * (pot + bet) < passive_EV(call_or_check) + safety_cap_mbb`. **Bet-classification framing (vladimir-robust, per 2026-05-27 consult):** classify villain bets by *ratio buckets* (`bet / pot ∈ [≤0.33, 0.34–0.66, 0.67–1.25, 1.26–1.49, ≥1.5]`), NOT by exact sizes. This handles vladimir's off-grid 0.27× and 1.72× pot sizes (visible in `ext/public-bots/vladimir/bots/vlad/deep_cfr_cpp/src/config.hpp`) without copying his sizing tree (explicitly forbidden by `docs/finals-strategy-2026-05-27.md` §4.4 and KANBAN "Action abstraction — explicitly DO NOT adopt"). Bucket thresholds inform the `safety_cap_mbb` and `villain_range` tightening. Engineer owns: helper function names/signatures (semantic dimensions are multiway count, board texture, made-hand class, draw proxy, action-log depth, bet-ratio bucket), `safety_cap_mbb` value per bucket, exact `villain_range` construction, and short-stack/raise-vs-call branches. Approximate budget: 90–130 LOC in `postflop.py` only; the budget is guidance, the gauntlet is the gate. No `src/bot.py`, `src/preflop_lookup.py`, `src/equity.py`, `src/opponent_model.py` edits; no env-var branches; no opponent-identity strings.
- **Done when:** all existing postflop/equity/LBR tests pass; ≥2 new edge-case tests in `tests/edge_cases/test_postflop_veto.py` cover the leak names that B4 emitted (each test references the `<street>__<position>__<hero_action>__<board_texture_bucket>` key it asserts behavior for); `audit_strategy_leakage` clean; import budget intact; `tools/package.py --strict` builds.
- **Key files:** `PokerBot-codex/src/postflop.py:154-380`, `src/equity.py:22-61`, `tests/edge_cases/test_{postflop_wiring,equity_wiring,lbr_spot_corrections,hardening_cases,legal_actions}.py`, `consult/artifacts/2026-06-02-weakness-w1-famadeo/top5_leaks.md`.
- **Dependencies:** B4 ("concentrated" verdict), B5 (supportive verdict). NOT B3 — PATCH-2A is structural-only and does not read priors at runtime, so B7 can run parallel to B3.
- **Size:** ~4–6 h.

#### B8 — PATCH-2A artifact-bound gauntlet [SHELVED 2026-05-28]

**SHELVED 2026-05-28** — downstream of B7 which was shelved. Vladimir-specific concern was addressed by a standalone audit (`consult/artifacts/2026-06-04-weakness-vladimir/`, 30,228 hands, 3 paired-seed bases) showing hero +119.78 bb/100 CI [+98.78, +141.08] against vladimir — no vladimir-specific patch indicated. See `STATUS.md` 2026-05-28T03:00:07Z Vladimir audit entry.
- **Goal:** Run the full G1–G11 set against the patched artifact, plus famadeo paired-seed h2h at bases 142 and 242 (≥100 matches each), plus **vladimir paired-seed h2h at bases 142 and 242 (≥20k hands each, ≥100 matches per base)** — elevated from regression-guard to first-class acceptance gate per 2026-05-27 consult, because our current vladimir evidence (Lane B 1085 hands, CI [−16, +40]) is statistically inconclusive and vladimir's Deep CFR → numpy runtime is the highest-skill threat in the public field. Plus public-bot h2h regression vs `{dominic, neel}`.
- **Done when:** STATUS-format block with all metrics; acceptance: famadeo Δ ≥ +15 bb/100 with paired CI excluding 0; **vladimir paired Δ mean > 0 with CI low > −20 across BOTH bases 142 and 242** (rejects the soft-PASS Lane B accept-gate; requires consistent positive signal at higher statistical confidence); no public-bot HURTS (no opponent's paired Δ CI excluding 0 on the negative side, mirroring the rollup rule that shelved PATCH-1); LBR aggregate Δ ≤ +20 mbb/g; LBR caps preserved (preflop ≤ 100, aggregate ≤ 200); every gauntlet step PASS. Any failure → `DO_NOT_PROMOTE`; candidate parked under `PokerBot-codex/submissions/` only; qualifier `v_final.zip` ships for finals unchanged (per `docs/playbooks/patch-window.md` Phase 9b rollback rule, which is the safe default; per engine README the patch-window upload is **one-shot** — `"You can submit one updated bot before D5"` — so the rollback decision is irreversible).
- **Key files:** `tools/{benchmark,h2h,exploit_check,audit_strategy_leakage,package,import_audit,smoke_run}.py`, `docs/playbooks/{hardening,patch-window}.md`.
- **Dependencies:** B7.
- **Size:** ~3–4 h wall.

#### B9 — Patch-window execution on real histories
- **Goal:** On 2026-06-02 morning execute `docs/playbooks/patch-window.md` Phases 0–9 against released hand histories: download → manual schema inspection → hardened analyzer → sanity-gate priors → bounded overlay-parameter tuning (only meaningful because B3 consumer is in place) → repackage → smoke/import/edge/leakage → regression bench → manual review → promote-or-rollback.
- **Done when:** either (a) finals artifact promoted with STATUS-format block and every gate GREEN, OR (b) rollback executed and qualifier artifact ships for finals. Rollback is the safe default.
- **Key files:** `docs/playbooks/patch-window.md`, `PokerBot-claude/tools/analyze_hand_histories.py`, `PokerBot-codex/src/opponent_model.py`, `data/finals_priors.npz`, `PokerBot-claude/consults/2026-05-27-overnight-D/priors/V*_priors.npz` (Phase 2.5 fallback).
- **Dependencies:** B3.
- **Size:** ~5–6 h wall over the 24-h window.

#### B10 — Finals upload decision + execution
- **Goal:** On 2026-06-03 evening decide ship target: if B8 cleared AND B9 promoted, upload PATCH-2A finals artifact; else upload qualifier `v_final.zip` unchanged.
- **Done when:** portal-side confirmation matches chosen artifact SHA; `STATUS.md` "## FINALS RESUBMITTED 2026-06-03" or "## FINALS ROLLBACK 2026-06-03" entry committed with 3–4 sentence rationale citing the gates that fired.
- **Key files:** `docs/finals-strategy-2026-05-27.md` §2, `docs/playbooks/patch-window.md` §9.
- **Dependencies:** B8, B9.
- **Size:** ~30 min wall.

### Phase C — PATCH-2B (optional; gated)

#### C1 — PATCH-2B scope + run (single conditional item) [AUTO-SHELVED 2026-05-28]

**AUTO-SHELVED 2026-05-28** — entry condition required "B8 cleared by ≥+15 bb/100 vs famadeo with zero public-bot HURTS". B7/B8 both shelved; entry condition cannot fire.
- **Goal:** Only enter if B8 cleared by ≥+15 bb/100 vs famadeo with zero public-bot HURTS and ≤+10 mbb/g LBR aggregate creep, AND the 06-02 → 06-03 queue (B4 → B7 → B8 → B9) finished with ≥6 h of wall remaining before the 06-05 finals close. If both conditions hold: scope range-conditioned cross-module work (`PokerBot-codex/src/preflop_lookup.py` + `src/postflop.py`), build it, run the B8 gauntlet against the new artifact. Drop entirely if either condition fails.
- **Done when:** either (a) `consult/artifacts/2026-06-04-patch2b/SCOPE.md` + new artifact + gauntlet log committed and finals ship target updated; or (b) one-line "do-not-pursue" rationale appended back into this plan citing the failed entry condition.
- **Key files:** `PokerBot-codex/src/preflop_lookup.py`, `src/postflop.py`, plus new tests under `PokerBot-codex/tests/edge_cases/`.
- **Dependencies:** B8 clean AND B9 closed with wall remaining.
- **Size:** ~8–10 h if executed, ~5 min if dropped.

### Phase D — Shadow Deep CFR red-team lane (optional; explicitly non-shipping)

**Frame (added 2026-05-27 per ChatGPT consult).** Deep CFR's prior rejection rationale was partly incorrect: "no GPU" no longer applies (user willing to rent), and "export pipeline ungated" was refuted by vladimir's working `gto_strategy.npz` + numpy MLP forward pass at `ext/public-bots/vladimir/bots/vlad/bot.py`. The corrected rejection is calendar/validation-bound: a 9-day window cannot train, integrate, gauntlet, and statistically prove a new neural policy beats `v_final.zip` sha `e4b4a8f1…598`. Phase D therefore uses Deep CFR as a RED-TEAM SPARRING OPPONENT only — never as a promoted ship artifact.

#### D1 — SHADOW-CFR-1 scope + GPU rental decision (single conditional item) [AUTO-SHELVED 2026-05-28]

**AUTO-SHELVED 2026-05-28** — entry trigger required "B8 cleared the gauntlet against `v_final.zip` and against vladimir h2h". B8 shelved (B7 invalidated by B4). Vladimir h2h audit completed standalone showing hero +119.78 bb/100 — no neural sparring opponent needed; existing public-bot field is well-characterized.
- **Goal:** Only enter if ALL three triggers fire: (1) B8 cleared the gauntlet against `v_final.zip` and against vladimir h2h (bases 142+242), (2) ≥24 hours wall remaining before 2026-06-05 finals close, (3) explicit user approval to rent a GPU (estimated 1× A100 or H100 on RunPod / Lambda, ~12–24 h, ~£30–80 total). If triggers fire: rent box, set up a Python 3.10 + PyTorch + numpy training env, port or adapt vladimir's `bots/vlad/deep_cfr/{train.py,networks.py,export.py,config.py}` PyTorch loop (do NOT use his C++ MCCFR stack — Windows .vcxproj, not portable to Linux GPU box), run time-boxed schedule (T0 2 h smoke verifying no schema/import bugs, T1 12 h training, T2 stop unless sparring bot beats v_final in controlled h2h). Export as `.npz` (same layout as vladimir: `layer{i}_w`, `layer{i}_b`, `n_layers`). Write numpy-only inference shim mirroring `vlad/bot.py:bot_decide_via_model()`. **Wire the resulting bot ONLY into `tools/h2h.py` and `tools/benchmark.py` as a new sparring opponent** — never into `submissions/` and never into any artifact-bound gauntlet path. If sparring bot beats our PATCH-2A candidate, that is evidence PATCH-2A may need more work; if sparring bot loses to PATCH-2A, that confirms PATCH-2A is robust to neural CFR pressure.
- **Done when:** either (a) `consult/artifacts/2026-06-04-shadow-cfr/{SCOPE.md, training.log, sparring_bot.npz, h2h_vs_v_final.json, h2h_vs_patch2a.json}` exists, committed, and finals ship decision (B10) records whether sparring results altered the rollback choice; or (b) one-line "do-not-pursue" rationale appended back into this plan citing the failed trigger (e.g. "B8 incomplete by 2026-06-04T00:00Z" or "user declined GPU rental" or "<24h remaining").
- **Hard stopping rules (any one fires → terminate the lane immediately):**
  - Cold import of the trained shim > 1.5 s
  - Runtime decide() p99 > 1.5 s in `smoke_run`
  - Sparring bot's `.npz` > 200 MB
  - Validator fails on the sparring bot zip
  - LBR exceeds caps (preflop > 100 mbb/g, aggregate > 200 mbb/g) on the sparring bot
  - Training fails to produce a model that beats `v_final.zip` in a paired-seed h2h at ≥200 hands
  - GPU rental spend exceeds £100
- **Non-shipping invariant (HARD):** the SHADOW-CFR-1 artifact MUST NOT be packaged via `tools/package.py --strict` for `submissions/`. It MUST NOT replace `submissions/v_final.zip` or `submissions/best_green.zip`. It MUST NOT enter the artifact-bound gauntlet (G1–G11) as a promotion candidate. Its only sanctioned uses are: (a) sparring opponent in `tools/h2h.py`, (b) gauntlet target for our PATCH-2A or other ship candidates, (c) diagnostic teacher for leak analysis. Violations of this invariant are equivalent to the rule-breaking PATCH-1 promotion attempt and must be reverted on detection.
- **Key files:** `ext/public-bots/vladimir/bots/vlad/deep_cfr/{train,networks,export,config}.py` (reference architecture), `ext/public-bots/vladimir/bots/vlad/bot.py` (reference inference shim), new lane workspace under `consult/artifacts/2026-06-04-shadow-cfr/`, new sparring bot at `bots/shadow_cfr/bot.py` + `bots/shadow_cfr/data/sparring_bot.npz` (outside `submissions/`).
- **Dependencies:** B8 clean AND ≥24 h wall remaining AND user GPU-rental approval.
- **Size:** ~14–28 h wall (2 h setup + 12–24 h training + 2 h h2h evaluation + writeup). Drop entirely if any trigger fails to fire.

## Open Questions

- **Leaderboard tooling (A3) go/no-go** — **RESOLVED 2026-05-27T22:30Z (orchestrator): DROPPED.** Rationale: `docs/morning-promotion-checklist.md` §1 (Lane A acceptance gate) already enforces statistical sufficiency via three orthogonal mechanisms — aggregate bb/100 ≥ 1.5× pooled SE, per-template floor requiring ≥ 4/5 with CI low > 0, and catastrophic CI low < −20 disqualifier; §2 grades each per-opponent matchup by CI band (GREEN/AMBER/RED). The SHIP path (Section 8) carries the canonical artifact unchanged and does not need a leaderboard view; the MODIFY path (Section 7) routes through §1's gates first. Adding a leaderboard view would be inert in both paths.
- **PATCH-2A statistical band** — **RESOLVED 2026-05-28 (user): pre-committed.** B8 must run ≥10 paired-seed bases × 100 matches each (~2.5h wall). Mirrors PATCH-1 reconcile rollup; rejects single-base seed-cluster bias. Acceptance rule unchanged: famadeo Δ ≥ +15 bb/100 with paired CI excluding 0, no public-bot HURTS, LBR aggregate Δ ≤ +20 mbb/g.
- **PATCH-2B trigger thresholds**: C1 entry condition stated (Δ ≥ +15 bb/100, no regressions, ≤+10 mbb/g LBR creep, ≥6 h wall remaining). Confirm thresholds before B8 completes if you want a stricter bar.
- **2026-06-02 hand-history release time**: The B9 5–6 h slot starts whenever the engine team publishes. If release is late-day, B7+B8 must run before histories arrive (PATCH-2A is structural and does not need them); B9 then runs single-threaded into 06-03.
- **B4 sample-size sufficiency** — **RESOLVED 2026-05-28 (user): 50000 hands.** Upgraded from plan baseline (5k) to paired-seed-equivalent precision; ~10h overnight wall but A1+A2 are already GREEN so this consumes only Phase B head-start slack, not critical-path. Concentration verdict (top-2 explain >50%) is now robust to PATCH-1-reconcile-style seed-cluster noise.

## References

- `consult/artifacts/2026-05-27-worktree-audit/MAP.md` — ship-state recommendation + env-var injection evidence.
- `consult/artifacts/release/RELEASE_NOTES.md` — 2026-05-22 release branch numbers.
- `consult/artifacts/release/gauntlet.log` — original gauntlet pass log.
- `PokerBot-claude/consults/2026-05-27-{hygiene-1,confirm-light3bet,confirm-light3bet-v14,patch1-A,patch1-reconcile,overnight-B,overnight-O}/SUMMARY.md` — today's failed-patch + audit evidence.
- `PokerBot-codex/src/postflop.py:154-380` — PATCH-2A insertion surface.
- `PokerBot-codex/src/equity.py:22-61` — equity API.
- `PokerBot-codex/src/opponent_model.py:71-134` — runtime archetype features (current overlay input).
- `PokerBot-claude/tools/analyze_hand_histories.py:384,459-492,548` — priors producer (post-hardening).
- `ext/public-bots/famadeo/bots/codex_holdem/bot.py:690-729, 2169-2232` — famadeo exploit shape.
- `docs/playbooks/patch-window.md` — operational patch-window flow.
- KANBAN.md → PATCH-WINDOW-PREP (✓ completed), CORPUS-RESEARCH-1 (off critical path).
