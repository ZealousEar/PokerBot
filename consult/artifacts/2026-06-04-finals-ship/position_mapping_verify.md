# 6-max Position-Mapping Verification — Shipped Finals Bot (`b108eff5`)

**Date:** 2026-06-04
**Mode:** read-only verification oracle (no edits to shipped bot, no upload)
**Unit under test:** `submissions/archive/finals-ship-b108eff5-editable-source/src/bot.py::_infer_position` (canonical lineage for shipped bytes)
**Oracle:** frozen engine `ext/fullhouse-engine/engine/game.py::PokerEngine` (button/blind/seat semantics)
**Tool:** `tools/verify_position_mapping.py` (tools-only, not packaged)

---

## Verdict: SYSTEMATIC BUG (active) + one latent bug (dormant)

The position mapping is **NOT correct** in 6-max. There is one **active, systematic** mislabel that bleeds preflop EV every finals match, plus one **latent** fallback bug that does not fire against the current frozen engine.

---

## Finding 1 — ACTIVE: Cutoff (CO) is mislabeled as MP in 6-max

**Severity: medium-high (real, recurring preflop EV leak).**

- **Where:** `src/bot.py` `_infer_position`, the labels list at **line ~124**:
  ```python
  labels = ["BTN", "SB", "BB", "UTG", "MP", "HJ", "CO"]   # index 5 = "HJ", index 6 = "CO"
  ```
  with `offset = (seat - btn_seat) % n` and a final `if label == "HJ": return "MP"`.
- **Bug:** the code comment one line above states the intended mapping
  `# offset: 0=BTN, 1=SB, 2=BB, 3=UTG, 4=MP, 5=CO`, i.e. **offset 5 should be CO**.
  But an extra `"HJ"` was inserted at index 5, pushing `"CO"` to index 6. In 6-max
  (`n=6`) the offset never reaches 6, so the cutoff seat (offset 5, immediately
  right of the button) resolves to `labels[5] = "HJ"`, which the trailing
  remap converts to **`"MP"`**. `"CO"` is therefore **never emitted in 6-max**.
- **Trigger condition:** every 6-max hand, whenever the bot acts from the cutoff
  (the seat one to the right of the button). Blinds are always present, so this is
  not an edge case — it is the steady state.

**Empirical proof** (`tools/verify_position_mapping.py`, real engine, dealer-rotated like `run_match`):

Locked 6-max (tables held at 6 players), 2000 hands, **57,762 decisions**:

| metric | value |
|---|---|
| total mismatches | 9,155 |
| overall mismatch rate | **15.85%** |
| distinct mismatch pairs | `{CO -> MP}` (only one) |
| CO decisions | 9,155 (15.8% of all decisions) |
| CO mislabel rate | **100.0%** |
| BTN / SB / BB / UTG / MP mislabel rate | 0.00% |

(A separate run that lets stacks deplete and tables shrink gives the same
signature: 22,043 decisions, the **only** normal-play mismatch is `CO -> MP`,
100% of CO decisions; all other positions 0%.)

**Why it matters (strategic impact):** `src/preflop_lookup.py` routes on the
position string into distinct ranges in `src/ranges.py`. Open-range sizes:

```
UTG=23  MP=40  CO=60  BTN=87  SB=71
```

`OPEN_RANGES["CO"]` is a strict superset of `OPEN_RANGES["MP"]` plus 20 extra
hand classes (`22 33 44 54s 65s 75s 86s 97s A2s A3s A4s A9o J8s JTo K7s K8s
KTo Q8s QTo T7s`). Because the cutoff is labeled MP, the bot **opens the CO with
the 40-hand MP range instead of the 60-hand CO range** — it folds 20 steal-worthy
hand classes from the cutoff that the blueprint intends to open. The same
mislabel also routes 3-bet/flat decisions through MP rather than CO logic. Net
effect: tighter-than-intended cutoff play, foregone steal/iso EV in ~1 of every
6 decisions. This is a silent leak — the bot still returns a legal action, so
nothing flags it.

**Note on table shrink:** the same off-by-one mislabels the cutoff seat
(offset `n-1`) at `n=5` as well (`labels[4]="MP"`). Headline figure above is the
finals-relevant pure 6-max case.

---

## Finding 2 — LATENT: blinds-missing fallback assumes seat 0 = SB (does NOT fire vs frozen engine)

**Severity: low against current engine (dead path); high IF the engine ever omits blind log entries.**

- **Where:** `src/bot.py` `_infer_position`, lines ~115–118:
  ```python
  if sb_seat is None or bb_seat is None:
      sb_seat = 0
      bb_seat = (sb_seat + 1) % n
  ```
- **Behaviour:** if `action_log` lacks `small_blind`/`big_blind` entries, the bot
  pins SB to seat 0 regardless of the true button, so positions are assigned with
  a fixed (wrong) origin.
- **Does it trigger?** **No, not against the frozen engine.** `engine/game.py`
  `start_hand()` calls `_post_blinds()`, which appends `small_blind` and
  `big_blind` to `action_log` **before** the first `action_request`. Every state
  the bot ever sees in this engine has both blind entries. The verifier confirms
  `blinds_present=True` for **100%** of 22,043 normal decisions.
- **Magnitude if it did fire** (synthetic run with blind entries stripped from
  the observed `action_log`): **77.6% mismatch** across 7,215 decisions, with
  errors smeared across every position pair (`SB->BTN`, `BB->SB`, `BTN->BB`, …).
  i.e. the fallback is near-random relative to ground truth.

**Assessment:** dormant given the frozen finals engine. It is only a risk if the
finals engine differs from the local clone in how it logs blinds (not expected —
`ext/fullhouse-engine` is the authoritative sandbox). Worth knowing, not worth a
code change pre-freeze.

---

## Reproduce

```bash
.venv/bin/python tools/verify_position_mapping.py --hands 1500 --seed 42
```

Outputs both the normal-play table (blinds logged) and the synthetic
blinds-stripped fallback table.

**Method notes:** `_infer_position(state)` is a pure function of
`(state, state["seat_to_act"])` and never reads bot identity, so evaluating it at
every engine `action_request` under a uniform legal-action policy is equivalent
to a real "Thorp + 5 refs" match for position-inference purposes, while covering
all six seats far more densely. Dealer rotation mirrors
`sandbox/match.py::run_match`. Ground truth is computed directly from
`engine.dealer_seat` and engine seat semantics (`SB=(d+1)%n`, `BB=(d+2)%n`,
`CO=offset n-1`); HJ is normalised to MP so the bot's intended HJ→MP alias is
**not** counted as a mismatch — only genuinely wrong labels surface.

---

## FIX APPLIED + VERIFIED (candidate copy only — frozen `b108eff5` untouched)

Per follow-up request, the CO mislabel was fixed in a **copy**, not the frozen
ship artifact:

- **Candidate source:** `consult/artifacts/2026-06-04-finals-ship/candidate-cofix/`
- **Candidate zip:** `consult/artifacts/2026-06-04-finals-ship/candidate-cofix.zip`
- **Frozen `submissions/...` artifact and `src/` tree: NOT modified.**

**The fix** (`candidate-cofix/src/bot.py` `_infer_position`): replaced the
fixed `labels` list with an offset-based mapping. The cutoff is now keyed as the
seat at offset `n-1` (always right of the button), so it stays correct as the
table shrinks below 6 after busts:

```python
if offset == 0: return "BTN"
if offset == 1: return "SB"
if offset == 2: return "BB"
if offset == 3: return "UTG"
if offset == n - 1: return "CO"
return "MP"
```

The blinds-missing fallback (Finding 2) was deliberately left as-is — it is
dormant against the frozen engine and out of scope for a one-line correctness fix.

**Verification of the candidate:**

| check | result |
|---|---|
| Position mapping (verifier, 22,043 normal 6-max decisions) | **0 mismatches (0.00%)** — CO now 0% (was 100%); all positions 0% |
| Engine validator (`sandbox/validator.py` on the zip) | **✅ PASSED** (AST + size + 4 decision smoke states) |
| 6-max match vs 5 refs (400 hands) | runs clean, **0 bot errors** |
| A/B strength — 60 paired seeds, candidate vs original, same 5-ref field, 400 hands each | **FIXED +762,924 vs ORIG +537,943 cumulative** (+224,981); per-match mean diff **+3,750**, 95% CI **[−673, +8,172]**; **30 W / 14 L / 16 T**; 0 errors |

**Read of the A/B:** strength signal is **neutral-to-positive and never a
regression**. The fix is directionally better (30–14 head-to-head, +225k
cumulative) but the 95% CI on the per-match mean narrowly crosses zero — expected,
since the change only touches CO opens (~15.8% of decisions, +20 open hands) and
the signal is swamped by 400-hand bust variance. The win is the **correctness**
guarantee (CO mapping 100%→0% wrong) with no downside, no errors, validator clean.
For tighter significance, run `tools/benchmark.py --paired-seed-base 42` at ≥50k
hands before any promotion.

**Reproduce the fix verification:**
```bash
BOT_SRC_ROOT="$PWD/consult/artifacts/2026-06-04-finals-ship/candidate-cofix" \
  .venv/bin/python tools/verify_position_mapping.py --hands 1500 --seed 42
.venv/bin/python ext/fullhouse-engine/sandbox/validator.py \
  consult/artifacts/2026-06-04-finals-ship/candidate-cofix.zip
```

**Not done (human-gated / out of scope this session):** promoting into `src/` or
`submissions/`, full ≥50k-hand benchmark vs `best_green.zip`, Docker smoke, and
the upload itself. The candidate is built and verified locally only.

---

## Recommendation

- The active CO→MP mislabel is a one-line fix (correct the `labels` list to
  `["BTN","SB","BB","UTG","MP","CO"]`, or drop the `"HJ"` slot / remove the
  HJ→MP remap). **Do not patch in this verification session** — code is frozen
  for finals; route any fix through the normal ship-gate (validator + import +
  edge + smoke + paired benchmark vs `best_green.zip`) with a human-gated upload.
- If shipping `b108eff5` as-is (per current finals plan), this is a known,
  bounded leak: cutoff plays one notch too tight. It does not produce illegal
  actions or crashes, so it is a confidence-shaving issue, not a
  disqualification risk.
