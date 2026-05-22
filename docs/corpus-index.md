# Corpus Index

Wikilinks into the external Obsidian vault under `Agentic/05 Research/PokerBot/`. Surfaced here so Codex can reach the deep references when implementing a technique. Cite with `# Source: [[note-name]]` in code.

## Build status

Notes built 2026-05-22 via parallel subagents (not the `/research` skill — concurrent slash-command invocations are blocked, so the build went DIY with WebFetch + WebSearch). Files live under the external Obsidian vault path `Agentic/05 Research/PokerBot/` and resolve to the wikilinks below.

If you want a `/research`-shaped note for any source, run that skill manually with the URL and let it overwrite the corresponding file.

## Sources

1. [[CFR-Zinkevich-2007]] — *Regret Minimization in Games with Incomplete Information*. Lever: CFR mechanics — informs the offline blueprint solver.
2. [[Libratus-Brown-Sandholm-2017]] — *Libratus* (Science). Lever: subgame solving + real-time refinement — informs whether/how to add live refinement on top of our blueprint.
3. [[Pluribus-Brown-Sandholm-2019]] — *Pluribus* (Science). Lever: 6-max blueprint, depth-limited solving, discrete sizing tree.
4. [[Cepheus-Bowling-2015]] — *Heads-up limit hold'em is solved*. Lever: CFR+ trainer + abstraction (bucketing) for the flop strategy.
5. [[MCCFR-Lanctot-2009]] — *Monte Carlo Sampling for Regret Minimization*. Lever: external-sampling MCCFR for both `tools/train_preflop.py` and `tools/train_flop.py`.
6. [[DeepCFR-Brown-2019]] — *Deep CFR*. Read-only — out of scope for our timeline (no PyTorch/TF in the sandbox); note documents *why* we skip it.
7. [[Engine-Fullhouse]] — Engine sandbox + reference bot characterisation (`template`, `aggressor`, `mathematician`, `shark`, `ref_bot_2`) with exploitable holes and counter-strategies. Lever: G1 wiring + G3 exploit-overlay targets.
8. (Billings/Davidson/Schauenberg opponent-modeling note was planned but not built — the engine reference note covers per-bot exploitable holes adequately for G3.)

## Why this set

These eight cover the technique families we will actually use (precomputed blueprint + abstraction + opponent modeling) and one excluded family (Deep CFR — too costly to implement here). The plan caps corpus reading at 8 sources / 6 hours so the budget goes to hardening, not bibliography.
