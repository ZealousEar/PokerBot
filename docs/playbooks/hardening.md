# Hardening Gauntlet — Local Verification

Run sequentially before packaging a submission. All steps must pass.

## 1. Import audit
```bash
python tools/import_audit.py --max-seconds 1.5 --max-mb 400
```
Cold-start < 1.5 s, RSS < 400 MB, no forbidden import per `validator.FORBIDDEN_MODULES` across all `src/*.py`.

## 2. Full regression suite
```bash
pytest -q
```
Must cover: betting replay, blueprint liveness/fallback, opponent-model
idempotence, multiway equity, side-pot/stack math, all-in vs raise-to-stack,
timeout fallback, malformed input, warmup, and illegal-action defense.

## 3. Rebuild and verify the trained artifact
```bash
python tools/train_blueprint.py \
  --iterations 1200 \
  --output data/blueprint_policy_v1.json
git diff --exit-code -- data/blueprint_policy_v1.json data/blueprint_policy_v1.sha256
```
The rebuild must be byte-identical to the reviewed artifact.

## 4. Build & validate package
```bash
python tools/package.py --output submissions/bot.zip --strict
python ext/fullhouse-engine/sandbox/validator.py submissions/bot.zip
unzip -l submissions/bot.zip
du -sh submissions/bot.zip
```
Engine validator must report PASSED. `bot.py` ≤ 5 MB at root, `data/` ≤ 200 MB, total ≤ 250 MB. No other `.py` at root, no `.py` inside `data/`, no symlinks.

## 5. Paired tournament-shaped benchmark
```bash
python tools/benchmark.py \
  --all-templates \
  --candidate submissions/bot.zip \
  --baseline submissions/v_final.zip \
  --hands 800 \
  --paired-seed-base 42 \
  --paired-seed-count 10 \
  --rotations all \
  --min-bb 0 \
  --output-dir evaluation_runs/promotion
```

This runs against all five reference bots. The gate uses the lower bound of
the seed-clustered paired 95% CI by default. Preserve the manifest,
`raw_results.jsonl`, and summary when recording a promotion decision.

## 6. Sandbox dry-run (optional but recommended)
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
