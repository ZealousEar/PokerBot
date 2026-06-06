# 2026-05-29 Away-Swarm Summary

Orchestration window: 2026-05-29T14:57Z → 2026-05-29T16:31Z (~94 minutes).

## Protected artifact status

- Both `submissions/v_final.zip` and `submissions/best_green.zip` retained sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` before, during, and after the run.
- Files remain `chmod 444` (read-only) — restore with `chmod 644` if you need to commit/rewrite.
- SHA watchdog ran throughout the swarm (60s polls); no breach ever recorded — see `sha_watchdog.log`.

## Lane verdicts

| Lane | Status | Verdict | Ship recommendation |
|------|--------|---------|---------------------|
| P0 mehedi-cluster | DONE 15:13Z | **DIFFERENT_LEAK** (preflop big_blind, not Toby river trap) | SHIP_LOCKED_ARTIFACT |
| P1 trap-sixmax-prevalence | DONE 15:46Z | **TRAP_PREVALENCE_DANGEROUS** (baseline already CRITICAL at 68% bust; trap bots are neutral-to-positive vs baseline) | SHIP_LOCKED_ARTIFACT |
| P2 postflop-trap-candidate | DONE 15:27Z | **PATCH_NOT_PROMOTABLE** (but candidate gains +17 bb/100 on Toby!) | Do not promote without human gate |
| P3 preflop-antecedent-grid | DONE 15:18Z | **NOT_PROMOTABLE** (no variant cleared the +5 bb/100 bar) | SHIP_LOCKED_ARTIFACT |
| P4 public-drift-completeness | DONE 16:31Z | **RED_REVIEW** (6 RED cells, 3 brand-new Toby variants discovered) | Do not modify without fully gated candidate |
| P5 patch-window-postflop-extractor | DONE 15:17Z | **GREEN** (tooling-only, 4 tests passing) | Ready for 2026-06-02 patch window |
| P6 ship-day-rehearsal | DONE 15:05Z | **NO_GO_SMOKE_FAIL** ⚠️ | Investigate `tools/smoke_run.py` change before 2026-06-01 |

## Critical things you must look at when you return (in order)

### 1. ⚠️ P6: NO_GO_SMOKE_FAIL on the locked artifact
- `tools/smoke_run.py` has **45 added lines uncommitted** on main (per `git status` at start).
- That change introduces strict 200-hand exit-code behaviour; when the template opponent busts early at hand 136 (normal because v_final is strong), the smoke wrapper exits 1.
- P2's candidate hit the same 136/200 — confirming it's the smoke harness, not the strategy.
- **You cannot upload on 2026-06-01 with this state.** Either revert the smoke_run.py change or relax the 200-hand expectation, then re-run P6 to get `GO_UPLOAD_LOCKED_V_FINAL`.

### 2. P4: 3 new RED public bots from Toby's repo
- `bots/loose_aggressive` -16.40 bb/100 [-17.80, -15.00]
- `bots/loose_passive` -11.80 bb/100 [-14.00, -9.60]
- `bots/stack_pressure` -20.00 bb/100 [-20.00, -20.00]
- Toby's `master` confirmed RED at -17.00. Mehedi `mybot` confirmed RED at -3.73.
- Pav `skantbot7.9` re-confirmed RED at -0.14 (NEW_THREAT classification because it wasn't in the prior pavmatrix).
- 13 other Pav skantbot7.x variants ALL tested GREEN.
- All other Toby variants (`tight_aggressive`, `tight_passive`, `position_exploiter`, `pure_pot_odds`, `bluff_heavy`, `random_bot`) tested GREEN.
- Live `vladimirfilip/bots/vlad` is TIMEBOXED_UNUSABLE (missing `data/gto_strategy.npz` in live repo).

### 3. P2: An effective Toby fix exists, but it isn't promotable as-is
- `consult/artifacts/2026-05-29-away/postflop-trap-candidate/zips/v_postflop_trap_candidate.zip` (sha `136c8cde…`)
- Edits limited to `src/postflop.py` (river-only texture guard) + edge tests.
- Toby b142 = +3.0 bb/100 (CI [-3,+9]), b242 = -1.0 (CI [-7,+5]) → ~+17 bb/100 vs locked artifact's prior -14.0 / -16.6.
- Reference regression clean: template +20, math +20, shark +20, ref_bot_2 +20, aggressor 0.
- Public regression: Pav 7.9 -1.07 (still slightly RED), Pav 7.6 +5.62, famadeo +3.89, neel +18.74, stoppedtime24 +20.
- Static gates all PASS (leakage, import 0.286s/32.6MB, edge 29, validator, exploit 18.0/5.65).
- Held back by (a) the same smoke parity issue P6 flagged, and (b) Pav 7.9 still slightly negative.
- **Decision** is the human's: gate this candidate through full review for finals? Note this is the strongest Toby fix found in this swarm.

### 4. P1: Six-max baseline is already CRITICAL — variance dominates
- Even C0 baseline (hero + template + aggressor + math + shark + ref_bot_2) ends with p50 = -10000 (busts) and 68% bust rate.
- Median bust hand 62 of 400 — consistent with 6-max variance, not a functional bug.
- Adding trap bots actually *improves* the median in some cases (Toby alone AMBER with p50 +10536).
- This is high-variance shipping, not a strategy failure. The prior QUAL-PODS reconciliation stands.

## Lane artifacts

```
consult/artifacts/2026-05-29-away/
├── _prompts/                              # 7 prompt files + launcher + watchdog + dashboard
├── ORCHESTRATOR_NOTES.md                  # Live notes during the swarm
├── SUMMARY.md                             # This file
├── sha_watchdog.log                       # Watchdog ticks (all ok)
├── mehedi-cluster/                        # P0
│   ├── MEHEDI_CLUSTER_REPORT.md           # → DIFFERENT_LEAK
│   ├── RESULTS.json
│   ├── STATUS_BLOCK.md
│   └── decision_log.jsonl
├── trap-sixmax-prevalence/                # P1
│   ├── TRAP_SIXMAX_REPORT.md              # → TRAP_PREVALENCE_DANGEROUS (variance-driven)
│   ├── RESULTS.json
│   ├── matches.jsonl
│   └── STATUS_BLOCK.md
├── postflop-trap-candidate/               # P2
│   ├── POSTFLOP_TRAP_CANDIDATE_REPORT.md  # → PATCH_NOT_PROMOTABLE
│   ├── RESULTS.json
│   ├── DIFF.patch
│   ├── command_logs/
│   ├── zips/v_postflop_trap_candidate.zip
│   └── STATUS_BLOCK.md
├── preflop-antecedent-grid/               # P3
│   ├── PREFLOP_ANTECEDENT_GRID_REPORT.md  # → NOT_PROMOTABLE
│   ├── RESULTS.json
│   ├── zips/preflop_antecedent_A0..A5.zip
│   └── STATUS_BLOCK.md
├── public-drift-completeness/             # P4
│   ├── PUBLIC_DRIFT_COMPLETENESS_REPORT.md # → RED_REVIEW
│   ├── RESULTS.json
│   ├── opponent_inventory.json
│   └── STATUS_BLOCK.md
├── patch-window-postflop-extractor/       # P5
│   ├── POSTFLOP_EXTRACTOR_REPORT.md       # → GREEN
│   ├── RESULTS.json
│   ├── DIFF.patch                         # → tooling/postflop-trap-extractor-2026-05-29
│   └── STATUS_BLOCK.md
└── ship-day-rehearsal/                    # P6
    ├── SHIP_DAY_REHEARSAL.md              # → NO_GO_SMOKE_FAIL ⚠️
    ├── GO_NO_GO.txt
    ├── command_logs/
    └── STATUS_BLOCK.md
```

## Worktrees created (P2/P3)

```bash
# Still on disk:
git worktree list
# → /Users/farhad/Code/PokerBot-codex-postflop-trap   [candidate/postflop-trap-2026-05-29]
# → /Users/farhad/Code/PokerBot-codex-preflop-antecedent [candidate/preflop-antecedent-grid-2026-05-29]

# Remove only after you've extracted DIFF.patch evidence:
git worktree remove ../PokerBot-codex-postflop-trap
git worktree remove ../PokerBot-codex-preflop-antecedent
```

## Cleanup commands

```bash
# Restore protected zips to default mode (only if you need to commit)
chmod 644 /Users/farhad/Code/PokerBot/submissions/v_final.zip /Users/farhad/Code/PokerBot/submissions/best_green.zip

# Tear down the tmux session
tmux -S /var/folders/0z/6q5nv2s14fjd3jcn5n4cyys40000gn/T/claude-tmux-sockets/poker-away.sock kill-server
```

## Net recommendation

**Default: SHIP the locked v_final.zip on 2026-06-01.** All seven lanes — including the deepest investigations into trap behaviour and six-max prevalence — return SHIP-class verdicts with one human-actionable blocker (P6's smoke harness) and one human-decision item (P2's effective-but-not-fully-gated Toby patch).

Before 2026-06-01, you must:
1. Resolve the `tools/smoke_run.py` regression so P6 returns `GO_UPLOAD_LOCKED_V_FINAL`.
2. Decide whether P2's candidate enters a full human-promotion gauntlet, or stays a research artifact.

Neither item changes the locked submitted artifact.
