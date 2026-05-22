# Patch Window Playbook — 2026-06-02 → 2026-06-03

24-hour patch window between qualifier and finals. Goal: tune the exploit overlay only, no baseline strategy edits.

## Hours 0–8 — Analysis

- Download JSON hand histories for our qualifier matches from the platform.
- Parse via `tools/replay.py` and compute per-opponent VPIP, PFR, AF, fold-to-c-bet on the full sample.
- Identify the 3–5 most distinctive playing styles among finalist field.

## Hours 8–16 — Tune exploit overlay

- Adjust opponent-model thresholds in `src/opponent_model.py`.
- Add 2–3 opponent-specific response tables only if a style is meaningfully different from the templates.
- **Do not touch the preflop blueprint or `src/postflop.py` flop strategy.**

## Hours 16–20 — Regression

- Re-run `tools/benchmark.py --all-templates --hands 10000`.
- If any template benchmark regresses > 2 bb/100, revert the change.
- Append regression check (with exact numbers) to STATUS.md.

## Hours 20–24 — Freeze

- Build `submissions/v_finals.zip` via `tools/package.py --strict`.
- Run `ext/fullhouse-engine/sandbox/validator.py submissions/v_finals.zip` → PASSED.
- Resubmit to platform.
- No further changes.
- Append `FINALS RESUBMITTED` to STATUS.md with the exact qualifier-vs-final benchmark delta.
