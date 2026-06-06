# REDTEAM_REPORT — 2026-06-03

Read-only adversarial audit of the **deployed Qualifier-II bot** `submissions/v_qual2_ship_d54640e0.zip`
(sha256 `d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421`).
Method: orchestrator orientation + empirical `decide()` reproduction, plus a 6-agent
workflow (lineage / runtime / strategy / benchmark / sandbox / completeness-critic).
Every strategy finding was reproduced by running the **exact deployed bytes** read-only
from `/tmp/rt_audit/d54640e0` under `.venv/bin/python` (Python 3.10.18 — identical to the
sandbox runtime). No repo file was modified; this report is the only write.

---

## Executive verdict

**Verdict on `d54640e0`: FINALS-RISKY.** Lineage is **RESOLVED** (not uncertain — see Lineage
map), but the deployed artifact is finals-risky on the merits: the very near-dead stack-off
class the Qualifier-II patch claims to fix is **still present in the exact deployed bytes and
was reproduced**, and the bot has **no equilibrium floor** to bound its downside against a
sharp single-elim field. Runtime/sandbox/validator are **SAFE** — every danger is strategic.

**The unifying thesis (the single best finals-loss framing).** `CLAUDE.md`’s architecture
rests on a "blueprint (near-Nash) bounds our downside vs sharp counter-exploiters; the overlay
is a *bounded* deviation." The deployed bot ships **no `.npz`, no CFR, no blueprint** — it is
hand-tuned ranges + **equity-vs-a-single-random-hand** + a narrow commit gate + a behavioural
overlay. **The Nash floor the whole safety argument depends on is absent.** So "downside is
bounded vs sharp opponents" is structurally false for `d54640e0`, and the overlay is
exploitable *by design*. Single-elimination rewards low variance; this bot is wide and
high-variance. This is a regression against the team’s own `PLAN.md`: G2/G3 specified an MCCFR
preflop blueprint (`data/preflop_blueprint.npz`) and a CFR+ flop blueprint
(`data/flop_strategy.npz`) as the intended near-Nash floor — the deployed bot ships **neither**
(`data/` holds only `.gitkeep`) and substitutes a hand-tuned heuristic.

### Top 5 risks (ranked by probability × chip-loss severity in the finals)

| # | Risk | Sev | Why it ranks here |
|---|------|-----|-------------------|
| **R1** | **Static-range `_can_commit` → near-dead stack-off (LEAK-1)** | CRITICAL | The forensic signal itself. **Reproduced**: bot stack-commits at **0.212** true equity (trip-K on paired `KK7`) and **0.000** true equity (2nd pair, dry river). High trigger probability (any value-bettor/trapper), full-stack severity. The shipped "fix" did **not** remove it. |
| **R2** | **Single-villain equity in multiway pots (LEAK-2)** | CRITICAL\* | 6-bot qualifier confirmed; finals size unknown. `hand_strength`/`equity_vs_range` model **one** opponent. **Measured** overstatement up to ~3.3×; demonstrated -EV call (vs-1 eq 0.502 → true 3-way 0.315 < pot-odds). \*CRITICAL if finals is multiway; guaranteed ≥2-way. |
| **R3** | **Depth-blind preflop stack-off (GAP-1, new)** | HIGH | **Reproduced**: facing a ~93bb 4-bet *jam* at 100bb, bot **flat-calls off ~91bb** with TT/99/JJ/AQo/KQs (24–37% eq vs `{QQ+,AK}`); **identical decision at 15bb**. `preflop_lookup.lookup()` has no stack/SPR node and `_can_commit` never runs preflop. **Dominant risk in a heads-up finals.** |
| **R4** | **No Nash floor + overlay exploitable by design (LEAK-3 + thesis)** | HIGH | Vestigial `.npz` → no bounded-downside guarantee. **Reproduced**: 2 all-ins in 9 actions flips villain to `hyper_aggressive`, loosening hero river calls (fold→call) and widening thin value. A sharp finalist who has seen our qualifier hands weaponizes this. |
| **R5** | **Benchmark blindness — greens don’t cover the leak class (BV-1/BV-2/BV-3)** | HIGH (meta) | Every *wired* gate is HU or a TODO stub; **no bundled opponent ever bets big with a capped-strong range**, so the leak is never punished. The deployed patch carries an **unmeasured −9.66 bb/100 HU regression** waved off as a "6-max artifact" **with zero 6-max measurement**. Net-positive of the shipped patch is **unproven on the deployed bytes**. |

### What must be tested before any strategy patch is trusted
1. **Resolve the finals table size** (heads-up vs 6-max). It is the *master discriminator* —
   it decides whether R3 (preflop, HU) or R2 (multiway) dominates. Spec is silent; get it from
   the organizers.
2. **Direct multiway pod on the deployed bytes** (`run_pods.py`, hero = `d54640e0` itself, paired
   seeds, vs `e4b4a8f1` baseline). The deployed bot’s multiway EV is currently **UNMEASURED**;
   the −128k inversion in the corpus is a *different* bot (see GAP-4).
3. **Stack-depth sweep** on the preflop 4-bet-jam call (R3) at 15/25/50/100bb.
4. **Build the missing archetypes** (wet-board polarized value-bettor; paired-board check-raise
   trapper) and gate `d54640e0` on them **multiway**, not HU.
5. **Re-run the LEAK-1 board suite (A–E)** as unit tests, gating commitment against an *inferred
   betting range* rather than `PRIOR_RANGE_TIGHT`.

---

## Evidence table

> Reproducers live at `/tmp/rt_audit/repro.py` (orchestrator A–E) and the strategy agent’s
> `/tmp/rt_audit/repro_multiway.py`, `repro_overlay2.py`, `repro_seat_alias.py`, `probe_eq2.py`.
> All import the deployed bytes read-only.

### LEAK-1 — Static-range commit gate → near-dead stack-off · **CRITICAL** · confidence high
- **Artifact:** `src/postflop.py:23,88-104,180-202` (deployed bytes).
- **Evidence (command output, `/tmp/rt_audit/repro.py`):**
  ```
  A) trip K, A-kicker on KK7, facing pot-ish bet:
     eq_vs_RANDOM=0.966  eq_vs_PRIOR_TIGHT=0.932 -> _can_commit=True
     eq_vs_BOATS_77_K7 (REALITY)=0.212   decide()={'raise', 1900}  COMMITS
  D) river 2nd-pair KhQc on Ah-Qd-7s-2c-3d:
     eq_vs_PRIOR_TIGHT=0.589 -> _can_commit=True (safe-board eq_strong>=0.55)
     eq_vs_RIVER_VALUE (REALITY)=0.000   decide()={'raise', 900}   COMMITS
  B) AA on monotone Qs-Js-9s, owed 60% stack: _can_commit=False -> decide()=fold   (gate works)
  E) nut flush AsKs on Qs-Js-3s: _can_commit=True -> raise   (control passes)
  ```
- **Mechanism:** The only board-aware commitment veto is `_can_commit`, fed
  `eq_strong = equity_vs_range(hole, board, PRIOR_RANGE_TIGHT)` where
  `PRIOR_RANGE_TIGHT = ["88+","AT+","KQs","KJs"]` is a **static preflop-style range** that never
  reflects the villain’s actual betting line. A hand that beats that generic range but loses to
  the villain’s *capped-strong* betting range passes the gate. On dry boards the safe-board
  threshold (`eq_strong >= 0.55`) is met by any decent pair → river value-jam into the nuts.
- **Exploiter archetype:** any bot that bets/raises big only with made hands on wet/paired
  boards; paired-board check-raise trapper.
- **Minimal reproducer:** board `['Ks','Kh','7d']`, hero `['As','Kc']`, villain jam range
  `{77,K7}`; assert `decide()` does **not** return a stack-committing raise/all_in.
- **Proposed test:** parametrized unit test over boards A–E asserting no stack-commit when true
  equity vs the inferred betting range < ~0.45.
- **Patch shape:** feed commit/large-call decisions an equity computed against an **inferred,
  line-conditioned** range (narrow on flush/paired/straighty boards when villain has bet/raised),
  not the static range; apply a commit veto to the cheap-call branch too. *(Do not just tighten
  thresholds — see Do-not-do.)*

### LEAK-2 — Single-villain equity in multiway pots · **CRITICAL (multiway)** · confidence high
- **Artifact:** `src/equity.py:127,169`; `src/postflop.py:50-55,142,184`.
- **Evidence (`repro_multiway.py`):**
  ```
  trip K (A) on KK7           hs(vs1)=0.945  true vs5=0.854
  AT overcards+gut Qs Js 9s   hs(vs1)=0.502  true vs2=0.315  true vs5=0.151
  KQ 2nd pair river AQ-high   hs(vs1)=0.757  true vs2=0.630  true vs5=0.293
  DECISION FLIP: call_threshold 0.380 < vs-1 eq 0.502 (calls) but > true vs-2 eq 0.315 -> -EV call
  ```
  (Independently re-run by the orchestrator; "true vsN" uses **explicit eval7 enumeration** of N
  random villains — hero must beat all N — not the range-tag parser, so the ~3.3× overstatement
  and the decision flip are sound.)
- **Mechanism:** `hand_strength` draws exactly **one** random villain; `equity_vs_range` is vs
  **one** combo; `_opponent_seat` returns a single seat and ignores all other live players. No
  function takes an opponent count. At 6-bot tables (engine `tournament.py:11 table_size=6`)
  pots are routinely 3–5 way, so every postflop equity is overstated and pot-odds calls/value
  bets fire on heads-up equity.
- **Exploiter archetype:** none required — structural; worst vs multiple loose callers (the
  passive hackathon field) who keep pots multiway.
- **Reproducer:** `hand_strength_multiway(['Ah','Td'],['Qs','Js','9s'],n_opp=4)` ≪ `n_opp=1`.
- **Proposed test:** integration — 3-live-player state must not `call` when true 4-way equity <
  pot-odds; unit — multiway equity must be ≥0.20 below the vs-1 number on that board.
- **Patch shape:** thread live-player count into the equity calls and require beating the **max
  of N** opponents (or apply a live-count-scaled discount to call/value thresholds). Keep
  rollout counts bounded (see Do-not-do — timeout budget).

### GAP-1 — Depth-blind preflop stack-off · **HIGH** · confidence high *(critic-found, orchestrator-reproduced)*
- **Artifact:** `src/preflop_lookup.py:45-50` (no stack/SPR arg); `src/ranges.py:331-335`
  (`CALL_VS_THREEBET = {JJ,TT,99,AQs,AJs,ATs,AQo,KQs}`); commit gate only at `postflop.py:88`.
- **Evidence (orchestrator command output):**
  ```
  Facing a ~93bb 4-bet JAM, hero stack 100bb, our seat=3 (3-bettor):
    TcTd -> call    9c9d -> call    JcJd -> call
    AhQc -> call    KhQh -> call    AcKs -> all_in    AcAd -> all_in
  Same hands @ 15bb stack -> call/call/call  (IDENTICAL tag => DEPTH-BLIND)
  ```
  eval7 (20k) vs a tight jam `{QQ+,AK}`: KQs .254, AQo .242, TT/JJ/99 .366 — all below the ~.448
  break-even → every one is a **-EV full-stack call**.
- **Mechanism:** `lookup()` takes no effective-stack / SPR / pot-odds argument, so the 3bet /
  call / 4bet tag is byte-identical at 15bb and 150bb, and the only stack-off veto (`_can_commit`)
  lives in `decide_postflop` and never executes on a preflop node. Raise *sizing* is also
  depth-blind (`current_bet*mult`, no cap vs stack/pot). **This is a regression against the
  team’s own plan:** `PLAN.md` (G2) specifies "`src/ranges.py` — opening / 3-bet / 4-bet ranges by
  position **and stack depth**" — the stack-depth axis was dropped in the shipped build.
- **Exploiter archetype:** any opponent that 4-bet-jams a non-maniac value range; **inflated in a
  heads-up finals** (blinds every hand → constant 3bet/4bet wars).
- **Proposed test:** stack-depth sweep facing a 4-bet-jam at {15,25,50,100}bb; assert the called
  range **shrinks** with depth (at 100bb JJ/TT/AQo/KQs must fold).
- **Patch shape:** add a stack-depth/SPR-conditioned node *before* any preflop call-off; do **not**
  blanket-tighten ranges (regresses correct short-stack jams / qualifier EV).

### LEAK-3 — Fake-"hyper_aggressive" overlay flip · **HIGH→MEDIUM** · confidence high
- **Artifact:** `src/opponent_model.py:159,185-189`; `src/postflop.py:153-160`.
- **Evidence (`repro_overlay2.py`):**
  ```
  FAKE-HYPER villain -> n_actions=9 all_in_rate=0.222 -> archetype='hyper_aggressive'
    shift={tighten_open:.2, fold_to_pressure_less:.2, value_widen_vs_aggro:.1, bluff_catch_less:-.05}
  DEMO1 river bluff-catch: PASSIVE villain -> {'fold'} ; FAKE-HYPER -> {'call'}
  DEMO2 thin value:        PASSIVE -> raise 300       ; FAKE-HYPER -> raise 396
  ```
- **Mechanism:** `archetype()` returns `hyper_aggressive` as soon as `all_in_rate > 0.15`
  (≈2 all-ins in ~13 actions). `exploit_shift` then sets `fold_to_pressure_less=0.20` /
  `value_widen_vs_aggro=0.10`, lowering the river `call_threshold` by `0.06` and the thin-value
  threshold to `0.68` — loosening exactly when a fake-maniac then value-bets.
- **Mitigation (downgrades to MEDIUM):** the engine caps `match_action_log` at the last **200**
  entries (`match.py:44,221`), so two early jams age out after ~20–25 hands and the
  classification self-corrects (GAP-3). Deviations are bounded by `MAX_DEVIATION_PP=0.20`.
- **Exploiter archetype:** an opponent that open-jams twice early (the `aggressor` template, or a
  finalist who deliberately buys two cheap all-ins) then plays a tight value line.
- **Proposed test:** a log with 2 all-ins among 9 actions must **not** classify `hyper_aggressive`;
  `decide()` on the DEMO1 river must still fold.
- **Patch shape:** require higher all-in count *and* a minimum sample before triggering
  `hyper_aggressive`; age/decay `all_in_count`.

### LEAK-4 — Seat-index aliasing after a bust · **MEDIUM** · confidence high
- **Artifact:** `src/opponent_model.py:82,87,103` (keys counters on `seat`, ignores `bot_id`).
- **Evidence (`repro_seat_alias.py`):** after a bust, seat 2’s merged counter →
  `n_actions=20 all_in_rate=0.250 aggression=0.667 -> archetype='hyper_aggressive'` (conflates
  two physical bots).
- **Mechanism:** the match remaps seat indices to the shrinking `alive` list each hand
  (`match.py:244,250-256,291`); `match_action_log` carries `bot_id` (`match.py:301`) but
  `observe_log` never reads it, so one seat counter blends two bots once anyone busts.
- **Mitigation:** bounded by the same 200-entry window (GAP-3) — not "permanent."
- **Proposed test:** a log where seat 2 is bot C (hands 0–4) then bot E (5–9) must yield two
  distinct archetypes.
- **Patch shape:** key counters on `entry['bot_id']`, map to current seat only at read time.

### LEAK-5 — Low-trial MC bias flips the 0.80 value boundary · **MEDIUM** · confidence high
- **Artifact:** `src/equity.py:172` (seeded by trials); `src/postflop.py:141,186-196`.
- **Evidence (`probe_eq2.py`, case D `KQ` on `Ah Qd 7s 2c 3d`):**
  ```
  trials= 180: eq=0.8278 (>=0.80 value-raise: True)   <-- the code's river trials
  trials=5000: eq=0.7841 (False)        gap=0.044 straddles the 0.80 branch
  ```
- **Mechanism:** river uses `trials=180`; the seeded estimate is **deterministically** ~+0.04
  biased on this hand, pushing a true-0.78 hand into the value-raise block every time it occurs.
- **Proposed test:** assert `|hand_strength(h,b,180) - hand_strength(h,b,5000)| <= 0.02` for
  boundary hands, or that `decide()` doesn’t value-raise when the 5000-trial eq < 0.80.
- **Patch shape:** add a noise margin to the 0.80/0.55 boundaries, or raise trials near boundaries.

### LEAK-6 — `_infer_position` fallback · **INFO (non-leak in this engine)** · confidence high
- The engine always posts blinds into `action_log` (`game.py:337-342`, included in `_build_state`
  `:573`), so the `sb_seat=0` fallback never fires. Verified: with blinds present, positions label
  correctly. **No patch required for this engine**; defensive only if the real finals engine omits
  blind entries. (Closes the orchestrator’s open question.)

### RUNTIME / SANDBOX — **SAFE** · confidence high
- **No runtime-legality finding.** Engine `_build_state` (`game.py:558-574`) provides **every** key
  the bot reads — zero missing-key silent folds. Raise **`amount` = street-total**
  (`game.py:_validate` snaps `amount = max(amount, current_bet+min_raise)`, `chips_needed =
  amount - bet_this_street`), matching `src/sizing.legal_raise_total` exactly; `all_in` is a
  distinct shape. The engine **coerces every return to a legal action** before it reaches the
  table; the bot independently triple-wraps `decide → run_with_budget → _strategy` in try/except.
  Agent verified `hero_errors=0` across HU, 6-bot, and 1v5-aggressor matches.
- **Validator PASSES** (exit 0) on the deployed zip; 4/4 TEST_STATES legal, ≤0.004s. **No forbidden
  imports/calls**; no `threading` (timeout_guard uses only `time`/`contextlib`). **Import 0.04–0.06s**,
  RSS ~21MB — far under the 30s warmup / 400MB ceilings. **No `.npz`/`np.load`/`open()` anywhere**;
  `BOT_DATA_DIR` is read into a dead var and never used → **no missing-data crash path** (verified
  import succeeds with the var unset and pointing at a nonexistent dir). Layout/size all within caps.
- **Timeout risk LOW:** equity loops are `trials` iterations of one `eval7.evaluate` (≤286 per call);
  agent measured ~286× headroom under the 2s budget.

---

## Anti-punt analysis

**Why near-drawing-dead stack-offs happen / where they originate.** The "range-aware" commit veto
`_can_commit` is fed equity computed against a **static preflop-tight range**
`PRIOR_RANGE_TIGHT = ["88+","AT+","KQs","KJs"]` (`postflop.py:23,184`), which omits the
board-specific monsters that actually comprise a *jamming* range. On a paired board the gate asks
"do I beat that generic range?" (trips beat it → True) instead of "do I beat the boats that jam
this board?" (no). **Reproduced:** trip-K stacks off at **0.212** vs `{77,K7}`; on a dry river the
safe-board branch (`eq_strong >= 0.55`) waves through 2nd pair at **0.000** vs the river value
range. That is precisely the forensic signature (LOST equity-at-commit ≈ 0.059): hands live vs a
*random* hand, dead vs the *betting* range. **Critically, the Qualifier-II "fix" did not close
this** — the deployed `postflop.py` is byte-identical to the commit literally named "the
`_can_commit` fix," and the bug reproduces against those exact bytes.

**Is there a hard equity/pot-odds/SPR veto before calling or jamming?** **No.** There are three
gates and all are bypassable:
- `call_threshold` (`postflop.py:145`) is a pot-odds gate but computed on **eq-vs-random**, so it
  overstates on wet/multiway boards.
- `_can_commit` is the only board-aware veto, but (a) it reads the **static** range, and (b) it is
  **only consulted when a single action commits ≥40% stack** (`commit_frac=0.40`). Sub-40% calls
  (multi-street grind-down) and `owed <= 0.15*stack` value-branch calls bypass it entirely
  (`postflop.py:193-194,199`). **Reproduced** (case C): bot calls a 29%-stack bet at **0.150** true
  equity, gate never consulted.
- There is **no SPR / effective-stack node at all preflop** (GAP-1) — the bot calls off 91bb the
  same as 15bb.

**Is multiway / wet-board equity realization discounted enough?** **No.** Equity is computed vs a
**single** random villain or a **single** combo, with **no multiway discount and no opponent
count** (LEAK-2). On wet boards the static commit range further fails to model the polarized
betting range. The two errors compound on exactly the boards where they hurt most.

**Do river calls/bluffs have threshold guards?** Partial and leaky. River calls use the pot-odds
`call_threshold` on eq-vs-random with overlay nudges that *loosen* it vs a (spoofable)
`hyper_aggressive` read (LEAK-3). The river **value-raise** is the only facing-a-bet path that can
raise, and it fires on a low-trial-biased 0.80 boundary (LEAK-5) gated only by the static-range
`_can_commit` (LEAK-1) — which is how 2nd pair jams the river at 0% equity (case D). C-bet bluffs
are frequency-based with no board-equity floor.

---

## Lineage map

**Method:** per-file sha256 of extracted zips + `git rev-list --all` search across all three
worktrees. **Verdict: lineage RESOLVED**, with one provenance gap.

```
ref         artifact                                              npz?   role
e4b4a8f1    submissions/best_green.zip == v_final.zip             YES    Qualifier-I ship ("SIMPLE", blueprint arch)
d54640e0    submissions/v_qual2_ship_d54640e0.zip   <== DEPLOYED  NO     Qualifier-II live upload ("ELABORATE" heuristic)
0ec835b6    PokerBot-claude/.../v_qual2_stackoff_fix.zip          YES    alternate candidate, NOT deployed
be7503d3    PokerBot-claude/.../v_overnight_v2.zip                YES+   reviewed-SHIP, NOT merged, NOT uploaded
```

**Relationships (decisive, sha-level):**
- **`d54640e0` = `claude best_green` heuristic core + exactly one swapped file (`postflop.py`).**
  Per-file sha vs claude `best_green.zip` (no npz): **MATCH** on bot/opponent_model/preflop_lookup/
  ranges/sizing/equity/timeout (7/8); **DIFF** only `postflop.py`. The swapped `postflop.py` is
  byte-identical to claude commit **`2733566`** ("V2 base: deployed qual2 postflop `_can_commit`
  fix") — i.e. the deployed gate *is* the version the bug reproduces against.
- **`d54640e0` ≠ canonical `src/`** and **≠ `e4b4a8f1`** on every strategy file (only
  `timeout_guard.py` is shared) — **do not treat canonical `src/` as the deployed strategy.**
- **vs `0ec835b6`:** differ on bot/opponent_model/preflop_lookup/sizing (postflop + ranges
  identical); `0ec835b6` ships 3 `.npz` (blueprint arch). It was **not** the bytes uploaded.
- **vs `be7503d3`:** differ broadly; `be7503d3` adds `commitment.py` + `hand_features.py` + 4 `.npz`.
  Unmerged/un-uploaded.

**Provenance gap (flagged):** `git rev-list --all` finds **no commit** whose `src` tree is
byte-identical to deployed `d54640e0/src` — the live bytes exist **only** as the preserved zip
(verified byte-identical across **4** locations) and were **never committed to VCS**. Also,
`consult/.../qual2-patch/FINDINGS.md:27` documents the qual2 build as `0ec835b6` (the *wrong*,
npz-bearing zip); **`STATUS.md:632` is authoritative and matches the deployed bytes (`d54640e0`).**
This audit is valid **for the `d54640e0` bytes hashed above**; the `0ec835b6` candidate has
*different* `opponent_model.py`/`sizing.py` and would need a separate pass if it ever ships.

**Full submission-zip sha table:**
```
e4b4a8f1...9598  best_green.zip / v_final.zip   npz:YES
7df4e702...ffb3  v0_scaffold.zip                npz:NO (no data/)
0792be72...8112  v0_wired.zip                   npz:NO (.gitkeep only)
f729b9ad...bede  v1_blueprint.zip               npz:preflop only
3487230f...da57  v2_postflop.zip                npz:YES (3)
7caa4f63...dbec  v3_hardened.zip                npz:YES (3)
5d65561e...0cef  v_final_pre_x1.zip             npz:YES (3)
9a3b812e...c0b0  v_final_reaudit.zip            npz:YES (3)
d54640e0...4421  v_qual2_ship_d54640e0.zip      npz:NO  <== DEPLOYED
```

---

## Test plan — 20 highest-value tests/benchmarks (ranked)

> Wiring caveat (BV-1): `tools/benchmark.py:71-92` and `tools/self_play.py:26-34` are **TODO stubs**
> that print and `return 0` without running a hand; only `tools/smoke_run.py` and
> `ext/fullhouse-engine/sandbox/match.py` actually play. The real multiway harness is the laneC
> `consult/artifacts/2026-05-30-dual-leak-swarm/laneC-toby-gauntlet/pods_locked/run_pods.py`.

1. **Resolve finals table size** (organizers/portal). Master discriminator for R2 vs R3.
2. **Direct multiway pod on the deployed bytes** — `run_pods.py` hero=`v_qual2_ship_d54640e0.zip`
   vs `e4b4a8f1`, 40 paired seeds; gate on six-max p50 chip delta & bust-rate no-worse.
   *(The corpus −128k inversion is a different bot — GAP-4 — so this is the only direct evidence.)*
3. **LEAK-1 board suite (A–E) as unit tests** — assert no stack-commit when true equity vs the
   *inferred* betting range < 0.45; boards `KK7` (boats), `QsJs9s` (flushes), dry river.
4. **GAP-1 stack-depth sweep** — `decide()` vs a 4-bet-jam at {15,25,50,100}bb; assert called range
   shrinks with depth (100bb: JJ/TT/AQo/KQs fold). `python` driver against `/tmp/rt_audit/d54640e0`.
5. **LEAK-2 multiway equity unit** — `hand_strength_multiway(AhTd,QsJs9s,n_opp=4)` < vs-1 − 0.20;
   integration: 3-live-player state must not `call` when true 4-way eq < pot-odds.
6. **Build a wet-board polarized value-bettor opponent** (bets big only with made flushes/sets/
   boats on wet/paired boards) and run it **multiway** vs `d54640e0` (paired seeds).
7. **Build a paired-board check-raise trapper** opponent; same multiway paired-seed run.
8. **Build a fake-archetype counter-exploiter** (two early all-ins, then tight value) — assert
   `d54640e0` doesn’t hemorrhage on river bluff-catches (LEAK-3).
9. **LEAK-3 classification test** — 2 all-ins in 9 actions must not be `hyper_aggressive`; the
   DEMO1 river must still fold.
10. **GAP-3 aging test** — 2 jams then 210 non-jam actions; archetype self-corrects once jams
    scroll past the 200-entry cap.
11. **LEAK-4 aliasing test** — seat reused by two bot_ids across a bust yields two archetypes.
12. **LEAK-5 boundary test** — `|eq@180 − eq@5000| ≤ 0.02` for boundary hands, or no value-raise
    when 5000-trial eq < 0.80.
13. **Cheap-call grind-down test** (case C) — sub-40%-stack call on a wet board at <0.20 true
    equity must be gated, not auto-called on pot odds.
14. **`d54640e0` vs all 5 bundled bots MULTIWAY** (6-max pods) — establish the real-field baseline
    the HU greens never measured; compare to `e4b4a8f1`.
15. **Paired-seed `--paired-seed-base 42 --paired-seed-count 10`** (or ≥50k hands) acceptance per
    the benchmark-variance policy — single-run 10k is monitoring only.
16. **LBR regression** (`tools/exploit_check.py`) on `d54640e0` — confirm ≤100 mbb/g preflop /
    ≤200 aggregate as a guard (not a Nash claim).
17. **River value-jam audit** — enumerate boards where `eq-vs-random ≥ 0.80` but `eq` vs a tight
    value range < 0.30 (TPTK/overpair into completed boards); count jam frequency.
18. **3-bet / 4-bet pot postflop SPR test** — verify commitment logic in low-SPR 3-bet pots where
    `_can_commit`’s 40% trigger interacts with small effective stacks.
19. **Smoke + validator regression** on any candidate (must stay green) — `validator.py`,
    `smoke_run.py --hands 200`, `pytest tests/edge_cases -x`.
20. **Side-pot / all-in legality fuzz** — multiway all-in states through `match.py` asserting
    `hero_errors=0` and correct side-pot eligibility.

---

## Do-not-do list

- **Do not blanket-tighten `_can_commit` thresholds or the preflop ranges.** Two independent
  attempts to tune this gate family regressed: the *deployed* patch itself measured **−9.66 bb/100
  HU** vs its own leaky baseline (`STATUS.md:631`, `FINDINGS.md:24`), waved off as a "6-max
  artifact" **with no 6-max measurement**; the V2 attempt (`be7503d3`) reintroduced a dominated
  paired-board cooler and a `owed_frac>0.25` hard-fold. The fix must be *range-* and
  *depth-aware*, not "tighter."
- **Do not repackage the artifact to "fix" anything.** `tools/package.py` embeds build timestamps →
  the sha drifts → it breaks the preserved-artifact chain and the very lineage this audit relies on.
  Patch in a worktree and re-verify a *new* zip; never mutate `d54640e0`.
- **Do not add naive heavy multiway Monte-Carlo rollouts.** At 0.5 CPU / 2s, N villains × rollouts
  can blow the deadline → auto-fold. Use bounded rollouts / closed-form discounts.
- **Do not trust any patch that passes HU smoke only.** The missing multiway + wet-board-value
  coverage is *what let this leak ship.* Gate on the multiway pod harness (test #2/#6/#7).
- **Do not adopt `be7503d3` (V2) as the finals bot on its review-SHIP alone** — it is unmerged,
  carries open dominated-cooler / over-fold warnings, and its only direct EV proxy is negative.
- **Do not "fix" LEAK-6 (position inference)** for this engine — it is a verified non-leak; touching
  it risks breaking correct labeling. Add a defensive guard only if the finals engine is confirmed
  to omit blind entries.
- **Do not upload/submit anything to the portal** — human-gated (`CLAUDE.md` upload policy). This
  audit recommends *tests*, not a ship.

---

### Confidence & scope
- All strategy leaks were **reproduced by running the exact deployed bytes**; numbers above are
  command output, not estimates. Runtime/sandbox verdicts are backed by validator output,
  `hero_errors=0` matches, and measured import time.
- **Honest gaps:** (a) the deployed bot’s *multiway* and *finals-format* EV is **unmeasured** —
  LEAK-2/GAP-2 are structurally proven and per-decision-reproduced, but the aggregate chip impact
  needs test #2; (b) finals table size is unknown and re-ranks R2↔R3; (c) the corpus HU→multiway
  −128k inversion is a *different* bot (GAP-4), so it is suggestive, not direct, evidence for
  `d54640e0`.
