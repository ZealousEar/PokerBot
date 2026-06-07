# Hardening Gauntlet — Local Verification

Run sequentially before packaging a submission. All steps must pass.

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
All four reference templates (`template`, `aggressor`, `mathematician`, `shark`): ≥ +5 bb/100, 95 % CI above zero.

## 4. Build & validate package
```bash
python tools/package.py --output submissions/bot.zip --strict
python ext/fullhouse-engine/sandbox/validator.py submissions/bot.zip
unzip -l submissions/bot.zip
du -sh submissions/bot.zip
```
Engine validator must report PASSED. `bot.py` ≤ 5 MB at root, `data/` ≤ 200 MB, total ≤ 250 MB. No other `.py` at root, no `.py` inside `data/`, no symlinks.

## 5. Sandbox dry-run (optional but recommended)
```bash
# Build the engine's image once
docker build -t fullhouse-engine ext/fullhouse-engine/sandbox/

# Extract the package and run a hand against a reference bot
mkdir -p /tmp/bot_test && unzip -o submissions/bot.zip -d /tmp/bot_test
docker run --rm --network none --memory 768m --cpus 0.5 \
  --read-only --no-new-privileges --user 1000:1000 \
  -v /tmp/bot_test:/bot:ro \
  -e BOT_DATA_DIR=/bot/data \
  -e BOT_PATH=/bot/bot.py \
  fullhouse-engine
```
