Hard invariant:
- Do not modify, rebuild, repackage, copy over, or replace:
  submissions/v_final.zip
  submissions/best_green.zip
- Both must remain sha256:
  e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
- Do not edit ext/fullhouse-engine/.
- Do not edit ext/public-bots/ snapshots.
- Do not infer ship behavior from current main src/. Main may be scaffold/stub.
- If strategy source is needed, use release/v_final-e4b4a8f1 or extract the locked zip.
- Any candidate artifact must have a new name and must never replace v_final.zip or best_green.zip.
- All commands must use .venv/bin/python, not host python.
- Record protected artifact SHA before and after the run.
- Write all outputs under consult/artifacts/2026-05-29-away/<lane-name>/ unless explicitly told otherwise.

Task: P2 Isolated postflop-trap candidate, candidate-only.

Use the global Hard Invariant above.

Goal:
Create and evaluate a minimal candidate patch for the Toby/Mehedi postflop-trap leak without touching the locked submitted artifact.

This is an exploratory candidate lane. It must not promote anything automatically.

Critical source discipline:
- Do not use current main src/ if it is scaffold.
- Base the candidate on release/v_final-e4b4a8f1 or on source extracted from the locked v_final.zip.
- If release/v_final-e4b4a8f1 is unavailable, extract v_final.zip into this lane artifact directory and patch that extracted source.
- Do not overwrite submissions/v_final.zip or submissions/best_green.zip.

Worktree:
The orchestrator has already created the worktree:
  ../PokerBot-codex-postflop-trap on branch candidate/postflop-trap-2026-05-29
You are launched with `-C ~/Code/PokerBot-codex-postflop-trap` so cwd is the worktree.
Use git inside this worktree for any commits. Do not touch the main worktree.

Output directory (write reports here; reference the main repo path):
/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/postflop-trap-candidate/

Problem to solve:
Toby `master` loss localized to:
1. river heads_up_button raise / raise_le_2/3pot on unpaired two-tone static wet-flush-draw boards.
2. river fold on paired two-tone static boards.
3. preflop heads-up button open-any is an antecedent, not the primary kill.

Mehedi may or may not match; read P0 output if already available. If P0 is unavailable, proceed against Toby and run Mehedi as validation.

Allowed edits:
- src/postflop.py only, in the release source / extracted candidate source.
- tests/edge_cases/test_postflop_trap_candidate.py
- candidate harness under this lane artifact directory.

Forbidden edits:
- src/bot.py
- src/preflop_lookup.py
- src/opponent_model.py
- src/equity.py
- src/sizing.py
- data/
- submissions/v_final.zip
- submissions/best_green.zip
- ext/fullhouse-engine/
- ext/public-bots/

Patch requirements:
- Minimal code.
- No opponent names.
- No repo names.
- No env-var strategy branches.
- No label leak.
- No runtime network/file I/O beyond normal data loading.
- No new forbidden imports.
- No use of pickle.
- Must return only legal actions.

Patch design constraints:
- The patch should target river trap behavior directly, not broad postflop rewrites.
- Preserve existing fixed-response cells.
- Preserve flop blueprint behavior.
- Preserve existing turn behavior unless evidence demands otherwise.
- Consider these candidate adjustments, but validate empirically:
  A. On river with can_check=True, suppress automatic 2/3-pot raise on wet/two-tone/static boards unless hand class is clearly strong.
  B. On river facing a large bet after prior investment on paired/two-tone/static boards, avoid the current brittle paired-only rule if it is folding too much or calling too much; determine from logs which direction fixes Toby.
  C. Use pot/owed/board texture/hand class; do not call equity_vs_range from the heuristic fallback if that path is currently budget-sensitive.
  D. Make the fallback passive: check/fold more often unless evidence says the leak is overfolding after induced investment.

Tests:
Add at least four edge tests:
1. River can_check wet/two-tone static with weak hand: candidate should check, not 2/3-pot raise.
2. River can_check dry/value hand: candidate should preserve value behavior if previous behavior was good.
3. River facing bet paired/two-tone static after prior investment: candidate behavior matches the evidence from Toby clusters.
4. Legality test across all patched outputs.

Candidate packaging:
- Build only:
  /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/postflop-trap-candidate/zips/v_postflop_trap_candidate.zip
  or, if package.py cannot output there:
  /Users/farhad/Code/PokerBot/submissions/v_postflop_trap_candidate.zip
- Never write v_final.zip or best_green.zip.

Evaluation stages:
Stage 0 -- preflight:
- Verify protected SHAs.
- Confirm candidate source matches release/v_final-e4b4a8f1 / locked zip source.

Stage 1 -- unit and static gates:
- .venv/bin/python tools/audit_strategy_leakage.py --src src/
- .venv/bin/python tools/import_audit.py --max-seconds 1.5 --max-mb 400
- .venv/bin/python -m pytest tests/edge_cases -x
- .venv/bin/python ext/fullhouse-engine/sandbox/validator.py <candidate_zip>
- .venv/bin/python tools/smoke_run.py --zip <candidate_zip> --hands 200

Stage 2 -- trigger-opponent H2H:
Run scheduled bb/100 and actual bb/100, paired seats:
- Toby master: bases 142 and 242.
- Mehedi mybot: bases 142 and 242, if P0 says SAME_TRAP or P0 unavailable.
- Minimum result target:
  candidate improves Toby by material margin versus locked artifact.
  candidate must not create hero errors or latency issues.

Stage 3 -- regression:
Run against:
- Pav skantbot7.9
- Pav skantbot7.6
- famadeo codex_holdem
- neel
- stoppedtime24 mybot
- vladimir if usable with data/model
- template, aggressor, mathematician, shark, ref_bot_2

Use available harnesses:
- public_saturation-style H2H for public bots.
- benchmark/all-template gate for references.

Promotion bar for report only:
- PATCH_PROMOTABLE_CANDIDATE only if:
  1. Trigger-opponent improvement is material.
  2. No public-opponent regression with CI excluding zero in bad direction.
  3. Validator/import/edge/smoke/leakage all pass.
  4. All-template benchmark does not materially regress.
  5. exploit_check remains under caps.
  6. v_final.zip and best_green.zip untouched.

Outputs:
- POSTFLOP_TRAP_CANDIDATE_REPORT.md
- RESULTS.json
- DIFF.patch
- command_logs/
- candidate zip path
- STATUS_BLOCK.md

Report verdict:
- PATCH_PROMOTABLE_CANDIDATE
- PATCH_NOT_PROMOTABLE
- NO_PATCH_FOUND
- ABORTED_INVARIANT_RISK

Even if PATCH_PROMOTABLE_CANDIDATE, do not replace any artifact.
Final line must say:
"Human promotion gate required; locked v_final.zip remains upload target unless explicitly overridden."
Verify protected SHAs after the run.
