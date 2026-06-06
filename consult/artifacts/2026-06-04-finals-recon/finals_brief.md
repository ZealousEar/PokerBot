# Finals Brief — Thorp (Fullhouse Hackathon 2026)
Assembled 2026-06-04 for downstream reviewer. Evidence-only. Companion artifacts (written concurrently, name-only): `field_meta.md`, `thorp_leak_report.md`.

---

## 0. Corpus provenance & scope (READ FIRST — affects how to trust §3, field_meta, thorp_leak)
All per-bot stats in this packet are computed from the **seeding/qualifier tournament replays** in `raw/hands/*.json` — the event that selected the 64 finalists (`raw/tournaments.json`: "Fullhouse 2026 - Demo Day 1", phase=day1, n_finalists=64; `finals_lb.json` is its cumulative-delta leaderboard). **The finals themselves are UNPLAYED** (submitted today, run after the deadline), so no finals-match data exists yet. Evidence this is seeding-field play, not finalist-vs-finalist: of 1919 matches only **1** has all six seats among the 64 finalists, and **Thorp's 40 matches contain 0 all-finalist tables** — finalists were spread across a broader mixed field (incl. non-finalists/qualifier opponents). **Interpretation:** treat field_meta and thorp_leak as a **behavioral proxy** for how these bots play (their tendencies vs a mixed field), not as a measurement of finals-table dynamics. Tendencies (VPIP/PFR/AF/fold-frequencies, leak shapes) transfer reasonably; absolute chip-delta/bust rates are vs the broader seeding field and will differ at a 64-bot or 6-bot finals table. Smoke-test/demo tournaments and aggregated multi-table records are excluded from all rate stats (see §3).

## 1. Finals phase structure
- **One frozen bot for BOTH phases.** Single zip submitted today, deadline 18:00 UTC 2026-06-04 (authoritative per CLAUDE.md + postmortem; 18:00 UTC = 19:00 BST in June). No re-submission between phases.
- **Phase A — Bubble (Swiss):** ~40 Swiss 6-max matches; advancement by **cumulative chip delta**; top 6 advance. This is a **chip-EV / max-extraction** regime.
- **Phase B — Final Table:** top 6 only; **last bot standing wins**. This is a **survival / ICM** regime (downside-bounded play favored).
- The strategic tension: the same code must serve a chip-EV regime and an ICM-survival regime, and (per §2) the bot has no signal to tell which one it is in.

## 2. Observation schema + phase distinguishability (VERIFIED)

**What `decide()` receives** — authoritative source = engine `_build_state` (`ext/fullhouse-engine/engine/game.py:555-574`) + the one key the match runner adds (`sandbox/match.py:219-221`). Runner passes stdin JSON verbatim and adds nothing (`sandbox/runner.py:84-109`). Two call shapes only:

1. **WARMUP** `{"type":"warmup"}` — once before hand 1 (`match.py:185`, `runner.py:99`); carries NO game data; bot short-circuits it (`src/bot.py:235,263` → `{"action":"check"}`).
2. **ACTION REQUEST** fields:
   - `"type":"action_request"` (`game.py:559`)
   - `"hand_id"`: str, format `<match_id>_h<hand_num zero-padded 4>` (`match.py:248`) — the ONLY hand-index/match-identity signal; bot reads it only for opponent-model dedupe (`src/bot.py:240`), never for phase.
   - `"street"`: preflop|flop|turn|river (`game.py:561`; read `src/bot.py:244`)
   - `"seat_to_act"`: int (`game.py:562`; `bot.py:103,159,172`)
   - `"pot"`: int (`game.py:563`; `bot.py:183`)
   - `"community_cards"`: list[str] (`game.py:564`)
   - `"current_bet"`: int (`game.py:565`; `bot.py:182`)
   - `"min_raise_to"`: int (`game.py:566`; `bot.py:186`)
   - `"amount_owed"`: int (`game.py:567`)
   - `"can_check"`: bool (`game.py:568`; `bot.py:181`)
   - `"your_cards"`: list[str] hole cards (`game.py:569`; `bot.py:155`)
   - `"your_stack"`: int (`game.py:570`; `bot.py:184`)
   - `"your_bet_this_street"`: int (`game.py:571`; `bot.py:185`)
   - `"players"`: list of public per-seat dicts `{seat,bot_id,stack,state,is_folded,is_all_in,bet_this_street,hole_cards:None}` (`game.py:572` via `Player.to_public_dict`; shape per `validator.py:102-109`). PLAYER COUNT = `len(players)` (`bot.py:100-101`). `bot_id` is exposed per seat → opponent identity observable.
   - `"action_log"`: list[{seat,action,amount}] for the CURRENT hand only (`game.py:573`); blinds appear as small_blind/big_blind (`game.py:337-338`); bot derives position from it (`bot.py:105-150`).
   - `"match_action_log"`: rolling cross-hand log (last MATCH_LOG_MAX_ENTRIES), injected ONLY into action_request (`match.py:219-221`); fed to opponent model (`bot.py:239-240`). Only persistent-across-hands payload; resets per match (`match.py:233`).

**NOT present anywhere:** blind level/amount (hardcoded SMALL_BLIND=50/BIG_BLIND=100, `game.py:27-28`, never escalate; bot hardcodes bb=100 at `bot.py:206-216`), starting stack as a field, `tournament_id`, `match_id` as its own field, `phase`/`stage`/`bubble`/`final_table` flag, hand-count/hands-remaining, table-number/seat-count metadata beyond live `len(players)`.

**PHASE-DISTINGUISHABILITY VERDICT (DEFINITIVE):** The bot **CANNOT distinguish a Bubble/Swiss match from the Final Table.** No phase/tournament/match-table identifier exists in either call shape. The usual inference signals are absent or degenerate in this engine: (a) blinds never escalate (`game.py:27-28,326-327`; bot hardcodes bb=100 `bot.py:206`); (b) no hands-remaining field — only `hand_num` inside `hand_id`, read solely for dedupe (`bot.py:240`); (c) field size is only `len(players)` per hand (`bot.py:100`), which shrinks as bots bust but reads identically in Swiss vs finals; (d) `match_action_log` persists within a match but resets per match (`match.py:233`) — no cross-match/tournament state. The shipped bot makes **NO phase determination at all**: it routes purely on street (`src/bot.py:244`) and per-state stack/position math; no branch reads any phase signal. **Phase is neither given nor inferrable → the bot plays identically in Bubble and Final Table.**

## 3. Table size (VERIFIED across all 1919 replay files)
- **Modal/true table size = 6 (6-MAX NLHE).** Per-match max table size = max(seat index)+1 across the match: `{4:6, 6:1788, 7:28, 9:2}` over 1824 non-empty matches → **98.0% (1788/1824) are exactly 6-handed**, 98.4% ≤ 6. Actor-based count agrees exactly. (Per-*hand* seat counts trend lower as bots bust within a match — short-handed late play — but the dealt/modal table is 6-max.)
- The seat-count anomaly in `len(seats)` (12/18/24, etc.) is **aggregated multi-table records** (N×6 seat entries, seat values cycle 0-5), NOT large tables. Genuinely >6-handed: only 30 matches / 521 hands of 840,759 (0.06%, negligible). 95 matches are empty/malformed (byes/forfeits/crashes).
- **Implication:** compute all rate stats **per-hand from seats actually dealt (indices 0-5)**, never from `len(seats)`.
- **6-max baseline norms** (interpret VPIP/PFR/AF/3bet/WTSD against these, not full-ring): VPIP ~22-28% (LAG reg), PFR ~18-22%, 3bet ~6-9%, postflop AF ~2-3, WTSD ~26-30%. VPIP <20% = nitty; >30% = loose. Raw aggregate VPIP/PFR reads lower without filtering all-fold blind hands.

## 4. Engine constraints (sandbox invariants)
- Runtime **Python 3.10** (eval7 0.1.7 won't build on 3.11+). Pinned: eval7==0.1.7, numpy==1.26.4, scipy==1.13.0, treys==0.1.8, scikit-learn==1.5.2. **No PyTorch at runtime.**
- **2 s per `decide()`**; one warmup call with **30 s** budget (load blueprints there).
- **AST validator** (`ext/fullhouse-engine/sandbox/validator.py`): forbidden modules (socket/urllib*/requests/http/subprocess/multiprocessing/pickle/threading/ctypes/importlib/…); forbidden patterns (`__import__(`, `eval(`, `exec(`, `compile(`, `getattr(__builtins__`, `os.system/popen/exec*/remove/...`). Valid actions: fold/check(can_check)/call/raise(amount=total)/all_in.
- Container flags: `--network none --memory 768m --cpus 0.5 --read-only --no-new-privileges --user 1000:1000`. Size: bot.py ≤5MB, data/ ≤200MB, total ≤250MB; bot.py at archive root; no other .py at root; no .py in data/; no symlinks/path-traversal. Data reads from `data/` at import time only via `BOT_DATA_DIR`.

## 5. Baseline `b108eff5`
- **Finals baseline = `submissions/v_final.zip` == `v_finals_rc_patched.zip`, sha256 `b108eff59b46b713…`** (VERIFIED on disk this session: `b108eff59b46b713`). Leak **PATCHED** (postflop near-dead stack-off fixed). This is the bot to ship, NOT the live R2 leak `d54640e0` / portal id `7a7ad230`.
- **Status:** validator PASS, edge near-dead guard PASS, 13 edge tests pass; but **UNBENCHMARKED** and **Docker smoke NOT run** locally; leakage audit flags comment/string literals (`postmortem :47, :785-799`).
- **Editable source (VERIFIED present):** `/Users/farhad/Code/PokerBot/submissions/archive/finals-ship-b108eff5-editable-source/src/` (bot.py, commitment.py, equity.py, hand_features.py, opponent_model.py, postflop.py, preflop_lookup.py, ranges.py, sizing.py, timeout_guard.py, __init__.py). Currently zip-only in the repo — not committed to git.
- **KNOWN RESIDUAL LEAKS in the patched gate** (code-verified, cite `docs/investigations/finals-prep-postmortem-2026-06-04.md:165-172`):
  | # | Texture | Mechanism | Severity / Freq |
  |---|---------|-----------|-----------------|
  | C | Dry unpaired bloated pot (TPTK/overpair) | `commitment.py:56` `eq >= SAFE_EQ_THRESHOLD (0.55)` vs *static* range — same class as original leak, commoner texture | High / Medium |
  | A | Trips on board (`99` on `777`) | `full_house_dominated` only checks board *pairs above our trips*; misses higher boats from over-pairs/case card | High / Low |
  | B | Monotone connected board | `commitment.py:54-55` nut-flush path jams into a possible straight flush | High / Very low |
  | bleed | Repeated barrels | `can_call_large` (`:69`) caps each call at 25% owed but not *cumulative* commitment | Medium / Medium |
  | preflop | n/a | Gate is **postflop-only**; if our 56% bust is 3-bet/4-bet-jam-driven, the gate does nothing — preflop path NOT yet audited | Potentially dominant / **Unverified** |
- Thorp's own profile (postmortem :126): chip/100 1564.78, win% 37.1, fold% 58.9, **call% 6.4**, raise% 34.7, **AF 5.45**, bust% 56, scoop% 0 — extreme polarization; an exploitable hole vs a sharp counter-exploiting seed.

## 6. The single decision question for the downstream reviewer
> Given a single frozen bot that (per §2) cannot distinguish the chip-EV Bubble regime from the ICM-survival Final Table regime and plays identically in both, and given the §5 residual leaks (notably the **unverified preflop bust source** behind Thorp's 56% bust rate and the dry-board `SAFE_EQ_THRESHOLD` gate), **what is the single highest-value, evidence-grounded action between now and 18:00 UTC** — ship-and-verify the frozen `b108eff5` as-is, or one specific narrowly-scoped change — and **what piece of evidence (which of the residual-leak probes, the deferred Docker smoke, or a bust-origin-by-street H2H) would most decisively settle that choice**? Propose nothing; identify the question and the decisive evidence.
