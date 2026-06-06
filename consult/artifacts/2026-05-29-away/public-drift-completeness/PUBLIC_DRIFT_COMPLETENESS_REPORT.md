# P4 Public Drift Completeness Sweep

Created: 2026-05-29T16:30:16Z

## Hard-invariant check

- `submissions/v_final.zip`: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- `submissions/best_green.zip`: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- Locked SHA expected: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- Strategy edits: none by this lane.
- Candidate artifacts: temporary opponent zips only, under `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/public-drift-completeness/opponent_zips`.

## Direct answers

1. Are Pav intermediate versions hiding a RED cell? **YES**. Tested Pav skantbot7 variants: skantbot7, skantbot7.1, skantbot7.10, skantbot7.11, skantbot7.12, skantbot7.13, skantbot7.3, skantbot7.4, skantbot7.5, skantbot7.6, skantbot7.7, skantbot7.8, skantbot7.9. Missing/absent in live repo: skantbot7.2.
2. Are Toby and Mehedi still the only RED public cells? **NO**. RED cells: Mehedi-dev-2404/fullhouse-engine bots/mybot/bot.py, Pav1602/fullhouse-engine bots/skantbot7.9/bot.py, TobyCoad/fullhouse-engine bots/loose_aggressive/bot.py, TobyCoad/fullhouse-engine bots/loose_passive/bot.py, TobyCoad/fullhouse-engine bots/master/bot.py, TobyCoad/fullhouse-engine bots/stack_pressure/bot.py.
3. Did any recently pushed fork add a new custom bot? **YES**. Recent custom rows in this matrix: 3.
4. Does live vladimir invalidate the prior local positive audit? **NO STABLE LIVE INVALIDATION**. Live public `bots/vlad` is marked `TIMEBOXED_UNUSABLE` because required `data/gto_strategy.npz` is absent from the live public clone; prior local audit remains background only.
5. Does anything justify opening a pre-qualifier MODIFY gate? **YES, review gate only**. RED evidence justifies orchestrator review, but not modifying `v_final.zip` without a fully gated candidate.

Default recommendation: do not modify `v_final.zip` without a fully gated candidate.

## Inventory and results

| repo | branch | commit | date | bot path | LOC | data files | validator | scheduled | actual | bb/100 scheduled | bb/100 actual | CI | hero errors | opp errors | p99 latency | verdict |
|---|---|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Mehedi-dev-2404/fullhouse-engine | main | `c2a1ea854acd` | 2026-05-29T15:46:55+01:00 | `bots/mybot/bot.py` | 992 | 0 | PASS | 89000 | 17971 | -3.73 | -18.46 | [-6.52, -0.90] | 0 | 0 | 0.0099 | RED |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.1/bot.py` | 1621 | 0 | PASS | 100000 | 38867 | 0.33 | 0.86 | [-2.01, 2.59] | 0 | 0 | 0.0069 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.10/bot.py` | 1857 | 0 | PASS | 20000 | 16903 | 2.40 | 2.83 | [-0.62, 5.53] | 0 | 0 | 0.0014 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.11/bot.py` | 1916 | 0 | PASS | 20000 | 17384 | 1.46 | 1.68 | [-0.32, 3.17] | 0 | 0 | 0.0010 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.12/bot.py` | 2180 | 0 | PASS | 20000 | 16846 | 1.43 | 1.69 | [-1.81, 4.61] | 0 | 0 | 0.0010 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.13/bot.py` | 2246 | 0 | PASS | 20000 | 17741 | 1.55 | 1.75 | [-1.05, 3.91] | 0 | 0 | 0.0008 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.3/bot.py` | 1653 | 0 | PASS | 100000 | 59513 | 11.04 | 18.55 | [8.96, 12.94] | 0 | 0 | 0.0008 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.4/bot.py` | 1685 | 0 | PASS | 20000 | 12553 | 12.79 | 20.38 | [10.01, 15.45] | 0 | 0 | 0.0008 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.5/bot.py` | 1688 | 0 | PASS | 100000 | 64129 | 12.80 | 19.96 | [11.14, 14.37] | 0 | 0 | 0.0009 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.6/bot.py` | 1723 | 0 | PASS | 20000 | 13946 | 10.34 | 14.83 | [7.07, 13.53] | 0 | 0 | 0.0015 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.7/bot.py` | 1753 | 0 | PASS | 20000 | 14166 | 11.61 | 16.40 | [8.42, 14.67] | 0 | 0 | 0.0015 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.8/bot.py` | 1765 | 0 | PASS | 20000 | 14828 | 10.03 | 13.53 | [7.10, 13.01] | 0 | 0 | 0.0011 | GREEN; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7.9/bot.py` | 1765 | 0 | PASS | 100000 | 84570 | -0.14 | -0.16 | [-1.88, 1.63] | 0 | 0 | 0.0011 | RED; NEW_THREAT |
| Pav1602/fullhouse-engine | main | `1ca89cf6d716` | 2026-05-29T16:00:38+01:00 | `bots/skantbot7/bot.py` | 1590 | 0 | PASS | 20000 | 12835 | 4.38 | 6.82 | [-1.71, 10.13] | 0 | 0 | 0.0057 | GREEN; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/bluff_heavy/bot.py` | 47 | 0 | PASS | 100000 | 6042 | 2.00 | 33.10 | [-0.60, 4.60] | 0 | 0 | 0.0059 | GREEN; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/loose_aggressive/bot.py` | 127 | 0 | PASS | 100000 | 18881 | -16.40 | -86.86 | [-17.80, -15.00] | 0 | 0 | 0.0034 | RED; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/loose_passive/bot.py` | 129 | 0 | PASS | 100000 | 22262 | -11.80 | -53.01 | [-14.00, -9.60] | 0 | 0 | 0.0040 | RED; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/master/bot.py` | 421 | 0 | PASS | 100000 | 5535 | -17.00 | -307.14 | [-18.40, -15.60] | 0 | 0 | 0.0047 | RED |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/position_exploiter/bot.py` | 147 | 0 | PASS | 100000 | 41718 | 16.87 | 40.45 | [15.40, 18.22] | 0 | 0 | 0.0052 | GREEN; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/pure_pot_odds/bot.py` | 96 | 0 | PASS | 100000 | 18252 | 5.00 | 27.39 | [2.60, 7.40] | 0 | 0 | 0.0020 | GREEN; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/random_bot/bot.py` | 32 | 0 | PASS | 100000 | 7166 | 3.60 | 50.24 | [0.80, 6.40] | 0 | 0 | 0.0077 | GREEN; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/stack_pressure/bot.py` | 138 | 0 | PASS | 100000 | 9009 | -20.00 | -222.00 | [-20.00, -20.00] | 0 | 0 | 0.0055 | RED; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/tight_aggressive/bot.py` | 147 | 0 | PASS | 100000 | 38145 | 17.27 | 45.28 | [15.89, 18.49] | 0 | 0 | 0.0056 | GREEN; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/tight_passive/bot.py` | 113 | 0 | PASS | 100000 | 32127 | 19.97 | 62.16 | [19.91, 20.00] | 0 | 0 | 0.0075 | GREEN; NEW_THREAT |
| TobyCoad/fullhouse-engine | main | `93516f33675d` | 2026-05-13T22:19:58+01:00 | `bots/trap_slow_player/bot.py` | 136 | 0 | PASS | 100000 | 49643 | 13.31 | 26.81 | [11.37, 15.18] | 0 | 0 | 0.0025 | GREEN; NEW_THREAT |
| agrawalneel25/fullhouse-engine | neel-work | `071d54c302cb` | 2026-05-12T17:52:21+01:00 | `bots/neel/bot.py` | 257 | 0 | PASS | 200000 | 102276 | 14.69 | 28.73 | [13.50, 15.81] | 0 | 0 | 0.0633 | GREEN |
| famadeo/fullhouse-engine | main | `c94dace1c6bf` | 2026-05-22T14:59:01-03:00 | `bots/codex_holdem/bot.py` | 2359 | 1 | PASS | 200000 | 43914 | 0.65 | 2.96 | [-1.30, 2.60] | 0 | 0 | 0.0643 | GREEN |
| stoppedtime24/fullhouse-engine | main | `52951cb7242e` | 2026-05-28T22:56:46+01:00 | `bots/mybot/bot.py` | 333 | 0 | PASS | 100000 | 38334 | 12.34 | 32.20 | [10.00, 14.57] | 0 | 0 | 0.0026 | GREEN; NEW_THREAT |
| vladimirfilip/fullhouse-engine | main | `d3e48d5ed86e` | 2026-05-29T10:13:56+01:00 | `bots/vlad/bot.py` | 696 | 0 | TIMEBOXED_UNUSABLE | n/a | n/a | n/a | n/a | [n/a, n/a] | n/a | n/a | n/a | TIMEBOXED_UNUSABLE |

## Recent fork enumeration

- Forks returned by `gh api repos/uzlez/fullhouse-engine/forks?per_page=100`: 30
- Recent cutoff: 2026-05-26T15:14:37Z
- Recent forks inspected: 6

Recent forks:
- `gonfdcg/fullhouse-engine` pushed `2026-05-29T14:18:32Z`
- `Benjamin-Yu-Sheng-Chang/fullhouse-hackathon` pushed `2026-05-29T14:27:35Z`
- `Mehedi-dev-2404/fullhouse-engine` pushed `2026-05-29T14:58:13Z`
- `lucashsu007-create/fullhouse-engine` pushed `2026-05-26T16:15:41Z`
- `stoppedtime24/fullhouse-engine` pushed `2026-05-28T21:58:10Z`
- `vladimirfilip/fullhouse-engine` pushed `2026-05-29T09:14:00Z`

## Specific confirmations

- famadeo `bots/codex_holdem`: live head remained `c94dace1c6bf523aa49e9c149d897c6b71a19c5e`; H2H was not rerun and prior GREEN metrics were reused.
- agrawalneel25 `neel-work/bots/neel`: live head remained `071d54c302cbd2d9d5fcc773260e7f5f894c642f`; H2H was not rerun and prior GREEN metrics were reused.
- Recent forks with custom non-template bot rows: Mehedi `bots/mybot`, stoppedtime24 `bots/mybot`, and vladimir `bots/vlad` (unusable because live public data is missing). The other recent forks inspected were template/reference only.
- Mehedi escalation collected 89,000 scheduled hands before the phase timebox; the verdict is still RED because the combined CI high is below zero.

## Notes

- Scheduled bb/100 is the primary matrix metric; actual bb/100 is reported separately because early busts reduce played hands.
- `NEW_THREAT` is attached to valid bots not present in the prior matrix.
- `TIMEBOXED_UNUSABLE` means a requested live bot could not be used as a complete public package due missing required data.
- Validator logs, clone/API logs, and H2H logs are under `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/public-drift-completeness/command_logs`.
