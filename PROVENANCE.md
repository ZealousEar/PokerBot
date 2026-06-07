# Provenance

This repository is a public, recruiter-facing snapshot of a Fullhouse Hackathon
2026 entry. Some numbers in the architecture write-up were produced on a
**private engine harness** — the competition sandbox plus local match and
exploitability (LBR) tooling — that is not part of this public tree. This file
states, for each claim, where it came from and whether you can reproduce it
here. Nothing below is a fabricated figure: a claim is either reproducible from
this repo or marked as a private-harness number that is *not* reproduced here.

## Shipped policy

The shipped public bot is a **hand-tuned heuristic blueprint** — preflop range
tables distilled from public solver charts (`src/ranges.py`) plus flop-bucket
postflop rules — combined with eval7 Monte-Carlo equity (`src/equity.py`) and a
bounded frequency overlay (`src/opponent_model.py`). MCCFR (preflop) and CFR+
(flop buckets) are the **intended offline-trained replacement**, not the running
policy. `decide()` runs with no `data/*.npz` and no engine clone.

## Claim → source → reproducible here

| Claim | Value | Source | Reproducible in this repo? |
|---|---|---|---|
| Finals result | Qualified; finished top 40 of 64 | Competition portal standings (external event) | No |
| Exploitability caps | ≤ 100 mbb/g preflop, ≤ 200 mbb/g aggregate (intended targets) | Private engine LBR harness | No — not measured here |
| bb/100 vs reference bots | not quoted in this repo | Private engine match harness | No |
| Benchmark variance | ~20 bb/100 (95% CI) at 10k hands | Private engine harness note | No — not measured here |
| Shipped policy shape | hand-tuned blueprint + eval7 equity + bounded overlay | `src/` | Yes |
| Bounded-overlay cap | per-knob shift ∈ [−0.20, +0.20] | `tests/unit/test_overlay_clamp.py` | Yes |
| Over-fold tendency | decision frequencies under synthetic pressure (no EV) | `tools/overfold_probe.py` · `docs/results/overfold-postmortem.md` | Yes |
| MC-equity accuracy | MC → exact enumeration; AKs vs QQ ≈ 46% | `tests/unit/test_equity_accuracy.py` · `tools/equity_study.py` | Yes |
| Preflop RFI ranges | 13×13 grids straight from `src.ranges` | `tools/plot_preflop_heatmap.py` | Yes |
| Decision pipeline | legalize → blueprint → equity → overlay → sizing | `notebooks/decision_walkthrough.ipynb` | Yes |

## Finals artifact integrity

The exact finals submission is committed at `submissions/v_final.zip`.

```
SHA256(submissions/v_final.zip) = b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b
```

Verify (from the repo root):

```bash
( cd submissions && shasum -a 256 -c v_final.zip.sha256 )
```

The unmodified, byte-for-byte submission also lives on the
[`finals-as-submitted`](../../tree/finals-as-submitted) branch; this `main`
branch is the post-finals maintained build.

## What "private engine harness" means

The competition ran bots inside a sandboxed engine (`ext/fullhouse-engine/`, a
separate, gitignored checkout). The bb/100 benchmarks, the LBR exploitability
caps, and the variance figure were all produced by driving that engine, so they
are not reproducible from this repo alone — and `tools/benchmark.py` /
`tools/self_play.py` exit non-zero, rather than print a number, when the engine
clone is absent. The engine-free artifacts in the table above (tests, probes,
the notebook) are fully reproducible in a clean clone.
