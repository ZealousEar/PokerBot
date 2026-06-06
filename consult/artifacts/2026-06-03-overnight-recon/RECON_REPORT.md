# V2 Overnight Recon — Thorp field & decision reconnaissance (2026-06-03)

**Mode:** investigation-only (no runtime strategy change). **Corpus:** `data/portal_histories/`
(public hand histories). **Core tool:** `tools/field_recon.py` (validated reconstruction).
**Deployed source audited:** `PokerBot-claude/src` (elaborate build that actually shipped).

---

## ANSWERS (the block Chat 2 needs)

```
PATCH PREFLOP TONIGHT:        NO
OPPONENT IDENTITY AVAILABLE:  YES  (runtime game_state.players[].bot_id is exposed; but
                                    GATED — using it trips audit_strategy_leakage.py and
                                    risks finals overfit. Cross-match UUID stability inferred,
                                    not locally proven.)

TOP 5 RUNTIME STRATEGY RISKS (highest EV/severity first):
  1. Postflop stack-offs with ~0% real equity on wet/paired/flush boards (equity-vs-random
     overconfidence). On Thorp's LOST showdowns, mean equity at the commit street was 0.059.
     47/59 stack-offs originate postflop. THIS is the leak the qual2-patch fix targets.
  2. Raise-or-fold over-aggression: call frequency ~2.2%, AF ~26. Forgoes call/check-call
     realization; bloats medium hands into -EV commitments or folds equity outright.
  3. High bust rate (42% of matches) -> high variance, hostile to a cumulative-chip-delta
     ranking and to single-elimination finals survival.
  4. Deep 3-bet flats (CALL_VS_THREEBET) feeding big postflop pots. Mostly covered by the
     postflop _can_commit gate; the un-covered slice (preflop all-in calls) is ~1 hand.
  5. No cross-match opponent adaptation: the seat-keyed opponent model warms only after 30
     hands and identity is (by policy) unused. Plus the postflop fix is slightly too tight HU.
```

---

## Definitions (load-bearing — used by every artifact)
- **Stack-off:** a hand in which Thorp voluntarily commits **≥ 40% of his stack at the start of
  that hand** (matches the postflop `commit_frac = 0.40` gate). "Deep" = start stack > 10,000.
- **Large pot:** a hand whose **final pot ≥ 5,000 chips (≥ 50 BB)**.
- **Realization:** measured **only on showdown hands** (villain cards revealed). For a Thorp showdown
  hand we compute Thorp's equity vs the villain's *actual* hand at his **commit street** (the street
  where he put the most chips in). Fold-side over-folding is argued from **frequencies**, explicitly
  labelled inferred — Thorp's folded holdings are never revealed, so "should have called" is not
  directly computable off-showdown.
- **Origin attribution** (stack-offs): the street at which Thorp's cumulative investment first crosses
  40% of start stack, combined with his preflop role → `preflop-raise` / `preflop-flat` /
  `postflop-escalation`.

## Methodology & reconstruction validation
Portal histories expose only seat-keyed `action_log` entries with **no street markers**; `amount` is
**cumulative bet-to** for `raise`/`all_in` but **incremental** for `call`/blinds (confirmed in
`engine/game.py::_validate`). `street_ended` reflects how far the *board ran*, not where betting
stopped. We therefore replay each `action_log` through a faithful port of the engine betting state
machine (street advance via `needs_to_act` / `_handle_aggression`; side pots by `total_invested`),
mapping seats→identity from a running-stack tracker (the engine re-indexes seats among *alive* bots
each hand). Validation across **16 matches / 9,058 hands**:

| check | result |
|---|---|
| showdown `revealed_cards` set == reconstructed non-folded set | **571 / 571** ✓ |
| `winners` sum == hand `pot` | **9,058 / 9,058** ✓ |
| non-all-in hand last betting street == board length | **8,801 / 8,801** ✓ |
| Thorp per-match reconstructed net == declared `chip_delta` | **11 / 11** ✓ (12th truncated) |

> One file (`d717930b`, "Final3", 100 hands) is **truncated** — its declared finals show one bot with
> all 60,000 chips while only 100 hands are stored. Its 100 hands reconstruct correctly (reveal/pot/
> segmentation all pass); it is excluded from chip-conservation and net aggregates only.

Thorp corpus = **12 matches / 6,915 hands** (exactly matches qual2-patch FINDINGS).

---

## 1. Full-field action fingerprints  → `opponent_profiles.json`, `field_clusters.json`
74 identities profiled across the 16 matches with hands (VPIP, PFR, AF, fold/call/raise freq, avg/max
raise-to, all-in count, big-commit rate, showdown win%, bust rate, net). Rule-based clusters:

| cluster | n |
|---|---|
| nit_tight_passive | 23 |
| TAG | 20 |
| LAG | 9 |
| maniac_boombust | 7 |
| loose_passive_station | 3 |
| insufficient_data (<60 hands) | 12 |

The field is **aggressive and boom/bust** — consistent with the portal stats API
(`qual2-patch/opponents_top25_stats.md`: top bots bust 31–64%). Cross-check of my reconstructed AF /
fold% / raise% against the portal table is **directionally consistent** (rank-correlated); absolute
gaps come from sample-subset (e.g. APEX 922 hands here vs 10,543 portal-wide) and AF definition.
Note `Bot1` is **ambiguous** — two distinct UUIDs share that name in the field.

**Thorp's own fingerprint is an extreme outlier:** VPIP 0.49 / PFR 0.48, **call freq 0.022**,
AF ~26, raise freq 0.57, fold 0.40, bust rate 0.42, showdown win% 0.62, big-commit rate 0.011. He is
a near-pure **raise-or-fold maniac** who wins most showdowns but commits with poor discipline.

## 2. Large-pot / stack-off spots  → `large_pot_decisions.csv`, `stackoff_decisions.csv`
- **211 large-pot hands** (final pot ≥ 5,000), **608 Thorp decisions** logged with full context.
- **59 stack-offs** (≥40% start stack): **net −32,041**, gross loss **−104,407**, gross win +72,366,
  **won 37/59 (63%)**. Signature: Thorp wins *most* big pots but loses *bigger* on the losers — the
  asymmetric tail of equity-vs-random overconfidence, not random bad luck.
- **Origin:** postflop-escalation **47** (−8,670) · preflop-raise 7 (−8,086) · preflop-flat 2
  (−18,961) · none 3 (+3,676). **The stack-off leak is overwhelmingly postflop** — exactly the class
  the deployed `_can_commit` fix gates.
- Worst single hands are postflop jams **drawing dead**: `2sKd` two-pair into a made straight
  (−11,500); `JhJs` into a flush board; `QhAc` two-pair into a set. (See `showdown_spots.csv`.)

> **FINDINGS reconciliation:** qual2-patch reported "16 all-ins, 12% won, −81,149; 6 deep −73,434".
> Chip-exact reconstruction shows literal all-ins are only **12–13 hands, 38–42% won, net −18k to −29k**.
> The −81k/−96k magnitude matches the broader **≥40%-stack commitment class measured as gross loss**,
> not literal all-ins, and the "12% won" is not reproducible (Thorp wins 42% of true all-ins, 63% of
> ≥40% commits). The prior diagnosis **conflated all-ins with the big-commit class and reported
> gross-ish losses**. Direction (postflop stack-off discipline) is right; magnitude was overstated.

## 3. Call / check-call realization  → `showdown_spots.csv` (115 Thorp showdown hands)
- **Equity at the commit street, by outcome:** WON hands mean **0.906**, LOST hands mean **0.059**.
  When Thorp loses a showdown he was typically **near-drawing-dead at the moment he committed** — a
  clean, hindsight-cards confirmation that the leak is *committing too much with dominated equity*,
  not getting unlucky with good equity.
- Thorp's **call frequency ~2.2%** (raise-or-fold) means he routinely **forgoes pot-control and
  check-call lines** that would realize medium-strength equity. With showdown win% 0.62, his made
  hands are fine — the EV he leaves on the table is in the **medium/marginal class** that he either
  bloats (→ stack-off) or folds. *(Fold-side magnitude is inferred from frequencies; Thorp's folded
  cards are never revealed, so it is not directly measurable.)*

## 4. Preflop / sizing threshold-to-stackoff bug?  → `PREFLOP_AUDIT.md`, `tools/preflop_sizing_audit.py`
**No.** Preflop is a pure **range/tag lookup** — zero equity/`hand_strength` calls; the all-in tag is
emitted once, gated to `{AA,KK,AKs,AKo}` at `len(raises)>=3`, and the betting tree narrows
monotonically as raises escalate. `sizing.legal_raise_total` caps every target at stack (no
`current_bet*3` geometric blow-up). Empirically, only 9/59 stack-offs are preflop-origin and those
are overwhelmingly **preflop all-ins as the aggressor** (coolers like `KsQs` vs `AA`), not a
threshold ratchet. The equity-vs-random miscalibration that caused the postflop bug **cannot exist**
in a range-gated preflop.

## 5. Runtime opponent identity in `game_state`?  → see below
**Available: YES (gated).** `engine/game.py::Player.to_public_dict()` returns `"bot_id"` for **every**
player (line 66), so `game_state["players"][i]["bot_id"]` is exposed to `decide()`; the same id also
appears in `match_action_log[].bot_id` (`sandbox/match.py:301`, injected via `_inject_match_log`).
Within-match identity is **certain**. Cross-match **stability is inferred**, not locally provable: the
local harness derives `bot_id` from the bot filename (`match.py:344-353`), but the portal stores
stable UUIDs (`bots[].bot_id`), so the tournament value is almost certainly the stable UUID.
**Two reasons not to use it tonight:** (a) `tools/audit_strategy_leakage.py` lists `bot_id` /
`opponent` as forbidden strings — branching on identity **fails the team's leakage gate**; (b)
hard-keying to qualifier UUIDs is exactly the overfit the near-Nash-baseline finals frame warns
against. The sanctioned channel is the **seat-keyed behavioural** `opponent_model`.

---

## Required conclusions
1. **Is runtime opponent identity available?** Yes — `players[].bot_id` and `match_action_log[].bot_id`
   are in the live state. But it is gated by the leakage audit and is strategically risky for finals;
   cross-match UUID stability is inferred. **Treat as available-but-unused.**
2. **Thorp's worst remaining decision classes** (ranked):
   (a) **postflop big commitments / stack-offs with dominated equity** on wet/paired/flush boards
   (losers avg 0.059 equity at commit) — the proven leak;
   (b) **under-realization from raise-or-fold** (call ~2.2%) — leaves medium-hand EV unrealized;
   (c) high **bust-rate variance** (42%).
3. **High-confidence preflop/sizing leaks worth patching tonight?** **No.** Preflop/sizing have no
   threshold-to-stackoff bug; the stack-off leak is postflop and already addressed. The only preflop
   signal (deep flats) is small-sample and its commitment is postflop-gated. Don't stack an unproven
   change on the proven fix.
4. **Which metrics should block upload?**
   - **Engine validator** (AST + size, authoritative) PASS; `import_audit` PASS.
   - **`audit_strategy_leakage` PASS** — critically, confirms no `bot_id`/identity branching slipped in.
   - **edge_cases 48/48**, **smoke_run 200/200 with 0 errors**.
   - **LBR**: preflop ≤ 100, aggregate ≤ 200 mbb/g.
   - **Acceptance** (`qual2-patch/acceptance_test.py`): the real-hand bust hands (`8d3d`, `Kc4h` flush
     board) still **FOLD**; nut/safe hands still **COMMIT**.
   - **Stack-off regression guard:** new build must not **increase ≥40%-stack commitment frequency**
     or worsen stack-off net vs `best_green`; deep-stack-off −EV must not regress.
   - Preserve `best_green.zip`; use paired seeds or ≥ 50k hands for any benchmark acceptance
     (10k single-run CI ≈ ±20 bb/100).

## Artifacts (this directory)
- `RECON_REPORT.md` (this file) · `PREFLOP_AUDIT.md`
- `opponent_profiles.json` (74 identities) · `field_clusters.json`
- `large_pot_decisions.csv` (608 decisions / 211 hands) · `stackoff_decisions.csv` (59 hands,
  origin-attributed) · `showdown_spots.csv` (115 showdown hands, equity-at-commit)
- Tools: `tools/field_recon.py` (reconstruction core, `validate`/`emit`),
  `tools/preflop_sizing_audit.py`

## Adversarial verification
Three independent verifiers (separate code paths / fresh context) were run to refute the load-bearing
claims:

- **Runtime identity (item 5) — CONFIRMED `available_gated`.** Independently traced
  `game.py:66 (Player.to_public_dict → "bot_id") → game.py:572 (_build_state) → match.py:293 (act)`,
  corroborated by `validator.py:103,106` (canonical state contract includes `players[].bot_id`).
  `match_action_log` carries `bot_id`; stability = **stable-UUID inferred** (local harness uses
  filenames); `audit_strategy_leakage.py` **does flag** the literal `bot_id`. Matches this report.
- **Preflop/sizing (item 4) — CONFIRMED `no_bug_confirmed`, leak_found = false.** Independently
  verified no equity/`hand_strength` in the preflop path; all-in tag gated to `{AA,KK,AKs,AKo}` at
  `len(raises)>=3`; sizing caps at stack. Key articulation: *"each escalation re-gates the hand
  against a strictly smaller range, so the raise war terminates for non-premiums before any stack-off
  — the structural inverse of the postflop bug, where one static `eq>=0.80`-vs-random threshold
  re-authorised `current_bet*3` indefinitely."*
- **Reconstruction numbers (items 1–3) — independent re-derivation did not converge in ~45 min and
  was stopped as redundant.** Notably, the verifier's own difficulty re-implementing marker-less
  street segmentation reinforces why this report ports the engine state machine rather than guessing.
  Not blocking: the reconstruction is already validated against **external ground truth** — the
  `revealed_cards` set match (571/571) uses portal-supplied showdown cards, and the per-match net
  check (11/11) uses portal-supplied `declared chip_delta`; neither figure comes from `field_recon.py`.

## Verification status
Reconstruction externally validated (revealed-set + chip_delta tables above). Two of three adversarial
verifiers confirmed the preflop and identity conclusions; the third (independent reconstruction
re-derivation) is a redundant confidence layer.
