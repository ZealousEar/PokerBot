# Public Competitor Intel - Fullhouse PokerBot

Date: 2026-05-24
Scope: Public GitHub data only. Excludes `ZealousEar`, which is our own account.

## Executive Summary

The stargazer list for `uzlez/fullhouse-engine` did not expose a finished public competitor bot after excluding `ZealousEar`. The visible stargazer forks are mostly untouched copies of the official engine.

The stronger signal is in the broader public fork network. Several non-stargazer forks contain valid bots that beat the bundled reference table in short local smoke tests. This means the likely qualifier threat is not a private super-solver; it is a population of simple, robust range plus equity bots that can farm weak template opponents.

Threat level:

- Qualifier: medium-high.
- Finals: medium, with high uncertainty.
- Main operational risk: overestimating reference-bot benchmarks. Beating the bundled bots is no longer a meaningful acceptance criterion.

## Methodology

Sources checked:

- `https://github.com/uzlez/fullhouse-engine/stargazers`
- GitHub public repo/profile pages for all public stargazers.
- GitHub public compare patches against `uzlez/fullhouse-engine`.
- GitHub public fork network at `https://github.com/uzlez/fullhouse-engine/network/members`.
- Raw public bot files and data files where available.
- Local engine validator and small smoke matches in `ext/fullhouse-engine`.

Guardrails:

- Public-source review only.
- No private repository access.
- No authentication bypass.
- No copying competitor code into our bot.
- Benchmark results are directional only; 300-hand samples are high variance.

## Stargazer Sweep

Public stargazers checked: 32.

After excluding `ZealousEar`, the relevant public stargazer repos found were:

| User | Public repo signal | Assessment |
| --- | --- | --- |
| `rishabhkarwal` | `rishabhkarwal/fullhouse` fork | Main branch compare patch empty versus upstream. Low direct evidence. |
| `stoppedtime24` | `stoppedtime24/fullhouse-engine` fork | Main branch compare patch empty versus upstream. Low direct evidence. |
| `BouillieAnonymous` | `BouillieAnonymous/fullhouse-engine` fork | Main branch compare patch empty versus upstream. Low direct evidence. |
| `chunyang-w` | `chunyang-w/fullhouse-engine` fork | Main branch compare patch empty versus upstream. Low direct evidence. |
| `AyushGupta05` | `AyushGupta05/fullhouse-engine` fork | Main branch compare patch empty versus upstream. Low direct evidence. |
| `andrinjoos` | `andrinjoos/Kuhn_Poker` | Empty/unrelated Kuhn poker repo. Low threat. |

Other hits from profile search were unrelated Telegram bots, trading bots, Discord bots, or older non-poker hackathons.

Conclusion: stargazers alone do not reveal a strong public competitor bot.

## Broader Fork Network Findings

The fork network revealed public bot work outside the stargazer list.

### `agrawalneel25/fullhouse-engine`, branch `neel-work`

Evidence:

- Compare subject: "Add poker bot collaboration tooling".
- Adds `bots/neel/bot.py`.
- 257-line bot.
- Imports `eval7` when available.
- Strategy summary from code comments: table-driven preflop ranges, Monte Carlo postflop equity, pot-odds calls, value bets, occasional semi-bluffs from late position.

Validator:

- PASS.

Smoke benchmark versus bundled reference table:

- Setup: 6-player table, 300 hands per seed, seeds 40-44.
- Opponents: aggressor, mathematician, shark, ref_bot_2, template.
- Deltas: `+14974`, `+26850`, `+16750`, `+16862`, `+6000`.
- Average delta: `+16287`.
- Positive runs: 5/5.

Threat assessment:

- High qualifier threat.
- This is the clearest evidence that a compact hand-tuned bot can crush the reference field.
- Likely weakness: fixed thresholds, simple public-card MC, no deep opponent model.

### `Linglingletsgo/fullhouse-engine`, branch `blueprint-exploit-bot`

Evidence:

- Compare subject: "Add blueprint exploit poker bot".
- Adds `bots/dominic/bot.py`.
- Adds `bots/dominic/data/blueprint.json`.
- 465-line bot plus 39KB JSON blueprint.
- JSON contains preflop hand classes, RFI ranges, street thresholds, and SPR buckets.
- Code includes an opponent profile, fold-rate/aggression adjustments, postflop equity proxy, and river overbet fold controls.

Validator:

- PASS.

Smoke benchmark versus bundled reference table:

- Setup: same 5x300-hand table as above.
- Deltas: `+10228`, `+18150`, `+14100`, `+16825`, `+4800`.
- Average delta: `+12821`.
- Positive runs: 5/5.

Threat assessment:

- High qualifier threat.
- More structured than `agrawalneel25`, but still threshold/proxy driven rather than a true solver.
- Likely weakness: predictable thresholding, exploitable river folds, no real showdown equity engine.

### `famadeo/fullhouse-engine`, branch `main`

Evidence:

- Compare subjects include:
  - "Add Codex Holdem bot and benchmark gates"
  - "Add survival reward model heads"
  - "Add public belief state foundation"
  - "Add range-conditioned equity sampling"
  - "Add benchmarked Hold'em risk gates and forensics"
- Adds `bots/codex_holdem/bot.py`.
- Adds `bots/codex_holdem/data/model.json`.
- 2359-line bot plus 60KB model JSON.
- Model JSON contains:
  - `preflop_strategy`
  - `postflop_ev`
  - `range_equity`
  - `risk_gates`
  - `river_blueprint`
  - `commitment_blueprint`
  - public belief feature names and training summaries
- Important caveat: `runtime_enabled` is false in the model JSON. Much of the model-head machinery may be scaffolded rather than active.

Validator:

- PASS.

Smoke benchmark versus bundled reference table:

- Setup: same 5x300-hand table as above.
- Deltas: `-100`, `+13750`, `+12650`, `+14150`, `+900`.
- Average delta: `+8270`.
- Positive runs: 4/5.

Threat assessment:

- Medium-high qualifier threat.
- More code and tooling than most public bots, with risk gates and range-conditioned equity sampling.
- Potential weakness: complexity, inactive model runtime, possible over-conservatism in some seeds.

### `saroopjagdev/fullhouse-engine`, branch `stable-stage18`

Evidence:

- Compare patch contains 24 staged commits.
- Adds `bots/mybot/bot.py`.
- 4959-line bot.
- Strategy features visible in code:
  - staged variants
  - preflop tree
  - opponent classification
  - anti-punt layer
  - leak adjustment layer
  - river defense variants
  - Monte Carlo equity configuration
  - exploit/leak multipliers
- Default variant appears to resolve to `M2_BASELINE_FROZEN`.

Validator:

- PASS.

Smoke benchmark versus bundled reference table:

- Setup: same 5x300-hand table as above.
- Deltas: `+7550`, `-10000`, `+15900`, `+17200`, `-10000`.
- Average delta: `+4130`.
- Positive runs: 3/5.

Threat assessment:

- Medium threat.
- Potentially strong when it survives, but unstable in short samples with two busts.
- Likely weakness: high complexity, variant drift, possibly brittle postflop/river guards.

### `vladimirfilip/fullhouse-engine`, branch `main`

Evidence:

- Compare subjects:
  - "Implement basic monte carlo equity algo"
  - "Implement equity-based decision-making, with simple..."
- Adds `bots/vlad/bot.py`.
- Simple eval7 Monte Carlo equity and pot-odds action selection.

Validator:

- FAIL under local validator with `.venv` available.
- Failure: assertion in `short_stack_all_in_decision`.

Threat assessment:

- Low unless fixed privately.
- The core idea is common and easy to repair, so use the archetype in benchmarks even if this public file is not submission-ready.

### `Littleguygabe/fullhouse-poker`, branch `main`

Evidence:

- Public fork with several bots:
  - `aof`
  - `memoryTest`
  - `mybot`
  - `ranger`
- `aof` is always all-in.
- `memoryTest` appears to test global memory and folds.
- `ranger` loads preflop ranges but returns fold.
- `mybot` has preflop range logic but postflop equity path is incomplete.

Validator:

- Some bots pass validator because they return legal actions.

Smoke benchmark:

- `little_aof`: busts quickly in the 300-hand smoke.
- `little_mybot`: poor/incomplete performance.

Threat assessment:

- Low in public form.

## Benchmark Caveats

The smoke tests were deliberately small:

- 5 paired seeds.
- 300 hands per seed.
- Same bundled reference table each run.
- Local dev mode, not Docker.

These runs are useful for triage only. They prove the public bots are functional and can exploit weak reference bots; they do not estimate true bb/100 with tournament-grade confidence.

## Strategic Implications

1. Reference-bot dominance is an inadequate bar.

The public `agrawalneel25`, `Linglingletsgo`, `famadeo`, and `saroopjagdev` bots all pass the validator and can beat the bundled bots in local short samples. Our acceptance gate should include stronger archetype opponents.

2. The common public pattern is simple but effective.

The most common pattern is:

- preflop hand/range table
- eval7 Monte Carlo equity or a cheap equity proxy
- pot-odds aware calls
- value betting at fixed thresholds
- some late-position/semi-bluff pressure
- basic river caution

This is enough to farm weak opponents in the qualifier.

3. Public evidence of true solver work is weak.

I found no public evidence of:

- real MCCFR training results
- CFR+ postflop abstraction tables
- exploitability measurement
- robust LBR guardrails
- large trained neural models active at runtime

This supports the current blueprint plus bounded overlay strategy, but only if our implementation actually benchmarks against stronger public-style archetypes.

## Recommended Defensive Benchmarks

Create local archetype opponents based on behavior, not copied code:

1. `range_mc_pot_odds`
   - Mimics `agrawalneel25`.
   - Table preflop, eval7 MC postflop, pot-odds call thresholds.

2. `blueprint_threshold_exploit`
   - Mimics `Linglingletsgo`.
   - JSON-style RFI ranges, fixed street thresholds, fold-rate/aggression overlays.

3. `risk_gated_conservative`
   - Mimics `famadeo`.
   - Equity sampling with risk gates, multiway/wet-board discounts, stackoff veto.

4. `stage_variant_anti_punt`
   - Mimics `saroopjagdev`.
   - Conservative preflop tree plus anti-punt river defense.

5. `monte_carlo_basic`
   - Mimics the repaired form of `vladimirfilip`.
   - Pure MC equity plus pot odds, simple raises with high equity.

Acceptance should use paired seeds, not one-off 10K or 300-hand runs.

## Tactical Exploit Targets

Likely profitable attack surfaces:

- Fixed threshold callers overfold when bet sizing pushes required equity just above their margin.
- MC bots overvalue raw showdown equity in multiway wet boards unless they have explicit discounts.
- Conservative river bots overfold medium-strength bluff-catchers to large river pressure.
- Range-table preflop bots are predictable in blind-defense and 3-bet pots.
- All-in/simple bots are easy chip donors but should not shape finals strategy.

Likely defensive requirements:

- Avoid punting into their strong-equity value thresholds.
- Do not make our own river defense as brittle as the public threshold bots.
- Add postflop multiway/wet-board equity realization penalties.
- Add pressure-aware preflop defense so simple exploit bots cannot print by aggression alone.

## Source Links

- Stargazers: https://github.com/uzlez/fullhouse-engine/stargazers
- Fork network: https://github.com/uzlez/fullhouse-engine/network/members
- Fullhouse site: https://fullhousehackathon.com/
- `rishabhkarwal/fullhouse`: https://github.com/rishabhkarwal/fullhouse
- `andrinjoos/Kuhn_Poker`: https://github.com/andrinjoos/Kuhn_Poker
- `agrawalneel25` compare: https://github.com/uzlez/fullhouse-engine/compare/main...agrawalneel25:fullhouse-engine:neel-work
- `Linglingletsgo` compare: https://github.com/uzlez/fullhouse-engine/compare/main...Linglingletsgo:fullhouse-engine:blueprint-exploit-bot
- `famadeo` compare: https://github.com/uzlez/fullhouse-engine/compare/main...famadeo:fullhouse-engine:main
- `saroopjagdev` compare: https://github.com/uzlez/fullhouse-engine/compare/main...saroopjagdev:fullhouse-engine:stable-stage18
- `vladimirfilip` compare: https://github.com/uzlez/fullhouse-engine/compare/main...vladimirfilip:fullhouse-engine:main
- `Littleguygabe/fullhouse-poker`: https://github.com/Littleguygabe/fullhouse-poker

## Next Actions

1. Add public-style archetype opponents locally for benchmarking.
2. Run paired-seed matches against these archetypes and bundled refs.
3. Add a STATUS entry only after benchmark numbers are produced in our worktree.
4. Treat any bot that only beats bundled references as unproven.
