# Qualifier Upload Decision & Worktree Map: Plan

## Goal
Answer two questions definitively before today's Swiss-qualifier deadline: (1) what every `~/Code/PokerBot*` worktree is for and which actually matter, and (2) exactly which file to upload and how — with confidence it is the right one. The artifact is already chosen and freshly re-verified; this plan is the upload runbook plus the repo orientation, so the decision is auditable and post-qualifier cleanup is scoped.

## Background

### Headline (verified TODAY)
- **Upload `/Users/farhad/Code/PokerBot/submissions/v_final.zip`**, sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- It passed the full **A3 ship-day verification GREEN at 2026-06-01T05:02:37Z** (`STATUS.md:602-623`): identity, engine validator (4/4 legal), leakage, import budget (0.107s / 33 MB), 25 edge tests, exploit/LBR (preflop 18.0 / aggregate 7.4 mbb/g vs caps 100/200), smoke (200/200, chip_delta +14500), size/layout, drift — **0/10 no-go conditions fired**. Logged verdict: "SHIP v_final.zip for the 2026-06-01 Swiss qualifier."
- `v_final.zip` is byte-identical to `best_green.zip`; both read-only, mtime unchanged since May 22.

### Why the bytes are unchanged since May 22 (this is not idle work)
- The May 22 build survived 9 days of attempts to beat it. Every candidate was benchmarked; **none was certified better**. Strongest near-miss `v_w3_candidate.zip` beat the R1 baseline on the primary objective but failed risk gates (Neel loss, ablation FAIL, LBR cap) and was left unpromoted by explicit decision (`PokerBot-codex/STATUS.md:747,789,794`).
- Decision locked 2026-05-29 (UPLOAD-LOCK GREEN, `STATUS.md:586`), re-confirmed by A3 today.

### Worktree map — 12 registered git worktrees (+1 internal), all forked from the release artifact
| Dir | Branch | Role |
|---|---|---|
| `PokerBot` | tooling/postflop-trap-extractor-2026-05-29 | **Canonical checkout.** Holds shippable `submissions/v_final.zip`; `STATUS.md` is source of truth. |
| `PokerBot-gauntlet` | release/v_final-e4b4a8f1 | **Release branch.** Holds the authoritative tool copies (import_audit / exploit_check / smoke_run) the ship commands pull from. |
| `PokerBot-claude` | vladimir-audit-2026-05-28 | Claude lane — Vladimir h2h audit + analyzer hardening. |
| `PokerBot-claude-b4` | b4-famadeo-audit-2026-05-28 | Claude lane — famadeo deficit audit (deficit collapsed → no patch). |
| `PokerBot-codex` | w4-track-1-lbr | Codex lane — LBR / W4 track 1. |
| `PokerBot-codex-b3` | b3-priors-consumer-2026-05-28 | Codex lane — finals-priors consumer. |
| `PokerBot-codex-t2` | w4-track-2-flop-equity | Codex lane — flop equity. |
| `PokerBot-codex-t3` | w4-track-3-archetype-calibration | Codex lane — archetype calibration. |
| `PokerBot-codex-postflop-trap` | candidate/postflop-trap-2026-05-29 | Candidate lane — postflop trap. |
| `PokerBot-codex-preflop-antecedent` | candidate/preflop-antecedent-grid-2026-05-29 | Candidate lane — preflop antecedent grid. |
| `PokerBot-laneA-postflop` | candidate/postflop-trap-v2-2026-05-30 | Candidate lane — postflop trap v2. |
| `PokerBot-laneB-mehedi` | candidate/mehedi-bb-defense-2026-05-30 | Candidate lane — Mehedi BB defense (h2h delta 0.0 → no fix). |
| `PokerBot/.claude/worktrees/wf_17770a2a-961-2` | (internal) | Tool-created scratch worktree. |

- All 12 are **legitimate `git worktree` checkouts** (confirmed via `git -C ~/Code/PokerBot worktree list`), not stray copies. They are parallel R&D lanes from the 05-27→05-30 overnight swarms — each tried to find an improvement; all concluded without promoting a better artifact (several still read `## FINAL SUBMITTED`).
- `CLAUDE.md` documents only 3 worktrees (PokerBot / -claude / -codex); `PokerBot-gauntlet` (the release branch) is a legitimate 4th keeper. The remaining **8 top-level lanes + 1 internal scratch** accreted during the overnight runs and are now **stale exploration lanes** — irrelevant to the upload, candidates for post-qualifier pruning (keep 4, prune 9; see W3).
- `consult/artifacts/` (main) vs `consults/` (worktrees) are two different local R&D log dirs; both are gitignored and **not part of the submission**.

### Artifact reconciliation (no better build is hiding anywhere)
- Canonical `e4b4a8f1…598` appears as `v_final.zip`/`best_green.zip` across PokerBot, -codex, -gauntlet, and as `v_final.zip` in -claude — a consistent "final" across every serious lane.
- Every distinct non-canonical zip was cross-checked against STATUS/consult verdicts: all are early gate snapshots, rollback-only artifacts, or explicitly rejected candidates. **No certified-better artifact exists.**

### Submission constraints (engine-authoritative)
- Layout: `bot.py` at zip root, optional `data/`, no other root `.py`, no `.py` in `data/`, no symlinks, no path traversal (`ext/fullhouse-engine/sandbox/validator.py:433-475`).
- Size: total ≤250 MB, `data/` ≤200 MB, `bot.py` ≤5 MB (`validator.py:38-40`). Ours: 28 K zip, 14 files.
- Runtime: Python 3.10; pinned libs (eval7 0.1.7, numpy 1.26.4, scipy 1.13.0, treys 0.1.8, sklearn 1.5.2); 2 s/decision, one 30 s warmup (`Dockerfile`, `runner.py:26-28`).

### Upload method
- Manual portal upload: "drag `submissions/v_final.zip` to the upload form," then "record the portal-side confirmation hash" (`docs/morning-promotion-checklist.md:299-302`).
- Engine README documents submission *formats* only — **no portal URL**, only `fullhousehackathon.com` (`ext/fullhouse-engine/README.md:190-195`).
- Patch-window rule (verbatim): "Hand histories from your D1 matches are downloadable as JSON. You can submit one updated bot before D5." (`ext/fullhouse-engine/README.md:152-153`).

## Approach

Three moves, in priority order. Only the first is on today's critical path.

- **Upload now (today).** Ship canonical `submissions/v_final.zip` (sha256 `e4b4a8f1…598`) as-is. A3 ship-day verification is GREEN (0/10 no-go, 2026-06-01T05:02:37Z) and the decision is locked — the only remaining action is the manual portal drag plus a post-upload hash cross-check. **Do not rebuild or repackage:** `tools/package.py` re-stamps the zip and the packaged `src/bot.py` deliberately differs from the current checkout (`AUDIT.md` drift table; A3 entry check #9), so a rebuild throws away the gauntletted artifact.
- **Make the D5 patch window safe (tonight → before 06-02).** The qualifier upload is recoverable only by getting it right today; the finals patch window is a single irreversible shot. One readiness blocker is confirmed: `tools/analyze_hand_histories.py` is **absent from the canonical checkout** (verified — present + tracked in both `PokerBot-claude` and `PokerBot-codex`). Resolve where the patch window runs from before histories drop.
- **Clean up the worktrees (post-qualifier, low stakes).** The Background map shows 12 worktrees where policy documents 3. After the upload is confirmed, prune the 8 stale R&D lanes + 1 internal scratch, keeping the 4 load-bearing checkouts. Cosmetic — it touches none of the shipped bytes.

**Sequencing:** W1 is the only thing that matters today. W2 (patch readiness) is time-critical before 2026-06-02 and should precede W3, since W3's keep-list is only final once W2 decides where the analyzer lives. W3 is whenever. W4 is the window itself. The one path-altering decision — rebuild vs ship-as-is — is already resolved to ship-as-is.

## Work Items

### W1 — Upload the locked qualifier artifact (TODAY, critical path)
- **Goal:** Get canonical `submissions/v_final.zip` (sha256 `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`) onto the qualifier portal and confirm the portal-reported hash matches. A3 already verified it GREEN — this is the upload, not re-verification.
- **Done when:** (1) **mandatory** identity re-check `LC_ALL=C shasum -a 256 submissions/v_final.zip submissions/best_green.zip` → both equal canonical; (2) any deeper re-check uses the AUDIT.md `.venv/bin/python` 9-command sequence (NOT bare host `python` 3.14, which lacks eval7) — optional, since A3 ran them GREEN at 05:02; (3) `v_final.zip` uploaded via the portal form; (4) portal confirmation handled — if the portal **shows** a hash it must equal `e4b4a8f1…598` (a true mismatch = no-go #9 → HOLD and re-upload); if the portal **shows no hash**, that is NOT a mismatch — record the portal confirmation/submission ID and proceed (do not freeze on a missing hash and risk the deadline); (5) a `## QUALIFIER SUBMITTED 2026-06-01` entry appended to `STATUS.md` with the portal hash or confirmation ID.
- **Key files:** `submissions/{v_final,best_green}.zip`; `docs/morning-promotion-checklist.md §8`; `consult/artifacts/2026-05-29-ship-lock-audit/AUDIT.md` (no-go list + 9-command sequence); `STATUS.md`.
- **Dependencies:** A3 verification — **DONE** (`STATUS.md:602-623`). Portal URL — from your hackathon account (see Open Questions).
- **Size:** ~15 min, manual.

### W2 — Make the D5 patch window safe (time-critical: tonight → before 2026-06-02)
- **Goal:** Run `docs/playbooks/patch-window.md` Phase 0 and resolve the two readiness blockers tonight, so the one-shot finals window opens from a working baseline rather than discovering breakage under the clock.
- **Done when:** (1) **Analyzer location resolved** — `analyze_hand_histories.py` confirmed absent from canonical (verified) but present/tracked in both `PokerBot-claude` (`vladimir-audit-2026-05-28`) and `PokerBot-codex`; the `PokerBot-claude` copy has **uncommitted edits**, so commit or stash it as part of this step; then pick one path tonight: cherry-pick it into the canonical checkout, OR designate `PokerBot-claude` as the patch-window working dir (and reflect that in W4); (2) **Patch branch confirmed** — canonical HEAD is `tooling/postflop-trap-extractor-2026-05-29`, not `main`, which trips Phase 0's "clean tree on main" wording; (3) Lane D synthetic-priors fallback reachable; (4) `data/` clean (no stale `finals_priors.npz`); (5) both artifact SHAs still canonical.
- **Key files:** `docs/playbooks/patch-window.md` (Phases 0 / 2.5 / 3); `PokerBot-claude/tools/analyze_hand_histories.py`; `data/`; `submissions/{v_final,best_green}.zip`.
- **Dependencies:** W1 (baseline = shipped state). Must finish before histories drop 2026-06-02.
- **Size:** ~30–45 min.

### W3 — Prune stale worktrees (post-qualifier, low stakes)
- **Goal:** Reduce the 12 registered worktrees (+1 internal) to the 4 load-bearing checkouts, reconciling to the documented policy.
- **Done when:** `git -C ~/Code/PokerBot worktree list` shows only `PokerBot` (canonical), `PokerBot-gauntlet` (release), `PokerBot-claude`, `PokerBot-codex`. Remove the other 8 + the internal scratch via **`git worktree remove`** (never `rm -rf`). **Caveat:** these lanes hold gitignored, on-disk-only `consults/`/artifacts not in canonical; `git worktree remove --force` silently discards them — back up or accept the loss first. Committed branch refs survive removal. **Must keep** `PokerBot-claude` and `PokerBot-codex` (they hold the analyzer W2/W4 depend on). Re-verify artifact SHAs unchanged after.
- **Key files:** git worktree registrations only (no `src/` / `submissions/` changes); `consult/artifacts/2026-05-27-worktree-audit/MAP.md`; `AGENTS.md` worktree policy.
- **Dependencies:** W1 (upload confirmed) and W2 — the keep-list retains `PokerBot-claude`/`-codex` regardless, so this ordering is for logical clarity (keep-list final only after W2), not because the prune would otherwise orphan the analyzer.
- **Size:** ~20 min.

### W4 — One-shot D5 finals submit-or-rollback (the window: 2026-06-02 → 06-03)
- **Goal:** Execute the existing `docs/playbooks/patch-window.md` runbook against the released D1 hand histories and make the irreversible one-shot call. **Default = ship qualifier `v_final.zip` unchanged for finals;** a patched `v_finals.zip` ships only if it clears every gate the qualifier did, at equal-or-better numbers.
- **Done when:** the playbook's promote-or-rollback decision is recorded in `STATUS.md` (a `## FINALS RESUBMITTED` or `## FINALS ROLLBACK` entry); the single updated-bot upload is spent at most once before D5.
- **Key files:** `docs/playbooks/patch-window.md` (authoritative phase list + acceptance gates — follow it, don't duplicate here); `docs/finals-strategy-2026-05-27.md §2` (default-to-same-artifact).
- **Dependencies:** W2 (readiness resolved) + the 2026-06-02 history release. One-shot/irreversible per engine README.
- **Size:** ~5–6 h across the 24-h window (per the playbook).

## Open Questions
- **Where exactly is the upload portal?** The repo references only `fullhousehackathon.com`; the precise qualifier submission URL/login is not in-repo (it lives behind your hackathon account). This is the one item the codebase cannot resolve.
- **What is the submission cutoff time (and timezone)?** Not recorded anywhere in-repo. It determines how urgent W1 actually is today — confirm it from the hackathon platform.

## References
- A3 ship-day verification: `STATUS.md:602-623`
- Upload-lock decision: `STATUS.md:586-596`
- Ship-day 9-command sequence: `consult/artifacts/2026-05-29-ship-lock-audit/AUDIT.md:117-171`
- Submission rules: `ext/fullhouse-engine/sandbox/{validator.py,Dockerfile,runner.py}`, `ext/fullhouse-engine/README.md`
- Upload checklist: `docs/morning-promotion-checklist.md:299-302`
- Worktree list: `git -C ~/Code/PokerBot worktree list`
