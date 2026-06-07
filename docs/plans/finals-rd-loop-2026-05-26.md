# Finals R&D Overnight Loop: Plan

## Goal

Build a tournament-mimicking benchmark grounded in real public competitor evidence, then run overnight R&D loops that take our bot from "passes a contaminated gauntlet" to "beats the strongest public bots by a decent margin under qualifier-shape conditions," so the 2026-06-01 Swiss qualifier outcome is a near-guarantee rather than a hope. Operative scoring metric: **cumulative chip delta** (engine README authoritative; "chip EV" is public-site shorthand).

## Background

### Locked decisions (Phase 1.5)

- **Scoring metric**: cumulative chip delta. Engine README and `docs/tournament-spec.md:8,54-56` agree; the organiser-site "chip EV" copy is public-facing shorthand. Bot must prefer lower variance / ranking robustness over raw +EV all-in coinflips that hurt cutoff probability.
- **Adversary surface**: 5 behaviour-matched archetypes (`range_mc_pot_odds`, `blueprint_threshold_exploit`, `risk_gated_conservative`, `stage_variant_anti_punt`, `monte_carlo_basic`) **plus** cloned public bots Neel / Dominic / Famadeo / Vladimir / Saroop into `ext/public-bots/<name>/`. GitHub clones are not attributable to repo owners (only aggregate clone counts via Insights → Traffic; no usernames/IPs). Daily-cron monitoring was envisioned but triaged to a one-shot `git ls-remote` snapshot on 2026-05-31 (W2); the full launchd cron + watchlist alerts ship 2026-06-02 as part of finals prep.
- **Loop architecture**: Option C — Claude `/CodexCode` swarm orchestration. Claude in `PokerBot-claude` conducts 4-8 Codex agents in isolated temp worktrees per swarm; Claude synthesizes. Token economics: 20x Codex + 5x Claude → Codex does the parallel implementation mass, Claude orchestrates and reviews. `PokerBot-codex` worktree role: slow-cooking native Codex `/goal` for long-horizon training/blueprint work that doesn't fit a 1-2hr swarm wave.
- **Success criterion**: 4-rung staircase.
  - **R1** — Benchmark trustworthy: tournament-mimicking surface built; current `submissions/v_final.zip` baseline numbers recorded.
  - **R2** — Field-beating: strict-positive 95% CI cumulative-chip-delta vs ≥ 85-90% of named public bots + archetypes; zero crashes/timeouts/illegal actions.
  - **R3** — Top-tier-beating: strict-positive CI vs Vladimir (Deep CFR), Famadeo (if `runtime_enabled` flips), Saroop (if verified strong), and a "mystery strong" deliberately-tuned archetype.
  - **R4** — Decent margin: CI lower bound ≥ N bb/100 above zero against the R3 set. N is calibrated in W9 from the R1 spread on the R3-tier seats (not the soft tier); candidate value ≈ 50 bb/100 but final number lands at calibration time.
- **Elegance constraint**: each new module must (a) cite GT/math basis with `# Source: [[note-name]]` comment, (b) demonstrate measured benchmark gain, (c) survive a "delete and re-benchmark" ablation, (d) keep LBR exploit guard under the cap.
- **Online-research clause**: every R&D iteration begins with a literature-survey step. Agents must cite the paper a technique derives from before implementing.

### Current bot reality (NOT what STATUS.md headline numbers suggest)

The X1 audit (`PokerBot-codex/consults/day1_x1/MANIFEST.md`, `PokerBot-codex/consults/Day 1 X1 bundle audit.md`) is the load-bearing truth, not the headline gauntlet numbers in `STATUS.md:234-242`:

- Pre-X1 wins were partly driven by **name-triggered opponent-identity branches** in `bot.py` that pattern-matched on opponent string names. Commit `9904ed1` surgically deleted them (-67 LOC). Post-X1 honest numbers:
  - `template +71.82`, `mathematician +144.60`, `shark +69.81`, `ref_bot_2 +144.60` (essentially unchanged)
  - **`aggressor +176.03 → -236.59`** (`MANIFEST.md:79-80`) — the win was fabricated by the branch
  - Overlay ablation: prior claimed +417 bb/100; honest ≈ 0 to -8 (`MANIFEST.md:81-82`)
  - Self-play ratchet: prior +4.47; honest -0.87 (`MANIFEST.md:83-84`)
  - H2H pre-vs-post: +0.00 BB/match, CI `[-3.36, +3.30]` → **EV-neutral when labels don't trigger** (`MANIFEST.md:87-89`)
- Audit verdict (`Day 1 X1 bundle audit.md:53-60`): post-X1 bot is *"compact pressure baseline + no live overlay + contaminated benchmark-specific branches now removed"*. Clean, **not green** under original Done-when.
- `tools/exploit_check.py` shipped guard reports hardcoded constants — "PASS is meaningless" (`MANIFEST.md:129-133`).
- Current evidence is mostly HU/reference-bot while the tournament is 6-bot, 400-hand Swiss cumulative chip delta (`Day 1 X1 bundle audit.md:62-63`).

This is closer to "v0 baseline" than "v_final." The plan must reckon with that.

### Module-by-module wiring gaps (PokerBot-codex/src/, the canonical post-X1 code)

- `src/bot.py:183 decide()` → `run_with_budget` (`src/timeout_guard.py:25-37`) → `_decide_core` (`bot.py:92-100`) → preflop / postflop dispatch.
- **Preflop blueprint** (`src/preflop_lookup.py:25-29`): loads `data/preflop_blueprint.npz` (hand→score map). Lookup at `:33` is threshold-based, not action-sequence-conditional. `position` only branches open/free-option (`:41-45`); `action_seq` collapses to `facing_aggression` boolean (`:38`).
- **Postflop blueprint** (`src/postflop.py:20-25`): loads `data/flop_buckets.npz` and `data/flop_strategy.npz` **but never references them at decide-time**. `decide_postflop()` (`:30-53`) is pure pot/check/paired-card heuristic. The bucketed-strategy seam exists but is dead.
- **Equity** (`src/equity.py:14`): eval7 evaluator pre-warmed at import, but `bot.py` / `postflop.py` never call it on the decision path.
- **Opponent model** (`src/opponent_model.py:18-75`): tracks raise_rate / all_in_rate / fold_rate / call_rate + `high_pressure` / `fold_prone_pressure` boolean flags. **No posterior distribution over archetypes. No magnitude calculation.**
- **Overlay** (`src/bot.py:158-181`): only triggers on `high_pressure` or `fold_prone_pressure`. Hard hand-score thresholds (88/72/58) — no counter-exploit-cost math.
- **Sizing tree** (`src/sizing.py:7`): `{min_raise, third_pot, half_pot, two_third_pot, pot, two_x_pot, all_in}`. Preflop emits only `min_raise` (`preflop_lookup.py:42,46`); postflop bypasses `sizing_to_amount()` and hardcodes ~2/3 pot inline (`postflop.py:35-39`).
- **Extension points**: opponent posterior = no seam (replace singleton `_OPPONENT_MODEL`); finals-mode toggle = no seam (only `POKERBOT_DISABLE_OVERLAY` env var); fingerprint class = no factory.

### Canonical tool implementations (which file is real, which is stub)

Main worktree (`PokerBot/tools/`) is mostly stubs. `PokerBot-codex/tools/` holds the shipped release-branch code.

| Tool | Canonical | State |
|---|---|---|
| `benchmark.py` | `PokerBot-codex/tools/benchmark.py` (703 LOC) — paired seeds, manifest-pinned priors, ablation, self-play. | Real. Main is 96-LOC stub. |
| `h2h.py` | `PokerBot/tools/h2h.py` (121 LOC) — paired seeds, two orientations, bootstrap CI. | Real. Missing from codex worktree. |
| `exploit_check.py` | `PokerBot-codex/tools/exploit_check.py` (507 LOC) — 20-spot risk proxy with thresholds. | Real but proxy-only (hardcoded constants per X1 audit). Main is 39-LOC stub. Claude has a richer 339-LOC LBR-style alternative. |
| `self_play.py` | `PokerBot-codex/tools/self_play.py` (186 LOC) — supports `--bot` artifact, runs engine subprocess per batch. | Real. Main is 38-LOC stub. |
| `smoke_run.py` | `PokerBot-codex/tools/smoke_run.py` (194 LOC) — Docker-flagged sandbox runner. | Real. Main has a 127-LOC partial. |
| `replay.py` | None. 25-LOC TODO stub everywhere including release branch. | Patch-window playbook depended on this; resolved in W8 by retiring `replay.py` and adopting `analyze_hand_histories.py`. |
| `analyze_hand_histories.py` | `PokerBot-claude/tools/analyze_hand_histories.py` (211 LOC) — schema-introspecting, writes `data/finals_priors.npz`. | Only in claude worktree. Missing from codex and main. |
| `audit_strategy_leakage.py` | `PokerBot-codex/tools/audit_strategy_leakage.py` (109 LOC) shipped; `PokerBot-claude/tools/audit_strategy_leakage.py` (271 LOC) is richer source-or-zip AST audit. | Both real, different angles. |
| `promote_artifact.py` | `PokerBot-codex/tools/promote_artifact.py` (121 LOC) shipped; Claude's is fuller verification gate. | Both real. |

### Tournament spec invariants (`docs/tournament-spec.md`)

- Qualifier 2026-06-01: Swiss-system online, 400 hands/match, 6-bot tables, top 64 advance, ranked by cumulative chip delta (`:6-8, 54-56`). **Round count not stated in spec** — assumption of 3 rounds needs verification.
- Finals 2026-06-05: ~~single-elim bracket, UCL East, seeded from qualifier (`:9, 56`)~~ **OBSOLETE.** Corrected 2026-06-06: finals reset equal; Phase 1 is Swiss-paired 6-max cumulative chip performance with shrinkage on the top-6 cut, then Phase 2 final table (source of truth: `AGENTS.md` "Finals FORMAT" + 17:32 consult `prompt-exports/2026-06-04-173203-plan-optimise-next-90min-finals-bot.md`:9,14).
- Patch window 2026-06-02: JSON hand histories downloadable; one updated bot allowed before finals (`:8`).
- Runtime: Python 3.10, no network, 768MB, 0.5 CPU, read-only, 2s/decide, one 30s warmup (`:18-23`).
- Data: read from `data/` only at module import via `BOT_DATA_DIR` (`:23`).
- Pinned libs: `eval7==0.1.7`, `numpy==1.26.4`, `scipy==1.13.0`, `treys==0.1.8`, `scikit-learn==1.5.2` (`:26-31`).
- Reference bots: `template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2` (`:48-53`). **Reports flag these as saturated** — public bots already beat them in 300-hand smokes.

### Competitor evidence (from `docs/deep-research-report.md` and `docs/competitor-intel-analysis-2026-05-26.md`)

- **Public bots already beat bundled refs.** A green gauntlet vs `{template, aggressor, mathematician, shark, ref_bot_2}` does not predict top-64 finish.
- **Named threats** (with public GitHub repos):
  - **Neel** (`agrawalneel25/neel-work`) — 257-line bot, eval7 MC equity + preflop tables + pot-odds + occasional semi-bluffs. Memo claims +16287 over 5×300 vs `v_final`.
  - **Dominic** (`Linglingletsgo/blueprint-exploit-bot`) — `bot.py` + `blueprint.json`; preflop hand classes, street thresholds, SPR logic, profile overlays. Memo claims +12821.
  - **Famadeo** (`famadeo/main`) — long `codex_holdem` + `model.json` with feature_names/heads/n_samples/target. **Caveat: `runtime_enabled: false`** — loader returns None unless flipped. Memo claims +8270.
  - **Vladimir** (`vladimirfilip/main`) — recently pushed Deep CFR artefacts (`deep_cfr/` directories, GTO-model loader, MC fallback) as of 2026-05-25. Old "low threat" label is stale.
  - **Saroop** (`saroopjagdev/stable-stage18`) — claimed 4959-line staged bot with opponent classification, anti-punt layers, river variants, exploit multipliers. Unverified.
- **Five archetype patterns** the reports identified across the public field:
  - `range_mc_pot_odds` — preflop chart + Monte Carlo equity + pot-odds calls + fixed-threshold value bets.
  - `blueprint_threshold_exploit` — blueprint JSON + street thresholds + profile overlay.
  - `risk_gated_conservative` — survival heads, risk gates, range-conditioned equity.
  - `stage_variant_anti_punt` — staged decision pipeline, anti-punt layers.
  - `monte_carlo_basic` — equity-only MC bots.
- **Smoke-test rankings are noisy** (300-hand CI half-width > 5000 chips). 10k paired-seed is the minimum trustworthy unit.
- **Scoring metric ambiguity**: organiser site says "chip EV"; engine README + tournament spec say cumulative chip delta. **We use cumulative chip delta**.

### `/CodexCode` swarm mechanics (`~/.claude/commands/CodexCode.md`, `~/.claude/skills/codex-code/`)

- Invocation: `/CodexCode <task>`. `--fast` triggers fast mode (`CodexCode.md:40`).
- N agents: Claude decomposes and picks 1-50; default wave size 10 (`SKILL.md:72`; `swarm-config.json:24`).
- Worktrees: `/tmp/codex_worktrees/<sid>/agent_<i>/`, branch `codex-swarm-<sid>-agent-<i>` (`CodexCode.md:147-150`; `worktree_manager.sh:75`).
- Per-agent files: `/tmp/codex_swarm_<sid>_<i>_{prompt.txt, result.txt, events.jsonl, stdout.txt}`.
- Base agent command: `codex exec -m gpt-5.4 -c reasoning.effort=xhigh -c model_context_window=1000000 -c model_auto_compact_token_limit=900000 -c stream_idle_timeout_ms=300000 --full-auto --skip-git-repo-check --ephemeral --json --output-schema ~/.claude/skills/codex-code/settings/agent-output-schema.json -C "<worktree>" -o <result> - < <prompt> > <events.jsonl> 2>&1` (`CodexCode.md:222`).
- Required prompt structure: `YOUR SUBTASK / FILE OWNERSHIP / CONTEXT / WORKING DIRECTORY / CONSTRAINTS / EXPECTED OUTPUT` (`CodexCode.md:158, 204`).
- Synthesis: `parse_jsonl.py --summary` → `aggregate_results.py --pretty` → `worktree_manager.sh merge` (default strategy `diff-apply` — stage all, write patch, `git apply --check`, `git apply`).
- Token tracking: per-agent `input_tokens` / `output_tokens` from JSONL `turn.completed` events.
- Config drift: `CodexCode.md:222,468` hard-pins `gpt-5.4`; `SKILL.md:105` / `swarm-config.json:5` now say primary `gpt-5.5`, fallback `gpt-5.4`. Plan should use whichever wins at exec time.

### Codex native `/goal` mechanics (`~/.codex/config.toml`, `~/.codex/goals_1.sqlite`)

- Enabled by `[features] goals = true` (`config.toml:16`). Current model `gpt-5.5`, 1M context, `xhigh` effort, danger-full-access.
- `thread_goals(thread_id PK, goal_id, objective, status, token_budget, tokens_used, time_used_seconds, created_at_ms, updated_at_ms)`.
- Status enum: `active | paused | blocked | usage_limited | budget_limited | complete`.
- One `/goal` per thread (PK); multiple concurrent threads globally (DB currently has 2 active rows from real prior runs).
- Resume: `codex resume --last` or `codex resume <SESSION_ID>`. Sessions at `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<thread_id>.jsonl`. Summaries at `~/.codex/memories/rollout_summaries/*.md`.

### GitHub change-detection primitive (for daily 6am cron)

- **Cleanest signal**: `git ls-remote <repo-url> HEAD refs/heads/main refs/heads/master` — compare returned SHA against last-stored SHA per repo. Zero API quota, no clone required for detection.
- For file-level diff after SHA change: `gh api repos/<owner>/<repo>/compare/<old>...<new>` or shallow `git clone --depth=1` + diff.
- `gh` CLI present: `/opt/homebrew/bin/gh` v2.72.0.
- No existing `~/.claude/skills/loop/` or `~/.claude/skills/schedule/` skill directories. Native macOS scheduling = launchd plist in `~/Library/LaunchAgents/`. The two `com.local.lol-*.plist` files in that directory are existing user-defined launchd jobs and can serve as templates.

### Prior art (and contradictions)

- `docs/playbooks/hardening.md` defines the pre-submission gauntlet but **only names 4 templates** while spec includes 5 (`ref_bot_2` missing).
- `docs/playbooks/patch-window.md` assumes `tools/replay.py` parses hand histories — but `replay.py` is a TODO stub everywhere. `AGENTS.md:93-98` says use `tools/analyze_hand_histories.py` (Claude has 211 LOC; codex/main don't).
- `PokerBot-claude/findings/claude-refbot-leaks.md` empirically characterized the 5 ref bots (50×200 hands, seeds 42-91) with concrete leak descriptions — useful but assumes overlay is live (post-X1 contradiction).
- Corpus has: CFR (Zinkevich 2007), Libratus (Brown/Sandholm 2017), Pluribus (Brown/Sandholm 2019), Cepheus (Bowling 2015), MCCFR (Lanctot 2009), DeepCFR (Brown 2019 — read-only). **Missing**: LBR (Lisý/Bowling 2017) vault note; opponent-modelling literature note (Billings/Davidson/Schauenberg planned, never built).

### Worktree policy (CLAUDE.md / AGENTS.md)

- `~/Code/PokerBot/` is canonical `main`. No agent edits during overnight runs.
- `~/Code/PokerBot-claude/` is Claude's worktree (branch `claude`). Bias per `PROMPT.claude.md`: harness, hardening, exploit overlay, tournament tooling, patch-window readiness.
- `~/Code/PokerBot-codex/` is Codex's worktree (branch `codex`). Bias per `PROMPT.codex.md`: compact lookup tables, parameter sweeps, training pipelines, benchmark automation, exploit-check improvements.
- No agent edits `ext/fullhouse-engine/`, `.venv/`, another agent's worktree, or `main` during overnight runs.
- No agent runs `pip install` unattended.

## Approach

Three concurrent tracks anchored on the X1-audit reality that the post-X1 bot is "compact pressure baseline + no live overlay + contaminated branches removed" (Background § "Current bot reality"):

1. **R1 → R4 staircase climbed by overnight `/CodexCode` swarms.** Claude in `PokerBot-claude` decomposes each rung into 4-8 parallel agent subtasks, spawns isolated temp worktrees per `~/.claude/skills/codex-code/`, and synthesizes winning diffs back into `PokerBot-codex/src/`. Every rung is gated by the new R1 benchmark surface — no "we beat X" claim ships without paired-seed 95 % CI > 0 from that surface. `release/v_final-e4b4a8f1` (STATUS § "Independent arbitration audit…") remains the rollback floor; we ship the highest-rung that passes hardening if anything later regresses.
2. **Native Codex `/goal` slow-cook in `PokerBot-codex`** for long-horizon work that exceeds a 1-2 hr swarm wave: postflop CFR+ over flop buckets (the dead `data/flop_strategy.npz` seam at `PokerBot-codex/src/postflop.py:20-25`), archetype-conditional preflop refinement, MCCFR over the discrete sizing tree at `PokerBot-codex/src/sizing.py:7`. One `/goal` thread per long-horizon task; deliverables are compact `data/*.npz` artifacts pinned by sha256 in `submissions/manifest.json`. Codex worktree doubles as the merge destination for winning swarm artifacts (Background Q4 resolved: both roles).
3. **Daily 6am competitor-intel cron** via launchd plist in `~/Library/LaunchAgents/` (templates: existing `com.local.lol-*.plist`). Detection primitive is `git ls-remote <url> HEAD refs/heads/main refs/heads/master`, compared against per-repo last-known SHAs in the manifest — zero API quota. Watchlist alerting on key flips (Famadeo `bots/codex_holdem/data/model.json:runtime_enabled false→true`, Saroop variant-default drift, Vladimir's `bots/vlad/deep_cfr/` artefact reachability). On change: shallow-clone, diff, write artifact to `consults/<date>/intel/`, auto-trigger the appropriate `tools/benchmark.py --six-max-mix` slice (Background § "GitHub change-detection primitive").

Two timeline-parallel sub-tracks:

- **Patch-window readiness (2026-06-02)**: retire the `tools/replay.py` stub everywhere (it's a TODO stub in all worktrees per Background § "Canonical tool implementations"), redirect `docs/playbooks/patch-window.md` to `tools/analyze_hand_histories.py` (211 LOC, working, only in `PokerBot-claude/tools/`), rehearse the 24 h tune-and-resubmit against a synthetic-history fixture.
- **Monte-Carlo Swiss qualifier simulator**: validates the "near-guarantee" claim by running ≥ 1000 simulated tournaments over the R1 field-mix with a 3/5/7-round sweep (Background Q2: round count is unknown), reporting top-64 admission per candidate bot variant.

**Elegance constraint enforcement** (Background § "Locked decisions"): every merged module must (a) carry a `# Source: [[note-name]]` comment, (b) demonstrate a measured benchmark gain on the R1 surface, (c) survive a "delete and re-benchmark" ablation showing it owns ≥ +1 bb/100 against at least one seat, (d) keep `tools/exploit_check.py` LBR under the 100/200 mbb/g cap. **Online-research clause**: each swarm wave begins with a literature-survey turn whose citations land in the wave's `consults/<date>/MANIFEST.md`.

**Final hardening** (`tools/import_audit.py` + `pytest tests/edge_cases` + real LBR cap + `tools/smoke_run.py` + engine validator + `--six-max-mix` CI > 0) gates the qualifier upload. The qualifier zip ships only when R4 + full hardening are green; otherwise we ship the highest-R-rung that clears hardening, with `release/v_final-e4b4a8f1` as the irreducible fallback.

**Timeline triage (6 days to 2026-06-01 qualifier).** At W5+W7+W9 stated cadence the lower-bound overnight time is ~42 h; available is ~50 h over 5 nights, *before* the ≥ 1 wall-day W1+W3 prep that gates the first overnight wave. Plan therefore demotes three items:
- **W2 (cron)** → cut to a one-shot manual `git ls-remote` SHA check on the morning of 2026-05-31 (~5 % of build cost, ~80 % of the value over the qualifier window).
- **W6 (simulator)** → deferred to post-qualifier finals prep. R1 per-opponent CIs already tell us whether we beat the field; the simulator validates the *near-guarantee* claim but does not change which artifact ships.
- **W4 (loop infra)** → halved: a 1-page playbook, no dry-run swarm.
Targets: v_R2 lands by 2026-05-29; v_R3+v_R4 attempted as a single combined wave 2026-05-30 → 2026-05-31. **Hard cutoff: 2026-05-31 23:59 UTC** — `## STOPPED AT R<n>` block in STATUS.md per `PROMPT.shared.md`, package highest passing rung.

---

## Work Items

Ordered by earliest-needed-first. Each item lists: **Goal**, **Done when**, **Key files**, **Dependencies**, **Size**, **Owner-suggestion**, **Citation expectation**.

### W1 — Lock R1 baseline: tournament-mimicking benchmark + current numbers

**Goal:** Replace the contaminated bundled-reference gauntlet (`STATUS.md:234-242` headline numbers, which Background flags as superseded) with a Swiss-shape, 6-bot, 400-hand, paired-seed evaluator over 5 behavior-matched archetype seats + 5 cloned named public bots + the 5 bundled refs. Record current `release/v_final-e4b4a8f1` artifact numbers as the R1 baseline.

**Done when:**
- `ext/public-bots/{neel,dominic,famadeo,vladimir,saroop}/` are read-only clones of upstream HEAD; manifest schema pinned at:
  ```json
  // submissions/manifest.json:competitor_clones
  {
    "<name>": {
      "url": "<https://github.com/...>",
      "last_seen_sha": "<40-char SHA>",
      "last_seen_iso": "<UTC ISO-8601>",
      "bot_path": "<path/to/bot.py inside their repo>",
      "data_paths": ["<path/to/blueprint.json>", ...],
      "debug_fork": false
    }
  }
  ```
  Reference: Background § "Adversary surface"; `docs/public-competitor-intel-2026-05-24.md` § "Source Links".
- `tools/archetypes/{range_mc_pot_odds,blueprint_threshold_exploit,risk_gated_conservative,stage_variant_anti_punt,monte_carlo_basic}/bot.py` exist, validator-PASS, behavior-matched (not code-copied) per `docs/public-competitor-intel-2026-05-24.md` § "Recommended Defensive Benchmarks". **Calibration target per archetype**: each must produce action-frequency vectors (VPIP, PFR, c-bet, fold-to-c-bet, 3-bet, all-in rate) within ±10 absolute percentage points of the reference patterns documented in the deep-research report's archetype tables, measured across ≥ 1000 hands of self-vs-template at seed 42. Calibration evidence lands at `tools/archetypes/<name>/CALIBRATION.md`. Each archetype carries a `# Source: [[note-name]]` comment for any modelled mechanic.
- `tools/benchmark.py --six-max-mix` runs ≥ 4 compositions × ≥ 200 matches × 400 hands paired-seed seat-swap with bootstrap 95 % CI; per-opponent bb/100 + CI emitted; manifest-pinned competitor SHAs verified before each run.
- `tools/analyze_hand_histories.py` ported from `PokerBot-claude/tools/analyze_hand_histories.py:1-211` into `PokerBot-codex/tools/`; the matching `tools/replay.py` stub in all worktrees deleted or replaced by a hard-fail-on-import redirect.
- R1 artifact at `consults/2026-05-26-r1-baseline/MANIFEST.md` records per-opponent numbers + CI, competitor clone SHAs, invocation arg-strings, environment, and a "supersedes `STATUS.md:234-242` headline gauntlet" header. Modelled on `PokerBot-codex/consults/day1_x1/MANIFEST.md`.

**Key files:**
- `tools/benchmark.py` (extend; canonical `PokerBot-codex/tools/benchmark.py:1-703`)
- `tools/archetypes/*` (new tree)
- `ext/public-bots/*` (new clones, gitignored)
- `tools/analyze_hand_histories.py` (port; canonical `PokerBot-claude/tools/analyze_hand_histories.py:1-211`)
- `submissions/manifest.json` (extend with `competitor_clones` block)
- `consults/2026-05-26-r1-baseline/MANIFEST.md` (new)

**Dependencies:** none — earliest needed.
**Size:** L (~16 p-hours; collapses to ~1 wall-clock day via 4-agent `/CodexCode` swarm).
**Owner-suggestion:** `/CodexCode` swarm from `PokerBot-claude`. Suggested 4-agent split: A = archetype seats, B = `--six-max-mix` evaluator + paired-seed seat-swap, C = public-bot cloner + integration tests, D = analyzer port + baseline run + MANIFEST. Synthesis by Claude main.
**Citation expectation:** `[[Pluribus-Brown-Sandholm-2019]]` (discrete sizing tree in archetypes), `[[Engine-Fullhouse]]` (ref-bot characterization), `[[MCCFR-Lanctot-2009]]` (paired-seed variance rationale). In-doc refs: `docs/competitor-intel-analysis-2026-05-26.md` Tier-1/Tier-2 list; `docs/tournament-spec.md:54-56` Swiss shape; `docs/public-competitor-intel-2026-05-24.md` archetype taxonomy.

---

### W2 — Competitor-intel SHA snapshot *(triaged for qualifier; full cron deferred to finals prep)*

**Goal:** Detect upstream changes in cloned competitor repos before qualifier without burning the ~6 p-hr build of a full daily cron. Full launchd cron + auto-rebenchmark + watchlist alerting is deferred to the 2026-06-02 → 2026-06-05 finals prep window.

**Done when (triaged version):**
- One-shot script `tools/competitor_intel_snapshot.sh` (new, ~30 LOC): for each repo in `submissions/manifest.json:competitor_clones`, run `git ls-remote <url> HEAD refs/heads/main refs/heads/master`; if SHA differs from `last_seen_sha`, shallow-clone the new HEAD into `ext/public-bots/<name>/` and update the manifest entry.
- Watchlist diff inspection done manually on the morning of 2026-05-31: cat `bots/codex_holdem/data/model.json:runtime_enabled` (Famadeo), `bots/mybot/bot.py` default variant constant (Saroop), `bots/vlad/deep_cfr/` directory existence (Vladimir).
- One-shot rebenchmark on changed competitors via `tools/benchmark.py --six-max-mix --filter <name>` if any of the above flipped state.
- Single artifact `consults/2026-05-31-intel-snapshot/MANIFEST.md` records what changed and what was rebenched.

**Done when (post-qualifier full cron, deferred to 2026-06-02):**
- `~/Library/LaunchAgents/com.local.pokerbot-competitor-intel.plist` (templates: existing `com.local.lol-*.plist`), daily 06:00 local, runs the script automatically, writes alert artifacts on flips, fires auto-rebenchmark. Spec'd here so 2026-06-02 finals prep can lift it.

**Key files:**
- `tools/competitor_intel_snapshot.sh` (new, qualifier scope)
- `submissions/manifest.json:competitor_clones` (W1's block)
- `consults/2026-05-31-intel-snapshot/MANIFEST.md` (one-shot artifact)
- *(deferred)* `~/Library/LaunchAgents/com.local.pokerbot-competitor-intel.plist`, `tools/competitor_intel.sh`, `cron_runs` manifest block

**Dependencies:** W1 (manifest's `competitor_clones` schema must exist).
**Size:** S triaged (~30 min on 2026-05-31 morning); M deferred (~6 p-hr post-qualifier).
**Owner-suggestion:** Claude main thread in `PokerBot-claude`.
**Citation expectation:** No corpus citation (infrastructure). In-doc reference: Background § "GitHub change-detection primitive".

---

### W3 — Wiring completion: postflop blueprint, equity at decide-time, real LBR, archetype posterior, finals toggle

**Goal:** Close the five wiring gaps in `PokerBot-codex/src/` (Background § "Module-by-module wiring gaps") so subsequent R-climbs have real surface area to optimize. The current bot has dead seams (postflop blueprint loaded but unreferenced; equity evaluator pre-warmed but never called on the decision path) and proxy gates (`tools/exploit_check.py` is no longer a constants stub but a per-spot hardcoded risk-lookup table — still a proxy, not real LBR).

**Done when** *(four sub-deliverables; partial merge allowed with documented sub-rollback per `tools/promote_artifact.py`):*
- **Postflop:** `src/postflop.py:decide_postflop()` consults `_flop_buckets` + `_flop_strategy` (the dead seam at `PokerBot-codex/src/postflop.py:20-25`) when artifacts are present; falls back to current heuristic when absent; measured gain ≥ +1 bb/100 against ≥ 1 W1 seat with CI > 0.
- **Equity at decide-time:** `src/equity.py:equity_vs_range()` called from at least the turn and river decision paths in `src/postflop.py`; remaining budget checked via `src/timeout_guard.py:run_with_budget()`. The only hard budget is the engine's 2 s/decide — caching, batching, and per-call cost are implementer choices.
- **Real LBR (not proxy):** `tools/exploit_check.py` replaces the current per-spot hardcoded `risk` lookup tables (`PokerBot-codex/tools/exploit_check.py:60-150` — note the older `[12,18,22,15,20]` literal constants flagged in `MANIFEST.md:129-133` were already removed per KANBAN 2026-05-22; the residual proxy is the per-spot risk table) with computed local best-response values per Lisý & Bowling 2017. Design budget (sample count, depth limit, chance-node sampling, source of policy randomization given current `decide()` is deterministic) is the implementer's call; minimum requirement is reproducibility across two seeds with the same suite spec, documented in a one-page `consults/<date>/R3/lbr-design.md`.
- **Archetype posterior:** `src/opponent_model.py:OpponentModel.pressure_features()` (currently returns booleans `high_pressure`/`fold_prone_pressure` at `PokerBot-codex/src/opponent_model.py:18-75`) is replaced by `archetype_features()` returning `{archetype_posterior: dict[str, float], n_observations: int, deviation_bound: float}`, where (a) the five posterior labels match W1's `tools/archetypes/` names, (b) `deviation_bound` is the per-feature maximum percentage-point shift the overlay may apply to the blueprint mix (derived from R1 numbers in W5, not legislated up front), (c) posterior uses observed action frequencies only — no identity strings — must clear `tools/audit_strategy_leakage.py`.
- **Legitimacy gate:** `tools/benchmark.py --ablate-overlay` (rewritten so it no longer targets aggressor-only; uses W1's archetype suite) shows ≥ +3 bb/100 gain against the R1 surface with CI lower bound > 0. This is the elegance-constraint (b)+(c) check for the overlay as a whole.

*(The earlier `POKERBOT_REGIME` qualifier-vs-finals regime toggle is removed from this work item — no W2-W10 item sets or asserts it, and finals (2026-06-05) sits outside this plan's scope. A separate finals-prep plan post-qualifier will own the regime split.)*

**Key files:**
- `PokerBot-codex/src/postflop.py:30-53` (postflop)
- `PokerBot-codex/src/equity.py:1-50` (equity wiring)
- `PokerBot-codex/tools/exploit_check.py:1-507` (full rewrite ~280-350 LOC; reference scaffold at `PokerBot-claude/tools/exploit_check.py` 339 LOC)
- `PokerBot-codex/src/opponent_model.py:18-75` (posterior + `deviation_bound`)
- `PokerBot-codex/tools/benchmark.py:217-219` (replace aggressor-only `_run_ablation()`)

**Dependencies:** W1 (need the R1 surface to gate the ablation legitimately; archetype names must match for the posterior labels).
**Size:** L (~24 p-hours; subdivides cleanly across a 5-agent swarm by file).
**Owner-suggestion:** `/CodexCode` swarm from `PokerBot-claude`; 5 agents, one per sub-deliverable. The real-LBR sub-task is the largest single piece; consider spinning it as a `PokerBot-codex` native `/goal` thread if the swarm wave runs long.
**Citation expectation:** `[[Cepheus-Bowling-2015]]` (bucketed CFR+ for postflop), `[[Libratus-Brown-Sandholm-2017]]` (blueprint + bounded refinement framing for the magnitude cap), **Lisý & Bowling 2017 arXiv:1612.07547 (LBR)** — *build the missing vault note `Agentic/05 Research/PokerBot/LBR-Lisy-Bowling-2017.md` as part of this work item*, since Background flags it as missing. In-doc reference: `docs/playbooks/hardening.md` LBR thresholds (≤ 100/200 mbb/g).

---

### W4 — Overnight loop playbook *(triaged — 1-page, no dry-run)*

**Goal:** Make R2/R3/R4 climbs runnable as repeatable overnight waves with the minimum documented protocol needed before the first wave fires. Full multi-doc loop infrastructure (separate `/goal` blueprint spec doc, consults-manifest template doc, dry-run smoke) is deferred to finals prep.

**Done when:**
- `docs/playbooks/overnight-loop.md` (new, ≤ 1 page) documents in one file: literature-survey step (online-research clause); `/CodexCode <task>` invocation with required prompt structure `YOUR SUBTASK / FILE OWNERSHIP / CONTEXT / WORKING DIRECTORY / CONSTRAINTS / EXPECTED OUTPUT` (per `~/.claude/commands/CodexCode.md:158,204`); elegance-constraint enforcement (cite-then-implement, measured gain, ablation survival, LBR cap); synthesis strategy (`worktree_manager.sh merge` default `diff-apply`); native Codex `/goal` slow-cook objective template (compact `data/*.npz` deliverable, sha256-pinned, resume via `codex resume --last`); consult-bundle skeleton (modelled on `PokerBot-codex/consults/day1_x1/MANIFEST.md:1-50`).
- No dry-run wave required; W5's first real R2 wave validates the loop end-to-end.

**Key files:**
- `docs/playbooks/overnight-loop.md` (new, ≤ 1 page)
- Read-only references: `~/.claude/commands/CodexCode.md`, `~/.claude/skills/codex-code/`, `~/.codex/config.toml`, `~/.codex/goals_1.sqlite`

**Dependencies:** none — parallel with W1; **must complete before W5** (R2 needs the loop documented).
**Size:** S triaged (~3 p-hours).
**Owner-suggestion:** Claude main thread in `PokerBot-claude` (orchestration documentation; matches `PROMPT.claude.md` P1 bias).
**Citation expectation:** No corpus citation (process docs). In-doc reference: Background §§ "`/CodexCode` swarm mechanics", "Codex native `/goal` mechanics"; `PokerBot-codex/consults/day1_x1/MANIFEST.md` as the canonical worked example.

---

### W5 — R2 climb: field-beating against ≥ 85-90 % of the R1 surface

**Goal:** Iterate overnight waves on top of W3 wiring to produce a bot that hits R2: strict-positive 95 % CI cumulative-chip-delta vs ≥ 85-90 % of the 15-seat W1 surface (5 archetypes + 5 named bots + 5 bundled refs), zero crashes / timeouts / illegal actions.

**Done when:**
- New artifact `submissions/v_R2.zip` promoted via `tools/promote_artifact.py` (and `best_green.zip` copied; per `submissions/manifest.json` schema).
- `tools/benchmark.py --six-max-mix --hands 50000 --paired-seed-base 42 --bot submissions/v_R2.zip`: ≥ 85 % of 15 seats have bb/100 > 0 with CI lower bound > 0; remaining seats not worse than `release/v_final-e4b4a8f1` by > 3 bb/100.
- `tools/exploit_check.py` (real LBR from W3) PASS: preflop ≤ 100 mbb/g, aggregate ≤ 200 mbb/g.
- `tools/smoke_run.py --zip submissions/v_R2.zip --hands 200` exit 0, no errors.
- Each merged sub-improvement satisfies the elegance constraint: `# Source: [[note-name]]` comment, measured gain on R1 surface, survives delete-and-rebench ablation (≥ +1 bb/100 ownership on ≥ 1 seat).
- `consults/<date>/R2/MANIFEST.md` per wave records: which subtask, which paper, which artifact sha256, which delta, which kept-or-rolled-back. Final wave's MANIFEST is the R2 lock document.

**Key files:**
- Whatever the swarm touches in `PokerBot-codex/src/` per wave; final merge target is `PokerBot-codex`
- `submissions/v_R2.zip`, `submissions/manifest.json`
- `consults/<date>/R2/MANIFEST.md` (one per wave)

**Dependencies:** W1 (benchmark surface), W3 (wiring), W4 (loop infra). W2 (cron) helpful but not blocking.
**Size:** L (3-5 overnight waves × ~6 wall-clock hours each).
**Owner-suggestion:** `/CodexCode` swarm from `PokerBot-claude`; any long-horizon blueprint subtask delegated to `PokerBot-codex` native `/goal` per W4.
**Citation expectation:** Each merged technique cites its corpus note: `[[CFR-Zinkevich-2007]]`, `[[MCCFR-Lanctot-2009]]`, `[[Cepheus-Bowling-2015]]`, `[[Pluribus-Brown-Sandholm-2019]]`, `[[Libratus-Brown-Sandholm-2017]]`, `[[Engine-Fullhouse]]` as applicable. Online-research clause: each wave begins with a literature-survey turn; links land in the wave's MANIFEST.

---

### W6 — Monte-Carlo Swiss qualifier simulator *(deferred to post-qualifier finals prep)*

**Goal:** Quantify top-64 admission probability per candidate bot variant under realistic Swiss field-mix. Useful for validating the "near-guarantee" claim and for tuning the finals-bracket strategy — but does NOT change which artifact ships in the 2026-06-01 qualifier. R1's per-opponent CIs (W1) already tell us if we beat the field.

**Done when (post-qualifier):**
- `tools/qualifier_simulator.py` (new) runs ≥ 1000 simulated tournaments per cell. Round count and field-size sweep design left to implementer once the actual qualifier results land (which removes most of the round-count uncertainty).
- Edge inputs loaded from the actual 2026-06-01 standings + R1 baseline.
- Output `consults/<date>/simulator/MANIFEST.md`.

**Dependencies:** W1, 2026-06-01 qualifier completion.
**Size:** M (~10 p-hours), to be done 2026-06-02 → 2026-06-04.
**Owner-suggestion:** `PokerBot-codex` native `/goal` thread.
**Citation expectation:** None (engineering). Background Q2 (round count) becomes mooted by actual qualifier data.

---

### W7 — R3 climb: top-tier-beating (Vladimir, Famadeo-if-runtime-on, Saroop, mystery-strong)

**Goal:** Iterate on R2 to a bot that hits R3: strict-positive 95 % CI vs the top-tier set — Vladimir's current Deep CFR `bots/vlad/`, Famadeo's `bots/codex_holdem/` with `runtime_enabled` forced true *for benchmark only*, Saroop's `bots/mybot/`, and a new `tools/archetypes/mystery_strong/` composed adversarially from the strongest sub-techniques surfaced during R2.

**Done when:**
- `tools/archetypes/mystery_strong/bot.py` created post-R2 by composing the strongest *winning* techniques from R2 swarm waves into a single adversarial seat (red-team-by-our-own-best, so we're stressed by the strongest version of ourselves that R2 surfaced); validator-PASS; **explicitly NOT shipped** in any submission archive (lives only under `tools/archetypes/` and `ext/public-bots/` analogs).
- `ext/public-bots/famadeo_runtime_on/` exists as a debug fork with `bots/codex_holdem/data/model.json:runtime_enabled` patched to `true`; gitignored; pinned in manifest with an explicit `debug_fork: true` flag and rationale ("upstream `runtime_enabled` is false per `docs/public-competitor-intel-2026-05-24.md`; this fork measures the worst-case threat from Famadeo flipping it"). The cron (W2) alerts on the upstream flip independently.
- `submissions/v_R3.zip` clears `tools/benchmark.py --six-max-mix --opponents vladimir,famadeo_runtime_on,saroop,mystery_strong --hands 50000 --paired-seed-base 42`: bb/100 > 0 with CI lower bound > 0 on ≥ 3 of 4; the 4th not worse than 0 by > 5 bb/100.
- R2 numbers preserved on the W1 surface (no regression > 3 bb/100 against any seat that R2 had at CI > 0).
- LBR + smoke + validator + `audit_strategy_leakage.py` all PASS (extend the leakage word list to cover `neel`, `dominic`, `famadeo`, `vladimir`, `vlad`, `saroop`, `mystery_strong`, and the archetype seat names).

**Key files:**
- `tools/archetypes/mystery_strong/` (new, post-R2)
- `ext/public-bots/famadeo_runtime_on/` (debug fork, gitignored)
- `submissions/v_R3.zip`, `submissions/manifest.json`
- `consults/<date>/R3/MANIFEST.md`
- `tools/audit_strategy_leakage.py` (extend word list; canonical `PokerBot-codex/tools/audit_strategy_leakage.py:21-43`)

**Dependencies:** W5 (R2 must land; `mystery_strong` is composed from R2-winning techniques), W2 (cron should have surfaced current Vladimir/Saroop HEADs).
**Size:** L (2-4 overnight waves).
**Owner-suggestion:** `/CodexCode` swarm from `PokerBot-claude`. `mystery_strong` construction itself is a discrete one-shot agent task.
**Citation expectation:** `[[DeepCFR-Brown-2019]]` (read-only — to *understand* Vladimir's threat model; corpus index flags Deep CFR as out-of-implementation-scope); `[[Libratus-Brown-Sandholm-2017]]` (subgame-solving framing for range-conditioned bots like Famadeo); newly-built `[[LBR-Lisy-Bowling-2017]]` vault note from W3.

---

### W8 — Patch-window readiness: retire `replay.py`, adopt `analyze_hand_histories.py`, rehearse 24 h protocol

**Goal:** Make the 2026-06-02 patch window executable end-to-end. Resolve Background Q5 (`replay.py` vs `analyze_hand_histories.py`) by committing to the recommended path (retire stub; adopt analyzer). Patch the 4-vs-5-template inconsistency in `docs/playbooks/hardening.md`.

**Done when:**
- `tools/replay.py` deleted in all worktrees, or replaced by a 5-line hard-fail-on-import shim pointing to `tools/analyze_hand_histories.py`.
- `tools/analyze_hand_histories.py` (ported into `PokerBot-codex` in W1) verified to schema-introspect a synthetic 200-hand JSON fixture; the analyzer does *not* hardcode field names (per Background's repeated note that the 2026-06-02 schema is unknown).
- `docs/playbooks/patch-window.md` rewritten: all `replay.py` references replaced by `analyze_hand_histories.py`; explicit "edit only `src/opponent_model.py` priors and `data/finals_priors.npz`; baseline strategy edits forbidden"; explicit reference to `tools/promote_artifact.py` as the only path that may write `submissions/v_finals.zip`.
- `docs/playbooks/hardening.md` § 3 updated: "all four templates" → "all five reference bots (`template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2`)" per `docs/tournament-spec.md:48-53`.
- **Dress rehearsal:** generate a synthetic finals-fixture JSON via a self-play export of the R-rung-current bot vs the 5 archetype seats; run `tools/analyze_hand_histories.py` to produce `data/finals_priors.npz`; swap into a forked `submissions/v_finals_rehearsal.zip`; re-run full hardening + W1 surface; assert no W1 seat regresses > 2 bb/100. Artifact discarded; rehearsal log preserved at `consults/<date>/patch-window-rehearsal/MANIFEST.md`.

**Key files:**
- `tools/replay.py` (delete or stub-fail)
- `tools/analyze_hand_histories.py` (verify; ported in W1)
- `docs/playbooks/patch-window.md` (rewrite)
- `docs/playbooks/hardening.md` § 3 (5-template fix)
- `submissions/v_finals_rehearsal.zip` (disposable rehearsal artifact)
- `consults/<date>/patch-window-rehearsal/MANIFEST.md` (new)

**Dependencies:** W1 (analyzer port + R1 surface for rehearsal).
**Size:** S (~4 p-hours including the rehearsal).
**Owner-suggestion:** `PokerBot-claude` worktree, Claude main thread (matches `PROMPT.claude.md` P5 explicit: "patch-window readiness").
**Citation expectation:** No corpus citation (playbook + tooling). In-doc references: Background § "Prior art (and contradictions)" for both the `replay.py` and 4-vs-5-template fixes; `docs/tournament-spec.md:8` for the patch-window allowance.

---

### W9 — R4 margin lock: calibrate N, hit lower-bound ≥ N against the R3 set, validate near-guarantee

**Goal:** Iterate R3 → R4: CI lower bound ≥ N bb/100 above zero against the R3 top-tier set, where N is *calibrated* during this item rather than committed prematurely. Resolves Background Q1.

**Done when:**
- **N calibration committed first, against the R3 tier (not the soft tier):** fix N by reading the R1 baseline distribution among the *R3 top-tier seats* (Vladimir, Famadeo-on, Saroop, mystery_strong) and choosing N such that `release/v_final-e4b4a8f1` shows CI lower bound near zero against the median R3 seat — N is the gap we have to *climb* on the hard tier, not on the soft tier. Background's candidate of 50 bb/100 is a guidepost; actual N may land at 30 or 80 depending on the R1 spread on the R3 set. Documented in `consults/<date>/R4/calibration.md` with the R1 R3-tier numbers and the chosen N.
- `submissions/v_R4.zip` clears `tools/benchmark.py --six-max-mix --opponents <R3-set> --hands 100000 --paired-seed-base 42` with CI lower bound ≥ N on ≥ 3 of 4 R3 seats.
- *(Optional, only if W6 has been promoted from deferred)* Monte-Carlo simulator re-run with `v_R4.zip`'s edge profile shows top-64 admission ≥ 0.90 with CI lower bound ≥ 0.85 — the "near-guarantee" gate. If W6 stays deferred, this gate is replaced by the R1+R3 CI gates alone.
- LBR + smoke + validator still PASS.
- R3 + R2 numbers preserved (no regression > 3 bb/100 anywhere on the W1 surface).

**Key files:**
- Whatever the swarm touches in `PokerBot-codex/src/`
- `submissions/v_R4.zip`, `submissions/manifest.json`
- `consults/<date>/R4/MANIFEST.md` + `consults/<date>/R4/calibration.md`

**Dependencies:** W7 (R3 must land). W6 (simulator) is *not* a hard prerequisite under triaged timing; if W6 is deferred post-qualifier, the simulator-gate becomes optional and W9's acceptance falls back to R1+R3 CI gates.
**Size:** L (2-3 overnight waves + calibration analysis).
**Owner-suggestion:** `/CodexCode` swarm from `PokerBot-claude`; calibration analysis (the N-fixing decision) by Claude main thread before the swarm fires.
**Citation expectation:** Same techniques-cite-papers expectation as W5/W7. The N calibration itself is empirical (no paper cited; just R1 numbers + a documented rule).

---

### W10 — Final hardening + package: qualifier upload gate

**Goal:** Package the highest-rung-passing bot as `submissions/v_qualifier.zip`, gate it on the full hardening gauntlet against the new R1 surface, freeze its sha256 in the manifest, and leave `release/v_final-e4b4a8f1` intact as the irreducible fallback.

**Done when:**
- Source-of-record decision recorded in `submissions/manifest.json`: which R-rung artifact (v_R4 ideally, else v_R3, else v_R2; never below v_R2 unless STATUS marks `## STOPPED AT R<n>` per `PROMPT.shared.md` block).
- `python tools/import_audit.py` PASS — cold < 1.5 s, RSS < 400 MB, no forbidden imports per `docs/tournament-spec.md:33-40`.
- `pytest tests/edge_cases -x` PASS — coverage extended for: 6-max ICM-like late-stage, malformed history payload during patch-window simulator, archetype-vs-archetype heads-up bust scenarios. `tests/edge_cases/test_safe_fallback.py` + `test_legal_actions.py` + `test_hardening_cases.py` baseline maintained.
- `python tools/exploit_check.py` (real LBR from W3) PASS — preflop ≤ 100 mbb/g, aggregate ≤ 200 mbb/g.
- `python tools/smoke_run.py --zip submissions/v_qualifier.zip --hands 200` — exit 0, no errors, ≥ 90 % hands played (per `PROMPT.shared.md` Done-when #6).
- `python ext/fullhouse-engine/sandbox/validator.py submissions/v_qualifier.zip` — PASSED on all 4 TEST_STATES.
- `python tools/benchmark.py --six-max-mix --hands 50000 --paired-seed-base 42 --bot submissions/v_qualifier.zip` — CI > 0 against ≥ 85 % of the 15-seat W1 surface.
- `python tools/audit_strategy_leakage.py --zip submissions/v_qualifier.zip` PASS — zero forbidden tokens; word list extended to include all archetype + competitor names per W7.
- `submissions/manifest.json` updated with new entry: `v_qualifier`, sha256, source-of-record R-rung, promotion sha matches. Pre-commit hook (`.githooks/pre-commit`) validates and lands.
- STATUS.md gains `## QUALIFIER PACKAGED` block in the `PROMPT.shared.md` proof-of-green format: artifact sha, R-rung, headline R1 numbers, simulator admission probability, hardening line-items, citation per gate.
- `release/v_final-e4b4a8f1` HEAD `a00561c` is byte-identical-untouched (verified by re-running its `git diff` against `main`).

**Key files:**
- `tools/import_audit.py`, `tools/exploit_check.py`, `tools/smoke_run.py`, `tools/audit_strategy_leakage.py`, `tools/promote_artifact.py` (read + run; canonical paths in `PokerBot-codex/tools/`)
- `ext/fullhouse-engine/sandbox/validator.py` (read-only)
- `submissions/v_qualifier.zip`, `submissions/manifest.json`
- `STATUS.md` (append-only)

**Dependencies:** W9 (highest-rung artifact must exist; if R4 misses, fall back to R3 artifact and STATUS records `## STOPPED AT R3`). W8 (hardening.md 5-template fix must be in before the gauntlet runs against the updated spec).
**Size:** S (~3 p-hours; mostly running the gauntlet + recording).
**Owner-suggestion:** Claude main thread in `PokerBot-claude` (final orchestration; matches `PROMPT.claude.md` P0/P1 bias on legal action + verification harness).
**Citation expectation:** `[[Engine-Fullhouse]]` for hardening sources (validator, edge cases, sandbox invariants); newly-built `[[LBR-Lisy-Bowling-2017]]` for the LBR cap rationale. In-doc reference: `docs/playbooks/hardening.md` (updated by W8) as the canonical pre-submission playbook.

---

## Open Questions

Background's five open questions are resolved in-plan: Q1 → W9 (N calibrated against R3-tier R1 spread); Q2 → mooted (W6 deferred post-qualifier; actual qualifier data resolves round count); Q3 → W2 triaged (Famadeo `runtime_enabled` checked manually on 2026-05-31, full watchlist deferred); Q4 → W3 + Approach track 2 (Codex worktree serves both `/goal` slow-cook *and* merge-destination roles); Q5 → W8 (`replay.py` retired, `analyze_hand_histories.py` adopted).

**Four order-changing questions surfaced by design critique** — answers would reshape the plan, but the plan is executable without them:

1. **Does first-paired-seed reproduce the Neel +16287 / Dominic +12821 memo numbers vs `v_final`?** If yes, R2 may already be near-green — climb R3 immediately, collapse W5 to one wave. If no, the public field is softer than feared and W5 collapses anyway.
2. **Is Vladimir's Deep CFR beatable in 50k paired-seed hands?** If not, R3/R4 against Vladimir are impossible — book it as a loss, focus remaining time on Saroop + Famadeo-on + mystery_strong, ship v_R3 with that scope.
3. **Is `release/v_final-e4b4a8f1` actually stronger than current `main` HEAD?** If worse, the rollback floor is dead weight and W1's R1 baseline can use `main` directly. If better, base W1's R1 measurements on it and drop the `main`-comparison step.
4. **Has the organiser confirmed Swiss round count?** Mooted for qualifier by W6 deferral, but the answer reshapes the deferred W6 from "build a sweep" to "build a single-cell simulator."

## References

### In-repo (load-bearing)
- `docs/tournament-spec.md` — qualifier/finals format, runtime constraints, ref bots.
- `docs/corpus-index.md` — corpus notes for citation in elegance constraint.
- `docs/deep-research-report.md`, `docs/competitor-intel-analysis-2026-05-26.md` — competitor landscape inputs.
- `docs/playbooks/hardening.md`, `docs/playbooks/patch-window.md` — existing gauntlet & patch-window protocol.
- `PokerBot-codex/consults/day1_x1/MANIFEST.md`, `PokerBot-codex/consults/Day 1 X1 bundle audit.md` — load-bearing reality check on post-X1 state.
- `PokerBot-claude/findings/claude-refbot-leaks.md` — empirical ref-bot leak characterization (pre-X1, treat with caution).
- `PROMPT.shared.md`, `PROMPT.claude.md`, `PROMPT.codex.md` — agent contracts.

### External (citation refs for elegance constraint)
- Brown & Sandholm 2017 (Libratus, *Science*) — blueprint + real-time subgame solving framing.
- Brown & Sandholm 2019 (Pluribus, *Science*) — 6-max blueprint, discrete action abstraction.
- Bowling et al. 2015 (Cepheus, *Science*) — CFR+ + bucket abstraction.
- Lanctot et al. 2009 — external-sampling MCCFR.
- Lisý & Bowling 2017 (arXiv 1612.07547) — Local Best Response (LBR) exploitability bound. **Vault note missing.**
- Billings/Davidson/Schauenberg opponent-modelling. **Vault note missing.**

### Tool refs
- `~/.claude/commands/CodexCode.md`, `~/.claude/skills/codex-code/SKILL.md` — swarm invocation.
- `~/.codex/config.toml`, `~/.codex/goals_1.sqlite` — native `/goal` config + state.
- `gh` CLI v2.72.0 at `/opt/homebrew/bin/gh`.
- GitHub clone visibility: aggregate Insights → Traffic only, no user identity (Quora, GitHub Community Discussion #40154).
- Claude Code `/goal` shipped v2.1.101 (2026-04-11); status-line/overlay panel v2.1.139; local install 2.1.148 confirmed.
