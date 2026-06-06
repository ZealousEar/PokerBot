# Finals Field Meta + Archetypes (64 finalists)

**Scope:** these are the 64 finalists' play in the **seeding/qualifier tournament** ("Demo Day 1", n_finalists=64); finals are unplayed. Treat as a behavioral proxy vs a mixed field (see `finals_brief.md §0`), not finals-table measurement. Computed from raw replays `raw/hands/*.json`. Table size = **6-max** (98% of real hands; per-hand attribution by seat indices 0-5). Action stats use **clean matches only** (excluded aggregated multi-table records — `seats` array with duplicate seat index — and 0-hand byes). Seats-array stats (delta/bust/error) use all matches. WTSD = revealed_cards keys / saw-flop. Dossier numbers were spot-verified: VPIP/PFR matched; dossier "3bet" was a raw count (replaced with %), dossier WTSD/saw_flop were internally inconsistent (recomputed).

## Field distribution (per-finalist)

| metric | median | p10 | p90 | IQR |
|---|---|---|---|---|
| VPIP % | 31.1 | 23.2 | 37.4 | 7.5 |
| PFR % | 20.5 | 11.6 | 26.8 | 7.6 |
| 3bet % | 6.7 | 4.3 | 9.2 | 2.1 |
| fold-to-3bet % | 74.7 | 53.3 | 85.2 | 16.3 |
| cbet % | 51.2 | 40.6 | 69.3 | 16.6 |
| fold-to-cbet % | 52.8 | 30.4 | 73.4 | 20.8 |
| WTSD % | 40.3 | 23.7 | 78.6 | 24.8 |
| postflop AF | 2.5 | 1.7 | 3.8 | 1.2 |
| all-in /100 | 0.9 | 0.6 | 1.7 | 0.5 |
| bust % | 59.3 | 45.1 | 69.2 | 13.9 |
| avg chip delta | 7236 | 3927 | 13729 | 5457 |
| error/crash matches | 0 | 0 | 3 | 1 |

Field reads slightly LAG vs 6-max norm (VPIP 31 vs 22-28 baseline, PFR 20, 3bet 6.7 in-band). High median fold-to-3bet (75%) = field is exploitable to 3bet pressure. High bust% (59%) reflects stack-off variance in fixed-blind 6-max.

## Archetypes (k-means k=4, standardized, NaN→field-median; k=5 split cluster1 without cleaner separation)

| clust | n | key centroid traits (VPIP/PFR/3bet/f3b/cbet/fcbet/WTSD/AF/bust/delta) | how it plays / how it loses |
|---|---|---|---|
| 0 | 7 | 38/29/11 / 76 / 46/63 / 30 / 2.8 / bust62 / Δ8.3k | **Hyper-LAG maniacs** (jew, GrandSlam, Worm). Widest opens, highest 3bet, low WTSD = bluff-heavy fold-to-aggression. Loses by spewing into calls / variance bust-outs. |
| 1 | 24 | 31/21/6 / 76 / 48/44 / 49 / 2.1 / bust58 / Δ9.2k | **TAG mainstream** (CallMeMaybe, SevenDeuces, APEX). Standard solid lines, low fold-to-cbet (44%) = sticky postflop. Best median rank (31). Loses on thin value / cooler stack-offs. |
| 2 | 21 | 27/16/7 / 60 / 56/51 / 54 / 2.6 / bust63 / Δ6.9k | **Tight-callers / passive-stations** (incl. **Thorp**, TheQuantBot, Freelo). Lowest PFR, lowest fold-to-3bet (60%) = calls down. Loses by passivity: under-3bets, pays off aggressors, lowest median delta. |
| 3 | 12 | 33/21/7 / 80 / 66/71 / 35 / 3.9 / bust47 / Δ13.0k | **Aggro value-bettors** (IveyBot, Hyperion, NecessarySkew). High cbet/fold-to-cbet/AF, lowest bust (47), highest delta, best median rank (19). The strongest cohort — disciplined aggression, folds correctly, prints chips. |
