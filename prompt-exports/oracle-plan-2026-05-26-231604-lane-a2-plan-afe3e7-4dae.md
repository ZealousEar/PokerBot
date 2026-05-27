## Final Prompt
<taskname="Lane A2 Plan"/>
<task>
Design Lane A-2: a diagnostic-first polish pass for `submissions/v_w3_candidate.zip` (sha256 `d78a4c6b...`) before any promotion to `v_final.zip`. The requested output is an actionable plan only, not implementation. It must cover instrumentation, diagnostic procedure, implementation plan if the diagnostic confirms the hypothesis, hardening, per-seat measurement, risk register, and a scoreboard scaffold for `prompt-exports/optimize-lane-a2-runs.md`.

Hard constraints from the user:
- Worktree is `/Users/farhad/Code/PokerBot-codex/` on branch `codex-x1-repair`.
- Do not touch `/Users/farhad/Code/PokerBot/` except invoking its validator path.
- Do not overwrite `submissions/v_final.zip` (rollback floor sha256 `e4b4a8f1...`). Build any new artifact under a new name first.
- W3 diff is uncommitted; treat worktree files, not HEAD, as the current candidate baseline.
- No source identity-string shortcuts. Existing test `test_archetype_posterior.py` rejects tokens such as bundled refs, `neel`, branch/snapshot/final artifact names in `src/opponent_model.py`.
</task>

<architecture>
- `src/opponent_model.py` builds a table-level, behavior-only archetype posterior from non-hero public action logs. Key constants: `MIN_ARCHETYPE_OBSERVATIONS`, `FULL_CONFIDENCE_OBSERVATIONS`, `MAX_DEVIATION_BOUND_PP = 4.0`. Current `deviation_bound` is `MAX_DEVIATION_BOUND_PP * sample_confidence`, where sample confidence comes from action count only. `top_probability` is computed and exposed but does not currently damp the bound.
- `src/bot.py` imports `OpponentModel`, queries `archetype_features()` in `_pressure_preflop_overlay()`, computes `_posterior_preflop_deviation(features)`, and applies bounded open/continue shifts around blueprint preflop decisions. Existing overlay gate returns blueprint if `deviation_bound_pp <= 0.0` or `abs(open_shift_pp)+abs(continue_shift_pp) < 0.75`.
- `tools/benchmark.py` defines the six-max measurement surface. It writes JSON with `results.{composition}.{seat_key}.bb_per_100`, `.ci_95`, `.crashes`, `.timeouts`, `.illegal_actions`. Seat keys are `seat_1:<opponent>` through `seat_5:<opponent>` and `seat_6:artifact`; the manifest headline composition values are under `seat_6:artifact`, not `__aggregate__`.
- `tools/package.py`, external validator, `tools/import_audit.py`, `tools/exploit_check.py`, `tools/audit_strategy_leakage.py`, and `tests/edge_cases` define the acceptance/hardening checks.
- W3 verification evidence lives in `consults/2026-05-26-r1-baseline/MANIFEST.md` plus the two selected W3 JSON result files for seed bases 42 and 142.
</architecture>

<selected_context>
PokerBot-codex/AGENTS.md: project rules, validator/import constraints, worktree policy, benchmark variance policy, artifact preservation rules.
PokerBot-codex/src/bot.py: current W3 overlay implementation; `_pressure_preflop_overlay()`, `_posterior_preflop_deviation()`, overlay gate, shift weights.
PokerBot-codex/src/opponent_model.py: current W3 posterior implementation; action-rate calibration, sample-count confidence, `top_probability`, `deviation_bound`, debug string.
PokerBot-codex/src/postflop.py and dependencies (`equity.py`, `preflop_lookup.py`, `ranges.py`, `sizing.py`, `timeout_guard.py`): imported by `bot.py`; included so implementation impact and packaging/import behavior can be reasoned about.
PokerBot-codex/tests/edge_cases/: full edge suite, including posterior identity audit and overlay-bounded tests; use local conventions when proposing new tests.
PokerBot-codex/tests/integration/test_six_max_benchmark.py: benchmark harness expectations.
PokerBot-codex/tools/benchmark.py: exact six-max composition definitions, seed schedule, output JSON schema, seat-key generation.
PokerBot-codex/tools/package.py: strict zip build behavior.
PokerBot-codex/tools/exploit_check.py: LBR regression guard; W3 aggregate baseline is 4387.4 mbb/g.
PokerBot-codex/tools/import_audit.py: forbidden imports/calls and cold-import measurement.
PokerBot-codex/tools/audit_strategy_leakage.py: artifact leakage audit.
PokerBot-codex/consults/2026-05-26-r1-baseline/MANIFEST.md: R1 baseline, W3 candidate verification, residual risks, reproducibility commands.
PokerBot-codex/consults/2026-05-26-r1-baseline/w3_candidate/six_max_mix_20260526T203154Z.json: W3 seed-base 42 output.
PokerBot-codex/consults/2026-05-26-r1-baseline/w3_candidate/holdout_142/six_max_mix_20260526T203230Z.json: W3 seed-base 142 output.
_git_data/.../diff/per-file/*.patch: focused uncommitted W3 patches for `src/bot.py`, `src/opponent_model.py`, `src/postflop.py`, selected tests, `tools/benchmark.py`, `tools/exploit_check.py`, `tools/audit_strategy_leakage.py`, and the manifest. `all.patch` is intentionally not selected because it is too large and mostly generated/log content.
</selected_context>

<relationships>
- `decide()` -> `_decide_core()` -> `_decide_preflop()` -> blueprint lookup -> `_pressure_preflop_overlay()` -> `OpponentModel.archetype_features()` -> `_posterior_preflop_deviation()` -> possible legal overlay action.
- `OpponentModel.archetype_features()` returns `archetype_posterior`, sample-count `confidence` only inside `posterior_debug`, `top_probability`, and `deviation_bound`. The proposed peak-confidence factor must multiply the existing sample-count confidence, not replace it.
- Six-max benchmark lineups in `tools/benchmark.py` place the artifact at `seat_6:artifact` for the manifest headline composition score. Per-opponent rows use the displaced opponent seat, e.g. C2 Neel is `results.C2["seat_1:neel"]`.
- Edge tests patch `bot._OPPONENT_MODEL` with fake features and call private helpers directly; use that pattern for any planned test of diffuse posterior damping/gating.
</relationships>

<required_design_decisions>
Your plan must explicitly resolve these, not leave them open:
1. Diagnostic first: add instrumentation in a new test/debug helper file, not production source. Use an env-var gate such as `POKERBOT_DEBUG_POSTERIOR=1`. Dump per-decision `top_probability`, sample-count confidence, `deviation_bound`, shifts, composition/seed/seat/hand metadata if available, and enough posterior info to classify diffuse vs confidently-wrong behavior. Run exactly one 400-hand C1 seed-42 match and one 400-hand C2 seed-42 match before designing damping.
2. Diagnostic interpretation: if C1 seed-42 is often `top_probability < 0.6` while C2 seed-42 is often `top_probability >= 0.6`, the diffuse hypothesis holds and the plan may proceed. If both are high, surface that the posterior is confidently wrong and stop for human review rather than tuning diffusion.
3. Redundancy between damping and gate: choose one coherent mechanism. Either rely on multiplicative damping plus the existing 0.75pp shift gate, or choose a non-overlapping hard bail zone plus damping ramp. Do not propose a threshold combination that makes a smooth zone dead code.
4. Multiplicative composition: final bound formula must be `MAX_DEVIATION_BOUND_PP * sample_confidence * peak_confidence_factor`. Do not swap out sample-count confidence.
5. Acceptance reporting must include per-seat and composition numbers with exact JSON paths.
6. Iteration cap: one polish pass; if iteration 1 hits acceptance, stop. If one of four strategic gates misses narrowly, iteration 2 is allowed. If iteration 2 misses, stop and surface to human.
</required_design_decisions>

<acceptance_gates>
All must hold before any promotion:
- C2 seed-base 42 and 142 `seat_6:artifact.ci_95[0] > 0`.
- Neel-in-C2 seed 42 `results.C2["seat_1:neel"].bb_per_100 >= 0`; also report seed 142 from the same path.
- C1 seed 42 `results.C1["seat_6:artifact"].bb_per_100 >= 15`.
- Zero crashes, zero timeouts, zero illegal actions across all 480 matches per seed-base. Sum or inspect all `results.C*.seat_*.{crashes,timeouts,illegal_actions}`; at minimum report `seat_6:artifact` and composition checks.
- `python -m pytest tests/edge_cases -x` remains 47/47 plus any new tests.
- Package strict, validator, import audit, strategy leakage audit pass.
- LBR aggregate from `tools/exploit_check.py --bot submissions/<new>.zip` is not worse than W3 candidate aggregate 4387.4 mbb/g.
</acceptance_gates>

<json_paths>
Use these exact paths for scoreboard extraction from each seed-base JSON:
- C1 composition headline: `results.C1["seat_6:artifact"].bb_per_100`, `.ci_95[0]`, `.ci_95[1]`.
- C2 composition headline: `results.C2["seat_6:artifact"].bb_per_100`, `.ci_95[0]`, `.ci_95[1]`.
- Neel-in-C2: `results.C2["seat_1:neel"].bb_per_100`, `.ci_95[0]`, `.ci_95[1]`.
- Failure counts: `results.C1..C4[*].crashes`, `.timeouts`, `.illegal_actions`; report totals per seed-base and call out any non-zero `bot_errors`.
- W3 seed 42 anchors: C1 `-1.50 [-19.76, +16.83]`; C2 `+62.79 [+18.30, +113.05]`; Neel-in-C2 `-16.94 [-38.18, +6.26]`; failures `0/0/0`.
- W3 seed 142 anchors: C1 `+20.43 [+0.23, +37.42]`; C2 `+25.68 [+6.17, +46.08]`; Neel-in-C2 `+21.04 [+0.55, +43.21]`; failures `0/0/0`.
</json_paths>

<commands>
Use these commands in the plan, with `<new>` replaced by a non-final artifact name such as `v_lane_a2_candidate.zip`:
```bash
cd /Users/farhad/Code/PokerBot-codex

# Diagnostic one-match scope before damping design
POKERBOT_DEBUG_POSTERIOR=1 .venv/bin/python tools/benchmark.py --six-max-mix --bot submissions/v_w3_candidate.zip --paired-seed-base 42 --paired-seed-count 1 --hands 400 --out-dir consults/2026-05-26-r1-baseline/lane_a2_debug/c1_c2_probe/
# The plan should explain how the debug helper restricts/extracts C1 and C2, or how to filter output to those two compositions without changing production code.

# Build and hardening checks
.venv/bin/python tools/package.py --output submissions/<new>.zip --strict
.venv/bin/python /Users/farhad/Code/PokerBot/ext/fullhouse-engine/sandbox/validator.py submissions/<new>.zip
.venv/bin/python tools/import_audit.py
.venv/bin/python -m pytest tests/edge_cases -x
.venv/bin/python tools/audit_strategy_leakage.py --zip submissions/<new>.zip
.venv/bin/python tools/exploit_check.py --bot submissions/<new>.zip

# Acceptance measurement
.venv/bin/python tools/benchmark.py --six-max-mix --bot submissions/<new>.zip --paired-seed-base 42 --paired-seed-count 10 --hands 400 --out-dir consults/2026-05-26-r1-baseline/lane_a2_candidate/
.venv/bin/python tools/benchmark.py --six-max-mix --bot submissions/<new>.zip --paired-seed-base 142 --paired-seed-count 10 --hands 400 --out-dir consults/2026-05-26-r1-baseline/lane_a2_candidate/holdout_142/
```
</commands>

<scoreboard_scaffold>
The requested plan must include contents for `prompt-exports/optimize-lane-a2-runs.md`. Prepopulate the W3 row and leave a Lane A-2 row template. Suggested columns:
`artifact`, `sha256`, `iteration`, `diagnostic verdict`, `C1 s42 seat_6 bb/100 [CI]`, `C1 s142 seat_6 bb/100 [CI]`, `C2 s42 seat_6 bb/100 [CI]`, `C2 s142 seat_6 bb/100 [CI]`, `Neel C2 s42 bb/100 [CI]`, `Neel C2 s142 bb/100 [CI]`, `failures s42/s142`, `edge tests`, `validator`, `import audit`, `LBR aggregate mbb/g`, `decision`.

Prepopulated W3 row values:
- artifact `submissions/v_w3_candidate.zip`, sha256 `d78a4c6be8269ea5340cc867f8986b6521978d5a96a79cc2322adbd30f2f8570`, iteration `W3 baseline`, diagnostic `not instrumented`, C1 s42 `-1.50 [-19.76, +16.83]`, C1 s142 `+20.43 [+0.23, +37.42]`, C2 s42 `+62.79 [+18.30, +113.05]`, C2 s142 `+25.68 [+6.17, +46.08]`, Neel C2 s42 `-16.94 [-38.18, +6.26]`, Neel C2 s142 `+21.04 [+0.55, +43.21]`, failures `0/0/0 both`, edge tests `47/47`, validator `PASS`, import audit `PASS 0.105s RSS 38.4MB`, LBR `4387.4`, decision `needs Lane A-2`.
</scoreboard_scaffold>

<ambiguities>
- The user asks for a plan, not code changes. The next model should output the plan and scaffold content, not implement unless explicitly redirected.
- The diagnostic helper file name is not fixed by the repo. The plan should choose a concrete new debug/test helper path and justify why it stays outside production packaged source.
- Exact debug log schema is open, but it must be machine-readable JSON and gated by `POKERBOT_DEBUG_POSTERIOR=1` or an equivalent explicit env var.
</ambiguities>

## Selection
- Files: 37 total (37 full)
- Total tokens: 101830 (Auto view)
- Token breakdown: full 101830

### Files
### Selected Files
/Users/farhad/Code/PokerBot-codex/
├── consults/
│   └── 2026-05-26-r1-baseline/
│       ├── w3_candidate/
│       │   ├── holdout_142/
│       │   │   └── six_max_mix_20260526T203230Z.json — 5,973 tokens (full)
│       │   └── six_max_mix_20260526T203154Z.json — 5,815 tokens (full)
│       └── MANIFEST.md — 7,828 tokens (full)
├── src/
│   ├── __init__.py — 0 tokens (full)
│   ├── bot.py — 2,751 tokens (full)
│   ├── equity.py — 620 tokens (full)
│   ├── opponent_model.py — 2,144 tokens (full)
│   ├── postflop.py — 2,935 tokens (full)
│   ├── preflop_lookup.py — 557 tokens (full)
│   ├── ranges.py — 529 tokens (full)
│   ├── sizing.py — 413 tokens (full)
│   └── timeout_guard.py — 376 tokens (full)
├── tests/
│   ├── edge_cases/
│   │   ├── test_archetype_posterior.py — 984 tokens (full)
│   │   ├── test_equity_wiring.py — 711 tokens (full)
│   │   ├── test_hardening_cases.py — 736 tokens (full)
│   │   ├── test_lbr_exploit.py — 422 tokens (full)
│   │   ├── test_legal_actions.py — 741 tokens (full)
│   │   ├── test_overlay_bounded.py — 1,424 tokens (full)
│   │   ├── test_postflop_wiring.py — 756 tokens (full)
│   │   └── test_safe_fallback.py — 418 tokens (full)
│   ├── integration/
│   │   └── test_six_max_benchmark.py — 1,239 tokens (full)
│   └── conftest.py — 68 tokens (full)
├── tools/
│   ├── audit_strategy_leakage.py — 767 tokens (full)
│   ├── benchmark.py — 11,330 tokens (full)
│   ├── exploit_check.py — 8,261 tokens (full)
│   ├── import_audit.py — 1,426 tokens (full)
│   └── package.py — 1,003 tokens (full)
└── AGENTS.md — 2,473 tokens (full)
/Users/farhad/Library/Application Support/RepoPrompt/Workspaces/Workspace-PokerBot-033C9CC6-325C-4F60-9E1F-D7E35E03B6C8/_git_data/
└── repos/
    └── pokerbot-codex-4c122237/
        └── 2026-05-26/
            └── 2257/
                └── diff/
                    └── per-file/
                        ├── consults__2026-05-26-r1-baseline__MANIFEST.md.patch — 7,989 tokens (full)
                        ├── src__bot.py.patch — 1,846 tokens (full)
                        ├── src__opponent_model.py.patch — 3,121 tokens (full)
                        ├── src__postflop.py.patch — 3,327 tokens (full)
                        ├── tests__edge_cases__test_archetype_posterior.py.patch — 1,078 tokens (full)
                        ├── tests__edge_cases__test_overlay_bounded.py.patch — 1,525 tokens (full)
                        ├── tools__audit_strategy_leakage.py.patch — 846 tokens (full)
                        ├── tools__benchmark.py.patch — 10,340 tokens (full)
                        └── tools__exploit_check.py.patch — 9,058 tokens (full)


---

## Generated Plan

## Chat Send ✅
- **Chat**: `lane-a2-plan-AFE3E7` | **Mode**: plan

### Response
The deferred tool list in this environment exposes only team/task management tools (`LSP`, `SendMessage`, `TaskCreate`, `TaskGet`, `TaskList`, `TaskUpdate`, `TeamCreate`, `TeamDelete`) plus the built-in `ToolSearch` and `advisor`. Neither `Write` nor `ExitPlanMode` is available, so the plan is delivered in the response below. The implementer should save this content to `/Users/farhad/.claude/plans/user-file-tree-users-farhad-code-pokerbo-federated-flask.md`.



---

# Lane A-2 — Diagnostic-First Polish for the W3 Candidate

## 1. Context

`submissions/v_w3_candidate.zip` (sha256 `d78a4c6b...`) cleared the primary R1 objective on both seed bases — C2 stat-sig win, average artifact bb/100 across compositions improved from R1 baseline +13.40 to +29.37 (s42) and +21.64 (s142). But three residual problems block promotion to `v_final.zip`:

1. **Neel-in-C2 regressed at seed 42** (`results.C2["seat_1:neel"].bb_per_100 = -16.94`, baseline `+1.29`). Neel uses Monte Carlo equity with a playable mixed range; the current conservative-archetype-targeted shifts hurt against balanced opponents.
2. **C1 seed-42 dropped** from `+27.73` to `-1.50` (not stat-sig, but real). Held-out s142 holds at `+20.43`, so this is not seed-overfit — the seed-42 swing comes from the same overlay-too-aggressive failure mode but on bundled-ref/mixed seats.
3. **`--ablate-overlay` gain `+0.62 < 3.00`** and **LBR aggregate `4387.4 mbb/g`** (22× cap, pre-existing per Lane D's honest LBR). Ablation FAIL is structurally indicative of the same diffuse-posterior overshoot pattern; LBR is informational only here.

**Hypothesis**: the overlay engages too aggressively when `archetype_posterior` is diffuse (no single label confidently identified). The existing `abs(open_shift) + abs(continue_shift) < 0.75pp` gate fails to catch the diffuse case because `_ARCHETYPE_SHIFT_WEIGHTS` continue-row weights *reinforce* across labels (sum ≈ +2.30), so even at uniform posterior the continue-shift at full bound is ~1.84pp and bypasses the gate.

**Cure**: damp the deviation bound by a `peak_confidence_factor` derived from `top_probability`, so diffuse posteriors hard-bail and moderately peaked posteriors apply graduated deviation. Diagnostic must confirm "C1 diffuse, C2 confident" before damping is designed; if posterior is confidently wrong, damping is wrong medicine and the lane stops.

## 2. Summary

Single-iteration polish on the W3 candidate. Two phases:

- **Diagnostic** (read-only, NOT packaged): probe the W3 candidate's per-decision `top_probability` distribution on one C1 seed-42 match and one C2 seed-42 match. If C1 is diffuse and C2 is confident, proceed; otherwise stop and surface.
- **Damping** (if diagnostic confirms): in `src/bot.py`, add a `peak_confidence_factor` that hard-bails below a low peak threshold and ramps to full deviation above a high peak threshold. Remove the redundant 0.75pp shift gate. Build `submissions/v_lane_a2_candidate.zip` (never `v_final.zip`). Re-measure seed 42 + 142 against the acceptance gates; re-run hardening sweep; verify LBR not worse than W3's 4387.4 mbb/g.

One tuning iteration permitted on narrow gate misses. No third iteration.

## 3. Current-state analysis

### Decision path (preflop overlay)

`decide(state)` → `_decide_core` → `_decide_preflop` →

1. `canonical_hand(your_cards)` → hand string
2. `_preflop_lookup(position, hand, action_seq)` → `{action, reason, sizing?}` blueprint decision
3. If `_OVERLAY_DISABLED` is False: `_pressure_preflop_overlay(state, hand, decision, action_seq)`
   - `OpponentModel.archetype_features(state)` → features dict
   - `_posterior_preflop_deviation(features)` → `{open_shift_pp, continue_shift_pp, deviation_bound_pp}`
   - Gate 1: `deviation_bound_pp <= 0` → None (overlay disengaged)
   - Gate 2 (the redundant one we are removing): `|open_shift| + |continue_shift| < 0.75` → None
   - Branch on `facing_raise`: at most one of (`_safe_fallback`, `_min_raise_action`, `_safe_fallback`) returned, only near the score-edge windows around `_OPEN_EDGE_SCORE` / `_CONTINUE_EDGE_SCORE`.
4. If overlay returned non-None: return that. Else return `_preflop_action_from_decision`.

### State that matters

- `src/opponent_model.py`: `MAX_DEVIATION_BOUND_PP = 4.0`. `archetype_features()` returns `archetype_posterior` (dict of 5 floats summing to ~1.0), `n_observations`, `deviation_bound = MAX_DEVIATION_BOUND_PP * sample_confidence`, `top_archetype`, `top_probability`, `facing_raise`. The `sample_confidence` ramps linearly from `n_observations=20` (factor 0) to `n_observations=220` (factor 1).
- `src/bot.py`: `_ARCHETYPE_SHIFT_WEIGHTS` is a 5×{open,continue} table. Continue row sums to `+2.30`, open row sums to `-0.05`. This asymmetry is the structural reason a diffuse posterior still produces a meaningful continue-shift.

### Observed empirics that drive the design

- Average continue-shift at uniform posterior (0.20 each), full sample-confidence, full 4pp bound: `0.20 × 2.30 × 4.0 = 1.84pp`. This is what's firing against Neel in C2 s42 and against mixed seats in C1 s42.
- `archetype_posterior` already exposes `top_probability`, but `_posterior_preflop_deviation` ignores it. This is the closest reusable signal — no model changes required.

### Reusable code (do not duplicate)

- `OpponentModel.archetype_features()` already computes `top_probability` and exposes it on every call. The damping reads it (and/or recomputes from `archetype_posterior` for test robustness).
- `tools/benchmark.py::_resolve_six_max_seat`, `_six_max_lineup_for_seat`, `_six_max_seed_schedule`, `_make_source_mount`, and the direct import of `ext/fullhouse-engine/sandbox/match.run_match` give the probe everything it needs to construct a single composition's lineup and run a deterministic 400-hand match without copy-pasting benchmark logic.
- `tests/edge_cases/test_overlay_bounded.py::peaked_features`/`FakeModel`/`assert_legal` is the established pattern for stubbing the OpponentModel and asserting overlay shapes; new damping tests reuse it.

### Blocking constraints

- `tests/edge_cases/test_archetype_posterior.py::test_no_identity_string_branches_or_audit_hits_in_model_source` audits `src/opponent_model.py` for tokens including bundled-ref names, branch labels, snapshot labels, and `v_final`. Any added field in `archetype_features()` must not contain those tokens.
- `tools/audit_strategy_leakage.py` runs the same audit on the packaged `bot.py` + `src/*.py`. Both stay clean.
- `tools/package.py` only packages `src/` and `data/`. Anything under `tools/probes/` is excluded automatically — the probe is safe to add there.

## 4. Design

### 4.1 Diagnostic helper — `tools/probes/posterior_dump.py` (NEW, never packaged)

**Kind**: One-shot Python CLI script. Lives at `tools/probes/posterior_dump.py`. `tools/probes/` is a new directory. Not imported by any production module.

**Why separate from production source**: the identity-leakage audit and the strict packager both target `src/`; a probe in `tools/probes/` is invisible to packaging and to the leakage audit. Production source stays untouched, which means the diagnostic and the polish iteration are independently revertible: rip out the probe file and the W3 source state is bit-identical.

**CLI surface**:

```
python tools/probes/posterior_dump.py
  --composition {C1|C2|C3|C4}
  --seed <int>
  --hands <int>                  # default 400
  --hero-seat <0..5>             # default 5 (artifact slot), matches benchmark seat_6:artifact
  --out <path-to-jsonl>          # default: env POKERBOT_DEBUG_POSTERIOR_OUT, then auto
  [--source-mount <dir>]         # default: copy of repo src/
```

Runs ONE 400-hand match (one composition, one seed, hero at one physical seat) and writes one JSONL record per `OpponentModel.archetype_features` call. Per the user's required design decision: exactly one C1 seed-42 match and one C2 seed-42 match before damping design.

**Injection mechanism (resolves the "not in production source" constraint)**:

1. Probe creates a temporary mount via the same pattern as `tools/benchmark.py::_make_source_mount`: `shutil.copytree(ROOT/'src', tmp/'src')`, write a temporary `bot.py` shim.
2. Probe writes a single new file into the mount: `tmp/_posterior_probe.py` with a monkey-patch that wraps `OpponentModel.archetype_features` to append a JSONL record after each call, gated on `POKERBOT_DEBUG_POSTERIOR == "1"`.
3. Probe's temp `bot.py` shim has one extra line versus the standard mount: `import _posterior_probe` between the `sys.path.insert` and the `from src.bot import decide` import. This ensures the monkey-patch is installed before `bot.decide` is first called.
4. Probe imports `run_match` from `ext/fullhouse-engine/sandbox/match` directly and calls it with `n_hands=400`, `seed=<arg>`, `verbose=False`, lineup constructed via `tools.benchmark._six_max_lineup_for_seat(mount_path, composition_entries, hero_seat)`.
5. After the match, probe reads the JSONL it produced, computes a small summary, prints it, then `shutil.rmtree`s the mount.

**JSONL record schema** (one line per `archetype_features` call):

```jsonc
{
  "match_id": "probe_C1_s42_seat6",
  "composition": "C1",
  "seed": 42,
  "hero_physical_seat": 5,
  "hand_id": "<engine-provided>",
  "street": "preflop|flop|turn|river",
  "seat_to_act": 0..5,
  "amount_owed": int,
  "facing_raise": bool,
  "n_observations": int,
  "top_archetype": "<one of ARCHETYPE_LABELS>",
  "top_probability": 0.0..1.0,
  "posterior": { "<label>": float, ... 5 entries },
  "deviation_bound": 0.0..4.0,
  "sample_confidence": 0.0..1.0,         // recomputed: deviation_bound / MAX_DEVIATION_BOUND_PP
  "overlay_disabled_env": bool           // True if POKERBOT_DISABLE_OVERLAY=1 at observe time
}
```

**Summary**: at end of run, probe computes (over decisions with `n_observations >= MIN_ARCHETYPE_OBSERVATIONS`):

- `top_probability` quartiles (`p25`, `p50`, `p75`, `p90`).
- Fraction of decisions where `top_probability < 0.40`, `< 0.50`, `< 0.60`, `< 0.65`.
- Top-archetype distribution (which labels win at the peak, and how often).
- Mean continue-shift produced by current weights at observed posteriors (recomputed independently from the W3 weight table; provides a "how much overlay is this match actually applying" number).

Prints a one-line classification using the rule in §4.2.

### 4.2 Diagnostic procedure and interpretation

**Required pre-design runs** (two commands, ~3–5 min wall time each):

```bash
cd /Users/farhad/Code/PokerBot-codex

mkdir -p consults/2026-05-26-r1-baseline/lane_a2_debug/c1_c2_probe/

POKERBOT_DEBUG_POSTERIOR=1 \
POKERBOT_DEBUG_POSTERIOR_OUT=consults/2026-05-26-r1-baseline/lane_a2_debug/c1_c2_probe/posterior_dump_C1_s42.jsonl \
.venv/bin/python tools/probes/posterior_dump.py --composition C1 --seed 42 --hands 400

POKERBOT_DEBUG_POSTERIOR=1 \
POKERBOT_DEBUG_POSTERIOR_OUT=consults/2026-05-26-r1-baseline/lane_a2_debug/c1_c2_probe/posterior_dump_C2_s42.jsonl \
.venv/bin/python tools/probes/posterior_dump.py --composition C2 --seed 42 --hands 400
```

**Classification per composition** (median `top_probability` across decisions with `n_observations >= 20`):

- `diffuse`: median `< 0.50`
- `borderline`: median in `[0.50, 0.60)`
- `confident`: median `>= 0.60`

Quartile checks supplement the median (a bimodal distribution can hide diffuse behavior under a median that looks fine):

- Probe also reports `p25 < 0.40` and `p75 < 0.55` checks; if both true → diffuse regardless of median.

**Decision matrix** (mandatory; printed by probe summary):

| C1 verdict | C2 verdict | Action |
|---|---|---|
| diffuse | confident | **PROCEED to §4.3 damping design.** Hypothesis confirmed. |
| confident | confident | **STOP.** Posterior is confidently wrong, not diffuse. Damping cannot help. Surface to human review. |
| diffuse | diffuse | **STOP.** Overlay is exploiting a confidently-wrong-but-narrowly-distributed signal in C2. Surface. |
| confident | diffuse | **STOP.** Inverted hypothesis — surface for re-analysis. |
| borderline | any | Run probe at seed 142 for C1 and C2; if still borderline, escalate; otherwise re-apply matrix on the s142 result. |

The implementer must not proceed to step 3 of the implementation order until this verdict is computed and visible in the probe's stdout summary.

### 4.3 Damping design — `_peak_confidence_factor` (gated on PROCEED)

**Mechanism choice** (resolves required design decision #3): replace the existing 0.75pp shift gate with a non-overlapping hard-bail-zone + linear ramp. Both the existing gate and a smooth ramp cannot coexist without one making the other partially dead — the ramp's low end already produces sub-0.75pp totals, which the gate would then unconditionally suppress, making that zone of the ramp inert.

**Helper** (signature and behavior; not the implementation):

```python
# src/bot.py, module-level
PEAK_CONFIDENCE_BAIL_THRESHOLD = 0.40    # below: factor = 0 (hard bail)
PEAK_CONFIDENCE_FULL_THRESHOLD = 0.65    # at/above: factor = 1 (full deviation)

def _peak_confidence_factor(top_probability: float) -> float:
    # Piecewise-linear, monotone non-decreasing in top_probability.
    # < BAIL → 0; >= FULL → 1; in between, linearly interpolated.
```

**Threshold rationale**:

- 5 archetypes, uniform prior `1/5 = 0.20`. A top of `0.40` is `2 × uniform` — the minimum point at which "one label genuinely leads" is meaningful. Below that, treat as no signal.
- `0.65` corresponds to "at least 65% mass on one label, at most 35% on the other four combined". This is "moderately strong" — strong enough to commit full deviation.
- The implementer MAY adjust these to `0.35 / 0.60` or `0.45 / 0.70` based on the diagnostic histogram, still within iteration 1. Larger changes (e.g. moving BAIL to 0.50) require justification in the scoreboard.

**Composition with sample_confidence** (resolves required design decision #4):

```python
# src/bot.py, in _posterior_preflop_deviation
posterior = features.get("archetype_posterior") or {}
top_prob  = max(posterior.values()) if isinstance(posterior, dict) and posterior else 0.0
sample_bound = _float(features.get("deviation_bound"), 0.0)   # already MAX * sample_confidence
peak_factor  = _peak_confidence_factor(top_prob)
bound = max(0.0, min(sample_bound * peak_factor, 4.0))
# bound = MAX_DEVIATION_BOUND_PP * sample_confidence * peak_factor   ← user-specified invariant
```

Note: `top_probability` is read from the posterior dict (not from `features["top_probability"]`) so existing tests that build `peaked_features` without a `top_probability` field still work, and the bot's gating logic is self-sufficient given any posterior dict.

**Gate removal** (resolves required design decision #3 — exactly one mechanism):

In `_pressure_preflop_overlay`, delete the line:

```python
if abs(shifts["open_shift_pp"]) + abs(shifts["continue_shift_pp"]) < 0.75:
    return None
```

The `if shifts["deviation_bound_pp"] <= 0.0: return None` guard is RETAINED — it now fires whenever `peak_factor == 0` (hard-bail zone) OR `sample_confidence == 0` (n_obs below MIN). Single coherent disengage signal.

**No other changes to overlay branching**: the `facing_raise` branch, the open/continue edge-score windows, `_within_shift`, `_min_raise_action`, and the `_safe_fallback` calls are unchanged. The behavior change is *only* in the bound magnitude.

### 4.4 State, concurrency, lifecycle, errors

- `_peak_confidence_factor` is pure (no I/O, no globals). One `max()` over a 5-element dict and a piecewise-linear evaluation. O(1).
- Probe writes JSONL with per-line atomic `f.write(json.dumps(record) + "\n")`. If probe crashes mid-run, partial JSONL is still parseable line-by-line. The match itself runs under the engine's deterministic seed; running probe twice with the same seed produces identical match outcomes (verified by counting JSONL lines and per-line `hand_id` match).
- Probe error handling: if `run_match` raises, `shutil.rmtree(mount, ignore_errors=True)` in a `finally` and re-raise. If a single JSONL append fails (disk full, permission), log to stderr and continue the match — diagnostic completeness is best-effort, not match-critical.
- Production overlay error handling: existing `try/except Exception: return {"action": "fold"}` in `decide()` already wraps the overlay path; new helper adds no new failure modes. The damping helper handles malformed input (empty/missing posterior → `top_prob = 0.0` → hard-bail) without raising.
- No concurrency: engine runs `decide()` synchronously under its 2s budget. No threads, no async, no shared mutable state in the damping path.

### 4.5 Algorithmic and edge cases

- Empty/missing posterior dict → `max()` over empty defaults to 0.0 → `peak_factor = 0` → `bound = 0` → overlay early-returns. Safe.
- Negative `top_probability` (cannot happen from OpponentModel, but defensive): `peak_factor = 0`.
- `top_probability` exactly at `BAIL`: strict `<` boundary, returns 0. Exactly at `FULL`: `>= ` boundary, returns 1. Ramp continuous in interior. No discontinuity in produced bound at boundaries.
- `MAX_DEVIATION_BOUND_PP * 1.0 * 1.0 = 4.0` upper bound preserved.
- Performance: ~5 floating-point ops added per preflop decision. Negligible against the existing equity-call budget.

## 5. File-by-file impact

### Modified

| File | What changes | Why | Ordering |
|---|---|---|---|
| `src/bot.py` | Add module-level `PEAK_CONFIDENCE_BAIL_THRESHOLD = 0.40`, `PEAK_CONFIDENCE_FULL_THRESHOLD = 0.65`. Add private `_peak_confidence_factor(top_probability) -> float`. In `_posterior_preflop_deviation`: derive `top_prob` from `archetype_posterior`, multiply `peak_factor` into the bound before computing shifts. In `_pressure_preflop_overlay`: remove the `abs(open) + abs(continue) < 0.75` early-return line. | Implements the diagnostic-confirmed damping. Replaces the redundant shift gate with the coherent peak-confidence gate. | After diagnostic PROCEED. |
| `tests/edge_cases/test_overlay_bounded.py` | Extend `peaked_features` helper to accept optional `peak: float = 1.0` argument — when `peak < 1.0`, distribute `(1.0 - peak) / 4.0` mass to the other four labels so `top_probability == peak`. Add three new tests (see §6). | Pins the new damping behavior; prevents accidental future re-introduction of the 0.75pp gate. | With the bot.py change (atomic). |

### Added

| File | What it is | Why |
|---|---|---|
| `tools/probes/posterior_dump.py` | New CLI script; injects a monkey-patched `OpponentModel.archetype_features` via temp source mount; runs one match; dumps JSONL; prints diffuse/confident verdict. Not packaged (lives under `tools/probes/`). Reuses `tools.benchmark._resolve_six_max_seat`, `_six_max_lineup_for_seat`, `_make_source_mount`-style copy, and `ext/fullhouse-engine/sandbox/match.run_match`. | Empirically classifies posterior shape on C1/C2 without modifying production source. Required before damping design. |
| `tools/probes/__init__.py` | Empty marker file. | Makes `tools/probes` importable if the probe is ever extended to reuse code across probes. Optional but conventional. |
| `prompt-exports/optimize-lane-a2-runs.md` | Scoreboard scaffold (see §9). New directory `prompt-exports/` if not present. | Tracks W3 baseline and Lane A-2 iteration(s) for downstream tooling. |

### Not modified (explicitly preserved)

- `src/opponent_model.py` — unchanged. `top_probability` already exposed; the audit invariant in `test_archetype_posterior.py::test_no_identity_string_branches_or_audit_hits_in_model_source` stays clean.
- `src/postflop.py`, `src/preflop_lookup.py`, `src/equity.py`, `src/ranges.py`, `src/sizing.py`, `src/timeout_guard.py` — out of scope.
- `tools/benchmark.py`, `tools/exploit_check.py`, `tools/audit_strategy_leakage.py`, `tools/package.py`, `tools/import_audit.py` — out of scope. The probe IMPORTS from `tools/benchmark.py` but does not modify it.
- `submissions/v_final.zip` — never written. The Lane A-2 artifact is `submissions/v_lane_a2_candidate.zip`.
- `submissions/v_w3_candidate.zip` — preserved (rollback target if Lane A-2 fails or rolls back).
- `consults/2026-05-26-r1-baseline/MANIFEST.md` — no Lane A-2 edits unless and until promotion is approved (separate user gate).

## 6. New tests (in `tests/edge_cases/test_overlay_bounded.py`)

All use the existing `FakeModel` + `monkeypatch(bot, "_OPPONENT_MODEL", ...)` pattern. All exercise private helpers directly — same pattern as the existing peak tests.

1. **`test_diffuse_posterior_hard_bails_below_peak_threshold`**
   - For each `label` in `ARCHETYPE_LABELS`: build `peaked_features(label, peak=0.30, bound=4.0)` (so `top_probability == 0.30 < BAIL`).
   - Assert `_posterior_preflop_deviation(features)["deviation_bound_pp"] == 0.0`.
   - Assert `_pressure_preflop_overlay(state(), "J7s", {"action": "fold", "reason": "range_fold"}, ())` returns `None`.

2. **`test_mid_peak_posterior_damps_bound_proportionally`**
   - `peaked_features("blueprint_threshold_exploit", peak=0.525, bound=4.0)` → `top_probability == 0.525`, midway through the ramp, expected `peak_factor = (0.525 - 0.40) / (0.65 - 0.40) = 0.5`.
   - Assert `deviation_bound_pp == pytest.approx(4.0 * 1.0 * 0.5, abs=1e-9) == 2.0`.
   - Assert `|open_shift| + |continue_shift|` remains within the new bound.

3. **`test_strong_peak_posterior_uses_full_bound`**
   - `peaked_features(label, peak=0.80, bound=4.0)` → `top_probability == 0.80 >= FULL`, `peak_factor == 1.0`.
   - Assert `deviation_bound_pp == pytest.approx(4.0, abs=1e-9)`.
   - This case must produce the same shifts as the existing peak-1.0 tests (within the ramp's saturation zone), so the existing behavior in `test_overlay_action_remains_legal_and_bounded_for_each_peak` is preserved at higher confidence.

4. **Existing tests, unchanged behavior to verify**:
   - `test_posterior_deviation_is_hard_bounded_for_each_peak`, `test_overlay_action_remains_legal_and_bounded_for_each_peak`, `test_risk_peak_widens_only_near_boundary_open`, `test_loose_or_threshold_peaks_tighten_boundary_opens`, `test_pressure_peaks_tighten_priced_continue` — all use `peak=1.0` implicitly through `peaked_features`; they should pass without modification once `peaked_features` defaults `peak=1.0`.
   - `test_overlay_disabled_cleanly_via_env_var` — unaffected; the env-var path short-circuits before damping.
   - `test_warmup_short_circuit_does_not_enter_preflop` — unaffected.

`pytest tests/edge_cases -x` must pass at `>= 50/50` (47 existing + 3 new). If `peaked_features` argument change breaks any other test, fix the test call sites in the same PR (additive `peak` argument, default `1.0` keeps all existing call sites green).

## 7. Acceptance gates (all must hold before any promotion)

Build the candidate artifact and re-measure:

```bash
cd /Users/farhad/Code/PokerBot-codex
.venv/bin/python tools/package.py --output submissions/v_lane_a2_candidate.zip --strict
.venv/bin/python /Users/farhad/Code/PokerBot/ext/fullhouse-engine/sandbox/validator.py submissions/v_lane_a2_candidate.zip
.venv/bin/python tools/import_audit.py
.venv/bin/python -m pytest tests/edge_cases -x
.venv/bin/python tools/audit_strategy_leakage.py --zip submissions/v_lane_a2_candidate.zip
.venv/bin/python tools/exploit_check.py --bot submissions/v_lane_a2_candidate.zip

.venv/bin/python tools/benchmark.py --six-max-mix --bot submissions/v_lane_a2_candidate.zip \
  --paired-seed-base 42 --paired-seed-count 10 --hands 400 \
  --out-dir consults/2026-05-26-r1-baseline/lane_a2_candidate/
.venv/bin/python tools/benchmark.py --six-max-mix --bot submissions/v_lane_a2_candidate.zip \
  --paired-seed-base 142 --paired-seed-count 10 --hands 400 \
  --out-dir consults/2026-05-26-r1-baseline/lane_a2_candidate/holdout_142/
```

### Hard gates (extract from the seed-42 and seed-142 JSON files)

| Gate | JSON path | Threshold |
|---|---|---|
| C2 s42 stat-sig win | `results.C2["seat_6:artifact"].ci_95[0]` | `> 0` |
| C2 s142 stat-sig win | `(holdout) results.C2["seat_6:artifact"].ci_95[0]` | `> 0` |
| Neel-in-C2 s42 not negative | `results.C2["seat_1:neel"].bb_per_100` | `>= 0` |
| Neel-in-C2 s142 reported | `(holdout) results.C2["seat_1:neel"].bb_per_100` | report only (no hard threshold, but flag regressions from W3 +21.04) |
| C1 s42 healthy | `results.C1["seat_6:artifact"].bb_per_100` | `>= 15` |
| Zero failures s42 | sum of `results.C{1,2,3,4}[seat_*].{crashes, timeouts, illegal_actions}` | `0` total / `0` total / `0` total |
| Zero failures s142 | same in holdout file | `0` / `0` / `0` |
| Edge tests | `pytest tests/edge_cases -x` | `>= 50/50` PASS |
| LBR not worse | `tools/exploit_check.py --bot submissions/v_lane_a2_candidate.zip` aggregate | `<= 4387.4 mbb/g` |
| Hardening | `package.py --strict`, validator, `import_audit.py`, `audit_strategy_leakage.py` | all PASS |

### Per-seat measurements to report (always)

For each of seed 42 and seed 142, extract and record in the scoreboard (and in the run log under `consults/2026-05-26-r1-baseline/lane_a2_candidate/`):

- **C1**: `results.C1["seat_6:artifact"]` → `bb_per_100, ci_95[0], ci_95[1]`.
- **C2**: `results.C2["seat_6:artifact"]` → `bb_per_100, ci_95[0], ci_95[1]`.
- **C3**: `results.C3["seat_6:artifact"]` → `bb_per_100, ci_95[0], ci_95[1]`.
- **C4**: `results.C4["seat_6:artifact"]` → `bb_per_100, ci_95[0], ci_95[1]`.
- **Neel-in-C2**: `results.C2["seat_1:neel"]` → `bb_per_100, ci_95[0], ci_95[1]`.
- **Famadeo-in-C2** (preserve W3 stat-sig win): `results.C2["seat_3:famadeo"]` → `bb_per_100, ci_95[0], ci_95[1]`.
- **Vladimir-in-C4** (preserve W3 s142 stat-sig win): `results.C4["seat_1:vladimir"]` → `bb_per_100, ci_95[0], ci_95[1]`.
- **Famadeo-in-C4**: `results.C4["seat_2:famadeo"]`.
- **Total failure count per composition**: sum of `crashes`, `timeouts`, `illegal_actions` over all `seat_*` rows.
- Any non-empty `bot_errors` field anywhere in the JSON → record verbatim.

Anchor values for delta computation:

- W3 s42: C1 `-1.50 [-19.76, +16.83]`; C2 `+62.79 [+18.30, +113.05]`; Neel-C2 `-16.94 [-38.18, +6.26]`; failures `0/0/0`.
- W3 s142: C1 `+20.43 [+0.23, +37.42]`; C2 `+25.68 [+6.17, +46.08]`; Neel-C2 `+21.04 [+0.55, +43.21]`; failures `0/0/0`.

## 8. Risk register

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Diagnostic shows confidently-wrong posterior (high `top_probability` but wrong label peaked). Damping is wrong medicine. | medium | high | STOP per §4.2 decision matrix. Surface to human. Do not proceed to step 3 of implementation order. |
| 2 | Damping too aggressive: C4 worst-case-tail regresses; Famadeo-in-C2 stat-sig win lost. | medium | high | Report Famadeo-in-C2 and Vladimir-in-C4 numbers explicitly in scoreboard. If C4 seat_6 ci_low drops below +30 (W3 was `+44.20`-ish lower-bound) on either seed, lower `BAIL` to 0.35 in iteration 2. |
| 3 | Damping too weak: Neel-in-C2 still negative on s42. | medium | medium | Bump `BAIL` to 0.45 in iteration 2. Or raise `FULL` to 0.70 to extend the ramp and reduce mid-zone deviation. |
| 4 | LBR worse (overlay reduced but blueprint LBR is the dominant floor). | low | low | LBR is a soft gate (≤ 4387.4); damping reduces overlay activity so direction is favorable. If somehow worse, debug — likely an unintended interaction with the gate removal. |
| 5 | Probe injection disturbs match determinism (e.g. import-ordering side effects). | low | medium | Verify probe is deterministic by running probe twice at same seed; line count and per-line `hand_id` sequence must match. If non-deterministic, fall back to a synthetic diagnostic: replay engine `match_action_log` records through `archetype_features` outside the engine. |
| 6 | New tests interact poorly with `peaked_features` default. | low | low | `peak=1.0` default keeps all existing call sites green; verify with `pytest -k peak` before adding new tests. |
| 7 | Probe dir accidentally packaged. | very low | low | `tools/package.py` only reads `src/` and `data/` per `build()` function — `tools/probes/` excluded by construction. Verify via strict-mode listing the first time. |
| 8 | Iteration 2 also misses gates. | low | high | Stop. Restore `submissions/v_w3_candidate.zip` as the head-of-line promotion target. Document the obstacle in the scoreboard `decision` column. No third iteration. |
| 9 | Editing tests + production source in one atomic step lands a test that secretly depended on the removed 0.75pp gate. | medium | low | Review the existing peak tests for accidental dependency on the gate — none expected, but explicit reading is part of the implementation order's step 3. |

## 9. Implementation order

Each numbered step is independently verifiable. Step 5 + 6 are atomic with respect to a single candidate artifact (build + hardening sweep land together or get discarded together).

1. **Write the diagnostic probe** — create `tools/probes/__init__.py` and `tools/probes/posterior_dump.py`. No edits to `src/`. Smoke: run the probe with `--composition C1 --seed 42 --hands 10` and verify it produces a non-empty JSONL with the expected schema and prints a summary line.
2. **Run diagnostic on C1 s42 and C2 s42** — 400-hand probes per §4.2 commands. Apply the decision matrix. If verdict ≠ PROCEED, STOP. Capture probe output to `consults/2026-05-26-r1-baseline/lane_a2_debug/c1_c2_probe/probe_summary.txt`.
3. **Edit `src/bot.py` and `tests/edge_cases/test_overlay_bounded.py` atomically** — add `_peak_confidence_factor`, update `_posterior_preflop_deviation`, remove the 0.75pp gate, add `peak` arg to `peaked_features`, add the three new tests. Verify: `pytest tests/edge_cases -x` ≥ 50/50.
4. **Manual review of existing peak tests** — read `test_overlay_action_remains_legal_and_bounded_for_each_peak`, `test_risk_peak_widens_only_near_boundary_open`, `test_loose_or_threshold_peaks_tighten_boundary_opens`, `test_pressure_peaks_tighten_priced_continue`. Confirm none accidentally depended on the now-removed gate (none expected — all use peak=1.0 and exercise non-zero shifts).
5. **Build candidate** — `tools/package.py --output submissions/v_lane_a2_candidate.zip --strict`. **MUST NOT be named `v_final.zip`.** Verify: zip exists, file listing shows only `bot.py`, `src/*.py`, `data/*` — no `tools/` content.
6. **Hardening sweep (atomic with step 5)** — validator, import audit, strategy leakage audit, LBR. All four must PASS (LBR aggregate `<= 4387.4`). If any fail, discard the zip, fix the cause in `src/bot.py` or tests, return to step 3.
7. **Acceptance measurement** — both `--six-max-mix` runs (seed 42 + seed 142). Each ~7 minutes wall time. Extract all per-seat measurements per §7.
8. **Scoreboard write** — populate the Lane A-2 row of `prompt-exports/optimize-lane-a2-runs.md` (scaffold in §10). One row per iteration.
9. **Decision**:
   - **All gates pass** → promotion candidate. Halt for explicit user approval before any `cp submissions/v_lane_a2_candidate.zip submissions/v_final.zip`. The user has not pre-approved promotion.
   - **One or two narrow misses** (e.g. C1 s42 = 13.5 instead of ≥ 15, or Neel-in-C2 s42 = -1.0 instead of ≥ 0) → **iteration 2** allowed. Adjust ONE of `BAIL` / `FULL` per the risk register's mitigation. Name the iteration-2 artifact `submissions/v_lane_a2_candidate_v2.zip`. Re-run steps 5–8.
   - **Iteration 2 misses** OR **iteration 1 misses 3+ hard gates** → STOP. Restore the W3 candidate as head-of-line. Document obstacle in scoreboard `decision`. No iteration 3.

### Iteration cap (resolves required design decision #6)

**One polish pass, optionally one tuning iteration. Hard cap of two iterations total.** If both miss, the problem is deeper than a threshold tweak and warrants full re-design (out of Lane A-2 scope).

## 10. Scoreboard scaffold — `prompt-exports/optimize-lane-a2-runs.md`

(File does not exist. Implementer creates it at step 8 with the content below. The directory `prompt-exports/` may not exist either — create it.)

```markdown
# Lane A-2 scoreboard — W3 polish via posterior peak-confidence damping

Columns:
- artifact: submissions/<name>.zip
- sha256: full sha256 of the zip
- iteration: W3 baseline | A-2 iter 1 | A-2 iter 2
- diagnostic verdict: PROCEED | STOP-confidently-wrong | STOP-diffuse-C2 | STOP-inverted | not instrumented
- C1 s42 seat_6 bb/100 [CI]: from results.C1["seat_6:artifact"]
- C1 s142 seat_6 bb/100 [CI]: from holdout file
- C2 s42 seat_6 bb/100 [CI]: from results.C2["seat_6:artifact"]
- C2 s142 seat_6 bb/100 [CI]: from holdout file
- Neel C2 s42 bb/100 [CI]: from results.C2["seat_1:neel"]
- Neel C2 s142 bb/100 [CI]: from holdout
- failures s42/s142: total crashes/timeouts/illegal_actions per seed-base
- edge tests: N/M pass count
- validator: PASS | FAIL
- import audit: PASS (cold Xs, RSS X MB) | FAIL
- LBR aggregate mbb/g: from exploit_check.py
- decision: needs Lane A-2 | promote | iter 2 | rollback | stop-and-surface

| artifact | sha256 | iteration | diagnostic verdict | C1 s42 seat_6 bb/100 [CI] | C1 s142 seat_6 bb/100 [CI] | C2 s42 seat_6 bb/100 [CI] | C2 s142 seat_6 bb/100 [CI] | Neel C2 s42 bb/100 [CI] | Neel C2 s142 bb/100 [CI] | failures s42/s142 | edge tests | validator | import audit | LBR aggregate mbb/g | decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| submissions/v_w3_candidate.zip | d78a4c6be8269ea5340cc867f8986b6521978d5a96a79cc2322adbd30f2f8570 | W3 baseline | not instrumented | -1.50 [-19.76, +16.83] | +20.43 [+0.23, +37.42] | +62.79 [+18.30, +113.05] | +25.68 [+6.17, +46.08] | -16.94 [-38.18, +6.26] | +21.04 [+0.55, +43.21] | 0/0/0 both | 47/47 | PASS | PASS 0.105s RSS 38.4MB | 4387.4 | needs Lane A-2 |
| submissions/v_lane_a2_candidate.zip | <fill after build> | A-2 iter 1 | <PROCEED | STOP-*> | <fill> | <fill> | <fill> | <fill> | <fill> | <fill> | <fill> | <fill>/<fill> | <PASS|FAIL> | <PASS X s, RSS Y MB|FAIL> | <fill> | <promote | iter 2 | rollback> |
| submissions/v_lane_a2_candidate_v2.zip (iter 2 only) | <fill> | A-2 iter 2 | (carryover from iter 1) | … | … | … | … | … | … | … | … | … | … | … | … |

Notes for the implementer:
- The W3 row's "Neel C2 s142" value (+21.04 [+0.55, +43.21]) is read from `results.C2["seat_1:neel"]` in the W3 s142 holdout JSON; the manifest summary table shows a Famadeo number for s142 instead, so cross-check JSON path is the source of truth.
- The W3 row's "Neel C2 s42" value (-16.94 [-38.18, +6.26]) is from the C2 s42 file; the manifest reports this verbatim.
- If iteration 1 fails the diagnostic gate, the entire damping row remains blank for that artifact; record "iter 1 aborted by diagnostic" in the decision column.
```

## 11. Unknowns / validate during implementation

| Unknown | Validation approach |
|---|---|
| Probe monkey-patch survives `run_match`'s loader contract. The engine may sandbox bot imports in ways that defeat the patch. | Step 1 smoke (`--hands 10`) must show a non-empty JSONL with at least one record per `archetype_features` call expected during preflop overlay activity. If JSONL is empty after a 10-hand smoke, the loader strips the probe — fall back to synthetic diagnostic: replay recorded `action_log` entries through `OpponentModel.archetype_features` from a test harness without going through `run_match` at all. |
| Threshold choice (0.40 / 0.65) may not match the empirical distribution. | Diagnostic histogram supplies the data. The implementer may shift thresholds within `[0.30, 0.50]` for BAIL and `[0.55, 0.75]` for FULL based on the histogram, as part of iteration 1. Document the chosen pair and the reasoning in the scoreboard's `iteration` cell. |
| Whether removing the 0.75pp gate exposes any unintended thin-shift behavior that the gate was masking. | Step 4 manual review of existing peak tests + the new tests covering peak=0.30, 0.525, 0.80 should catch it. If any unexpected test fails, the issue is real — investigate before iterating. |
| Whether the s142 acceptance run also produces Neel-in-C2 regression beyond W3's +21.04. | Recorded in scoreboard "Neel C2 s142" column. Not a hard gate, but a stat-sig regression below +5 from the W3 s142 anchor (+21.04) is a reason to consider iteration 2 even if all hard gates pass. |
| Whether `submissions/v_lane_a2_candidate.zip` size remains ≤ ~32.5 KB. | Step 5 reports zip size; if it grew unexpectedly, the diff includes unintended content. |

---

End of plan. Once the diagnostic verdict is PROCEED and the acceptance gates clear, the candidate artifact is ready for explicit user approval before any `cp` to `submissions/v_final.zip`. The plan does not authorize promotion under any condition.


> 💡 Continue this plan conversation with ask_oracle(chat_id: "lane-a2-plan-AFE3E7", new_chat: false)