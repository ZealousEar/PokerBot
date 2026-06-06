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
