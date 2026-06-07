<div align="center">

# PokerBot — finals-as-submitted

*6-max no-limit Texas hold'em — the exact artifact submitted to the Fullhouse Hackathon 2026 finals*

</div>

> [!WARNING]
> **FROZEN — REFERENCE ONLY.** This branch preserves the unmodified bot submitted to the
> Fullhouse Hackathon 2026 finals: `submissions/v_final.zip` (sha256 `b108eff5…`) together with
> its extracted `src/` and `data/`. Nothing here is maintained.
> **For the maintained, post-finals build, documentation, and architecture, go to [`main`](../../tree/main).**

---

## What this branch is

A point-in-time snapshot of the finals submission, kept so the competition artifact stays
inspectable and reproducible exactly as it was scored. Code and blueprint data are intentionally
left untouched; bug fixes and improvements live only on `main`.

This was a 6-max no-limit hold'em bot built for the first
[**Fullhouse Hackathon 2026**](https://fullhousehackathon.com/) (lead sponsor
[Quadrature Capital](https://www.quadrature.ai/)). It qualified for the finals — the UK's first
quantitative poker hackathon. The design pairs a hand-tuned near-Nash heuristic blueprint
(distilled from public solver charts) with a bounded, opponent-adaptive exploit overlay,
running inside a locked-down sandbox.

## Sandbox constraints it was built for

- **Runtime:** Python 3.10 · pinned `eval7 / numpy / scipy / treys / scikit-learn`
- **Container:** `--network none --memory 768m --cpus 0.5 --read-only`
- **Budget:** 2 s per `decide()` (30 s warmup for blueprint load)

## Build & verify (no engine required)

```bash
pip install "Cython<3" wheel
pip install --no-build-isolation eval7==0.1.7
pip install -r requirements.txt
python tools/import_audit.py
pytest tests/edge_cases
```

Full architecture, strategy write-up, game-theoretic framing, corpus, and the complete
build/verify matrix are documented on **[`main`](../../tree/main)**.

---

<div align="center">

*Released under the [MIT License](LICENSE).*

</div>
