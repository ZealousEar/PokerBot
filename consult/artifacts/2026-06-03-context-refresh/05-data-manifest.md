## 5. Data/artifact manifest

Lineage tags used below: **SIMPLE e4b4a8f1** = qualifier-locked artifact (`best_green.zip` ≡ `v_final.zip`, identical sha256). **DEPLOYED d54640e0** = Qualifier-II patch (`v_qual2_ship_d54640e0.zip`), uploaded to portal 2026-06-03 per `STATUS.md:632`.

All sizes/sha256/shapes/gitignore/load-path facts below were harvested directly from disk in the main worktree (`shasum -a 256`, `git check-ignore`, `numpy.load`, `unzip -l`); GROUND TRUTH pre-fetch is corroborated and, where it diverges from current disk state, the divergence is flagged in the Notes.

### 5.1 `data/` manifest

| File | Size | sha256 (prefix) | npz keys → shape (dtype) | Provenance (`metadata`) | Git state | Loaded by which runtime file / how |
|---|---|---|---|---|---|---|
| `data/preflop_blueprint.npz` | 2,147 B | `74f30511…` | `hands`(169,)`<U3`; `scores`(169,)`int16`; `pair`(169,)`bool`; `suited`(169,)`bool`; `high_rank`(169,)`int8`; `low_rank`(169,)`int8`; `metadata`(3,)`<U80` | `deterministic_preflop_blueprint`; `source=Pluribus-Brown-Sandholm-2019,MCCFR-Lanctot-2009`; **`requested_iters=0`** | UNTRACKED — `.gitignore:39 data/*.npz` | **NONE.** See §5.3 — vestigial. |
| `data/flop_buckets.npz` | 582 B | `df32f635…` | `bucket_ids`(64,)`int16`; `metadata`(2,)`<U80` | `buckets=64`; `deterministic_texture_hash` | UNTRACKED (`.gitignore:39`) | **NONE.** See §5.3. |
| `data/flop_strategy.npz` | 17,029 B | `d3f8774d…` | `hand_bin_ids`(32,)`int16`; `strategy`(64,32,3)`float32`; `metadata`(2,)`<U80` | `buckets=64`; `hand_bins=32` | UNTRACKED (`.gitignore:39`) | **NONE.** See §5.3. |
| `data/portal_histories/` (dir, 56 `*.json`) | ~9.1 MB on disk; **only 18 are real** (>30 B), 38 are failed-download stubs | — | top-level dict keys: `match_id, tournament, round, status, started_at, completed_at, n_hands_target, seed, bots[], hands[]` | n/a | UNTRACKED dir (`?? data/portal_histories/`) | n/a — finals-patch corpus, not a runtime blueprint. See §5.4. |
| `data/.gitkeep` | 0 B | — | — | — | tracked | n/a |

Data-npz total = 2,147 + 582 + 17,029 = **19,758 B (~19.3 KB)**, far under the 200 MB `data/` cap.

### 5.2 `submissions/` manifest

| File | Size | sha256 (prefix) | Lineage tag | Git state | Notes |
|---|---|---|---|---|---|
| `v_qual2_ship_d54640e0.zip` | 18,492 B | `d54640e0…` | **DEPLOYED d54640e0** | UNTRACKED — `.gitignore:36 submissions/*.zip` | Live qualifier-II artifact. sha256 matches `STATUS.md:632` exactly. mtime Jun 3 06:48. |
| `best_green.zip` | 28,208 B | `e4b4a8f1…` | **SIMPLE e4b4a8f1** | UNTRACKED (`.gitignore:36`) | Read-only (`-r--r--r--`). Byte-identical sha to `v_final.zip`. |
| `v_final.zip` | 28,208 B | `e4b4a8f1…` | **SIMPLE e4b4a8f1** | UNTRACKED (`.gitignore:36`) | Read-only. ≡ `best_green.zip`. |
| `v_final_reaudit.zip` | 28,208 B | (== e4b4a8f1 by size) | SIMPLE (apparent) | UNTRACKED | Same size as SIMPLE; sha not re-hashed this pass. |
| `v_final_pre_x1.zip` | 28,534 B | NOT RUN | other | UNTRACKED | Pre-X1 snapshot. |
| `v3_hardened.zip` | 28,110 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `v2_postflop.zip` | 28,110 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `v1_blueprint.zip` | 9,289 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `v0_wired.zip` | 5,682 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `v0_scaffold.zip` | 5,098 B | NOT RUN | other | UNTRACKED | Gate snapshot. |
| `.gitkeep` | 0 B | — | — | tracked | — |
| `.DS_Store` | 6,148 B | — | — | UNTRACKED | macOS cruft. |

DEPLOYED zip internals (`unzip -l`): `bot.py`(654 B root shim) + `src/*.py`(8 modules) + `data/.gitkeep`(0 B). **The shipped zip bundles NO npz** — its `data/` holds only the empty `.gitkeep`. Total uncompressed 52,234 B; `bot.py` 654 B (≪ 5 MB cap); whole zip 18 KB (≪ 250 MB total cap).

### 5.3 Which runtime file loads each npz, and how — RESOLVED: none

The assignment expected a cross-reference `preflop_lookup.py → preflop_blueprint.npz` and `postflop.py → {flop_buckets,flop_strategy}.npz`. Direct reading of both the working tree and the DEPLOYED zip shows **no such load path exists in either**:

- **Working tree** `src/preflop_lookup.py` (24 lines) and `src/postflop.py` (25 lines) are **stubs**. Loaders are nulled with TODOs:
  - `preflop_lookup.py:17-18` — `# TODO (G2): load blueprint eagerly here.` / `_blueprint = None`; `lookup(...)` returns `None` (`:24`).
  - `postflop.py:16-18` — `# TODO (G3): load flop_buckets.npz and flop_strategy.npz at import.` / `_flop_buckets = None` / `_flop_strategy = None`; `decide_postflop` returns check/fold placeholder.
  - `_DATA_DIR` is computed (`BOT_DATA_DIR` env → fallback) in both, but never used to `np.load`.
- **DEPLOYED zip** `src/preflop_lookup.py` (4,531 B — a *real* impl, unlike the working-tree stub) loads no npz: `grep` for `np.load|.npz|BOT_DATA_DIR` returns nothing; its docstring states *"Heuristic blueprint (per solver policy — hand-tuned tables ship before MCCFR training)"* and it imports ranges from `src.ranges` (pure Python: `OPEN_RANGES`, `THREEBET_VS_OPEN`, …). The shipped `postflop.py` (8,656 B) likewise has no npz load.
- A repo-wide check confirms `np.load`/`.npz` appears **only** in the two stub files' TODO comments; `src/equity.py` and the shipped `src/` tree contain zero npz loads.

**Conclusion:** `data/*.npz` are **vestigial scaffolding** from the original G2/G3 blueprint plan (`CLAUDE.md`: MCCFR preflop / CFR+ flop buckets). `preflop_blueprint.npz` even records `requested_iters=0` (never trained). Neither bot in the lineage consumes them; the DEPLOYED bot's strategy is the hand-tuned tables in `src/ranges.py`. Package-size impact of the npz is therefore moot for the shipped artifact (it bundles none) and negligible (~19 KB) for the working tree.

### 5.4 Notes / flagged gaps

**(a) Artifact-preservation gap — UPDATED vs GROUND TRUTH (partly resolved, residual remains).**
GROUND TRUTH stated the DEPLOYED bot d54640e0 is *not* preserved in `submissions/` (only `/tmp/v_ship.zip`, now gone). **That is now stale.** On disk, `submissions/v_qual2_ship_d54640e0.zip` (mtime Jun 3 06:48) exists and its sha256 is exactly `d54640e081eb6d1113ab70238c3b6f37e3d8457898b9e80cdc28d7c2a71f4421` — byte-for-byte the live artifact per `STATUS.md:632`. So the binary IS preserved locally. **Residual gap:** it is **git-untracked** (`.gitignore:36 submissions/*.zip`; `git ls-files` empty; no commit history). Preservation is local-disk-only; a fresh clone or disk loss would still lose the DEPLOYED artifact. Same untracked status applies to the SIMPLE e4b4a8f1 zips.

**(b) `data/portal_histories/` — incomplete/partially-failed download confirmed.**
Of 56 `*.json`, **38 are failed-download stubs** (27–28 B) containing `{"error":"Sign in required"}` or `{"error":"Match not found"}`, not poker data. Only **18 files are real** (>30 B; up to 876 KB). Nine filenames are **truncated UUID fragments** — `-.json`, `2.json`, `4.json`, `5.json`, `8.json`, `9.json`, `b.json`, `c.json`, and `46-a921-dffe25725f2a.json` (a UUID mid-slice) — symptomatic of a broken download/rename loop that split UUIDs and persisted auth-error response bodies as files. *(Note: the Read tool and `cat` are intercepted on these paths, returning the same `{"error":"Sign in required"/"Match not found"}` strings; the file contents were read via `python json.load`, which is the authoritative source for the schema below.)*

**Schema (top-level + nested `hands[]`), documented not dumped.** Full file e.g. `c72169ca-…json` (a `status:"failed"` match, `hands:[]`) and `0c18615c-…json` (`status:"complete"`, `n_hands_target:800`, 556 hands actual):
- Top level: `match_id, tournament, round, status, started_at, completed_at, n_hands_target, seed, bots[], hands[]`.
- `bots[]` element: `bot_id, bot_name, seat, final_stack, chip_delta` (+ `bot_errors[]` on some). `"Thorp"` appears as a competing bot.
- `hands[]` element: `hand_num, street_ended, pot, community_cards[], action_log[], revealed_cards{}, winners[], my_decisions[]`.
  - `action_log[]` element: `seat, action, amount`.
  - `winners[]` element: `amount, bot_id`.

This corpus is the basis for the finals-patch priors (`tools/analyze_hand_histories.py` → `data/finals_priors.npz` per `CLAUDE.md` patch-window policy); the high stub/fragment ratio means the on-disk download is **partial** and should be treated as incomplete for prior-fitting. STATUS.md (`:638`) records a reconstruction over "16 matches / 9,058 hands" / "Thorp corpus = 12 matches / 6,915 hands" — implying a more complete pull was processed elsewhere than what currently sits in `data/portal_histories/`.
