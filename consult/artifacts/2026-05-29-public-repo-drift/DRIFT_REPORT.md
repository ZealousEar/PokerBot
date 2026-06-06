# Public-repo drift audit + H2H — 2026-05-29

## Top-line verdict

**PUBLIC_PRIORS_INVALIDATED.**

Reason: at least one prior/live public opponent is now RED and at least one new public top-fork opponent is RED against locked `submissions/v_final.zip` (`e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`). No locked artifact or baseline snapshot was modified.

## Scope / invariants

- Hero was always `submissions/v_final.zip`; hash stayed `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- No files under `submissions/`, `src/`, `data/`, `tools/`, `tests/`, `ext/fullhouse-engine/`, or `ext/public-bots/` were edited by this audit.
- New clones, temporary opponent zips, logs, and scripts were written only under `consult/artifacts/2026-05-29-public-repo-drift/`.
- H2H method: artifact-bound paired seeds, two seat orientations per seed, scheduled-hand bb/100, bootstrap CI over seed-pair deltas, same policy as `tools/public_saturation.py`.

## Drift / H2H table

| repo | default branch | live head SHA | commit date | local snapshot SHA | drifted? | bot path | validator | scheduled hands | actual hands | hero bb/100 scheduled | hero bb/100 actual | 95% CI | hero errors | opp errors | p99 latency | verdict |
|---|---|---:|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Pav1602/fullhouse-engine | main | `555c84f58d01952e025ec4b80c06da7f4ec6cced` | 2026-05-25T11:00:14+01:00 | — | NEW | `bots/skantbot7.9/bot.py` | PASS | 20,000 | 16,949 | +0.20 | +0.24 | [-2.24, +2.81] | 0 | 0 | 0.0012s | GREEN; NEW-THREAT |
| Pav1602/fullhouse-engine | main | `555c84f58d01952e025ec4b80c06da7f4ec6cced` | 2026-05-25T11:00:14+01:00 | — | NEW | `bots/skantbot7.6/bot.py` | PASS | 20,000 | 14,174 | +9.61 | +13.56 | [+6.23, +12.77] | 0 | 0 | 0.0012s | GREEN; headline variant |
| vladimirfilip/fullhouse-engine | main | `f8b8723ce324685429a5098d6b76586005010210` | 2026-05-28T23:37:29+01:00 | `1fbf389224eed471a54768898acdecb093a2bd6e` | YES | `bots/vlad/bot.py` | PASS via fallback; missing public `data/gto_strategy.npz` | 1,500 partial | 270 | -6.67 | -37.04 | n/a | 0 | 0 | n/a | TIMEBOXED_PARTIAL |
| famadeo/fullhouse-engine | main | `c94dace1c6bf523aa49e9c149d897c6b71a19c5e` | 2026-05-22T14:59:01-03:00 | `c94dace1c6bf523aa49e9c149d897c6b71a19c5e` | NO | `bots/codex_holdem/bot.py` | prior PASS | 200,000 | 43,914 | +0.65 | +2.96 | [-1.30, +2.60] | 0 | 0 | 0.0643s | GREEN; prior reused |
| agrawalneel25/fullhouse-engine (`neel-work`) | neel-work | `071d54c302cbd2d9d5fcc773260e7f5f894c642f` | 2026-05-12T17:52:21+01:00 | `071d54c302cbd2d9d5fcc773260e7f5f894c642f` | NO | `bots/neel/bot.py` | prior PASS | 200,000 | 102,276 | +14.69 | +28.73 | [+13.50, +15.81] | 0 | 0 | 0.0633s | GREEN; prior reused |
| TobyCoad/fullhouse-engine | main | `93516f33675d32beaeb3228a554c1323926cd71d` | 2026-05-13T22:19:58+01:00 | `fc1cfb6413389f431db8e360d2a0b73b3feaabaf` | YES | `bots/master/bot.py` | PASS | 200,000 | 10,596 | -15.30 | -288.79 | [-16.50, -14.00] | 0 | 0 | 0.0034s | **RED** |
| stoppedtime24/fullhouse-engine | main | `52951cb7242eb1e3abc638ccd287a08ce37ff34a` | 2026-05-28T22:56:46+01:00 | — | NEW | `bots/mybot/bot.py` | PASS | 20,000 | 8,034 | +14.05 | +34.97 | [+9.09, +18.00] | 0 | 0 | 0.0012s | GREEN; NEW-THREAT |
| Mehedi-dev-2404/fullhouse-engine | main | `aa14a35a4f185f8608ae962aef17a7c620909a4b` | 2026-05-28T00:44:05+01:00 | — | NEW | `bots/mybot/bot.py` | PASS | 20,000 | 3,767 | -9.00 | -47.78 | [-14.00, -4.00] | 0 | 0 | 0.0013s | **RED; NEW-THREAT** |

Notes:
- Toby escalation completed at 100,000 scheduled hands for bases 142 and 242. Component results: base142 `-14.00` CI `[-16.00,-12.00]`, base242 `-16.60` CI `[-18.00,-15.00]`.
- Mehedi 100k escalation was attempted but time-boxed after 18,500 scheduled / 3,383 actual partial hands; partial bb/100 remained negative at `-9.19`. The completed 20k first pass is the reported RED evidence.
- Vladimir live H2H was time-boxed after 3 completed orientations because the live repo does not include `bots/vlad/data/gto_strategy.npz`; the bot validated through a slow Monte Carlo fallback and projected beyond the practical 20-minute first-pass limit.

## Prior-opponent drift assessment

**vladimir** — stale / unresolved live drift. Local prior snapshot `1fbf389...` was GREEN at `+3.70` bb/100 scheduled, CI `[+2.40,+5.00]`, over 400k scheduled. Live main is now `f8b8723...` and still points at `bots/vlad/bot.py`, but the public live clone lacks `data/gto_strategy.npz`, while the local baseline snapshot had multiple `data/*.npz` files. Validator passes via fallback. H2H was time-boxed and is not a stable verdict.

**famadeo** — unchanged. Live head equals local snapshot `c94dace...`; prior matrix remains applicable: GREEN `+0.65` bb/100 scheduled, CI `[-1.30,+2.60]`, 200k scheduled, zero hero errors.

**neel** — unchanged on tracked `neel-work`. Live branch head equals local snapshot `071d54c...`; prior matrix remains applicable: GREEN `+14.69`, CI `[+13.50,+15.81]`, 200k scheduled, zero hero errors.

**dominic / TobyCoad** — invalidated. Local prior snapshot `fc1cfb...`/`bots/dominic` was AMBER at `-1.22`, CI `[-3.24,+0.72]`, 200k scheduled. Live main is `93516f...`, no longer has `bots/dominic`, and exposes `bots/master` as the strongest/canonical named bot. Artifact-bound H2H after escalation is RED at `-15.30`, CI `[-16.50,-14.00]`, 200k scheduled, zero errors. This is a prior flip to RED.

## Pav1602 / skantbot assessment

Pav1602 is a new priority repo and was not present in the prior matrix. It was also not returned by the upstream fork API list, so it was inspected separately.

All `skantbot*` variants found: `skantbot`, `skantbot2`, `skantbot3` (no `bot.py`), `skantbot4`, `skantbot6`, `skantbot6_phase1`, `skantbot6_phase4_baseline`, `skantbot6_phase5_baseline`, `skantbot6_phase6_baseline`, `skantbot7`, `skantbot7.1`, `skantbot7.3`, `skantbot7.4`, `skantbot7.5`, `skantbot7.6`, `skantbot7.7`, `skantbot7.8`, `skantbot7.9`.

Canonical/latest inference: `play_human_hu.py` defaults to `skantbot7.9`, and `skantbot7.9` is the highest versioned submission file. The user-highlighted `skantbot7.6` was also tested. Both validate and both are GREEN against the locked artifact:

- `skantbot7.9`: `+0.20` bb/100 scheduled, CI `[-2.24,+2.81]`, zero errors.
- `skantbot7.6`: `+9.61` bb/100 scheduled, CI `[+6.23,+12.77]`, zero errors.

Conclusion: Pav is a valid new public family but not a RED threat in this audit.

## Other public forks

`gh api repos/uzlez/fullhouse-engine/forks --paginate` returned **30** public forks. All returned forks had 0 stars, so I used recent push time as the tie-breaker for the requested top-5 inspection. Top five inspected/cloned:

| fork | pushed_at | non-template bot dirs | action |
|---|---|---|---|
| vladimirfilip/fullhouse-engine | 2026-05-28T22:37:32Z | `vlad` in clone; API hit rate limit later | handled as drifted prior; H2H time-boxed |
| MatusGib/fullhouse-engine | 2026-05-28T21:58:34Z | none | template/reference only; no H2H |
| stoppedtime24/fullhouse-engine | 2026-05-28T21:58:10Z | `mybot` | validated + H2H GREEN |
| Benjamin-Yu-Sheng-Chang/fullhouse-hackathon | 2026-05-28T14:39:04Z | none | template/reference only; no H2H |
| Mehedi-dev-2404/fullhouse-engine | 2026-05-27T23:44:07Z | `mybot` | validated + H2H RED |

A content-inventory attempt over all 30 forks was partially rate-limited after metadata collection; raw files are under `metadata/forks.tsv` and `metadata/fork_bot_inventory.tsv`.

## Decision-cluster / leak section

The H2H runner used here does not emit street/position/action-class leak keys, so no localized code leak can be asserted from this evidence alone. Observable failure clusters:

- **Toby `master` RED**: repeated early all-stack busts in both seat orientations, zero errors. Across 200k scheduled / 10,596 actual hands, hero lost `-3,060,000` chips. Orientation breakdown: base142 o0 `-600k` chips (20 wins / 80 losses), base142 o1 `-800k` (10 / 90), base242 o0 `-880k` (6 / 94), base242 o1 `-780k` (11 / 89). Average actual hand count is ~26.5 per 500-hand orientation.
- **Mehedi `mybot` RED**: first pass lost `-180,000` chips over 20k scheduled / 3,767 actual hands, zero errors. Orientation breakdown: o0 `-100k` chips (5 wins / 15 losses), o1 `-80k` (6 / 14). Partial 100k escalation remained negative after 18.5k scheduled.

No `PATCH-CANDIDATE` is marked because the deficit is not localized to a specific street/position/action class by available tooling. It is a threat/regression candidate for orchestrator review.

## Ship impact

- **B10 / public-prior matrix:** changed. The matrix is invalidated by Toby `master` RED and reinforced by Mehedi `mybot` RED.
- **Qualifier upload on 2026-06-01:** this audit does not authorize modifying or replacing `submissions/v_final.zip`. If no explicit promotion gate fires, keep the locked canonical artifact. The evidence should trigger an orchestrator patch/review decision, not an ad hoc edit.
- **Locked artifact:** keep `submissions/v_final.zip` and `submissions/best_green.zip` untouched unless a separate explicit promotion gate approves a replacement.

## Recommendation

**Escalate to the orchestrator’s patch/review workflow; do not modify the locked artifact in this agent.** If no fully-gated replacement is selected before upload, keep `submissions/v_final.zip` locked.

Raw logs and sidecars are in `consult/artifacts/2026-05-29-public-repo-drift/logs/`; machine-readable summary is `RESULTS.json`.
