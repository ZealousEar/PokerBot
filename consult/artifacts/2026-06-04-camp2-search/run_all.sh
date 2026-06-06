#!/bin/bash
# Sequential candidate evaluation: failure-tester gate -> gauntlet (alone) -> paired analysis.
# Runs ONE candidate fully before the next (no concurrency -> no false >2s timeouts).
set -u
cd /Users/farhad/Code/PokerBot
source .venv/bin/activate 2>/dev/null
ROOT=/Users/farhad/Code/PokerBot
BASE=$ROOT/consult/artifacts/2026-06-04-camp2-search
BL=$BASE/baseline/live_b108eff5/results/match_results.json
ft=$BASE/failure_tester.py
pa=$BASE/paired_analyze.py

for c in A-3bet B-cbet C-overlay D-river; do
  ZIP=$BASE/zips/cand_$c.zip
  SRC=$BASE/work-trees/$c/src
  echo "===== CANDIDATE $c ====="
  echo "[$c] failure_tester..."
  python "$ft" --zip "$ZIP" --src "$SRC" --hands 200 > "$BASE/logs/ft_$c.json" 2> "$BASE/logs/ft_$c.err"
  if ! python -c "import json,sys; sys.exit(0 if json.load(open('$BASE/logs/ft_$c.json'))['PASS'] else 1)"; then
    echo "[$c] FAILURE_TESTER FAILED -> drop"; continue
  fi
  echo "[$c] failure_tester PASS. gauntlet (alone)..."
  python tools/deployed_artifact_gauntlet.py --bot "$ZIP" --baseline submissions/v_final.zip \
    --hands-per-opponent 4200 --match-len 200 --seed-base 42 --skip-probes \
    --outdir "$BASE/results/$c" > "$BASE/logs/gauntlet_$c.log" 2>&1
  echo "[$c] paired analysis..."
  python "$pa" --candidate "$BASE/results/$c/results/match_results.json" --baseline "$BL" \
    --label "$c" --json-out "$BASE/results/${c}_paired.json" > "$BASE/logs/paired_$c.txt" 2>&1
  python -c "import json; r=json.load(open('$BASE/results/${c}_paired.json')); print('[$c] margin',r['aggregate_margin_bb100'],'CI',r['paired_ci95'],'worst',r['worst_bucket']['margin_bb100'],'errs',r['candidate_runner_errors'],'PROMOTE',r['PROMOTE'])"
done
echo "===== ALL DONE ====="
