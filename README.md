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

## Mission

Win the Fullhouse Hackathon 2026 by submitting `submissions/v_final.zip`:

| When           | Stage              | Format                                    |
| -------------- | ------------------ | ----------------------------------------- |
| **2026-06-01** | Qualifier (Swiss)  | 400-hand matches; cumulative chip delta   |
| **2026-06-05** | Finals (bracket)   | 64-player single-elimination              |

The two regimes pull in opposite directions and dictate the architecture below.

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

| Regime              | Field           | Bias            | Why                                              |
| ------------------- | --------------- | --------------- | ------------------------------------------------ |
| Qualifier (Swiss)   | Mostly weak     | Max exploit     | Overlay dominates — chip extraction wins         |
| Finals (bracket)    | Sharp survivors | Near-Nash floor | Blueprint dominates — bound the downside         |

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
│   ├── bot.py                    decide() entry
│   ├── preflop_lookup.py         offline-trained preflop range
│   ├── postflop.py               flop bucketing + turn/river equity
│   ├── equity.py                 eval7-backed Monte Carlo
│   ├── opponent_model.py         frequency-based exploit overlay
│   ├── ranges.py                 range representation
│   ├── sizing.py                 discrete bet-sizing tree
│   └── timeout_guard.py          2 s budget enforcement
├── tools/                        train · benchmark · package · audit
├── tests/                        unit · integration · edge_cases · property
├── data/                         *.npz blueprints (gitignored, regen via tools/)
├── docs/                         tournament spec · API cheatsheet · corpus index
├── ext/fullhouse-engine/         official engine clone (read-only, gitignored)
├── submissions/                  built bot.zip artifacts (gitignored)
├── .githooks/pre-commit          submission verification gate
├── AGENTS.md                     project brief: invariants · frame · policies
├── PLAN.md                       G1 → G5 gate roadmap
├── PROMPT.shared.md              contract: done-when · verification · proof-of-green
├── STATUS.md                     append-only audit log
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

> **Python 3.10 only.** `eval7==0.1.7` ships pre-generated C bindings that target the pre-3.11 `longintrepr.h` layout.

---

## Build & Verify

| Step               | Command                                                                             |
| ------------------ | ----------------------------------------------------------------------------------- |
| Self-play          | `python tools/self_play.py --opponent <name> --hands <N>`                           |
| Benchmark          | `python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42`     |
| Import audit       | `python tools/import_audit.py`                                                      |
| Edge cases         | `pytest tests/edge_cases -x`                                                        |
| Build submission   | `python tools/package.py --output submissions/<name>.zip --strict`                  |
| Engine validator   | `python ext/fullhouse-engine/sandbox/validator.py submissions/<name>.zip`           |
| Sandbox smoke run  | `python tools/smoke_run.py --zip submissions/<name>.zip --hands 200`                |

The pre-commit hook activates per-clone with `git config core.hooksPath .githooks` and refuses commits that break submission verification. Override with `FORCE_COMMIT=1 git commit ...` for explicit rollbacks only.

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

## Gate Progression

```
G0  Scaffold      ── Repo + tooling skeleton
G1  Wired         ── decide() returns legal actions in the engine
G2  Preflop       ── Blueprint preflop range table
G3  Postflop      ── CFR+ flop buckets + overlay
G4  Hardened      ── Edge-case sweep + smoke validation
G5  Verified      ── LBR cap + ablation + self-play ratchet
```

Each gate appends a GREEN / AMBER / RED entry to `STATUS.md` with verification numbers, files changed, and the corpus note that drove the design (`# Source: [[note-name]]`).

---

## Internal Tournament Results — 2026-05-22 Snapshot

Two agents — **Claude Code** in `~/Code/PokerBot-claude/` (branch `claude`) and **Codex CLI** in `~/Code/PokerBot-codex/` (branch `codex`) — executed G1 → G5 in parallel from the same `scaffold-baseline` tag, each writing to its own worktree only. Both posted `## FINAL SUBMITTED` on their `STATUS.md`. A paired-seed head-to-head between their `v_final.zip` artifacts via [`tools/h2h.py`](tools/h2h.py) decided the qualifier ship.

### vs reference templates &nbsp;·&nbsp; bb/100 &nbsp;·&nbsp; paired-seed &nbsp;·&nbsp; n=10,000

```
                   claude     codex      ── bar (1 █ = 10 bb/100) ──
                   bb/100     bb/100     claude            codex
                   --------   --------   --------          ------------------
template            +26.42     +71.82    ███               ███████
aggressor*         +433.33    +178.09    wide CI ▶         ██████████████████
mathematician       +31.69    +144.60    ███               ██████████████
shark               +27.96     +70.16    ███               ███████
ref_bot_2           +31.69    +144.60    ███               ██████████████
```

\* claude's +433.33 vs aggressor carries a 95 % CI of ±227 because aggressor busts in ~12 hands. Codex's +178.09 comes from longer matches and is the more trustworthy number.

### Head-to-head &nbsp;·&nbsp; claude `v_final.zip` &nbsp;vs&nbsp; codex `v_final.zip`

```
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║                        H E A D - T O - H E A D                         ║
║                                                                        ║
║                       ╭─────────────────────╮                          ║
║                       │     CODEX  WINS     │                          ║
║                       ╰─────────────────────╯                          ║
║                                                                        ║
║         50 matches  ·  paired-seed  ·  seat-swap  ·  8,379 hands       ║
║                                                                        ║
║         claude per-match BB delta :  −65.40 BB                         ║
║         95 % CI                   :  [−77.63, −51.35]                  ║
║         claude bb/100             :  −39.03                            ║
║                                                                        ║
║         claude busted in 24 / 50 matches  (48 %)                       ║
║         codex never busted (0 / 50)                                    ║
║                                                                        ║
║         bot errors  :  claude 0    codex 0                             ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
```

### Local Best-Response exploitability &nbsp;·&nbsp; lower is closer to Nash &nbsp;·&nbsp; 20-spot suite

```
preflop
  claude   ██████████████████                              35.5 mbb/g   (cap ≤ 100)
  codex    ███████████                                     22.0 mbb/g   (cap ≤ 100)

aggregate
  claude   ████████████████████████████████████████████    87.4 mbb/g   (cap ≤ 200)
  codex    ██████                                          12.8 mbb/g   (cap ≤ 200)
```

Codex's aggregate LBR of 12.8 mbb/g is striking — deep inside the safety band. Consistent with the head-to-head: codex's overlay extracts heavily *against* sophisticated opponents while leaving few exploitable holes itself on the LBR probe set.

### Verdict

```
qualifier  2026-06-01   ──▶   ship  codex/v_final.zip   (sha 5d65561e…)
finals     2026-06-05   ──▶   re-evaluate on 2026-06-02 patch window
```

Codex takes the qualifier slot decisively. Head-to-head, its frequency overlay exploits patterns in claude's blueprint and busts claude in roughly half the matches. The finals decision is deferred to the 2026-06-02 patch window: at that point we either re-tune codex's overlay frequencies against the actual finals field, or fall back to claude's safer blueprint if the field looks adaptive enough to counter-exploit codex's overlay.

The runner used for the verdict is preserved at [`tools/h2h.py`](tools/h2h.py) for re-use after the patch window.

---

## Worktree Layout

The repo runs three parallel trees off a shared `.git`:

| Tree                    | Branch   | Role                                              |
| ----------------------- | -------- | ------------------------------------------------- |
| `~/Code/PokerBot/`      | `main`   | canonical; coordinator                            |
| `~/Code/PokerBot-claude/` | `claude` | Claude Code agent worktree                        |
| `~/Code/PokerBot-codex/`  | `codex`  | Codex CLI agent worktree                          |

Each agent edits only its own worktree. No agent edits `ext/fullhouse-engine/`, another agent's tree, or `main` during overnight runs.

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

*Private competition repo · not for redistribution*

</div>
