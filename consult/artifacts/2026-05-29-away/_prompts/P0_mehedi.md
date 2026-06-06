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

Task: P0 Mehedi decision-cluster analysis, no edits.

Use the global Hard Invariant above.

Goal:
Determine whether Mehedi-dev-2404/fullhouse-engine `bots/mybot` RED result is caused by the same postflop-trap-style river heuristic leak observed against TobyCoad/fullhouse-engine `bots/master`, or by a different leak.

Context:
- Toby `master` is RED at -15.30 scheduled bb/100 over 200k scheduled / 10,596 actual hands.
- Mehedi `bots/mybot` is RED + NEW-THREAT at about -9 scheduled bb/100 over 20k scheduled / 3,767 actual hands.
- Toby cluster localization found three material river clusters:
  1. river heads_up_button raise / raise_le_2/3pot on unpaired two-tone static wet-flush-draw boards.
  2. river fold on paired two-tone static boards.
  3. same paired-board fold cluster with label drift.
- Prior allowed seams were checked and not material:
  preflop pressure overlay, six-max position labeling, limp+iso, illegal check->call.
- The only material seam was postflop heuristic behavior.

Inputs:
- consult/artifacts/2026-05-29-public-repo-drift/DRIFT_REPORT.md
- consult/artifacts/2026-05-29-public-repo-drift/RESULTS.json
- consult/artifacts/2026-05-29-public-drift-patch/PATCH_REPORT.md
- consult/artifacts/2026-05-29-public-drift-patch/CLUSTER_NOTES.md
- consult/artifacts/2026-05-29-public-drift-patch/instrumented_h2h.py
- Existing temporary Mehedi packaged opponent zip if present.
- If the Mehedi zip is absent, rebuild a temporary zip under this lane artifact directory from the public repo; do not modify ext/public-bots.

Output directory:
consult/artifacts/2026-05-29-away/mehedi-cluster/

Run plan:
1. Verify protected SHAs before:
   shasum -a 256 submissions/v_final.zip submissions/best_green.zip

2. Validate or build the Mehedi opponent zip.
   Use only a temporary artifact path:
   consult/artifacts/2026-05-29-away/mehedi-cluster/opponent_zips/mehedi_mybot.zip

3. Run instrumented paired H2H against Mehedi:
   - Artifact-bound hero: submissions/v_final.zip
   - Opponent: Mehedi mybot zip
   - Use the same seed/orientation schedule as the drift audit if recoverable.
   - Otherwise use paired seed bases 142 and 242.
   - Capture at least:
     scheduled hands,
     actual hands,
     scheduled bb/100,
     actual bb/100,
     95% CI,
     hero errors,
     opponent errors,
     p99 latency if available.

4. Capture hero decision logs with:
   - hand_id
   - match_id
   - seed
   - orientation
   - final hand chip delta
   - street
   - position label
   - action class
   - raw action
   - pot
   - amount_owed
   - can_check
   - current_bet
   - min_raise_to
   - board
   - board texture bucket
   - hero cards
   - final board
   - whether this was the last hero decision in the hand.

5. Produce cluster tables:
   A. Last-decision attribution in losing hands.
   B. Every-decision attribution in losing hands.
   C. Street-only summary.
   D. Board-texture summary.
   E. Top 10 clusters by scheduled bb/100 impact.
   F. Antecedent summary: preflop opens that precede later river losses.

6. Compare Mehedi directly to Toby:
   Toby pattern:
   - river heads_up_button raise / raise_le_2/3pot
   - unpaired two-tone static / wet-flush-draw
   - river fold on paired two-tone static
   - preflop HU button open-any as antecedent, not primary kill

Verdict rules:
- SAME_TRAP:
  Mehedi top-3 last-decision clusters overlap Toby's river paired/unpaired pattern
  and explain material scheduled bb/100 loss.
- DIFFERENT_LEAK:
  Mehedi top clusters are elsewhere: preflop, turn, multiway, legalizer, latency,
  or opponent-specific non-river behavior.
- INCONCLUSIVE:
  insufficient actual hands, insufficient decision logs, malformed opponent zip,
  or wide CI that prevents localization.

Outputs:
- MEHEDI_CLUSTER_REPORT.md
- RESULTS.json
- decision_log.jsonl
- STATUS_BLOCK.md

MEHEDI_CLUSTER_REPORT.md format:
1. One-line verdict:
   SAME_TRAP / DIFFERENT_LEAK / INCONCLUSIVE

2. H2H summary table:
   scheduled hands | actual hands | scheduled bb/100 | actual bb/100 |
   95% CI | hero errors | opponent errors | p99 latency

3. Top cluster table:
   rank | attribution mode | street | position | action | board texture |
   chips | scheduled bb/100 | n hands | n decisions | notes

4. Toby comparison table:
   Toby cluster | Mehedi matching cluster | same/different | evidence

5. Ship recommendation:
   SHIP_LOCKED_ARTIFACT / HOLD / PATCH_CANDIDATE

Default recommendation:
SHIP_LOCKED_ARTIFACT unless a candidate has already cleared full gates.
Do not recommend replacing v_final.zip.
Verify protected SHAs after the run.
