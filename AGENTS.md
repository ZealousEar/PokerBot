# PokerBot — Codex Project Brief

Read this every turn. Pull deeper context from `docs/corpus-index.md`, `docs/tournament-spec.md`, `docs/api-cheatsheet.md`, and `PLAN.md` before editing strategy code.

## Mission
Win the Fullhouse Hackathon 2026 by submitting `submissions/v_final.zip` that finishes #1 by cumulative chip delta in the Swiss qualifier (2026-06-01) and #1 in the finals competition (2026-06-05; see corrected Finals FORMAT below). Prize pool £4,000+, lead sponsor Quadrature Capital.

## Finals FORMAT (updated 2026-06-04 20:00-deadline announcement — READ FIRST, overrides older finals notes)
- **Finals are a FRESH competition. Q1/Q2 standings do NOT carry.** The "#57/64 underdog / bottom of bracket" framing below is OBSOLETE — every finalist starts equal. Ignore old combined rank for strategy.
- **NOT single-elimination.** Phase 1 "The Bubble": ~40 Swiss-paired 6-max matches/bot, **800 hands** each, 6 bots/table, fresh 10k chips, ranked by **cumulative chip performance** (statistical shrinkage on the top-6 cut). Top 6 advance. Phase 2 "Final Table": top 6, up to 5000 hands/match, last bot standing wins £4,000.
- **Regime = cumulative chip EXTRACTION over a Swiss field (like the qualifier), not a single-elim variance gamble.** Our exploit-overlay aggro bot fits Phase 1 (Q2 proof: #54, +1565 chip/100, near-identical 6-max Swiss conditions); 800-hand matches give the 30-hand exploit warmup more runway. Still ship b108eff5 as-is.
- **DEADLINE EXTENDED to 20:00 UK today 2026-06-04 (= 19:00 UTC).** Whatever is on the portal at 20:00 UK plays finals.

## Finals state (updated 2026-06-04 — read before any finals work)
- **Thorp QUALIFIED for finals**: Q1 #85/289, Q2 #54/289, **combined #57/64** (HISTORICAL ONLY — finals reset to equal footing; see Finals FORMAT above).
- **The live R2 artifact is the LEAK build** (`d54640e0`, portal id `7a7ad230`) — an overnight agent autonomously uploaded it; the leak (postflop near-dead stack-off) was NOT patched in the shipped bytes.
- **FINALS BASELINE = `submissions/v_final.zip` == `v_finals_rc_patched.zip`, sha256 `b108eff5…`** (leak PATCHED). This is the bot to ship to finals, NOT the R2 build. Source is currently zip-only (not committed) — extract `consult/artifacts/2026-06-04-finals-recon/patched_src/` and commit before shipping.
- **Strategy: ship `b108eff5` as-is, freeze code, verify (incl. deferred Docker smoke), human-gated SHA-verified upload.** Do NOT hand-tune in code (exploit overlay already ships) and do NOT chase Nash de-risk. Residual leaks + verification TODO + full finalist field: `docs/investigations/finals-prep-postmortem-2026-06-04.md` and `STATUS.md [FINALS-RECON]`.
- Patch deadline was 18:00 UTC 2026-06-04.

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
- **Finals (corrected 2026-06-04 fresh Swiss/cumulative Phase 1; see Finals FORMAT above):** standings reset and cumulative chip extraction decides the Bubble cut; shrinkage makes gratuitous high variance a liability, and sharp opponents can still counter-exploit naive max-exploit play → keep a near-Nash baseline plus bounded overlay that caps downside. The older single-elim/#57-underdog/variance-as-asset rationale is obsolete (17:32 consult: `prompt-exports/2026-06-04-173203-plan-optimise-next-90min-finals-bot.md`:9,14).

The architectural answer is the **blueprint + refinement** pattern from Brown & Sandholm:

- **Blueprint** (`src/preflop_lookup.py` + `src/postflop.py`): an approximation of Nash over the abstracted game, computed offline via external-sampling MCCFR for preflop and CFR+ over flop buckets for postflop. This is the floor — even if our opponent fingerprinting fails completely, the blueprint guarantees we play near-equilibrium on the abstracted game.
- **Refinement / overlay** (`src/opponent_model.py`): live deviation from the blueprint toward best-response against the inferred opponent type. Magnitude is bounded — a large deviation is exploitable in return; the bound is set so a worst-case counter-exploit costs us less than the expected overlay gain. We replace Libratus-style real-time subgame solving (compute-prohibitive here) with this frequency-based overlay.

**Abstraction is the leverage point.** We cannot solve 6-max NLHE; we can solve a coarsened version. The two coarsenings:
- **Action abstraction** — discrete sizing tree `{1/3 pot, 2/3 pot, pot, 2× pot, all_in}` per Pluribus 2019.
- **State abstraction** — flop bucketing (≤ 200 buckets) and hand-strength bins (≤ 50 per bucket) per Cepheus 2015.

**Exploitability is the safety metric.** Local best-response (Lisý & Bowling 2017 LBR) over a fixed 20-spot suite reports how much a best-responding opponent could extract against us. Cap: ≤ 100 mbb/g preflop, ≤ 200 mbb/g aggregate. Higher = more exploit power but more counter-exploit risk; lower = closer to Nash but less exploit edge. G5 verifies this stays in the band.

**What we drop and why:**
- Real-time subgame solving (Libratus 2017) — compute-prohibitive at 0.5 CPU / 2 s decision budget.
- Deep CFR (Brown 2019) as the SHIPPED policy — calendar/validation-bound, not infrastructure-bound (corrected 2026-05-27 consult). Runtime PyTorch is still forbidden, but `.npz` + numpy inference is proven feasible (vladimir ships a 274→9 numpy MLP forward pass loading `gto_strategy.npz`). The binding constraint is the 9-day calendar — training, integration, validator/leakage/LBR/all-templates/public-bot gauntlet, and statistically proving the new policy beats the locked artifact does not fit before finals close. Allowed adjacent use: SHADOW-CFR-1 red-team / sparring opponent (`docs/plans/qualifier-finals-rollout-2026-05-27.md` Phase D), never the promoted ship artifact.
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

## Upload / submission policy (HUMAN-ONLY — hard rule, added 2026-06-03)
Never upload, submit, deploy, or push a bot live to the Fullhouse portal (`portal.fullhousehackathon`, `fullhousehackathon.com`) or any external competition endpoint without Farhad's explicit, in-the-moment approval of that specific upload. No autonomous, overnight, or background agent may submit — ever. Default to having Farhad perform the upload himself; if he delegates a specific upload, get an explicit per-upload go-ahead first. Building and fully verifying ship zips locally is encouraged — taking one live is a human-gated action. Covers qualifier, patch-window, and finals submissions. (Context: an overnight agent self-uploaded the Qualifier II patch on 2026-06-03 with no human in the loop; that must not recur.)

## Solver policy
External-sampling MCCFR (G2) and CFR+ over flop buckets (G3) are conditional on benchmark improvement against `best_green.zip`. If two consecutive non-trivial training attempts fail to improve measured bb/100 against `best_green.zip`, halt solver work and ship deterministic hand-tuned ranges + exploit priors instead. Prefer compact tables built from existing charted solver outputs over from-scratch overnight training. Treat LBR (`tools/exploit_check.py`) as a regression guard, not a Nash quality claim.

## Worktree policy
`~/Code/PokerBot/` is canonical (`main`). `~/Code/PokerBot-claude/` (`claude`) and `~/Code/PokerBot-codex/` (`codex`) are isolated worktrees forked from tag `scaffold-baseline`. Each agent edits only its own worktree. No agent edits `ext/fullhouse-engine/`, `.venv/`, another agent's worktree, or `main` during overnight runs. No agent runs `pip install` unattended.

## Benchmark variance policy
At 10k hands, bb/100 variance is ~20 bb/100 (95 % CI). Single-run 10k benchmarks are valid for monitoring progress but not for acceptance. For G3 all-templates acceptance, G5 ratchet/ablation, and branch-arbitration comparisons, either use paired seeds (`tools/benchmark.py --paired-seed-base 42 --paired-seed-count 10`) or bump `--hands` to ≥ 50000.

## Patch-window policy
Before 2026-06-02: implement `tools/analyze_hand_histories.py` that introspects schema from the first JSON record (do not hardcode field names — the hackathon schema is unknown until release) and emits compact priors to `data/finals_priors.npz`: population VPIP/PFR/aggression, fold-to-c-bet, average sizing by street, common preflop action sequences, obvious bot-cluster fingerprints.

On 2026-06-02: parse downloaded histories, update compact priors only, re-run the full validator + import + edge-case + smoke + benchmark suite. The patch-window bot must still pass every check. Keep the qualifier artifact preserved.

## Compute budget (updated 2026-05-27)
- Claude Code plan: **20×** the base subscription rate (parallel sessions, higher token allotment, longer wall-clocks per turn).
- Codex CLI plan: **20×** equivalent (parallel sandboxes, larger context budgets per lane).
- Implication for overnight queues: the 21-lane queue used ~120 k Claude orchestrator tokens + aggregated codex across 22 lanes in ~70 min of wall, with ~7.8 h of the 9 h cap unused. Future lanes can fan out wider — push toward 35–50 narrow lanes per night with shorter per-lane budgets, rather than 20 broad lanes — and we can comfortably run 2–3 overnights between now and qualifier (2026-06-01).
- Implication for finals patch window (2026-06-02): the analyzer + retune + full G1–G11 gauntlet fit inside a single 9-h window with budget to spare; we are compute-bound on architecture (no PyTorch / no C++ at submission time), not on subscription quota.
