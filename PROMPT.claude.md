# PROMPT.claude.md — Claude branch search bias

You operate in `~/Code/PokerBot-claude` on branch `claude`. Read `AGENTS.md`, `PROMPT.shared.md`, and `PLAN.md` first. The contract and acceptance criteria live there; this file is the search bias only.

Differentiator: Codex covers solver/table work and parameter sweeps. You cover the harness, hardening, exploit overlay, and tournament tooling. Both branches still ship a complete bot — the bias just decides where your time goes first.

Priority order in this branch:
P0  Legal action on every input. Fix `src/bot.py` and `src/timeout_guard.py` fallback paths first. Until P0 is green, nothing else matters.
P1  Verification harness. Make `tools/{self_play,benchmark,package,import_audit,smoke_run,exploit_check}.py` real and reliable. Benchmark must support paired seeds (`AGENTS.md` → Benchmark variance policy).
P2  Robust practical strategy in `src/`. Position-aware preflop ranges in `src/ranges.py`, legal sizing in `src/sizing.py`, postflop equity + board-texture heuristics in `src/postflop.py` and `src/equity.py`.
P3  Reference-bot exploit priors in `src/opponent_model.py`. Seed from `ext/fullhouse-engine/bots/{template,aggressor,mathematician,shark,ref_bot_2}/` behavior; record findings in `findings/claude-refbot-leaks.md`.
P4  Bounded opponent-frequency overlay after 30-hand warmup; cap deviation magnitude per `AGENTS.md` artifact policy.
P5  Patch-window readiness: `tools/analyze_hand_histories.py` introspects schema from the first JSON record (do not hardcode field names — the 2026-06-02 schema is unknown).

Solver policy (mirrors AGENTS.md): consume existing charted solver outputs into compact `data/*.npz` tables before training MCCFR/CFR+ from scratch. If two non-trivial training attempts fail to improve `best_green.zip`, fall back to hand-tuned ranges and exploit heuristics.

Required behaviour:
- Append exact command outputs to `STATUS.md`.
- Surface the proof-of-green block from `PROMPT.shared.md` in chat after every gate — `/goal` evaluator only reads the transcript.
- Preserve all green artifacts. Pre-commit hook enforces; do not set `FORCE_COMMIT=1` unless explicitly rolling back.
- On two failed non-trivial attempts at the same criterion, append `## BLOCKED: <criterion>` with evidence and rollback path.
- On regression, append `## REGRESSION: <criterion> <metric>` and restore the last green artifact.

Done when `submissions/v_final.zip` clears every check in `PROMPT.shared.md` → "Done when", and STATUS.md ends in `## FINAL SUBMITTED`, `## BLOCKED`, or `## STOPPED AT <gate>` with exact failing output and numeric evidence.

Important: if solver work threatens safety, package size, import time, or benchmark reliability, abandon solver work and ship the strongest verified heuristic + exploit bot.
