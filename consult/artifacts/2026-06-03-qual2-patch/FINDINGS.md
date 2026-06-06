# Qualifier II patch — stack-off discipline fix (2026-06-03)

## Situation
- Thorp finished **#85 / 300+** in Qualifier I. Metric = **CHIP Δ / 100H** (rate). Top-64 cutoff ≈ **+1,355/100H**; Thorp **+679**.
- Patch window OPEN (~12h); one upload supersedes the active bot; portal upload form live for us. A **Qualifier II** re-runs patched bots.
- Ground truth pulled from portal.fullhousehackathon (auth = Brave Supabase cookie injected into agent-browser).

## Diagnosis (from 12 real completed matches / 6,915 hands)
- Thorp profile: **BUST 56%, SCOOP 0%, AF 5.45, CALL 6.4%** vs #1 `final` (AF 1.97, SCOOP 36%) — boom/bust, exploitable.
- Leak is concentrated, not diffuse: **16 all-ins, 12% won, net −81,149 chips**; 6 deep stack-offs (>10k) = −73,434. 90% of hands commit ≤533. `bot_errors = 0` (not crashes).
- Mechanism: deployed bot is the **elaborate equity-driven** version (NOT the simple `v_final.zip`). `src/postflop.py` "facing a bet" used `eq>=0.80 → raise current_bet*3`, where `eq = hand_strength` = **equity vs RANDOM**. On wet/paired boards vs a betting villain (range capped strong) this overstates us; re-raises compound into full-stack jams at ~12% real equity. Confirmed in hand 269 (32k in on 4-club board vs nut flush) and hand 65 (jam K-high flush `8d3d` into tens-full).

## Fix (surgical, `src/postflop.py` only)
- Cap re-raise size at pot-sized (no `current_bet*3` geometric blow-up).
- Gate any **large commitment** (`max(owed, raise_chips_in) ≥ 40% stack`) on **board-aware nuttedness** via `_can_commit`:
  - flush board → require the **nut flush** (or eq-vs-tight-range ≥0.92 for boats);
  - paired board → eq-vs-tight-range ≥0.80;
  - safe board → eq-vs-tight-range ≥0.55.
- Otherwise fold (or call only if ≤15% stack). Small-pot aggression and genuine nut stack-offs unchanged.

## Validation
- **Acceptance (real field hands)**: both bust hands now FOLD (8d3d eq_strong 0.70; Kc-flush/4-club 0.87). Nut AdJd, safe-board AA, big KK-set still COMMIT. (Trustworthy signal — real data.)
- **Gauntlet (all green)**: engine validator 4/4; import_audit; strategy-leakage; edge_cases 48/48; smoke 200/200 0 errors; LBR preflop 32.1 / aggregate 81.2 mbb/g (caps 100/200).
- **Regression proxies** (advisor: use only as crash/regression check): vs templates patched==baseline (no-op vs passive — surgical); h2h vs baseline −9.66 bb/100 CI crosses 0 (HU over-tightness artifact; game is 6-max). Leak-triggering field bots unavailable locally.

## Artifact
- `v_qual2_stackoff_fix.zip` sha256 `0ec835b6ca6acbafec44236c71e257832736730e330555aa02ab01ba84cfbac7`
- Built from PokerBot-claude worktree (elaborate deployed-equivalent) + the postflop fix. Baseline preserved (`postflop_baseline.py`).

## Residual risk
- Local proxies can't reproduce the real aggressive field, so the +EV magnitude is inferred from the real-hand replay, not measured. Fix is calibrated for 6-max (tight betting ranges); slightly too tight HU.
