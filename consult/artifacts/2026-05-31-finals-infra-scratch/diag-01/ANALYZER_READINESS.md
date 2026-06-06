# Analyzer Readiness (Finals Patch Window 2026-06-02)

> Scratch-only readiness review. No canonical edits, no analyzer port, no `data/finals_priors.npz` write.
> Findings from `context_builder` discovery+oracle (which read the listed files) plus direct path checks.
> Items flagged "(verify line refs)" are pending the native Workflow verification pass.

## 1. Toby-class river trap measurement — COVERED
- **Tool:** canonical `tools/analyze_postflop_trap_prevalence.py` (892 LOC). Present and test-covered.
- **Measures:** Toby/Mehedi postflop **trap prevalence** (river check-then-raise traps, paired-board river
  folds, etc.); emits frequencies, clusters, chip impacts, fingerprints, and text/JSON reports.
- **CLI:** `--input`/`--in`, `--json-out`, `--report`, `--top-n`. Parses single JSON, JSONL, and directories.
- **Ingest 06-02 histories?** Yes — it reads JSON/JSONL hand-history records (not only fixtures). Fixtures:
  `tests/integration/fixtures/postflop_trap_prevalence/` (`toby_can_check_trap.json`,
  `toby_paired_river_fold.json`, `mehedi_early_bust.json`, multiway/anonymous/opaque cases).
- **Status:** production-ready for ITS purpose (Toby river traps). It does **not** produce population priors
  and is **not** a substitute for the B9 priors analyzer.

## 2. B9 hand-history priors analyzer — PRESENT ONLY IN SIBLING; CANONICAL ABSENT
- **Intended surface:** `PokerBot-claude/tools/analyze_hand_histories.py` (630 LOC). Thinner 225-LOC variant in
  `PokerBot-codex`.
- **Canonical absence:** `/Users/farhad/Code/PokerBot/tools/analyze_hand_histories.py` does **not** exist; the
  `a00561c` / `release/v_final-e4b4a8f1` line does not carry it either. Must be ported into the release line
  **or** the window run from `PokerBot-claude`.
- **CLI:** `--in / --out / --force` (writes `.npz` priors; prints parse quality). Does **NOT** accept
  `--input / --output / --report`. (verify line refs)
- **Schema introspection:** intended to introspect schema from the first JSON record per CLAUDE.md policy
  (do not hardcode field names). (verify)
- **Priors emitted:** population VPIP/PFR/aggression, fold-to-c-bet, sizing by street, common preflop
  sequences, bot-cluster fingerprints — BUT see defects below.

## 3. Defects to fix BEFORE the window (tonight, eve of 06-01 — this is Phase 0 readiness)
- **C2 — fold-to-c-bet hardcoded:** in `analyze_hand_histories.py` `_aggregate()`, `cbet_faced`/`cbet_folded`
  are initialized but **never incremented** (`last_aggressor` tracked then dead-ended), so `pop_fold_cbet`
  always takes the `else` branch = **0.50** regardless of data. The playbook's 30–65% sanity gate will always
  read 0.50 and pass → false confidence. (verify line refs)
- **k-means bot-cluster fingerprints — unimplemented:** promised in the extractor docstring; implement or drop
  the spec before relying on it.
- **Playbook ↔ tool CLI mismatch:** `docs/playbooks/patch-window.md`
  - Phase 3 invokes the analyzer with `--input/--output/--report` → does not match `--in/--out/--force`.
  - Phase 7 LBR uses `exploit_check.py --zip` → release scorer supports `--bot` only.
  - Phase 0 / Phase 3 reference `tools/analyze_hand_histories.py` under `~/Code/PokerBot`, which is absent.
  Reconcile flags + tool location, or the window wastes time on avoidable failures. (verify exact lines)
- **B9_PREP notes:** `PokerBot-claude/consult/artifacts/2026-06-02-patch-window-prep/B9_PREP_SUMMARY.md`
  (review for any reconciliations already captured). (verify)

## 4. Mehedi-class BB-defense — MEASUREMENT GAP (must add post-06-02)
No history-parsing measure of BB-vs-button defense exists today (only live engine-vs-fixed-zip probes). The
precise missing measurement to implement against downloaded histories:
- **Positions:** identify hero/opponent seats, specifically **BB vs BTN** (heads-up button pressure).
- **Pressure detection:** detect **2.5× / 3× button opens** and button pressure sequences (open → 3-bet / jam).
- **Denominator:** count **BB opportunities FACING button aggression** (not all hands).
- **Responses:** measure BB **fold / call / all-in / raise** frequencies in those spots.
- **Normalization:** by **opportunities**, NOT total hands.
- **Isolation:** separate **HU-button pressure** from the generic preflop fold/all-in population fingerprint.

## 5. Exact scripts/paths to run after 2026-06-02 histories arrive
1. **Toby traps:** `/Users/farhad/Code/PokerBot/.venv/bin/python tools/analyze_postflop_trap_prevalence.py --input <hist_dir> --json-out <scratch>/toby_traps.json --report <scratch>/toby_traps.txt`
2. **Population priors:** `/Users/farhad/Code/PokerBot/.venv/bin/python PokerBot-claude/tools/analyze_hand_histories.py --in <hist_dir> --out data/finals_priors.npz` (after porting onto the release line OR running from the claude worktree; confirm `--in/--out` vs the playbook's `--input/--output/--report`).
3. **Add the Mehedi BB-defense measure** (§4) — currently unimplemented.
4. Re-run the full gauntlet (validator + import + leakage + edge + smoke + benchmark); update compact priors only; keep the qualifier artifact preserved.

## 6. Blockers
1. B9 priors analyzer absent from canonical/release line (port or run-from-sibling).
2. Playbook ↔ analyzer/exploit_check CLI mismatch (flags + tool path).
3. fold-to-c-bet hardcoded 0.50 (C2) — gives false sanity-gate confidence.
4. k-means bot-cluster fingerprints unimplemented.
5. Mehedi BB-defense history measure unimplemented.
6. LBR exploit gate is blind (LBR_UNTRUSTED — see REPORT.md §4) — not an analyzer blocker but it removes the
   exploitability arm from any finals promotion gate.
**Safety net:** patch-window.md Phase 2.5 (synthetic priors V1–V5) + Phase 9b (rollback to locked v_final,
sha e4b4a8f1…598) mean the default outcome of "analyzer doesn't work" is shipping the locked qualifier — safe.
