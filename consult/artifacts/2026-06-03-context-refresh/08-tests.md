## 8. Test coverage and missing tests

> Scope: main worktree at branch `tooling/postflop-trap-extractor-2026-05-29` (the on-disk tree at the time of writing). Lineage tags: **SIMPLE e4b4a8f1** = shipped `submissions/v_final.zip` sha `e4b4a8f1…598` (release branch `release/v_final-e4b4a8f1`); **DEPLOYED d54640e0** = qual2 postflop-stackoff-fix ship build (`/tmp/v_ship.zip`, the X1/qual2-patch lineage). Numbers are tagged to the build that produced them.
>
> **Output-path note:** my assignment passed the literal placeholder `undefined/08-tests.md` (the orchestrator's template variable for the report directory did not render). The intended report dir is undeterminable from disk — no context-refresh manifest or sibling fragments (`0[0-9]-*.md`) exist anywhere in the repo. This fragment is written to `consult/artifacts/2026-06-03-context-refresh/08-tests.md` (project convention for forensic artifacts). Relocate as needed.

### 8.1 What this worktree actually contains (CURRENT)

`git ls-files` for this branch tracks exactly **one** edge-case test source file and **one** integration test source file. The recursive tree:

| Path | Tests | Status |
|---|---|---|
| `tests/conftest.py` | — | Puts repo root on `sys.path` (so `from src.bot import decide` resolves). 10 lines, no assertions. |
| `tests/edge_cases/test_safe_fallback.py` | **4** | Tracked in HEAD. |
| `tests/integration/__init__.py` | — | Empty package marker. |
| `tests/integration/test_analyze_postflop_trap_prevalence.py` | **4** | Tracked in HEAD. Tests a *tool*, not the bot. |
| `tests/integration/fixtures/postflop_trap_prevalence/` | — | 6 fixture files (5 JSON/JSONL + `opaque_strings.json`). |

There is **no** `tests/unit/` and **no** `tests/property/` directory on disk in this worktree, despite `CLAUDE.md` listing `tests/{unit,integration,edge_cases,property}/` as the verification surface and STATUS.md line 13 recording their creation at scaffold. (Source: `git ls-files tests/`; recursive `ls tests/`.)

#### Ghost (stale-`.pyc`-only) edge tests — direct evidence of the thin worktree

`tests/edge_cases/__pycache__/` contains compiled `.pyc` for two test modules whose **source is absent** from this branch:
- `test_hardening_cases.cpython-310-pytest-9.0.3.pyc`
- `test_legal_actions.cpython-310-pytest-9.0.3.pyc`

`git ls-files tests/edge_cases/` returns only `test_safe_fallback.py`; `git log --diff-filter=D` shows no delete commit for either ghost file. They were compiled by a pytest run that imported test modules from *another build/worktree* (the richer SIMPLE/gauntlet trees) and left cache artifacts behind. **They do not run here** — pytest only collects from source files, which are gone. (Source: `ls tests/edge_cases/__pycache__/`; `git ls-files`; `git log --diff-filter=D`.)

### 8.2 What each present test ACTUALLY asserts

**`tests/edge_cases/test_safe_fallback.py` (4 tests)** — game states copied from `ext/fullhouse-engine/sandbox/validator.py::TEST_STATES`:

| Test | Asserts | Bot under test |
|---|---|---|
| `test_safe_fallback_checks_when_possible` | `bot._safe_fallback(flop, can_check=True)` returns exactly `{"action":"check"}` | this-tree `src.bot` |
| `test_safe_fallback_folds_facing_bet` | `bot._safe_fallback(preflop, can_check=False, amount_owed=100)` returns exactly `{"action":"fold"}` | this-tree `src.bot` |
| `test_decide_handles_warmup_without_raising` | `bot.decide({"type":"warmup"})` returns a `dict` with an `"action"` key (does not assert *which* action) | this-tree `src.bot` |
| `test_decide_returns_legal_action_on_garbage` | For `[{}, preflop, flop, {"random_garbage":True}, None, 42, []]`, `decide(...)` returns a dict whose `action ∈ {fold,check,call,raise,all_in}`; if `raise`, an `"amount"` key is present | this-tree `src.bot` |

Coverage character: this file verifies the **never-crash / always-legal contract** only. It does NOT assert strategic correctness, raise amount legality (only key *presence*), `min_raise_to` snapping, all-in vs raise distinction, or any street-specific decision. The garbage test exercises the *exception path* of `decide`, not its strategy.

**`tests/integration/test_analyze_postflop_trap_prevalence.py` (4 tests)** — exercises the **tool** `tools/analyze_postflop_trap_prevalence.py` against 6 synthetic fixtures; **zero** of these touch `src.bot` / `decide()`:

| Test | Asserts (abridged) |
|---|---|
| `..._counts_required_synthetic_families` | `total_records_found==6`, `records_successfully_parsed==6`, `postflop_action_records>=8`, `river_action_records>=5`; specific cluster keys present (`river__button__raise__…`, `river__big_blind__fold__…`); river can_check raise freqs (`unpaired_two_tone_static.raise>=2`, `wet_flush_draw.raise==1`); facing-bet fold/call freqs; three named Toby/Mehedi fingerprint counts |
| `..._reports_chip_impact_and_nonfinite_rejections` | `chip_impact_available is True`; a cluster appears in `top_clusters_by_chip_impact`; `nonfinite_amounts_rejected==1`; `"ROUNDS"` in detected top-level schema keys |
| `..._handles_opaque_string_fixture_without_crashing` | On `opaque_strings.json`: all counts 0, `top_clusters_by_frequency==[]` (no crash on unparseable input) |
| `..._text_report_contains_required_summary_fields` | Rendered text report contains `"Total records found: 6"`, `"Postflop action records parsed:"`, `"River can_check raise frequency"`, `"Toby/Mehedi-like fingerprints"` |

This is patch-window *extractor* coverage (schema-introspection, frequency tallying, non-finite rejection, opaque-input robustness) — valuable for the analyzer pipeline, but it is **not bot-behaviour coverage**.

### 8.3 DISCREPANCY — STATUS cites far richer edge suites from OTHER builds

STATUS.md records edge-test counts that **do not exist in this worktree's tree**. Tagged by lineage:

| STATUS line | Reported | Build / lineage | Present here? |
|---|---|---|---|
| 23, 44, 119, 157 | `edge_cases 4 passed` | scaffold / this-tree contract | **Yes (4)** — matches CURRENT |
| 244, 249, 328 | `edge_cases 25/25` | **SIMPLE e4b4a8f1** (`release/v_final-e4b4a8f1`, G11 / gauntlet reproduction) | **No** |
| 339, 342 | `55/55 edge_cases (52 existing + 3 new priors-consumer)`; adds `tests/edge_cases/test_priors_consumer.py (+92/-0)` | PokerBot-gauntlet release-branch build (priors-consumer) | **No** — `test_priors_consumer.py` absent |
| 631, 642 | `edge_cases 48/48` | **DEPLOYED d54640e0** ship build `/tmp/v_ship.zip` (qual2 postflop-stackoff fix) | **No** |

So STATUS reports **three** different edge counts (25, 48, 55) from three different artifact lineages; this worktree carries the original **4**-test scaffold contract plus a 4-test tool integration suite. The richer suites (`test_hardening_cases`, `test_legal_actions`, `test_priors_consumer`, and whatever brought 25→48→55) live on the SIMPLE/DEPLOYED/gauntlet branches and were never merged into `tooling/postflop-trap-extractor-2026-05-29`. The only fossil of them here is the two stray `.pyc` files in 8.1. **This worktree's bot-behaviour test surface is thin and stale relative to what shipped.** (Sources cited inline; counts harvested from STATUS.md.)

> Caveat: the 25/48/55 suite *contents* are not on disk in this tree, so the per-test assertions of those richer suites cannot be inspected here — only their pass-counts are harvestable from STATUS.md. The missing-test matrix below is judged against what is **provably present in this worktree**, and notes where STATUS evidence suggests another build already covers a row.

### 8.4 Relevant `tools/` (one line each)

All under `tools/`; first line of each module docstring (Source: docstring head of each file). Most invoke the real engine and/or Docker — out of scope to run here.

| Tool | One-line purpose |
|---|---|
| `self_play.py` | Runs N hands of our bot vs a named opponent via `match.py`; reports crashes, illegal actions, timeouts. |
| `benchmark.py` | bb/100 vs reference opponents (G2/G3) or GT verification suites (G5) with bootstrap 95% CIs. (Docstring also self-describes as a historical gate stub — see `public_saturation` note.) |
| `exploit_check.py` | Local best-response (LBR, Lisý & Bowling 2017) exploitability estimate over a fixed 20-spot suite; regression guard (caps 100/200 mbb/g). |
| `import_audit.py` | Verifies cold-start time, RSS, and absence of forbidden imports across **every** `.py` in `src/` (validator only AST-scans `bot.py`). |
| `package.py` | Builds the submission zip (root `bot.py` shim re-exporting `decide`) and validates structure. |
| `smoke_run.py` | Exercises a submission inside the real engine **sandbox container** vs a reference bot for a few hands; catches timeout/OOM/missing-data/slow-import the AST validator cannot. |
| `replay.py` | Replays a hand-history JSON through `src.bot.decide` for reproducible diagnosis (patch-window). |
| `h2h.py` | Paired-seed head-to-head between two bot artifacts (seats swapped); reports A's per-match BB delta + bootstrap CI. |
| `field_recon.py` | Investigation-only: reconstructs hand state from public portal histories in `data/portal_histories/`. |
| `audit_strategy_leakage.py` | Scans packaged strategy source for identity-leakage strings (opponent labels, artifact/branch names, seed-like values). |
| `analyze_postflop_trap_prevalence.py` | Patch-window postflop-trap extractor; schema-introspects JSON/JSONL histories, emits field-level Toby/Mehedi signals (tooling only). |
| `preflop_sizing_audit.py` | Investigation-only: checks whether PREFLOP/SIZING code shares the "threshold-to-stackoff" bug fixed in qual2-patch. |
| `b8_gauntlet.py` | Single-command gauntlet for candidate zips; orchestrates existing verification tools as subprocesses, emits STATUS-style block. |
| `public_saturation.py` | Public-bot saturation sweeps for artifact-bound H2H evidence; drives the engine directly (notes `benchmark.py` is "still a historical gate stub in this tree"). |
| `qualifier_pods.py` | Estimates 400-hand qualifier chip-delta distributions for six-max pods via the sandbox match runner. |
| `train_flop.py` | Offline flop bucket + strategy generation → `data/flop_buckets.npz` (training, unrestricted compute). |
| `train_preflop.py` | Offline preflop blueprint generation → `data/preflop_blueprint.npz` (`numpy.savez_compressed`). |

`field_recon` appears twice in the assignment list; it is a single tool, listed once above.

### 8.5 MISSING-TEST MATRIX (ranked by tournament risk)

Risk = consequence × likelihood at the 2 s/decision, fold-on-exception sandbox where an illegal/late action is silently converted to a fold (chips lost). "Covered here" = provably exercised by a test in *this* worktree. "STATUS-elsewhere" = a richer SIMPLE/DEPLOYED/gauntlet build plausibly covers it but the source is not in this tree (see 8.3 caveat).

| # | Capability under test | Risk | Covered in THIS worktree? | Justification |
|---|---|---|---|---|
| 1 | Raise below `min_raise_to` / above stack / **equal-to-call** ambiguity (legal amount, snap-up, all-in vs raise-to-stack) | **High** | **No** (garbage test asserts only that an `"amount"` key *exists*, never its legality vs `min_raise_to`/stack) | An illegal `amount` → runner converts to fold → direct chip loss every occurrence. Validator's `VALID_ACTIONS` checks shape, not numeric legality. STATUS-elsewhere: likely `test_legal_actions` (ghost `.pyc`). |
| 2 | Malformed / partial `game_state` (missing keys, wrong types, truncated dict) beyond the 7 garbage inputs already tried | **High** | **Partial** — `test_decide_returns_legal_action_on_garbage` covers `{}`, `None`, `42`, `[]`, `{"random_garbage":True}` | Real sandbox feeds engine-shaped dicts with occasional missing fields; the 5 garbage inputs are coarse. Missing: dicts with *some* required keys absent (e.g. `your_stack` missing, `community_cards` malformed). |
| 3 | All-in & **side-pot** states (multiple all-ins, capped pots, uneven stacks) | **High** | **No** | Side-pot math errors mis-size raises → illegal action or value leak; common in 400-hand qualifier pods with short stacks. No fixture or decide-test exercises a side-pot state. |
| 4 | Timeout under expensive equity call (decision > 2 s when equity/Monte-Carlo path is hit) | **High** | **No** | A single >2 s decision = forced fold. `timeout_guard.py` exists (per `CLAUDE.md` map) but **no test asserts the guard fires** or that worst-case equity stays under budget. smoke_run catches it only at runtime in Docker (not run here). |
| 5 | Warmup exception (`{"type":"warmup"}` raising, or blueprint load failing) | **Med** | **Yes (partial)** — `test_decide_handles_warmup_without_raising` asserts a dict-with-`action` is returned | Covered for the no-raise contract only; does NOT assert blueprints actually loaded, nor that a *broken* warmup payload is survived. Warmup has a 30 s budget so timeout risk is low; correctness-of-load is untested. |
| 6 | Missing / empty / contradictory legal actions (`can_check` False with `amount_owed` 0; check requested when illegal) | **Med** | **Partial** — `_safe_fallback` check-vs-fold branch tested for two consistent states | No test for *contradictory* inputs (e.g. `can_check:True` but `current_bet>0`). `_safe_fallback` is the right place; only the happy path is asserted. |
| 7 | River bluff-catcher thresholds (call/fold at marginal showdown equity) | **Med** | **No** | Strategic-strength row; mis-set threshold bleeds EV but never crashes → lower ops risk, real chip-EV risk. The trap-extractor fixtures describe river fold/call *populations*, but assert the **tool**, not `decide`. |
| 8 | Wet-board equity realization (draw-heavy flop/turn equity vs made hands) | **Med** | **No** | EV/correctness, not legality. Fixture taxonomy includes `wet_flush_draw`, but only as extractor input — `equity.py` realization is untested against `decide`. |
| 9 | Multiway pots (3+ live players; range/equity adjustments vs heads-up) | **Med** | **No** | Qualifier is 6-max; multiway is the common case. A `sixmax_multiway_anonymous.json` fixture exists but feeds the *extractor* test, not bot decisions. STATUS line 631 notes HU-tuning artifacts ("game is 6-max"), underscoring the gap. |
| 10 | Package structure & forbidden imports (root `bot.py` only, no `.py` in `data/`, no forbidden modules, size caps) | **Med** | **No (unit)** — enforced operationally by `tools/package.py --strict`, `import_audit.py`, the engine `validator.py`, and the `.githooks/pre-commit` hook, but **no pytest test** asserts it | Catastrophic if it regresses (whole submission rejected), but multiple non-pytest guards already cover it, so residual risk is Med not High. Not in the `pytest tests/edge_cases` surface. |
| 11 | Blind-defense & 3-bet-pot pressure (BB defend freq, 4-bet/jam thresholds) | **Med/Low** | **No** | Strategic EV row; fingerprint `mehedi_preflop_pressure_early_bust_like` is extractor-only. No `decide` test for preflop pressure spots. |
| 12 | Deterministic seed reproducibility (same seed → identical action stream) | **Low** | **No** | Harness/QA property, not a sandbox-scored path. `h2h.py`/`benchmark.py` rely on paired seeds; a regression here corrupts *measurement*, not the shipped bot. No test pins it. |
| 13 | Bootstrap CI correctness (the CI math in `benchmark.py`/`h2h.py`) | **Low** | **No** | Affects trust in acceptance numbers, not bot legality/EV. Per benchmark-variance policy the CIs gate decisions; an off-by math bug would mislead, but it is meta-tooling. No test covers the estimator. |

#### Cross-reference summary (already-covered vs genuinely missing, this worktree)

- **Already (partly) covered here:** warmup-no-raise (#5), garbage/malformed-input legality contract (#2, partial), `_safe_fallback` check-vs-fold for *consistent* states (#6, partial). All via `test_safe_fallback.py`.
- **Genuinely missing here, High risk:** raise-amount numeric legality / equal-to-call (#1), side-pot/all-in states (#3), equity-call timeout-guard (#4). These are the legality/ops failures that the fold-on-exception runner converts straight into chip loss and are the priority gaps.
- **Genuinely missing here, Med risk (EV/strategy or guarded-elsewhere):** contradictory legal-action inputs (#6 full), river bluff-catcher (#7), wet-board realization (#8), multiway (#9), package/forbidden-imports as pytest (#10, but operationally guarded), blind-defense/3-bet pressure (#11).
- **Genuinely missing here, Low risk (meta-tooling):** seed reproducibility (#12), bootstrap-CI correctness (#13).
- **Provably covered by another build, not here:** legal-action legality (#1) and input hardening (#2) map to the ghost `test_legal_actions.py` / `test_hardening_cases.py` and the priors-consumer suite that STATUS records as 25/48/55 — but their source is absent from this tree (8.3 caveat), so the assertions cannot be verified here.

**Bottom line:** the shipped artifacts (SIMPLE e4b4a8f1, DEPLOYED d54640e0) were verified against 25-/48-/55-test edge suites per STATUS, but `tooling/postflop-trap-extractor-2026-05-29` carries only the 4-test never-crash contract plus a 4-test extractor integration suite. The richest, highest-risk legality coverage (rows #1, #3, #4) is not reproducible in this worktree.
