# Preflop / Sizing Audit — does the postflop "threshold-to-stackoff" bug exist preflop?

**Date:** 2026-06-03 · **Scope:** investigation-only · **Tool:** `tools/preflop_sizing_audit.py`
**Source audited:** `PokerBot-claude/src/{preflop_lookup.py, ranges.py, sizing.py, bot.py}` — the
**deployed-equivalent** elaborate build (per `consult/artifacts/2026-06-03-qual2-patch/FINDINGS.md`;
the tiny `PokerBot/src/*.py` is the simple `v_final` variant, not what shipped).

## Question
The postflop leak (qual2-patch): `postflop.py` facing a bet used `eq >= 0.80` where
`eq = hand_strength` = **equity vs a RANDOM hand**, authorising a `current_bet * 3` re-raise that
compounded into full-stack jams at ~12% real equity on wet/paired/flush boards. Does **preflop**
or **sizing** contain the same shape — a strength threshold that ratchets a marginal holding into a
disproportionate stack commitment?

## Verdict: **NO** — no equivalent bug preflop or in sizing.

### Static evidence (all checks PASS)
1. **No equity threshold in the preflop path.** `preflop_lookup.py` and `bot.py::_preflop_action`
   contain zero calls to `hand_strength` / `equity_vs_range` and no `eq >= x` comparison. Preflop is a
   pure **range-tag lookup** keyed on `(position, canonical_hand, action_seq)`. The equity-vs-random
   miscalibration that drove the postflop bug structurally **cannot occur** here.
2. **The all-in tag is range-gated and reachable only at the top of the betting tree.**
   `preflop_lookup.py` emits `{"tag": "all_in"}` exactly **once**, under `len(raises) >= 3`, and only
   for `{AA, KK, AKs, AKo}` (`preflop_lookup.py:131-133`). The tree **narrows monotonically** as
   betting escalates: `open` (any range hand) → `threebet`/`call` (1 raise) → `fourbet`/`call`
   (2 raises) → `jam premiums only` (3+ raises). A marginal hand drops out at each tier — the exact
   opposite of the postflop path, where `eq >= 0.80` stayed true and kept re-raising.
3. **Sizing caps at stack.** `sizing.py::legal_raise_total` converts any target with
   `chips_needed >= my_stack` to `all_in` (`sizing.py:51-52`); there is no `current_bet * 3`
   geometric escalation. Preflop raise multipliers are bounded and tier-locked: open 2.5–3×BB,
   3-bet 3–3.5×, 4-bet 2.3× (`bot.py:289-309`).
4. **The postflop bug pattern (`current_bet * 3` off an equity threshold) is absent** from the
   preflop/sizing source.

### Empirical evidence (Thorp, 12 matches / 6,915 hands — see `stackoff_decisions.csv`)
59 stackoffs (Thorp committed ≥40% of his hand-start stack). Origin attribution:

| origin | n | net chips | preflop all-ins | where the chips went in |
|---|---|---|---|---|
| **postflop-escalation** | **47** | −8,670 | 0 | pf 10,119 / postflop 153,536 |
| preflop-raise | 7 | −8,086 | 5 | pf 59,311 / postflop 732 |
| preflop-flat | 2 | −18,961 | 1 | pf 18,761 / postflop 838 |
| none (<40% but listed) | 3 | +3,676 | 0 | — |

- **47/59 stackoffs originate postflop** — the commitment decision is made in `postflop.py`, already
  gated by the qual2-patch `_can_commit` board-nuttedness fix.
- The **9 preflop-origin stackoffs are overwhelmingly preflop all-ins** (money in preflop, board ran
  out): mostly Thorp as the **preflop aggressor** getting coolered with legitimate jam hands
  (`KsQs` into `AA`, `AcTc` into `KK` — 16%/30% equity), plus short-stack jams. These are within
  reasonable preflop ranges; the losses are **variance/coolers, not a systematic threshold leak**.
- The only "flat → stackoff" signal is **2 hands, −18,961**: one standard `JJ` flat vs a 3-bet that
  ran into a board it lost on (cooler, was 59% preflop), and one bad `Ts9c` preflop all-in call.
  `n=2` is far too small to justify a surgical preflop change, and the deployed `facing_bb_3bet_deep`
  PATCH-1 already folds weak speculative deep 3-bet flats.

## Residual preflop note (not a tonight-patch)
Deep 3-bet **flats** (`CALL_VS_THREEBET = {JJ,TT,99,AQs,AJs,ATs,AQo,KQs}`) can feed large postflop
pots. But the *commitment* in those hands is made postflop and is therefore **covered by the postflop
`_can_commit` gate** — except the rare preflop all-in call (n≈1 here). Stacking an unproven preflop
range change on top of the proven postflop fix is **additive risk for negligible measured EV**.

## Recommendation
**Do not patch preflop or sizing tonight.** Ship the proven postflop stack-off fix. If a future
window wants to address realization, the higher-value target is Thorp's **raise-or-fold tendency**
(call frequency ≈2%), not a preflop threshold bug that does not exist.
