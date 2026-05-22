# Hardening Gauntlet — Pre-submission

Run sequentially before any `submissions/v_*.zip` upload. All steps must pass.

## 1. Import audit
```bash
python tools/import_audit.py --max-seconds 1.5 --max-mb 400
```
Cold-start < 1.5 s, RSS < 400 MB, no forbidden import per `validator.FORBIDDEN_MODULES` across all `src/*.py`.

## 2. Edge cases
```bash
pytest tests/edge_cases -x
```
Must cover: side-pot, all-in vs raise-to-stack distinction, raise-below-min, raise-above-stack, timeout fallback, malformed input, warmup call, illegal-action defense.

## 3. Benchmark
```bash
python tools/benchmark.py --all-templates --hands 10000 --min-bb 5
```
All four templates (`template`, `aggressor`, `mathematician`, `shark`): ≥ +5 bb/100, 95 % CI above zero.

## 4. Coarse exploitability
```bash
python tools/exploit_check.py --max-mbb 80
```

## 5. Build & validate package
```bash
python tools/package.py --output submissions/v_final.zip --strict
python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip
unzip -l submissions/v_final.zip
du -sh submissions/v_final.zip
```
Engine validator must report PASSED. `bot.py` ≤ 5 MB at root, `data/` ≤ 200 MB, total ≤ 250 MB. No other `.py` at root, no `.py` inside `data/`, no symlinks.

## 6. Sandbox dry-run (optional but recommended)
```bash
# Build the engine's image once
docker build -t fullhouse-engine ext/fullhouse-engine/sandbox/

# Extract our package and run a hand against shark
mkdir -p /tmp/bot_test && unzip -o submissions/v_final.zip -d /tmp/bot_test
docker run --rm --network none --memory 768m --cpus 0.5 \
  --read-only --no-new-privileges --user 1000:1000 \
  -v /tmp/bot_test:/bot:ro \
  -e BOT_DATA_DIR=/bot/data \
  -e BOT_PATH=/bot/bot.py \
  fullhouse-engine
```

## 7. STATUS check
Confirm `STATUS.md` shows G1–G4 all GREEN with numeric evidence, then append `FINAL SUBMITTED` with the final benchmark numbers, archive size, and import audit results.
