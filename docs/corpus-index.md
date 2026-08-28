# Corpus Index

A short reading list of the academic work the architecture draws on. Each entry notes the lever it informs; implementations cite the source at the call site (e.g. `# Source: Zinkevich 2007`).

## Sources

1. Zinkevich 2007 — *Regret Minimization in Games with Incomplete Information*. Lever: CFR mechanics — informs the offline blueprint solver.
2. Brown & Sandholm 2017 — *Libratus* (Science). Lever: subgame solving + real-time refinement — informs whether/how to add live refinement on top of the blueprint.
3. Brown & Sandholm 2019 — *Pluribus* (Science). Lever: 6-max blueprint, depth-limited solving, discrete sizing tree.
4. Bowling et al. 2015 — *Cepheus: Heads-up Limit Hold'em Poker is Solved* (Science). Lever: regret-minimization training and abstraction (bucketing) for the compact lookup strategy.
5. Lanctot et al. 2009 — *Monte Carlo Sampling for Regret Minimization in Extensive Games*. Evaluated as a scalable follow-on; the shipped small abstraction instead uses deterministic full-tree CFR so its artifact is exactly reproducible.
6. Brown et al. 2019 — *Deep CFR*. Evaluated as a candidate for the final policy but not adopted: runtime PyTorch is outside the allowed library set, and while `.npz` + numpy inference is feasible, the project calendar did not allow training, integrating, and statistically validating a new neural policy against the locked baseline. Kept as background only.
7. Fullhouse engine — sandbox + reference-bot characterisation (`template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2`), each with its exploitable holes and counter-strategies. Lever: engine wiring + exploit-overlay targets.
8. Billings, Davidson & Schauenberg — opponent-modeling line. Lever: the incremental, bounded per-`bot_id` frequency model and conservative range reweighting.

## Why this set

These cover the technique families actually used — a precomputed blueprint, state/action abstraction, and frequency-based opponent modeling — plus one family evaluated but not adopted for the final policy (Deep CFR, calendar-bound rather than infrastructure-bound). The reading list is deliberately small so effort goes to hardening rather than bibliography.

## Shipped vs deliberately bounded

The **shipped** policy combines a deterministic offline-trained mixed lookup table with conservative hand-tuned action gates, joint-range eval7 equity, and a bounded incremental opponent model. The trainer solves a small one-decision Bayesian abstraction with full-tree vanilla CFR; it is genuinely optimized and live for discrete sizing mixes, but it is not a six-player no-limit equilibrium solver. Preflop charts and postflop commitment logic therefore retain authority over fold/call/raise categories. Libratus-style live refinement remains dropped as compute-prohibitive under the 0.5 CPU / 2 s limit. Module headers record the exact shipped scope at each call site.
