# Candidate-vs-Locked Gate Harness

`gate_harness.py` — a reusable, parameterized tool that gates **any** candidate
submission zip against the **locked** baseline (`submissions/v_final.zip`) on
decision-grade paired-seed six-max pods, behind a fail-fast cheap→expensive
staged pipeline. Built so the **2026-06-02 patch window** can evaluate a
candidate fast and safely.

- It is **artifact-local**: it never imports/modifies `src/`, never writes to
  `submissions/`, and loads both the candidate (hero) and the locked baseline
  as zip files passed on the command line.
- **Nothing auto-promotes.** A candidate that clears the full gate is only
  *flagged* for a human MODIFY decision. `submissions/v_final.zip` stays the
  upload target unless a human explicitly overrides.
- It verifies both canonical locked zips' sha256 ==
  `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
  at **start** and **end** of every run (independent of `--locked`); on any
  mismatch it aborts with `protected_sha_ok=false` and exit code 2.

This consolidates the proven 3-script dual-leak pattern
(`2026-05-30-dual-leak-swarm/laneC-toby-gauntlet/{pods_candidate,pods_locked}/run_pods.py`
+ `summarize_pods.py`) into one parameterized tool. The engine-interaction
internals (`DecisionTimer`, single-match runner, `infer_bust`) are reused
near-verbatim.

---

## Exact run command (decision-grade gate)

**Recommended / validated command — gate on `C0,C1`** (the calibrated set):

```bash
/Users/farhad/Code/PokerBot/.venv/bin/python \
  /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-31-scratch-improve/gate-harness/gate_harness.py \
  --candidate /path/to/candidate.zip \
  --locked /Users/farhad/Code/PokerBot/submissions/v_final.zip \
  --pods C0,C1 \
  --seed-base 142 --seeds 40 \
  --jobs 1 \
  --p50-tol 6000 --bust-tol 0.15
```

The decisive pods (`C0`, then `C1`) are always evaluated first. The tolerances
`(6000, 0.15)` are calibrated **only** for `C0,C1` (see Self-test). `C1` is the
proven discriminator; `C0` is saturation-blind (context only).

**`C3,C4` are NOT in the recommended command — tolerances are uncalibrated and
the pods are slow.** They execute end-to-end, but: (a) their paired-diff floor
has not been measured against these tolerances, and (b) early data shows `C3`
likely shares `C0`'s saturation blindness (the fold-heavy scaffold *bleeds
small* while locked busts, so the weaker bot can score a *better* C3 paired
diff). Before trusting `C3,C4`, re-run the byte-identical no-op on them to
measure their floor and pick pod-appropriate tolerances, and inspect opponent
error rates (the slow public bots may be erroring/timing out — bot-vs-broken-bot
data, not clean signal). A single global `--p50-tol` set high enough for a noisy
C4 would also desensitize C1, so prefer per-regime calibration over one loose
tolerance.
Outputs land in `runs/run_<candidate_sha8>/` (override with `--run-name`):
`gate_summary.json`, `GATE_RESULTS.md`, `pods_candidate/matches.jsonl`,
`pods_locked/matches.jsonl`, `protected_sha_{before,after}.json`.

### Pipeline (fail-fast; a candidate that fails an earlier stage does NOT advance)

| Stage | Cost | Checks |
| --- | --- | --- |
| 1 | cheap | engine `validator.py` (candidate zip) + `tools/import_audit.py` (working `src/` — see caveat) + `tools/audit_strategy_leakage.py` (candidate zip) |
| 2 | medium | `pytest tests/edge_cases -x` + `tools/smoke_run.py` (candidate zip, authoritative docker) |
| 3 | expensive (LAST) | paired-seed six-max pods for candidate AND locked on identical seeds; `C0` then `C1` first |

`--skip-stage1` / `--skip-stage2` exist for pod-only calibration; do **not** use
them for a real gate. `--allow-small-seeds` permits `<40` seeds for wiring
self-tests only (a decision-grade gate requires `>=40` paired seeds).

---

## Why `--jobs 1` (mandatory for trustworthy pairing)

The C0 reference opponents `aggressor` and `shark` call **unseeded
`random.random()`**; each bot runs in its own subprocess that auto-seeds from OS
entropy, so opponent *actions* are irreducibly nondeterministic run-to-run.
(The engine deals a **deterministic deck** per seed via a local
`random.Random(hand_seed)`, so pairing on identical seeds cancels **card**
variance — but not opponent-action variance.)

Empirically, `--jobs 2` produced far wider swings than `--jobs 1` for a
byte-identical candidate (two in-process `run_match` calls contend; a single
seed flipped a +17,501 survival into a −10,000 bust). `--jobs 1` removes that
confound at trivial cost. **Caveat for prior work:** any earlier pod run using
`jobs>1` (including the inherited laneC pattern) carries this concurrency-noise
caveat.

**Measured per-match timing (matters for patch-window budgeting):**
- `C0`/`C1` (reference + toby field): ~0.7–1.3 s/match → a 40-seed `C0,C1`
  gate (160 matches) is a few minutes.
- `C3`/`C4` (heavier public bots — mehedi, famadeo, neel, pav): **8–91 s/match**
  (the slow public bots repeatedly hit the 2 s per-decision timeout) → a 40-seed
  `C3,C4` gate is **tens of minutes, not minutes**. Budget accordingly.

`PYTHONHASHSEED=0` is pinned in the harness for defense-in-depth (it only
affects a hero that hash-seeds its own RNG, e.g. `equity.py` — which is **dead
code** on `v_final`'s decision path; verified no `equity` import in the shipped
strategy). It does **not** affect the `random` module and does **not** make the
opponents deterministic.

---

## PASS/FAIL logic (primary signal = paired-diff median)

For each pod, the harness computes the **per-seed paired diff**
(`candidate_chip_delta − locked_chip_delta`) and its distribution
(p10/p25/p50/p75/p90/mean/stdev/min/max). The **primary gate signal is the
paired-diff median (p50)** — this preserves the variance reduction the paired
design exists for. Marginal medians and the marginal-p50 delta are reported for
context but are **not** the gate signal.

A pod **PASSes** iff it is complete AND:
- `paired_diff_p50 >= -p50_tol` (no median chip regression), AND
- `candidate_bust_rate - locked_bust_rate <= bust_tol` (no bust regression).

Overall verdict is `GATE_CLEAR_FLAG_FOR_HUMAN_MODIFY` only when **every** stage
passes and **every** requested pod passes.

---

## Self-test (how the harness was validated) — calibration is load-bearing

The lane spec's "no-op = package current `src/`" assumption is **false on this
branch**: the canonical `src/` is the **G0 scaffold** (stubs:
`raise NotImplementedError("G3")`, empty `RANGES`, `TODO (G2/G3)`), while
`v_final.zip` contains the fully-implemented strategy. `git show main:src/bot.py`
confirms even `main` carries the scaffold — **the shipped strategy has no git
source-of-truth on either branch; it exists only inside the zip** (human flag
below). So packaging `src/` yields a weaker *stub bot*, not a no-op.

Two controls were therefore used, with distinct roles:

| Control | What it is | Role | Expectation |
| --- | --- | --- | --- |
| `true_noop_candidate.zip` | byte-identical copy of `v_final.zip` (same sha) | negative control / wiring proof | clears the gate (≈ no regression) |
| `scaffold_candidate.zip` | `package.py --strict` on canonical `src/` (the stub) | positive control / regression detector | FAILs the gate |

### Measured floor and discrimination band (40 paired seeds, `--jobs 1`, seed base 142)

`runs/floor_truenoop_40seed/` and `runs/positive_control_scaffold_40seed/`:

| | C0 paired Δp50 | C1 paired Δp50 | C0 Δbust | C1 Δbust |
| --- | ---: | ---: | ---: | ---: |
| **true_noop** (identical) | 0 | **−2310** | +2.5pp | **+10.0pp** |
| **scaffold** (weaker) | 0 | **−11962** | −40.0pp | −12.5pp |

The byte-identical no-op floor is **not** zero off-saturation: the paired-diff
distribution has huge tails (true_noop C1 stdev ≈ 15,989; range
[−36,777, +40,672]) from survive-vs-bust discordances driven by opponent RNG.
The **median** is robust to those tails (C0 = 0, C1 = −2310), so calibrate on it.
(The paired-diff *means* — C0 −1299, C1 −5401 — are within ≈1 SE / ≈2 SE of zero
respectively; this is opponent-RNG noise, not a wiring fault. More seeds tighten
the unsaturated-pod floor but are not required at 40.)

Discriminating constraints from the data:
- `p50_tol` must **exceed 2310** (the no-op C1 floor — below it a byte-identical
  bot FALSE-FAILS) and stay **below 11962** (the scaffold C1 regression).
  Chosen **6000** (margin both ways). Band: **[2310, 11962)**.
- `bust_tol` must **exceed 0.10** (no-op C1 bust noise). Chosen **0.15**.

### Validated verdicts at `--p50-tol 6000 --bust-tol 0.15`

- `true_noop_candidate.zip` → **`GATE_CLEAR_FLAG_FOR_HUMAN_MODIFY`** (C0 PASS, C1 PASS).
- `scaffold_candidate.zip` → **`GATE_FAIL_POD_REGRESSION`** (C0 PASS [saturation-blind], **C1 FAIL** on Δp50 = −11962).

At the **default** tolerances `(0, 0)` the no-op FALSE-FAILS on C1 — that is the
key calibration result, not a harness bug. Always pass calibrated tolerances.

### Full-pipeline plumbing (all five stages exercised)

`runs/selftest_allstages_truenoop/` (true_noop, small bounded pods): **validator
PASS, import_audit PASS, leakage_audit PASS, edge_tests PASS, smoke_run PASS
(docker)**, then pods. Confirms every stage runs end-to-end. The 2-seed pod in
that run is **not** a calibration measurement (its diff is dominated by a single
opponent-RNG bust flip) — the 40-seed runs above are the load-bearing evidence.

Protected SHAs verified `OK` at start **and** end of every run.
Self-test seed count: 40 (decision-grade) for the two calibration controls;
2 (bounded, `--allow-small-seeds`) for the plumbing-only all-stages run.

---

## Caveats and human flags (report, not this lane to fix)

1. **`import_audit` audits working-tree `src/`, not the candidate zip** (no
   `--zip` flag). It is meaningful only when the candidate was built from the
   current `src/`. The candidate zip's actual imports are covered by the engine
   validator's forbidden-module AST scan on the zip. On this branch `src/` is
   the stub, so for a `v_final`-derived candidate this stage audits the
   scaffold; it is kept because Stage 1 is required, but it is informational for
   such candidates.
2. **C0 is saturation-blind; a non-saturated discriminating pod (C1+) is
   mandatory.** Verified directly: scaffold C0 has 0 hero action errors, and its
   p50=0 comes from genuine ties/saturation (the fold-heavy scaffold busts
   *less* — 10/40 vs locked 26/40 — so it scores a *better* bust rate and a 0
   median on C0). Gated on C0 alone, the weaker scaffold would FALSE-PASS.
3. **The bust-rate guard is calibrated against false-positives, not validated as
   a catch.** The scaffold busts *less* than locked, so the bust guard never
   trips for it. Showing the guard catches a real bust regression needs an
   over-aggressive candidate that busts *more* — building it is out of scope.
4. **Coarse operating point at seed base 142.** Locked `v_final` busts this
   reference field ~70–100% of C0 matches at this seed base, pushing the
   chip-delta metric toward its −10,000 floor (hence tolerances ≈ half a
   starting stack). More seeds will **not** fix C0 — saturation is a
   field/seed-base property, not a sample-size one. Recommend the human pick a
   field / seed base that keeps locked off the bust floor so chip-delta has
   resolution; re-measure the floor and re-pick tolerances for that regime.
5. **No git source-of-truth for the shipped strategy.** Both `main:src/bot.py`
   and this branch's `src/bot.py` are the G0 scaffold; `v_final.zip`'s
   implemented strategy is not committed anywhere. Notable for provenance.

---

## Files in this directory

- `gate_harness.py` — the reusable tool.
- `README.md` — this file.
- `true_noop_candidate.zip` — byte-identical copy of `v_final.zip` (negative control).
- `scaffold_candidate.zip` — `package.py` on canonical `src/` stub (positive control).
- `opponent_zips/` — lane-local copied/built opponent zips (auto-created).
- `floor_run.log`, `positive_run.log` — calibration run logs.
- `runs/` — per-candidate outputs:
  - `floor_truenoop_40seed/`, `positive_control_scaffold_40seed/` — calibration.
  - `selftest_allstages_truenoop/` — all-stage plumbing check.
  - `selftest_jobs1_truenoop/` — early jobs=1 wiring check (superseded by floor run).
