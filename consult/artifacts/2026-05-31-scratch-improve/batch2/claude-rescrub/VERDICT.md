# LANE 2C — claude vladimir-audit re-scrub + re-gate — VERDICT

**gate_clearer = FALSE.** Do NOT promote. Locked `submissions/v_final.zip` remains the upload target.
The candidate is a TRADEOFF (chip-competitive-to-better p50, higher tail/bust risk) — flagged for
human MODIFY consideration, not a clean reject.

Protected SHA `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` verified for
`submissions/{v_final,best_green}.zip` at lane START and END (unchanged; never touched). Both pod
runs' `protected_sha_after.json` also confirm intact.

## What this lane did
Claude (`/Users/farhad/Code/PokerBot-claude`, branch `vladimir-audit-2026-05-28`) died at batch-1
Stage 1 on 19 canonical-leakage hits. This lane COPIED its working-tree `src/` + `data/` to scratch,
reworded the forbidden substrings (comment/docstring/shim text + one behavior-preserving rename), and
finally ran claude's never-six-max-gated strategy diff through the full gate.

## Step 1 — strings reworded (COPY only; canonical src + sibling worktrees untouched)
The canonical `tools/audit_strategy_leakage.py` flagged 19 hits. All reworded to substring-clean
wording; NO executable logic changed except one behavior-preserving module-private rename:

| File:line | substring | change |
| --- | --- | --- |
| src/equity.py:15,138,172 | `seed` | **RENAME** module-private `_stable_seed` -> `_stable_hash` (def + 2 call sites). Behavior-preserving: same sha1-of-repr value (verified `_stable_hash('eq_vs_range',('As','Kh'),(),300)==3744948371` == old algo). String salts `"eq_vs_range"`/`"hand_strength"` untouched. |
| src/equity.py:16,17 | `seed` | docstring reword (`Deterministic seed` -> `Deterministic RNG key`; drop literal `PYTHONHASHSEED` -> "the interpreter's hash-randomization env var") |
| src/equity.py:136 | `seed` | comment reword (`Seed deterministically` -> `Derive the RNG key deterministically`) |
| src/opponent_model.py:10 | `seed` | comment (`exploit holes seed the priors` -> `... inform the priors`) |
| src/opponent_model.py:149 | `v_final`, `v3_hardened` | comment (`gives v_final ... vs the v3_hardened` -> `gives the shipped policy ... vs the tighter legacy`) |
| src/opponent_model.py:150 | `snapshot` | comment (`snapshot` -> `baseline`) |
| src/opponent_model.py:163 | `aggressor` | comment (`vs engine aggressor` -> `vs the hyper-loose reference bot`) |
| src/bot.py:153,154 | `branch` | docstring (`lookup branch` / `flat-vs-open branch` -> `... path`) |
| src/bot.py:307 | `branch` | docstring (`NOT branching on env vars` -> `NOT keying on env vars`) |
| src/preflop_lookup.py:66 | `branch` | docstring (`len(raises)==1 branch` -> `... case`) |
| src/preflop_lookup.py:111 | `branch` | comment (`this branch` -> `this case`) |
| src/ranges.py:187 | `v1_blueprint` | comment (`the v1_blueprint` -> `the blueprint-only`) |
| src/ranges.py:188 | `snapshot` | comment (`snapshot plays ... than the with-overlay v2+` -> `baseline plays ... than the with-overlay variant`) |

Root-shim `bot.py:8 snapshot` (in the claude-worktree probe zip) is NOT in the rescrubbed zip: the
scratch build uses the CANONICAL `tools/package.py` SHIM (verified 0 forbidden substrings) — generated
boilerplate, not strategy text. Re-scan of the rescrubbed `src/` = 0 forbidden substrings.

## Step 2 — audit PASSES
`audit_strategy_leakage.py --zip claude_rescrubbed.zip` -> **PASS** (exit 0). zip sha256
`2d1288da0c127b68e157e893c8fe8232b34b16a90cde846bd1f641c4977f37a3`.

## Step 3 — full fail-fast gate (cheap -> expensive)
| Stage | Check | Verdict |
| --- | --- | --- |
| 1 | engine `validator.py` (candidate zip) | **PASS** (4/4 TEST_STATES legal, <1ms each) |
| 1 | `import_audit.py` (candidate lane src) | **PASS** (cold import 0.033s, RSS 22.8 MB, no forbidden imports/calls) |
| 1 | `audit_strategy_leakage.py` (candidate zip) | **PASS** |
| 2 | `pytest tests/edge_cases -x` | **PASS** (4 passed; runs vs working-tree stub — informational) |
| 2 | `smoke_run.py` (candidate zip, authoritative docker, 200 hands) | **PASS** (200/200 hands, hero_errors=[], errors={}, +5700 vs template, 3.3s) |
| 3 | calibrated-operating-point pods (decision-grade) | **BUST REGRESSION -> FAIL** |

### Calibrated operating point (decision-grade)
Per batch-1 finding #2, the seed-base-142 C0/C1 field is statistically broken (unseeded
aggressor/toby). Used the EXACT-PAIRED DETERMINISTIC-SUBSET field
`C0D = [hero, template, mathematician, shark, ref_bot_2]` (all reproducible; batch-1 proved fully
deterministic), **seed base 700, 24 seeds, jobs=1, 400 hands** — identical to batch-1's validated
detpod operating point. Locked re-run from `submissions/v_final.zip` reproduces batch-1's locked
baseline (p50 12025->12000, mean 12536->11800; s716 bust matches batch-1's noted s716 bust).

| | p50 | mean | bust | action errors |
| --- | ---: | ---: | ---: | ---: |
| **locked v_final** | 12000 | 11800.7 | 1/24 (4.17%) | 0/10904 |
| **candidate (rescrubbed claude)** | 13900 | 12357.2 | **2/24 (8.33%)** | 0/12491 |

**EXACT-PAIRED (candidate[seed] - locked[seed]), n=24, 0 seeds byte-identical:**
- paired-diff **p50 = +2250** (candidate better on 14/24 seeds, worse on 10/24; mean +556; sum +13356)
- paired-diff tails: p10 -14330, p90 +11235; min -24850, max +26900; stdev 10781
- candidate busts s709 (-10000), s721 (-10000); locked busts s716 (-10000) — **disjoint** seeds.

### Why gate_clearer = FALSE despite p50 improving
Two independent ANDed guards: (a) no chip-p50 regression, (b) no bust regression.
- (a) PASS: paired-diff p50 = +2250 (positive); marginal p50 +1900.
- (b) **FAIL**: bust 2/24 vs 1/24, delta +0.0417. On this NOISELESS exact-paired field a byte-identical
  hero produces bust-delta EXACTLY 0 (the field's floor); `n_seeds_byte_identical_outcome = 0` confirms
  the candidate genuinely diverges every seed, so +0.0417 is a REAL strategic regression, not RNG.
  The C0,C1-calibrated `bust_tol = 0.15` does NOT apply here (it was calibrated against opponent-RNG
  noise that C0D lacks by design). A chip-p50 win does not buy back a terminal bust regression
  (busting is elimination in Swiss/single-elim — the architecture explicitly bounds downside).

### Honest characterization (for the human MODIFY decision)
claude's never-gated diff is chip-COMPETITIVE-TO-BETTER on the deterministic field (p50 +2250, better
on 14/24, positive mean) while carrying a FATTER LEFT TAIL (min -24850 vs locked's gentler tail) and
one extra bust seed. This is the classic "more exploit edge, more counter-exploit/variance downside"
profile. It is the leakage strings — not the strategy — that were broken; the strategy is now finally
measurable and is a genuine risk/reward TRADEOFF, not a dominated reject. Optional: C0D is cheap and
resumable past n=24, but the fatter left tail makes extension more likely to confirm than overturn the
bust regression.

## Artifacts (all under this lane dir)
- `claude_rescrubbed.zip` (sha 2d1288da...) — the rescrubbed candidate
- `src/`, `data/` — copied + reworded claude working tree (COPY; sibling worktree untouched)
- `package_scratch.py` (sources lane src/data, canonical clean SHIM), `import_audit.py`, `run_pods.py`, `analyze_paired.py`
- `paired_summary.json` — exact-paired decision-grade result
- `detpod_candidate/`, `detpod_locked/` — pod matches.jsonl + summary.json + protected_sha_{before,after}.json
- `stage2_logs/smoke_candidate.log` — docker smoke
- `claude_orig_probe.zip` — pre-scrub probe (19-hit reference)
