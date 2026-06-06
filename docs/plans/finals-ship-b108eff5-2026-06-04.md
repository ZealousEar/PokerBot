# Finals Ship: b108eff5 Freeze + Conditional Chip-EV Probes — Plan

**Date:** 2026-06-04 · **Deadline context:** finals close 2026-06-05 · **Author:** orchestrated from two genius LLM consults (standard + extended), merged and de-duplicated, grounded against the live repo.

## Goal

Ship the patched finals baseline `b108eff5` (`submissions/v_final.zip`) to the finals as a **pure chip-EV** bot. Default action is **freeze and ship the existing bytes unchanged**. Land a strategy edit **only** if a single, surgical candidate beats the exact `b108eff5` zip in a same-seed paired A/B run with all safety gates green. End state: SHA-verified artifact, full verification pass, human-gated upload.

## Posture update (2026-06-04, post-upload)

The `b108eff5` build is **already uploaded and live** for finals. Given a re-upload window before close (2026-06-05) and "nothing to lose," the posture shifts from *freeze-by-default* to **lean into the candidate edits**: the live bot is the floor, and the paired A/B gate means we **re-upload only a candidate that provably beats the live bot**. A losing candidate is discarded and the live build stays. Two invariants hold: re-upload only on a proven head-to-head win, and **upload stays human-gated**. Item 0 (verify) and Item 1 (commit source) still run first so any candidate is built and tested against a clean, reproducible baseline.

## Decision (both consults unanimous)

- **Ship pure chip-EV. Do NOT bake in always-on ICM / survival caution.** No runtime phase signal exists (no tournament ID, hands-remaining, blind level, final-table flag, or cross-match state), so any survival brake would also tax Bubble play — where scoring is cumulative chip delta and the field overfolds. See `consult/artifacts/2026-06-04-finals-recon/finals_brief.md`, `field_meta.md`.
- **Freeze by default.** The highest-EV move is verification + packaging discipline, not a last-minute unpaired strategy edit. The patched baseline already includes a near-Nash blueprint + bounded overlay and fixed the R2 postflop stack-off leak.
- **Edit only the editable archive source**, never the canonical scaffold `src/` (which is a stub, not the b108eff5 implementation).

## Background (verified seams)

### Artifact identity — confirmed
- `submissions/v_final.zip` sha256 = `b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b`, size 44274 — matches the finals baseline `b108eff5`. **Freeze = ship these exact bytes; no repackage needed.**
- `submissions/best_green.zip` sha256 = `e4b4a8f1…`, size 28208 — different artifact; do not confuse with the finals ship.
- The b108eff5 source is **zip-only / not committed to git** (`git status` shows recon dir untracked; `AGENTS.md:10-12` confirms). Two editable copies exist and must be reconciled before any rebuild:
  - `submissions/archive/finals-ship-b108eff5-editable-source/{bot.py,src/,data/}`
  - `consult/artifacts/2026-06-04-finals-recon/patched_src/{bot.py,src/,data/}`

### Strategy source seams (editable archive = `submissions/archive/finals-ship-b108eff5-editable-source/`)
- Decision flow: root `bot.py` shim → `src/bot.py:decide()` → `_strategy()` → `_preflop_action()` / `postflop.decide_postflop()` → `_legalize_action()`.
- `src/ranges.py`:
  - `THREEBET_VS_OPEN` `:252`, `THREEBET_BTN_VS_OPEN` `:265`, `THREEBET_SB_VS_OPEN` `:278`, `THREEBET_BB_VS_OPEN` `:289`.
  - `A9s/A8s/A7s/A6s` **absent** from every 3-bet set. `A5s/A4s` **present** in each (`:261/:274/:286/:298`).
  - `FOURBET_VS_THREEBET` `:326`; `A5s/A4s` present at `:328`.
- `src/postflop.py`:
  - `decide_postflop()` `:96`; `pot_odds` `:128`.
  - `can_check` c-bet bluff block (`cbet_bluff_prob`) `:146-156`.
  - facing-bet branch `:158`; `eq_strong`, `commit_ok`, `owed_frac` computed `:168-170`.
- `src/hand_features.py`: `classify_hand = hand_features` `:246` (reuse for made-hand classification; do not duplicate board logic).
- `src/commitment.py`: `COMMIT_FRACTION = 0.40` `:11`, `SAFE_EQ_THRESHOLD = 0.55` `:14`, `LARGE_CALL_MAX_OWED_FRACTION = 0.25` `:15`.

### A/B harness — verified
- `tools/deployed_artifact_gauntlet.py` is the real engine-backed runner: imports `sandbox.match as match_mod` (`:35-36`), calls `match_mod.run_match(..., seed=seed)` (`:486`), runs **same-seed, both-orientation** matches vs reference bots + synthetic opponent zips (`:477-486`, `:876-880`). Flags: `--bot`, `--baseline`, `--outdir`, `--hands-per-opponent` (default 800), `--match-len` (default 200), `--seed-base` (default 42), `--skip-matches`, `--skip-probes` (`:832-844`).
- **Caveat:** `--baseline` is only inventoried, not matched (`:891-892`). True A/B = run the gauntlet **twice** (baseline zip, then candidate zip) on identical `--seed-base`/opponents, then diff aggregate chip delta.
- `tools/benchmark.py` is a **TODO stub** (`:18-21`, `:74-92` print `TODO …`). **Do not use it as acceptance evidence.**

### Field facts driving the chip-EV thesis
- Finalist field median fold-to-3bet ≈ 74.7% (p90 85.2%), fold-to-cbet ≈ 52.8%, median VPIP 31.1% / PFR 20.5% — overfolds to pressure (`field_meta.md`).
- Thorp bust split: ~75% (15/20 clean busts) postflop; largest losses cluster in postflop stack-offs / top-pair / two-pair / trips payoffs; only ~5/top-20 are preflop (`thorp_leak_report.md`, `VERIFICATION_REPORT.md`).
- Implication: residual chip-EV lives in (a) preflop/flop *pressure* against overfolders and (b) tighter postflop *payoff discipline* — not in broad rewrites.

## Approach

1. **Freeze first.** Treat `b108eff5` (existing `v_final.zip` bytes) as the ship artifact. Run the full verification gauntlet against it (this is the user's "failure-mode check"). If anything fails, fix the failure — not the strategy.
2. **Conditional probes, paired-gated.** If verification is green and time remains, test the merged candidate list below, one isolated branch each, against the exact `b108eff5` zip. Promote a candidate **only** if it clears the shared promotion gate. Otherwise ship frozen bytes.
3. **Commit the source.** Reconcile the two editable copies and commit the b108eff5 source before shipping (currently zip-only) so the finals artifact is reproducible.
4. **Human-gated upload** of the SHA-verified bytes. No autonomous upload (hard rule, CLAUDE.md).

### Shared promotion gate (applies to every candidate)

A candidate ships **only if all** hold, comparing candidate-zip vs exact `b108eff5`-zip on identical seeds/opponents:
- Aggregate scheduled chip delta beats baseline by **≥ +2 bb/100** (use +3 for the wider preflop candidate A, per the more conservative consult).
- **No** opponent bucket worse than **−5 bb/100** (allow down to −10 only if aggregate ≥ +8).
- **Zero** runner errors / timeouts / illegal actions.
- No regression on large-commit safety probes (run `--skip-matches` probe pass first).
- Validator + import audit + `pytest tests/edge_cases -x` all green.
- Reject if the gain comes only from one outlier opponent (e.g. `all_in_maniac`) or one high-variance seed.

## Work Items

### Item 0 — Freeze + verify baseline (REQUIRED; this is the ship path)
**Goal:** Prove the existing `b108eff5` bytes pass every gate, then lock them as the ship artifact.
**Done when:**
- SHA of `submissions/v_final.zip` re-confirmed = `b108eff5…`.
- `python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip` → pass.
- `python tools/import_audit.py` → pass.
- `pytest tests/edge_cases -x` → pass.
- Deferred Docker smoke completed: `python tools/smoke_run.py --zip submissions/v_final.zip --hands 200` → pass.
- Residual large-commit probe pass green: `python tools/deployed_artifact_gauntlet.py --bot submissions/v_final.zip --outdir consult/artifacts/finals-freeze/b108eff5-probes --skip-matches`.
- STATUS.md updated with SHA, command outputs, GREEN, and an explicit "strategy code frozen" line.
**Key files:** `submissions/v_final.zip`, `ext/fullhouse-engine/sandbox/validator.py`, `tools/{import_audit.py,smoke_run.py,deployed_artifact_gauntlet.py}`, `tests/edge_cases/`, `STATUS.md`.
**Dependencies:** none. **Size:** S (verification only).

### Item 1 — Commit the b108eff5 source (REQUIRED before ship)
**Goal:** Make the finals artifact reproducible from committed source.
**Done when:** the two editable copies (`submissions/archive/finals-ship-b108eff5-editable-source/` and `consult/artifacts/2026-06-04-finals-recon/patched_src/`) are byte-diffed and reconciled; the authoritative source is committed; a rebuild from it reproduces a zip whose decision-relevant behavior matches `b108eff5` (validator-equivalent). Note any byte differences from the shipped zip and confirm they are packaging-only, not strategy.
**Key files:** both editable source trees, `tools/package.py`.
**Dependencies:** none (parallel to Item 0). **Size:** S–M.

### Item 1.5 — Failure-mode tester (REQUIRED; reusable on every artifact)
**Goal:** A single repeatable "does this bot break?" check that runs against the live build now and against any candidate zip before re-upload. It catches catastrophic failures (the things that actually lose finals), separate from chip-EV.
**What it must exercise (per zip):**
- **Contract / crash safety:** no exceptions, no timeouts (>2 s/decide), no illegal actions, no malformed action dicts. Drive via the sandbox runner over a fuzzed sweep of game states (varied streets, stacks, can_check true/false, all-in spots, min-raise snaps). Reuse `tests/edge_cases/` + `tools/edge_case_harness.py`.
- **Known disaster spots (regression probes):** dry-board TPTK/overpair into set in a bloated pot; dominated underboat near-dead commitment; A-high flush on monotone; near-dead postflop stack-off (the original R2 leak). Run via `python tools/deployed_artifact_gauntlet.py --bot <zip> --skip-matches` (probe-only pass) and assert no large-commit on these states.
- **Validator + import + smoke:** `validator.py`, `import_audit.py`, `smoke_run.py --hands 200` all green.
- **Output:** a pass/fail summary per zip, logged to STATUS.md with the zip's SHA.
**Done when:** the tester runs end-to-end on `submissions/v_final.zip` and returns a clean pass; it accepts an arbitrary `--zip` so any candidate can be checked with one command before the paired A/B.
**Key files:** `tools/edge_case_harness.py`, `tools/deployed_artifact_gauntlet.py`, `tools/smoke_run.py`, `ext/fullhouse-engine/sandbox/{validator.py,runner.py}`, `tests/edge_cases/`, `STATUS.md`.
**Dependencies:** none (composes existing tools; build the wrapper if one doesn't already exist — do not weaken any safety rail). **Size:** S–M.

### Item 2 — Candidate A: widen non-committal 3-bet pressure (CONDITIONAL)
**Goal:** Steal more opens from an overfolding field by adding suited-ace blockers to positional 3-bet ranges. Target fold equity, not bigger stack-offs.
**Change:** add `A9s, A8s, A7s, A6s` to `THREEBET_BTN_VS_OPEN` (`ranges.py:265`) and `THREEBET_SB_VS_OPEN` (`:278`). **BB is contested** between the two consults — exclude `THREEBET_BB_VS_OPEN` by default (avoids building OOP bloated pots vs tight-caller/station cluster); test BB inclusion only as a separate sub-variant if BTN+SB clears the gate and time allows. Do **not** touch `FOURBET_VS_THREEBET`, `CALL_VS_THREEBET`, sizing, or all-in logic.
**Done when:** candidate clears the shared promotion gate (≥ +3 bb/100 aggregate for this wider-range candidate); 4-bet/preflop-all-in incidents do not rise materially; validator/edge/import green.
**Key files:** `…/src/ranges.py`. **Dependencies:** Item 0 green. **Size:** S.

### Item 3 — Candidate B: dry-flop c-bet bluff bump (CONDITIONAL)
**Goal:** Take one more class of low-risk half-pot stabs on dry boards the field overfolds.
**Change:** in `decide_postflop()` `can_check` branch (`postflop.py:146-156`), add a small `cbet_bluff_prob` bump (≈ +0.07) for **dry, unpaired, non-high-card** flops only. Keep existing dry-high-card bump (+0.10), the `0.25 < eq < 0.55` bluff window, and 0.50-pot sizing. Do **not** change wet/paired boards, turn/river, value thresholds, equity trial counts, or sizing.
**Done when:** clears the shared promotion gate (≥ +2 bb/100); no rise in all-in count; large-commit probes unchanged; validator/edge/import green.
**Key files:** `…/src/postflop.py`. **Dependencies:** Item 0 green. **Size:** S.

### Item 4 — Candidate C: top-pair/two-pair large-payoff brake (CONTINGENCY ONLY)
**Goal:** Cut tail losses from the dominant postflop bust class — but only if a residual large-commit failure is reproduced on `b108eff5`.
**Gate to even attempt:** run direct probes first (dry-board TPTK/overpair into set in bloated pot; underboat; A-high flush on monotone; `dominated_underboat_near_dead_commitment`). Proceed **only** if `b108eff5` actually large-commits in one of these.
**Change (if triggered):** in `decide_postflop()` facing-bet branch (after `:168-170`), block **large raises/calls** (not normal calls) when: street in {turn, river} AND would commit ≥ 0.40 stack AND board unpaired & no flush possible AND made-hand category pair/two_pair (via `classify_hand`, `hand_features.py:246`) AND `eq_strong < 0.70` → route to existing `can_call_large()`/fold. Do **not** edit `commitment.py` constants (too blunt; hits draws and bluff-catchers equally).
**Done when:** the reproduced probe is fixed AND paired EV is no worse than −2 bb/100 AND it reduces ≥40%-stack losing commitments without merely making the bot passive. **Reject if it only lowers bust count while reducing cumulative chip delta** (Bubble scores chip delta, not survival).
**Key files:** `…/src/postflop.py`, `…/src/hand_features.py`. **Dependencies:** Item 0 green + reproduced failure. **Size:** M.

### Item 5 — Candidate D: remove A5s/A4s 4-bet bluffs (NOT RECOMMENDED)
**Goal:** (Documented for completeness.) Reduce rare preflop spew by removing `A5s/A4s` from `FOURBET_VS_THREEBET` (`ranges.py:328`).
**Status:** Do **not** touch. Evidence is against it — busts are 75% postflop, and these blockers are profitable vs an overfolding field. Revisit only if new b108eff5-specific evidence shows preflop busts dominate.

## DO-NOT-TOUCH (merged from both consults)

1. **No phase / ICM detection** — no runtime signal exists; any such logic is fabricated and taxes Bubble.
2. **Edit only the editable archive source**, never the canonical scaffold `src/` (stub).
3. **No changes to root `bot.py` shim or zip layout** — strict validator contract (root `bot.py` only, no other root `.py`, no `.py` in `data/`, no symlinks, size caps).
4. **No changes to `_legalize_action()`, `_safe_fallback()`, `sizing.legal_raise_total()`** unless fixing a failing validator/edge test — these are the final safety rails.
5. **Do not raise equity Monte-Carlo trial counts** (tuned for ≤280 trials under 2 s / 0.5 CPU).
6. **No new deps / forbidden modules** (PyTorch, solvers, network, subprocess, multiprocessing, threading, pickle, importlib, etc.).
7. **Do not rewrite `opponent_model.py` or regenerate `field_priors.npz`** — bounded overlay is already integrated; unverified retune changes many behaviors at once.
8. **Do not loosen postflop value thresholds or `can_commit_raise()`** — remaining credible postflop work is tighter, not looser (R2 failure was near-dead stack-off).
9. **Do not use `tools/benchmark.py` as arbiter** — it is a TODO stub. Use `deployed_artifact_gauntlet.py` paired runs.
10. **No solver / CFR / Nash de-risk work** — calendar-infeasible, gated off.
11. **No autonomous upload** — human-gated, SHA-verified bytes only (CLAUDE.md hard rule).

## Implementation order

1. Item 0 — verify existing `b108eff5` bytes pass every gate.
2. Item 1 — reconcile + commit the source (parallel-safe).
3. Item 1.5 — build/run the failure-mode tester; confirm the live build passes clean. This is the gate every candidate must also clear.
4. Candidates in parallel (nothing-to-lose posture): Item 2 (Candidate A) and Item 3 (Candidate B) as isolated branches. For each: failure-mode tester → paired A/B vs the exact live `b108eff5` zip.
5. Item 4 (Candidate C) **only** if the failure-mode tester reproduces a large-commit on `b108eff5`.
6. Item 5 — skip.
7. **Re-upload decision:** if a candidate clears both the failure-mode tester and the paired A/B gate, it becomes the new ship artifact; otherwise the live `b108eff5` stays. Append STATUS.md proof-of-green with SHA.
8. Human-gated, SHA-verified re-upload (only on a proven win).

## Open Questions

- **Source reconciliation:** do `submissions/archive/finals-ship-b108eff5-editable-source/` and `consult/artifacts/2026-06-04-finals-recon/patched_src/` byte-match? Which is authoritative for the commit in Item 1? (Resolve before any rebuild.)
- **Time budget:** with finals close 2026-06-05, is there room to run any conditional candidate (each ≈ probe pass + paired gauntlet + validator/edge ≈ 30–45 min), or is freeze-only the call? Freeze is fully sufficient to ship.
- **Candidate A BB inclusion:** keep excluded by default (recommended) unless paired evidence justifies the OOP risk.

## References

- Consults: standard + extended genius LLM responses (pasted in task; this plan is their merged, de-duplicated synthesis).
- `consult/artifacts/2026-06-04-finals-recon/{field_meta.md,thorp_leak_report.md,finals_brief.md,VERIFICATION_REPORT.md,finalist_dossiers.md}`
- `docs/investigations/finals-prep-postmortem-2026-06-04.md`, `STATUS.md [FINALS-RECON]`
- Editable source: `submissions/archive/finals-ship-b108eff5-editable-source/src/{ranges.py,postflop.py,commitment.py,hand_features.py}`
- Harness: `tools/deployed_artifact_gauntlet.py`; stub to avoid: `tools/benchmark.py`
