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

Task: P5 Patch-window postflop-trap prevalence extractor, tooling only.

Use the global Hard Invariant above.

Goal:
Extend patch-window readiness so real 2026-06-02 hand histories can tell us whether the Toby/Mehedi postflop-trap class is actually present in the qualifier field.

This is tooling-only. No runtime strategy edits.

Worktree:
The orchestrator has NOT created a separate worktree for this lane.
Use a feature branch inside the main worktree (~/Code/PokerBot):
  tooling/postflop-trap-extractor-2026-05-29
Create it with:
  git checkout -b tooling/postflop-trap-extractor-2026-05-29
If the branch already exists from a prior run, switch to it instead of recreating.

Output directory:
consult/artifacts/2026-05-29-away/patch-window-postflop-extractor/

Allowed edits:
- tools/analyze_hand_histories.py, or a new tool:
  tools/analyze_postflop_trap_prevalence.py
- tests/integration/
- docs/playbooks/patch-window.md addendum, if needed.
- Artifact docs under this output directory.

Forbidden edits:
- src/
- data/finals_priors.npz
- submissions/
- ext/

Goal behavior:
Create a tool that can read the same JSON/JSONL hand histories supported by analyze_hand_histories.py and emit postflop prevalence signals:

Core cluster key:
street__position__hero_action__board_texture_bucket

Required outputs:
- total records found
- records successfully parsed
- postflop action records parsed
- river action records parsed
- top clusters by frequency
- top clusters by chip impact if hand outcomes are present
- river can_check raise frequency on:
  unpaired two-tone static
  wet flush-draw
  paired two-tone static
- river facing-bet fold/call frequencies on:
  paired two-tone static
  unpaired two-tone static
- action sequence fingerprints that resemble Toby/Mehedi traps
- parse quality JSON with failures and schema keys.

Schema robustness:
Reuse existing analyzer alias logic if possible:
- deep wrappers
- pf/f/t/r street names
- amountBB fields
- mixed casing
- JSONL
- nested streets
- non-finite amount rejection

Tests:
Build minimized synthetic fixtures:
1. Toby-like river can_check trap sequence.
2. Toby-like paired-board river fold sequence.
3. Mehedi-like early-bust sequence if inferable from logs.
4. Six-max multiway hand with anonymous players.
5. JSONL fixture with mixed casing.
6. Negative fixture with opaque strings only -> should not crash and should report zero parsed postflop records.

Commands:
- .venv/bin/python -m pytest tests/integration -x
- Run tool against synthetic fixtures and write reports.

Outputs:
- POSTFLOP_EXTRACTOR_REPORT.md
- RESULTS.json
- example_report.txt
- tests added/updated
- DIFF.patch
- STATUS_BLOCK.md

Report must include:
1. Exact command to run on real 2026-06-02 histories.
2. Sanity thresholds:
   - proceed if records_successfully_parsed > 0
   - proceed if postflop_action_records > 0
   - treat as inconclusive if river_action_records too low
   - fallback to default if schema opaque
3. How this interacts with B9:
   - It informs B10 manual review.
   - It does not itself change strategy.
   - It may justify a postflop candidate only if real histories show material prevalence.

Verify protected SHAs after the run.
