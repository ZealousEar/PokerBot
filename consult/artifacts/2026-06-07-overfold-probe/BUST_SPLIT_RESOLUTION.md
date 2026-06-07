# BUST_SPLIT_RESOLUTION — Workstream F

Scope: forward remediation only. No strategy code, `docs/`, `AGENTS.md`, submissions, uploads, `git add`, or `git commit`.

## Command run

```bash
.venv/bin/python tools/recompute_thorp_bust_split.py \
  --raw-dir consult/artifacts/2026-06-04-finals-recon/raw/hands \
  --json-out consult/artifacts/2026-06-07-overfold-probe/bust_split_recomputed.json
```

Script/data citations:
- Clean-match filter: `tools/recompute_thorp_bust_split.py:44-57`.
- Per-action street reconstruction from stripped `action_log`: `tools/recompute_thorp_bust_split.py:89-172`.
- Last non-blind Thorp chip-commitment classifier: `tools/recompute_thorp_bust_split.py:178-211`.
- Aggregate counters/output: `tools/recompute_thorp_bust_split.py:214-298` and `consult/artifacts/2026-06-07-overfold-probe/bust_split_recomputed.json:790-871`.

## VERIFIED — raw replay recomputation

Input/methodology matched the source-data hygiene envelope in `thorp_leak_report.md:5-11`: Thorp bot id `7a7ad230-2b19-46ff-af11-5df254b6f078`; bust is `final_stack == 0`; clean means 6 seats plus unique Thorp seat; aggregated multi-table rows are excluded.

Recomputed hygiene counts:
- Raw match JSON files scanned: **1,919** (`bust_split_recomputed.json:862`).
- Thorp match files: **40** (`bust_split_recomputed.json:870`).
- Clean Thorp matches: **36** (`bust_split_recomputed.json:791`).
- Thorp bust seat-entries: **22 total**, with **2 excluded non-clean** (`bust_split_recomputed.json:793,871`).
- Clean busts classified: **20** (`bust_split_recomputed.json:790`).
- Forced-blind tails after the last non-blind commitment: **4** (`bust_split_recomputed.json:2`). These are tracked separately so forced blind-offs do not masquerade as strategic committing streets.

Committing-street split from raw `action_log` rows, using the last non-blind Thorp chip commitment (`call`/`raise`/`all_in`):

| Street bucket | Count | % of 20 clean busts |
|---|---:|---:|
| Preflop | **5** | **25%** |
| Postflop | **15** | **75%** |
| -- flop | 6 | |
| -- turn | 4 | |
| -- river | 5 | |

This **confirms** `thorp_leak_report.md:24-35`'s headline **5 preflop / 15 postflop (25% / 75%)** claim. The recomputed postflop sub-breakdown differs by one street from the report table (this run: flop 6 / turn 4 / river 5; report: flop 5 / turn 5 / river 5), but the decisive preflop-vs-postflop split is reproduced exactly.

Important method boundary: `VERIFICATION_REPORT.md:27-30` independently notes that method choice moves this count; it got **4 / 16** under a biggest-stack-destroying-loss method and warned that naive last-chip readings can understate postflop when short stacks blind off. This recomputation therefore records forced-blind tails separately and uses the last non-blind chip commitment as the committing street. The robust source-data conclusion is **postflop-majority, not preflop-dominated**.

## INFERRED — contradiction resolution

The apparent contradiction is not a true same-sample contradiction. The qualifier replay figure is real-replay evidence for Thorp’s **leak-build** busting profile over clean qualifier matches (`n=20` clean busts). The FINALS-EXEC-RIVER-TRIAGE entry is a different artifact: patched `b108eff5`, synthetic 6-max Lane A data, a **9-hand river-resolved subset**, compact summaries only, and its own limitation says boards/cards/pots were not recoverable (`STATUS.md:892-900`). Therefore:

- Use this recomputation / `thorp_leak_report.md` for: **qualifier real-replay busting distribution** of the leak build. It is postflop-majority; exact recomputed preflop-vs-postflop split is **5/15**, matching the report headline; the prior verification report's alternate biggest-loss method gives 4/16.
- Use RIVER-TRIAGE only for: **patched build synthetic-subset triage** showing no repeated river-decision overcommit (`STATUS.md:895-900`). It is not evidence that qualifier Thorp busts were preflop-dominated.

This resolves only the **busting failure-mode** accounting. It is separate from the over-folding-bleed root cause. Resolving this split does **not** refute or change the over-folding root cause; it only removes the logged confusion between qualifier replay busts and the patched synthetic river-triage subset.
