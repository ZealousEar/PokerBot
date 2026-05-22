# PokerBot

Fullhouse Hackathon 2026 entry. Heuristic-first hybrid for 6-max no-limit hold'em with precomputed preflop blueprint, flop bucket lookup, eval7-backed turn/river equity, and an opponent-frequency exploit overlay.

## Quickstart

```bash
# One-shot install (eval7 needs Cython<3 + --no-build-isolation)
pip3 install "Cython<3"
pip3 install --no-build-isolation eval7==0.1.7
pip3 install -r requirements.txt

# Edge-case tests
pytest tests/edge_cases -x

# 100-hand smoke vs template opponent (G1 verification)
python tools/self_play.py --opponent template --hands 100 --strict

# Benchmark vs all four templates (G3 verification)
python tools/benchmark.py --all-templates --hands 10000 --min-bb 5

# Build and validate submission (G4 verification)
python tools/import_audit.py
python tools/package.py --output submissions/v_final.zip --strict
python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip
```

## Layout

- `AGENTS.md` — full project brief for Codex
- `PROMPT.md` — `/goal` text to launch a Codex session
- `PLAN.md` — four-gate milestone plan (G0 scaffold → G4 hardening)
- `STATUS.md` — append-only audit log; check for current state
- `docs/` — tournament spec, API cheatsheet, playbooks, corpus index
- `src/` — strategy modules; `src/bot.py` is the real `decide()` entry
- `tools/` — training, benchmarking, packaging, auditing
- `tests/` — unit, integration, edge_cases, property
- `ext/fullhouse-engine/` — official engine clone (read-only)
- `submissions/` — built `bot.zip` artifacts

## Sandbox (sourced from `ext/fullhouse-engine/sandbox/Dockerfile`)
- Python 3.10
- Allowed: `eval7`, `numpy`, `scipy`, `treys`, `scikit-learn` + Python stdlib excluding the forbidden modules listed in `AGENTS.md`
- 2 s/decision, 768 MB RAM, 0.5 CPU, `--network none --read-only --no-new-privileges --user 1000:1000`
- Submission: `bot.py` (≤ 5 MB) at archive root, `data/` (≤ 200 MB), total ≤ 250 MB

## How the submission is built
`tools/package.py` writes a thin `bot.py` shim at the archive root that re-exports `decide` from `src.bot`. All strategy code stays under `src/`; blueprints under `data/`. The shim adds the archive directory to `sys.path` so `from src.bot import decide` resolves inside the sandbox.
