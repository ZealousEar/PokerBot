## 4. Current implementation map

**Scope:** `/Users/farhad/Code/PokerBot` (main worktree) ONLY. All file hashes below are sha256 truncated to 8 hex chars, computed live from disk this session.

### 4.0 Lineage verdict (READ FIRST) — current-main `src/` is the SCAFFOLD-BASELINE, not the shipped strategy

The presupposition that this worktree's `src/postflop.py` is "the SIMPLE or the ELABORATE build" is **false**. Verified evidence: every strategy module in current-main `src/` is an unimplemented stub from tag `scaffold-baseline`. The shipped bots (both SIMPLE `e4b4a8f1` and DEPLOYED `d54640e0`) were packaged from a *different* tree (the elaborate build), not from current-main `src/`.

Hard proof — `src/bot.py` sha256 = **`f38cbb67`**, which is byte-identical to the STATUS A3 drift hash:

> STATUS.md L615 (`2026-06-01T05:02:37Z · A3 ship-day`): "drift: packaged shim `b405d542…`, packaged `src/bot.py` `d33484ed…`, current-main `src/bot.py` `f38cbb67…` (differs — confirms do NOT repackage from main)"

Lineage table (from STATUS.md, in-scope main only):

| Bot | sha256 (8) | What it is | Source tree |
|---|---|---|---|
| SIMPLE | `e4b4a8f1` | `submissions/v_final.zip` == `best_green.zip`; Qualifier-I artifact | elaborate build (packaged `src/bot.py`=`d33484ed`), NOT current-main |
| DEPLOYED Qual-II | `d54640e0` | `best_green.zip` + postflop `_can_commit` fix only; uploaded 2026-06-03 | elaborate build + postflop fix; "exact bytes unverifiable (source not exposed)" (STATUS L633) |
| current-main `src/` | `bot.py`=`f38cbb67` | scaffold-baseline stubs (this worktree) | tag `scaffold-baseline` |

STATUS.md L633 states the inconsistency explicitly: "submissions/v_final.zip (sha e4b4a8f1) is the SIMPLE bot and does NOT match deployed behavior — records/artifact lineage are inconsistent across worktrees." The Qual-II `_can_commit` fix (STATUS L628–629) was applied to the **elaborate** `src/postflop.py` ("Root cause in elaborate src/postflop.py 'facing a bet'"), which does NOT exist in current-main — current-main `src/postflop.py` is the 25-line stub below.

**Implication:** Nothing in current-main `src/` is the running tournament strategy. To inspect deployed behavior, read the elaborate build (e.g. PokerBot-claude base `2733566` per `consult/artifacts/.../V2_PLAN.md` L7 — out of THIS scope) or unzip the deployed artifact. This section documents the scaffold that is physically present on main.

### 4.1 Import graph from `bot.py` (runtime)

Traced from `src/bot.py`. At runtime, `decide()` imports **nothing from `src/`** — the strategy wiring is commented out (L23–26):

```
# from src.preflop_lookup import lookup as _preflop_lookup
# from src.postflop import decide_postflop as _decide_postflop
# from src.timeout_guard import run_with_budget
```

So the live import graph is just: `bot.py → {os, sys}` (stdlib only). The other 7 modules (`postflop`, `preflop_lookup`, `equity`, `opponent_model`, `sizing`, `ranges`, `timeout_guard`, `__init__`) are present on disk but **not imported by the running code path**. `numpy`/`eval7` are referenced only in docstrings/TODOs; no module actually imports them yet.

Line counts: bot 48, timeout_guard 37, opponent_model 28, postflop 25, preflop_lookup 24, sizing 22, equity 11, ranges 7, `__init__` 0 (202 total).

### 4.2 File-by-file

#### `src/bot.py` (`f38cbb67`, 48 lines)
- **Purpose:** Engine entry; exports `decide(game_state) -> dict`. Shipped archive root has a shim that re-exports this.
- **Public API:** `decide(game_state: dict) -> dict` (L36); helper `_safe_fallback(game_state) -> dict` (L29). Sets `DATA_DIR` from `BOT_DATA_DIR` env or `../data` (L18–21).
- **Behavior:** warmup → `{"action":"check"}` (L41–42); else returns `_safe_fallback` (check if `can_check` else fold), wrapped in try/except → fold (L43–48). **This is a pure fold/check fallback bot — no strategy is wired.**
- **Runtime deps:** `os`, `sys` only (stdlib).
- **Data files loaded:** none (commented-out wiring; computes `DATA_DIR` but never reads it).
- **Failure modes:** none material — every path returns a legal action; non-dict input → fold; exceptions caught → fold. The risk is *strategic* (it folds/checks everything), not crash.
- **TODO/FIXME:** L23–26 commented wiring ("Codex wires these during G2/G3").
- forbidden-import scan: CLEAN

#### `src/postflop.py` (`37fcf9bb`, 25 lines)
- **Purpose (intended):** Postflop strategy — flop bucket lookup + turn/river heuristic. `# Source: [[PokerBot/Cepheus/Bowling-2015]]`.
- **Public API:** `decide_postflop(game_state: dict) -> dict` (L21).
- **Behavior:** **stub** — `check` if `can_check` else `fold` (L23–25). Module globals `_flop_buckets=None`, `_flop_strategy=None` (L17–18) — never loaded.
- **Runtime deps:** `os`, `pathlib.Path` only. (numpy intended, not imported.)
- **Data files loaded:** **none.** Intended to load `flop_buckets.npz` + `flop_strategy.npz` (both present on disk: 582 B and 17029 B) but the load is a TODO.
- **LINEAGE:** This is the **SCAFFOLD stub**, NOT the SIMPLE-bot postflop and NOT the ELABORATE build. The deployed Qual-II `_can_commit` board-aware commit gate (flush→nut/eq≥0.92, paired→≥0.80, safe→≥0.55; STATUS L629) lives in the *elaborate* `src/postflop.py` that is **absent from this worktree**. No `_can_commit`, no `current_bet*3` escalation, no `board_texture`/`_flush_suit` here — confirmed by the 25-line body.
- **Failure modes:** strategically inert (folds when it can't check). `game_state.get("can_check")` assumes dict input — would `AttributeError` on non-dict, but only ever called by wired code (none).
- **TODO/FIXME:** L16 "load flop_buckets.npz and flop_strategy.npz at import"; L22 "Placeholder — Codex implements during G3".
- forbidden-import scan: CLEAN

#### `src/preflop_lookup.py` (`2d6505fb`, 24 lines)
- **Purpose (intended):** Preflop blueprint lookup from `data/preflop_blueprint.npz`. `# Source: [[PokerBot/Pluribus/Brown-Sandholm-2019]]`.
- **Public API:** `lookup(position: str, hand: tuple, action_seq: tuple)` (L21).
- **Behavior:** **stub** — returns `None` (L24). `_blueprint=None` (L18); resolves `_BLUEPRINT_PATH = _DATA_DIR/"preflop_blueprint.npz"` (L15) but never opens it.
- **Runtime deps:** `os`, `pathlib.Path`. (numpy intended.)
- **Data files loaded:** **none.** Intended: `preflop_blueprint.npz` (present, 2147 B) — load is a TODO.
- **Failure modes:** none (always returns None → caller would fall through to blueprint-less play).
- **TODO/FIXME:** L17 "load blueprint eagerly here"; L23 "implement".
- forbidden-import scan: CLEAN

#### `src/equity.py` (`900f6cc5`, 11 lines)
- **Purpose (intended):** Monte-Carlo equity-vs-range using eval7, ≤5 ms/call, pre-warm LUTs at import.
- **Public API:** `equity_vs_range(hero, board, villain_range, trials=2000) -> float` (L9).
- **Behavior:** **stub** — `raise NotImplementedError("G3")` (L11).
- **Runtime deps:** none imported. eval7 intended (L6 TODO) but **not imported** — so no eval7 dependency is live anywhere in `src/`.
- **Data files loaded:** none.
- **Failure modes:** any call **raises** `NotImplementedError`. Safe only because nothing calls it (not wired into `bot.py`); if wired naively it would crash → engine fold.
- **TODO/FIXME:** L6 "import eval7, pre-warm LUTs"; L11 NotImplementedError.
- forbidden-import scan: CLEAN

#### `src/opponent_model.py` (`744ac64d`, 28 lines)
- **Purpose (intended):** Per-seat frequency tracker (VPIP/PFR/AF/FoldToCBet), exploit after 30-hand warmup. `# Source: [[PokerBot/OpponentModeling/Billings-Davidson-Schauenberg]]`.
- **Public API:** class `OpponentModel` (L11) with `__init__` (L14), `observe_hand(hand_event: dict)` (L18), `is_warm_for(seat_id) -> bool` (L22), `features(seat_id) -> dict` (L25). Module const `WARMUP_HANDS=30` (L8).
- **Behavior:** **stub** — only increments `self._hands_seen`; `features()` returns `{}` (L28); `is_warm_for` compares a *global* hand count, not per-seat (TODO).
- **Runtime deps:** none (pure Python).
- **Data files loaded:** none.
- **Failure modes:** none crash; `features()` returning `{}` means any consumer must handle empty dict.
- **TODO/FIXME:** L15 "per-seat dict of counters"; L27 "implement".
- forbidden-import scan: CLEAN

#### `src/sizing.py` (`0edb3f3d`, 22 lines)
- **Purpose:** Bet-sizing tree → chip amount. Discrete sizings per Pluribus action abstraction.
- **Public API:** `sizing_to_amount(sizing: str, pot: int, stack: int) -> int` (L10). Const `SIZINGS = ("third_pot","two_third_pot","pot","two_x_pot","all_in")` (L7).
- **Behavior:** **IMPLEMENTED** (the only non-stub strategy helper). Maps tag→`min(fraction·pot, stack)`; unknown tag → `raise ValueError` (L22).
- **Runtime deps:** none (pure Python).
- **Data files loaded:** none.
- **Failure modes:** `ValueError` on unknown sizing tag (defensive; caller must pass a valid tag). Integer floor division — `pot//3` truncates; for `pot<3` returns 0-chip "raise", which an engine would snap to `min_raise_to` or treat as invalid → fold. Not wired into `bot.py`, so no live exposure.
- **TODO/FIXME:** none.
- forbidden-import scan: CLEAN

#### `src/ranges.py` (`0d6da014`, 7 lines)
- **Purpose (intended):** Preflop ranges by position × stack depth → `frozenset[str]` of canonical hands.
- **Public API:** module dict `RANGES: dict = {}` (L7).
- **Behavior:** **empty** — `RANGES = {}`.
- **Runtime deps:** none.
- **Data files loaded:** none.
- **Failure modes:** none; any lookup yields KeyError/empty unless caller guards.
- **TODO/FIXME:** L6 "populate from a respected source".
- forbidden-import scan: CLEAN

#### `src/timeout_guard.py` (`bc2d818c`, 37 lines)
- **Purpose:** Advisory wall-clock budget tracker. Note (L1–7): the engine enforces the hard 2 s via its own daemon thread (`ext/fullhouse-engine/sandbox/runner.py::_call_with_timeout`); bot code cannot use `threading` (FORBIDDEN). This module only lets the pipeline check remaining budget and short-circuit.
- **Public API:** `@contextmanager deadline(seconds=SOFT_DEADLINE_S)` yielding `remaining()` (L18–22); `run_with_budget(decision_fn, fallback_fn, game_state, budget_s=SOFT) -> dict` (L25). Consts `SOFT_DEADLINE_S=1.20`, `HARD_FALLBACK_S=1.80` (L14–15).
- **Behavior:** **IMPLEMENTED.** `run_with_budget` runs `decision_fn`; if over budget OR exception → `fallback_fn` (L31–37). Uses `time.monotonic()`.
- **Runtime deps:** `time`, `contextlib.contextmanager`, `typing.Callable` (all stdlib).
- **Data files loaded:** none.
- **Failure modes:** **post-hoc only** — it checks elapsed *after* `decision_fn` returns (L33), so a `decision_fn` that hangs past 2 s is NOT interrupted by this guard (only the engine's daemon thread can). `HARD_FALLBACK_S` is defined but unused. Advisory, as documented. Not wired into `bot.py`.
- **TODO/FIXME:** none.
- forbidden-import scan: CLEAN — note this module *names* `threading` in a docstring (L4) explaining why bot code must NOT use it; no `import threading`.

#### `src/__init__.py` (`e3b0c442`, 0 lines)
- **Purpose:** Package marker. Empty (hash `e3b0c442…` is the sha256 of empty content).
- **Public API / deps / data / failures / TODO:** none.
- forbidden-import scan: CLEAN

### 4.3 Cross-reference: ground-truth `data/*.npz` vs loaders

| npz file | size (B) | mtime | Loaded by | Status |
|---|---|---|---|---|
| `preflop_blueprint.npz` | 2147 | May 22 04:26 | `preflop_lookup.py` (intended) | present, **never loaded** (TODO L17) |
| `flop_buckets.npz` | 582 | May 22 04:43 | `postflop.py` (intended) | present, **never loaded** (TODO L16) |
| `flop_strategy.npz` | 17029 | May 22 04:43 | `postflop.py` (intended) | present, **never loaded** (TODO L16) |

Assignment named `flop_strategy.npz`; on disk it is `flop_strategy.npz` (matches). `data/portal_histories/` also present (not a runtime npz; finals/recon input). No `data/finals_priors.npz` on disk yet (patch-window deliverable per CLAUDE.md).

### 4.4 Forbidden-module / sandbox-risk scan — whole `src/` tree

Live grep of `src/` for FORBIDDEN_MODULES (`socket`, `urllib*`, `requests`, `http`, `subprocess`, `multiprocessing`, `pickle`, `shelve`, `threading`, `ctypes`, `importlib`, `runpy`, `ftplib`, `smtplib`) and forbidden call patterns (`eval(`, `exec(`, `__import__(`, `compile(`, `os.system/popen/exec*/spawn*/fork/kill/remove/rename`): **0 matches** ("NONE FOUND"). Only `threading` appears as a *prose mention* in `timeout_guard.py` L4 documenting the prohibition; not an import.

**Tree-wide verdict — forbidden-import scan: CLEAN.** Caveat: this clears the *scaffold* on current-main only; it does NOT clear the deployed elaborate build (`d54640e0`), whose source is not in this worktree and is "unverifiable (source not exposed)" per STATUS.md L633. The authoritative validator gate for the shipped artifact is `ext/fullhouse-engine/sandbox/validator.py` run against the zip, logged GREEN for the SIMPLE artifact at STATUS A3 (L602–623) and for the Qual-II ship build at STATUS QUAL2-PATCH (L631, "validator 4/4 PASS").
