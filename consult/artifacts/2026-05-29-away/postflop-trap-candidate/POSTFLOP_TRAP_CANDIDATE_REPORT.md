# Postflop trap candidate report — 2026-05-29

## Verdict

**PATCH_NOT_PROMOTABLE.** The candidate materially reduces the Toby `master` heads-up failure, but it does not clear the promotion bar: smoke exits nonzero on the repository smoke wrapper, the all-template/regression surface is not clean, and Pav 7.9 remains slightly negative in the final selected-candidate run.

No artifact was promoted or copied over the locked submission.

## Candidate

- Zip: `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/postflop-trap-candidate/zips/v_postflop_trap_candidate.zip`
- Zip sha256: `136c8cde3258995bde89eb14e91b678c329c3af2a5b16806c453a4c4d68d8571`
- Edits: `src/postflop.py`, `tests/edge_cases/test_postflop_trap_candidate.py` only.
- Patch shape: river-only texture guard suppresses automatic 2/3-pot raise on two-tone static rivers unless the hand is clearly strong; facing-bet paired/two-tone/static call is restricted to clear river value after prior investment.

## Protected artifact status

- Expected locked SHA: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- Before and after checks both matched for `/Users/farhad/Code/PokerBot/submissions/v_final.zip` and `/Users/farhad/Code/PokerBot/submissions/best_green.zip`.
- `ext/fullhouse-engine/` and `ext/public-bots/` were not edited.

## Preflight

- Worktree `HEAD` equals `release/v_final-e4b4a8f1`: `a00561cfadf18d3bc2b03ef2403e55346207670c`.
- Locked zip `src/postflop.py`, release source, and pre-patch worktree source all matched sha256 `f1d81e1ab99471768172c8c4bcd22f6cd988c1fa4eb09cbb102d0ca9a51f7dee`.

## Static and unit gates

| Gate | Result | Evidence |
| --- | --- | --- |
| leakage audit requested `--src` | unsupported | tool only accepts `--zip`; logged exit 2 |
| leakage audit on candidate zip | PASS | `final_audit_strategy_leakage_zip.log` |
| import audit | PASS | cold import 0.286s, RSS 32.6 MB |
| edge cases | PASS | 29 passed |
| validator | PASS | engine validator accepted candidate zip |
| smoke 200 | FAIL_HAND_COUNT_BASELINE_PARITY | candidate 136/200, no errors, +10000 chips; locked baseline also 136/200, no errors, +10000 chips |
| exploit check | PASS | preflop 18.0 mbb/g, aggregate 5.65 mbb/g |

## Trigger H2H

| Opponent/base | scheduled | actual | scheduled bb/100 | 95% CI | actual bb/100 | hero/opp errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Toby master base 142 candidate | 20000 | 2207 | +3 | [-3, +9] | +27.19 | 0 / 0 |
| Toby master base 242 candidate | 20000 | 2565 | -1 | [-7, +5] | -7.797 | 0 / 0 |

Locked prior Toby evidence: base 142 `-14.0` CI `[-16.0, -12.0]`; base 242 `-16.6` CI `[-18.0, -15.0]` over 100k scheduled per base. Candidate improvement is material, but the 20k candidate CIs still cross zero.

Mehedi P0 classification was `DIFFERENT_LEAK`; optional validation on base 142 was `+6.0` scheduled bb/100 with CI `[-4.0, +16.0]`, zero errors.

## Regression

Reference bots, selected final candidate:

| Opponent | scheduled bb/100 | 95% CI | errors |
| --- | ---: | ---: | ---: |
| template | +20 | [+20, +20] | 0 / 0 |
| aggressor | +0 | [-10, +10] | 0 / 0 |
| mathematician | +20 | [+20, +20] | 0 / 0 |
| shark | +20 | [+20, +20] | 0 / 0 |
| ref_bot_2 | +20 | [+20, +20] | 0 / 0 |

Same-harness locked `aggressor` was `+4.0` CI `[-6.0, +12.0]`; the candidate is `0.0` CI `[-10.0, +10.0]`, so regression is not CI-excluding but is a material mean drop on this short check.

Public bots, selected final candidate:

| Opponent | scheduled bb/100 | 95% CI | errors |
| --- | ---: | ---: | ---: |
| Pav skantbot7.9 | -1.074 | [-4.194, +2.281] | 0 / 0 |
| Pav skantbot7.6 | +5.619 | [+1.623, +9.448] | 0 / 0 |
| famadeo codex_holdem | +3.885 | [-4, +11.36] | 0 / 0 |
| neel | +18.74 | [+16.21, +20] | 0 / 0 |
| stoppedtime24 mybot | +20 | [+20, +20] | 0 / 0 |
| vladimir | SKIPPED | public live bot missing required data/model, prior run timeboxed on fallback | n/a |

## Files

- `RESULTS.json` — structured evidence.
- `DIFF.patch` — candidate source/test diff.
- `command_logs/` — raw command output and H2H JSON/logs.
- `STATUS_BLOCK.md` — compact status block.
- `zips/v_postflop_trap_candidate.zip` — candidate artifact only.

## Decision

Do not promote. The patch is useful evidence that the Toby leak is river-postflop and that suppressing weak two-tone static river bets helps, but the regression surface and smoke wrapper result are not clean enough for a submission override.

Human promotion gate required; locked v_final.zip remains upload target unless explicitly overridden.
