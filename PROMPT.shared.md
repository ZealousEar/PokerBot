Ship `submissions/v_final.zip` — a Fullhouse Hackathon 2026 entry that wins the 2026-06-01 Swiss qualifier and the 2026-06-05 finals bracket via a near-Nash blueprint plus a bounded opponent-frequency overlay. Operate inside your assigned worktree (claude or codex); read your branch-specific prompt for the search bias.

Context (source of truth):
- Read `AGENTS.md` for the project brief, sandbox invariants, valid actions, artifact / solver / worktree / benchmark-variance policies, and the game-theoretic frame.
- Read `PROMPT.{claude,codex}.md` for the role bias on your branch.
- Read `PLAN.md` for the five-gate path (G1 wired → G2 preflop blueprint → G3 postflop + overlay → G4 hardening → G5 game-theoretic verification) with corpus anchors and tasks.
- Read `docs/corpus-index.md` before drawing on the literature; cite techniques at the call site with `# Source: [[note-name]]`.
- Treat `ext/fullhouse-engine/` as authoritative and read-only.

Scope:
- Edit only `src/`, `tools/`, `tests/`, `docs/`, `data/`, `submissions/`, `.githooks/`, `findings/` within your own worktree.
- Append-only to `STATUS.md`.
- Preserve every passed gate's verification-command exit code in later gates.
- Maintain `submissions/best_green.zip` as the latest validator-passing, edge-case-passing, smoke-run-passing artifact (see `AGENTS.md` → Artifact policy). Pre-commit hook enforces.

Constraints:
- Python 3.10; allowed libraries `eval7`, `numpy`, `scipy`, `treys`, `scikit-learn`; pass every `ext/fullhouse-engine/sandbox/validator.py` module and call-pattern check.
- Return a legal action from `decide()` on every input; load blueprints at module import (covered by the engine's 30 s warmup).
- Keep `bot.py` ≤ 5 MB, `data/` ≤ 200 MB, total package ≤ 250 MB.

Done when (every line passes simultaneously on the same `v_final.zip`):
1. `tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42` → ≥ 15 bb/100 vs each of `template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2` (95 % CI > 0). Paired seeds required (see AGENTS.md → Benchmark variance policy).
2. `tools/benchmark.py --ablate-overlay --hands 10000 --paired-seed-base 42` → with-overlay beats blueprint-only by ≥ 3 bb/100.
3. `tools/benchmark.py --self-play --vs-prior --paired-seed-base 42` → `v_final` beats each prior gate snapshot by ≥ 3 bb/100.
4. `tools/exploit_check.py` → LBR ≤ 100 mbb/g preflop, ≤ 200 mbb/g aggregate (20-spot suite). Treat as regression guard, not a Nash claim.
5. `ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip` → PASSED.
6. `tools/smoke_run.py --zip submissions/v_final.zip --hands 200` → exit 0 inside real sandbox container (no bot_errors, no timeouts, ≥ 90 % hands played).
7. `pytest tests/edge_cases -x` → exit 0.
8. `tools/import_audit.py` → cold import < 1.5 s, RSS < 400 MB, every import clears the validator's module + call-pattern scan.
9. `STATUS.md` ends with `## FINAL SUBMITTED` listing G1 → G5 GREEN with verification output and a `# Source: [[note-name]]` citation per gate.

Verification (run after each change to the active gate; paste exact output into `STATUS.md` AND surface the proof-of-green block below in chat — `/goal` evaluator only reads the transcript):
- G1: `python tools/self_play.py --opponent template --hands 100 --strict`
- G2: `python tools/benchmark.py --opponent template --hands 10000`
- G3: `python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42`
- G4: `python tools/import_audit.py && pytest tests/edge_cases -x && python tools/package.py --output submissions/v3_hardened.zip --strict && python tools/smoke_run.py --zip submissions/v3_hardened.zip --hands 200`
- G5: `python tools/benchmark.py --ablate-overlay --hands 10000 --paired-seed-base 42 && python tools/benchmark.py --self-play --vs-prior --paired-seed-base 42 && python tools/exploit_check.py`
- Final: `python tools/package.py --output submissions/v_final.zip --strict && python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip && python tools/smoke_run.py --zip submissions/v_final.zip --hands 200`
- Report exact pass/fail per criterion plus residual risks (CI width, exploitability tail outside the 20-spot sample).

Proof-of-green format (compact enough to survive `/goal` context summarisation — surface in chat after every gate, also append to STATUS.md):

    [G3 GREEN 2026-05-22T03:14Z branch=claude]
    validator=PASS edge=PASS import=PASS package=PASS smoke=PASS
    bench/all template=+18.2 aggressor=+22.1 mathematician=+16.4 shark=+15.1 ref_bot_2=+14.9 (CI ±2.1, n=10000, paired-seed-base=42)
    artifact=submissions/v2_postflop.zip sha256=ab12cd34
    best_green=submissions/v2_postflop.zip (promoted from v1_blueprint)

If blocked:
- On two consecutive non-trivial failures of the same verification, halt; append `## BLOCKED: <criterion>` to `STATUS.md` with (a) the exact failing command output, (b) the smallest next decision needed (e.g. "raise MCCFR iter 1M → 5M" or "abandon solver, ship hand-tuned"), (c) numeric evidence from the failing run, (d) the rollback path to the last GREEN gate.
- On a previously GREEN criterion regressing, halt; append `## REGRESSION: <criterion> <metric>` with the same four fields. Restore `submissions/best_green.zip` if it was overwritten.
- On wall-clock 2026-05-31 23:59 UTC, halt; package the highest-gate build that passes its verification; append `## STOPPED AT <gate>` listing GREEN and short-fall criteria.

Cross-branch knowledge sharing: write notable empirical findings (reference-bot leaks, sizing inflection points, opponent fold frequencies) to `findings/<branch>-<topic>.md`. Read the other branch's findings at session start with `git log <other-branch> --oneline -- findings/`.
