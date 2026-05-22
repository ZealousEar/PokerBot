# PokerBot — Execution Plan

Today: 2026-05-22 | Qualifier: 2026-06-01 | Finals: 2026-06-05 | Hard freeze: 2026-05-31 23:59 UTC

Each gate names its **corpus anchor** — the vault note that drives its design. Cite it in code with `# Source: [[note-name]]` at the call site and in the gate's STATUS.md entry.

## Gates

### G0 — Scaffold (complete)

- [x] Directory tree under `~/Code/PokerBot/`
- [x] Engine cloned to `ext/fullhouse-engine/`
- [x] Tournament constraints codified from engine source
- [x] Library versions pinned in `requirements.txt`
- [x] AGENTS.md, PROMPT.md, PLAN.md, STATUS.md, README.md present
- [x] `src/` stubs (8 modules) + `tools/` stubs (8 scripts) present
- [x] `tests/edge_cases/test_safe_fallback.py` validates safe-fallback contract
- [x] Engine validator PASSED on `submissions/v0_scaffold.zip`

### G1 — Wired (target Day 1–2)

**Exit criterion:** `python tools/self_play.py --opponent template --hands 100 --strict` exits 0; engine validator PASSED on `submissions/v0_wired.zip`. Zero crashes, zero illegal actions, zero timeouts.

**Corpus anchor:** [[Engine-Fullhouse]] — API contract, runner timeout behaviour, valid-action shapes.

Tasks:
- [ ] `src/bot.py` — `decide(game_state)` returns a legal action for every input including `type=="warmup"`
- [ ] `src/timeout_guard.py` — `run_with_budget()` wall-clock budget tracker (threading is forbidden)
- [ ] `tools/self_play.py` — drives N hands against `ext/fullhouse-engine/bots/<opponent>/bot.py` via `sandbox/match.py`
- [ ] `tests/edge_cases/test_legal_actions.py` — every code path returns action ∈ `{fold, check, call, raise, all_in}` with `amount` when raising
- [ ] Build `submissions/v0_wired.zip`; engine validator → PASSED

Append GREEN entry to STATUS.md with verification output + corpus citation.

### G2 — Preflop blueprint (target Day 3–4)

**Exit criterion:** `python tools/benchmark.py --opponent template --hands 10000` reports ≥ 15 bb/100 with 95 % CI > 0.

**Corpus anchor:** External-sampling MCCFR per [[MCCFR-Lanctot-2009]]; blueprint shape `(position × hand × action-seq) → action+sizing` and discrete sizing tree `{1/3 pot, 2/3 pot, pot, 2× pot, all_in}` per [[Pluribus-Brown-Sandholm-2019]]; regret-matching update + average-strategy convergence per [[CFR-Zinkevich-2007]].

Tasks:
- [ ] `tools/train_preflop.py` — external-sampling MCCFR over the 6-max preflop tree; ~1 M iterations target
- [ ] `data/preflop_blueprint.npz` — saved via `numpy.savez_compressed`
- [ ] `src/preflop_lookup.py` — eager load at module import (covered by 30 s warmup); returns action + sizing for `(position, hand, action_seq)`
- [ ] `src/ranges.py` — opening / 3-bet / 4-bet ranges by position and stack depth (cite specific source)
- [ ] `src/sizing.py` — sizing tree wired into blueprint output
- [ ] `src/postflop.py` minimal — check-call with hand-strength threshold for now
- [ ] `tools/benchmark.py` — runs N hands vs opponent, reports bb/100 with bootstrap 95 % CI
- [ ] Build `submissions/v1_blueprint.zip`; engine validator PASSED

Append GREEN entry to STATUS.md with benchmark output + corpus citation.

### G3 — Postflop + Exploit overlay (target Day 5–6)

**Exit criterion:** `python tools/benchmark.py --all-templates --hands 10000` reports ≥ 15 bb/100 vs each of `template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2`, all CIs > 0.

**Corpus anchor:** Flop bucketing (≤ 200 buckets × ≤ 50 hand bins) and CFR+ trainer per [[Cepheus-Bowling-2015]]; opponent-fingerprint refinement pattern per [[Libratus-Brown-Sandholm-2017]] (we replace nested subgame solving with frequency overlay); per-bot exploit priors seeded from [[Engine-Fullhouse]] §"Reference bots — strategies and exploits"; equity-vs-range fallback for turn/river per [[Pluribus-Brown-Sandholm-2019]] (depth-limited heuristic in lieu of full solve).

Tasks:
- [ ] `tools/train_flop.py` — CFR+ over ≤ 200 flop buckets × ≤ 50 hand bins; saves `data/flop_buckets.npz` + `data/flop_strategy.npz`
- [ ] `src/postflop.py` — flop bucket lookup, eager load at import
- [ ] `src/equity.py` — `equity_vs_range(hero, board, villain_range, trials=2000)` using eval7, ≤ 5 ms/call; LUT pre-warm at import
- [ ] `src/opponent_model.py` — per-seat VPIP / PFR / AF / FoldToCBet rolling counters; 30-hand warmup; bounded deviation magnitude (initial cap: shift baseline frequency by ≤ 20 pp toward best-response)
- [ ] `src/bot.py` — `decide()` routes preflop through blueprint, postflop through bucket lookup (flop) + equity heuristic (turn/river), then applies overlay shifts
- [ ] Seed `opponent_model` priors from [[Engine-Fullhouse]] reference-bot exploit holes
- [ ] Build `submissions/v2_postflop.zip`; engine validator PASSED

Append GREEN entry to STATUS.md with all five benchmark outputs + corpus citation.

### G4 — Hardening (target Day 7)

**Exit criterion:** All edge cases pass; package ≤ 250 MB; cold-start import < 1.5 s; 10 000-hand crash-free integration; engine validator PASSED on `submissions/v3_hardened.zip`.

**Corpus anchor:** [[Engine-Fullhouse]] §"Engineering pitfalls to avoid".

Tasks:
- [ ] `tools/import_audit.py` — cold start < 1.5 s, RSS < 400 MB, scan all `src/*.py` for forbidden imports + call patterns
- [ ] `tests/edge_cases/` — side-pot, all-in, raise-below-min, raise-above-stack, timeout, malformed input, warmup, illegal-action defense
- [ ] 10 000-hand integration run vs engine harness — zero crashes, zero illegal actions, zero timeouts
- [ ] Tighten `timeout_guard.run_with_budget` fallback paths under load
- [ ] `tools/package.py --strict` builds `submissions/v3_hardened.zip`; engine validator PASSED

Append GREEN entry to STATUS.md with full hardening gauntlet output + corpus citation.

### G5 — Game-theoretic verification (target Day 7–8)

**Exit criterion:** Ablation ≥ 3 bb/100; self-play ratchet ≥ 3 bb/100 per prior gate; LBR ≤ 100 mbb/g preflop and ≤ 200 mbb/g aggregate on a 20-spot suite. Build `submissions/v_final.zip`; engine validator PASSED.

**Corpus anchor:** Blueprint+refinement validation pattern per [[Libratus-Brown-Sandholm-2017]] + [[Pluribus-Brown-Sandholm-2019]]; local best-response per Lisý & Bowling 2017 (not in vault corpus — inline reference: arXiv:1612.07547).

Tasks:
- [ ] `tools/benchmark.py --ablate-overlay --hands 10000` — runs with-overlay bot vs blueprint-only bot against a biased-opponent suite (tight-passive, loose-passive, tight-aggressive, loose-aggressive synthetic seats); reports gain attributable to overlay
- [ ] `tools/benchmark.py --self-play --vs-prior` — runs `v_final` vs each of `v0_wired`, `v1_blueprint`, `v2_postflop`, `v3_hardened` snapshots; verifies monotone ≥ 3 bb/100 improvement
- [ ] `tools/exploit_check.py` — implement local best-response over a fixed 20-spot suite (5 preflop, 5 flop, 5 turn, 5 river); report mbb/g per spot and aggregate
- [ ] Build `tests/integration/test_biased_opponents.py` synthetic opponents (tight/loose × passive/aggressive)
- [ ] Preserve gate snapshots (`submissions/v{0..3}_*.zip`) for the ratchet check; do not overwrite
- [ ] Build `submissions/v_final.zip`; engine validator PASSED

Append GREEN entry to STATUS.md with all three game-theoretic measurements + `## FINAL SUBMITTED` + corpus citations per gate.

## Stop conditions

- Any criterion fails twice consecutively after non-trivial fixes → append `BLOCKED: <criterion> <reason>` to STATUS.md, pause.
- Previously GREEN criterion regresses → append `REGRESSION: <criterion> <metric>`, pause.
- Allowed-library import unexpectedly fails inside sandbox → pause, report.
- 2026-05-31 23:59 UTC arrives → package highest-gate build that passes its own verification, append `STOPPED AT <gate>`, stop.
