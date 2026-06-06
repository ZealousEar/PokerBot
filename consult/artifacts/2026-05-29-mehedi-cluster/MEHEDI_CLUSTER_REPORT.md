DIFFERENT_LEAK — Mehedi’s largest last-decision clusters are preflop facing re-raise fold/all-in, not Toby’s full river unpaired-raise + paired-board-fold trap; a material river paired-fold overlap exists but is secondary.

# Mehedi public-drift decision-cluster analysis — 2026-05-29

## H2H summary

| metric | value |
| --- | --- |
| hero artifact | submissions/v_final.zip |
| canonical hash OK | True |
| opponent zip validator | PASS |
| seed/orientation schedule | base 142, stride 1000, 2 orientations per seed, 500 scheduled hands/orientation |
| scheduled / actual hands | 20,000 / 3,767 |
| actual-to-scheduled ratio | 18.8% |
| hero chip delta | -180,000 |
| hero bb/100 scheduled | -9.00 |
| hero bb/100 actual | -47.78 |
| hero / opp errors | 0 / 0 |
| hero decision records | 4,232 |

Orientation split: o0 `-10.00 bb/100` scheduled over 10,000 scheduled / 1,842 actual; o1 `-8.00 bb/100` over 10,000 scheduled / 1,925 actual.

## A. Last-decision attribution in losing hands

Diagnostic note: losing-hand attribution is not additive to net deficit because winning hands offset these losses.

| rank | street | pos | true_pos | action_class | board_texture | count | chips | bb/100 sched | share vs net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | preflop | big_blind | heads_up_button | fold | preflop | 572 | -114400 | -5.720 | 63.6% |
| 2 | preflop | big_blind | heads_up_button | all_in | preflop | 11 | -74856 | -3.743 | 41.6% |
| 3 | river | big_blind | big_blind | fold | 5card_paired_two_tone_static | 22 | -69806 | -3.490 | 38.8% |
| 4 | preflop | big_blind | big_blind | fold | preflop | 688 | -68800 | -3.440 | 38.2% |
| 5 | preflop | big_blind | big_blind | all_in | preflop | 10 | -65179 | -3.259 | 36.2% |
| 6 | river | heads_up_button | big_blind | fold | 5card_unpaired_two_tone_static | 16 | -50768 | -2.538 | 28.2% |
| 7 | river | big_blind | big_blind | fold | 5card_unpaired_two_tone_static | 16 | -50768 | -2.538 | 28.2% |
| 8 | river | heads_up_button | big_blind | fold | 5card_paired_two_tone_static | 11 | -32313 | -1.616 | 17.9% |
| 9 | river | heads_up_button | big_blind | all_in | 5card_paired_two_tone_static | 4 | -10475 | -0.524 | 5.8% |
| 10 | preflop | heads_up_button | heads_up_button | all_in | preflop | 1 | -9850 | -0.492 | 5.5% |

## B. Every-decision attribution in losing hands

| rank | street | pos | true_pos | action_class | board_texture | count | chips | bb/100 sched | share vs net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | preflop | big_blind | big_blind | call_le_3/4pot | preflop | 105 | -290575 | -14.529 | 161.4% |
| 2 | preflop | heads_up_button | heads_up_button | raise_min | preflop | 670 | -250600 | -12.530 | 139.2% |
| 3 | preflop | big_blind | heads_up_button | fold | preflop | 572 | -114400 | -5.720 | 63.6% |
| 4 | turn | big_blind | big_blind | raise_le_2/3pot | 4card_unpaired_two_tone_static | 30 | -94018 | -4.701 | 52.2% |
| 5 | river | big_blind | big_blind | raise_le_2/3pot | 5card_paired_two_tone_static | 24 | -76152 | -3.808 | 42.3% |
| 6 | preflop | big_blind | heads_up_button | all_in | preflop | 11 | -74856 | -3.743 | 41.6% |
| 7 | turn | heads_up_button | big_blind | raise_le_2/3pot | 4card_unpaired_two_tone_static | 25 | -70852 | -3.543 | 39.4% |
| 8 | river | big_blind | big_blind | fold | 5card_paired_two_tone_static | 22 | -69806 | -3.490 | 38.8% |
| 9 | preflop | big_blind | big_blind | fold | preflop | 688 | -68800 | -3.440 | 38.2% |
| 10 | preflop | big_blind | big_blind | all_in | preflop | 10 | -65179 | -3.259 | 36.2% |

## C. Street-only summary (last-decision losing-hand attribution)

| street | count | chips | bb/100 sched | share vs net |
| --- | --- | --- | --- | --- |
| preflop | 1303 | -334266 | -16.713 | 185.7% |
| river | 103 | -304384 | -15.219 | 169.1% |
| turn | 27 | -27120 | -1.356 | 15.1% |
| flop | 62 | -20415 | -1.021 | 11.3% |

## D. Board-texture summary (last-decision losing-hand attribution)

| board_texture | count | chips | bb/100 sched | share vs net |
| --- | --- | --- | --- | --- |
| preflop | 1303 | -334266 | -16.713 | 185.7% |
| 5card_paired_two_tone_static | 47 | -143564 | -7.178 | 79.8% |
| 5card_unpaired_two_tone_static | 48 | -137879 | -6.894 | 76.6% |
| 5card_paired_two_tone_connected | 7 | -19768 | -0.988 | 11.0% |
| 4card_unpaired_two_tone_static | 15 | -14876 | -0.744 | 8.3% |
| 4card_paired_two_tone_static | 7 | -8158 | -0.408 | 4.5% |
| 3card_unpaired_two_tone_static | 15 | -5183 | -0.259 | 2.9% |
| 3card_unpaired_rainbow_static | 12 | -3883 | -0.194 | 2.2% |
| 5card_unpaired_two_tone_connected | 1 | -3173 | -0.159 | 1.8% |
| 3card_unpaired_two_tone_connected | 10 | -3000 | -0.150 | 1.7% |
| 4card_paired_two_tone_connected | 3 | -2686 | -0.134 | 1.5% |
| 3card_unpaired_rainbow_connected | 6 | -2649 | -0.132 | 1.5% |

## E. Top 10 clusters by scheduled bb/100 impact

| rank | street | pos | true_pos | action_class | board_texture | count | chips | bb/100 sched | share vs net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | preflop | big_blind | heads_up_button | fold | preflop | 572 | -114400 | -5.720 | 63.6% |
| 2 | preflop | big_blind | heads_up_button | all_in | preflop | 11 | -74856 | -3.743 | 41.6% |
| 3 | river | big_blind | big_blind | fold | 5card_paired_two_tone_static | 22 | -69806 | -3.490 | 38.8% |
| 4 | preflop | big_blind | big_blind | fold | preflop | 688 | -68800 | -3.440 | 38.2% |
| 5 | preflop | big_blind | big_blind | all_in | preflop | 10 | -65179 | -3.259 | 36.2% |
| 6 | river | heads_up_button | big_blind | fold | 5card_unpaired_two_tone_static | 16 | -50768 | -2.538 | 28.2% |
| 7 | river | big_blind | big_blind | fold | 5card_unpaired_two_tone_static | 16 | -50768 | -2.538 | 28.2% |
| 8 | river | heads_up_button | big_blind | fold | 5card_paired_two_tone_static | 11 | -32313 | -1.616 | 17.9% |
| 9 | river | heads_up_button | big_blind | all_in | 5card_paired_two_tone_static | 4 | -10475 | -0.524 | 5.8% |
| 10 | preflop | heads_up_button | heads_up_button | all_in | preflop | 1 | -9850 | -0.492 | 5.5% |

## Direct comparison to Toby top-3 clusters

| Toby rank | Toby row | Mehedi exact row | Mehedi broad equivalent | tag | note |
| --- | --- | --- | --- | --- | --- |
| 1 | river / heads_up_button / heads_up_button / raise_le_2/3pot / 5card_unpaired_two_tone_static | none | ranks [11, 12]; 6 decisions; -19038 chips; -0.952 bb/100 | different | The unpaired river 2/3-pot raise shape exists only as ranks 11/12 combined; it is not a top-three Mehedi driver. |
| 2 | river / big_blind / heads_up_button / fold / 5card_paired_two_tone_static | ranks [14]; -7620 chips; -0.381 bb/100 | ranks [3, 8, 14, 35]; 36 decisions; -111372 chips; -5.569 bb/100 | same_partial | The paired-board river fold shape is material in Mehedi, but the exact Toby HU labels are diluted/shifted and Mehedi’s two largest clusters are preflop. |
| 3 | river / heads_up_button / heads_up_button / fold / 5card_paired_two_tone_static | ranks [35]; -1633 chips; -0.082 bb/100 | ranks [3, 8, 14, 35]; 36 decisions; -111372 chips; -5.569 bb/100 | same_partial | The paired-board river fold shape is material in Mehedi, but the exact Toby HU labels are diluted/shifted and Mehedi’s two largest clusters are preflop. |

Top-3 Toby-specific tags: `rank_1=different`, `rank_2=same_partial`, `rank_3=same_partial`.

Broad-shape totals: paired river fold `-5.569 bb/100` scheduled; unpaired river 2/3-pot raise `-0.952 bb/100`; combined Toby river shapes `-6.521 bb/100`. The combined number is material, but it is not the top-three Mehedi signature because the two largest Mehedi last-decision clusters are preflop pressure decisions (`-5.720` and `-3.743 bb/100`).

## Verdict rationale

- Toby’s full trap was all-river in the top three, led by river 2/3-pot raising on unpaired two-tone static boards.

- Mehedi’s top two last-decision clusters are preflop `big_blind / true heads_up_button` facing a second preflop raise: fold (`-5.720 bb/100`) and all-in (`-3.743 bb/100`).

- The paired-board river-fold component is real and material (`-5.569 bb/100` pooled across labels), but Toby’s rank-1 unpaired river raise component is only `-0.952 bb/100` and starts at ranks 11/12.

- Therefore classify Mehedi as `DIFFERENT_LEAK` with a secondary shared paired-river-fold symptom, not `SAME_TRAP`.

## Upload recommendation

`SHIP_LOCKED_ARTIFACT`. No allowed seam is identified for a pre-qualifier patch. A postflop heuristic rewrite remains forbidden, and the preflop pressure signature would still require a separate full-gauntlet candidate before promotion. `submissions/v_final.zip` and `submissions/best_green.zip` remained at the canonical hash during this analysis.

## Files written

- `consult/artifacts/2026-05-29-mehedi-cluster/instrumented_h2h.py`

- `consult/artifacts/2026-05-29-mehedi-cluster/decision_log.jsonl`

- `consult/artifacts/2026-05-29-mehedi-cluster/logs/mehedi_mybot_instrumented_s142.json`

- `consult/artifacts/2026-05-29-mehedi-cluster/logs/mehedi_mybot_clusters_s142.json`

- `consult/artifacts/2026-05-29-mehedi-cluster/RESULTS.json`

- `consult/artifacts/2026-05-29-mehedi-cluster/MEHEDI_CLUSTER_REPORT.md`

- `consult/artifacts/2026-05-29-mehedi-cluster/STATUS_BLOCK.md`
