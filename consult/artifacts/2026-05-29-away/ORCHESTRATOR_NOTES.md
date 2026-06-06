# Orchestrator notes — 2026-05-29 away swarm

## Launch posture
- 7 lanes (P0-P6) launched via `codex exec --dangerously-bypass-approvals-and-sandbox` in tmux session `poker-away` on isolated socket.
- Protected zips `chmod 444` for OS-level protection.
- SHA watchdog in window 0 kills tmux server on socket if either protected SHA changes.
- Pre-created worktrees:
  - `../PokerBot-codex-postflop-trap` on `candidate/postflop-trap-2026-05-29` from `release/v_final-e4b4a8f1` (for P2)
  - `../PokerBot-codex-preflop-antecedent` on `candidate/preflop-antecedent-grid-2026-05-29` from `release/v_final-e4b4a8f1` (for P3)

## Monitor commands
```bash
# Dashboard
bash /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/_prompts/status_dashboard.sh

# Attach interactively
tmux -S /var/folders/0z/6q5nv2s14fjd3jcn5n4cyys40000gn/T/claude-tmux-sockets/poker-away.sock attach -t poker-away

# Per-lane log
tail -f /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/<lane>/codex_run.log
```

## Findings flagged for human review

### P6 ship-day-rehearsal: DONE — NO_GO_SMOKE_FAIL ⚠️
- Completed 15:05:34Z, exit=0.
- `tools/smoke_run.py --zip submissions/v_final.zip --hands 200` exited code 1 at 136/200 hands.
- Chip delta: v_final=10000, template=-10000, no hero errors.
- Interpretation: opponent (template) busted early; smoke_run.py treats early termination as fail.
- Note: `tools/smoke_run.py` is uncommitted on main with 45 added lines (per `git status` + `git diff --stat` at orchestration start) — almost certainly the change that introduced the strict 200-hand exit-code behavior.
- Protected SHAs unchanged before AND after.
- Agent applied stop rule: validator/import/leakage/size/git-check NOT run after smoke fail. No repair attempted. v_final.zip and best_green.zip untouched.
- **Human action on return:** Decide whether (a) revert `tools/smoke_run.py` to the committed version, or (b) the 200-hand expectation needs revision, then re-run P6 rehearsal before 2026-06-01 upload.

### P0 mehedi-cluster: DONE — DIFFERENT_LEAK ✓
- Completed 15:13:22Z, exit=0.
- 20000 scheduled / 3764 actual hands, scheduled -9.00 bb/100, actual -47.82 bb/100, 95% CI [-14.00, -4.00].
- Verdict reason: dominant top-2 last-decision clusters are PREFLOP big_blind fold/all_in (-15.87 scheduled bb/100). Toby-style river clusters are present but secondary (-6.20 scheduled bb/100 in top-10).
- Mehedi loss is therefore mostly preflop big_blind aggression handling, NOT the Toby postflop river trap.
- Recommendation: **SHIP_LOCKED_ARTIFACT**.
- This is good news for the locked artifact: Mehedi is a different leak class, not a generalized postflop-trap class — so no broad structural patch is justified by Mehedi alone.

### P3 preflop-antecedent-grid: DONE — NOT_PROMOTABLE ✓
- Completed 15:18:15Z, exit=0.
- Built and tested 5 candidate variants (A0 baseline through A5 position-specific).
- A4 selected as best of the variants but did not clear the +5.0 bb/100 improvement bar on Toby/Mehedi targets vs A0.
- Locked v_final.zip remains upload target.

### P5 patch-window-postflop-extractor: DONE — GREEN ✓
- Completed 15:17:21Z, exit=0.
- Tooling-only: `tools/analyze_postflop_trap_prevalence.py` + integration tests (4 passed, 0.26s).
- Synthetic fixtures parse correctly (6 records, 10 postflop actions, 5 river actions).
- Branch `tooling/postflop-trap-extractor-2026-05-29` carries the diff.
- Ready for 2026-06-02 patch window.

### P2 postflop-trap-candidate: DONE — PATCH_NOT_PROMOTABLE (but useful evidence) ⚠️
- Completed 15:27:01Z, exit=0.
- Candidate built (`v_postflop_trap_candidate.zip`, sha `136c8cde…`); locked v_final.zip and best_green.zip untouched.
- Edit surface: `src/postflop.py` only (river-only texture guard) + edge tests.
- **Trigger H2H**: Toby base 142 = +3.0 bb/100 (CI [-3,+9]), base 242 = -1.0 (CI [-7,+5]). Locked artifact prior: -14.0 / -16.6. So **candidate gains ~17 bb/100 on Toby**.
- Regression on references: template +20, aggressor 0, math +20, shark +20, ref_bot_2 +20.
- Regression on public: Pav 7.9 = -1.07, Pav 7.6 = +5.62, famadeo +3.89, neel +18.74, stoppedtime24 +20.
- Static gates: leakage PASS, import PASS (0.286s, 32.6 MB), edge PASS (29), validator PASS, exploit PASS (preflop 18.0, aggregate 5.65).
- Smoke: FAIL on the same 136/200 hand-count parity as locked (no errors). This is the `tools/smoke_run.py` harness behaviour P6 flagged — not a candidate-specific bug.
- Final decision per agent: `do_not_promote`. Human promotion gate required.
- **Human action on return:** decide whether to gate this candidate through full human review for finals (B5/B6/B7 schedule). Note: this is the strongest Toby fix found — but Pav 7.9 regression and smoke parity both need human sign-off.

## Cleanup after swarm finishes
```bash
# Restore zips to default mode if you want to commit
chmod 644 /Users/farhad/Code/PokerBot/submissions/v_final.zip /Users/farhad/Code/PokerBot/submissions/best_green.zip

# Tear down tmux session
tmux -S /var/folders/0z/6q5nv2s14fjd3jcn5n4cyys40000gn/T/claude-tmux-sockets/poker-away.sock kill-server

# Worktrees (only after you're sure you don't need P2/P3 candidate work)
git worktree remove /Users/farhad/Code/PokerBot-codex-postflop-trap
git worktree remove /Users/farhad/Code/PokerBot-codex-preflop-antecedent
```
