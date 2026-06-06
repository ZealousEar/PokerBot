# Phase A decision-cluster notes — public drift patch

Top-line: **LOCALIZED, BUT NOT PATCHABLE UNDER THIS TASK'S ALLOWED SCOPE**.

Method: artifact-local driver-side instrumentation around `sandbox.match.BotProcess.act()` in `consult/artifacts/2026-05-29-public-drift-patch/instrumented_h2h.py`. The locked hero remained `submissions/v_final.zip`; the engine and ship bot were not edited. Probe target was TobyCoad `bots/master` because it is the strongest RED signal.

Probe result:

- Scheduled hands: 20,000
- Actual hands: 963
- Hero chip delta: -260,000
- Hero scheduled bb/100: -13.00
- Hero actual bb/100: -269.99
- Hero errors: 0
- Opponent errors: 0
- Hero decision records: 3,481
- Decision log: `logs/toby_master_decisions_s142.jsonl`
- Cluster summary: `logs/toby_master_clusters_s142.json`

## Top losing clusters

Impact is attributed to the **last hero decision in each losing hand**, measured against the 20,000 scheduled-hand denominator.

| rank | street | position_label | true_position_label | action class | board texture | count | chips | bb/100 scheduled | mbb/g scheduled | likely source |
|---:|---|---|---|---|---|---:|---:|---:|---:|---|
| 1 | river | heads_up_button | heads_up_button | `raise` / `raise_le_2/3pot` | `5card_unpaired_two_tone_static` | 22 | -55,792 | -2.790 | -27.90 | `src/postflop.py:38-44` automatic 2/3-pot bet/raise whenever `can_check` and `pot >= 200` |
| 2 | river | big_blind | heads_up_button | `fold` | `5card_paired_two_tone_static` | 21 | -53,256 | -2.663 | -26.63 | `src/postflop.py:46-53` paired-only call heuristic; folds to large river bet after prior investment |
| 3 | river | heads_up_button | heads_up_button | `fold` | `5card_paired_two_tone_static` | 21 | -51,807 | -2.590 | -25.90 | `src/postflop.py:46-53` paired-only call heuristic; folds to large river bet after prior investment |

Secondary observation: if every decision in a losing hand is charged with the final hand delta, the largest antecedent is heads-up button preflop min-raise (`273` decisions, `-403,745` chips, `-20.19 bb/100` scheduled). That implicates `src/preflop_lookup.py:40-42` open-any heads-up/button steal behavior as an enabling line, but it is **not** an allowed seam in this task and is not a last-decision cluster. It is also tightly coupled to the same postflop line that keeps betting/calling into Toby's scripted river traps.

## Allowed seam checks

1. **Preflop pressure overlay** (`src/bot.py:158-180`, `src/opponent_model.py:50-54`): not material in this Toby probe. Preflop all-in as last losing decision occurred once for -10 chips (`-0.001 bb/100` scheduled). Preflop folds after current `raise_count >= 2` totaled about `-1.03 bb/100` scheduled, far smaller than the river clusters.
2. **Six-max position labeling** (`src/bot.py:102-120`): the H2H probe is heads-up, not six-max. Some analysis-time heads-up label mismatches appear (`position_label=big_blind`, `true_position_label=heads_up_button`), but `decide_postflop()` does not consume position, and the preflop facing-aggression branch is effectively position-independent. No material patch seam is localized here.
3. **Limp + iso-raise counting** (`src/preflop_lookup.py:37-53`): not localizable from a heads-up Toby run; no multiway limp+iso sequences exist.
4. **Illegal check facing a bet** (`src/bot.py:60-63`): no evidence that strategy-output `check` was legalized into a costly `call`; top losses are direct postflop `raise`/`fold` decisions.

## Phase A conclusion

Do **not** enter Phase B. The strongest localized leak is the forbidden postflop heuristic surface, and the allowed seams do not explain a material share of the triggering Toby deficit. Per task stance, `NO_PATCH` is the correct outcome.
