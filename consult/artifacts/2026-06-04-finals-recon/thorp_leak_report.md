# Thorp Leak Report (finals recon, 2026-06-04)

Thorp bot_id `7a7ad230-2b19-46ff-af11-5df254b6f078`. Evidence from raw replays `raw/hands/*.json`.

## Method / data hygiene
- Thorp appears in 40 match files; **36 are clean 6-max** (len(seats)==6, Thorp seat index not shared with another bot). 4 are aggregated multi-table records (seat-index collisions) -> fold-stats computed on the 36 clean matches only.
- Hands attributed to Thorp by his unique seat index within each clean match.
- `amount` convention (verified by pot reconciliation, **15343/15626 hands = 98.2%** reconcile within +/-2): blinds=posted; `raise` amount = total-to **for that street** (resets each street); `call`/`all_in` = increment added this street. Streets segmented by betting-round close (all live players matched + acted). The 1.8% misreconciling are all-in side-pot caps -- irrelevant to fold rates; for chip-loss ranking I use Thorp's summed contribution (lost-pot magnitude).
- Bust = a Thorp seat entry with `final_stack==0`. **Bust split classified by the street Thorp put his LAST chips in** (committing street), NOT the terminal board -- preflop all-ins that run out to the river are counted preflop.
- Flop texture taxonomy (first 3 board cards): `paired` (any pair), `wet` (2-tone or mono / flush-draw heavy), `dry` (rainbow unpaired).
- Hole cards only known when in `revealed_cards` (keyed by bot_id) at showdown; unknown marked `??`.

## Fold-stat table (36 clean matches)
| Stat | Value |
|---|---|
| Fold-to-3bet (Thorp opened PF, faced reraise) | **62.1%** (157/253) |
| Fold-to-cbet -- dry (rainbow) | 52.2% (72/138) |
| Fold-to-cbet -- wet (2-tone/mono) | 58.8% (127/216) |
| Fold-to-cbet -- paired | 51.6% (33/64) |
| River-fold (faced river bet) | 33.3% (53/159) |

Fold-to-cbet aggregate ~= 55.0% (232/418). Fold-to-3bet 62% is on the high/exploitable side for 6-max.

## DECISIVE bust split (preflop vs postflop)
22 total bust seat-entries; 2 in aggregated records (excluded). **20 clean busts:**

| Committing street | Count | % of clean busts |
|---|---|---|
| **Preflop** | **5** | **25%** |
| **Postflop** | **15** | **75%** |
| -- flop | 5 | |
| -- turn | 5 | |
| -- river | 5 | |

**HEADLINE: 5 preflop / 15 postflop (25% / 75%). 3-of-4 Thorp busts are decided postflop.** (2 further busts in multi-table aggregate records not attributable.)

## Top-20 biggest chip-loss hands
loss = Thorp's chips committed to the lost pot. "cmt" = committing street. allin = Thorp shoved.

| # | loss | holes | board | cmt | allin | category |
|---|---|---|---|---|---|---|
| 1 | 46418 | ?? | Qs 7h 7c Ah 6c | pf | Y | preflop spew (4bet-pot shove) |
| 2 | 46303 | KhAd | 4c Jh Kd 6c Qs | pf | Y | preflop stack-off (AK) |
| 3 | 41154 | ?? | Qs Ac Qc Kh 3c | river | Y | postflop stack-off |
| 4 | 37639 | ?? | 2d 8d Ah 3h Jh | flop | Y | postflop stack-off |
| 5 | 34773 | 5sAs | 2c 3c Tc 6h Ad | pf | Y | preflop stack-off (A5s) |
| 6 | 34212 | 9hQh | Qs Kd 6s 9c 5d | river | N | postflop stack-off / cooler |
| 7 | 33427 | QsJc | Jd 8d 2h Jh Qd | turn | Y | postflop stack-off / cooler (2pr vs trips) |
| 8 | 32871 | ?? | Ts Tc Td 5c 8h | flop | Y | postflop stack-off (board trips) |
| 9 | 32023 | ?? | 2s 7h Ac 4h 6s | turn | Y | postflop stack-off |
| 10 | 31189 | ?? | 2d 8s 6s Qd Tc | turn | N | postflop stack-off |
| 11 | 28921 | QdQh | 7c 9d 7d 8c 3c | river | Y | postflop stack-off / cooler (QQ) |
| 12 | 26633 | QcAc | 9c Ts Kc Qh 6d | flop | N | postflop stack-off / cooler |
| 13 | 25638 | Jd9h | 3s 9c 2h 8c Js | river | Y | postflop stack-off / cooler (2pr) |
| 14 | 25094 | ?? | Jc 5d Qs Ks Ah | flop | Y | postflop stack-off |
| 15 | 24395 | ?? | 9s Js 8c 5h Jh | pf | Y | preflop spew |
| 16 | 24038 | ?? | 7h 3c 6c 8s Kc | turn | N | postflop stack-off |
| 17 | 23738 | ?? | 4h Tc Jh 9d 6s | river | N | postflop stack-off |
| 18 | 23385 | KdAd | Td Qh 3d 6s Kh | river | N | postflop stack-off / cooler (AK top pair) |
| 19 | 23084 | KsAc | 2h Kh Jc 3s 5d | river | N | postflop stack-off / cooler (AK top pair) |
| 20 | 22637 | JcJh | 2d Qs 7s 9s 2s | pf | Y | preflop stack-off (JJ) |

Top-20 split: 5 preflop (all all-in: spews + AK/A5s/JJ stack-offs), 15 postflop (mostly stack-offs / coolers; big-pot top-pair & two-pair pay-offs on turn/river dominate). Pattern: large losses cluster in postflop stack-offs with top-pair/two-pair holdings paying off on turn/river.
