# Overnight 2026-05-27 — Multi-lane probe queue launch

**Wall budget:** 9 hours hard cap. Global kill switch at T+9 h.
**Worktree:** `/Users/farhad/Code/PokerBot-claude/` only. Do not touch `~/Code/PokerBot/` (canonical) or `~/Code/PokerBot-codex/` (other agent's tree).
**Baseline artifact:** canonical `~/Code/PokerBot/submissions/v_final.zip`, sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` (`e4b4a8f1…598`).
**Source of truth for lane specs:** `~/Code/PokerBot/KANBAN.md`, section **"Overnight 2026-05-27 — Parallel multi-lane probe queue"**. Re-read it once at start; the per-lane methods, outputs, and accept gates live there. This prompt is the dispatch + monitoring layer only.

---

## Token-routing policy (binding)

- All execution work runs through `/CodexCode` (Codex CLI agents in isolated worktrees inside `PokerBot-claude/`). Target split ≈ **85 % Codex / 15 % Claude**.
- `/CodexConsult` is **forbidden** for this run. It is a planner/worker/reviewer/judge swarm — overkill for unattended throughput.
- Claude (you) does: re-reading KANBAN, dispatching `/CodexCode` jobs, polling sessions every 15 min, capturing failures, and writing the wake-up `SUMMARY.md`.
- One `/CodexCode` agent per lane, **except Lane B**: split into 4 parallel `/CodexCode` jobs (one per opponent — vladimir, dominic, famadeo, neel). All other lanes are single-agent.
- No nested delegation; do not spawn explore/design/pair agents. `/CodexCode` is the only execution primitive.

---

## Lane drops (pre-flight diagnostics)

Diagnostic pass ran before this prompt. One lane drops, two patches needed.

- **DROP Lane G — Cold-start RSS + decision latency stress.** Docker daemon not running on host; `fullhouse-sandbox:latest` cannot be launched. Skip entirely.
- **All four Lane B / Lane K opponents stay in.** 1-hand smoke against `v_final.zip` produced zero `bot_errors` for vladimir/vlad, dominic/dominic, famadeo/codex_holdem, neel/neel (0.13 – 0.26 s/hand). Earlier "vladimir / famadeo flagged as load risks" is invalidated as of this diagnostic.
- **Lane J retained.** GitHub API reachable (HTTP 200).

---

## Step 0 — must-run repairs before any lane launch

The claude worktree is mid-rebuild and needs three corrections. Run these from `~/Code/PokerBot-claude/` **before** dispatching anything. These are file copies, not edits to canonical or `-codex`.

```bash
cd /Users/farhad/Code/PokerBot-claude/

# 0.1 — Pin the baseline. claude worktree currently holds a stale build (ceb20ecc…).
cp /Users/farhad/Code/PokerBot/submissions/v_final.zip submissions/v_final.zip
shasum -a 256 submissions/v_final.zip  # MUST start with e4b4a8f1
# Halt the run if sha does not match — every benchmark/exploit/H2H depends on this exact artifact.

# 0.2 — Lane B + F dependency. h2h.py missing in claude (exists in canonical).
cp /Users/farhad/Code/PokerBot/tools/h2h.py tools/h2h.py
/Users/farhad/Code/PokerBot/.venv/bin/python tools/h2h.py --help  # confirm

# 0.3 — Make the lane scratch root.
mkdir -p consults/2026-05-27-overnight-{B,A,D,E,F,I,J,K,L,M,N,O,P,Q,R,S,T,SUMMARY}

# 0.4 — Dry-run h2h.py against ONE public bot as a directory (fail-fast cascade guard).
# This was verified at prompt-build time, but re-verify here in case the worktree shifted.
# Halt if h2h.py rejects the dir path or prints no bb/100 summary — Lane B and downstream Phase 2 depend on this code path.
/Users/farhad/Code/PokerBot/.venv/bin/python tools/h2h.py \
  --bot-a submissions/v_final.zip \
  --bot-b ext/public-bots/vladimir/bots/vlad/ \
  --hands 2 --paired-seed-base 999 --match-len 2 \
  --label-a v_final --label-b vlad 2>&1 | tail -10
```

Known stub to route around: `tools/self_play.py` is a G1 TODO that prints and exits 0; it does **not** run hands. Any lane wanting self-play must use `h2h.py --bot-a v_final.zip --bot-b v_final.zip` or invoke `ext/fullhouse-engine/sandbox/match.py` directly. Lane S (decision-cluster mining) in particular: tell the Codex agent to use `sandbox/match.py` with the canonical zip on both seats, dumping each hand's action log to disk for clustering.

---

## Hard rules (every lane, every Codex agent)

1. **No auto-promote.** Never copy any candidate into `submissions/v_final.zip` or `best_green.zip`. Promotion is morning-human only.
2. **No edits outside `PokerBot-claude/`.** Canonical `PokerBot/` and `PokerBot-codex/` are read-only. Tooling reads from canonical (`tools/h2h.py` source, baseline zip) are fine; writes are not.
3. **All artifacts under `consults/2026-05-27-overnight-<lane>/`.** Nothing leaks into `submissions/`, `data/`, `src/`, or `tools/`.
4. **Paired seeds are mandatory.** Every benchmark/H2H uses `--paired-seed-base 42 --paired-seed-count 10` (or KANBAN-specified equivalent). Single-seed numbers are inadmissible.
5. **Lane A pre-commits acceptance criteria.** Before sweep launch, the Lane A agent writes `consults/2026-05-27-overnight-A/PRE_COMMIT.txt` listing the exact gates (bb/100 > baseline + 1.5 × pooled SE; LBR ≤ 100/200; edge clean; import clean; validator PASS; beats ≥ 4 of 7 templates). Any later leaderboard claim must reference this file.
6. **Per-lane kill switches.** Per KANBAN: Lane A halts on 3 consecutive non-improving candidates OR 6 CPU-hours, whichever first. Other lanes: halt if their per-lane wall budget × 1.5 is exceeded.
7. **Global 9 h kill.** Record `START_T=$(date +%s)` at Phase-1 dispatch. If `now - START_T >= 9*3600` at any monitoring tick, cancel all live `/CodexCode` sessions and jump straight to SUMMARY assembly with whatever data exists.
8. **Lane H staggers strictly after Lane A.** Both write the same `src/opponent_model.py` / `src/sizing.py` files via candidate dirs; do not run concurrently.
9. **In-tree source edits for lane-internal work are allowed; promotion is not.** A Codex agent on (e.g.) Lane K may edit `tools/exploit_check.py` or add files under `tools/probes/` if its method requires it. That edit must stay in the worktree; no Codex agent may package an edited tree into `submissions/` or overwrite the baseline zip. If unsure, write the modified artifact to `consults/2026-05-27-overnight-<lane>/candidates/` instead of `submissions/`.

---

## Phase plan

### Phase 1 — launch immediately (parallel, no inter-lane dependencies)

| Lane | Codex jobs | Notes |
|---|---|---|
| B | **4 parallel** (one per opponent: vladimir/vlad, dominic/dominic, famadeo/codex_holdem, neel/neel) | Each runs `tools/h2h.py --bot-a submissions/v_final.zip --bot-b ext/public-bots/<who>/bots/<bot>/ --hands 10000 --paired-seed-base 42`. Output `consults/2026-05-27-overnight-B/<opponent>/h2h.json`. |
| A | 1 | 15-candidate overlay grid; writes `PRE_COMMIT.txt` first. |
| D | 1 | 5 synthetic JSON variants → `analyze_hand_histories.py`. |
| F | 1 | Adversarial seed search seeds 1–500 per opponent. |
| I | 1 | LBR 20→100 spots on `v_final.zip`. |
| J | 1 | GitHub rescan; agent task. |
| N | 1 | Validator red-team adversarial states. |
| O | 1 | Competitor source dive (read-only over `ext/public-bots/`). |
| P | 1 | Vladimir Deep CFR pipeline analysis (read-only). |
| Q | 1 | Worktree reconciliation (5 min; meta). |
| R | 1 | claude X1-repair AMBER 50 k paired-seed re-run. |

### Phase 2 — gated on Lane B SUMMARY.md complete

| Lane | Codex jobs | Trigger |
|---|---|---|
| E | 1 | Lane B's per-opponent bb/100 feeds tournament-finish Monte Carlo. |
| K | 1 | Per-opponent LBR using competitor as best-responder approximation. May require small `exploit_check.py` extension — Codex agent decides scope. |
| L | 1 | Preflop range tuning vs observed VPIPs from Lane B logs. |

### Phase 3 — gated on Lane A completion

| Lane | Codex jobs | Trigger |
|---|---|---|
| H | 1 | Sizing-frequency sweep. Writes same opponent_model / sizing files — must not run concurrently with A. |
| M | 1 | 3-bet / 4-bet frequency sweep. |

### Phase 4 — stretch (only after all above are queued / done, AND > 2 h wall remaining)

| Lane | Codex jobs | Notes |
|---|---|---|
| S | 1 | 1 000-hand replay decision-cluster mining via `sandbox/match.py` (not the stub `self_play.py`). |
| T | 1 | 5–10 synthetic finals-competitor variants; benchmark `v_final.zip` against them. |

### Lane G — dropped (Docker daemon offline)

If Docker daemon is started later in the run, do **not** retroactively launch Lane G — the wall budget is already committed. Note "Lane G: dropped, daemon not running at launch" in SUMMARY.md.

---

## Lane B aggregation (between Phase 1 and Phase 2)

The 4 parallel `/CodexCode` jobs each write only `consults/2026-05-27-overnight-B/<opponent>/h2h.json`. **You (the orchestrator) write the aggregate `consults/2026-05-27-overnight-B/SUMMARY.md`** — no Codex agent owns it.

Trigger: all 4 of `B/{vladimir,dominic,famadeo,neel}/h2h.json` exist and parse as valid JSON. Then:

1. Read each opponent's per-match BB delta, 95 % CI, bb/100, error counts.
2. Write `B/SUMMARY.md` as a 4-row table (opponent | bb/100 | CI low | CI high | errors | accept-gate verdict). KANBAN gate: mean > 0 AND CI low > −20 bb/100 per opponent.
3. Only after `B/SUMMARY.md` is written may Phase 2 (E, K, L) dispatch.

If one or two B sub-jobs fail or time out: write `B/SUMMARY.md` anyway with those rows marked FAILED, and dispatch Phase 2 with only the surviving opponents in scope.

## Monitoring loop (every 15 minutes from Phase-1 dispatch)

At each tick:

1. `agent_manage.list_sessions` (state filter: `running`, `waiting_for_input`, `failed`). Record each session's id + lane tag to `consults/2026-05-27-overnight-SUMMARY/STATE.json` so the kill switch can find them.
2. For each `waiting_for_input`: read the prompt, decide. Approve actions consistent with Hard Rules 1–9 (writing under its lane's `consults/` dir, reading public bots, hashing zips, in-tree source edits for lane-internal work). **Decline** any attempt to modify `submissions/`, overwrite the baseline zip, or write into another lane's dir — redirect to `consults/<lane>/candidates/<n>/`.
3. For each `failed`: capture lane id, error class, last 50 lines stderr to `consults/2026-05-27-overnight-SUMMARY/FAILURES.md`. Decide: retry once with relaxed scope, or mark FAILED in the wake-up summary.
4. For each completed lane: confirm `consults/2026-05-27-overnight-<lane>/SUMMARY.md` exists (Lane B's SUMMARY is your responsibility, per the section above). If the lane unblocks a Phase-2 / Phase-3 dependent, dispatch the dependent.
5. **Disk check.** `df -h /Users/farhad/Code/PokerBot-claude/`. If free space drops below 2 GB, stop dispatching new lanes; if below 500 MB, cancel running lanes and jump to SUMMARY.
6. **Wall check.** If `now - START_T >= 9*3600`, fire the kill switch (next section).
7. Log one line to `consults/2026-05-27-overnight-SUMMARY/MONITORING.log`: `<iso-timestamp> phase=<n> live=<count> done=<count> failed=<count> wall_remaining=<h:mm> free_gb=<n>`.

If your own context is filling up: keep `STATE.json` current (active session IDs, dispatched lanes, completed lanes, failures, phase) so a fresh chat could resume by reading it.

**Failure escalation:** if more than 4 lanes fail in a single phase, or if Lane A AND Lane B both fail, stop dispatching new lanes — finish in-flight work, then write SUMMARY.

## Global 9 h kill switch — exact sequence

When `now - START_T >= 9*3600`:

1. Read `consults/2026-05-27-overnight-SUMMARY/STATE.json` → list of live `<session_id, lane>` pairs.
2. For each session: `agent_run op=cancel session_id=<id>`. Tolerate cancel failures — `/CodexCode` sub-sessions may not all be cancellable directly; record any that resist into `FAILURES.md` as `kill_resisted`.
3. Stop dispatching new lanes regardless of cancel success.
4. Wait up to 60 s for cancellations to settle, then proceed to assemble `SUMMARY.md` with the data that landed. Lanes whose sessions resisted cancel are recorded as TRUNCATED in the wake-up table.
5. If `agent_run op=cancel` is not available for some reason, the fallback is the same: stop dispatching, write SUMMARY from what landed. The 9 h cap is a *no new work* boundary, not a guarantee of process termination.

---

## Wake-up deliverable — `consults/2026-05-27-overnight-SUMMARY/SUMMARY.md`

Write at end-of-run, whether by completion or kill switch. Single file, one page. Format:

```markdown
# Overnight 2026-05-27 — Wake-up SUMMARY

**Wall:** start <iso> / end <iso> / elapsed <h:mm:ss> / cap 9 h
**Kill reason:** <natural completion | global 9 h kill | failure cascade>
**Baseline pinned:** v_final.zip sha e4b4a8f1…598
**Token budget actuals:** Claude ~<X>k / Codex ~<Y>k (read from session logs; rough est OK)

## Per-lane status

| Lane | Tier | Status | Wall | Headline number | Output dir |
|---|---|---|---|---|---|
| B-vladimir | 1 | DONE/AMBER/FAIL/SKIPPED | <m> | bb/100 ± CI | consults/.../B/vladimir/ |
| B-dominic  | 1 | … | … | … | … |
| B-famadeo  | 1 | … | … | … | … |
| B-neel     | 1 | … | … | … | … |
| A          | 1 | … | … | top candidate Δ vs baseline | consults/.../A/ |
| D          | 1 | … | … | variants passed / 5 | consults/.../D/ |
| E          | 2 | … | … | P(finish≤1, ≤5, ≤64) | consults/.../E/ |
| F          | 2 | … | … | worst-seed mean Δ | consults/.../F/ |
| G          | 2 | SKIPPED — docker daemon offline | — | — | — |
| K          | 2 | … | … | max mbb/g vs competitors | consults/.../K/ |
| H          | 3 | … | … | best sizing config Δ | consults/.../H/ |
| I          | 3 | … | … | 100-spot LBR pre/agg | consults/.../I/ |
| J          | 3 | … | … | new competitors found | consults/.../J/ |
| N          | 3 | … | … | malformed states passed / total | consults/.../N/ |
| L          | 4 | … | … | best range adj Δ | consults/.../L/ |
| M          | 4 | … | … | best 3bet/4bet config Δ | consults/.../M/ |
| O          | 4 | … | … | techniques worth porting | consults/.../O/ |
| P          | 4 | … | … | reusability verdict | consults/.../P/ |
| Q          | 4 | … | … | branches diverged / total | consults/.../Q/ |
| R          | 4 | … | … | X1 AMBER → resolved? | consults/.../R/ |
| S          | 4 | … | … | top suspicious cluster | consults/.../S/ |
| T          | 4 | … | … | best synthetic Δ | consults/.../T/ |

## Recommended morning actions (max 5, tournament-impact-ranked)

1. <highest-impact next move, e.g. "Promote Lane A candidate #N — passes all gates, +X bb/100, LBR within band">
2. …
3. …
4. …
5. …

## Risks / open questions

- <anything unresolved>

---

**DO NOT auto-promote.** Every change to `submissions/` is a manual human decision after reading the per-lane evidence above.
```

Order rows in the table by tier then lane id, as shown.

Headline-number examples (use the lane's actual output, not these placeholders):
- Lane B per opponent: `+42.1 bb/100 [CI +18.4, +66.8]`
- Lane A top candidate: `MAX_DEV=0.15, thresholds=(0.55,0.35), Δ vs baseline +12.4 bb/100 (paired SE 3.1)`
- Lane I expanded LBR: `preflop 38.2 mbb/g (cap 100), aggregate 91.4 mbb/g (cap 200)`
- Lane R: `template +XX.X vs baseline +13.20 — AMBER resolved/unresolved`

Recommended-action bullets must be ranked by **tournament impact** (qualifier finish probability shift), not by lane number or completion order.

---

## Launch sequence (your first 10 minutes)

1. Re-read `~/Code/PokerBot/KANBAN.md` section "Overnight 2026-05-27 — Parallel multi-lane probe queue". You'll dispatch lanes by quoting that section to each `/CodexCode` agent.
2. Run Step 0 (copy baseline zip, copy `h2h.py`, mkdir consults tree). Verify the baseline sha equals `e4b4a8f1…598`. Halt if not.
3. Record `START_T` to `consults/2026-05-27-overnight-SUMMARY/STATE.json` along with the lane drop note for G.
4. Dispatch Phase 1 in this order (single message per `/CodexCode` invocation):
   - First: Lane B × 4 (vladimir, dominic, famadeo, neel) — these gate Phase 2 and have the largest wall-time spread.
   - Then: A (long, single agent).
   - Then in any order: D, F, I, J, N, O, P, Q, R.
5. Each dispatch must include: (a) the lane's KANBAN paragraph, (b) the worktree path `/Users/farhad/Code/PokerBot-claude/`, (c) the output dir `consults/2026-05-27-overnight-<lane>/`, (d) Hard Rules 1–9 by reference, (e) explicit instruction "Single Codex agent, no nested delegation, no auto-promote, write SUMMARY.md when done".
6. Enter the monitoring loop (15 min cadence). Trigger Phase 2 on Lane B completion. Trigger Phase 3 on Lane A completion. Trigger Phase 4 only when ≥ 2 h wall remain and most Tier-1/2/3 lanes are DONE or FAILED.
7. At T+9 h or natural completion, write `SUMMARY.md` per the format above.

Begin now.
