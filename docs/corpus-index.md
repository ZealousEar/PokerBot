# Corpus Index

A short reading list of the academic work the architecture draws on. Each entry notes the lever it informs; implementations cite the source at the call site (e.g. `# Source: Zinkevich 2007`).

## Sources

1. Zinkevich 2007 — *Regret Minimization in Games with Incomplete Information*. Lever: CFR mechanics — informs the offline blueprint solver.
2. Brown & Sandholm 2017 — *Libratus* (Science). Lever: subgame solving + real-time refinement — informs whether/how to add live refinement on top of the blueprint.
3. Brown & Sandholm 2019 — *Pluribus* (Science). Lever: 6-max blueprint, depth-limited solving, discrete sizing tree.
4. Bowling et al. 2015 — *Cepheus: Heads-up Limit Hold'em Poker is Solved* (Science). Lever: CFR+ trainer + abstraction (bucketing) for the flop strategy.
5. Lanctot et al. 2009 — *Monte Carlo Sampling for Regret Minimization in Extensive Games*. Lever: external-sampling MCCFR for the preflop and flop blueprint training.
6. Brown et al. 2019 — *Deep CFR*. Evaluated as a candidate for the final policy but not adopted: runtime PyTorch is outside the allowed library set, and while `.npz` + numpy inference is feasible, the project calendar did not allow training, integrating, and statistically validating a new neural policy against the locked baseline. Kept as background only.
7. Fullhouse engine — sandbox + reference-bot characterisation (`template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2`), each with its exploitable holes and counter-strategies. Lever: engine wiring + exploit-overlay targets.
8. Billings, Davidson & Schauenberg — opponent-modeling line (planned, not built; the engine reference-bot characterisation in (7) covered the per-bot exploitable holes adequately).

## Why this set

These cover the technique families actually used — a precomputed blueprint, state/action abstraction, and frequency-based opponent modeling — plus one family evaluated but not adopted for the final policy (Deep CFR, calendar-bound rather than infrastructure-bound). The reading list is deliberately small so effort goes to hardening rather than bibliography.

## Shipped vs intended

The **shipped** public policy is a hand-tuned heuristic blueprint — preflop range tables distilled from public solver charts (`src/ranges.py`) plus flop-bucket postflop rules — combined with eval7 Monte-Carlo equity (`src/equity.py`) and a bounded frequency overlay (`src/opponent_model.py`). The MCCFR (5) and CFR+ (4) *training* lines are the **intended** offline-trained replacement for that blueprint, not the running policy; Libratus-style real-time refinement (2) is referenced but dropped (compute-prohibitive at 0.5 CPU / 2 s). Each `src/*.py` module tags its `# Source` reference with a `# Status: SHIPPED | INTENDED` marker recording which it is.
