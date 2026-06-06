#!/usr/bin/env bash
# Launch a single /goal lane via codex exec.
# Usage: launch_lane.sh <lane_name> <prompt_file> <working_dir>
set -euo pipefail

LANE="$1"
PROMPT_FILE="$2"
WORKDIR="$3"

LOG_DIR="/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/${LANE}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/codex_run.log"
PID_FILE="$LOG_DIR/codex.pid"
START_FILE="$LOG_DIR/codex_start.txt"
END_FILE="$LOG_DIR/codex_end.txt"

date -u +"%Y-%m-%dT%H:%M:%SZ launch from $WORKDIR" > "$START_FILE"
echo "=== LANE $LANE START $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG"
echo "PROMPT: $PROMPT_FILE" | tee -a "$LOG"
echo "WORKDIR: $WORKDIR" | tee -a "$LOG"
shasum -a 256 /Users/farhad/Code/PokerBot/submissions/v_final.zip /Users/farhad/Code/PokerBot/submissions/best_green.zip 2>&1 | tee -a "$LOG"

cd "$WORKDIR"

# Feed prompt via stdin so heredoc-safe; tee log preserves the full run.
codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  -C "$WORKDIR" \
  - < "$PROMPT_FILE" 2>&1 | tee -a "$LOG"

EXIT=${PIPESTATUS[0]:-$?}
echo "=== LANE $LANE END $(date -u +%Y-%m-%dT%H:%M:%SZ) exit=$EXIT ===" | tee -a "$LOG"
date -u +"%Y-%m-%dT%H:%M:%SZ exit=$EXIT" > "$END_FILE"
shasum -a 256 /Users/farhad/Code/PokerBot/submissions/v_final.zip /Users/farhad/Code/PokerBot/submissions/best_green.zip 2>&1 | tee -a "$LOG"
echo "DONE_${LANE}"
