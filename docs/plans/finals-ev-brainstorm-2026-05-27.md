# Finals-EV Brainstorm — 2026-05-27

## Goal
Surface the highest-EV improvements for the finals candidate across three linked areas — PATCH-2A bounded postflop EV veto, vladimir-specific exploits operationalized into concrete patches, and finals-bracket-specific overlays — and triage to a top-3 in each area plus 2–3 wildcards. Each idea is grounded in `file:line` and triaged by (impact × implementability × low-regression-risk). The brainstorm is codex-primary (`PokerBot-codex/`), and every top-3 item names what would need to migrate to `PokerBot/` (main) before the finals upload.

## Background

### Worktree & artifact authority
- `~/Code/PokerBot/` is canonical; finals artifact lives at `PokerBot/submissions/v_final.zip` per `PokerBot/docs/plans/qualifier-finals-rollout-2026-05-27.md:15-18`.
- `~/Code/PokerBot-codex/` is the patch-window scratchpad for PATCH-2A + B3 priors consumer per `qualifier-finals-rollout-2026-05-27.md:103-106`.
- **Divergence trap**: `PokerBot/src/postflop.py:21-25` is currently a stub (`decide_postflop` only) — no `_equity_turn_river_action`, no `_heuristic_postflop_action`. Every codex postflop change must migrate to main before finals build, or the finals zip ships an outdated strategy.

### PATCH-2A target functions (codex)
- `_heuristic_postflop_action` at `PokerBot-codex/src/postflop.py:152` — deterministic fallback; 2/3-pot bet when checked-to with playable hand, call only on made pair when price ≤ `max(100, pot//3)`, else fold.
- `_equity_turn_river_action` at `PokerBot-codex/src/postflop.py:334` — turn/river only; calls `equity_vs_range(hero, board, (), trials=160)` (random villain), pot-odds + margin call threshold (turn 0.08, river 0.04); 0.20s soft deadline; returns `None` if equity unavailable.
- `decide_postflop` at `PokerBot-codex/src/postflop.py:366` — dispatch order: (1) `_patched_response_action` exact-key patches at `:368`, (2) `_blueprint_flop_action` flop blueprint at `:372`, (3) `_equity_turn_river_action` at `:376`, (4) `_heuristic_postflop_action` at `:380`.
- Existing safety hooks: card validation (`_card_key:113`, `_valid_unique_cards:122`), raise-amount clamping (`_raise_two_thirds_pot:132`), equity cache `[0,1]` clamp (`_cache_equity:297`), deadline wrap (`:25-27`, `:322-331`).

### Equity primitives
- `equity_vs_range(hero, board, villain_range, trials=2000)` at `PokerBot-codex/src/equity.py:22` — MC, eval7. Empty `villain_range` = random hand. Live calls use `_EQUITY_TRIALS=160` (`postflop.py:27`) → ~0.8–1.2 ms median in codex venv. Combo count has near-zero cost effect (each trial samples one combo).
- **Type mismatch**: `equity_vs_range` expects concrete two-card combos like `(("As","Ks"), …)`; `ranges.py` exports `PREMIUM`, `STRONG_CONTINUE`, `OPEN_HEADS_UP` as `frozenset[str]` of canonical strings like `"AKs"`. A `villain_range` builder must expand canonical → 169-key combo enumeration.

### Famadeo veto pattern (study reference)
- `range_bucket_hands`/`legacy_inferred_range_bucket`/`inferred_range_bucket` at `ext/public-bots/famadeo/bots/codex_holdem/bot.py:650-759` (~100 LOC range-tightening with size/position/multiway awareness).
- `postflop_fold_probability` (`:2140-2161`, ~22 LOC), `postflop_realized_equity` (`:2168-2181`, ~14 LOC), `postflop_bet_ev` (`:2184-2191`, ~8 LOC), `postflop_ev_veto` (`:2194-2223`, ~30 LOC), `postflop_call_veto` (`:2227-2242`, ~17 LOC).
- Signal hierarchy: bet-ratio buckets drive range inference → multiway + wet-board + low-SPR taxes inflate required edge → veto compares bet-EV vs passive-EV and snaps to fallback. Total famadeo footprint ~200 LOC; PATCH-2A budget is 90–130 LOC → requires aggressive simplification (drop deep range bucketing, hand-strength-based bucket only).

### Opponent model surface & B3 gap
- `OpponentModel.archetype_features(game_state)` at `PokerBot-codex/src/opponent_model.py:79-141` derives 5-archetype posterior (`range_mc_pot_odds`, `blueprint_threshold_exploit`, `risk_gated_conservative`, `stage_variant_anti_punt`, `monte_carlo_basic`) from observed public action rates. **Hardcoded constants**: `MIN_ARCHETYPE_OBSERVATIONS=20`, `FULL_CONFIDENCE_OBSERVATIONS=220`, `MAX_DEVIATION_BOUND_PP=4.0` at `:23-25` (note: **not** `MAX_DEVIATION_PP`).
- **Postflop has NO posterior plumbing**: `_decide_core` routes postflop states directly to `_decide_postflop(game_state)` at `bot.py:104-110` without calling `archetype_features`. Overlay is preflop-only via `_pressure_preflop_overlay` at `bot.py:149-152, 176-223`.
- **B3 priors consumer not landed**: no `np.load("finals_priors.npz")`, no priors-loading scaffold anywhere in `opponent_model.py` (no `numpy`/`json`/`os` imports at module level). Nearest precedent for import-time `.npz` loading: `preflop_lookup.py:20-30` and `postflop.py:28-59`.
- Test invariants to preserve: `tests/edge_cases/test_archetype_posterior.py` (uniform below threshold, peaked above), `test_overlay_bounded.py` (overlay sum ≤ `deviation_bound` ≤ 4.0; no overlay-induced all_in; `POKERBOT_DISABLE_OVERLAY=1` clean disable).

### Game-state inputs & bracket-state limits
- Engine passes only intra-match hand state per `PokerBot/docs/api-cheatsheet.md:13-28` and `ext/public-bots/vladimir/engine/game.py:555-574`: `hand_id`, `street`, `seat_to_act`, `pot`, `community_cards`, `current_bet`, `min_raise_to`, `amount_owed`, `can_check`, `your_cards`, `your_stack`, `your_bet_this_street`, `players`, `action_log`. **No `hand_index`, `total_hands`, `time_bank`, blinds, `multiway_count`, or bracket-round signal**. Multiway count must be derived from `len(players)`.
- Match harness injects `match_action_log` with `hand_num`, `seat`, `bot_id`, `action`, `amount` per `ext/public-bots/vladimir/sandbox/match.py:219-222, 299-305`. **Hand-within-match is derivable from `max(hand_num)` in match_action_log; bracket round is not.**
- Current bot extracts: stack-total at `bot.py:87-94` (`your_stack + your_bet_this_street`); position from `players`/`seat_to_act` at `bot.py:114-131`. **No existing hand-index / stack-ratio / match-phase axis** in `opponent_model.py` or `postflop.py`.

### Vladimir already-documented weaknesses (operationalize, don't re-derive)
- 4+-way pots undertrained per his own `ext/public-bots/vladimir/bots/vlad/deep_cfr/MULTIWAY_IMPROVEMENTS.md:4-21`. Existing proposed fix in his repo: oversample 4+-way + add `n_active` feature — he probably has not shipped it.
- Off-grid sizings 0.27p / 1.72p at `ext/public-bots/vladimir/bots/vlad/deep_cfr_cpp/src/config.hpp:3-17` calibrated only to common bet nodes; novel-but-near sizings should fall into untrained interpolation.
- Tree bound: max 4 raises per street at `config.hpp:51-52` → 5th-raise pots are out-of-distribution.
- 60% GTO + 40% one-step MC blend (per `consults/2026-05-27-overnight-P/vladimir_analysis.md:8-15`) — the seam is where one-step MC EV disagrees with multi-step game tree.
- Training cost prohibitive to replicate (per same analysis, `:30-34`) — we should **not** try to train his net; we exploit at runtime.

### Finals strategy prior (already in repo)
- `PokerBot/docs/finals-strategy-2026-05-27.md:64-82` argues "sharper bracket field → narrower bounded deviation" because (a) private histories → opponents have no read on us, default to Nash baseline; (b) public histories → our visible patterns get best-responded, **still** stay inside the cap.
- Brainstorm should steelman both narrower-finals and variance-seeking ideas side-by-side; the impact × implementability gate picks the survivor.

### Tooling for acceptance tests (canonical: main worktree)
- `PokerBot/tools/h2h.py` exists in `PokerBot/tools/`; **absent in `PokerBot-codex/tools/`**. Acceptance tests must invoke from main worktree against codex zip artifacts.
- `tools/benchmark.py` flags: `--all-templates`, `--six-max-mix`, `--ablate-overlay`, `--self-play --vs-prior`, `--paired-seed-base`, `--paired-seed-count`, `--hands`, `--bot`, `--min-bb`. No `--archetype-pin` flag exists.
- `tools/exploit_check.py` LBR thresholds: `--max-preflop-mbb 100.0`, `--max-aggregate-mbb 200.0`, `--samples-per-spot 600`, `--heldout-seed 9001`. Output JSON + summary line.
- `tools/audit_strategy_leakage.py` scans packaged `bot.py` + `src/*.py` for leakage tokens (`bot_id`, ref bot names, `best_green`, `v_final`, snapshot labels). **Strategy code must not reference opponent name strings or branch labels.**
- `tools/promote_artifact.py` Gate H: aggregate delta ≥ 0, regressed comps ≤ 1, manifest SHA integrity.

### Anti-pattern constraints (from prompt)
- No Deep CFR as ship candidate (allowed only as Phase D sparring).
- No off-grid sizes in our action abstraction (KANBAN "Action abstraction — explicitly DO NOT adopt").
- No opponent-name strings or env-var strategy toggles (leakage audit fails).
- No `src/preflop_lookup.py` rewrites in patch window (postflop-only per `docs/playbooks/patch-window.md` Phase 4).
- No new sizing-tree nodes; no real-time subgame solving; no threading/async/multiprocessing/file-writes-during-decide.

## A. PATCH-2A veto specifics (offensive — built in `PokerBot-codex/src/postflop.py`)

### 15 candidate ideas
1. `_bet_ratio_bucket(bet:int, pot:int) -> str` returning one of `tiny ≤0.33 | small 0.34–0.66 | mid 0.67–1.25 | large 1.26–1.49 | huge ≥1.5`, slotted next to `_response_patch_key` at `PokerBot-codex/src/postflop.py:128`; vladimir-robust per `ext/public-bots/vladimir/bots/vlad/deep_cfr_cpp/src/config.hpp:3-17` because it classifies his 0.27p and 1.72p without copying his nodes.
2. `_multiway_count(players) -> int` returning `len([p for p in players if not p.get("is_folded")])` next to `_response_patch_key` at `PokerBot-codex/src/postflop.py:128`; needed because `players` is the only multiway signal per `PokerBot/docs/api-cheatsheet.md:13-28`.
3. `_effective_spr(stack_total, pot) -> float` near `PokerBot-codex/src/postflop.py:128`, deriving from the existing stack-total convention at `PokerBot-codex/src/bot.py:87-94`; gates the low-SPR tax in the veto.
4. `_board_wetness(board) -> bool` returning `True` when 4-flush, paired, or 3-connector on board; new helper near `PokerBot-codex/src/postflop.py:128` — note the suit/rank vectors at `:239-245` are computed over hero+board combined inside `_hand_strength_bin`, so `_board_wetness` is new code, not a refactor.
5. Reuse `_hand_strength_bin` (`PokerBot-codex/src/postflop.py:205-248`) to derive `made_class ∈ {air, weak_pair, strong_pair, two_pair_plus}` for the veto's commit-meaningful-chunk predicate; avoids a new hand classifier.
6. `_villain_combos_from_canonical(canon_set, known_cards) -> tuple[tuple[str,str], ...]` expanding `ranges.py` `PREMIUM`/`STRONG_CONTINUE` to concrete two-card combos compatible with `equity_vs_range` at `PokerBot-codex/src/equity.py:22`. Expansion rules: pair `"AA"` → 6 combos `(As-Ah, As-Ad, As-Ac, Ah-Ad, Ah-Ac, Ad-Ac)`; suited `"AKs"` → 4 combos (one per suit); offsuit `"AKo"` → 12 combos (4×3 cross-suit). Filter out any combo using cards in `known_cards = {hero_c1, hero_c2, *board}`. Resolves the canonical-string/concrete-combo type mismatch flagged in Background.
7. `_passive_ev(equity, owed, pot) -> float` and `_bet_ev(equity, bet, pot, fold_prob) -> float` in `PokerBot-codex/src/postflop.py:128+`; mirrors `ext/public-bots/famadeo/bots/codex_holdem/bot.py:2184-2191` in 6 lines each. Since PATCH-2A drops the famadeo range-bucket inference surface, `fold_prob` reads from a static table keyed by `_bet_ratio_bucket`: `_FOLD_PROB_BY_BUCKET = {tiny:0.55, small:0.45, mid:0.30, large:0.20, huge:0.10}` (small bets get more folds than huge bets, reflecting field-average fold-to-cbet patterns); the table is the lever, not a derived signal.
8. Insert the bet-side veto into `_equity_turn_river_action` at `PokerBot-codex/src/postflop.py:347-352` (the `can_check` raise branch): if `_multiway_count ≥ 2 ∨ _board_wetness ∨ _effective_spr ≤ 1.5` AND `made_class ≤ weak_pair` AND `_bet_ev < _passive_ev + safety_cap_mbb[bucket]`, fall back to check.
9. Insert the call-side veto into `_equity_turn_river_action` at `PokerBot-codex/src/postflop.py:355-365` (the facing-bet branch): when bucket ∈ {large, huge} AND `equity < pot_odds + margin + 0.04 × (multiway−2)`, return fold instead of call.
10. Mirror the veto into `_heuristic_postflop_action` at `PokerBot-codex/src/postflop.py:163-175` as defense-in-depth for when `_equity_for_state` returns `None` (over budget / invalid cards) — same gate, equity-free, bucket + multiway only.
11. Optional second `equity_vs_range` call with `villain_range = _villain_combos_from_canonical(PREMIUM | STRONG_CONTINUE, known)` and `trials=80`, fired only when bucket ∈ {large, huge}; split `_EQUITY_TRIALS=160` at `PokerBot-codex/src/postflop.py:27` into `80 + 80` so the shared `_EQUITY_CALL_BUDGET_S=0.20` at `:25` is preserved.
12. Wrap the second equity call in `deadline(_EQUITY_CALL_BUDGET_S/2)` from `PokerBot-codex/src/timeout_guard.py:25-27` and short-circuit to bucket-only veto if `remaining() ≤ 0`; matches the existing deadline pattern at `PokerBot-codex/src/postflop.py:322-331`.
13. New `tests/edge_cases/test_postflop_veto.py` with one case per Phase B4 leak name (e.g. `turn__BTN__cbet__wet_paired`) that synthesizes a wet+multiway state and asserts the action transitions from raise/call to check/fold post-veto; aligns with `PokerBot-codex/tests/edge_cases/test_postflop_wiring.py` discipline.
14. Keep `decide_postflop` dispatch order intact at `PokerBot-codex/src/postflop.py:366-380` — veto fires inside `_equity_turn_river_action` and `_heuristic_postflop_action` only; fixed-response cells at `:368` and flop blueprint at `:372` are never bypassed.
15. Use existing `_cache_equity` at `PokerBot-codex/src/postflop.py:297` for the second tighter-range equity, keyed with `bucket` appended to the existing `(hand_id, street, hero, board)` key so random-range and tight-range values cache independently.

### Top 3 (impact × implementability × low-regression-risk)

#### A-T1 — Core bet/call veto in `_equity_turn_river_action` (ideas #2,#3,#4,#5,#7,#8,#9)
- **Pitch.** The famadeo veto is the single highest-EV postflop patch we can ship inside a 90–130 LOC budget; bundling bet-side and call-side into one place keeps the change atomic and reviewable.
- **Sketch.** Inside `_equity_turn_river_action` at `PokerBot-codex/src/postflop.py:334-365`, after equity is known but before the raise/check/call/fold return, compute `bucket`, `mw`, `spr`, `wet`, `made`; if `(mw ≥ 2 ∨ wet ∨ spr ≤ 1.5)` AND `made ≤ weak_pair`:
  - facing bet (`amount_owed > 0`): if `equity < pot_odds + margin + 0.04*(mw−2)`, return `{"action":"fold"}`; else fall through.
  - free check (`can_check`): if `_bet_ev(equity, bet=⅔ pot, ...) < _passive_ev(equity, owed=0, pot) + safety_cap_mbb[bucket]`, return `{"action":"check"}`; else fall through.
  - `safety_cap_mbb[bucket] = {tiny:40, small:80, mid:120, large:180, huge:260}` mbb/g (starting defaults mirroring `ext/public-bots/famadeo/bots/codex_holdem/bot.py:2210-2218` at ¼ scale; the implementing agent owns the final calibration via paired-seed sweep).
  - **Posterior-aware cap scaling (folds Section C idea #11):** when `_LAST_POSTERIOR` (C-T2) is populated AND `top_archetype == "risk_gated_conservative"` AND `top_probability ≥ 0.55`, multiply `safety_cap_mbb[bucket]` by `(1.0 + 0.3 × (top_probability − 0.5))` before the comparison — expensive vetos when posterior says villain rarely commits. This is the in-plan consumer of C-T2's `_LAST_POSTERIOR`; if C-T2 is cut, this clause becomes a no-op via the `is None` guard.
- **Acceptance.** From `PokerBot/`: `python tools/h2h.py --bot-a submissions/v_final.zip --bot-b <candidate.zip> --paired-seed-base 142 --hands 40000 --label-a baseline --label-b patch2a` and again with `--paired-seed-base 242` against famadeo zip; gate is paired Δ ≥ +15 bb/100 with CI excluding 0 (Phase B8 famadeo gate). Plus `python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42` showing no template CI low < 0; and `python tools/exploit_check.py --bot <candidate.zip> --max-preflop-mbb 100 --max-aggregate-mbb 200 --samples-per-spot 600`.
- **Risk.** False-positive veto on heads-up dry boards with weak pair could fold a +EV call vs aggressor-class opponents and surface as a `test_lbr_spot_corrections.py` regression on `flop_small_pair_call` / `river_small_bet_pair`; the `mw ≥ 2 ∨ wet ∨ spr ≤ 1.5` gate is designed to never fire heads-up on dry high-SPR, but the 20-spot LBR suite at `PokerBot-codex/tools/exploit_check.py:SPOTS` is the load-bearing safety check.
- **Migration.** `PokerBot-codex/src/postflop.py` helpers (`_bet_ratio_bucket`, `_multiway_count`, `_effective_spr`, `_board_wetness`, `_passive_ev`, `_bet_ev`) and the veto block inside `_equity_turn_river_action` → wholesale replace `PokerBot/src/postflop.py` (currently the 25-line stub at `:21-25`, so the migration is full-file replacement — this is the divergence trap from Background).

#### A-T2 — Bet-ratio-bucket-driven range tightening (#1 + #6 + #11)
- **Pitch.** Bucketing villain bet-by-pot gives PATCH-2A a single anti-vladimir lever without copying his sizing tree; paired with a tighter `villain_range` for `large`/`huge` buckets it sharpens the veto's expected value at zero new sizing nodes.
- **Sketch.** Add `_bet_ratio_bucket` and `_villain_combos_from_canonical` near `PokerBot-codex/src/postflop.py:128`; in the A-T1 facing-bet branch, when bucket ∈ {large, huge}, run a second `equity_vs_range(hero, board, villain_combos_premium, trials=80)` gated by `deadline(_EQUITY_CALL_BUDGET_S/2)`, take `min(equity_random, equity_tight)` as the veto-side equity; the original `_equity_for_state` call at `:309-330` stays unchanged for the legit pot-odds math.
- **Acceptance.** `python tools/exploit_check.py --bot <candidate.zip> --max-aggregate-mbb 200 --samples-per-spot 600 --heldout-seed 9001` (PATCH-2A must not lift aggregate LBR by >+20 mbb/g per Phase B8); `python tools/h2h.py --bot-a submissions/v_final.zip --bot-b <candidate.zip> --paired-seed-base 142 --hands 20000` against `vladimir` and `dominic` zips — gate is no opponent's paired Δ CI excluding 0 on the negative side.
- **Risk.** The 80+80 trial split widens the bootstrap CI on equity estimates relative to the current 160-trial call; mitigated by caching both keys via `_cache_equity` so subsequent decisions pay no extra MC cost, and falling back to bucket-only veto if `remaining() ≤ 0`.
- **Migration.** `PokerBot-codex/src/postflop.py` two helpers + tightened-range call site → `PokerBot/src/postflop.py`; also `PokerBot/src/ranges.py` must expose `PREMIUM` and `STRONG_CONTINUE` (verify the main copy under `release/v_final-e4b4a8f1` matches the codex copy before patching).

#### A-T3 — Heuristic-fallback mirror of the veto (#10)
- **Pitch.** When `_equity_for_state` returns `None` (invalid cards, over budget, non-turn/river), the bot falls through to `_heuristic_postflop_action` at `:154-176` — mirroring the bucket-only veto there is ~12 LOC and removes a catastrophic-fail mode where the veto is bypassed precisely when timing pressure is highest.
- **Sketch.** Inside `_heuristic_postflop_action` at `PokerBot-codex/src/postflop.py:163-175`, after the existing "paired & owed ≤ pot/3" branch, compute `bucket = _bet_ratio_bucket(current_bet, pot)`, `mw = _multiway_count(...)`; if bucket ∈ {large, huge} AND mw ≥ 3, return `{"action":"fold"}` regardless of paired/owed; otherwise preserve current behavior.
- **Acceptance.** Add cases to `PokerBot-codex/tests/edge_cases/test_postflop_wiring.py` mirroring `test_blueprint_absent_falls_back_without_crash` at `:54`, where `_equity_for_state` is monkey-patched to return `None` on a `large`-bucket multiway state — assert fold rather than call. Then `pytest tests/edge_cases -x` from `PokerBot-codex/` and `python tools/smoke_run.py --hands 200` from `PokerBot/`.
- **Risk.** Heuristic was previously the safe fallback; tightening fold criteria reduces the floor in over-budget scenarios but cannot underperform a pre-veto fold (worst case fold-where-previous-was-call = chip-neutral or chip-slightly-negative); no path here lifts a check to fold.
- **Migration.** `PokerBot-codex/src/postflop.py` `_heuristic_postflop_action` → `PokerBot/src/postflop.py` (same wholesale replace as A-T1; heuristic doesn't currently exist in main).

---

## B. Vladimir-specific exploits (defensive — no copying his sizing tree)

### 14 candidate ideas
1. Multiway equity discount in `_equity_turn_river_action` at `PokerBot-codex/src/postflop.py:355-365`: subtract `0.04 × max(0, mw−3)` from `equity` before the `pot_odds + margin` comparison; operationalizes `ext/public-bots/vladimir/bots/vlad/deep_cfr/MULTIWAY_IMPROVEMENTS.md:4-21`.
2. Multiway value-threshold lift in the `can_check` branch at `:347-352`: raise `value_threshold` from 0.36/0.42 (turn/river) to 0.48/0.54 when `mw ≥ 4`; suppresses thin value bets into his undertrained defenders.
3. 4-raise terminal: count current-street raise events from `action_log`; when `raise_count == 4` (vlad's tree cap at `ext/public-bots/vladimir/bots/vlad/deep_cfr_cpp/src/config.hpp:51-52`), forbid our own raise — call or fold only.
4. 5th-raise pressure exploit: when `raise_count ≥ 4` AND `_hand_strength_bin ≥ strong_pair`, apply `_raise_two_thirds_pot` at `PokerBot-codex/src/postflop.py:132` for one final pressure round; his net responds from a noisy out-of-distribution branch.
5. Off-grid sizing detector treated as range-uninformative: when `_bet_ratio_bucket(villain_bet, pot) ∈ {tiny, huge}` AND boundary is within ±0.05 of his 0.27p/1.72p anchors (`config.hpp:3-17`), use `villain_range=()` random in equity — he's bluffing or value-betting indistinguishably.
6. GTO-vs-MC seam exploit: in `_equity_turn_river_action`, when bucket ∈ {mid} AND `_board_wetness == False` AND `mw == 2`, prefer call over raise even when equity supports raise; his 60% GTO / 40% MC blend (`PokerBot-claude/consults/2026-05-27-overnight-P/vladimir_analysis.md:8-15`) value-bets thinly here.
7. Pre-river commit guard: when `_effective_spr ≤ 1.0` AND street ∈ {flop, turn}, downgrade raise to call — his MAX_DEPTH=200/MAX_RAISES=4 tree bound (`config.hpp:51-52`) means his commit-with-marginal is undertrained.
8. Recursive-aggression detector: derive `recent_raise_actor` from `action_log` last 3 actions; if the same villain has raised twice and we haven't, his net is in a deep recursion branch — fold marginal calls instead of float.
9. Multiway-flag input to `OpponentModel.archetype_features` at `PokerBot-codex/src/opponent_model.py:79-141`: append `mw_count` to `current_pressure` at `:189` and tilt posterior toward `risk_gated_conservative` when `mw ≥ 4` AND `top_archetype == blueprint_threshold_exploit`.
10. Bracket-context posterior weight: when `match_action_log` shows villain's raise rate has shifted >1.5σ from his first-50-hand baseline, posterior favors his "one-step MC" mode over "GTO" mode; thin patch in `_posterior_from_rates` at `PokerBot-codex/src/opponent_model.py:166-186`.
11. All-in skepticism vs vlad-class: when posterior peaks at `monte_carlo_basic` or `blueprint_threshold_exploit` AND villain's `current_bet ≥ 0.5 × stack`, demand `equity ≥ 0.65` for call inside `_equity_turn_river_action` at `:355-365`.
12. Wet-multiway dual-veto: combine A-T1 veto with B1 multiway tax — when `_board_wetness AND mw ≥ 3 AND vladimir-shaped posterior`, set veto `safety_cap_mbb` to 2× base (e.g., `large=360`, `huge=520`); compound effect against his most undertrained surface.
13. Posterior-driven postflop tighten (postflop-side only, since `src/preflop_lookup.py` is forbidden per `PokerBot/docs/playbooks/patch-window.md` Phase 4): plumb posterior to `decide_postflop` and when posterior peaks at high-aggression, demote our flop continuation to check/fold in the first 25% of the flop blueprint cells.
14. Detection-only-no-act variant: add `_bet_ratio_bucket` classifier logging (in-memory only) at `PokerBot-codex/src/postflop.py:128` without acting on it; ship after finals once we have hand-history data to validate cutoffs.

### Top 3 (impact × implementability × low-regression-risk)

#### B-T1 — Multiway equity tax + value-threshold lift in `_equity_turn_river_action` (#1 + #2)
- **Pitch.** Vladimir's own README at `ext/public-bots/vladimir/bots/vlad/deep_cfr/MULTIWAY_IMPROVEMENTS.md:4-21` admits his net is undertrained in 4+-way; a small equity tax + value-threshold lift in our single best postflop seam exploits that gap in ~12 LOC, no new module.
- **Sketch.** Inside `_equity_turn_river_action` at `PokerBot-codex/src/postflop.py:341-365`:
  - call branch (`:355-365`): replace `call_threshold = min(0.72, pot_odds + margin)` with `call_threshold = min(0.72, pot_odds + margin + 0.04 * max(0, _multiway_count − 3))`.
  - check branch (`:347-352`): replace `value_threshold = 0.36 if street == "turn" else 0.42` with `value_threshold = base + 0.12 * max(0, _multiway_count − 3)` where `base ∈ {0.36, 0.42}`.
  - both branches gated by the `_multiway_count` helper from A-T1.
- **Acceptance.** `python tools/h2h.py --bot-a submissions/v_final.zip --bot-b <candidate.zip> --paired-seed-base 142 --hands 20000 --label-a baseline --label-b b1` and `--paired-seed-base 242` against vladimir zip — gate is paired Δ mean > 0 with CI low > −20 across both seed bases (Phase B8 vladimir elevated gate); plus `python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42` to confirm no template regresses.
- **Risk.** In 6-max tables we routinely hit `mw = 5` or 6 multiway; tax accumulates non-linearly (0.04 × 3 = 0.12 added to `pot_odds`), and on the river could lift `call_threshold` past 0.65 in spots where calling is mathematically correct against the median field — mitigated by the existing `min(0.72, ...)` cap and the conservative 0.04 constant.
- **Stacking with A-T2.** If both A-T2 and B-T1 ship, the order is: (1) A-T2 computes `equity = min(equity_random, equity_tight)` FIRST; (2) B-T1 leaves equity untouched and instead inflates the `call_threshold` side of the comparison by the multiway tax. The two adjustments stack additively on opposite sides of `equity ≥ call_threshold`, not multiplicatively on equity itself — prevents the double-discount that would turn marginal calls into reflex folds at `mw=5` against a large-bucket bet.
- **Migration.** `PokerBot-codex/src/postflop.py` two-line tweaks inside `_equity_turn_river_action` + `_multiway_count` helper → `PokerBot/src/postflop.py`; piggybacks on the A-T1 migration since both target the same function.

#### B-T2 — 4-raise terminal + 5th-raise pressure exploit (#3 + #4)
- **Pitch.** Vlad's `MAX_RAISES_PER_STREET = 4` (`ext/public-bots/vladimir/bots/vlad/deep_cfr_cpp/src/config.hpp:51-52`); reading `action_log` to detect the boundary lets us avoid his clean blueprint reply (fold/call only) and exploit the 5th-raise out-of-distribution branch when we're strong.
- **Sketch.** Add `_current_street_raise_count(action_log, street)` near `PokerBot-codex/src/postflop.py:128`. Inside `_equity_turn_river_action` at `:333-365`, before the existing dispatch:
  - if `_current_street_raise_count == 4` AND `_hand_strength_bin ≥ strong_pair` AND `_effective_spr > 1.5`: return `_raise_two_thirds_pot(...)` (`:132`) regardless of equity (5th-raise pressure).
  - if `_current_street_raise_count == 4` AND `_hand_strength_bin < strong_pair`: `call` if `equity ≥ pot_odds`, else `fold` — never raise (4-raise terminal).
  - **Dispatch order inside `_equity_turn_river_action`:** B-T2's raise-count short-circuit fires BEFORE A-T1's equity-veto check. Rationale: raise-count is action-log-derived and cheap; A-T1's veto consumes equity which is the more expensive signal; B-T2's strong-hand 5th-raise pressure must not be overridden by A-T1's weak-hand veto (different branches by `_hand_strength_bin` anyway, but ordering is documented to lock the patch shape).
- **Acceptance.** Add `tests/edge_cases/test_vlad_tree_cap.py` synthesizing an `action_log` with 4 raise events on the current street, asserting our action is never `raise` with `made ≤ weak_pair` and IS `raise` with `made ≥ strong_pair`; `pytest tests/edge_cases -x`; then h2h as in B-T1.
- **Risk.** Vlad isn't the only opponent capping his tree at 4; aggressor and other reference bots may legitimately raise 5+ times when stacks remain, and forcing call/fold gives them a +EV continuation — mitigated by also gating on `_effective_spr > 1.5` and the `_hand_strength_bin` split.
- **Migration.** `PokerBot-codex/src/postflop.py` `_current_street_raise_count` helper + dispatch block inside `_equity_turn_river_action` → `PokerBot/src/postflop.py`.

#### B-T3 — GTO-vs-MC seam: mid-bucket dry-board passive preference (#6)
- **Pitch.** Vlad's 60/40 GTO+MC blend is most fragile on the dry-board mid-bucket spot where GTO wants to bluff and MC wants to value-bet thin; calling rather than raising harvests his MC mode without bloating the pot when he's GTO-bluffing.
- **Sketch.** Inside `_equity_turn_river_action` at `PokerBot-codex/src/postflop.py:355-365`, when `_bet_ratio_bucket(current_bet, pot) == "mid"` AND `_board_wetness == False` AND `_multiway_count == 2` AND `equity ∈ [pot_odds + margin, pot_odds + margin + 0.15]`: return `{"action":"call"}` even if the surrounding logic would raise. Equity window keeps us from downgrading clear value raises.
- **Acceptance.** `python tools/h2h.py --bot-a submissions/v_final.zip --bot-b <candidate.zip> --paired-seed-base 142 --hands 20000 --label-a baseline --label-b b3` against vladimir; confirm no LBR regression via `python tools/exploit_check.py --bot <candidate.zip> --max-preflop-mbb 100 --max-aggregate-mbb 200` (mid-bucket spots like `flop_small_pair_call` should not flip behavior).
- **Risk.** "Always call mid-bucket dry-board heads-up with marginal equity" is a documented LBR-exploit pattern by sharp 3-bet defenders (lane-A1 sharp_3bet_punisher archetype was −3.36 bb/100); the narrow `equity ∈ [pot_odds+margin, +0.15]` window scopes this tightly enough that the 20-spot LBR suite should still pass, but this is the riskiest of the three — ship only if A-T1 + B-T1 + B-T2 have cleared the gauntlet.
- **Migration.** `PokerBot-codex/src/postflop.py` 6-line branch inside `_equity_turn_river_action` → `PokerBot/src/postflop.py`.

---

## C. Finals-bracket overlays (intra-match phase + stack-ratio only; no bracket-round signal)

### 15 candidate ideas
1. Postflop posterior plumbing seam: extend `decide_postflop(game_state, posterior=None)` at `PokerBot-codex/src/postflop.py:366`, and at the call site `PokerBot-codex/src/bot.py:104-110` derive `features = _OPPONENT_MODEL.archetype_features(state)` then pass `posterior=features`; structural prerequisite for every other overlay below.
2. Narrower bracket-context deviation: in `PokerBot-codex/src/opponent_model.py:99` set `deviation_bound = MAX_DEVIATION_BOUND_PP * confidence * 0.7` when `top_probability ≥ 0.55`; respects `PokerBot/docs/finals-strategy-2026-05-27.md:64-82` (sharper field → narrower overlay).
3. Hand-index-aware overlay weight: derive `hand_in_match = max(item["hand_num"] for item in match_action_log)` per `ext/public-bots/vladimir/sandbox/match.py:219-222` inside `PokerBot-codex/src/opponent_model.py:_observed_actions`, scale `deviation_bound` by 0.6 in `hand_in_match < 30`, 1.0 in `30..300`, 0.7 in `> 300`.
4. Stack-pressure scaling: in `_pressure_preflop_overlay` at `PokerBot-codex/src/bot.py:149-152, 176-223`, if `your_stack > 2 × STARTING_STACK` OR `< 0.5 × STARTING_STACK`, scale `deviation_bound` by 0.5 — both extremes argue for blueprint-truer play.
5. `finals_priors.npz` consumer in `PokerBot-codex/src/opponent_model.py` at module top, mirroring the `np.load` pattern at `PokerBot-codex/src/postflop.py:28-59`: load `data/finals_priors.npz` with `try/except` no-op fallback, expose `_FINALS_PRIORS` dict; covers the Phase B3 P0.
6. Field-VPIP-driven cap: if `_FINALS_PRIORS['vpip'] < 0.22`, set runtime deviation cap to `2.0`; if `> 0.30`, raise to `3.0` (capped at `MAX_DEVIATION_BOUND_PP=4.0`); read-only modulation in `_posterior_from_rates` at `PokerBot-codex/src/opponent_model.py:166-186`.
7. Field-fold-to-cbet-driven safety cap: if `_FINALS_PRIORS['fold_to_cbet'] > 0.55`, raise the A-T1 `safety_cap_mbb[bucket]` by 30% (their over-folds make our veto cheaper); modulation in `PokerBot-codex/src/postflop.py:128+`.
8. Adaptive top-archetype tie-break: in `_top_posterior` at `PokerBot-codex/src/opponent_model.py:117-126`, when `top_probability < 0.30` (no clear archetype), set `deviation_bound = 0` regardless of confidence; matches sharper-field-narrower-overlay.
9. Sample-size floor escalation: introduce `FINALS_MIN_OBSERVATIONS = 60` at `PokerBot-codex/src/opponent_model.py:23-25`, consumed only when `_FINALS_PRIORS` is loaded; default `MIN_ARCHETYPE_OBSERVATIONS=20` stays to preserve qualifier behavior.
10. Variance-cap on committed-chip ratio: in `decide_postflop` (newly threaded with posterior per #1), if `your_bet_this_street / max(1, your_stack + your_bet_this_street) > 0.30` AND we're not facing all-in, downgrade `raise` → `call`; tighter variance for bracket survival.
11. Posterior-bounded veto strength in A-T1: scale A-T1's `safety_cap_mbb[bucket]` by `(1.0 + 0.3 × (top_probability − 0.5))` when `top_archetype == risk_gated_conservative`; expensive vetos when posterior says villain rarely commits.
12. Multiway-fold-suppression: at `_pressure_preflop_overlay` (`PokerBot-codex/src/bot.py:149-152`), when `len(players) ≥ 4` AND `top_archetype != blueprint_threshold_exploit`, scale `open_shift_pp` by 0.5; reduces overlay-induced opens against unknown bracket fields.
13. Aggression-burst auto-narrow: derive `recent_raises = sum(1 for a in match_action_log[-20:] if a.get("action") == "raise")`; if `≥ 6`, set `deviation_bound = min(deviation_bound, 2.0)`.
14. Bracket-quiet overlay floor: at `PokerBot-codex/src/bot.py:181` (existing `< 0.75` micro-shift skip), raise the floor to `1.20` when `_FINALS_PRIORS` is loaded; suppresses micro-shifts that look like reads.
15. Variance-seeking when-behind (steelman counter to #2/#4): when `your_stack < 0.4 × STARTING_STACK` AND `hand_in_match > 250`, **widen** `deviation_bound` by `1.25` and bias toward `aggressive` archetype overrides; single-elim variance argument — we need a coin-flip more than we need Nash.

### Top 3 (impact × implementability × low-regression-risk)

#### C-T1 — Narrower bracket-context deviation bound (#2 + #4)
- **Pitch.** Highest-leverage finals overlay with the lowest blast radius: a two-axis scale (posterior confidence × stack ratio) tightens our overlay where the bracket field is sharpest, with one constant edit and one helper across `opponent_model.py` + `bot.py`.
- **Sketch.** In `PokerBot-codex/src/opponent_model.py:99`:
  ```
  deviation_bound = MAX_DEVIATION_BOUND_PP * confidence
  if top_probability >= 0.55:
      deviation_bound *= 0.7
  ```
  In `PokerBot-codex/src/bot.py:_pressure_preflop_overlay` at `:149-152`, add:
  ```
  stack_ratio = your_stack / STARTING_STACK
  if stack_ratio > 2.0 or stack_ratio < 0.5:
      features = dict(features)
      features["deviation_bound"] *= 0.5
  ```
  (`STARTING_STACK = 10000` per engine convention.)
- **Acceptance.** `pytest tests/edge_cases/test_overlay_bounded.py -x` must still pass (existing `test_posterior_deviation_is_hard_bounded_for_each_peak` invariant still holds because we scale down, not up); plus `python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42` showing no template regresses, and a new `tests/edge_cases/test_finals_overlay_narrower.py` asserting `top_probability=0.60` + `stack_ratio=2.5` ⇒ final `deviation_bound ≤ MAX_DEVIATION_BOUND_PP × 0.7 × 0.5 = 1.4`.
- **Risk.** Narrower overlay against weak qualifier-tier opponents who appear in the bracket leaves EV on the table — but bracket field is sharper by selection (`PokerBot/docs/finals-strategy-2026-05-27.md:64-82`), so asymmetric risk favors narrower; mitigated by keeping the `MAX_DEVIATION_BOUND_PP=4.0` ceiling intact, so we strictly subset qualifier behavior, never extend it. Note: #15 (variance-seeking when behind) is the explicit steelman counter — it lost the triage because the bracket-round signal that would make it precise is unavailable (we can only see hand-in-match, not bracket-round depth), so widening on shaky inputs invites LBR exploit.
- **Migration.** `PokerBot-codex/src/opponent_model.py` 1 conditional + `PokerBot-codex/src/bot.py` 3-line stack-ratio block → `PokerBot/src/opponent_model.py` + `PokerBot/src/bot.py`; main worktree on `release/v_final-e4b4a8f1` has both files at post-X1 state, so this is a small patch-style migration.

#### C-T2 — Postflop posterior plumbing seam (#1)
- **Pitch.** Without this seam, A-T1's posterior-aware `safety_cap_mbb` scaling (folded-in idea #11) is structurally unable to read the posterior; landing the plumbing once is a small structural enabler that converts the bot from preflop-only overlay to unified posterior-aware policy without rewriting strategy logic. **In-plan consumer:** A-T1's veto-block clause that scales `safety_cap_mbb` by `(1.0 + 0.3 × (top_probability − 0.5))` when `top_archetype == "risk_gated_conservative"` AND `top_probability ≥ 0.55`. If C-T2 ships separately or after A-T1, that clause is gated by `if _LAST_POSTERIOR is not None` and becomes a no-op until C-T2 lands.
- **Sketch.** Change `decide_postflop(game_state: dict) -> dict` to `decide_postflop(game_state: dict, posterior: dict | None = None) -> dict` at `PokerBot-codex/src/postflop.py:366`; at the call site `PokerBot-codex/src/bot.py:104-110`, change:
  ```
  if street in ("flop","turn","river"):
      return _decide_postflop(game_state)
  ```
  to:
  ```
  if street in ("flop","turn","river"):
      features = _OPPONENT_MODEL.archetype_features(game_state)
      return _decide_postflop(game_state, posterior=features)
  ```
  Internal callees keep their signatures unchanged for this patch — `posterior` is stored as module-level `_LAST_POSTERIOR` and read by subsequent ideas; this avoids touching the dispatch order at `PokerBot-codex/src/postflop.py:368,372,376,380`.
- **Acceptance.** `pytest tests/edge_cases -x` — `test_postflop_wiring.py`, `test_equity_wiring.py`, `test_lbr_spot_corrections.py` must not regress (new `posterior=None` default preserves prior behavior); add `tests/edge_cases/test_posterior_seam.py` asserting `_LAST_POSTERIOR` is populated after `bot.decide(state_with_street='flop')`.
- **Risk.** Module-level `_LAST_POSTERIOR` introduces hidden state across calls in a stateless-by-convention bot; mitigated by clearing `_LAST_POSTERIOR = None` at the top of `_decide_postflop` if `posterior is None`, so any single-call test sees deterministic behavior, and the engine's warmup-then-live model means hidden state never persists across hands maliciously.
- **Migration.** `PokerBot-codex/src/postflop.py` signature change + `_LAST_POSTERIOR` module var + `PokerBot-codex/src/bot.py` call-site change at `:104-110` → `PokerBot/src/postflop.py` + `PokerBot/src/bot.py`; pairs naturally with A-T1 migration since both touch `postflop.py`.

#### C-T3 — `finals_priors.npz` consumer modulating deviation bound + safety cap (#5 + #6 + #7)
- **Pitch.** This IS the Phase B3 P0 item from `PokerBot/docs/plans/qualifier-finals-rollout-2026-05-27.md:B3` and is the only finals overlay that reads the actual patch-window producer output; without it, the entire `PokerBot-claude/tools/analyze_hand_histories.py` pipeline is dead code at runtime.
- **Sketch.** At top of `PokerBot-codex/src/opponent_model.py` (next to existing imports), mirror the load pattern at `PokerBot-codex/src/postflop.py:28-59`:
  ```
  _FINALS_PRIORS = None
  try:
      import numpy as np
      _priors_path = _DATA_DIR / "finals_priors.npz"
      if _priors_path.exists():
          with np.load(_priors_path, allow_pickle=False) as data:
              _FINALS_PRIORS = {k: data[k].item() if data[k].ndim == 0 else data[k] for k in data.files}
  except Exception:
      _FINALS_PRIORS = None
  ```
  Then in `_posterior_from_rates` at `:166-186`, after computing `posterior`, modulate `deviation_bound`:
  ```
  if _FINALS_PRIORS is not None:
      vpip = float(_FINALS_PRIORS.get("vpip", 0.25))
      if vpip < 0.22: cap = 2.0
      elif vpip > 0.30: cap = 3.0
      else: cap = MAX_DEVIATION_BOUND_PP
      deviation_bound = min(deviation_bound, cap)
  ```
  And in A-T1's `safety_cap_mbb` lookup in `PokerBot-codex/src/postflop.py`, scale by `1.3` when `_FINALS_PRIORS['fold_to_cbet'] > 0.55`.
- **Acceptance.** `python tools/import_audit.py --max-seconds 1.5 --max-mb 400` to confirm priors load is under budget per `PokerBot/docs/playbooks/patch-window.md` Phase 6; `pytest tests/edge_cases -x` (specifically `test_overlay_bounded.py` and `test_archetype_posterior.py` must pass with and without `data/finals_priors.npz` present); add `tests/edge_cases/test_finals_priors_loader.py` synthesizing a stub `finals_priors.npz` with `vpip=0.18` and asserting `deviation_bound ≤ 2.0`; `python tools/audit_strategy_leakage.py --zip submissions/v_final.zip` must still pass.
- **Risk.** A malformed `data/finals_priors.npz` (wrong keys, NaN, wrong dtype) could load successfully but inject nonsense into the cap — the `try/except` swallows it; mitigated by Phase 3 sanity gate in `PokerBot/docs/playbooks/patch-window.md` (VPIP must be in 18–40%, otherwise Phase 2.5 fallback fires); also `min(deviation_bound, cap)` semantics mean a corrupt `vpip` field can only narrow, never widen.
- **Migration.** `PokerBot-codex/src/opponent_model.py` (loader block + modulation in `_posterior_from_rates`) → `PokerBot/src/opponent_model.py`; safety-cap scaling lives inside A-T1's veto block so it migrates with A-T1; `data/finals_priors.npz` itself is produced by `PokerBot-claude/tools/analyze_hand_histories.py` and copied to `PokerBot/data/` during Phase 3 of the patch window.

---

## D. Wildcards

#### D1 — Famadeo public-belief mirror as a unified pressure signal
- **Pitch.** Stand up a tiny `src/public_belief.py` exposing `extract_public_belief(state) -> {multiway_count, recent_raise_depth, pot_to_stack_ratio, range_narrowing_estimate}`, consumed by BOTH `_pressure_preflop_overlay` and the A-T1 veto; collapses three open-coded pressure derivations into one source-of-truth and makes future overlays additive.
- **Sketch.** New file `PokerBot-codex/src/public_belief.py` with 4 pure functions reading only `game_state` (no module state); called from `PokerBot-codex/src/bot.py:_pressure_preflop_overlay` at `:149-152` and from A-T1's veto block; replaces ad-hoc `len(players)`, `_current_pressure` (`PokerBot-codex/src/opponent_model.py:228-240`), and per-call multiway counts.
- **Acceptance.** `python tools/benchmark.py --all-templates --hands 10000 --paired-seed-base 42`; `python tools/h2h.py --bot-a submissions/v_final.zip --bot-b <candidate.zip> --paired-seed-base 142 --hands 20000` against famadeo and vladimir; gate is no template regression AND vladimir paired Δ CI low > −20.
- **Risk.** Patch-window playbook at `PokerBot/docs/playbooks/patch-window.md` Phase 4 explicitly forbids `src/bot.py` edits during the patch window; this idea must land BEFORE the patch window (i.e., as part of the PATCH-2A artifact built on 2026-06-02 outside the playbook flow) or it is disqualified — high coordination cost, and the abstraction overhead may not pay back inside the 90–130 LOC budget.

#### D2 — Lightweight equity-oracle lookup at warmup
- **Pitch.** Pre-compute a ~200-state equity table covering common board+hand-class signatures, ship as `data/equity_corner_cases.npz` (~50 KB), consult at decide-time as a fast-path before the live 160-trial MC; trims 0.8–1.2 ms median per decision for the hottest spots.
- **Sketch.** New offline tool `PokerBot-codex/tools/build_equity_oracle.py` enumerates `(made_class, multiway, board_texture_bucket) → equity` via repeated `equity_vs_range` calls with `trials=5000`, writes `data/equity_corner_cases.npz`; loaded at module import in `PokerBot-codex/src/postflop.py` via the existing `_DATA_DIR` pattern at `:21-27`; `_equity_for_state` at `:309-330` checks the table first, falls through to live equity if no match.
- **Acceptance.** `python tools/import_audit.py --max-seconds 1.5 --max-mb 400` (cold-start budget per `PokerBot/docs/playbooks/patch-window.md` Phase 6); `python tools/smoke_run.py --hands 200` for live latency; `pytest tests/edge_cases/test_equity_wiring.py -x` so `test_equity_cache_hit_on_repeat_call_within_same_hand` continues working.
- **Risk.** Coarse approximation; mismatch between oracle equity and live equity creates a silent strategy drift hard to debug, and rebuilding requires keeping the offline tool in sync with future equity changes — fixes a non-bottleneck (we're not equity-budget-constrained at 160 trials × ~1 ms) at the cost of new failure modes.

#### D3 — In-process LBR-style self-monitor that tightens veto on the fly
- **Pitch.** Maintain a module-level rolling estimate of our own decision exploitability (1-step LBR proxy from recent decision EVs); if the estimate exceeds a threshold, automatically tighten A-T1's `safety_cap_mbb` for the next N decisions — continuous self-defense without any opponent identification.
- **Sketch.** New helper `_decision_lbr_tick(state, action, equity)` in `PokerBot-codex/src/postflop.py:128+` writes to a `collections.deque(maxlen=64)` of decision-EV deltas; `_lbr_signal` returns mean delta; when `< −20 mbb/g`, multiply A-T1 `safety_cap_mbb` by 1.5 for the next 16 decisions (counter-decrements); zero file writes, zero threading.
- **Risk.** Module-level mutable state across `decide()` calls is the strongest red flag in the sandbox model — bots are assumed deterministic per state per `PokerBot/docs/tournament-spec.md`; a corrupted deque could pessimize ALL subsequent decisions, and the LBR proxy from in-process EV deltas is a weak signal (Lisý & Bowling 2017 LBR is multi-step and against a best-response opponent, not against our own samples).

---

**If I had to pick ONE patch to ship beyond PATCH-2A, it would be B-T1 (multiway equity tax + value-threshold lift)** because it operationalizes a weakness vladimir documents in his own repo (`MULTIWAY_IMPROVEMENTS.md:4-21`) inside the same function PATCH-2A already opens, in ~12 LOC, against the highest-skill threat in the public field, with no new modules and no `src/bot.py` edits — it slots into the same migration that A-T1 already pays for.

## Open Questions
- **Ordering: should C-T2 (posterior plumbing) land BEFORE A-T1, alongside it, or after?** Recommended default: bundle C-T2 with A-T1 in a single patch so A-T1's posterior-aware `safety_cap_mbb` scaling clause is live on day one; the `if _LAST_POSTERIOR is not None` guard means C-T2 can also ship later as a v2 without breaking A-T1. Confirm at patch-window kickoff.
- **Will `data/finals_priors.npz` be valid at A-T1 build time?** The Phase 3 sanity gate fires if VPIP ∉ [18%, 40%]. If priors are invalid/absent on 2026-06-02 morning, C-T3 silently no-ops via `try/except` — making its `safety_cap_mbb *= 1.3` clause dead. Decide whether C-T3 ships bundled with A-T1 (cheap, single migration) or as a separate PR landing after Phase 3 confirms valid priors (safer, but two builds).
- **Is A-T1's helper bundle atomic, or splittable?** B-T1 / B-T2 / A-T3 piggyback on `_bet_ratio_bucket`, `_multiway_count`, `_effective_spr`, `_board_wetness`, `_hand_strength_bin` reuse, `_passive_ev`, `_bet_ev`. If A-T1 review stalls, three downstream items stall with it — worth landing helpers as a shared-infra PR first.
- **Does `_LAST_POSTERIOR` module-level state pass the validator AST scan and the leakage audit?** Not on `FORBIDDEN_MODULES` or `FORBIDDEN_PATTERNS`, but the bot is documented stateless in `PokerBot/docs/tournament-spec.md`. Spot-check via `python tools/audit_strategy_leakage.py --zip <candidate.zip>` before C-T2 lands.
- **Equity budget contention:** `_EQUITY_CALL_BUDGET_S=0.20` is shared between existing equity path and any veto-side equity. A-T2 proposes the 80+80 trial split with deadline halving; alternative is doubling the budget to 0.40s — decide when measuring veto-side MC variance on the codex venv.
- **Main-worktree migration target:** Does the `release/v_final-e4b4a8f1` branch in `PokerBot/` already carry the post-X1 `opponent_model.py` + `bot.py` state that C-T1 / C-T2 migration assumes? Verify before patch-window kickoff; if not, migration is a wholesale-replace rather than a patch.

## References
- `PokerBot/docs/plans/qualifier-finals-rollout-2026-05-27.md` (Phase B sections B3/B4/B7/B8, Phase D shadow lane).
- `PokerBot/docs/finals-strategy-2026-05-27.md` (sharper-field-narrower-overlay argument, finals artifact-swap criteria).
- `PokerBot/docs/playbooks/patch-window.md` (postflop-only scope, Phase 4 constraints).
- `PokerBot/KANBAN.md` (action-abstraction prohibitions).
- `ext/fullhouse-engine/sandbox/{validator.py,Dockerfile,runner.py}` (sandbox invariants, forbidden modules/calls).
- `ext/public-bots/famadeo/bots/codex_holdem/bot.py:650-759, 2140-2259` (veto pattern reference).
- `ext/public-bots/vladimir/bots/vlad/{CFR_PLAN.md, deep_cfr/MULTIWAY_IMPROVEMENTS.md, deep_cfr_cpp/src/config.hpp}` (vladimir design + known weaknesses).
- `PokerBot-claude/consults/2026-05-27-overnight-P/vladimir_analysis.md` (our own lane-P findings).
