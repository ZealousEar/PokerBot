# Provenance

This repository is a public snapshot of a Fullhouse Hackathon 2026 entry. Some
historical numbers came from private match and exploitability (LBR) tooling.
The maintained tree now includes an official-engine match driver, but the old
raw runs and LBR implementation remain private. This file states which claims
are reproducible, historical, or still unmeasured.

## Shipped policy

The maintained public bot uses hand-tuned preflop action charts and postflop
commitment gates as a safety envelope. Inside actions those gates already
permit, `data/blueprint_policy_v1.json` supplies mixed sizes trained offline by
deterministic vanilla CFR over 234 small public-context games. Postflop equity
is joint across all active opponents, collision-free, and conditioned on public
action context. Opponent observations are incremental and keyed by `bot_id`;
because the public tree ships no `field_priors.npz`, exploit shifts are neutral
by default. `decide()` loads the committed JSON artifact at import time and
falls back to the safety charts if it is missing or fails its digest check; no
engine clone is needed at runtime.

## Claim → source → reproducible here

| Claim | Value | Source | Reproducible in this repo? |
|---|---|---|---|
| Finals result | Qualified; finished top 40 of 64 | Competition portal standings (external event) | No |
| Exploitability caps | ≤ 100 mbb/g preflop, ≤ 200 mbb/g aggregate (intended targets) | Private engine LBR harness | No — not measured here |
| bb/100 vs reference bots | not quoted in this repo | Private engine match harness | No |
| Benchmark variance | ~20 bb/100 (95% CI) at 10k hands | Private engine harness note | No — not measured here |
| Maintained policy shape | chart/commitment safety envelope + trained mixed sizing + joint multiway equity | `src/` · `data/blueprint_policy_v1.json` | Yes |
| Abstract blueprint training | 234 contexts · 1,170 rows · 1,200 iterations/context · 438 meaningfully mixed rows | artifact metadata · `tools/train_blueprint.py` | Yes — deterministic regeneration |
| Abstract convergence diagnostic | mean NashConv-style gap 2.98693416 → 0.00403651 | artifact metadata | Yes — for the stated one-decision abstraction only |
| Bounded-overlay cap | per-knob shift ∈ [−0.20, +0.20] | `tests/unit/test_overlay_clamp.py` | Yes |
| Overlay replay safety | repeated snapshots are idempotent; profiles survive seat reindexing by `bot_id` | `tests/unit/test_opponent_model_incremental.py` | Yes |
| Default adaptive behavior | neutral shifts without a validated `field_priors.npz` | `src/opponent_model.py` | Yes |
| Historical over-fold tendency | decision frequencies under synthetic pressure (no EV) for an earlier revision | `docs/results/overfold-postmortem.md` | Historical — the current policy has changed |
| Large-call pricing | `CALL_EQUITY_BUFFER` = 0.015; no arbitrary 25% cap; structural near-dead guard remains | `tests/unit/test_call_equity_buffer.py` · edge suite · `src/commitment.py` | Yes |
| MC-equity accuracy | MC → exact enumeration; AKs vs QQ ≈ 46% | `tests/unit/test_equity_accuracy.py` · `tools/equity_study.py` | Yes |
| Multiway equity contract | weighted collision-free holdings, fractional ties, deterministic/adaptive MC, exact tractable rivers | `tests/unit/test_multiway_equity.py` | Yes |
| Preflop RFI ranges | 13×13 grids straight from `src.ranges` | `tools/plot_preflop_heatmap.py` | Yes |
| Paired evaluator | cyclic six-seat schedule, common match IDs/seeds, clustered bootstrap CI, raw manifests | `tools/evaluation.py` · `tests/unit/test_evaluation_harness.py` | Yes with official engine clone |
| Qualifier-history analysis | official rich events; optional captured-state decision replay | `tools/qualifier_replay.py` | Yes with supplied history |

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
separate, gitignored checkout). The historical bb/100 figures, LBR caps, and
variance note cannot be reconstructed because their original raw runs and LBR
implementation are not committed. The maintained `tools/benchmark.py` and
`tools/self_play.py` now drive the public official engine and write manifests,
raw JSONL, and confidence-interval summaries; they fail non-zero when that
checkout is absent. This makes new experiments reproducible without
retroactively validating the old private figures.
