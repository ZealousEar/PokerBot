# Qualifier brainstorm capture — 2026-05-27 evening

## Purpose

Capture two independent agent brainstorms on the qualifier upload posture (proof-before-patch framing) for comparison against `docs/plans/qualifier-finals-rollout-2026-05-27.md`. Both agents were given the same brief: critique the rollout plan's "ship canonical AS-IS" assumption and recommend whether qualifier-day posture should change.

## Contents

| File | Source | Status |
|---|---|---|
| `genius_response.md` | External "genius" agent (Opus-4.7-class) | ✅ filed 2026-05-27T23:06:59Z |
| `repo_prompt_response.md` | Repo Prompt agent | ⏳ awaited |
| `DIFF.md` | Side-by-side convergence/divergence analysis | ⏳ pending both responses |

## How this links to the rollout plan

The two responses inform whether to insert a **pre-qualifier public-field readiness gauntlet** between A1 and A3 in `docs/plans/qualifier-finals-rollout-2026-05-27.md`. If both agents converge on "yes, add it," the plan needs a new A2b work item and the SHIP decision in `docs/morning-promotion-checklist.md §6` needs a public-bot gate added to the matrix. If they diverge, the divergences go to the user via `ask_user` before A1 dispatches.

## Why log verbatim

The orchestrator loop is stateless across compactions. STATUS.md captures the *decision* but not the *evidence that drove it*. Storing both responses verbatim under `consult/artifacts/` matches the established pattern (compare `2026-05-27-worktree-audit/MAP.md`, `arbitration/ORCHESTRATOR_REPORT.md`) so a resumed session can reconstruct *why* we deviated (or did not deviate) from the plan.

## Next step

Wait for the Repo Prompt agent response. File it as `repo_prompt_response.md` with the same verbatim-then-orchestrator-notes structure. Then produce `DIFF.md` calling out the load-bearing disagreements, and surface those via `ask_user` before dispatching A1.
