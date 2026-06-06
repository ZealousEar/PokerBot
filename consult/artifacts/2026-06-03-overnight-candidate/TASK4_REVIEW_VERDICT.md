# Task 4 — Adversarial Review Verdict

Candidate: `submissions/v_overnight_v2.zip` (overnight-v2, branch `v2-overnight-2026-06-03`, deployed `c8ab743` → `b43e81b`)
SHA256: `be7503d3bd4b3dca72978429e2e5f59a642ad5d01824a82d8cab2abedbf899b4` (matches V2_RESULTS; zip `src/*.py`+`data/*.npz` byte-identical to the reviewed worktree)
Date: 2026-06-03 · Runtime verified: Python 3.10.18 (sandbox-matched)

BLOCKERS:
- none

WARNINGS:
- [#5-cousin / dominated boat] `src/hand_features.py::full_house_or_better` short-circuits the commitment gate unconditionally (returns True regardless of equity). The trigger is NOT rare — any made boat that is dominated qualifies, including the common single-paired under-boat (e.g. hero `77` on `K K 7` loses to any `Kx`; verified `Qc9h` on `Kd Ks Qs Qd 5c` → `can_commit_raise=True` at ~10% equity). Why it is non-blocking anyway: boats were NOT the leak class the patch targets — the recon's worst real stack-offs were two-pair/overpair/non-nut-flush into bigger made hands (`2sKd` two-pair into a straight, `JhJs` into a flush, `QhAc` two-pair into a set), and all of those remain correctly gated. So `full_house_or_better` leaves an ADJACENT cooler unfixed rather than re-opening the targeted leak; it does not crash, return illegal, or bypass the gate (it is the gate's own branch). Fix: gate `full_house_or_better` behind an equity check on multi-paired boards (require nut/near-nut boat).
- [#7 / overfold] `src/commitment.py::can_call_large` hard-returns `False` whenever `owed_frac > 0.25`, ignoring pot odds/equity (verified: `eq_strong=0.60, pot_odds=0.30, owed_frac=0.26 → False`). A priced-in +EV call is folded once the bet exceeds 25% of remaining stack and the hand is not nutted. The failed-raise→call degrade exists but only below the 0.25 cliff. Net vs baseline it folds LESS (fixed-spot: fold 6→2, call 1→8) and FINDINGS already flags "slightly too tight HU," so it is acceptable bounded discipline, not a correctness fault. Fix: make the cap equity-aware (permit the call above 25% when `eq_strong` sufficiently exceeds `pot_odds`).
- [#11 / evidence] The +EV magnitude is INFERRED from replays, not measured. `RECON_REPORT.md` itself documents that qual2 `FINDINGS.md` overstated the leak ("16 all-ins, 12% won, −81,149" vs reconstructed "12–13 all-ins, 38–42% won, −18k..−29k"; conflated literal all-ins with the ≥40%-stack commit class), and the only DIRECT benchmark (h2h vs baseline −9.66 bb/100) is negative, hand-waved as an HU over-tightness artifact in a 6-max game. Leak DIRECTION (stop dominated postflop stack-offs) is sound and the acceptance/fixed-spot evidence is valid for the targeted spots. Do NOT justify SHIP on the EV number — justify it on the green gauntlet + sound commitment discipline + strictly-better-than-deployed.
- [#6 / multiway modeling] `src/postflop.py::_opponent_seat` reads only the first live opponent in multiway pots. Legal and non-crashing, but the overlay is blind to other players in 6-max — a strategic simplification, not a correctness issue.
- [minor] `src/opponent_model.py::observe_log` has approximate/dead counting (e.g. `_in_hand` flag never set; VPIP/PFR best-effort). Strategic accuracy only; it never raises (decide wraps it).

TESTS TO ADD:
- Multiway (3–6 handed) and side-pot / already-all-in-opponent `decide()` legality assertions (multiway currently untested; side pots only lightly in `test_engine_invariants`).
- Dominated 2nd-nut boat on a double-paired/trips board: assert `decide_postflop` does NOT stack off when `full_house_or_better` is true but equity is low (locks the #5-cousin decision).
- Explicit flush-gate tests: naked nut flush on a paired board gated at `PAIRED_EQ_THRESHOLD` (0.80); genuine non-nut flush (Ace live) gated at `FLUSH_EQ_THRESHOLD` (0.92) → fold below.
- Overfold boundary: `can_call_large` at `owed_frac` just above 0.25 with priced-in equity — assert/lock the intended fold-vs-call behavior so the tradeoff stays visible.
- Data resilience: import + `decide()` with `BOT_DATA_DIR` unset and with `field_priors.npz` absent → no exception, neutral overlay, legal action.

SHIP/NO-SHIP:
SHIP

---

## Evidence (reproduced on the actual zip, not trusted from V2_RESULTS)

### Gauntlet — all GREEN
| Gate | Command | Result |
|---|---|---|
| Engine validator (authoritative AST+size) | `validator.py v_overnight_v2.zip` | PASS — 4/4 states legal, ≤12ms each |
| Import audit | `tools/import_audit.py` | PASS (exit 0) — cold import 0.092s, RSS 38.1 MB |
| Strategy leakage | `tools/audit_strategy_leakage.py --zip` | PASS — n_hits=0; identity-branch detection (`bot_id`/`bot_name`/`opponent.name ==/!=/in`) intact; whitelist added env toggles only |
| Tests (edge+integration+unit) | `pytest tests/edge_cases tests/integration tests/unit` | PASS — 80 passed, 0.93s |
| Smoke — HEADS-UP only (crash/illegal/timeout) | `tools/smoke_run.py --zip --hands 200` | PASS — 200/200, `hero_errors=[]`, 0 errors (harness is 1v1 only) |
| Real 6-MAX match (crash/illegal/timeout) | `match.py v_overnight_v2.zip + 5 engine bots --hands 400 --seed {42,7}` | PASS — 2×400 hands 6-handed, **HERO errors 0**; Thorp net +35,280 / +13,050 (no over-fold chip-bleed; 2 seeds, not an EV claim) |
| LBR exploitability | `tools/exploit_check.py --zip` | PASS — preflop 32.1, aggregate 82.4 mbb/g (caps 100/200) |

### Focused probes (shipped entry / internal gates)
- **#1 crash/illegal/timeout** — 15 adversarial states (multiway, side-pot+all-in opp, hero stack 0, short stack, owed>stack, len-0/1/3 cards, None community, empty players, empty dict, missing keys, river huge bet) → every return legal, zero crashes. `decide()` fully wrapped in try/except → `_safe_fallback` + final `_legalize_action` (snaps sub-min raises, over-stack→all_in, rejects non-int). The lone scanner "illegal" flag was `warmup → check`, a false positive (engine discards the warmup return; smoke's warmup ran clean).
- **#1 timeout** — heaviest path (multiway wet flop facing bet, `hand_strength` + `equity_vs_range@280`): n=250 mean 7.1ms, p99 8.4ms, **MAX 12.8ms** vs 2000ms hard budget. Soft `timeout_guard` is post-hoc only; real enforcement is the engine daemon thread (legal fold on overrun). No timeout risk.
- **#2 forbidden** — validator PASS is authoritative; independent read shows only allowed libs (`os/sys/time/hashlib/random/eval7/numpy/collections/contextlib/typing`); `np.load(..., allow_pickle=False)`; no `subprocess/threading/pickle/eval/exec/__import__`.
- **#3 large-commit bypass** — none found. Every ≥40%-stack commit requires `can_commit_raise=True`; raise target capped at `current_bet + max(pot,1)` (no `current_bet*3` geometric blow-up). Verified AA on `2h7dJc` facing 60%-stack bet → `eq_strong_vs_tight=0.884`, `commit_ok=True` → legitimate value all-in.
- **#4 paired-flush** — board `7d7h Kd Qd 2d`, hero `AdJd` naked nut flush, `full_house_or_better=False`: `can_commit_raise` = False@0.50/0.79, True@0.80/0.95 → gated by `PAIRED_EQ_THRESHOLD`, NOT auto-approved by the flush branch (paired checked first). Satisfies "nut flush alone must not stack off."
- **#5 non-nut flush** — board `9d4d2d Th 3s` (Ace live), hero `KdQd` (`made_flush=True, nut_flush=False`): `can_commit_raise` = False@0.80/0.91, True@0.92/0.99 → requires `FLUSH_EQ_THRESHOLD` (0.92).
- **#6 multiway/side-pots/short/all-in** — 15-state probe all legal, PLUS two real engine 6-handed 400-hand matches (seeds 42, 7) of the candidate vs 5 engine bots: **HERO errors 0** in production-shape multiway/side-pot states, and Thorp finished top both times (no over-fold chip-bleed — refutes the #7 cliff being catastrophic in real 6-max; 2 seeds is not an EV claim). (Bot does not compute side-pot math itself — it emits a legal action on `amount_owed`; engine handles pot accounting.) Note: `smoke_run`/`benchmark` are HU-only; 6-max legality rests on the `try/except`+`_legalize_action` floor (guarantees a legal action under any state shape) confirmed by this real-match run.
- **#7 overfold** — confirmed 0.25 `owed_frac` cliff (see WARNING). Direction also confirmed good: genuinely dominated big bets fold.
- **#8 range parser** — every shipped + named token correct: `AT+`→AT/AJ/AQ/AK(s+o); `A2s+`→suited Ax ladder; `K9o+`→K9o,KTo,KJo,KQo; **`QJs-T9s`→QJs,JTs,T9s**; `88+`→88..AA; `A2+`,`K9+`,`QT+`,`JT`,`T9s`,`98s`,`KQs`,`KJs` all correct. `PRIOR_RANGE_TIGHT/LOOSE` feed the live gate and parse without raising.
- **#9 opponent fallback** — seat-keyed (not identity); cold seat (<30 hands) → all-zero neutral shifts; `_FIELD_PRIORS=None` → neutral; `exploit_shift`/`archetype` never raise on cold/garbage and are additionally inside `decide()`'s guards.
- **#10 BOT_DATA_DIR** — import-time load wrapped in try/except → neutral. Verified: baseline, `BOT_DATA_DIR` unset (→ pkg/data), `field_priors.npz` missing, and empty data dir all → `decide()` legal, no crash (`field_priors_loaded` degrades to False).
- **#11 acceptance** — re-ran: real bust hands `8d3d` (eq_strong 0.68) and `Kc`-flush/4-club (0.81) now FOLD; nut `AdJd`, safe `AA`, `KK`-set, boat-on-paired-flush all COMMIT. Reproduces V2_RESULTS exactly. Valid for the targeted spots (constructed states, not full engine replays).

### SHIP rationale
No blocker (crash / illegal action / timeout / forbidden import / validator fail / large-commit bypass) exists; the full documented gauntlet reproduces GREEN on the byte-verified artifact; the commitment discipline is sound on flush/paired boards; the residual leaks (dominated boat, 25% overfold cliff) are rare/bounded and strictly improve on the deployed bot that finished #85. The EV magnitude is inferred, not measured — SHIP rests on the green gauntlet + discipline, not the replay number.

Fallback note (three-way): if any listed warning is treated as ship-blocking, the surgical `v_qual2_stackoff_fix.zip` (postflop-only `_can_commit`) is the narrower alternative; doing nothing keeps the known leak live.
