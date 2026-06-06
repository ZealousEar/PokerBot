# Lane C Toby-only gauntlet report — 2026-05-30

## Verdict

**SHIP_LOCKED.** The candidate has positive Toby H2H raw-chip evidence, but fails the actual promotion bar in six-max: C1 (+Toby weak-field) worsens p50 and bust rate versus locked. No tournament-metric reason to replace the battle-tested locked artifact.

Human promotion gate required; locked v_final.zip remains upload target unless explicitly overridden.

## Protected artifact invariant

- Expected SHA: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Start: PASS (see `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneC-toby-gauntlet/command_logs/start_sha_python.log`).
- End: PASS via `shasum -a 256` (see `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneC-toby-gauntlet/command_logs/end_shasum.log`): `v_final.zip=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`, `best_green.zip=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Protected zips were not modified or rebuilt.

## Authoritative smoke reconciliation

- Exact prior command shape was the repository wrapper: `.venv/bin/python tools/smoke_run.py --zip <candidate> --hands 200` from `/Users/farhad/Code/PokerBot`.
- Re-run 5x on the Lane A candidate: **5/5 PASS**, exit 0. Each run ended at 136/200 because `template` busted normally, with hero `+10000` and no errors.
- Reconciliation: the old report classified this as `FAIL_HAND_COUNT_BASELINE_PARITY`; the current wrapper reports `OK: normal_bust`. This is not a candidate runtime failure.

## Paired Toby H2H — raw chip delta + bust behavior

| base | artifact | raw chip delta | actual hands | hero busts | Toby busts | median hero-bust hand | median Toby-bust hand | sched bb/100 (CI) |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 142 | locked | -720000 | 2525 | 86/100 | 14/100 | 22.5 | 13.0 | -14.4 [-16.8,-12.0] |
| 142 | candidate | +60000 | 5696 | 47/100 | 53/100 | 44 | 42 | +1.2 [-2.0,+4.4] |
| 242 | locked | -920000 | 2697 | 96/100 | 4/100 | 24.5 | 13.5 | -18.4 [-19.6,-16.8] |
| 242 | candidate | -100000 | 6416 | 55/100 | 45/100 | 63 | 46 | -2.0 [-5.6,+1.6] |

- Candidate minus locked raw chip delta: base 142 `+780000`, base 242 `+820000`.
- H2H takeaway: candidate materially reduces Toby HU damage, but base 242 still loses raw chips (`-100000`) and H2H is not sufficient for promotion.

## Six-max pods — tournament metric gate

Same-day locked rerun completed C0/C1 and then stalled during later pods; C0/C1 are sufficient for fail-fast. Prior complete locked pod data from `2026-05-29-away/trap-sixmax-prevalence` is included in `RESULTS.json` and agrees directionally.

| pod | status | locked cum | locked p50 | locked bust | candidate cum | candidate p50 | candidate bust | delta cum | gate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| C0_BASELINE_RECHECK | complete | -417324 | -10000 | 70.0% | -295809 | -10000 | 65.0% | +121515 | PASS_NO_WORSE_P50_BUST |
| C1_SINGLE_TOBY_WEAK_FIELD | complete | +773177 | +3686 | 40.0% | +318026 | -7362 | 49.0% | -455151 | FAIL |
| C3_TOBY_MEHEDI_WEAK_FIELD | partial_or_skipped_after_fail_fast; not decision-grade | +16120 | -10000 | 52.5% | -5914 | -3278 | 40.0% | -22034 | NOT_USED |
| C4_PUBLIC_NIGHTMARE | partial_or_skipped_after_fail_fast; not decision-grade | +100543 | +2067 | 42.5% | +3672 | +1836 | 0.0% | -96871 | NOT_USED |

- C1 is the decisive blocker: candidate p50 `-7362` vs same-day locked `+3686`, and candidate bust rate `49.0%` vs locked `40.0%`.
- This violates the explicit requirement that the candidate must not worsen six-max p50 or bust rate. C3/C4 and unchanged-matchup spot-checks were stopped/skipped after this fail-fast gate.

## Files

- `RESULTS.json`: `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneC-toby-gauntlet/RESULTS.json`
- Logs: `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneC-toby-gauntlet/command_logs`
- Candidate zip: `/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-30-dual-leak-swarm/laneA-postflop-v2/zips/v_postflop_trap_v2_p2_already_clean.zip` sha `d042c977f7c29b01d3cc50f98d56edbf93c4de7b1e0ef7e73a76de1b6c6345bf`

## Final decision

**Do not promote. Upload target remains the locked `submissions/v_final.zip`.**

Human promotion gate required; locked v_final.zip remains upload target unless explicitly overridden.
