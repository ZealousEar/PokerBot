# P5 Patch-Window Postflop Trap Extractor Report

## Scope

Tooling-only patch-window readiness. No runtime strategy files, `data/finals_priors.npz`, `submissions/`, `ext/fullhouse-engine/`, or `ext/public-bots/` were edited.

New tool:

```bash
.venv/bin/python tools/analyze_postflop_trap_prevalence.py --input <history-file-or-dir>
```

It reads JSON, JSONL, deep wrappers, nested street containers, abbreviated streets (`pf/f/t/r`), mixed casing, `amountBB` fields, and rejects non-finite amount values from numeric sizing.

## Real 2026-06-02 Command

Run this after downloading and extracting qualifier histories:

```bash
cd /Users/farhad/Code/PokerBot
.venv/bin/python tools/analyze_postflop_trap_prevalence.py \
  --input data/qualifier_histories_2026-06-02/ \
  --json-out consult/artifacts/2026-05-29-away/patch-window-postflop-extractor/real_2026-06-02_RESULTS.json \
  --report consult/artifacts/2026-05-29-away/patch-window-postflop-extractor/real_2026-06-02_report.txt \
  --top-n 50
```

This command does not write strategy priors and does not package a bot.

## Synthetic Fixture Result

Command run:

```bash
.venv/bin/python tools/analyze_postflop_trap_prevalence.py \
  --input tests/integration/fixtures/postflop_trap_prevalence \
  --json-out consult/artifacts/2026-05-29-away/patch-window-postflop-extractor/RESULTS.json \
  --report consult/artifacts/2026-05-29-away/patch-window-postflop-extractor/example_report.txt \
  --top-n 20
```

Observed:

| metric | value |
| --- | ---: |
| total records found | 6 |
| records successfully parsed | 6 |
| postflop action records parsed | 10 |
| river action records parsed | 5 |
| non-finite amounts rejected | 1 |

Synthetic trap signals:

| signal | result |
| --- | ---: |
| river can_check raise on unpaired two-tone static | 2 / 2 |
| river can_check raise on wet flush-draw | 1 / 1 |
| river facing-bet fold on paired two-tone static | 1 / 1 |
| river facing-bet call on unpaired two-tone static | 1 / 1 |
| Toby-like unpaired river raise fingerprint | 2 |
| Toby-like paired river fold fingerprint | 1 |
| Mehedi-like preflop-pressure early-bust fingerprint | 1 |

## Sanity Thresholds

- Proceed with manual review only if `records_successfully_parsed > 0`.
- Proceed with postflop prevalence review only if `postflop_action_records > 0`.
- Treat river-specific conclusions as inconclusive if `river_action_records < 50`; use `50-199` only as directional evidence and prefer `>= 200` before ranking cluster prevalence.
- Fallback to the default/no-postflop-candidate path if the schema is opaque: zero successful parses, zero postflop actions, or parse failures dominated by missing/unknown action fields.

## B9 / B10 Interaction

- This extractor informs B10 manual review.
- It does not itself change strategy.
- It may justify opening a postflop candidate only if real 2026-06-02 histories show material prevalence in the required river clusters and fingerprints.
- If real histories are sparse or opaque, the correct result is inconclusive and the locked qualifier artifact remains the default.

## Verification

Protected artifact SHA before and after the run:

```text
e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598  submissions/v_final.zip
e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598  submissions/best_green.zip
```

Tests:

```text
.venv/bin/python -m pytest tests/integration -x
4 passed in 0.26s
```
