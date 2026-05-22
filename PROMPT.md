In `~/Code/PokerBot`, ship `submissions/v_final.zip` — a Fullhouse Hackathon 2026 entry that wins the 2026-06-01 Swiss qualifier and the 2026-06-05 finals bracket via a near-Nash blueprint plus a bounded opponent-frequency overlay.

Context (source of truth):
- Read `AGENTS.md` for the project brief, sandbox invariants, valid actions, and the game-theoretic frame.
- Read `PLAN.md` for the five-gate path (G1 wired → G2 preflop blueprint → G3 postflop + overlay → G4 hardening → G5 game-theoretic verification) with corpus anchors and tasks.
- Read `docs/corpus-index.md` before drawing on the literature; cite techniques at the call site with `# Source: [[note-name]]`.
- Treat `ext/fullhouse-engine/` as authoritative and read-only.

Scope:
- Edit only `src/`, `tools/`, `tests/`, `docs/`, `data/`, `submissions/`.
- Append-only to `STATUS.md`.
- Preserve every passed gate's verification-command exit code in later gates.

Constraints:
- Python 3.10; allowed libraries `eval7`, `numpy`, `scipy`, `treys`, `scikit-learn`; pass every `ext/fullhouse-engine/sandbox/validator.py` module and call-pattern check.
- Return a legal action from `decide()` on every input; load blueprints at module import (covered by the engine's 30 s warmup).
- Keep `bot.py` ≤ 5 MB, `data/` ≤ 200 MB, total package ≤ 250 MB.

Done when (every line passes simultaneously on the same `v_final.zip`):
1. `tools/benchmark.py --all-templates --hands 10000` → ≥ 15 bb/100 vs each of `template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2` (95 % CI > 0).
2. `tools/benchmark.py --ablate-overlay --hands 10000` → with-overlay beats blueprint-only by ≥ 3 bb/100.
3. `tools/benchmark.py --self-play --vs-prior` → `v_final` beats each prior gate snapshot by ≥ 3 bb/100.
4. `tools/exploit_check.py` → LBR ≤ 100 mbb/g preflop, ≤ 200 mbb/g aggregate (20-spot suite).
5. `ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip` → PASSED.
6. `pytest tests/edge_cases -x` → exit 0.
7. `tools/import_audit.py` → cold import < 1.5 s, RSS < 400 MB, every import clears the validator's module + call-pattern scan.
8. `STATUS.md` ends with `## FINAL SUBMITTED` listing G1 → G5 GREEN with verification output and a `# Source: [[note-name]]` citation per gate.

Verification (run after each change to the active gate; paste exact output into `STATUS.md`):
- G1: `python tools/self_play.py --opponent template --hands 100 --strict`
- G2: `python tools/benchmark.py --opponent template --hands 10000`
- G3: `python tools/benchmark.py --all-templates --hands 10000`
- G4: `python tools/import_audit.py && pytest tests/edge_cases -x && python tools/package.py --output submissions/v3_hardened.zip --strict`
- G5: `python tools/benchmark.py --ablate-overlay --hands 10000 && python tools/benchmark.py --self-play --vs-prior && python tools/exploit_check.py`
- Final: `python tools/package.py --output submissions/v_final.zip --strict && python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip`
- Report exact pass/fail per criterion plus residual risks (CI width, exploitability tail outside the 20-spot sample).

If blocked:
- On two consecutive non-trivial failures of the same verification, halt; append `## BLOCKED: <criterion>` to `STATUS.md` with (a) the exact failing command output, (b) the smallest next decision needed (e.g. "raise MCCFR iter 1M → 5M"), (c) numeric evidence from the failing run, (d) the rollback path to the last GREEN gate.
- On a previously GREEN criterion regressing, halt; append `## REGRESSION: <criterion> <metric>` with the same four fields.
- On wall-clock 2026-05-31 23:59 UTC, halt; package the highest-gate build that passes its verification; append `## STOPPED AT <gate>` listing GREEN and short-fall criteria.
