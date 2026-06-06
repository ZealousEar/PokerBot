# Critique — Overnight Thorp V2 Implementation Contract (2026-06-03)

**Scope:** plan-only contract vs ground-truth `PokerBot-claude/src`. Spot-checks confirm the defect map: `_can_commit` (`postflop.py:88`) tests flush before paired and gates both SITE A/B; `expand_range_tag` (`equity.py:47`) gives `AT+`→`{ATs,ATo}` and `QJs-T9s`→`[]`; `exploit_shift` emits 4 keys, consumers read 3 more. Q3 (case-2 = royal → COMMIT; the new non-boat nut-flush spot is the real defect) is correct. Contract is strong; concrete gaps below.

## 1. Top-3 under-specified seams
1. **SPR / effective-stack sourcing (SITE A/B).** `commitment.allow_raise` takes `spr` as a caller arg and §3 needs `effective_stack=min(my,villain)`, but `decide_postflop` computes neither today and no extractor is named. `_opponent_seat` (`postflop.py:50`) returns the *first* non-folded opponent — arbitrary in multiway, so "villain stack" is ambiguous vs the actual aggressor. Name the function returning `(effective_stack, spr, pot)` and which opponent feeds it.
2. **`hand_features` nut booleans (the real `eval7.handtype` gap).** The handtype branch *is* bounded — `made_category`/`full_house_or_better`/`is_nut_flush` are derivable manually (+ existing `_has_nut_flush`) if absent. But `handtype` yields only a *category*, never nut-ness; §3 adds `is_second_nut_flush`/`is_non_nut_flush`/`is_nut_straight`/`blocker_only` with **no derivation**, while `commitment` consumes only `full_house_or_better`+`is_nut_flush`. Fallback is adequate for what's used; the schema over-reaches (see §4).
3. **Seat→`bot_id` mapping is one-snapshot; `observe_log` spans hands.** Log entries carry seat only; `players[]` is the current snapshot. Plan never states the load-bearing assumption that seat→bot_id is match-stable, nor that `features`(`:101`)/`is_warm`/`archetype`/`exploit_shift` must switch their `_counts[seat]` key in lockstep (WP-4 omits `features`). Both call sites change arg type — `postflop` and `bot.py:205` (already calls `exploit_shift(opp_seat)`).

## 2. Specificity balance
- **Dropped framing (regression):** export §5/§8 carried floors — templates **≥15 bb/100 CI>0**, ablation/self-play **≥3**, plus the full `promote_artifact.py --holdout-comparator-sha256 …` gate-H line. Plan replaced these with "positive delta" / "confirm via `--help`". WP-6 then has no pass bar — **cite the exact done-when floors from `PROMPT.shared.md` inline** and restore the explicit promote command.
- **Locked value that is a guess:** regime cutoffs `2500/10000` and `SPR_CAP medium/deep 2.0/2.5` are asserted, but "validated by → replay regime distribution" only measures *how often* a regime fires, not correctness. Reframe as *default; retune only if a regime is degenerate*. By contrast `EQ_FLOOR 0.92/0.80/0.55` and `COMMIT_FRAC 0.40` correctly inherit current `_can_commit`/`commit_frac` values — keep asserted.

## 3. Contradictions / missing dependencies
- **Merge order WP-0..WP-6 is internally consistent**, and the WP-3→WP-4 serialization on shared `postflop.py` is correctly acknowledged (§6) — no contradiction there.
- **`field_priors.json` schema ⟂ assignment inputs:** the per-`bot_id` record omits `river_raise_freq`/`allin_freq`/`large_bet_freq`, yet §3 lists them as inputs and `overbluff_river`/`raise_monkey`/`short_stack_punter` need them. Declare stored `archetype` authoritative **or** add the fields. This is the WP-1→WP-4 handoff and is currently inconsistent.
- **WP-1 capability unverified:** the 5→10 cluster map reaches ~6 of 10; the rest need per-`bot_id` river/all-in signals WP-1 must emit. Confirm `field_recon` computes them before WP-4 depends.
- **Shared enum not single-sourced:** the 10-archetype names are written by WP-1 (into `field_priors`) and returned by WP-4 (`archetype()`) — make it one shared constant (like `ZERO_SHIFT`), not a §3 prose table.
- **Consistency nits:** `SHORT_CALL_ESCAPE_FRAC` home conflicts (§3 `commitment.py` block vs ledger `postflop.py`); WP-5 deps differ (§6 "after WP-2" vs §8 "WP-1, WP-2").

## 4. Over-planning — cut/simplify
- Drop unused `HandFeatures`/`BoardFeatures` fields (`is_second_nut_flush`, `is_non_nut_flush`, `is_nut_straight`, `blocker_only`, `trips_on_board`, `monotone`, `straight_complete`) — also dissolves seam #2's derivation question.
- `SPR_CAP["short"]=3.0` is dead config given the explicit short-regime bypass — delete the short `SPR_CAP`/`EQ_FLOOR` entries.
- `sizing.commit_raise_total` duplicates existing `pot_size_bet(pot,state,fraction)` (`sizing.py:62`) — reuse it.
- §4 Gate A–G mapping restates the test matrix a third time — compress to a pointer.

## 5. Questions that change implementation order
- **Q1 (WP-0)** correctly gated first; a SHIP-zip divergence rebases every `opponent_model`/`sizing` anchor. Keep as the hard pre-gate.
- **NEW:** does the live decision state expose `players[].stack` and a match-stable seat→bot_id? Q2 asks only about `bot_id`, not villain stack. If absent, `commitment` effective-stack collapses to `my_stack` (changes WP-3 SPR) and WP-4 ships `_field_default`-only.
- **NEW:** does existing `field_recon` already emit per-`bot_id` river/all-in freqs? If not, WP-1 grows from "extend+map" to "compute new stats" and the 10-way split may be unreachable pre-qualifier — reorders WP-1↔WP-4.
- `eval7.handtype` presence (WP-2 step 0) — already correctly gated.
