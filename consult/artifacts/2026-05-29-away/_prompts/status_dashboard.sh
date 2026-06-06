#!/usr/bin/env bash
# Snapshot of swarm progress. Usage: status_dashboard.sh
SOCKET=/var/folders/0z/6q5nv2s14fjd3jcn5n4cyys40000gn/T//claude-tmux-sockets/poker-away.sock
ROOT=/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away
EXPECTED=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) DASHBOARD ==="
echo
echo "--- protected SHAs ---"
A=$(shasum -a 256 /Users/farhad/Code/PokerBot/submissions/v_final.zip 2>/dev/null | cut -c1-64)
B=$(shasum -a 256 /Users/farhad/Code/PokerBot/submissions/best_green.zip 2>/dev/null | cut -c1-64)
[ "$A" = "$EXPECTED" ] && echo "OK v_final.zip" || echo "!! BREACH v_final.zip = $A"
[ "$B" = "$EXPECTED" ] && echo "OK best_green.zip" || echo "!! BREACH best_green.zip = $B"

echo
echo "--- load + codex procs ---"
uptime
echo "codex exec count: $(pgrep -f 'codex exec' | wc -l)"

echo
echo "--- per-lane status ---"
for lane in mehedi-cluster trap-sixmax-prevalence postflop-trap-candidate preflop-antecedent-grid public-drift-completeness patch-window-postflop-extractor ship-day-rehearsal; do
  log="$ROOT/$lane/codex_run.log"
  end="$ROOT/$lane/codex_end.txt"
  lines=$(wc -l < "$log" 2>/dev/null || echo 0)
  if [ -f "$end" ]; then
    status="DONE: $(cat "$end")"
  else
    status="RUNNING ($lines log lines)"
  fi
  printf "%-38s %s\n" "$lane" "$status"
done

echo
echo "--- tmux windows ---"
tmux -S "$SOCKET" list-windows -t poker-away 2>/dev/null || echo "tmux server down!"

echo
echo "--- key files materialized ---"
for lane in mehedi-cluster trap-sixmax-prevalence postflop-trap-candidate preflop-antecedent-grid public-drift-completeness patch-window-postflop-extractor ship-day-rehearsal; do
  d="$ROOT/$lane"
  reports=$(ls "$d"/*.md "$d"/STATUS_BLOCK.md "$d"/GO_NO_GO.txt "$d"/RESULTS.json 2>/dev/null | tr '\n' ' ')
  printf "%-38s %s\n" "$lane" "${reports:-<nothing yet>}"
done
