# LANE C — Sibling Candidate Gate Results (2026-05-31)

Gate run from canonical `/Users/farhad/Code/PokerBot` with `.venv/bin/python`.
Siblings were packaged READ-ONLY (their own `tools/package.py`, CWD=sibling);
neither sibling worktree nor canonical `src/` was edited.

## Protected artifact integrity
- `submissions/v_final.zip` sha256 = `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598` at START and END.
- `submissions/best_green.zip` sha256 = same, START and END.
- protected_sha_ok = TRUE.

## Candidate 1 — codex (PokerBot-codex, branch w4-track-1-lbr)
- Modified working tree: `src/postflop.py` (+62), `src/preflop_lookup.py` (+7) — LBR spot corrections.
- Self-label on latest commit d1ec588: "checkpoint: W3 candidate baseline (forensic, not for promotion)". Its committed W3 lineage FAILED Gate H on held-out seed-base 142; the gated changes here are uncommitted on top of that fork point.
- Packaged: `codex.zip` sha256 `e2ba542b79ca6a026fdbad30274e818d71ad75d0e2cfdef499afaa0b4e5fa296` (bot.py 295 lines, postflop.py 380 lines).

Gate ladder:
- Stage 1 validator: PASS (exit 0).
- Stage 1 import_audit (tool byte-identical to canonical; ran on sibling tree): PASS, cold import 0.091s / 38.1MB.
- Stage 1 canonical leakage audit (zip-based): PASS.
- Stage 2 edge tests (pytest tests/edge_cases on codex tree): 73 passed.
- Stage 2 authoritative smoke (Docker sandbox, vs template, 200 hands): OK, 0 hero/bot errors, 136/200 normal bust (template busted), 3.25s.
- LBR exploit_check (codex W3 tool via lane-local wrapper run_exploit.py): candidate aggregate 78.2 mbb/g, preflop 0.0 mbb/g (within caps 100/200); locked v_final on the SAME tool = 521.7 preflop / 4883.0 aggregate. CAVEAT — NOT INDEPENDENTLY VERIFIED: this is codex's OWN 925-line forensic SPOTS suite, and codex's entire diff is "LBR spot corrections" tuned against this exact suite, so a low candidate score is expected by construction (circular — the same flaw that makes claude's own leakage tool non-authoritative). Decisive tell: locked v_final is the shipped artifact that historically passed a <=200 LBR gate, yet scores 4883 (24x over caps) on this tool, proving this tool is NOT the gate v_final passed. Treat the LBR arm as inconclusive / not independently confirmed, not a clean pass.
- Stage 3 paired six-max pods (40 paired seeds, base 142, candidate vs locked `pods_locked/matches.jsonl`; opponent zips verified byte-identical to locked baseline):

| composition | paired seeds | locked p50 | cand p50 | locked bust | cand bust | paired Δmean (cand−locked) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C0_BASELINE_RECHECK | 40 | -10000 | +18875 | 75.0% | 22.5% | +19546 |
| C1_SINGLE_TOBY_WEAK_FIELD | 40 | -951 | -10000 | 45.0% | 75.0% | -6809 |

  - C0 (no Toby): candidate ROBUSTLY BETTER — bust 9/40 (22.5%) vs locked 30/40 (75.0%), -52.5pp ~3.5sigma; 38/40 seeds >= locked; paired Δsum +781,857. Statistically strong, not noise. Bust-cause glance: all 9 candidate busts are river, winner = aggressor — locked's high C0 bust is an aggressor-driven phenomenon the candidate handles much better.
  - C1 (one Toby seat): candidate worse on the conservative no-regression bar, but the signal is NOISY/TAIL-DRIVEN, not a collapse: median paired diff = 0, only 19/40 seeds worse (21/40 are >= locked), negative mean (-6809) driven by a few -60000 bust seeds in a bimodal format. The adverse signal is bust 75% vs 45% (+12 busts/40 ≈ 2sigma — "probably worse," not nailed). Bust-cause: 30 river busts, winner dominated by toby_master (78 credits). So the candidate cannot AFFIRMATIVELY demonstrate "no bust regression" in C1 → fails a conservative no-regression gate.
  - Decisive-pod protocol: an unrefuted bust regression appeared at C1 → STOPPED before C3/C4 per fail-fast rule.

VERDICT (codex): does NOT clear the FULL gate — cannot affirmatively clear the six-max no-regression bar on C1_SINGLE_TOBY_WEAK_FIELD. Honest shape: codex ROBUSTLY IMPROVES the weak-field baseline (C0, ~3.5sigma, aggressor-shaped) and AMBIGUOUSLY-WORSENS the Toby pod (C1, +30pp bust but zero-median / minority-of-seeds / high-variance). Not "junk" and not a clean fail — it's a strong baseline gain plus a possible Toby-specific hole. Actionable for a human: the LBR patch may have a Toby-shaped hole — investigate C1 specifically (more seeds to resolve the 2sigma bust delta); if real it's a targeted defect, if noise codex is promising. Not flagged for promotion. (all-template benchmark not run — gate already unresolved at pods; cannot rescue. LBR arm inconclusive per circularity caveat above.)

## Candidate 2 — claude (PokerBot-claude, branch vladimir-audit-2026-05-28)
- Modified working tree: `src/{bot,postflop,preflop_lookup,sizing}.py` — anti-Vladimir audit, large strategy diff, never six-max gated.
- Packaged: `claude.zip` sha256 `a5a52d973e4f1191c74082cf0848dd30f8f98b3ed423f55d7d62cae2c1d97387` (bot.py 322 lines, postflop.py 131 lines).

Gate ladder:
- Stage 1 validator: PASS (exit 0).
- Stage 1 import_audit (sibling tree): PASS, cold import 0.036s / 22.4MB.
- Stage 1 CANONICAL leakage audit (zip-based, authoritative): **FAIL (exit 1)** — 19 hits.
  - Hits (all comment-only / shim text, NOT runtime identity branching): `bot.py:8 snapshot` (claude's own package.py SHIM text "no weakened-snapshot rigging"); `src/bot.py:153,154,307 branch`; `src/equity.py seed` (x6, deterministic-RNG seeding comments+code); `src/opponent_model.py:10 seed`, `:149 v3_hardened`+`v_final`, `:150 snapshot`, `:163 aggressor`; `src/preflop_lookup.py:66,111 branch`; `src/ranges.py:187 v1_blueprint`, `:188 snapshot`.
- Stage 1 sibling leakage audit (secondary signal): PASS, 0 hits — claude's own tool uses a narrower forbidden list (identity tokens only: template/aggressor/.../v_final/claude_bot) and reportedly does not flag `branch`/`seed`/`snapshot`, and even misses the `v_final`/`v3_hardened` comment hits the canonical tool catches. This circularity (grading a sibling with its own looser tool) is exactly why the canonical hardened tool is authoritative.

VERDICT (claude): DIED at Stage 1 on canonical leakage (exit 1). Does NOT advance to smoke/edge/pods; its strategy was never evaluated. The failure is comment/shim hygiene, not a demonstrated strategy defect — a human can scrub the offending comment strings + the package.py shim text and re-gate. No scrubbed variant was built (out of scope: do not re-derive the candidate).

## Bottom line
- gate_clearer = FALSE. Neither sibling candidate clears the FULL hardened gate.
- codex: cleared static + edge + smoke; LBR arm inconclusive (candidate's own forensic tool, not independently verified); could not affirmatively clear the six-max no-regression bar — robust C0 gain (~3.5sigma, aggressor-shaped) but unrefuted C1 Toby bust regression (75% vs 45%, ~2sigma, zero-median/minority-of-seeds). A strong baseline gain plus a possible Toby-specific hole worth a human look — NOT a clean fail.
- claude: failed the cheapest stage (canonical leakage, comment/shim hygiene only); strategy unevaluated; human can scrub strings + re-gate.
- Nothing promoted. Locked `v_final.zip` / `best_green.zip` untouched and SHA-verified at start and end.
- Engine stability: `ext/fullhouse-engine/sandbox/{match,runner,validator}.py` mtime 2026-05-22, unchanged across the May 30 (locked baseline) → May 31 (candidate) window, so engine drift does not threaten the pairing. Opponent zips verified byte-identical to the locked baseline.
- Baseline note for the human: the locked C0_BASELINE_RECHECK has an inverted property (locked busts 75% with NO trap bot vs 45% WITH a Toby present), driven by aggressor in the no-Toby pod. Anyone reusing this baseline must know this.
