# Finals Infra Scratch Report

> SCRATCH-ONLY finals-infrastructure lane. Qualifier is SHIP_LOCKED. No MODIFY, no promotion,
> no reupload. Allowed write scope: `consult/artifacts/2026-05-31-finals-infra-scratch/` only.
> Evidence base: three pre-existing batch-2 result JSONs (re-read this session), a fresh live
> experiment sweep (release anchor + scratch LBR at three seed/budget points, all completed
> successfully — `diag-01/lbr_runs/experiments.log`), a `context_builder` discovery+oracle code
> diagnosis, and direct artifact-guard checks. The RepoPrompt agent-delegation tools
> (`agent_run`/`agent_manage`) are NOT available in this environment; verification was done via
> the native Workflow tool + direct reads instead.

## 1. Protected artifact invariant
- **Start SHA** (restart of interrupted lane): `submissions/v_final.zip` and `submissions/best_green.zip`
  both `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`; `cmp` ZIP_IDENTITY: **identical**.
- **Mid-run re-verify** (experiment batch pre/post guards): both still `e4b4a8f1…` (`SHA guard (pre)` and
  `SHA guard (post)` in `lbr_runs/experiments.log` both `e4b4a8f11f801ece`).
- **End SHA**: see the `END_GUARD` block appended at the very bottom of this file (written in the same op).
- **Verdict: INTACT — PASS.** No protected artifact was modified, rebuilt, repackaged, copied over,
  replaced, extracted-over, deleted, renamed, or touched. The release scorer was read via `git show`
  (read-only) into scratch; nothing under `release/`, `src/`, `tools/`, `data/`, `tests/`, `docs/`,
  `submissions/`, or `STATUS.md` was written. v_final.zip was only OPENED read-only (zipimport) by the
  scorers; its bytes are unchanged.

## 2. LBR methodology comparison
| | Release fixed-spot scorer | Scratch match-play LBR |
|---|---|---|
| Path | `release/v_final-e4b4a8f1:tools/exploit_check.py` (507 LOC); read-only copy at `diag-01/release_anchor/tools/exploit_check.py` | `consult/artifacts/2026-05-31-scratch-improve/batch2/lbr-impl/lbr_check.py` (537 LOC) |
| CLI | `--bot --max-preflop-mbb --max-aggregate-mbb` (NO hands/rollouts → deterministic) | `--bot --hands --rollouts --seed-base --max-preflop-mbb --max-aggregate-mbb --json-out` (defaults **hands=4000/rollouts=80**) |
| Method | Scores a fixed suite of ~20 synthetic `SPOTS`; maps each bot action to a hand-authored **risk score in [0,100]** via `_risk_for()` (e.g. fold=0 … all_in≈95); preflop=max, aggregate=mean | Drives full HU hands through the real engine; villain = one-step argmax over Monte-Carlo EV + **passive check/call rollout tail**; reports villain net chips as mbb/g |
| Units | "mbb/g" **by label only** — bounded non-negative risk points, never chip flow | villain net chips per hand × 10 (1 BB = 100 chips); a real zero-sum chip flow |
| Historical v_final | preflop **+18.0** / aggregate **+7.4** (RELEASE_NOTES G8) | (see §3 — sign-unstable, FAILS at default budget) |

- **Sign/units of the scratch tool (derived from JSON):** `villain_mbb_g = (villain_net_chips / hands) × 10`,
  e.g. `−113930/400 = −284.825 → ×10 = −2848.25`. Normalizes **per scheduled hand**; intended convention
  **positive = villain (attacker) profits = hero exploitable**.
- **Anchor reproduced? YES — EXACTLY.** The release synthetic-spot scorer first crashed as-is from the scratch
  copy: `exploit_check.py:487` does `str(bot_path.relative_to(ROOT))`, raising `ValueError` because the absolute
  `submissions/v_final.zip` is outside the materialized `release_anchor/` subtree (traceback in `experiments.log`
  block 2C, RC=1) — a cosmetic output-formatting bug (defect **C3**), not a scoring bug. A **scratch-only
  path-fixed copy** (`exploit_check_pathfix.py`, new file; the materialized original was NOT overwritten)
  reproduced the historical anchor **precisely: preflop 18.0 / aggregate 7.4 mbb/g, `exploit_check PASS`**
  (`release_anchor/anchor_run.log`; matches RELEASE_NOTES G8 to the decimal), with v_final SHA `e4b4a8f1…`
  unchanged. The output is a 20-spot risk rubric (per-spot `risk_mbb_g` ∈ [0,35], e.g. `river_free_showdown`=35,
  `pf_fold_prone_defend_broadway`=18); preflop=max, aggregate=mean. This **confirms it is a bounded
  non-negative risk score, not a chip-flow exploitability estimate.**
- **Are the scratch numbers directly comparable to +7.4/+18.0? NO.** Different estimators of different
  quantities: the release tool emits a **bounded non-negative risk rubric** (EV-vs-baseline over fixed spots);
  the scratch tool emits **full-match zero-sum chip flow**. The scratch tool's OWN docstring argues the
  synthetic-spot formulation "double-counts dead money … inflates the number by orders of magnitude," i.e. the
  two are not on the same scale and neither validates the other. (The scratch docstring further claims
  match-play "reproduces small numbers for v_final" — contradicted by its own output; see §3.)

## 3. LBR experiments
**A. Durable batch-2 JSONs (hands=400 / rollouts=20 / seed=42), re-read this session:**

| Bot (HERO) | aggregate mbb/g | preflop mbb/g | villain_net_chips (agg) | hero_busts | villain_busts | elapsed (agg) |
|---|---|---|---|---|---|---|
| `submissions/v_final.zip` | −2848.25 | −78.9 | −113930 | 15 | 30 | 1.8 s |
| `sibling-gate/codex.zip` | **+978.75** | +497.27 | +39150 | 16 | 16 | 30.6 s |
| `batch2/claude-rescrub/claude_rescrubbed.zip` | −3028.12 | −1390.88 | −121125 | 14 | 30 | 71.5 s |

**B. Fresh live sweep on v_final this session (`lbr_runs/experiments.log`, all completed, SHA-guarded):**

| Run | hands | rollouts | seed | preflop mbb/g | aggregate mbb/g | gate result |
|---|---|---|---|---|---|---|
| 2D | 400 | 20 | 42 | **−78.9** | −2848.25 | PASS (RC=0) — *auto-pass on negative* |
| 2D | 400 | 20 | 123 | **+2358.15** | −431.48 | FAIL (RC=1) |
| **2E (tool default budget)** | **4000** | **80** | 42 | **+893.0** | −64.9 | **FAIL (RC=1)** |

**C. Release anchor:** as-is run (2C) → `ValueError` on `exploit_check.py:487` `relative_to(ROOT)` (RC=1, cosmetic
defect C3). Scratch-only path-fixed copy (`exploit_check_pathfix.py`) → **preflop 18.0 / aggregate 7.4 mbb/g,
`exploit_check PASS`** — reproduces RELEASE_NOTES G8 exactly (`release_anchor/anchor_run.log`). Deterministic
(no seed/budget). Confirms the release tool is a fixed risk rubric, not comparable to the match-play chip flow.

**Verified source locations (read this session + workflow verification):** `lbr_check.py` —
`villain_mbb_g = (villain_net / max(1,n_played)) / BIG_BLIND * 1000` (lines 446-448; BIG_BLIND=100 → ×10, per
actual hands played); villain candidate set = check/fold/call + raise@{0.5,1.0,2.0}×pot + all_in with argmax over
Monte-Carlo EV (lines 203-255); passive check/call rollout tail for villain's future nodes (lines 301-312);
**gate `*_pass = (mbb_g <= cap)` with NO `>= 0` floor (lines 521-523) = defect C1.** Sign convention: positive =
villain/attacker profits = hero exploitable (intended).

**Interpretation — four independent disqualifiers:**
1. **FAILS at its own default budget.** At hands=4000/rollouts=80 (the docstring target) v_final scores
   **preflop +893.0 mbb/g, far above the 100 cap → FAIL.** The headline "−78.9/−2848 PASS" was an
   **under-budget (h400/r20)** artifact, not a real pass.
2. **Sign-unstable across seed AND budget.** Preflop swings **−78.9 → +2358 → +893** by changing only the seed
   or budget. A converged exploitability estimate cannot flip sign; this magnitude of seed/budget sensitivity
   means the estimator has not converged and its number is meaningless as a bound. *(Per explicit reviewer
   guidance: sign-instability across seeds/budgets is itself disqualifying — a one-budget pass does not rescue it.)*
3. **The villain is sub-Nash (not a real best response).** In the negative runs the "best-responder" villain
   LOSES chips to v_final and busts ~2× as often as hero (30 vs 15). A true LBR is a **lower bound on
   exploitability and is ≥ 0** — at every node the villain can fold to floor its loss near zero. A deeply
   negative villain proves it is choosing actions strictly worse than folding. Mechanism: one-step argmax over
   **noisy** Monte-Carlo EV (only 20–80 rollouts; lines 203-255) suffers the optimizer's curse and over-selects
   high-variance jams, while the **passive check/call tail** (lines 301-312) under-models hero's future
   aggression — so the villain over-commits and busts. (Note: the passive tail is *standard* LBR depth-limiting
   that loosens the bound; it is not itself a bug. The disqualifiers are the empirical instability + the unfloored
   gate, not the tail.) Its sign even depends on the *opponent* (codex +978 while v_final/claude are negative),
   so it is measuring an interaction artifact, not a property of the hero alone.
4. **The gate auto-passes negatives.** `main()` decides `*_pass = (mbb_g <= cap)` with **no `>= 0` floor and no
   validity flag** (code defect C1, confirmed by `context_builder` source reading) — so an invalid deeply
   negative result green-lights the bot. This *inverts* the gate: the more the estimator misfires downward, the
   "safer" the bot looks.

## 4. LBR status
classification: LBR_UNTRUSTED

*(Cross-checked by an adversarial agent explicitly tasked to defend LBR_TRUSTED: its steelman — "treat the tool
as a structural best-response probe, not an exploitability metric" — collapsed on the same three points (sign
instability disqualifying; gate logic inverted via C1; no confidence intervals at tiny N). Its independent verdict:
**LBR_UNTRUSTED, confidence high.**)*

## 5. Consequence for promotion gates
No candidate may use this LBR lane as promotion evidence unless LBR_TRUSTED.
Because the classification is **LBR_UNTRUSTED**, the exploit-measurement arm is **blind**. Any finals
promotion must either:
(a) **fix the LBR first** — add a `>= 0` floor / validity flag to the gate (C1), give the villain a genuine
    fold-floor and a non-passive / deeper best-response tail, report confidence intervals, and require
    convergence so v_final lands a small POSITIVE near the documented ~+7.4 region under a properly comparable
    method; **or**
(b) explicitly mark exploit measurement as **UNRESOLVED for human review** and make no exploitability claim.
Do **not** repair by flipping a sign — units/seat/blind handling are correct (confirmed); the failure is a
sub-Nash attacker + an unfloored gate, not a sign bug.

## 6. Analyzer readiness
Full detail in the companion file `diag-01/ANALYZER_READINESS.md`. Summary:
- **Toby-class river trap:** canonical `tools/analyze_postflop_trap_prevalence.py` (892 LOC) is present,
  test-covered (`tests/integration/fixtures/postflop_trap_prevalence/`), parses JSON/JSONL/dirs, and is the
  intended Toby river-trap-prevalence measure. CLI exposes `--input`/`--in`, `--json-out`, `--report`, `--top-n`.
- **B9 hand-history priors analyzer:** **absent in canonical** PokerBot. Intended hardened surface is
  `PokerBot-claude/tools/analyze_hand_histories.py` (630 LOC), CLI **`--in/--out/--force`** (NOT
  `--input/--output/--report`); writes `.npz` priors.
- **Playbook CLI mismatch:** `docs/playbooks/patch-window.md` Phase 3 invokes the analyzer with
  `--input/--output/--report` and Phase 7 invokes `exploit_check.py --zip`, neither of which matches the real
  CLIs (`--in/--out/--force`; release scorer is `--bot` only). Reconcile before 2026-06-02.
- **Hardcoded prior (C2):** population fold-to-c-bet falls through to a constant **0.50** in the claude
  analyzer's `_aggregate()` (counters never incremented) → the Phase 3 sanity gate always "passes" on a fake value.
- **k-means bot-cluster fingerprints:** promised in docstrings, **unimplemented**.
- **Mehedi-class BB-defense:** **no history-parse measurement exists** (only live engine-vs-fixed-zip probes).
  Precise missing spec defined in `ANALYZER_READINESS.md`.

## 7. Qualifier decision
This lane does not alter qualifier decision.
SHIP_LOCKED remains active.

## 8. Final recommendation
RECOMMENDATION: NO QUALIFIER MODIFY — upload submissions/v_final.zip unchanged; use this report only for post-qualifier/finals infrastructure.
