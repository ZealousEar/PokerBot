# Lane B closeout — NO_BB_FIX (2026-05-30)

**Verdict: NO_BB_FIX.** The Mehedi-class heads-up big-blind defense leak (preflop BB fold −9.13,
BB all_in −6.74) resists a clean fix.

## Why
- The damaging cluster is concentrated in Mehedi's 2.5x/3x button-open pressure spots, not the
  trivial min-open spots.
- Any BB-defense band wide enough to alter those pressure spots changed early stack trajectories
  badly (structural: more marginal OOP flops / altered jam frequencies → predictable stack bleed),
  which regresses the broader field rather than only helping Mehedi.
- The only *safe* band (true HU min-open prices only) shows ~exact-zero delta vs Mehedi — it covers
  the required unit behavior but does not touch the leak. So there is no clean, non-regressing band
  that materially fixes Mehedi.
- Iteration was bounded (2 mechanism-justified rebuilds) per the orchestration plan; conclusion is a
  legitimate negative, and the default (ship locked) already covers Mehedi.

## Status / provenance
- The Codex session **crashed (agent_error) before writing its formal REPORT.md**; this note is the
  human-authored closeout. Partial artifacts present in this directory:
  `laneB_eval.py`, `mehedi_b142.json`, `mehedi_pilot3_b142.json`, `v_mehedi_bb_defense_laneB.zip`,
  `candidate_zip_sha256.txt`, `command_logs/`.
- Protected artifacts verified UNCHANGED after the crash: `v_final.zip` and `best_green.zip` both
  remain sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- No orphaned benchmark processes left running.

## Consequence
No Mehedi component to merge → the dual candidate collapses to Toby-only (Lane A's
`v_postflop_trap_v2_p2_already_clean.zip`). Mehedi stays unaddressed for the qualifier; locked
`v_final.zip` remains the upload target unless the Toby-only candidate earns promotion on the
six-max pod metric.
