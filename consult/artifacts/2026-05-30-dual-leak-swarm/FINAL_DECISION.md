# Dual-Leak Swarm — Final Decision (2026-05-30)

## RECOMMENDATION: SHIP THE LOCKED `submissions/v_final.zip` (sha `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`). Do NOT promote a candidate before the qualifier.

The swarm attempted to fix both live leaks (Toby river trap, Mehedi BB defense). Neither yields a
promotable candidate on the decision-grade tournament metric.

## Mehedi (Lane B) → NO_BB_FIX
The HU big-blind defense leak resists a clean fix: any band wide enough to touch Mehedi's 2.5x/3x
pressure spots wrecks early stack trajectories / regresses the field; the only safe band (min-open
only) shows ~zero delta vs Mehedi. Mehedi stays unaddressed; locked covers it by default. (The Lane B
session crashed before its formal report; see laneB-mehedi-bb/CLOSEOUT_NO_BB_FIX.md.)

## Toby (Lanes A + C) → clean H2H, but NET-NEGATIVE in six-max pods → NOT promotable
- The "blockers" that shelved P2 were noise (advisor hypothesis, confirmed): at 50k paired seeds the
  Pav 7.9 regression CI includes zero, and the P2 `FAIL_HAND_COUNT_BASELINE_PARITY` was a quirk of that
  lane's own harness — the authoritative engine smoke passes 5/5 deterministically.
- Paired H2H vs Toby (same seeds): candidate **+780,000** chips (base142) / **+820,000** (base242), and
  the candidate busts SLOWER (survives ~2.4x longer). A decisive heads-up win.
- BUT the qualifier scores cumulative SIX-MAX POD chip delta, and there the candidate is NET NEGATIVE
  (paired candidate − locked, 40 seeds each, same seeds, 0 errors, SHAs intact):

  | Pod | Paired chip delta | Bust rate cand vs locked |
  |---|---:|---|
  | C0 baseline (no Toby) | +40,260 | 72.5% vs 75.0% |
  | C3 Toby+Mehedi weak field | +34,730 | 40.0% vs 55.0% |
  | C1 single-Toby weak field | **−128,826** | 47.5% vs 45.0% |
  | C4 public nightmare | −19,313 | 35.0% vs 42.5% |
  | **Net (all pods)** | **−73,149** | — |
  | **Net (Toby-containing pods)** | **−94,096** | — |

- Why the H2H win does not generalize: in a single-Toby + weak-field pod, most pot action is against the
  weak field, not Toby. The river-check that beats Toby heads-up sacrifices value against the field it is
  no longer raising — so the candidate wins the duel but loses the pod. C1 is a broad negative
  (mean −3,221/seed, p10 −29,870), not a single-seed fluke.

## Decision rule applied
Default = ship locked. No candidate shows a positive pod-metric reason to replace a battle-tested
artifact ~1.5 days before a £4k qualifier. No-regression is necessary, not sufficient; this candidate is
net-negative on the actual scoring metric and busts more in the single-Toby pod. → **SHIP LOCKED.**

## Invariant honored throughout
Protected `v_final.zip` and `best_green.zip` verified sha `e4b4a8f1...` UNCHANGED at every lane
start/end. No candidate ever overwrote either. All candidate work lived under new names in isolated
worktrees off `release/v_final-e4b4a8f1`.

## What was NOT run (and why that's correct)
Lane D (Toby-class prevalence) was held and is now moot: prevalence only mattered to size a benefit that
does not exist — the candidate fails the pod bar regardless of how common Toby-class bots are.

## OPEN ITEM FOR THE HUMAN
Confirm the OFFICIAL qualifier submission cutoff (date / time / timezone) and upload the locked
`v_final.zip` with margin. Only the internal freeze 2026-05-31 23:59 UTC is documented in-repo.

## Artifacts
- `PLAN.md` (orchestration plan + live findings)
- `laneA-postflop-v2/` — P2_ALREADY_CLEAN: clean candidate, paired H2H, static gates
- `laneB-mehedi-bb/CLOSEOUT_NO_BB_FIX.md`
- `laneC-toby-gauntlet/` — authoritative smoke logs, paired Toby JSONs, POD_RESULTS.md, pod_summary.json
