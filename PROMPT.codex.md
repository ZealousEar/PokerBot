# PROMPT.codex.md — Codex branch search bias

You operate in `~/Code/PokerBot-codex` on branch `codex`. Read `AGENTS.md`, `PROMPT.shared.md`, and `PLAN.md` first. The contract and acceptance criteria live there; this file is the search bias only.

Differentiator: Claude covers harness, hardening, and exploit overlay. You cover compact lookup tables, parameter sweeps, training pipelines, and benchmark automation. Both branches still ship a complete bot — the bias decides where your time goes first.

Priority order in this branch:
P0  Bot is legal on every engine state (shared baseline; do not regress). Until P0 is green, nothing else matters.
P1  Solid deterministic baseline so the bot is benchmarkable: position-aware preflop ranges, legal sizing, postflop equity thresholds, safe fallback.
P2  Compact lookup tables in `data/*.npz`. Prefer consuming existing charted solver outputs over training MCCFR/CFR+ from scratch (see solver policy below).
P3  Parameter sweeps against reference bots in `ext/fullhouse-engine/bots/`. Tune: preflop open/3bet/call thresholds, aggression multipliers, c-bet and fold-to-c-bet, value/bluff thresholds, sizing tags, overlay caps. Use paired seeds (`AGENTS.md` → Benchmark variance policy); report bb/100 ± CI.
P4  Improve `tools/exploit_check.py` (LBR) as a regression guard — not a Nash claim. ≤ 100 mbb/g preflop, ≤ 200 mbb/g aggregate over the 20-spot suite.
P5  Maintain `submissions/best_green.zip` after every verified improvement. Pre-commit hook enforces.

Solver policy: External-sampling MCCFR (G2) and CFR+ over flop buckets (G3) are allowed, but conditional on benchmark improvement against `best_green.zip`. If two consecutive non-trivial training attempts fail to improve measured bb/100, halt solver work and ship deterministic hand-tuned ranges plus exploit priors. Prefer compact tables from existing charted solver outputs over from-scratch overnight training.

Acceptance rule for any table or parameter change:
- validator PASS,
- edge-case PASS,
- import-audit PASS,
- smoke-run PASS,
- bench/all not worse on any opponent,
- improves at least one meaningful target or reduces risk,
- fits package size limits and import-time budget.

Required behaviour:
- Append exact command outputs to `STATUS.md`.
- Surface the proof-of-green block from `PROMPT.shared.md` in chat after every gate — `/goal` evaluator only reads the transcript.
- Write empirical findings (sweep results, opponent leaks, sizing inflection points) to `findings/codex-<topic>.md` so the claude branch can see them via `git log codex --oneline -- findings/`.
- On two failed non-trivial attempts at the same criterion, append `## BLOCKED: <criterion>` with evidence and rollback path.
- On regression, append `## REGRESSION: <criterion> <metric>` and restore the last green artifact.

Done when `submissions/v_final.zip` clears every check in `PROMPT.shared.md` → "Done when", and STATUS.md ends in `## FINAL SUBMITTED`, `## BLOCKED`, or `## STOPPED AT <gate>` with exact failing output and numeric evidence.
