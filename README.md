<div align="center">

# PokerBot

**A Fullhouse Hackathon 2026 entry**
*6-max no-limit Texas hold'em — blueprint + bounded exploit overlay*

`Python 3.10`  ·  `eval7`  ·  `numpy`  ·  `scipy`  ·  `treys`  ·  `scikit-learn`

</div>

```
       ╭──────────────────────────────────────────────────╮
       │                                                  │
       │    near-Nash blueprint  +  bounded overlay       │
       │                                                  │
       │    2 s / decide   ·   0.5 CPU   ·   768 MB RAM   │
       │                                                  │
       ╰──────────────────────────────────────────────────╯
```

---

## Overview

A 6-max no-limit Texas hold'em bot built for the first **Fullhouse Hackathon 2026** (lead sponsor Quadrature Capital; £4,000+ prize pool). The tournament runs in two regimes that pull in opposite directions and dictate the architecture below:

| When           | Stage                       | Format                                                                                                            |
| -------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **2026-06-01** | Qualifier (Swiss)           | 400-hand 6-max matches; ranked by cumulative chip delta; top 64 advance                                           |
| **2026-06-05** | Finals (Swiss / cumulative) | Phase 1 "The Bubble": ~40 Swiss-paired 6-max matches, 800 hands each, ranked by cumulative chips; Phase 2: final table |

---

## Results

- **Qualifiers** — two Swiss rounds ranked by cumulative chip delta. Finished in the **top 64** and advanced to the finals.
- **Finals** — a fresh Swiss/cumulative competition among the 64 qualifiers (standings reset to equal footing). Finished in the **top 40**.

---

## Strategy in One Paragraph

Two-regime tournament dictates a two-layer strategy. The **blueprint** (`src/preflop_lookup.py` + `src/postflop.py`) approximates Nash over an abstracted game — external-sampling MCCFR for preflop and CFR+ over flop buckets for postflop. The **overlay** (`src/opponent_model.py`) deviates from the blueprint toward best-response against the inferred opponent type; magnitude is bounded so a worst-case counter-exploit costs us less than the expected gain. The leverage point is abstraction: a discrete sizing tree `{1/3 pot, 2/3 pot, pot, 2× pot, all_in}` (Pluribus 2019) and flop bucketing capped at 200 buckets × 50 hand-strength bins (Cepheus 2015). The safety metric is exploitability via Local Best-Response over a fixed 20-spot suite (Lisý & Bowling 2017), capped at ≤ 100 mbb/g preflop and ≤ 200 mbb/g aggregate.

---

## Architecture

```
                          ┌──────────────────────────────┐
                          │         decide(state)        │
                          └───────────────┬──────────────┘
                                          │
                          ┌───────────────┴────────────────┐
                          ▼                                ▼
                 ┌─────────────────┐              ┌─────────────────┐
                 │    Blueprint    │   overlay    │ Opponent Model  │
                 │   (near-Nash)   │ ◄──shift──── │  (frequency,    │
                 │                 │              │   bounded)      │
                 └────────┬────────┘              └─────────────────┘
                          │
                 ┌────────┴─────────┐
                 ▼                  ▼
          preflop_lookup        postflop
          (MCCFR table)        (CFR+ buckets
                                + eval7 equity)
```

---

## Game-Theoretic Frame

| Regime                      | Field        | Bias                              | Why                                                          |
| --------------------------- | ------------ | --------------------------------- | ------------------------------------------------------------ |
| Qualifier (Swiss)           | Mostly weak  | Max exploit                       | Overlay dominates — chip extraction wins                     |
| Finals (Swiss / cumulative) | Strong field | Near-Nash floor + bounded overlay | Cumulative extraction; shrinkage penalizes variance, so cap the downside |

We replace Libratus-style real-time subgame solving (compute-prohibitive at 0.5 CPU / 2 s) with a frequency-based overlay whose deviation magnitude is bounded.

**Dropped, with reasons:**
- Real-time subgame solving (Libratus 2017) — compute budget
- Deep CFR (Brown 2019) — no PyTorch / TF in the allowed library set
- Nested endgame solving — same compute reasons

---

## Repository Layout

```
PokerBot/
├── src/                          strategy modules
│   ├── bot.py                    decide() entry — legalizes actions, timeout fallback
│   ├── preflop_lookup.py         offline-trained preflop range
│   ├── ranges.py                 6-max range representation
│   ├── postflop.py               flop bucketing + turn/river play
│   ├── commitment.py             stack-off / commitment gating
│   ├── hand_features.py          board-texture + hand classifiers
│   ├── equity.py                 eval7-backed Monte Carlo equity
│   ├── opponent_model.py         frequency-based exploit overlay
│   ├── sizing.py                 discrete bet-sizing tree
│   └── timeout_guard.py          2 s budget enforcement
├── tools/                        benchmark · package · import-audit · self-play
├── tests/                        edge-case + integration suites
├── data/                         *.npz blueprints (gitignored, regen via tools/)
├── docs/                         tournament spec · API cheatsheet · corpus index
├── ext/fullhouse-engine/         official engine clone (separate, gitignored)
├── submissions/                  built bot.zip artifacts (gitignored)
├── LICENSE                       MIT
├── requirements.txt              pinned dependencies
└── README.md                     this file
```

---

## Setup

```bash
# eval7 needs Cython<3 and --no-build-isolation
pip install "Cython<3"
pip install --no-build-isolation eval7==0.1.7
pip install -r requirements.txt
```

> **Python 3.10 only.** `eval7==0.1.7` bundles pre-generated C bindings that target the pre-3.11 `longintrepr.h` layout.

---

## Build & Verify

These run in a clean clone, with no engine required:

| Step             | Command                                                           |
| ---------------- | ---------------------------------------------------------------- |
| Import audit     | `python tools/import_audit.py`                                   |
| Edge cases       | `pytest tests/edge_cases`                                        |
| Build submission | `python tools/package.py --output submissions/bot.zip --strict` |

The remaining steps need the official engine cloned into `ext/fullhouse-engine/` — a separate, gitignored checkout that provides the sandbox, validator, and local match driver:

| Step              | Command                                                                         |
| ----------------- | ------------------------------------------------------------------------------- |
| Self-play         | `python tools/self_play.py --opponent <name> --hands <N>`                       |
| Benchmark         | `python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42` |
| Engine validator  | `python ext/fullhouse-engine/sandbox/validator.py submissions/bot.zip`          |
| Sandbox smoke run | `python tools/smoke_run.py --zip submissions/bot.zip --hands 200`               |

---

## Sandbox Invariants

Sourced from `ext/fullhouse-engine/sandbox/{validator.py,Dockerfile,runner.py}` — these are hard constraints:

- **Runtime:** Python 3.10
- **Pinned libraries:** `eval7==0.1.7`, `numpy==1.26.4`, `scipy==1.13.0`, `treys==0.1.8`, `scikit-learn==1.5.2`
- **Container:** `--network none --memory 768m --cpus 0.5 --read-only --no-new-privileges --user 1000:1000`
- **Budget:** 2 s per `decide()`; one warmup call before hand 1 with a 30 s budget for blueprint load
- **Submission size:** `bot.py` ≤ 5 MB, `data/` ≤ 200 MB, total ≤ 250 MB
- **Layout:** `bot.py` at archive root re-exports `decide` from `src/bot.py`; no other `.py` at root, no `.py` inside `data/`, no symlinks, no path traversal

### Valid actions

```python
{"action": "fold"}
{"action": "check"}                     # only when can_check is True
{"action": "call"}
{"action": "raise", "amount": N}        # N is the TOTAL chips, not the increment
{"action": "all_in"}                    # distinct from raise-to-stack
```

Invalid actions default to fold; the runner emits `{"action": "fold", "error": ...}` on exception or timeout.

---

## Development Gates

The bot was built in verified stages, each closed only after its checks passed:

```
G0  Scaffold      ── Repo + tooling skeleton
G1  Wired         ── decide() returns legal actions in the engine
G2  Preflop       ── Blueprint preflop range table
G3  Postflop      ── CFR+ flop buckets + overlay
G4  Hardened      ── Edge-case sweep + smoke validation
G5  Verified      ── LBR cap + ablation + self-play ratchet
```

Each gate was held to numeric evidence — import audit, edge-case sweep, benchmark, and an exploitability (LBR) check — before the next one started.

---

## Corpus

Architectural decisions anchor to academic work indexed in [`docs/corpus-index.md`](docs/corpus-index.md):

| Note                                 | Lever                                  |
| ------------------------------------ | -------------------------------------- |
| CFR (Zinkevich 2007)                 | Offline blueprint solver mechanics     |
| MCCFR (Lanctot 2009)                 | External-sampling variance reduction   |
| Cepheus (Bowling 2015)               | State abstraction — buckets and bins   |
| Libratus (Brown & Sandholm 2017)     | Subgame solving (referenced, dropped)  |
| LBR (Lisý & Bowling 2017)            | Exploitability audit as safety metric  |
| Pluribus (Brown & Sandholm 2019)     | Discrete sizing tree; 6-max blueprint  |

Implementations cite their source at the call site.

---

<div align="center">

*Released under the [MIT License](LICENSE).*

</div>
