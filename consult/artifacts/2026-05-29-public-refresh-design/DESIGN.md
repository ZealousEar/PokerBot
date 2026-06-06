# Public-opponent H2H refresh design — 2026-05-29

Status: **DESIGN ONLY**. No benchmark, H2H, packaging, or saturation command was run while writing this file.

## Scope and hard invariants

- Canonical hero artifact: `submissions/v_final.zip`.
- Required sha256: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
- Do not modify, rebuild, repackage, copy over, or replace `submissions/v_final.zip` or `submissions/best_green.zip`.
- Do not edit `src/`, `tools/`, `submissions/`, or `ext/`.
- Do not modify `ext/public-bots/`; public-bot zips, logs, and JSON outputs should be created only under:
  `consult/artifacts/2026-05-29-public-refresh-design/run/`.
- `tools/public_saturation.py` is the right methodology runner because it already records:
  scheduled-hand bb/100, actual-hand bb/100, hero/opponent errors, p99 decide latency, early-bust rate, public-bot packaging sha, and the existing GREEN/AMBER/RED rule.
- Do **not** run `tools/public_saturation.py --all` directly: the current script hardcodes `ARTIFACT_DIR = consult/artifacts/2026-05-28-public-saturation`, so a refresh must use an artifact-local wrapper or monkeypatch that redirects outputs to the 2026-05-29 design/run directory without editing repo tools.

## Prior evidence being refreshed

From `consult/artifacts/2026-05-28-public-saturation/SUMMARY.md`:

| Opponent | Verdict | Mean bb/100 scheduled | 95% CI | Half-width | Scheduled | Actual | Hero errors | Hero p99 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| vladimir | GREEN | +3.70 | [+2.40, +5.00] | 1.30 | 400000 | 20081 | 0 | 0.0399s |
| famadeo | GREEN | +0.65 | [-1.30, +2.60] | 1.95 | 200000 | 43914 | 0 | 0.0643s |
| dominic | AMBER | -1.22 | [-3.24, +0.72] | 1.98 | 200000 | 77337 | 0 | 0.0764s |
| neel | GREEN | +14.69 | [+13.50, +15.81] | 1.15 | 200000 | 102276 | 0 | 0.0633s |

Only **dominic** is unresolved. This refresh should therefore be dominic-focused. Re-running GREEN opponents has low ship-decision value and increases cost/noise.

## Hand-count design

Goal: tighten dominic's current scheduled-hand CI half-width by at least 50%.

- Current dominic evidence: `200000` scheduled hands, half-width `1.98` bb/100.
- CI half-width scales approximately as `1 / sqrt(N)`.
- Minimum total scheduled hands for half-width `<= 0.99`: `200000 * (1.98 / 0.99)^2 = 800000`.
- Designed refresh: `4` predeclared seed bases × `250000` scheduled hands/base = `1000000` scheduled hands.
- Expected half-width: `1.98 * sqrt(200000 / 1000000) ≈ 0.89` bb/100, about a `55%` reduction.
- Use `match_len=500`; each seed-pair is two seat orientations, so:
  `seed_count = hands / (2 * match_len) = 250000 / 1000 = 250` seed-pairs per base.
- Predeclared bases: `42, 142, 242, 342`.
- Seed stride should stay `1000`, matching `public_saturation.py`'s existing base schedule: seed `= base + k * seed_stride`.

Primary metric remains **scheduled-hand bb/100**, matching existing public-saturation policy. Actual-hand bb/100 must be reported separately because early busts distort actual-hand normalization.

## Runner contract for the execution agent

Use an artifact-local wrapper, e.g.:

`consult/artifacts/2026-05-29-public-refresh-design/run_public_refresh.py`

The wrapper should not edit repo files. It should import `tools.public_saturation` and set:

- `public_saturation.ARTIFACT_DIR = Path("consult/artifacts/2026-05-29-public-refresh-design/run").resolve()`
- `public_saturation.HERO_ZIP = Path("submissions/v_final.zip").resolve()`

It should expose these execution-facing flags:

- `--opponent`
- `--paired-seed-base` — maps to `public_saturation.run_base(..., base=...)`
- `--seed-count` — validates the intended number of seed-pairs
- `--hands` — scheduled hands per base; require `hands == seed_count * 2 * match_len`
- `--match-len`
- `--seed-stride`
- `--artifact-dir`
- `--force` only for restarting incomplete outputs in the new artifact directory
- `--aggregate` to load the predeclared matrix and render `RESULTS.json` / `SUMMARY.md`

If the execution agent instead runs `tools/public_saturation.py` directly, it must first isolate output redirection in an artifact-local copy/monkeypatch. Direct use of the checked-in script as-is will write into the 2026-05-28 saturation directory and should be treated as operator error.

## Exact command matrix

Run sequentially unless the human explicitly accepts latency contamination from parallel CPU contention. Sequential runtime gives cleaner p99 latency.

Preflight guard, before any H2H:

```bash
cd /Users/farhad/Code/PokerBot
ART=consult/artifacts/2026-05-29-public-refresh-design/run
EXPECTED_SHA=e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598
# Verify manually or with shasum before execution; abort if this differs.
# shasum -a 256 submissions/v_final.zip
```

Dominic refresh matrix:

```bash
python consult/artifacts/2026-05-29-public-refresh-design/run_public_refresh.py \
  --artifact-dir consult/artifacts/2026-05-29-public-refresh-design/run \
  --opponent dominic --paired-seed-base 42 --seed-count 250 --hands 250000 \
  --match-len 500 --seed-stride 1000

python consult/artifacts/2026-05-29-public-refresh-design/run_public_refresh.py \
  --artifact-dir consult/artifacts/2026-05-29-public-refresh-design/run \
  --opponent dominic --paired-seed-base 142 --seed-count 250 --hands 250000 \
  --match-len 500 --seed-stride 1000

python consult/artifacts/2026-05-29-public-refresh-design/run_public_refresh.py \
  --artifact-dir consult/artifacts/2026-05-29-public-refresh-design/run \
  --opponent dominic --paired-seed-base 242 --seed-count 250 --hands 250000 \
  --match-len 500 --seed-stride 1000

python consult/artifacts/2026-05-29-public-refresh-design/run_public_refresh.py \
  --artifact-dir consult/artifacts/2026-05-29-public-refresh-design/run \
  --opponent dominic --paired-seed-base 342 --seed-count 250 --hands 250000 \
  --match-len 500 --seed-stride 1000
```

Aggregate after all four base runs finish:

```bash
python consult/artifacts/2026-05-29-public-refresh-design/run_public_refresh.py \
  --artifact-dir consult/artifacts/2026-05-29-public-refresh-design/run \
  --aggregate --opponent dominic --paired-seed-bases 42,142,242,342
```

Equivalent current-tool parameter mapping, for audit only:

| Requested flag | `tools/public_saturation.py` equivalent |
|---|---|
| `--paired-seed-base B` | `--base B` |
| `--seed-count 250` | implied by `--hands 250000 --match-len 500` |
| `--hands 250000` | same scheduled-hand budget per base |
| `--match-len 500` | same |
| `--seed-stride 1000` | same |

Do not use `tools/h2h.py` for this refresh unless it is only a secondary diagnostic: it lacks scheduled-vs-actual reporting, public-bot packaging, p99 latency capture, and the public-saturation verdict policy.

## Runtime estimate

Observed dominic saturation timing from 2026-05-28:

| Base | Scheduled | Start | Done | Wall |
|---:|---:|---:|---:|---:|
| 142 | 100000 | 01:08:38Z | 01:20:02Z | ~11.4 min |
| 242 | 100000 | 01:20:02Z | 01:32:29Z | ~12.5 min |

Projected for the designed refresh:

- Per base: `250000 / 100000 * 11.4–12.5 min ≈ 28.5–31.3 min`.
- Four bases sequential: `~114–125 min`.
- Add packaging/aggregation/slack: plan for `~2.0–2.25 h` wall-clock.
- Parallel execution could reduce wall-clock but should be avoided if p99 latency is a decision input; CPU contention may inflate p99 and create false latency concerns.

## Result template for the executing agent

The execution agent should fill this in as `consult/artifacts/2026-05-29-public-refresh-design/run/SUMMARY.md` or a sibling report. Do not append `STATUS.md` unless the orchestrator explicitly asks.

```markdown
# Public-opponent refresh results — 2026-05-29

- Design: `consult/artifacts/2026-05-29-public-refresh-design/DESIGN.md`
- Hero artifact: `submissions/v_final.zip`
- Hero sha256 observed: `<fill>`
- Expected sha256: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`
- Runner: artifact-local wrapper over `tools/public_saturation.py`
- Match policy: paired seeds, two seat orientations per seed, `match_len=500`, `seed_stride=1000`
- Verdict rule: GREEN = mean > 0 and CI low > -20; RED = CI high < 0; AMBER = mixed.

## Aggregate

| Opponent | Bases | Verdict | Mean scheduled bb/100 | 95% CI | Half-width | Half-width reduction vs 1.98 | Actual bb/100 | Scheduled hands | Actual hands | Early-bust rate | Hero errors | Opp errors | Hero p99 latency | Hero max latency |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dominic | 42,142,242,342 | `<fill>` | `<fill>` | `[<fill>, <fill>]` | `<fill>` | `<fill>%` | `<fill>` | `<fill>` | `<fill>` | `<fill>%` | `<fill>` | `<fill>` | `<fill>s` | `<fill>s` |

## Per-base

| Opponent | Base | Verdict | Mean scheduled bb/100 | 95% CI | Half-width | Actual bb/100 | Scheduled | Actual | Early-bust rate | Hero errors | Opp errors | Hero p99 latency | Log |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| dominic | 42 | `<fill>` | `<fill>` | `[<fill>, <fill>]` | `<fill>` | `<fill>` | 250000 | `<fill>` | `<fill>%` | `<fill>` | `<fill>` | `<fill>s` | `dominic_s42.log` |
| dominic | 142 | `<fill>` | `<fill>` | `[<fill>, <fill>]` | `<fill>` | `<fill>` | 250000 | `<fill>` | `<fill>%` | `<fill>` | `<fill>` | `<fill>s` | `dominic_s142.log` |
| dominic | 242 | `<fill>` | `<fill>` | `[<fill>, <fill>]` | `<fill>` | `<fill>` | 250000 | `<fill>` | `<fill>%` | `<fill>` | `<fill>` | `<fill>s` | `dominic_s242.log` |
| dominic | 342 | `<fill>` | `<fill>` | `[<fill>, <fill>]` | `<fill>` | `<fill>` | 250000 | `<fill>` | `<fill>%` | `<fill>` | `<fill>` | `<fill>s` | `dominic_s342.log` |

## Carry-forward public cells

| Opponent | Source | Verdict | Mean scheduled bb/100 | 95% CI | Note |
|---|---|---|---:|---:|---|
| vladimir | `2026-05-28-public-saturation`; plus separate vladimir consolidated audit | GREEN | +3.70 scheduled saturation; +119.78 actual-h2h audit | [+2.40,+5.00] scheduled; [+98.78,+141.08] actual audit | Not rerun; already resolved. |
| famadeo | `2026-05-28-public-saturation` | GREEN | +0.65 | [-1.30,+2.60] | Not rerun. |
| neel | `2026-05-28-public-saturation` | GREEN | +14.69 | [+13.50,+15.81] | Not rerun. |

## Operator notes

- Did any command write outside `consult/artifacts/2026-05-29-public-refresh-design/run/`? `<yes/no; explain>`
- Was `submissions/v_final.zip` sha verified unchanged before and after? `<yes/no; hashes>`
- Were `submissions/best_green.zip`, `src/`, `tools/`, or `ext/` modified? `<yes/no; must be no>`
- Any stdout noise or public-bot packaging anomaly? `<fill>`
```

## Decision rule for B10 finals recommendation

Baseline B10 recommendation remains: **ship qualifier `v_final.zip` as-is for finals unless patch-window evidence promotes a fully verified alternate**.

This refresh should **not** change B10 under any normal statistical outcome near the current dominic result. In particular:

- dominic becomes GREEN: confidence improves; no artifact or recommendation change.
- dominic remains AMBER: no recommendation change.
- dominic becomes a small RED only because the tightened CI excludes zero around a small loss, e.g. mean between `0` and `-5` scheduled bb/100: record the public-bot weakness, but no B10 change.

Reopen B10 triage only on a hard RED:

1. **Artifact/runner integrity RED**: hero sha mismatch, any hero errors/timeouts, max decide latency at or above the 2s engine limit, or p99 latency implausibly near the limit (use `>=1.5s` as an operator warning threshold). This is not a strategy signal; it means the refresh setup or artifact assumptions are broken and must be investigated.
2. **Strategic RED large enough to matter**: dominic aggregate over at least `800000` scheduled hands has scheduled-hand mean `<= -10 bb/100` and `ci_high < -5 bb/100`, with actual-hand bb/100 also materially negative rather than an early-bust normalization artifact. This should trigger a finals projection rerun with a dominic downside prior.
3. **Catastrophic public-bot RED**: scheduled-hand mean `<= -20 bb/100` and `ci_high < -10 bb/100`. Treat this as hard evidence that the current public-opponent risk model is stale.

Practical assessment: a B10-changing strategic RED is unlikely given the current dominic mean is only `-1.22` scheduled bb/100. If the only goal is deciding whether to ship, the cost-benefit favors **skipping execution**. Execute only if the human wants to close the public-saturation AMBER label before ship lock.

## Risk / cost-benefit

### Benefits

- Converts the only remaining public-saturation AMBER cell into a tighter GREEN/AMBER/RED classification.
- Adds fresh hero-error and p99-latency evidence against dominic without touching the artifact.
- Uses paired seeds and two seat orientations, reducing card/seat variance.
- Reports scheduled and actual bb/100 separately, preserving the early-bust signal.

### Costs / risks

- Roughly `2.0–2.25 h` sequential wall-clock for information that is unlikely to change B10.
- Directly running checked-in `tools/public_saturation.py` risks polluting the 2026-05-28 evidence directory because of the hardcoded artifact path.
- A tiny statistically significant dominic loss may create a scary RED label without changing expected finals EV; magnitude matters.
- Public H2H is not the finals game: finals are bracketed and broader than one public dominic matchup.
- Actual-hand bb/100 can look extreme under early busts; scheduled-hand bb/100 is the policy metric.
- Parallelizing runs can distort latency measurements, so sequential execution is preferred if p99 is considered evidence.

## Recommendation

Do **not** run this refresh for ship/no-ship decision-making. The current evidence already supports ship-as-is unless a hard RED appears. If the human wants optional confidence-building, run the dominic-only 1M scheduled-hand matrix above and treat it as an evidence-label refresh, not a promotion gate.
