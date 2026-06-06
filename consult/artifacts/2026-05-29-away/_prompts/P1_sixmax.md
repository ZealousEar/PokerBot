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

Task: P1 Six-max trap-prevalence stress test, no strategy edits.

Use the global Hard Invariant above.

Goal:
Estimate whether Toby `master` and Mehedi `mybot` RED H2H results translate into dangerous six-max qualifier pods for the locked artifact.

Context:
- Qualifier format: six-bot tables, 400 hands per match, cumulative chip delta, top 64 advance.
- Toby master is RED heads-up.
- Mehedi mybot is RED heads-up.
- H2H evidence alone may overstate or understate six-max risk because trap bots occupy only some villain seats.
- Existing QUAL-PODS RED was previously reconciled as high six-max variance rather than functional failure; this lane specifically tests new trap-bot prevalence.

Output directory:
consult/artifacts/2026-05-29-away/trap-sixmax-prevalence/

Inputs:
- submissions/v_final.zip
- Temporary opponent zips from public drift audit:
  Toby master, Mehedi mybot, Pav skantbot7.9, Pav skantbot7.6,
  stoppedtime24 mybot, famadeo codex_holdem, neel, vladimir if usable,
  engine reference bots.

If missing, build temporary zips under:
consult/artifacts/2026-05-29-away/trap-sixmax-prevalence/opponent_zips/

Do not write into ext/public-bots or submissions.

Run compositions:
C0_BASELINE_RECHECK:
  hero, template, aggressor, mathematician, shark, ref_bot_2

C1_SINGLE_TOBY_WEAK_FIELD:
  hero, toby_master, template, mathematician, shark, ref_bot_2

C2_SINGLE_MEHEDI_WEAK_FIELD:
  hero, mehedi_mybot, template, mathematician, shark, ref_bot_2

C3_TOBY_MEHEDI_WEAK_FIELD:
  hero, toby_master, mehedi_mybot, template, shark, ref_bot_2

C4_PUBLIC_NIGHTMARE:
  hero, toby_master, mehedi_mybot, famadeo, neel, pav_skantbot7_9

C5_TRAP_HEAVY:
  hero, toby_master, mehedi_mybot, stoppedtime24_mybot, pav_skantbot7_9, shark

C6_DOMINIC_RENAME_COMPARISON:
  hero, toby_master, old_dominic_if_available, famadeo, neel, shark

C7_TWO_TOBY_CLONES:
  hero, toby_master_clone1, toby_master_clone2, template, shark, ref_bot_2
  Only run this if duplicate packaging is legal in local simulation.
  If not legal, skip and report SKIPPED_DUPLICATE_NOT_SUPPORTED.

Run protocol:
- Use artifact-bound sandbox/match.py or an existing qualifier_pods-style runner.
- 400 scheduled hands per match.
- At least 100 seeds per composition if feasible.
- Record scheduled chip delta and actual hands separately.
- Record:
  p10, p25, p50, p75, p90, mean, stdev, bust rate,
  hero error rate, opponent error rate, p99 decide latency.
- Record per-seat chip deltas if the engine exposes them.
- Record early-bust causes if inferable.

Decision bands:
- GREEN: p50 > 0 and p10 > -5000
- AMBER: p50 > 0 but p10 <= -5000
- RED: p50 <= 0
- CRITICAL: p50 <= -5000 or bust rate >= 60%

Outputs:
- TRAP_SIXMAX_REPORT.md
- RESULTS.json
- matches.jsonl
- STATUS_BLOCK.md

TRAP_SIXMAX_REPORT.md must include:
1. One-line verdict:
   TRAP_PREVALENCE_SAFE / TRAP_PREVALENCE_AMBER / TRAP_PREVALENCE_DANGEROUS

2. Composition table:
   composition | seats | color | p10 | p50 | p90 | mean |
   stdev | bust rate | hero errors | p99 ms

3. Comparison:
   - Does one Toby seat alone flip the pod?
   - Does one Mehedi seat alone flip the pod?
   - Do Toby+Mehedi together flip the pod?
   - Is the danger driven by early busts or accumulated chip bleed?

4. Upload recommendation:
   SHIP_LOCKED_ARTIFACT unless there is already a fully-gated replacement.
   Never overwrite v_final.zip.
Verify protected SHAs after the run.
