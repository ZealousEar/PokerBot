# PokerBot — Handover (2026-05-31, finals scratch-lane work)

## TL;DR
The qualifier bot is **SHIP_LOCKED**: upload `submissions/v_final.zip` unchanged before the
**2026-06-01 12:00 UK / 13:00 Rome / 11:00 UTC** cutoff. Two overnight-style improvement batches ran
finals candidates through the full promotion gate. **No candidate cleared; nothing was promoted; the
locked artifact is verified byte-intact.** The durable wins are infrastructure + knowledge, not a new
bot: a calibrated decision-grade evaluation field, a (still-unvalidated) LBR tool, and a corrected
picture of where the real strategy lives in git. Two candidates are honest near-misses flagged for
human MODIFY. Continue from "Open threads" below.

---

## 1. HARD INVARIANTS — do not violate
- **Never modify/overwrite/repackage/move/delete** `submissions/v_final.zip`, `submissions/best_green.zip`,
  or anything under `release/`. Both zips are gitignored and live ONLY in the canonical checkout.
- Both must remain sha256 **`e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`**
  (byte-identical to each other). Verify at the start AND end of any work. Last verified intact: after batch 2.
- **Nothing auto-promotes.** No artifact replaces `v_final.zip` without clearing the FULL gate (§4) and
  an explicit human MODIFY. A gate-clearer is only *flagged*.
- Do **not** edit canonical `src/` in place or the sibling worktrees. Copy to scratch; use worktree isolation for src-mutating experiments.
- Use the canonical venv by absolute path: `/Users/farhad/Code/PokerBot/.venv/bin/python`. Never `pip install`. Runtime is Python 3.10; no PyTorch/C++ at submission time.
- Qualifier-day reupload default = **NO REUPLOAD**; leaderboard drift alone does not open MODIFY.

## 2. Mission / decision / timeline
- Goal: win the Fullhouse Hackathon 2026 (Swiss qualifier 2026-06-01, finals bracket 2026-06-05).
- **Qualifier: SHIP_LOCKED** — `v_final.zip` unchanged. All prior candidates failed the six-max bar.
- **Finals patch window: 2026-06-02** — opponent hand histories released; retune compact priors only, re-run the full gauntlet.
- This work stream = **finals candidate development in scratch lanes**, qualifier frozen.

## 3. Verified facts (I checked these directly this session)
- **Locked artifact intact** post-both-batches: both zips sha `e4b4a8f1…598`, `cmp` identical, `git status -- submissions/` clean.
- **Source-of-truth correction (important):** the shipped strategy is **git commit `a00561c`** (branch
  `release/v_final-e4b4a8f1`; `v_final.zip` == `a00561c` byte-for-byte; `a00561c:src/bot.py` = 196 LOC of
  real logic). **`main` and the current checkout (`tooling/postflop-trap-extractor-2026-05-29`) are the
  48-line G0 scaffold stub** — `a00561c`'s "promote onto main" never actually landed. **Any finals/patch
  work must branch from `a00561c` / `release/v_final-e4b4a8f1`, NOT from `main`/current checkout.** Reconcile `main` separately.

## 4. The promotion gate (clear ALL, then human MODIFY only)
protected SHA untouched until promotion · validator (engine `ext/fullhouse-engine/sandbox/validator.py`)
· import audit · **leakage audit (canonical `tools/audit_strategy_leakage.py --zip` is authoritative**; it
is a forbidden-substring scanner — siblings' own narrower tools are not) · edge tests · authoritative
Docker smoke · **exploit/LBR caps (preflop ≤100, aggregate ≤200 mbb/g — currently UNMEASURABLE, see §8)** ·
reference all-template benchmark (no broad regression) · public regression · trigger H2H (Toby + Mehedi) ·
**six-max pods with no p50 AND no bust regression — on the decision-grade field C0D (§5)**.

## 5. Evaluation methodology you MUST use (hard-won)
- **`jobs=1` is mandatory** for pods — opponents `aggressor`/`toby_master` use UNSEEDED RNG; `jobs>1` corrupts seed pairing outright.
- **There is no stable noisy-field operating point.** 18 seed bases scanned; even the best (base 900)
  swings locked C0 bust 36%→79% run-to-run because aggressor/toby are unseeded (engine seeds only card dealing).
- **Decision-grade field = `C0D` = `[hero, template, mathematician, shark, ref_bot_2]`** (all reproducible;
  locked-vs-locked 33/40 byte-identical, paired median 0, noise stdev ~714 — low-noise, not zero: `shark`
  has one minor unseeded branch). **All no-p50/bust-regression claims must use C0D.** On C0D the tolerances
  are tight (≈ p50_tol 500, bust_tol 0.05) — NOT the wide p50_tol=6000/bust_tol=0.15 that batch-1 calibrated
  for the *noisy* C0/C1 field. On a noiseless field even +1 bust is a real divergence.
- The toby/aggressor pods (C0/C1) are **directional-only effect-size reads** — never decision-grade. Use them only to flag concerns for human review.

## 6. What's been done — batches 1 & 2
**Batch 1:** built the gate harness; discovered the scaffold/source-of-truth issue + the gate-noise issue;
overlay-cap reduction = near-no-op (shelved); claude blocked at leakage (cosmetic strings); codex measurement-invalid at the broken base-142 point.
**Batch 2:** re-calibrated → C0D; gave codex + claude decision-grade verdicts (§7); built the LBR tool (§8).
Operational: 2 lanes stalled (headless) but their work was salvaged (see §11).

## 7. Candidate dispositions (all NOT clearers; nothing promoted)
- **codex** (`sibling-gate/codex.zip`, sha `e2ba542b…`; sibling `PokerBot-codex` branch `w4-track-1-lbr`,
  LBR spot corrections, self-labeled "forensic, not for promotion"): on C0D 40 paired seeds, **paired-diff
  median −1750/match, worse on 32/40 (~2.5σ)** → small but **real systematic regression**. Its big C0
  "survival gain" was an aggressor-floor artifact and does not generalize; on the clean field it bleeds EV
  by playing more marginal spots. Possible future work: keep the anti-aggressor robustness without the passive-field EV cost.
- **claude** (`batch2/claude-rescrub/claude_rescrubbed.zip`, sha `2d1288da…`; sibling `PokerBot-claude`
  branch `vladimir-audit-2026-05-28`, re-scrubbed of 19 cosmetic leakage strings + 1 behavior-preserving
  rename): on C0D 24 paired seeds, **p50 +2250 (better on 14/24) BUT +1 bust (2/24 vs 1/24)** → a genuine
  **chip-up/bust-up tradeoff**, fails the no-bust-regression bar as-is. Human-judgment call, not a dominated reject.
- **overlay-cap** (`overlay-cap/cap015.zip`, `cap010.zip`): `MAX_DEVIATION_PP` scalar doesn't exist in the
  shipped artifact (it's a discrete preflop overlay); re-cast shove-removal variants are a near-no-op vs the passive field. **Shelve.**

## 8. Infra status
- **Gate harness — DONE & usable:** `gate-harness/gate_harness.py` (+ README). Parameterized
  `--candidate/--locked/--pods/--seed-base/--seeds`; fail-fast static→smoke→pods; protected-SHA guards. Use with C0D + jobs=1.
- **LBR tool — BUILT but NOT VALIDATED (open):** `lbr-impl/lbr_check.py` (537 LOC, match-play LBR). **Sanity
  anchor FAILED**: v_final scored **aggregate −2848 / preflop −78.9 mbb/g** (negative ⇒ the "villain" loses to
  v_final ⇒ it is NOT actually best-responding; a true LBR is ≥0 and v_final's historical value is ~+7.4).
  So codex's "FAIL" (+978) and claude's number are **untrustworthy**. The gate's exploit arm is still
  effectively unmeasured. Canonical `tools/exploit_check.py` remains a stub. **Needs a stronger villain
  and/or much larger budget (the docstring target was hands=4000/rollouts=80) before its numbers mean anything.**

## 9. Patch-window (06-02) analyzer readiness (from earlier audit)
- `tools/analyze_hand_histories.py` (schema-introspecting, writes `data/finals_priors.npz`) exists **only in
  siblings** — claude 630 LOC (hardened, intended surface), codex 225 LOC — **ABSENT in canonical**. Either
  port into the `a00561c`-based release line or run the window from `PokerBot-claude`.
- **k-means bot-cluster fingerprints** are promised in both extractor docstrings but **unimplemented**.
- **Mehedi-class BB-defense leak has no history-parsing measurement** (only live engine-vs-fixed-zip probes);
  Toby river-trap prevalence IS covered by canonical untracked `tools/analyze_postflop_trap_prevalence.py`.

## 10. Open threads — prioritized next actions
1. **Fix/validate the LBR tool** (`lbr_check.py`): stronger villain (deeper best-response, not just one-step
   + passive tail) and/or hands=4000/rollouts=80; success = v_final lands a small POSITIVE near ~7.4 mbb/g.
   Until then the exploit arm is unmeasured. (Task #6 is in_progress for this.)
2. **Decide build-vs-drop on the two near-misses** (human MODIFY): codex (small clean-field regression) and
   claude (chip-up/bust-up tradeoff). Neither clears as-is; both are real signals.
3. **Reconcile `main`** and confirm the 06-02 window branches from `a00561c` / `release/v_final-e4b4a8f1`.
4. **Patch-window prep** (§9): port `analyze_hand_histories.py` into the release line; implement the
   bot-cluster fingerprints or drop the spec; add a position-aware Mehedi BB-defense history measure.
5. **Codex follow-up experiment:** can the anti-aggressor robustness be kept without the C0D EV bleed?
6. Run any new candidate through `gate_harness.py` on **C0D, jobs=1** before any claim.

## 11. Operational lessons
- **Headless lanes stall** when a single subprocess runs >3 min with no progress (the stall detector kills
  after 6×180s). Run pods/LBR **in the background** (`run_in_background`) or in **small seed-chunks** so the
  agent returns to its loop frequently. The deterministic C0D pod (fast opponents) completes fine; the
  toby/aggressor public-bot pods (8–91s/match) are what stall.
- **Salvage partial lane work** — a "failed" lane often finished its core analysis before stalling (batch-2
  lane 2A's `VERDICT.md` + `paired_analysis.json` were complete and decision-grade).
- **Worktree isolation** for src-mutating lanes; build candidates to artifact-local zips via `package.py
  --output <scratch>` (it has no default path, so it never touches the locked zips).
- Leftover (harmless): git worktree `/Users/farhad/Code/PokerBot/.claude/worktrees/wf_17770a2a-961-2`.

## 12. Key paths & commands
- Scratch root: `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-31-scratch-improve/`
  - `BATCH1_REPORT.md`, `BATCH2_REPORT.md`, this `HANDOVER.md`
  - `gate-harness/gate_harness.py` (+ README), `lbr-impl/lbr_check.py`
  - `sibling-gate/codex.zip`, `batch2/claude-rescrub/claude_rescrubbed.zip`, `overlay-cap/cap0{15,10}.zip`
  - `recalib-codex/VERDICT.md` + `paired_analysis.json` (decision-grade codex evidence)
- Pre-upload verify: `shasum -a 256 submissions/{v_final,best_green}.zip` →`e4b4a8f1…598`;
  `.venv/bin/python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip`;
  `.venv/bin/python tools/audit_strategy_leakage.py --zip submissions/v_final.zip`.
- Build & verify (project): `tools/package.py --output <scratch>.zip --strict`; `tools/smoke_run.py --zip <z> --hands 200`; `pytest tests/edge_cases -x`.

## 13. Task board
#1–#5,#7 completed · #6 (trustworthy LBR) **in_progress** — tool built, sanity anchor failed, needs debug ·
#8 (batch-2 synthesis) pending → effectively delivered by this handover, formally blocked on #6.

**Bottom line for the genius agent:** qualifier ships locked and verified; do finals work off `a00561c`;
gate every candidate on **C0D / jobs=1**; the highest-leverage open task is making the **LBR measurement
trustworthy** (the exploit arm is currently blind); two near-miss candidates await a human build/drop call.
