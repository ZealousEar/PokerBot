## P5 Patch-Window Postflop-Trap Prevalence Extractor — GREEN

- Branch: `tooling/postflop-trap-extractor-2026-05-29`
- Scope: tooling-only extractor plus integration fixtures/tests.
- Protected artifacts: `submissions/v_final.zip` and `submissions/best_green.zip` remained at `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Test: `.venv/bin/python -m pytest tests/integration -x` -> `4 passed in 0.26s`.
- Synthetic run: `records_successfully_parsed=6`, `postflop_action_records=10`, `river_action_records=5`.
- Output files: `RESULTS.json`, `example_report.txt`, `POSTFLOP_EXTRACTOR_REPORT.md`, `STATUS_BLOCK.md`, `DIFF.patch`.
- B9/B10: extractor informs B10 manual review only; it makes no strategy or artifact changes.
