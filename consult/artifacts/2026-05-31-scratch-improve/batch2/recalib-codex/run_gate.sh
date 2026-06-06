#!/bin/zsh
set -e
LANE=/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-31-scratch-improve/batch2/recalib-codex
PY=/Users/farhad/Code/PokerBot/.venv/bin/python
RP="$LANE/run_pods.py"
LOCKED=/Users/farhad/Code/PokerBot/submissions/v_final.zip
CODEX=/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-31-scratch-improve/sibling-gate/codex.zip
COMPS="C0D_DETERMINISTIC_SUBSET C0_BASELINE C1_SINGLE_TOBY_WEAK_FIELD"

echo "=== LOCKED side (v_final.zip), base 900, 40 seeds, jobs=1 ==="
PYTHONHASHSEED=0 "$PY" "$RP" --hero-zip "$LOCKED" --out-dir "$LANE/gate_locked" \
  --compositions ${(z)COMPS} --seed-base 900 --seeds 40 --jobs 1 --hands 400

echo ""
echo "=== CODEX side (codex.zip), base 900, 40 seeds, jobs=1 ==="
PYTHONHASHSEED=0 "$PY" "$RP" --hero-zip "$CODEX" --out-dir "$LANE/gate_codex" \
  --compositions ${(z)COMPS} --seed-base 900 --seeds 40 --jobs 1 --hands 400

echo ""
echo "=== ALL DONE ==="
