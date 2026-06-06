# Stage-1 Finals Packet — Verification Report
**Date:** 2026-06-04 · **Role:** verify-and-gate (independent recompute from raw data) · **Verdict: GO (corrections applied)**

All numbers below were recomputed from `raw/hands/*.json` (1919 files), `raw/finalist_dossiers.json`, `raw/our_bots.json`, and the engine source — NOT trusted from the artifacts. A canonical parser was validated against two independent gates before any stat was accepted:
- **Pot reconciliation:** 825,922 / 840,759 hands reconcile within ±2 chips = **98.24%** (leak report claims ~98.2% on Thorp's subset). Validates street-segmentation + amount convention *jointly*.
- **Zero-sum chip_delta:** 1802 / 1802 clean matches sum to exactly 0.
- **Amount convention (engine truth, `game.py:143-175`):** `raise.amount` = total-to-this-street (set), `call`/`all_in`/blinds = increment. Confirmed in code AND empirically.
- **Identity:** Thorp = `7a7ad230-2b19-46ff-af11-5df254b6f078` confirmed via `our_bots.json` (bot_name "Thorp") before computing any Thorp stat.

---

## Check results

### 1. SCHEMA TRUTH — **PASS** (blocker)
Every field claimed in `finals_brief.md §2` exists in the engine. Source = `_build_state` (`game.py:555-574`): `type, hand_id, street, seat_to_act, pot, community_cards, current_bet, min_raise_to, amount_owed, can_check, your_cards, your_stack, your_bet_this_street, players, action_log` — all present, none invented. `players[]` shape matches `Player.to_public_dict` (`game.py:63-73`, `hole_cards:None`). `match_action_log` added only to action_request by `_inject_match_log` (`match.py:219-221`). Warmup carries no game data (`runner.py:99`). Blinds hardcoded `SMALL_BLIND=50 / BIG_BLIND=100` (`game.py:27-28`), never escalate. **No phase/tournament/bubble/final-table/hands-remaining field exists** → the Bubble-vs-Final-Table-indistinguishability verdict is correct: the bot has no phase signal.

### 2. TABLE SIZE — **PASS** (blocker)  · minor label fixed
Per-match max table size = max(seat)+1: **{4:6, 6:1788, 7:28, 9:2}** over 1824 non-empty matches → **1788/1824 = 98.03% are 6-handed**. Reproduces the artifact exactly. Genuinely >6-handed = 30 matches / 521 hands (`{7:311,8:140,9:70}`) and 95 empty matches — both reproduce brief §3 exactly. Positional/3-bet metrics are attributed per-hand by seat 0-5 (6-max), correct.
- **Correction applied:** brief §3 called this "Per-hand true size"; the counts sum to 1824 *matches*, so it is per-*match* max. Relabeled to "Per-match max table size" + noted per-hand seat counts trend lower late-match. Conclusion (6-max) unchanged.

### 3. STAT FIDELITY (8 finalists) — **PASS** · one row corrected
Recomputed VPIP/PFR/WTSD/bust%/avg-chip-delta for jew, CallMeMaybe, Thorp, IveyBot, TheQuantBot, Hyperion, SevenDeuces, Worm and diffed vs `finalist_dossiers.json`:
- **VPIP, PFR:** all within ≤0.5pp. **bust%, avg chip delta:** essentially exact (e.g. Thorp 55.0/55.0, Δ6442/6442; Worm 69.2/69.2, Δ3956/3956).
- **WTSD apparent mismatch is definitional, not an error:** dossier `wtsd_pct` (jew 8.6) = showdowns / *total hands* (confirmed: 8.6 = sd/hands exactly), whereas `field_meta.md` uses revealed/saw-flop (the correct WTSD). My field-median WTSD (39.4) matches field_meta's 40.3. field_meta itself states it recomputed the inconsistent dossier WTSD/saw_flop. Packet artifact is correct.
- **Discrepancy → FIXED:** `field_meta.md` avg-chip-delta row read median **7768** (p10 4569 / p90 14404 / IQR 5257). True value (dossier-exact AND raw all-matches recompute) = median **7236** (p10 3927 / p90 13729 / IQR 5457). field_meta's 7768 matches neither all-matches (7236) nor clean-only (8196) — it was ~7% high (>5% chip-delta flag threshold). **Row corrected in `field_meta.md`.** VPIP (31.1), PFR (20.5), bust% (59.0 vs claimed 59.3) medians verified fine.

### 4. BUST SPLIT (decisive) — **PASS**
- Clean/aggregated counts reproduce the report **exactly**: Thorp in 40 files = 36 clean 6-seat + 4 aggregated multi-table; **20 clean busts + 2 aggregated** (`final_stack==0`).
- Postflop-dominant conclusion **confirmed**. Independent recompute by *biggest stack-destroying loss per bust match*: **4 preflop / 16 postflop = 80% postflop** (flop 6 / turn 5 / river 5). Report states **5 / 15 = 75% postflop** (flop5/turn5/river5). The two methods land within **±1 bust** — the difference is "the hand where the stack hit 0" vs "the hand of the biggest commitment." Both robustly say **~75–80% of Thorp busts are decided postflop**; the headline "3-of-4 decided postflop" is **supported**.
- Method note: a naive "street of last chips in" reading mis-classifies gradual blind-offs (engine caps blinds at stack, `game.py:326`, so a short stack goes all-in rather than "SB+fold") and would understate postflop — the biggest-loss/bust-hand framing the report uses is the correct one. No change needed to `thorp_leak_report.md`; its bust split is substantively right.

### 5. CLUSTERING SANITY — **PASS**
k=4: n = 7 + 24 + 21 + 12 = **64** (all finalists assigned, no empty cluster). Centroids are well separated on VPIP/PFR/3bet/AF/bust and labels match: c0 hyper-LAG (highest VPIP38/PFR29/3bet11), c1 TAG (31/21/6), c2 tight-callers/stations (lowest PFR16; **Thorp here** — consistent with his recomputed PFR 18.6/VPIP 28.3), c3 aggro value (highest AF 3.9, lowest bust 47). Sensible and consistent.

### 6. SHOWDOWN DECODE — **PASS**
Independently decoded jew's `revealed_cards` → notation: top hands T9o/Q3o/Q9o/K3o/98o/K2o reproduce the dossier; pair% 8.7 vs 9.0, suited% 26.2 vs 26.0. Spot decodes correct: `9d8s→98o` (offsuit), `Qh3s→Q3o` (offsuit), `9c8d→98o` (offsuit). Suited/offsuit/pair logic sound.

### 7. EVIDENCE-ONLY — **PASS**
No strategy or code recommendation leaked. `finals_brief.md §6` explicitly poses the decision question and states "Propose nothing." §5 residual-leak table is code-verified diagnosis (evidence), not advice. `field_meta.md` archetype "how it loses" notes are descriptive. `thorp_leak_report.md` is pure measurement. The downstream model's recommendation space is preserved.

### 8. PACKET HYGIENE — **PASS** (finding: selection was empty; rebuilt)
- **Finding:** the curated RepoPrompt selection did **not exist** (empty — only stored prompts). Built it to **exactly the 9 intended files**: `finals_brief.md`, `field_meta.md`, `thorp_leak_report.md` + `patched_src/src/{bot,postflop,commitment,opponent_model,sizing,preflop_lookup}.py` (implementation `src/bot.py`, not the root shim; excluded equity/hand_features/ranges/timeout_guard/__init__).
- No raw hands, no `data/` .npz, no post-mortem prose, no extra dossier/table md.
- **Token count: 15,147 tokens (full content of the 9 files).** (RepoPrompt auto-management attaches a 267-token codemap of a related `opponent_model.py`; cosmetic, strip at export.)

### 9. INTERNAL CONSISTENCY — **PASS**
Cross-file numbers cohere: Thorp VPIP/PFR (28/18.6) and cluster-2 placement consistent across field_meta + thorp_leak; Thorp fold-to-3bet 62.1% ≈ cluster-2 centroid (~60). Brief §0 provenance verified exactly: 1 all-finalist 6-max table in 1919, Thorp's 40 matches contain 0, Thorp in 40 files. Minor note (not a defect): brief §5 cites "56% bust" (postmortem-sourced) vs raw recompute 55.0% — 1pp, different sources; and brief's "unverified preflop bust source" (about the postflop-only *gate* code path) should be read alongside thorp_leak's empirical bust-street split (postflop-dominant) — they address different things and do not contradict.

---

## Corrections applied
1. `field_meta.md` — avg-chip-delta distribution row: `7768 / 4569 / 14404 / 5257` → **`7236 / 3927 / 13729 / 5457`** (dossier-exact, raw-recompute-confirmed).
2. `finals_brief.md §3` — "Per-hand true size" → "Per-match max table size" (+ clarifying note). Value/conclusion unchanged.

(Bot source under `patched_src/` was NOT modified.)

## Blockers
None. Both blocker gates PASS: schema claim is true (every field exists, phase truly indistinguishable) and table size is correct (6-max, 98%), so all positional/rate metrics are valid.

---

# FINAL VERDICT: **GO** — safe to ChatGPT-export.
Selection = exactly the 9 intended files, **15,147 tokens**.
