# PokerBot — Codex Project Brief

Read this every turn. Pull deeper context from `docs/corpus-index.md`, `docs/tournament-spec.md`, `docs/api-cheatsheet.md`, and `PLAN.md` before editing strategy code.

## Mission
Win the Fullhouse Hackathon 2026 by submitting `submissions/v_final.zip` that finishes #1 by cumulative chip delta in the Swiss qualifier (2026-06-01) and #1 in the finals bracket (2026-06-05). Prize pool £4,000+, lead sponsor Quadrature Capital.

## Repository map
- `src/bot.py` — entry implementation. The shipped `bot.zip` has a small `bot.py` shim at archive root that re-exports `decide` from here.
- `src/preflop_lookup.py`, `src/postflop.py`, `src/equity.py`, `src/opponent_model.py`, `src/ranges.py`, `src/sizing.py`, `src/timeout_guard.py` — strategy modules.
- `data/*.npz` — precomputed blueprints; load eagerly at module import (covered by the engine's 30 s warmup budget).
- `tools/` — training, benchmarking, packaging, import auditing.
- `tests/{unit,integration,edge_cases,property}/` — verification surface.
- `ext/fullhouse-engine/` — local engine clone for testing; **do not modify**.

## Build & verify commands
- Self-play: `python tools/self_play.py --opponent <name> --hands <N>`
- Benchmark vs all templates: `python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42`
- Import audit: `python tools/import_audit.py`
- Build submission: `python tools/package.py --output submissions/<name>.zip --strict`
- Engine validator (authoritative, AST + size only): `python ext/fullhouse-engine/sandbox/validator.py submissions/<name>.zip`
- Sandbox smoke run (runs the bot in a real container): `python tools/smoke_run.py --zip submissions/<name>.zip --hands 200`
- Edge cases: `pytest tests/edge_cases -x`

## Sandbox invariants (HARD — sourced from `ext/fullhouse-engine/sandbox/{validator.py,Dockerfile,runner.py}`)
- Runtime: **Python 3.10**. eval7 0.1.7 does not build on 3.11+ (uses pre-generated C against pre-3.11 `longintrepr.h`).
- Pinned libraries: `eval7==0.1.7`, `numpy==1.26.4`, `scipy==1.13.0`, `treys==0.1.8`, `scikit-learn==1.5.2`.
- Container flags: `--network none --memory 768m --cpus 0.5 --read-only --no-new-privileges --user 1000:1000`.
- 2 s per `decide()`. One warmup call (`type=="warmup"`) before hand 1 with 30 s budget — load blueprints there.
- File reads from `data/` only at import time via `os.environ["BOT_DATA_DIR"]` (engine sets it; fall back to `os.path.dirname(__file__)/data`).
- Submission size: `bot.py` ≤ 5 MB, `data/` ≤ 200 MB, total ≤ 250 MB. `bot.py` at archive root; no other `.py` at root; no `.py` inside `data/`; no symlinks; no path traversal.

## Forbidden modules (validator `FORBIDDEN_MODULES`)
`socket`, `urllib`, `urllib2`, `urllib3`, `requests`, `httpx`, `aiohttp`, `http`, `ftplib`, `smtplib`, `telnetlib`, `xmlrpc`, `subprocess`, `multiprocessing`, `pickle`, `shelve`, `threading`, `ctypes`, `runpy`, `importlib`.

## Forbidden call patterns (validator AST scan)
`__import__(`, `eval(`, `exec(`, `compile(`, `getattr(__builtins__`, `__builtins__[…]`, `globals()[`, `locals()[`, any `subprocess.*`, any `os.{system,popen,exec*,spawn*,fork,kill,remove,unlink,rmdir,removedirs,chmod,chown,replace,rename}`.

## Valid actions (validator `VALID_ACTIONS`)
- `{"action": "fold"}`
- `{"action": "check"}`  — only when `can_check` is True
- `{"action": "call"}`
- `{"action": "raise", "amount": N}`  — `amount` is the **total** chips put in, not the increment; below `min_raise_to` is snapped up
- `{"action": "all_in"}`  — distinct from raise-to-stack

Invalid actions default to fold; the runner emits `{"action": "fold", "error": ...}` on exception or timeout.

## Game-theoretic frame (the architectural commitment)

Two-regime tournament dictates a two-layer strategy.

- **Qualifier (Swiss, 400-hand matches vs mostly weak field):** maximum chip extraction wins → bias toward best-response against the inferred opponent type.
- **Finals (single-elim bracket of top 64):** survivors include sharp opponents who will counter-exploit naive max-exploit play → need a near-Nash baseline that bounds our downside.

The architectural answer is the **blueprint + refinement** pattern from Brown & Sandholm:

- **Blueprint** (`src/preflop_lookup.py` + `src/postflop.py`): an approximation of Nash over the abstracted game, computed offline via external-sampling MCCFR for preflop and CFR+ over flop buckets for postflop. This is the floor — even if our opponent fingerprinting fails completely, the blueprint guarantees we play near-equilibrium on the abstracted game.
- **Refinement / overlay** (`src/opponent_model.py`): live deviation from the blueprint toward best-response against the inferred opponent type. Magnitude is bounded — a large deviation is exploitable in return; the bound is set so a worst-case counter-exploit costs us less than the expected overlay gain. We replace Libratus-style real-time subgame solving (compute-prohibitive here) with this frequency-based overlay.

**Abstraction is the leverage point.** We cannot solve 6-max NLHE; we can solve a coarsened version. The two coarsenings:
- **Action abstraction** — discrete sizing tree `{1/3 pot, 2/3 pot, pot, 2× pot, all_in}` per Pluribus 2019.
- **State abstraction** — flop bucketing (≤ 200 buckets) and hand-strength bins (≤ 50 per bucket) per Cepheus 2015.

**Exploitability is the safety metric.** Local best-response (Lisý & Bowling 2017 LBR) over a fixed 20-spot suite reports how much a best-responding opponent could extract against us. Cap: ≤ 100 mbb/g preflop, ≤ 200 mbb/g aggregate. Higher = more exploit power but more counter-exploit risk; lower = closer to Nash but less exploit edge. G5 verifies this stays in the band.

**What we drop and why:**
- Real-time subgame solving (Libratus 2017) — compute-prohibitive at 0.5 CPU / 2 s decision budget.
- Deep CFR (Brown 2019) — no PyTorch/TF in the allowed library set.
- Nested endgame solving — same compute reasons.

## Engineering conventions
- Decide first, refine second: every code path returns a legal action; correctness before strategic strength.
- Anchor architectural decisions in `docs/corpus-index.md` references.
- Add a `# Source: [[note-name]]` comment when implementing a technique from the corpus.
- Tests are mandatory at each gate; no merge without numeric verification logged to `STATUS.md`.
- Every gate's STATUS.md entry names which corpus note drove its design choice.

## Status protocol
Append a timestamped section to `STATUS.md` at every gate, with: gate id, GREEN/AMBER/RED, exact benchmark numbers, files changed, next action. Also surface the compact proof-of-green block (see `PROMPT.shared.md`) in the chat transcript — `/goal` evaluator only reads the transcript and auto-summarisation can erase STATUS.md evidence.

## Artifact policy
Always preserve `submissions/best_green.zip` — the latest validator-passing, edge-case-passing, smoke-run-passing artifact. After each gate, if the new build clears every check, promote it: `cp submissions/<new>.zip submissions/best_green.zip` (and commit). A `.githooks/pre-commit` hook refuses commits to `submissions/` that break verification; activate per-clone with `git config core.hooksPath .githooks`. Override with `FORCE_COMMIT=1 git commit ...` only for explicit rollbacks.

Preserve all gate snapshots (`submissions/v{0..3}_*.zip`) — `tools/benchmark.py --self-play --vs-prior` depends on them.

## Solver policy
External-sampling MCCFR (G2) and CFR+ over flop buckets (G3) are conditional on benchmark improvement against `best_green.zip`. If two consecutive non-trivial training attempts fail to improve measured bb/100 against `best_green.zip`, halt solver work and ship deterministic hand-tuned ranges + exploit priors instead. Prefer compact tables built from existing charted solver outputs over from-scratch overnight training. Treat LBR (`tools/exploit_check.py`) as a regression guard, not a Nash quality claim.

## Worktree policy
`~/Code/PokerBot/` is canonical (`main`). `~/Code/PokerBot-claude/` (`claude`) and `~/Code/PokerBot-codex/` (`codex`) are isolated worktrees forked from tag `scaffold-baseline`. Each agent edits only its own worktree. No agent edits `ext/fullhouse-engine/`, `.venv/`, another agent's worktree, or `main` during overnight runs. No agent runs `pip install` unattended.

## Benchmark variance policy
At 10k hands, bb/100 variance is ~20 bb/100 (95 % CI). Single-run 10k benchmarks are valid for monitoring progress but not for acceptance. For G3 all-templates acceptance, G5 ratchet/ablation, and branch-arbitration comparisons, either use paired seeds (`tools/benchmark.py --paired-seed-base 42 --paired-seed-count 10`) or bump `--hands` to ≥ 50000.

## Patch-window policy
Before 2026-06-02: implement `tools/analyze_hand_histories.py` that introspects schema from the first JSON record (do not hardcode field names — the hackathon schema is unknown until release) and emits compact priors to `data/finals_priors.npz`: population VPIP/PFR/aggression, fold-to-c-bet, average sizing by street, common preflop action sequences, obvious bot-cluster fingerprints.

On 2026-06-02: parse downloaded histories, update compact priors only, re-run the full validator + import + edge-case + smoke + benchmark suite. The patch-window bot must still pass every check. Keep the qualifier artifact preserved.
