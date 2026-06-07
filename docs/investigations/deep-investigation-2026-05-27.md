# Investigation: Deep meta-review (2026-05-27)

## Summary
Multi-thread investigation triggered by user: dberweger DeepCFR comparison, vladimir win durability, tournament leaderboard, off-grid sizing decision, engine-bot provenance, synthetic finals field rationale, kanban refresh, DeepCFR portability, corpus completeness, confidence-interval honesty audit, and the 9h-overnight-actually-ran-1h diagnostic.

## Symptoms
- Lane B vladimir result shows +55.30 bb/100 over only 1085 hands with CI crossing zero — calling this a "win" overstates the evidence.
- Overnight queue completed in 70 min when wall cap was 9h — 7.8 h of compute unused.
- Public claim from dberweger2017 ("beats pro poker players") needs auditing against our actual bench.
- We have 200 MB data envelope but ship a 28 KB artifact — heuristic blueprint, no neural net.
- Lane T showed we lose to every synthetic finals variant; finals readiness is unclear.
- KANBAN.md is stale; many overnight lanes done but not checked off.

## Hypotheses to test
1. **(H1)** We are not "comfortably" beating vladimir — the 1085-hand sample is too small.
2. **(H2)** dberweger's bot is strictly stronger than vladimir's, and possibly stronger than ours.
3. **(H3)** dberweger's pre-trained weights are not portable into our sandbox (PyTorch + ONNX, not numpy-only).
4. **(H4)** The 9h queue completed in 1h because per-lane prompts were narrow + parallelizable; no second-wave plan triggered when first wave finished.
5. **(H5)** Lane E's top-64 probability is anchored on field=128 which is an unsupported guess; the real ranking confidence is wider than reported.
6. **(H6)** Our corpus covers the core papers; a dedicated /research run would add specific value (ICM, recent Deep CFR public weights, multiway-aware equity).
7. **(H7)** The three Lane O counter-plays are portable inside the remaining wall-clock; off-grid sizing is the one we should NOT adopt (per finals-strategy doc §4.4).

## Background / Prior Research

### Explore A — dberweger2017 DeepCFR repo + Medium article

- **Architecture (current repo, supersedes Medium):** input_dim=156, hidden=256, 3 hidden ReLU layers, action head (3 outputs: fold / check-call / raise), continuous sizing head (0.1x–3.0x pot). ~205,572 params per net; advantage + strategy nets ~411,144 params total.
- **Older Medium architecture (deprecated by README):** input=500, hidden=256, 5 hidden layers, 4 actions, ~392,452 params per net.
- **Framework:** PyTorch (`torch==2.5.1`); training uses Adam + TensorBoard + optional CUDA.
- **Runtime:** **PyTorch required at inference.** `choose_action()` builds tensor, runs `strategy_net`, softmaxes, samples. `load_model()` uses `torch.load()`. **No NumPy export exists.** Direct sandbox port is blocked — PyTorch is not in our allowed library set.
- **Weights:** `.pt` format, 2.46 MB and 2.56 MB. License: MIT.
- **Training:** staged (random opponents → self-play → mixed vs checkpoint pool), up to 20000 iters × 400 traversals. No wall-clock / hardware / reproducibility info.
- **Performance claim:** 15–17 chips/game vs **random**, 20+ chips/game vs **random** after mixed training, beats own checkpoint pool. Evidence is **screenshots only**. No LBR, no exploitability, no ACPC-style CIs, no human paired-seed match, no Pluribus comparison. Author's "beats pro poker players" claim is anecdotal, not benchmarked.
- **Action abstraction:** 3 discrete types + continuous size. NOT the Pluribus 5-discrete tree, NOT Vladimir's 9-action discrete tree.
- **Compared to Vladimir:** Vladimir's bot is RICHER (274→512×4→9, ~933k params), MORE PORTABLE (numpy `.npz`, no PyTorch at runtime), better characterized (Monte Carlo blend + GTO prior). **dberweger is likely weaker as a Fullhouse submission than Vladimir, and is not directly shippable.**
- **Verdict:** borrow training-methodology ideas only. Do not port; do not ship weights.

### Explore B — Pre-trained 6-max NLHE weights landscape (May 2026)

- **Pluribus weights:** never released (intentional, to prevent online-poker misuse).
- **DeepStack official:** HU only, no production weights, neural-CFV requires PyTorch.
- **DeeperStack / PyStack:** Lua/Torch7 or TF1, HU only.
- **OpenSpiel / RLCard:** algorithms only — only pretrained checkpoint is Leduc CFR, not 6-max NLHE.
- **DecisionHoldem:** AGPL-3.0, HU, C++/pthread/`.so` — not shippable.
- **RoboPoker:** Rust MCCFR, abstractions 32 MB (flop) → 347 MB (turn) → 3 GB (river) — exceeds 200 MB data envelope beyond flop.
- **Slumbot 2019:** code only, no weights, HU lineage.
- **dberweger:** PyTorch-bound; small weights but no NumPy export.
- **MIT-licensed compact 6-max preflop charts (Tyloo):** ~22 KB total, manually transcribable, but heuristic — not solver-grade.
- **Verdict: NO drop-in solver-derived 6-max blueprint is shippable.** The only realistic external assets are heuristic preflop charts (already covered by our charted ranges).

### Explore C — Public-bots' scores against engine reference bots

- **No documented public-repo benchmark beats our numbers.** All four public repos (vladimir/dominic/famadeo/neel) ship benchmark harnesses but no saved score reports.
- **Vladimir's `.streak/BUST_ANALYSIS.json`** records a bad run: vlad 0 wins, aggressor 60000 chips — evidence Vladimir loses to aggressor.
- **All engine reference bots are byte-identical** (SHA-256 confirmed) between `ext/fullhouse-engine/bots/` and every public repo's copy. Confirmed source: Fullhouse-provided, not invented by any public repo.
- **Strategy commentary:**
  - vladimir: Deep CFR/GTO net + Monte Carlo fallback (`bots/vlad/CFR_PLAN.md`).
  - dominic: Blueprint + heuristic exploit overlay (`bots/dominic/bot.py:1`); benchmark harness omits ref_bot_2.
  - famadeo: Explicitly NOT ReBeL runtime; public-state heuristics + coarse range inference (`docs/rebel_public_belief_plan.md`).
  - neel: Fast heuristic baseline — preflop table + MC postflop + pot odds.
- **Verdict:** We have NO public evidence ranking us anywhere in the field. We assume we're competitive based on our own internal numbers, which is reasonable given our internal benchmarks, but we cannot claim measured superiority.

### Explore D — Corpus completeness audit

- **All 7 notes exist on disk, all 4–6 KB.** Shallow summaries, not deep research notes.
- **Coverage strongest:** CFR/MCCFR/Pluribus framing.
- **Coverage gaps (relevant to our work):**
  - **LBR (Lisý & Bowling 2017, arXiv:1612.07547)** — only inline references; no dedicated note despite `tools/exploit_check.py` depending on the concept.
  - **ICM / bracket survival** — completely missing; ~~relevant for single-elim finals payout asymmetry~~ **OBSOLETE for finals Phase 1 after the 2026-06-04 format correction**. Correct source of truth: `AGENTS.md` "Finals FORMAT" + 17:32 consult (`prompt-exports/2026-06-04-173203-plan-optimise-next-90min-finals-bot.md`:9,14): Phase 1 is Swiss/cumulative with shrinkage; ICM/bracket-survival only remains relevant, if at all, to the Phase 2 final table.
  - **Bayesian opponent modeling** (Billings/Davidson/Schauenberg, Bayes' Bluff arXiv:1207.1411) — planned but explicitly dropped from corpus.
  - **Public-belief / range-conditioned equity (DeepStack continual resolving)** — missing; directly relevant to the famadeo technique we want to port.
  - **Recent Deep CFR variants** (HDCFR, SD-CFR, knowledge-distillation Deep CFR, 2025/2026 discounted/predictive neural CFR).
  - **Action-abstraction theory beyond Pluribus** (sliding-window / automated action abstraction).
- **Verdict: a focused /research run TONIGHT is worth doing, scoped to 4–5 narrow topics.** Top priorities by tournament-impact: (1) LBR, (2) Bayesian opp modeling for the 06-02 hand-history patch, (3) public-belief / range-conditioned equity, (4) action abstraction theory, (5) ICM.

## Investigator Findings

(Oracle synthesis — `untitled-chat-E35149`, captured 2026-05-27.)

### 1. DeepCFR ship/skip — STATUS QUO WINS
- Vladimir's `gto_strategy.npz` (3.56 MiB, NumPy-only runtime, MIT): shippable in principle. **Skip in practice** — useless without his 274-feature extractor + 9-action abstraction. Adopting it = shipping his bot wholesale on 5 days. His Lane B win against us was INDETERMINATE (CI crosses 0). No.
- dberweger's weights: PyTorch at runtime. Validator rejects. Trained vs random opponents; "beats pros" is screenshot evidence. Hard skip on capability, not licensing.
- **Default: status quo + fix POKERBOT_DISABLE_OVERLAY at `src/bot.py:39`.**

### 2. Confidence interval audit — Lane E's 99.94% is fiction
- Three unmeasured load-bearing assumptions: entrant count (Lane E used 128, real range 100–300), Swiss rounds (assumed 10, range 6–12), edge vs median entrant (sampled from 9 selection-biased data points).
- **P(top 64) realistic range: 40% (pessimistic: 250 entrants, edge ≈ 0) to 90% (optimistic: 128 entrants, edge ≈ +20).** Refuse to give a point estimate — that's the mistake Lane E made.
- **P(win finals) realistic: 1–15%.** ~~Upper bound 5–15% at +5 bb/100 edge per bracket match; lower bound <1% if Lane T's −135 vs v5 reproduces against a real entrant.~~ **HISTORICAL / OBSOLETE bracket model.** Do not reuse this as a live finals estimate after the 2026-06-04 correction; finals Phase 1 is Swiss/cumulative with shrinkage, not six single-elim matches (source: `AGENTS.md` "Finals FORMAT" + 17:32 consult `prompt-exports/2026-06-04-173203-plan-optimise-next-90min-finals-bot.md`:9,14).

### 3. Light-3-bet prevalence
- ~~P(≥1 bracket opponent 3-bets competently) ≈ **95%** — basic poker hygiene.~~ **HISTORICAL / OBSOLETE bracket model.** Reframe as finalist-field exposure risk under Swiss/cumulative tables; no six-match bracket probability should be treated as live.
- ~~P(facing a v5-class ADVERSARIAL light-3-bettor) ≈ **25–40%** across 6 bracket matches — not 88%.~~ **HISTORICAL / OBSOLETE bracket model.** Corrected format requires Phase 1 exposure estimates over ~40 Swiss-paired 6-max matches, not six single-elim bracket matches.
- Distinguish "competent 3-bet" (we may handle) from "adversarial 12% BB defense" (Lane T's hole).

### 4. Cheapest material finals-EV move — CONFIRM BEFORE PATCHING
- v5 was unreplicated, 1306 hands, CI half-width ~70 — actual loss could be −50 or −200.
- **Step 1 (1.5h, 0 LOC):** Paired-seed re-run of v5 vs v_final, 50 seeds × 400 hands × 2 orientations.
- **Step 2 (2h, ~15 LOC + 3 tests, only if CI confirms loss > 50 bb/100):** Single exact-match `_RESPONSE_PATCHES` entry in `src/preflop_lookup.py` keyed on `(position='big_blind', voluntary_seq=('raise',), stack_depth_bb>80)`. Avoid over-fit to v5's specific sizing.
- **Step 3 (1h):** Regression bench `--six-max-mix` + LBR.
- **Total: ~5h. Biggest risk: exact-match key over-fits to v5; mitigated by keying on context not amount.**

### 5. Overnight queue redesign — adaptive depth + chained continuations
Root cause: lanes narrow + parallel + independent; finished 40–70 min; no second wave; 3-non-improver kill fired too early.
- **Phase 1 (0–2h):** discovery — current 22-lane fan-out.
- **Phase 2 (2–6h):** chained refinement — each result triggers a follow-up. Lane A leader → Lane A′ runs 5× more seeds on top 3. Lane B RED matchup → Lane B′ runs 10k more hands. Lane T −135 → Lane T′ paired-seed confirm.
- **Phase 3 (6–9h):** commitment — long paired-seed validation of Phase-2 winners.
- **Mechanical fixes:** replace 3-non-improver kill with "stop at 50% wall budget OR 5 non-improvers". Add a watchdog that auto-launches deeper variants if >2h remain and no lanes running. Lanes start short (2k hands), extend if signal, not start long and kill early.

### 6. Localhost leaderboard — <2h, stdlib only
- 3 files: `tools/leaderboard.py` (orchestrator ~100 LOC), `tools/leaderboard_render.py` (stdlib `string.Template` → HTML ~80 LOC), output `tools/leaderboard.html`.
- 18 opponents: 5 engine + 4 public + 5 synthetic finals + 4 prior snapshots.
- Per-pair: `tools.h2h.run_match --paired-seed-base 42 --paired-seed-count 10 --hands 400`. ~30s × 18 = 9 min compute, ~18 min with retries.
- Reuse `_bootstrap_ci` from `tools/benchmark.py`. Emit JSON, then vanilla `<table>` with `data-sort` attribute on each header. Per-cell match count + CI width visible.
- **Critical UX:** Lane B-vladimir's 1085-hand sample should look obviously thin next to 50k-hand engine numbers. Display hands-played and CI width prominently.

## Investigation Log

### Phase 1 — Initial triage
**Hypothesis:** All 10 sub-questions are answerable via a fan-out of 4–5 parallel explore agents + 1 pair investigator + 1 oracle synthesis pass.
**Findings:** TBD
**Evidence:** TBD
**Conclusion:** TBD

## Root Cause

There is no single root cause — this is a multi-thread synthesis. The dominant theme: **internal confidence has outpaced external evidence**. Lane E reported P(top 64)=99.94 % from a model anchored on unverified field-size + unverified Swiss-rounds + a 9-data-point edge sample. Lane B vladimir +55.30 was reported as a "win" but is an INDETERMINATE 1085-hand sample. The 9h overnight ran 1h not because of failure but because the queue had no Phase 2 / Phase 3.

The single rule-relevant finding: `src/bot.py:39` reads `POKERBOT_DISABLE_OVERLAY`. Validator does NOT flag this (env-var reads are not on the forbidden-call list). Our INTERNAL `tools/audit_strategy_leakage.py` does. Strip the line before any qualifier upload; not a rules break, but a stylistic regression from the X1 patch hygiene policy.

## Recommendations

In strict priority order for the next 48 hours:

1. **HYGIENE-1** — Strip `POKERBOT_DISABLE_OVERLAY` env-var read from `src/bot.py:39`. ~30 min. Re-package + full G1–G11 gauntlet. This is the only rules-adjacent blocker.
2. **CONFIRM-1** — Paired-seed re-run Lane T v5_light_3bet vs v_final. 1.5h compute, 0 LOC. Confirm or invalidate the −135 bb/100 figure before any preflop patch.
3. **LEADERBOARD-1** — Localhost round-robin dashboard (`tools/leaderboard.py` + `tools/leaderboard_render.py`, ~180 LOC stdlib-only). Render 18 opponents with hands-played + CI width visible so noisy samples are obvious. ~2h.
4. **PATCH-1** (conditional on CONFIRM-1 reproducing) — Single exact-match `_RESPONSE_PATCHES` entry in `src/preflop_lookup.py` keyed on `(position='big_blind', voluntary_seq=('raise',), stack_depth_bb>80)`. ~2h.
5. **OVERNIGHT-2** — Adaptive queue redesign with Phase 1 (discovery, 2h) / Phase 2 (chained refinement, 4h) / Phase 3 (commitment, 3h) + wall-budget watchdog + relaxed kill rule.
6. **CORPUS-RESEARCH-1** — Focused /research run for 5 missing notes (LBR, Bayesian opp modeling, public-belief equity, action abstraction, ICM). 4–6h off-critical-path.

Explicitly do NOT do:
- Port vladimir's or dberweger's weights.
- Train Deep CFR from scratch.
- Add off-grid sizing nodes to the action abstraction.
- Re-run Lane A/H/M with the same kill rule.

## Preventive Measures

- Every overnight lane brief should include a "if you finish early, do X" continuation clause and a Phase 2 trigger.
- Every benchmark number narrated as "win" or "loss" must include sample size + CI half-width.
- Every confidence estimate must declare its load-bearing assumptions explicitly (field size, edge distribution, sample size).
- Pre-launch infra check (Docker up, network reachable, baseline SHA verified) before every overnight kickoff.
- Hygiene audit (`tools/audit_strategy_leakage.py`) is now part of the morning checklist Section 0, not just Section 7.
- Hypotheticals section in KANBAN.md is the seed log; promote only on numeric evidence to Now.
