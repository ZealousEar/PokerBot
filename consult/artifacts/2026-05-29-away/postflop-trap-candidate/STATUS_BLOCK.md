[P2 POSTFLOP_TRAP_CANDIDATE 2026-05-29 verdict=PATCH_NOT_PROMOTABLE]
protected=v_final.zip,best_green.zip sha256=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598 before=PASS after=PASS
candidate=/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-29-away/postflop-trap-candidate/zips/v_postflop_trap_candidate.zip sha256=136c8cde3258995bde89eb14e91b678c329c3af2a5b16806c453a4c4d68d8571
static: leakage_zip=PASS import=PASS(0.286s,32.6MB) edge=PASS(29) validator=PASS exploit=PASS(preflop=18.0,aggregate=5.65) smoke=FAIL_HAND_COUNT_BASELINE_PARITY(136/200,no_errors; locked same)
trigger: Toby b142=+3.0 sched bb/100 CI[-3,+9], b242=-1.0 CI[-7,+5], zero errors; locked prior b142=-14.0, b242=-16.6
regression: refs template=+20 aggressor=0 mathematician=+20 shark=+20 ref_bot_2=+20; public Pav7.9=-1.0738 Pav7.6=+5.6187 famadeo=+3.8851 neel=+18.7381 stoppedtime24=+20
decision=do_not_promote; Human promotion gate required; locked v_final.zip remains upload target unless explicitly overridden.
