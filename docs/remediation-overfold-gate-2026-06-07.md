# Remediation PR — Over-fold risk gate + record correction (2026-06-07)

Branch: `remediation/overfold-gate-2026-06-07`. Tag: `overfold-probe-2026-06-07`.
Authoritative brief (read-only): `docs/investigations/why-predicted-risk-shipped-2026-06-06.md` (§7 gate, §8 diffs).
**Nothing was uploaded, shipped, or sent to any portal.** Every change is a commit on this feature branch for human review.

## Commits (on top of a baseline checkpoint of the pre-existing dirty tree)
| Commit | Workstream | What |
|---|---|---|
| `42deef4` | — | checkpoint: pre-remediation working-tree baseline (NOT authored by this run; isolates remediation deltas) |
| `4d48b6c` | A | correct dead single-elim / variance-as-asset premise across docs |
| `2f08141` | C/D | institutionalize premise-tagged decision gate + freeze lanes |
| `35425cc` | B | build mechanism-matched over-fold exploiter + bleed instrument + run |
| (this) | consolidate | fill worked gate example with B's real numbers + this summary |

## Headline measured result (Workstream B — the instrument that was missing)
Run vs **frozen b108eff5** (`sha256 b108eff59b46b713fdfb1530f73eaeaa924f5dd9cb5ed72d3e63512a9ce3c36b`), 25 paired seeds × 2 HU orientations, 9,998 hands, 0 hero/opp errors.

- **Isolated over-fold bleed: −12.43 bb/100** (−124,260 chips) over **1,023 flop/turn fold-after-pressure hands** — computed from engine per-action events, not win-rate.
- **Net Thorp delta: +18.85 bb/100** (CI [+16.97, +21.05]) vs this fixed HU exploiter.
- **FINDING (not forced):** the over-fold mechanism is **real and now measurable**, but a *fixed HU* exploiter does **not** reproduce the "mean EV vs a strong seed may be negative" claim. The probe deliberately did not p-hack a null into a negative.
- Evidence: `consult/artifacts/2026-06-07-overfold-probe/REPORT.md` (+ `run_10000/results/`); exploiter zip sha `ad8ca05e…`.

## Escalation result (tag `overfold-escalation-2026-06-07`) — net-negative still NOT reproduced
Follow-up per decision #1: an **adaptive** exploiter (ramps barrels on detected over-folding, defends correctly) run both **HU** and **6-max multiway** (the actual finals regime) vs the same frozen `b108eff5`.
- Adaptive HU: Thorp net **+25.21 bb/100** (CI [+23.20,+27.16]), bleed −1.51 bb/100, 39 pressure-folds.
- 6-max adaptive: Thorp net **+25.88 bb/100** (CI [+16.18,+36.05]), bleed −3.90 bb/100, 43 pressure-folds.
- **Verdict: NOT REPRODUCED on either axis; margin widened.** **Boundary (important):** the adaptive bot fired the postflop pressure-fold mechanism *far less* (39–43 vs 1,023 in the fixed-HU probe) — so this is *not* proof Thorp has no over-fold hole; it shows these heuristic instruments don't reproduce net-negative EV. The risk stays AMBER under the gate.
- Evidence: `consult/artifacts/2026-06-07-overfold-probe/escalation/REPORT.md`.

**Net conclusion across both probes:** the over-fold *mechanism* is confirmed real and quantified, but **no heuristic exploiter built in-window (fixed HU, adaptive HU, or adaptive 6-max) drives b108eff5 net-negative.** The original "mean EV vs a strong seed may be negative" remains **unconfirmed** — it would require a genuinely strong/solver-grade opponent that pressures *and* defends optimally, which exceeds these instruments. The instrument + gate are the durable deliverable; the EV claim is not established.

## Change inventory (file:line, all VERIFIED unless noted)
**A — record correction (`4d48b6c`):**
- `AGENTS.md:6,66` — finals frame corrected single-elim→Swiss/cumulative (CLAUDE.md is a symlink to AGENTS.md).
- `docs/investigations/finals-prep-postmortem-2026-06-04.md:62,159-165` — strike-corrected the dead "#57 underdog / single-elim / variance asset" rationale; re-derived Swiss liability; restated risk as over-folding bleed (not preflop busting); 17:32-consult pointer.
- `docs/tournament-spec.md:5,11,59`; `docs/finals-strategy-2026-05-27.md` (table + bracket-metric strikes); `docs/plans/finals-rd-loop-2026-05-26.md:68`; `docs/plans/finals-ev-brainstorm-2026-05-27.md` (variance-seeking premises marked historical); `docs/investigations/deep-investigation-2026-05-27.md:69,88,91-92`; `docs/deep-research-report.md:28,31`.
- Sweep: 62 matches across 12 files triaged; remaining mentions are struck/OBSOLETE/historical/source-of-truth. No uncorrected live single-elim rationale remains.

**C/D — gate + freeze lanes (`2f08141`):**
- `AGENTS.md:94-108` — premise-tagged decisions gate: premises as checkable assertions verified at PHASE-START + on every external announcement change (not only ship gate); hard named-hole→mechanism-matched-probe pairing; mechanism-match rule.
- `AGENTS.md:110-114` — two freeze lanes (strategy-shape early-lock vs late hotfix) with the Thorp 90-min lead-time rationale.
- `AGENTS.md:116-117` — reconciliation-sweep rule.
- `docs/playbooks/patch-window.md:246,293-294,301-325` — gauntlet must include an adaptive counter-exploiter; named hole AMBER until matched probe logged; worked Thorp gate entry. (`:25,:152` CLAUDE.md→AGENTS.md consistency edits — minor deviation, noted.)

**B — instrument (`35425cc`):**
- `tools/deployed_artifact_gauntlet.py:55,262-302,575-657,1029-1096` — `overfold_exploiter` opponent + fold-after-pressure bleed parser/summary/CSV.
- `tools/synthetic_opponents.py:165-239` — standalone exploiter mirror.
- `consult/artifacts/2026-06-07-overfold-probe/` — REPORT.md + run_10000 evidence + generated exploiter.

## Points requiring a HUMAN decision
1. **Diagnosis fork — now informed by two probes (RESOLVED to a decision point):** neither a fixed HU nor an adaptive HU/6-max exploiter reproduced net-negative EV for b108eff5. Decide whether to (a) accept "over-fold mechanism confirmed real but not shown net-dominant by heuristic exploiters," or (b) invest in a **solver-grade / LBR-style adaptive opponent** that maximally pressures AND defends — the only remaining instrument that could settle the EV claim. The gate keeps the hole AMBER until such a probe runs or the claim is formally retired.
2. **Optional E (deferred, lower value now):** a de-polarized Thorp variant demo — less compelling given both probes show b108eff5 already net-positive vs the over-fold exploiters; defer unless (b) above is pursued.
3. **F — DONE** (tag context, commit `afe0e74`): recomputed qualifier bust split confirms 25%/75% postflop; the RIVER-TRIAGE divergence is a different build+sample, not a true contradiction. Busting accounting only; does not change the over-fold root cause.
4. **Pre-existing leakage-audit flag:** `tools/audit_strategy_leakage.py --zip submissions/v_final.zip` returns 1 on comment/string literals (validator + match clean). Pre-existing; needs a policy/tooling decision (noted in the postmortem too).

## Confirmation
- No upload / no portal interaction / no autonomous shipping occurred. The exploiter and all zips are test instruments only.
- The frozen artifact `b108eff5` was read-only throughout (sha re-verified post-run: unchanged).
- The read-only source-of-truth investigation doc was not edited.
