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

Task: P3 Preflop antecedent grid, candidate-only.

Use the global Hard Invariant above.

Goal:
Test whether tightening the heads-up button / small-blind / button open-any branch reduces Toby/Mehedi trap exposure without a structural postflop rewrite.

This is a candidate probe, not a promotion.

Source discipline:
- Base on release/v_final-e4b4a8f1 or locked zip extracted source.
- Do not use current main if it is scaffold.
- Do not touch v_final.zip or best_green.zip.

Worktree:
The orchestrator has already created the worktree:
  ../PokerBot-codex-preflop-antecedent on branch candidate/preflop-antecedent-grid-2026-05-29
You are launched with `-C ~/Code/PokerBot-codex-preflop-antecedent` so cwd is the worktree.

Output directory (write reports here; reference the main repo path):
/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/preflop-antecedent-grid/

Allowed edits:
- src/preflop_lookup.py only.
- tests/edge_cases/test_preflop_antecedent_grid.py
- candidate harness files under this artifact directory.

Forbidden edits:
- src/postflop.py
- src/bot.py
- src/opponent_model.py
- data/
- submissions/v_final.zip
- submissions/best_green.zip
- ext/

Candidate grid:
Build these candidate variants, one at a time:
A0 baseline extracted/release source, no change.
A1 HU/button open floor: score >= 20
A2 HU/button open floor: score >= 32
A3 HU/button open floor: score >= 40
A4 HU/button open floor: score >= 50
A5 position-specific:
   heads_up_button floor >= 32
   small_blind/button six-max floor >= 40

Implementation:
- In the branch where position in ("heads_up_button", "small_blind", "button")
  currently min-raises any hand, add score floor.
- Below floor:
  if can_check/free option semantics apply, check where legal;
  otherwise fold.
- Keep strong hands and normal range_open behavior unchanged.
- Do not add opponent-specific logic.

For each candidate:
1. Build candidate zip under:
   /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/preflop-antecedent-grid/zips/
2. Run:
   - leakage audit
   - import audit
   - edge tests
   - validator
   - smoke
3. Run H2H:
   - Toby master
   - Mehedi mybot
   - Pav skantbot7.9
   - Pav skantbot7.6
   - famadeo
   - neel
   - stoppedtime24
   - reference templates if feasible

Metrics:
- scheduled bb/100
- actual bb/100
- CI
- actual hands
- early bust rate
- hero errors
- p99 latency
- frequency of HU button opens
- frequency of river trap entries if decision logs available

Decision:
- If no variant materially improves Toby/Mehedi, output NO_PREFLOP_ONLY_FIX.
- If a variant improves Toby/Mehedi but regresses GREEN cells, output NOT_PROMOTABLE.
- If a variant improves Toby/Mehedi and does not regress, output DEFENSIVE_PREFLOP_CANDIDATE, but do not promote.

Outputs:
- PREFLOP_ANTECEDENT_GRID_REPORT.md
- RESULTS.json
- per-candidate diffs
- candidate zip paths
- command_logs/
- STATUS_BLOCK.md

Final line:
"Locked v_final.zip remains upload target unless human explicitly opens MODIFY gate."
Verify protected SHAs after the run.
