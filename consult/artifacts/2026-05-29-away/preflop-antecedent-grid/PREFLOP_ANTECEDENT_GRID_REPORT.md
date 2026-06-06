# P3 Preflop Antecedent Grid Report

Verdict: NOT_PROMOTABLE
Selected candidate: A4

Protected artifacts:
- v_final.zip before/after: e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598 / e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
- best_green.zip before/after: e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598 / e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598

Decision rule:
- Material Toby/Mehedi improvement: actual bb/100 delta >= 5.0 on both targets vs A0.
- GREEN regression: non-target actual bb/100 delta <= -5.0 vs A0.
- Per-decision p99 latency is unavailable from the engine API; proxy seconds/hand is recorded in RESULTS.json.
- River trap entries are not labelled in decision logs; river losing commit frequency is recorded as a proxy.

Candidate zips:
- A0: /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/preflop-antecedent-grid/zips/preflop_antecedent_A0.zip sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
- A1: /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/preflop-antecedent-grid/zips/preflop_antecedent_A1.zip sha256=a544cc04457973ce254952cf78ece18ab40f8c86ce50b2933e99141c98b63bb2
- A2: /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/preflop-antecedent-grid/zips/preflop_antecedent_A2.zip sha256=d7b635af58b75dac722c11c650a50a54ac6cf9f6a131d971120f21ea7dd7cb85
- A3: /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/preflop-antecedent-grid/zips/preflop_antecedent_A3.zip sha256=c66ee19e0f2fb16756df3111c721cdf7306fc8f15211492e96b91aed4dcf9901
- A4: /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/preflop-antecedent-grid/zips/preflop_antecedent_A4.zip sha256=957cf22a655adc57b2df67854e6f6a917f58dd53e273d8bfd312fd641d2dfcc8
- A5: /Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/preflop-antecedent-grid/zips/preflop_antecedent_A5.zip sha256=cb100759cb9cd7a8ae5ba88f7b92df0d8f4fe472f888c4aa20b49066fe35b721

Verification:

| candidate | leakage | import | edge | validator | smoke |
|---|---:|---:|---:|---:|---:|
| A0 | True | True | True | True | False |
| A1 | True | True | True | True | False |
| A2 | True | True | True | True | False |
| A3 | True | True | True | True | True |
| A4 | True | True | True | True | True |
| A5 | True | True | True | True | False |

H2H actual bb/100 (95% bootstrap CI):

## toby_master

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | -198.02 [-362.84, +0.42] hands=202/1200 err=0 | 1.000 | 1.000 | 0.489 |
| A1 | -189.57 [-383.51, -6.33] hands=211/1200 err=0 | 0.972 | 1.000 | 0.504 |
| A2 | -220.59 [-387.58, -55.75] hands=272/1200 err=0 | 0.701 | 1.000 | 0.541 |
| A3 | -163.93 [-307.29, -24.92] hands=366/1200 err=0 | 0.571 | 1.000 | 0.518 |
| A4 | -159.15 [-267.63, -41.51] hands=377/1200 err=0 | 0.378 | 1.000 | 0.536 |
| A5 | -198.02 [-399.87, -17.09] hands=202/1200 err=0 | 0.713 | 1.000 | 0.536 |

## mehedi_mybot

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | -62.89 [-165.78, +42.17] hands=394/1200 err=0 | 0.995 | 0.833 | 0.545 |
| A1 | -65.94 [-175.45, +42.22] hands=394/1200 err=0 | 0.964 | 0.833 | 0.500 |
| A2 | -35.65 [-91.53, +17.40] hands=737/1200 err=0 | 0.715 | 0.667 | 0.455 |
| A3 | -50.74 [-96.90, -4.83] hands=815/1200 err=0 | 0.536 | 0.500 | 0.538 |
| A4 | -51.84 [-99.15, -4.00] hands=815/1200 err=0 | 0.349 | 0.500 | 0.458 |
| A5 | -35.65 [-91.53, +17.40] hands=737/1200 err=0 | 0.715 | 0.667 | 0.455 |

## pav_skantbot7_9

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | -7.31 [-43.40, +20.92] hands=900/1200 err=0 | 0.976 | 0.333 | 0.357 |
| A1 | +0.94 [-21.62, +21.89] hands=1073/1200 err=0 | 0.944 | 0.167 | 0.250 |
| A2 | -8.79 [-36.66, +15.17] hands=1027/1200 err=0 | 0.698 | 0.167 | 0.231 |
| A3 | -37.37 [-98.05, +23.78] hands=681/1200 err=0 | 0.422 | 0.667 | 0.222 |
| A4 | -31.93 [-74.24, +4.20] hands=900/1200 err=0 | 0.290 | 0.333 | 0.333 |
| A5 | -12.14 [-37.89, +13.02] hands=995/1200 err=0 | 0.701 | 0.333 | 0.214 |

## pav_skantbot7_6

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | +9.44 [-25.97, +41.66] hands=1027/1200 err=0 | 0.813 | 0.167 | 0.238 |
| A1 | +20.00 [-7.17, +51.79] hands=1017/1200 err=0 | 0.855 | 0.333 | 0.095 |
| A2 | +6.94 [-21.30, +33.73] hands=1073/1200 err=0 | 0.626 | 0.167 | 0.185 |
| A3 | -25.71 [-63.96, +7.54] hands=900/1200 err=0 | 0.492 | 0.333 | 0.190 |
| A4 | -47.91 [-93.18, -2.19] hands=844/1200 err=0 | 0.293 | 0.500 | 0.308 |
| A5 | +3.47 [-26.07, +33.93] hands=1046/1200 err=0 | 0.605 | 0.333 | 0.125 |

## famadeo

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | -5.67 [-77.76, +66.48] hands=791/1200 err=0 | 1.000 | 0.667 | 0.340 |
| A1 | +0.00 [-92.31, +92.23] hands=410/1200 err=0 | 0.980 | 1.000 | 0.301 |
| A2 | -35.21 [-102.47, +30.03] hands=568/1200 err=0 | 0.697 | 1.000 | 0.322 |
| A3 | -10.89 [-73.99, +50.67] hands=608/1200 err=0 | 0.528 | 0.833 | 0.319 |
| A4 | -19.45 [-66.50, +29.99] hands=721/1200 err=0 | 0.359 | 0.833 | 0.346 |
| A5 | -7.59 [-76.20, +59.61] hands=669/1200 err=0 | 0.707 | 0.667 | 0.349 |

## neel

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | +19.86 [-7.17, +46.47] hands=973/1200 err=0 | 0.996 | 0.333 | 0.438 |
| A1 | +21.82 [-3.66, +50.86] hands=1036/1200 err=0 | 0.971 | 0.333 | 0.411 |
| A2 | +6.65 [-21.56, +36.19] hands=1084/1200 err=0 | 0.727 | 0.333 | 0.400 |
| A3 | -9.82 [-39.93, +18.97] hands=1070/1200 err=0 | 0.536 | 0.333 | 0.419 |
| A4 | -22.96 [-53.63, +5.81] hands=1055/1200 err=0 | 0.372 | 0.500 | 0.412 |
| A5 | +6.90 [-23.20, +35.71] hands=1117/1200 err=0 | 0.730 | 0.167 | 0.417 |

## stoppedtime24_mybot

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | +22.90 [-20.71, +61.06] hands=911/1200 err=0 | 1.000 | 0.667 | 0.571 |
| A1 | +73.91 [+22.22, +135.39] hands=709/1200 err=0 | 0.960 | 0.833 | 0.417 |
| A2 | +40.26 [-0.80, +85.11] hands=862/1200 err=0 | 0.715 | 0.500 | 0.414 |
| A3 | +29.03 [-12.50, +66.93] hands=872/1200 err=0 | 0.544 | 0.667 | 0.517 |
| A4 | +18.58 [-19.85, +58.69] hands=956/1200 err=0 | 0.377 | 0.500 | 0.379 |
| A5 | +36.06 [-4.40, +77.68] hands=856/1200 err=0 | 0.715 | 0.500 | 0.444 |

## ref_template

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | +72.46 [+69.75, +75.27] hands=552/800 err=0 | 0.993 | 1.000 | 1.000 |
| A1 | +67.80 [+64.58, +71.19] hands=590/800 err=0 | 0.929 | 1.000 | 1.000 |
| A2 | +51.89 [+48.50, +55.81] hands=766/800 err=0 | 0.715 | 0.750 | 1.000 |
| A3 | +39.19 [+35.69, +43.12] hands=800/800 err=0 | 0.545 | 0.000 | 0.000 |
| A4 | +24.94 [+21.19, +29.06] hands=800/800 err=0 | 0.350 | 0.000 | 0.000 |
| A5 | +51.89 [+48.50, +55.81] hands=766/800 err=0 | 0.715 | 0.750 | 1.000 |

## ref_aggressor

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | -277.78 [-777.67, +246.75] hands=72/800 err=0 | 0.306 | 1.000 | 0.000 |
| A1 | +0.00 [-368.92, +437.44] hands=111/800 err=0 | 0.255 | 1.000 | 0.000 |
| A2 | +0.00 [-391.30, +430.71] hands=100/800 err=0 | 0.220 | 1.000 | 1.000 |
| A3 | -256.41 [-695.28, +238.47] hands=78/800 err=0 | 0.205 | 1.000 | 1.000 |
| A4 | -256.41 [-721.22, +238.71] hands=78/800 err=0 | 0.179 | 1.000 | 0.000 |
| A5 | -256.41 [-736.68, +231.82] hands=78/800 err=0 | 0.231 | 1.000 | 0.000 |

## ref_mathematician

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | +145.45 [+138.91, +152.36] hands=275/800 err=0 | 1.000 | 1.000 | 0.500 |
| A1 | +136.52 [+128.16, +144.88] hands=293/800 err=0 | 0.959 | 1.000 | 0.667 |
| A2 | +112.04 [+103.36, +120.59] hands=357/800 err=0 | 0.719 | 1.000 | 0.286 |
| A3 | +94.34 [+85.50, +102.59] hands=424/800 err=0 | 0.557 | 1.000 | 0.000 |
| A4 | +67.34 [+59.68, +74.24] hands=594/800 err=0 | 0.349 | 1.000 | 0.333 |
| A5 | +112.04 [+103.36, +120.59] hands=357/800 err=0 | 0.719 | 1.000 | 0.286 |

## ref_shark

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | +72.20 [+68.68, +76.17] hands=554/800 err=0 | 0.993 | 1.000 | 0.667 |
| A1 | +69.32 [+65.25, +73.14] hands=577/800 err=0 | 0.962 | 1.000 | 1.000 |
| A2 | +51.63 [+47.33, +55.47] hands=768/800 err=0 | 0.719 | 0.500 | 0.000 |
| A3 | +38.38 [+34.25, +42.56] hands=800/800 err=0 | 0.545 | 0.000 | 0.000 |
| A4 | +24.50 [+20.44, +28.75] hands=800/800 err=0 | 0.350 | 0.000 | 0.000 |
| A5 | +51.63 [+47.33, +55.47] hands=768/800 err=0 | 0.719 | 0.500 | 0.000 |

## ref_ref_bot_2

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | +145.45 [+138.91, +152.36] hands=275/800 err=0 | 1.000 | 1.000 | 0.500 |
| A1 | +136.52 [+128.16, +144.88] hands=293/800 err=0 | 0.959 | 1.000 | 0.667 |
| A2 | +112.04 [+103.36, +120.59] hands=357/800 err=0 | 0.719 | 1.000 | 0.286 |
| A3 | +94.34 [+85.50, +102.59] hands=424/800 err=0 | 0.557 | 1.000 | 0.000 |
| A4 | +67.34 [+59.68, +74.24] hands=594/800 err=0 | 0.349 | 1.000 | 0.333 |
| A5 | +112.04 [+103.36, +120.59] hands=357/800 err=0 | 0.719 | 1.000 | 0.286 |

## ref_sixmax_mix

| candidate | actual bb/100 [CI] | HU open freq | early bust | river losing commit freq |
|---|---:|---:|---:|---:|
| A0 | -50.00 [-75.22, -27.13] hands=600/600 err=0 |  | 0.000 | 0.500 |
| A1 | -53.38 [-100.52, -3.36] hands=562/600 err=0 |  | 0.667 | 0.800 |
| A2 | -50.00 [-86.68, -10.60] hands=600/600 err=0 |  | 0.000 | 0.429 |
| A3 | -45.19 [-86.44, +3.11] hands=592/600 err=0 |  | 0.333 | 0.444 |
| A4 | -50.00 [-75.51, -29.51] hands=600/600 err=0 |  | 0.000 | 0.500 |
| A5 | -50.00 [-82.13, -24.85] hands=600/600 err=0 |  | 0.000 | 1.000 |

Decision details:

- A1: Toby delta=8.446342264558211, Mehedi delta=-3.045685279187822, improves=False, regressions=[{'target': 'ref_mathematician', 'delta_bb_per_100': -8.935774123487448}, {'target': 'ref_ref_bot_2', 'delta_bb_per_100': -8.935774123487448}]
- A2: Toby delta=-22.568433313919627, Mehedi delta=27.240755153627333, improves=False, regressions=[{'target': 'famadeo', 'delta_bb_per_100': -29.538701233952384}, {'target': 'neel', 'delta_bb_per_100': -13.204216805785734}, {'target': 'ref_mathematician', 'delta_bb_per_100': -33.4097275273746}, {'target': 'ref_ref_bot_2', 'delta_bb_per_100': -33.4097275273746}, {'target': 'ref_shark', 'delta_bb_per_100': -20.574561898315288}, {'target': 'ref_template', 'delta_bb_per_100': -20.57081772429712}]
- A3: Toby delta=34.08537575068982, Mehedi delta=12.15352371461492, improves=True, regressions=[{'target': 'famadeo', 'delta_bb_per_100': -5.222170470423848}, {'target': 'neel', 'delta_bb_per_100': -29.68256284158254}, {'target': 'pav_skantbot7_6', 'delta_bb_per_100': -35.155397598182404}, {'target': 'pav_skantbot7_9', 'delta_bb_per_100': -30.061116005873714}, {'target': 'ref_mathematician', 'delta_bb_per_100': -51.11492281303603}, {'target': 'ref_ref_bot_2', 'delta_bb_per_100': -51.11492281303603}, {'target': 'ref_shark', 'delta_bb_per_100': -33.82716606498195}, {'target': 'ref_template', 'delta_bb_per_100': -33.27626811594203}]
- A4: Toby delta=38.868608346245765, Mehedi delta=11.05536420541246, improves=True, regressions=[{'target': 'famadeo', 'delta_bb_per_100': -13.775422532618169}, {'target': 'neel', 'delta_bb_per_100': -42.81559645986664}, {'target': 'pav_skantbot7_6', 'delta_bb_per_100': -57.35438653973059}, {'target': 'pav_skantbot7_9', 'delta_bb_per_100': -24.620000000000005}, {'target': 'ref_mathematician', 'delta_bb_per_100': -78.11447811447813}, {'target': 'ref_ref_bot_2', 'delta_bb_per_100': -78.11447811447813}, {'target': 'ref_shark', 'delta_bb_per_100': -47.70216606498195}, {'target': 'ref_template', 'delta_bb_per_100': -47.52626811594203}]
- A5: Toby delta=0.0, Mehedi delta=27.240755153627333, improves=False, regressions=[{'target': 'neel', 'delta_bb_per_100': -12.954990656406963}, {'target': 'pav_skantbot7_6', 'delta_bb_per_100': -5.968832907296494}, {'target': 'ref_mathematician', 'delta_bb_per_100': -33.4097275273746}, {'target': 'ref_ref_bot_2', 'delta_bb_per_100': -33.4097275273746}, {'target': 'ref_shark', 'delta_bb_per_100': -20.574561898315288}, {'target': 'ref_template', 'delta_bb_per_100': -20.57081772429712}]

Locked v_final.zip remains upload target unless human explicitly opens MODIFY gate.
