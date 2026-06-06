# Worktree ship-state audit — 2026-05-27

## 1. Ship-state recommendation

**SHIP canonical `~/Code/PokerBot/submissions/v_final.zip` sha `e4b4a8f1…598` AS-IS for the 2026-06-01 qualifier.** The packaged `src/bot.py` (sha `d33484ed…`, 196 LOC) contains `_OVERLAY_DISABLED = os.environ.get("POKERBOT_DISABLE_OVERLAY") == "1"` at line 39, which our internal `audit_strategy_leakage` tool flags but is **not** a sandbox safety issue (see §1a evidence below).

### 1a. Env-var injection audit — engine sandbox cannot inject `POKERBOT_DISABLE_OVERLAY`

Verified 2026-05-27 by grep against `ext/fullhouse-engine/sandbox/`:

| Evidence | File:Line | Implication |
|---|---|---|
| `POKERBOT_DISABLE_OVERLAY` absent from entire `ext/fullhouse-engine/sandbox/` | grep → no matches | Engine never sets it intentionally. |
| Docker run cmdline (qualifier mode) enumerates only `-e ACTION_TIMEOUT`, `-e BOT_PATH`, `-e BOT_DATA_DIR` | `match.py:131-133` | Docker passes ONLY these three env-vars into the container. Host `os.environ` is NOT forwarded by Docker unless `--env-file` or explicit `-e` is used. |
| `env = { **os.environ, BOT_PATH, BOT_DATA_DIR, ACTION_TIMEOUT }` | `match.py:140-144` | This block only applies to the local subprocess fallback (`USE_DOCKER=false`), not to the qualifier sandbox. |
| Container flags `--network none --read-only --no-new-privileges --user 1000:1000` | `match.py:122-128` | No process inside can set/read env from outside; FS is read-only; no escalation. |
| Engine-recognized env-vars: `BOT_PATH`, `BOT_DATA_DIR`, `ACTION_TIMEOUT`, `WARMUP_TIMEOUT`, `BOT_MEMORY`, `BOT_CPUS`, `BOT_TMPFS`, `SANDBOX_IMAGE`, `USE_DOCKER`, `MATCH_ID` | `match.py:31-40`, `runner.py:26-28` | None of these change overlay behaviour. |

Conclusion: in the qualifier Docker sandbox, `POKERBOT_DISABLE_OVERLAY` is guaranteed unset → `_OVERLAY_DISABLED = False` → overlay runs normally. The audit-leakage flag is local-testing hygiene, not a qualifier risk. The variable would only matter if a local benchmarker explicitly set it on the host when running in subprocess fallback mode — that's a tooling concern, not a ship-state concern.

Risk of repackaging from a dirty worktree exceeds the marginal hygiene gain 5 days from qualifier.

## 2. Source provenance

`~/Code/PokerBot/src/bot.py` (main HEAD `050b058`) is the **G0 scaffold stub** (48 LOC, `_safe_fallback` only). The real strategy code that produced the ship artifact lives on `release/v_final-e4b4a8f1` HEAD `a00561c` (an `rsync` mirror of codex's post-X1 dirty working tree from 2026-05-22). The packaged `src/bot.py` byte-content (`d33484ed…`) matches neither current canonical/claude/codex `src/bot.py` exactly — it is a historical snapshot held in the zip and on the release branch.

## 3. Hygiene SHA trail

| Artifact | SHA | Provenance |
|---|---|---|
| `v_hygiene_candidate.zip` (in SUMMARY) | `58a2ec90…` | The documented HYGIENE-1 build: legalizer + clamp + leakage PASS + LBR caps PASS. No promotion. **Not on disk anywhere.** |
| `v_hygiene_candidate.zip` (on disk) | `41768b97…` | Later rebuild of hygiene candidate; still has `decide_blueprint_only`; no `POKERBOT_DISABLE_OVERLAY`. **Undocumented.** |
| `v_hygiene_true.zip` (on disk, newest) | `c3af9d39…` | Most recent "true hygiene" rebuild; no env-var, lacks `decide_blueprint_only`. **Undocumented; SUMMARY is stale.** |

Both undocumented rebuilds are technically cleaner than the ship artifact but lack a passing gauntlet record. Do **not** promote them without a fresh full G1–G11 sweep.

## 4. Diff summary — claude uncommitted src/ vs packaged v_final src/

Claude's uncommitted src/ replaces the X1-era pressure-overlay scaffold with a broader blueprint+refinement stack: eager imports of `src.*`, `get_model().exploit_shift`, inferred position/action-sequence, deep-stack BB-3-bet detection helper, a final `_legalize_action` defensive clamp on every exit, and a `decide_blueprint_only` public entry-point for overlay ablation. The env-var overlay switch is removed. Strategically non-identical to the ship artifact; behaviorally a superset on engine-shaped states (legalizer is a strict refinement) but introduces a new code surface that has not run the qualifier-bar gauntlet at any documented SHA.

## 5. Risks if we ship canonical AS-IS

| Risk | Severity | Mitigation |
|---|---|---|
| `POKERBOT_DISABLE_OVERLAY` env-var in packaged `src/bot.py:39` | LOW | Sandbox does not set it; defaults to `_OVERLAY_DISABLED=False`. Hygiene-only flag. |
| Main HEAD `src/` is scaffold, not ship code | MEDIUM | Do NOT re-package from canonical worktree. Use `release/v_final-e4b4a8f1` for any rebuild. |
| No hygiene/legalizer hardening in ship artifact | LOW | Strategy returns from `decide()` already cover the legal-action contract; `_safe_fallback` short-circuits malformed inputs. |
| Provenance drift between SUMMARY-documented SHA and disk SHA | MEDIUM | Block any promotion until a fresh gauntlet is run against a frozen SHA. |
| Patch-window (2026-06-02) requires `tools/analyze_hand_histories.py` to handle unknown schemas | HIGH | PATCH-WINDOW-PREP work is in-flight in claude worktree as of 2026-05-27T20:30. |

## Recommendation matrix

| Action | Verdict |
|---|---|
| Upload canonical `v_final.zip` to qualifier portal on 2026-06-01 | ✅ GO |
| Re-package `v_final.zip` from any worktree before qualifier | ❌ NO-GO (regression risk) |
| Promote `v_hygiene_true.zip` to `best_green.zip` before qualifier | ❌ NO-GO (undocumented SHA, no gauntlet) |
| Continue PATCH-WINDOW-PREP analyzer hardening | ✅ GO (in-flight) |
| Plan OVERNIGHT-2 for finals overlays | ✅ GO (post-qualifier focus) |
| Reconcile worktree drift post-qualifier | ✅ GO (after 2026-06-01) |

Authored by Orchestrator 2026-05-27 from explore session F76D966A audit. Cross-checked against `~/Code/PokerBot/STATUS.md` 2026-05-22 release-branch entry and `~/Code/PokerBot-claude/consults/2026-05-27-hygiene-1/SUMMARY.md`.
