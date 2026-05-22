# Tournament Specification

Authoritative source: `ext/fullhouse-engine/README.md` + `sandbox/Dockerfile` + `sandbox/validator.py` + `sandbox/runner.py`. Re-read at G1 start and at patch-window opening; any drift gets flagged in STATUS.md.

## Event
- **Name:** Fullhouse Hackathon 2026, London
- **Qualifier:** 2026-06-01 — Swiss-system online; 400 hands per match; 6-bot tables; top 64 advance
- **Patch window:** 2026-06-02 — hand histories downloadable as JSON; one updated bot allowed before finals
- **Finals:** 2026-06-05 — single-elimination bracket at UCL East
- **Prize pool:** £4,000+, lead sponsor Quadrature Capital

## API contract
- Submission: `bot.py` exporting `decide(game_state: dict) -> dict`.
- Layout: `bot.py` at archive root; optional `data/` sibling for blueprints; no other `.py` at root; no `.py` inside `data/`; no symlinks; no path traversal.
- Size: `bot.py` ≤ 5 MB; `data/` ≤ 200 MB; total ≤ 250 MB.
- Submission formats accepted: bare `.py`, directory, or `.zip`.

## Sandbox profile
- Image: `python:3.10-slim` (eval7 0.1.7 fails to build on 3.11+).
- `--network none --memory 768m --cpus 0.5 --read-only --no-new-privileges --user 1000:1000`.
- 2 s wall clock per `decide()`. One warmup call (`type=="warmup"`) before hand 1 with **30 s** budget — load blueprints here.
- File reads from `data/` only at module-import time via `os.environ["BOT_DATA_DIR"]` (engine sets it).
- Engine enforces timeout via daemon thread; bot cannot use `threading` to dodge it.

## Pinned libraries (Dockerfile)
- `eval7==0.1.7` (requires `Cython<3` + `--no-build-isolation` at install)
- `numpy==1.26.4`
- `scipy==1.13.0`
- `treys==0.1.8`
- `scikit-learn==1.5.2`

## Forbidden modules (`validator.FORBIDDEN_MODULES`)
`socket`, `urllib`, `urllib2`, `urllib3`, `requests`, `httpx`, `aiohttp`, `http`, `ftplib`, `smtplib`, `telnetlib`, `xmlrpc`, `subprocess`, `multiprocessing`, `pickle`, `shelve`, `threading`, `ctypes`, `runpy`, `importlib`.

## Forbidden call patterns (validator AST scan)
`__import__(`, `eval(`, `exec(`, `compile(`, `getattr(__builtins__`, `__builtins__[…]`, `globals()[`, `locals()[`, any `subprocess.*`, any `os.{system,popen,exec*,spawn*,fork,kill,remove,unlink,rmdir,removedirs,chmod,chown,replace,rename}`.

## Failure modes (runner emits action with `error` key)
- Crash inside `decide()` → auto-fold for that hand; bot stays in match.
- Return value not a dict with `action` key → fold.
- Action not in `{fold, check, call, raise, all_in}` → fold.
- `raise` missing `amount` → fold; below `min_raise_to` → snapped up to min.
- Exceed 2 s wall clock → auto-fold (daemon worker keeps running in background until it finishes or OOM-kills).
- Forbidden import / call pattern → validator rejects at submission time.
- Package > 250 MB, `data/` > 200 MB, or `bot.py` > 5 MB → validator rejects.
- Warmup call exception → engine emits `{"ok": False, "error": "warmup_exception"}`; hand 1 still runs.

## Reference bots (`ext/fullhouse-engine/bots/`)
- `template/` — pocket pairs + basic pot odds
- `aggressor/` — raises constantly regardless of hand
- `mathematician/` — calls only when getting 3:1 pot odds
- `shark/` — tight preflop, position-aware, value bets
- `ref_bot_2/` — exists in repo but undocumented; treat as wildcard during G3 benchmarks

## Scoring
- Qualifier: cumulative chip delta across Swiss rounds; top 64 advance.
- Finals: single-elimination bracket seeded from qualifier standings.
- 400 hands per qualifier match (engine README §"Tournament format" notes this is double the demo's 150 hands and is intentional to tilt the field toward skill over variance).
