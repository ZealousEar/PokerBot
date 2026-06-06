# Critique — Qualifier Upload Decision & Runbook (2026-06-01)

**Reviewed:** `docs/plans/qualifier-upload-and-worktree-map-2026-06-01.md` vs. its source export `prompt-exports/oracle-plan-2026-06-01-104946-upload-runbook-d428f-bdd6.md`. **Scope:** decision/runbook correctness only — no bot-strategy or code review.

**Verdict:** Accurate and safe to act on today. The artifact decision, the worktree map, and the analyzer finding all check out against the live repo. The reorder introduces **no contradiction**. Remaining gaps are contingency/polish — but **two are worth fixing before you upload** (hash-confirmation fallback; deadline cutoff time).

## 1. Upload runbook (W1) — correct, two fixes
The three elements you flagged are present and right: hash cross-check (W1 done-when #4), the `.venv/bin/python` vs. host-`python` caveat (#2), and the "do not rebuild/repackage" warning (Approach). Upgrades:
- **Promote the cheap identity check to mandatory.** `LC_ALL=C shasum -a 256 v_final.zip best_green.zip` is marked *optional*; before an irreversible upload, make this one **required** (2 s, confirms you're shipping canonical bytes). Leave the heavy 9-command sequence optional as written — A3 ran it GREEN at 05:02.
- **The one step that misleads if read literally:** done-when #4 says "portal hash mismatch = HOLD" but is silent on the portal showing **no** hash. Under a hard deadline a human then either freezes (and misses an unrecoverable submission) or skips the step. Specify the branch: portal shows a hash → must equal `e4b4a8f1…598`, mismatch → re-upload, don't accept; portal shows none → the upload still stands, capture the confirmation page/ID and proceed. **Absence ≠ mismatch.**

## 2. Dependency reorder (W1→W2→W3→W4) — sound, no contradiction
The DAG is clean (W2←W1, W3←W1+W2, W4←W2; no cycle, no contradiction). W2-before-W3 is the better order — but be precise about *why*. It is **not** that W3 would otherwise orphan the analyzer: your W3 keep-list (and the export's C1) already retains both `PokerBot-claude` and `PokerBot-codex`, so the analyzer survives in either order. The real benefit is **logical clarity** — W3's keep-list is only final once W2 picks the analyzer's home (cherry-pick into canonical vs. designate `PokerBot-claude` as the patch-window dir). Frame it as clarity, not orphan-avoidance; the export kept both too, so "more correct than the export" would overstate it.

## 3. Load-bearing claims vs. live repo — verified
Spot-checked against the working tree (`git worktree list`, on-disk + `git ls-files`):
- **Analyzer:** `tools/analyze_hand_histories.py` is **absent** from canonical `PokerBot` and **present + tracked in both** `PokerBot-claude` and `PokerBot-codex`. The plan's "present in both" is correct (and more accurate than the export, which named only claude). Two precision fixes: (a) W2 says "untracked on [canonical branch]" — it is actually **absent** (not on disk, not tracked); the operational claim ("can't run it from canonical") still holds. (b) claude's copy carries **uncommitted** edits (` M`) — this reinforces W3's `--force`-silently-discards caveat and means W2-option-(b) would rest on uncommitted work; commit/stash it as part of W2.
- **Worktree map:** `git worktree list` returns exactly the 13 entries (12 registered + internal scratch) with branch names matching your table 1:1; the keep-4 / prune-9 split is correct.

## 4. Over-planning (W4) — trim to a pointer
The literal ask was "what do I upload + what are these folders." W2 earns its place — the analyzer blocker is a real, today-relevant find. **W4 is over-scoped:** it re-enumerates the 9 phases + full gate list that already live in `docs/playbooks/patch-window.md`, so it will drift from the playbook. The export itself marked this item *optional*. Trim W4 to a pointer: playbook ref + "default = rollback to `v_final.zip`" + "one-shot, irreversible." That keeps the doc focused on today without losing the load-bearing readiness work in W2.

## 5. Missing items that would actually bite
1. **No submission cutoff time / timezone anywhere.** "Due today" + "do W2 tonight" assumes a late cutoff; if it's, say, midday UTC, W1 is far more urgent and the "tonight" framing for W2 is moot. Add the exact instant to **Open Questions** beside the portal URL — both are account-only unknowns that gate a today-upload and must be resolved **first**.
2. **Hash-absent contingency** (see §1) — same root cause: an unrecoverable action with an under-specified success signal.

*(Skipped as out-of-lane/nit: re-verifying the SHA — that's A3's job, already done; and the "#9" label being reused for both an A3 check and a no-go condition — true but immaterial.)*

## Fix before upload (shortlist)
1. **W1 #4:** add the hash-absent branch (absence ≠ mismatch → capture confirmation ID, proceed).
2. **Open Questions:** resolve + record the exact submission cutoff time/timezone, before anything else.
