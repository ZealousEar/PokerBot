# Pre-Qualifier Review Triage — 2026-05-29

Scope: triage HIGH/MEDIUM findings from `consult/artifacts/2026-05-28-pre-qualifier-review/REVIEW.md` against the locked qualifier artifact context.

Locked artifact: `submissions/v_final.zip` / `submissions/best_green.zip`, sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.

Code references below are from `release/v_final-e4b4a8f1`, not `main` HEAD. No source files, `submissions/`, or `ext/` were modified.

Evidence used:
- `consult/artifacts/2026-05-28-gauntlet-variance/SUMMARY.md`: G1-G11 PASS across 5 repeats; all-template means: template `+71.82`, aggressor `+109.72 ± 12.06`, mathematician `+144.60`, shark `+70.43`, ref_bot_2 `+144.60`; overlay gain `+32.53`; LBR preflop `18.0` mbb/g, aggregate `7.4` mbb/g; no pass/fail flips.
- `consult/artifacts/2026-05-28-public-saturation/SUMMARY.md`: vladimir GREEN `+3.70`, famadeo GREEN `+0.65`, dominic AMBER `-1.22`, neel GREEN `+14.69`; hero errors `0`.
- `consult/artifacts/2026-05-28-pods/SUMMARY.md`: 100-seed 6-max pods C1/C3 RED, C2/C4 AMBER; high bust rates but hero error rate `0.000%`.
- `STATUS.md` tail: B8 smoke GREEN with protected artifact hashes unchanged; later gauntlet variance GREEN; public saturation GREEN/AMBER as above.
- `docs/playbooks/patch-window.md`: patch window should update compact priors / overlay thresholds only; structural `bot.py` / `postflop.py` changes are outside the safe B9 scope unless a separate fully-gated artifact is justified.
- Optional Vladimir h2h artifact present in sibling worktree: consolidated `+119.78` bb/100, 95% CI `[+98.78, +141.08]`, errors `0/0`.

## Ranked risk table

| Rank | Finding ID | Severity | Code trigger | Gauntlet visibility | Classification |
|---:|---:|---|---|---|---|
| 1 | 1 | HIGH | `src/opponent_model.py:50-54` sets `high_pressure` true on loose aggregate pressure or `current_pressure["raise_count"] >= 2`; `src/bot.py:158-175` then returns `all_in` for `score >= 72`. | Partly visible. The 50k all-template repeats, LBR (`18.0` / `7.4` mbb/g), public saturation, and 100-seed pods would show a catastrophic overlay leak. They did not. But gauntlet ablation shows overlay is weaker vs `sharp_3bet_punisher` (`+4.316` with overlay vs `+14.99` blueprint-only), so the exposure is real but bounded. Pre-qualifier fix risk is higher than shipping because it requires forbidden repackaging and would invalidate the green evidence. | candidate for B9 overlay threshold tuning |
| 2 | 3 | HIGH | `src/opponent_model.py:50-53`: `total >= 2 and raise_rate >= 0.75 and current_pressure["facing_raise"]` can trigger `high_pressure` after two observed villain actions. | Partly visible through the same overlay surfaces as finding 1. Overlay still adds `+32.53` bb/100 overall in ablation and public saturation is not broadly negative, so practical exposure is bounded. The two-sample trigger is the safest high-value B9 tuning target if histories confirm early false positives. Pre-qualifier fix risk is higher than shipping. | candidate for B9 overlay threshold tuning |
| 3 | 2 | HIGH | `src/bot.py:102-120`: `_position_label` uses raw `seat_to_act` index for 6-max (`seat >= len(players)-2 -> button`, `seat <= 1 -> early`) instead of deriving position from button/blinds. | Visible in aggregate. The 100-seed 6-max pods exercise rotating seats and show C1/C3 RED, but all-template repeats, public H2H, latency, errors, and LBR remain green/bounded. No per-position attribution proves this is the cause. Fixing requires `bot.py` structural logic, outside B9 overlay/prior scope and higher-risk before qualifier. | candidate for separate structural patch after finals evidence |
| 4 | 6 | MEDIUM | `src/postflop.py:30-53`: postflop ignores hole-card equity / board texture and uses pot-size c-bet plus paired-rank call heuristic; `src/postflop.py:18-27` loads flop tables but this function never reads them. | Broadly visible, not isolated. All-template and public H2H would expose a major postflop collapse; they are mostly GREEN with dominic AMBER and pod C1/C3 RED. This supports “known strategic ceiling,” not a qualifier blocker. Patch-window playbook forbids `postflop.py` rewiring, so pre-qualifier or B9 structural fixes are higher risk. | candidate for separate structural patch after finals evidence |
| 5 | 7 | MEDIUM | `src/preflop_lookup.py:40-42`: when not facing aggression, `heads_up_button`, `small_blind`, and `button` return min-raise with no `score` gate. | Partly visible. A field that 3-bet-punishes steals should surface in sharp-pressure archetypes and pods; current evidence is bounded: all-template repeats pass, public saturation is mostly GREEN/AMBER, and `sharp_3bet_punisher` remains positive though weaker with overlay. Pre-qualifier range edits require repackaging and are higher risk than keeping the locked artifact. | monitor in patch-window histories |
| 6 | 4 | MEDIUM | `src/preflop_lookup.py:37,49-53`: `voluntary` includes limp calls; limp+iso makes `len(voluntary) > 1`, skipping the `score >= 76 and len(voluntary) <= 1` priced-continue branch. | Weakly visible. 50k all-template and 100-seed pod aggregates can mask sparse limp+iso branches; no sequence-frequency diagnostics are in the supplied summaries. Because this depends on real qualifier field limp/iso frequency, it should be measured before any change. Pre-qualifier fix risk is higher than shipping. | monitor in patch-window histories |
| 7 | 5 | MEDIUM | `src/bot.py:60-63`: `_legalize_action` converts strategy `check` to `call` whenever `can_check` is false. | Not visible through error metrics because the emitted action is legal. If it were frequent/catastrophic, chip-delta and bust-rate surfaces would likely be worse; current public/all-template evidence bounds it. Internal strategy intent is not recoverable from histories, and fixing touches `bot.py` legalizer behavior, so this is not a B9 quick tune. | candidate for separate structural patch after finals evidence |
| 8 | 8 | MEDIUM | `src/postflop.py:18-27` eagerly loads `_flop_buckets` / `_flop_strategy`; `src/equity.py:22` defines `equity_vs_range`, with no shipped call sites for the sampler. | Directly visible to import/RSS audits, not gameplay. Import audit remains green (`~0.089s`, `~32 MB` RSS in variance summary), and unused code cannot change decision EV. Removing it before qualifier would still require a forbidden rebuild for negligible benefit. | ignore for qualifier |

## Recommended 2026-06-02 B9 patch-window watchlist

The B9 analyzer should not infer internal bot intent. It should extract field/population facts from real histories and only support a patch if the facts are strong enough to survive the full patch-window gate.

1. **Pressure overlay false positives**
   - First hand/action count at which opponents satisfy high-pressure-like stats.
   - Frequency of facing a raise after only 2 observed villain actions.
   - Frequency of single-pot `raise_count >= 2` spots.
   - Outcomes for hero all-ins with medium-strong `score 72-87` hands versus observed 3-bet/4-bet ranges.
   - Population split: value-heavy pressure vs fold-prone pressure. If pressure is mostly value-heavy, raise `high_pressure` sample floors and all-in score threshold.

2. **Open-any steal vulnerability**
   - True BTN/SB/head-up button open frequency and response rates.
   - Population 3-bet rate versus steals, especially from blinds.
   - EV of bottom-range steal opens if hole cards are available; otherwise chip delta after steal-open sequences.
   - If 3-bet-vs-steal is materially higher than public templates, consider only a fully-gated preflop/range adjustment; do not touch the qualifier artifact.

3. **Limp + iso-raise sequence frequency**
   - Count common preflop action sequences with one or more limps followed by one raise.
   - Hero continuation/fold outcomes in limp+iso spots, bucketed by hand-score bands `76-85`, `86+`, and `STRONG_CONTINUE`.
   - If limp+iso is rare, leave it. If common and costly, queue as a structural preflop patch candidate after evidence.

4. **6-max position attribution**
   - Reconstruct true positions from dealer/blind/action order in histories, independent of raw seat index.
   - Compare VPIP/PFR/RFI/steal outcomes by true position versus raw seat.
   - Flag whether losses concentrate in mislabel-prone seats. This supports a later structural fix, not a same-day unvalidated bot.py rewrite.

5. **Postflop heuristic leakage**
   - C-bet frequency and EV when hero can check and pot `>= 200`.
   - Fold/call EV facing flop/turn/river bets by made-hand class if cards are visible.
   - Probe losses in paired-only bluff-catch spots, wet boards, overpairs, and draw-heavy boards.
   - Do not wire the dead flop/equity tables during B9 unless a separate full validation plan exists; the playbook forbids postflop rewiring.

6. **Legal check-to-call anomaly proxy**
   - Histories cannot reveal the raw strategy output, but monitor large `amount_owed` calls with weak/no-showdown holdings and no prior planned aggression.
   - Treat any signal as structural-review evidence only; not a direct B9 threshold tune.

7. **Dead loaded surface budget**
   - Keep checking import time/RSS after any priors addition. Current dead loads are harmless; do not spend the qualifier patch budget removing them.

## Closing ship-override verdict

No HIGH or MEDIUM finding overrides ship-as-is for the 2026-06-01 qualifier.

Reasoning: every proposed pre-qualifier fix would require modifying/repackaging the locked artifact, which is explicitly forbidden absent a promotion gate. The observed artifact-bound evidence is green or bounded where these failures should surface in aggregate: G1-G11 passed across five repeats, all-template means remain strongly positive, LBR is far below caps, public saturation is mostly GREEN with only dominic AMBER, 6-max pods show risk but not a source-isolated blocker, and hero errors are zero. The rational action is to ship the canonical `e4b4a8f1...598` artifact unchanged, monitor the listed signals in real 2026-06-02 histories, and only promote a finals patch if it clears the full patch-window gauntlet.
