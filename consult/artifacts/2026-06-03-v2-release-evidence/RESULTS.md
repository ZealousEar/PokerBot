# V2 Release / Evidence Lane — 2026-06-03

Release/evidence lane (Chat 5). **Does not invent strategy.** Measures, certifies gates,
and records the upload decision for the V2 candidate vs the live emergency patch.

## Artifact map (SHA256 verified this session)

| Role | Artifact | SHA256 | Notes |
|---|---|---|---|
| Deployed-equivalent **baseline** | `qual2-patch/postflop_baseline.py` over elaborate src | (source, not zipped) | leak: `target = current_bet*3`, **no** commit gate |
| **Live emergency patch** (on portal) | `PokerBot-claude/submissions/v_qual2_ship.zip` = `qual2-patch/v_qual2_SHIP_bestgreen+fix.zip` | `d54640e0…f4421` | postflop `_can_commit`, **flush-checked-before-paired** |
| **V2 candidate** | `PokerBot-claude/submissions/v_overnight_v2.zip` | `be7503d3…f899b4` | `commitment.py` + `hand_features.py`, **paired-checked-before-flush** |
| (other patch variant, NOT live) | `v_qual2_stackoff_fix.zip` | `0ec835b6…fbac7` | elaborate+fix; superseded by the bestgreen+fix that was uploaded |

Runtime: PokerBot-claude `.venv` = **Python 3.10.18**, eval7 0.1.7, numpy 1.26.4 (sandbox-matched).
Host `python3` is 3.14 and must NOT be used (eval7 won't import).

## Reality notes (why the literal task command list could not run as written)
- Canonical `tools/{benchmark,exploit_check,replay}.py` are **TODO stubs** (`return 0` / `print("TODO")`);
  canonical `src/` is a **scaffold stub**. Running the task's command list in canonical would certify the stub.
- The real V2 code + real tooling + the already-GREEN gauntlet live in **PokerBot-claude**.
- `tools/replay.py` is a 25-line stub in BOTH worktrees → the 15-metric, 3-way **history** replay harness
  does **not exist**. This lane built a focused **constructed-spot** replay (`disc.py`, `gate_sweep.py`,
  `disc2.py`) that produces the safety-critical metric subset empirically. Full real-history replay
  metrics (loss-on-revealed-showdowns, multiway, short-stack call-off) remain **not measurable** without
  building the counterfactual replay over portal histories (out of scope; `field_recon.py` reconstructs
  the *deployed baseline* only).
- `smoke_run.py` has **no `--strict`** flag and is HU-only; `--hands 1000` Docker smoke not re-run
  (prior 200/200 GREEN twice: V2_RESULTS + Task-4). `package.py` always zips the worktree `src/`
  (no source arg) → not repackaged into a misleading `v_overnight_candidate.zip`; the existing
  `be7503d3` is certified instead.

## 1. Three-way constructed-spot replay (decide_postflop; seed-pinned)

Action on each spot (`raise`/`all_in` = commit; ≥40%-stack = large commit):

| Spot | want | BASELINE | LIVE PATCH (d54640e0) | V2 (be7503d3) |
|---|---|---|---|---|
| A1 `8d3d` non-nut (real leak hand 65) | FOLD | all_in ✗ | **fold** ✓ | **fold** ✓ |
| A5 `Kc4h` non-nut flush, 4-club (real leak hand 269) | FOLD | raise ✗ | **fold** ✓ | **fold** ✓ |
| A2 `AdJd` nut | commit | all_in ✓ | all_in ✓ | raise ✓ |
| A3 `AhAd` safe small | raise | raise ✓ | raise ✓ | raise ✓ |
| A4 `KhKs` set big | commit | all_in ✓ | all_in ✓ | raise ✓ |
| A6 `QcQs` genuine boat on paired-flush | commit | all_in ✓ | **fold** ✗ (over-tight) | raise ✓ |
| D1 `Qc9h` dominated Q-full | fold | all_in | **all_in** | **raise** |
| D2 `7s7h` dominated 7-full (under-boat) | fold | all_in | **all_in** | **raise** |
| **C4 `KdQd` non-nut flush on PAIRED board** | **FOLD** | all_in ✗ | **fold** ✓ | **raise ✗** |

Large-commit count over the 9 spots: **baseline 8 · live patch 4 · V2 6**.

Key reads:
- **A1/A5 (criterion 1):** V2 and the patch both FOLD the two real qualifier-leak hands. ✓
- **A2/A3/A4/A6 (criterion 2):** V2 value-commits all four safe/nut hands; the patch over-folds A6 (a genuine boat). V2 > patch here.
- **D1/D2:** dominated boats do NOT discriminate — **both** patch and V2 commit them. Because `equity_vs_range`
  vs the fixed tight prior `["88+","AT+","KQs","KJs"]` scores a Q-full ≈ 0.83–0.91 (the prior is not "any-King"),
  the patch's paired gate (0.80) and V2's full-house bypass both pass. Neither bot closes this class.
- **C4 (criterion 4): the divergence.** V2 large-raises a non-nut flush on a paired board where the live
  patch folds. **This is the verdict driver.**

## 2. Fixed-equity gate sweep (Monte-Carlo-independent — isolates the structural cause)

`can_commit_raise(hole, board, eq)` decision vs a fixed eq sweep; measured eq from 3 seeds × 2000 trials.

| Board / hand | measured eq | LIVE PATCH commits at eq≥ | V2 commits at eq≥ |
|---|---|---|---|
| **C4** non-nut flush `KdQd` on **paired** `5d5h2d9dTs` | ~0.87 (patch) / ~0.92 (v2) | **0.92** (flush branch) → **FOLD** | **0.80** (paired branch) → **COMMIT** |
| C3 **nut** flush `AdQd` on paired `5d5h2d9dTs` | ~0.87 / ~0.93 | **0.50** (auto via `_has_nut_flush`) → COMMIT | **0.80** → COMMIT |
| D1 dominated `Qc9h` Q-full | ~0.91 / ~0.83 | **0.80** (paired) → COMMIT | **0.50** (`full_house_or_better`) → COMMIT |

Mechanism — **branch ordering differs**:
- **Live patch** `postflop._can_commit`: flush-suit FIRST → non-nut flush requires `eq≥0.92`; paired SECOND (0.80).
- **V2** `commitment.can_commit_raise`: `full_house_or_better` FIRST → then **paired (0.80)** → then flush (0.92).
  On a board that is BOTH paired and flush, V2 takes the **paired** branch (0.80) and never reaches the
  0.92 flush gate. → V2 commits non-nut flushes on paired boards at a **0.12-lower equity bar** than the patch.

**Why Task-4's adversarial review (SHIP) missed this:** its non-nut-flush probe #5 used an *unpaired*
flush board (`9d4d2d Th 3s`), where V2 correctly gates at 0.92. Criterion 4 names **paired** boards,
where the ordering bug bites. The release lane caught a real gap the review did not.

## 3. Hard gates on V2 `be7503d3` (firsthand, `.venv` 3.10) — ALL GREEN

| Gate | Command | Result |
|---|---|---|
| Engine validator | `validator.py submissions/v_overnight_v2.zip` | **PASS** — 4/4 legal, ≤11 ms |
| Import audit | `tools/import_audit.py` | **PASS** — cold import 0.091 s, RSS 37.0 MB (caps 1.5 s / 400 MB) |
| Strategy leakage | `tools/audit_strategy_leakage.py --zip …` | **PASS** — 12 files, n_hits=0, sha=`be7503d3…` |
| Tests | `pytest tests/edge_cases tests/integration tests/unit -q` | **PASS** — 80 passed, 0.97 s |
| Package `--strict` | `tools/package.py --output /tmp/…  --strict` | **PASS** — exit 0; file-set identical to shipped zip |

Not re-run (low value / no flag / doesn't change verdict): Docker smoke `--hands 1000 --strict`
(`--strict` not a flag; HU-only; prior 200/200 GREEN ×2), `benchmark --all-templates/--ablate-overlay`
(slow, variance-bound, explicitly not the ship basis per Task-4), `exploit_check` LBR
(prior 32.1 / 82.4 mbb/g ×2, within caps 100/200).

## 4. Pass-criteria scorecard (referent = LIVE emergency patch)

| # | Criterion | Result |
|---|---|---|
| 1 | Original leak cases still no-stackoff | **PASS** (A1, A5 fold) |
| 2 | Safe controls still value-commit | **PASS** (A2/A3/A4/A6; V2 > patch on A6) |
| 3 | Zero paired-board nut-flush-only large raises | **NOT CLEAN for either** (patch auto-commits; V2 commits at eq≥0.80) |
| 4 | Zero non-nut flush large stackoffs on paired boards | **FAIL (V2)** — C4 commits; patch folds |
| 5 | Raise-to-stackoff count **down vs baseline** | **PASS** (8 → 6; patch lower at 4) |
| 6 | Call/check-call realization **up vs emergency patch** | **NOT SUPPORTED** — V2 `can_call_large` hard-cuts at owed_frac>0.25; patch calls to <0.40 (V2 tighter, not looser) |
| 7 | No validator/import/package/test failure | **PASS** (§3) |
| 8 | STATUS.md append with exact outputs | done |

## 5. Verdict — NO (keep emergency patch active)

V2 is **infra-GREEN** but is **not cleanly at-least-as-safe** as the already-live, already-GREEN
emergency patch:
- It **regresses on criterion 4** — reintroduces a dominated-cooler commit class (non-nut flush large
  stackoff on paired boards) that the live patch closes, via the `commitment.py` paired-before-flush
  ordering. This is the exact leak family the whole effort targets.
- Criterion 6 is **not demonstrated** (V2's call gate is tighter than the patch's).
- V2's genuine wins (A6 boats, equity-range fixes, neutral cold-start overlay, equity-gated nut-flush
  on paired) are real but pertain to **inferred, unmeasured EV** — Task-4 itself forbids justifying
  ship on EV.

The patch is live; the burden of proof for superseding it is on YES and is **unmet**. Per the lane's
stop rule, the strategy regression is **returned to Orchestrate**.

### Fix to return to Orchestrate (one-line, surgical)
In `src/commitment.py::can_commit_raise`, check the **flush board before the paired board** (mirror the
live patch's `_can_commit` ordering), OR gate a non-nut flush on a paired+flush board at
`FLUSH_EQ_THRESHOLD` (0.92) rather than `PAIRED_EQ_THRESHOLD` (0.80). Re-run `disc.py` C4 → expect FOLD.
Add the missing test: non-nut flush on a **paired** board asserts no large stackoff (locks criterion 4).

Evidence harnesses: `disc.py` (3-way spot replay), `gate_sweep.py` (fixed-eq structural proof),
`disc2.py` (priced-in call probes).
