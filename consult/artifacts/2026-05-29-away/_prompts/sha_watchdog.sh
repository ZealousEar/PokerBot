#!/usr/bin/env bash
# SHA watchdog - kills entire tmux server on socket if either protected SHA changes.
# Usage: sha_watchdog.sh <socket_path>
set -uo pipefail
SOCKET="$1"
EXPECTED=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
LOG=/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/sha_watchdog.log
echo "=== watchdog start $(date -u +%Y-%m-%dT%H:%M:%SZ) socket=$SOCKET ===" >> "$LOG"
while sleep 60; do
  A=$(shasum -a 256 /Users/farhad/Code/PokerBot/submissions/v_final.zip 2>/dev/null | cut -c1-64)
  B=$(shasum -a 256 /Users/farhad/Code/PokerBot/submissions/best_green.zip 2>/dev/null | cut -c1-64)
  if [ "$A" != "$EXPECTED" ] || [ "$B" != "$EXPECTED" ]; then
    echo "SHA BREACH $(date -u +%Y-%m-%dT%H:%M:%SZ) v_final=$A best_green=$B" | tee -a "$LOG"
    tmux -S "$SOCKET" kill-server 2>/dev/null
    break
  fi
  echo "ok $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
done
