# CONSULT — PokerBot "Thorp": optimise the next ~90 minutes to make the finals bot as strong as possible

You are a top-tier poker-AI + game-theory + ML-engineering advisor. You cannot access our repo or runtime; the local agent (Claude Code, with RepoPrompt MCP tools) has gathered everything below and can execute anything you specify. Be direct, evidence-based, and concrete. Two hard facts frame everything: our bot is ALREADY LIVE on the portal as a valid fallback, and any RE-SHIP must clear a full verification gate and a HUMAN upload before a ~90-minute deadline.

Your ultimate deliverable: **a concrete, ranked, time-boxed plan for how to spend the next ~90 minutes to maximise the bot's expected finals performance** — mapping each action to the right execution harness, with EV direction, downside risk, and whether it fits the verification window. Tell us plainly whether the best move is to SHIP-AS-IS (freeze), SHIP-A-DATA-RETUNE, or SHIP-A-CODE-FIX.

---

## 1. The competition (format changed TODAY — reason from THIS, not older assumptions)
- Finals are a FRESH competition. Qualifier 1 & 2 standings DO NOT carry; every finalist starts equal.
- **Phase 1 "The Bubble":** ~40 Swiss-paired 6-max matches per bot, **800 hands each**, 6 bots/table, fresh 10,000 chips per match. Ranked by **CUMULATIVE chip performance** across all matches, with small statistical SHRINKAGE on the top-6 cut. Top 6 advance.
- **Phase 2 "Final Table":** top 6, 10k chips, up to 5,000 hands/match, auto-ends when one bot holds all chips. Last bot standing wins £4,000.
- **Deadline:** whatever is on the portal at 20:00 UK today (~90 min away) plays the finals. Upload is HUMAN-ONLY (explicit per-upload go-ahead; no autonomous upload).
- NOT single-elimination. We previously (wrongly) assumed single-elim + "embrace variance as the underdog." Dead. Phase 1 rewards consistent cumulative chip extraction over a Swiss field; shrinkage regresses high-variance lines toward the mean.

## 2. Our bot — "Thorp" (LIVE submission, sha b108eff5)
- Architecture: near-Nash blueprint (preflop lookup + postflop CFR+ buckets, shipped as `.npz` + numpy inference) + a bounded live exploit OVERLAY. `opponent_model.exploit_shift()` returns per-cluster frequency deviations after a ~30-hand warmup vs a precomputed `data/field_priors.npz`, capped at MAX_DEVIATION_PP = 0.20, consumed by `postflop.decide_postflop`.
- Style (qualifier data, indicative): fold 58.9% / call 6.4% / raise 34.7% / AF 5.45 / avg-raise 430 / bust 56% / scoop 0%. **Extreme polarization** (very low call %).
- Leak history: earlier build stacked off near-dead on paired/under-boat full houses (commitment gate compared equity to a STATIC tight range, not villain's actual jamming range). b108eff5 PATCHES this. Validator 4/4, import-clean, edge_cases 14-passed, Docker smoke 200/200 (+5550), failure-mode-check PASS.
- Read-only validation just run (800-hand match length = finals length, paired seeds, 0 errors) vs the 5 ENGINE reference bots: beats aggressor +1250 bb/100, shark +22, mathematician +27, ref_bot_2 +27. NOTE: engine reference bots, NOT the real finalist field; all HEADS-UP; no by-street bust instrumentation.
- Residual KNOWN leaks (low freq, postflop only): (C) dry unpaired bloated-pot TPTK/overpair jams on eq≥0.55 vs STATIC range — same class as original leak, more common texture; (A) trips-on-board domination miss; (B) nut-flush jam into possible straight-flush on monotone connected boards; (bleed) per-call cap 25% owed but NO cumulative cross-street commitment cap. **Preflop is NOT audited** — if 56% bust is 3-bet/4-bet-jam driven, the postflop gate doesn't help.

## 3. The finalist field (64 bots; playstyle for 43; same bots, results reset)
- **Hyper-aggro / high-fold (polar, like us)** ×8: Oxvard, Thorp(us), talan, goku, make_no_mistakes, Inefficiency, BATNEEC, TheHouse.
- **Nit / tight-passive** ×4 (fold ~70–75% → free steals): Looper257, winning, Lyra, G-Forge.
- **Calling-station / loose-passive** ×6: CrimsonBot, Khan't Fold, SummerSun, TheUnknown, elprofesoriqo, never played poker.
- **Balanced** ×23 (strong: SevenDeuces win61.8/AF1.41, NecessarySkew AF2.36, FerdaBot, Hyperion, IveyBot, durak, twader, gems_VC2…).
- **Aggressive** ×2: 50CentRaise, GrandSlam.
- High-bust stations to punish: CallMeMaybe (fold62.5/AF1.2/bust91.7), goku (bust91.7). Full per-bot table available on request.

## 4. What we already tried THIS window (failed — do not blindly repeat)
- Candidate A: widen 3-bet (+A9s–A6s BTN/SB). Paired-seed A/B vs baseline: **−353 bb/100**, cratered vs aggressor (−726). DISCARDED.
- Candidate B: +0.07 cbet bluff on dry/unpaired flops. Paired-seed A/B: **−741 bb/100**, cratered vs aggressor (−1143). DISCARDED.
- Solver-halt rule (2 non-improving attempts → stop) has fired.

## 5. Six blind spots WE identified (validate, correct, or de-prioritise each — and add any we BOTH missed)
1. **6-max multiway ≠ heads-up.** All our evidence (H2H tool, A/B gauntlet) is heads-up. Finals are 6 bots × 800 hands. Multiway punishes polarization and thin value-jams. We have ZERO 6-max evidence — likely our biggest unmeasured risk.
2. **Overlay re-warms every match.** ~30/800 ≈ 4% of each match played "blind" on static priors; Swiss re-pairs each match (no cross-match memory). And `field_priors.npz` was tuned for the QUALIFIER population, not these 64.
3. **Bust-origin unknown.** 56% bust, scoop 0%, never instrumented by street or preflop-vs-postflop. If busts are preflop 3-bet/4-bet jams, our postflop leak-patch answered the wrong question; preflop was never audited.
4. **Phase 2 is ICM-like.** Last-bot-standing across 6 with up to 5000 hands rewards survival/stack management, not raw chip-EV; our bot is chip-EV with no short-stack/ICM awareness. (Lower priority — must make top 6 first.)
5. **Shrinkage changes the variance calculus.** ~40 matches averaged + shrinkage regresses high-variance lines; consistency now matters more than the old single-elim frame implied.
6. **Robustness at scale.** ~40×800 ≈ 32k decisions/bot; any timeout/exception defaults to fold and silently bleeds. We validated 200-hand smoke only; no sustained-load stress test.

## 6. Execution harnesses available to the local agent in the next 90 min
- **RepoPrompt MCP** — file ops, code maps, selection, read-only git, in-repo edits.
- **Claude Code** — this agent; direct edits + bash + the `.venv` (Python 3.10 + eval7) engine; can run `tools/h2h.py`, `tools/benchmark.py` (paired-seed / all-templates), `tools/self_play.py`, `tools/deployed_artifact_gauntlet.py`, the engine validator, import audit, leakage audit, edge_cases pytest, Docker smoke, and `tools/package.py`.
- **Codex CLI** — parallel sandbox agents in isolated worktrees (20× plan, can fan out many narrow lanes).
- **Claude Code `/goal`** and **Codex `/goal`** — autonomous goal-seeking harnesses that can iterate train→verify loops unattended.
- Compute is NOT the bottleneck; the 90-min CALENDAR + the full verification gate is. Engine has NO PyTorch/C++ at submission; numpy `.npz` inference only.

## 7. Hard constraints on any RE-SHIP
Must pass ALL before upload: engine validator (AST+size), import audit, leakage audit, edge_cases pytest, a paired-seed (or ≥50k-hand) benchmark PROVING net-positive vs `best_green`, Docker smoke. Then a HUMAN SHA-verified upload. Data-only changes (e.g. retuning `field_priors.npz`) still pass the same gate but touch no code (smaller validator/leakage surface, but a 6-max benchmark proving improvement is still required). Benchmark variance at 10k hands ≈ ±20 bb/100 (95% CI) — single 10k runs are NOT acceptance-grade.

---

## YOUR TASK — answer all, then give the bottom line
**A. The 90-minute plan.** Produce a concrete, ranked, time-boxed sequence of actions to maximise expected finals performance, each tagged with: which harness runs it, EV direction, downside risk, and FITS-WINDOW (yes/no given the gate). Bias toward not breaking a working live artifact, but flag any clearly +EV low-risk move we're leaving on the table. Explicitly decide: build 6-max evidence first (and with what opponents) vs attempt an improvement; and whether `/goal` autonomy is worth it here or too risky given the gate + the failed A/B history.
**B. Best use of the field data.** Is retuning `field_priors.npz` (DATA-ONLY) toward the actual finals field a higher-value, lower-risk lever than code edits? How would you set priors to exploit the nit-heavy + high-bust-station mix WITHOUT over-fitting or becoming counter-exploitable, given each 800-hand match re-warms from scratch?
**C. Polarization in cumulative-chip Swiss.** Does call 6.4% help or hurt vs the single-elim frame we previously assumed, especially MULTIWAY? Should we add a calling range — and is that even safe under the gate in 90 min?
**D. Anything we BOTH missed.** Name additional blind spots beyond our six (e.g. position/stack-depth coverage of the blueprint, multiway all-in side-pot handling, opponent bots that themselves adapt, sizing-tell exploits, seed/variance gaming of the benchmark, what a sharp opponent does to a 6.4%-call bot).

For each: recommendation + rationale + the single most important risk. **End with a one-line bottom line: SHIP-AS-IS vs SHIP-A-DATA-RETUNE vs SHIP-A-CODE-FIX, and the first concrete command/action the local agent should run in the next 5 minutes.**
