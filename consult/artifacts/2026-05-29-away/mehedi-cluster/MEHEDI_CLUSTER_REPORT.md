DIFFERENT_LEAK

# Mehedi decision-cluster report

Verdict reason: dominant top-2 last-decision clusters are preflop (-15.87 scheduled bb/100); Toby-style river clusters are present but secondary (-6.20 scheduled bb/100 in top-10 last clusters).

## H2H summary

| scheduled hands | actual hands | scheduled bb/100 | actual bb/100 | 95% CI | hero errors | opponent errors | p99 latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20000 | 3764 | -9.00 | -47.82 | [-14.00, -4.00] | 0 | 0 | 0.0064s |

## Top cluster table

| rank | attribution mode | street | position | action | board texture | chips | scheduled bb/100 | n hands | n decisions | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | last_decision_losing_hands | preflop | big_blind | fold | preflop | -182600 | -9.13 | 1257 | 1257 | different: no Toby top-cluster match |
| 2 | last_decision_losing_hands | preflop | big_blind | all_in | preflop | -134875 | -6.74 | 20 | 20 | different: no Toby top-cluster match |
| 3 | last_decision_losing_hands | river | big_blind | fold | 5card_paired_two_tone_static | -80599 | -4.03 | 25 | 25 | same: river fold / paired two-tone static |
| 4 | last_decision_losing_hands | river | heads_up_button | fold | 5card_unpaired_two_tone_static | -57300 | -2.87 | 20 | 20 | different: no Toby top-cluster match |
| 5 | last_decision_losing_hands | river | big_blind | fold | 5card_unpaired_two_tone_static | -55667 | -2.78 | 19 | 19 | different: no Toby top-cluster match |
| 6 | last_decision_losing_hands | river | heads_up_button | fold | 5card_paired_two_tone_static | -33946 | -1.70 | 12 | 12 | same: river fold / paired two-tone static |
| 7 | last_decision_losing_hands | river | heads_up_button | all_in | 5card_paired_two_tone_static | -11330 | -0.57 | 4 | 4 | different: no Toby top-cluster match |
| 8 | last_decision_losing_hands | river | big_blind | raise / raise_le_2/3pot | 5card_paired_two_tone_static | -10156 | -0.51 | 3 | 3 | different: no Toby top-cluster match |
| 9 | last_decision_losing_hands | preflop | heads_up_button | all_in | preflop | -9850 | -0.49 | 1 | 1 | different: no Toby top-cluster match |
| 10 | last_decision_losing_hands | river | heads_up_button | raise / raise_le_2/3pot | 5card_unpaired_two_tone_static | -9519 | -0.48 | 3 | 3 | same: river raise / unpaired two-tone static |

## Toby comparison

| Toby cluster | Mehedi matching cluster | same/different | evidence |
| --- | --- | --- | --- |
| river heads_up_button raise / raise_le_2/3pot on unpaired two-tone static wet-flush-draw boards | river heads_up_button raise / raise_le_2/3pot 5card_unpaired_two_tone_static -0.48 bb/100 | same | dominant top-2 last-decision clusters are preflop (-15.87 scheduled bb/100); Toby-style river clusters are present but secondary (-6.20 scheduled bb/100 in top-10 last clusters) |
| river fold on paired two-tone static boards | river big_blind fold 5card_paired_two_tone_static -4.03 bb/100<br>river heads_up_button fold 5card_paired_two_tone_static -1.70 bb/100 | same | dominant top-2 last-decision clusters are preflop (-15.87 scheduled bb/100); Toby-style river clusters are present but secondary (-6.20 scheduled bb/100 in top-10 last clusters) |
| same paired-board fold cluster with label drift | river big_blind fold 5card_paired_two_tone_static -4.03 bb/100<br>river heads_up_button fold 5card_paired_two_tone_static -1.70 bb/100 | same | dominant top-2 last-decision clusters are preflop (-15.87 scheduled bb/100); Toby-style river clusters are present but secondary (-6.20 scheduled bb/100 in top-10 last clusters) |
| preflop HU button open-any antecedent, not primary kill | heads_up_button raise / raise_min -1.61 bb/100 | antecedent only | dominant top-2 last-decision clusters are preflop (-15.87 scheduled bb/100); Toby-style river clusters are present but secondary (-6.20 scheduled bb/100 in top-10 last clusters) |

## Ship recommendation

SHIP_LOCKED_ARTIFACT

Do not replace `submissions/v_final.zip` or `submissions/best_green.zip`; no candidate artifact was built.
