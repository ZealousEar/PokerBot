SHIP

# Ship-lock audit — canonical `submissions/v_final.zip`

Date: 2026-05-29  
Artifact under audit: `submissions/v_final.zip`  
Canonical sha256: `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`

## One-line verdict

**SHIP `submissions/v_final.zip` as-is for the 2026-06-01 qualifier.** Do not rebuild or replace it. The only live caveats were caused by current-main/tool/environment drift, and artifact-bound release-branch rechecks reproduced the locked green evidence.

## Audit scope and invariants

- I did **not** edit, rebuild, copy over, or replace any file under `submissions/`.
- I did **not** run `tools/package.py`.
- I did **not** modify `ext/fullhouse-engine/`.
- I wrote only this audit file under `consult/artifacts/2026-05-29-ship-lock-audit/` and used temporary files under `/private/tmp` to run release-branch verification scripts against the locked zip.
- Ship behavior is inferred from the zip and `release/v_final-e4b4a8f1`, not from current `main` `src/`.

## Evidence table

| Gate | Latest recorded evidence | Live audit result | Verdict |
|---|---|---|---|
| Artifact SHA | `RELEASE_NOTES.md` and `STATUS.md` lock `v_final.zip` + `best_green.zip` to `e4b4a8f1…598`; release branch `a00561c`. | `LC_ALL=C LANG=C shasum -a 256 submissions/v_final.zip submissions/best_green.zip` → both exactly `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`, exit 0. | **PASS** |
| Validator | Release G3 PASS 4/4; A1 PASS 4/4; variance 5/5 PASS. | `python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip` → ✅ PASSED, 4 test states legal, exit 0. | **PASS** |
| Import audit | Release: `0.079s`, `33.8 MB`; A1: `0.097s`, `32.0 MB`; variance mean `0.089s`, `32.12 MB`. | Artifact-bound temp extraction + release import tool: `.venv/bin/python tools/import_audit.py --max-seconds 1.5 --max-mb 400` → `0.064s`, `32.9 MB`, exit 0. Current-main command also exits 0 but only measures scaffold/main drift. | **PASS** |
| Edge cases | Release: `25 passed`; A1: `25 passed`; variance 5/5 PASS. | Artifact-bound temp extraction + release tests: `.venv/bin/python -m pytest tests/edge_cases -x` → `25 passed in 0.18s`, exit 0. Current-main command passes only 4 scaffold tests; not ship-authoritative. | **PASS** |
| Smoke | Release G6 PASS `200/200`, chip delta `+14500`; A2 Docker smoke across 5 opponents/10k hands: 0 errors, p99 ~15–16 ms; variance 5/5 PASS. | Release-branch `smoke_run.py` copy in `/private/tmp` against canonical zip → `[smoke_run] OK`, `200/200`, chip delta `+14500`, errors `{}`, exit 0. Current-main `tools/smoke_run.py` drift gave nonzero solely for early stop `136/200`, chip delta `+10000`, errors `{}`; host `python` 3.14 failed due missing `eval7`. | **PASS via release tool; current-main drift noted** |
| Leakage | Release G7 PASS; A1 leakage PASS; variance 5/5 PASS. | Current and release-branch leakage tools both report zip sha `e4b4a8f1…598` and `audit_strategy_leakage PASS`, exit 0. | **PASS** |
| Exploit / LBR | Release G8 and A1 remediation: real artifact-bound LBR preflop `18.0 mbb/g`, aggregate `7.4 mbb/g`, suite size 20, below caps 100/200. L1 exact run documented `--zip` as unsupported and remediated with `--bot`. | Current-main `tools/exploit_check.py` is a TODO stub, exit 0 but not meaningful. Release-branch `exploit_check.py` copy in `/private/tmp`, run with `--bot submissions/v_final.zip`, reproduced preflop `18.0`, aggregate `7.4`, `exploit_check PASS`, exit 0. | **PASS** |
| Size/layout | Release package validator and notes: root `bot.py`, data under cap, total under cap. | `du -h submissions/v_final.zip` → `28K`; `unzip -l` tail shows `data/*.npz` and total `42354` bytes across 14 files. Validator also enforces layout. | **PASS** |

## Public-saturation evidence

Source: `consult/artifacts/2026-05-28-public-saturation/SUMMARY.md`; artifact-bound paired H2H; rule: GREEN if mean > 0 and CI low > -20, RED if CI high < 0.

| Opponent | Bases | Verdict | Mean bb/100 | 95% CI | Scheduled | Actual | Early-bust | Hero errors | p99 latency | Ship constraint |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| vladimir | 142,242,342,442 | GREEN | +3.70 | [+2.40,+5.00] | 400000 | 20081 | 100.0% | 0 | 0.0399s | No block. |
| famadeo | 142,242 | GREEN | +0.65 | [-1.30,+2.60] | 200000 | 43914 | 99.5% | 0 | 0.0643s | No block. |
| dominic | 142,242 | AMBER | -1.22 | [-3.24,+0.72] | 200000 | 77337 | 95.0% | 0 | 0.0764s | Finals-review input, not qualifier block. |
| neel | 142,242 | GREEN | +14.69 | [+13.50,+15.81] | 200000 | 102276 | 85.8% | 0 | 0.0633s | No block. |

Public saturation does **not** constrain qualifier ship. There is no RED opponent, no hero errors, and the only AMBER cell is small and CI-over-zero.

## Pod-color matrix

Source: `consult/artifacts/2026-05-28-pods/SUMMARY.md`; 400 hands × 100 seeds per pod, local `match.py`, canonical SHA fixed.

| Pod | Seats | Color | p10 | p50 | p90 | Mean | Stdev | Bust rate | Hero errors | p99 decide ms |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C1 | hero, template, aggressor, mathematician, shark, ref_bot_2 | RED | -10000 | -10000 | 13575 | -1513 | 12181 | 63.0% | 0.000% | 8.292 |
| C2 | hero, neel, dominic, famadeo, vladimir, shark | AMBER | -10000 | 3954 | 26732 | 5352 | 14981 | 35.0% | 0.000% | 39.245 |
| C3 | hero, neel, dominic, famadeo, aggressor, mathematician | RED | -10000 | -9637 | 24122 | 638 | 14899 | 50.0% | 0.000% | 65.479 |
| C4 | hero, vladimir, famadeo, template, shark, ref_bot_2 | AMBER | -10000 | 4182 | 26042 | 4866 | 13950 | 32.0% | 0.000% | 65.287 |

## QUAL-PODS RED reconciliation — does this override ship?

**No. QUAL-PODS RED does not override ship-as-is.**

Reasoning:

1. The pod study is a distribution stress estimate, not a functional gate. It recorded `0.000%` hero errors in all four pods and p99 decide latency under 66 ms.
2. RED is defined by median (`p50 <= 0`), not by a statistically established negative expectation. C3 is RED with p50 `-9637` but mean `+638`; C1 has mean `-1513` with stdev `12181` and p90 `+13575`. That is high six-max/bust variance, not a validator/sandbox failure.
3. Stronger artifact-bound gates remain green: release G1–G11, A1 remediation, A2 10k-hand Docker smoke, 5× gauntlet variance, leakage, and real LBR all pass.
4. Public-opponent saturation is 3 GREEN + 1 AMBER, no RED, 0 hero errors. The separate vladimir audit is strongly positive over ~30k hands; famadeo’s earlier deficit collapsed over 50k; pre-qualifier review says “No BLOCKER”.
5. There is no fully gauntletted replacement candidate. Rebuilding or modifying now would violate the artifact lock and introduces more risk than the pod RED removes.

Interpretation: C1/C3 are real warning signs for single-table variance and tough mixed pods. They should inform 2026-06-02 finals/patch-window review, not block the 2026-06-01 qualifier upload.

## STATUS.md vs artifact lock

No artifact-lock conflict found.

- Recent STATUS entries repeatedly preserve `submissions/v_final.zip` and `submissions/best_green.zip` at `e4b4a8f1…598`.
- B8 runner had early RED entries, then later GREEN entries with protected SHA before/after unchanged; the REDs were runner/profile issues, not promotion instructions.
- A1 explicitly records the `--zip` exploit CLI bug and remediates with release CLI `--bot`, ending with `artifact_bound_remediation_failures=0`.
- QUAL-PODS RED records distribution risk and says next action is interpretation; it does not instruct replacement.
- Worktree audit and release notes both say: ship canonical artifact as-is, do not repackage.

## Worktree-vs-packaged drift

Command run:

```bash
LC_ALL=C LANG=C unzip -p submissions/v_final.zip bot.py | LC_ALL=C LANG=C shasum -a 256
LC_ALL=C LANG=C unzip -p submissions/v_final.zip src/bot.py | LC_ALL=C LANG=C shasum -a 256
LC_ALL=C LANG=C shasum -a 256 src/bot.py
```

Results:

| File/content | sha256 |
|---|---|
| Packaged root `bot.py` shim | `b405d54247128d2c946b2689a13ce47b9a610d8adeb0ecbfb965bcface7e883f` |
| Packaged `src/bot.py` strategy | `d33484ed1473406a0951967f8d3796677defea4aae9594d1da24f75c8858d77f` |
| Current main `src/bot.py` | `f38cbb67bc64a0effaf94bcee794e60e809adbf978ed836f4c951da2bc96c2eb` |

These differ. Therefore current `main` `src/bot.py` is not the ship source. Ship behavior must be inferred from `submissions/v_final.zip` and/or `release/v_final-e4b4a8f1` (`a00561c`), not from current `main` source.

## No-go conditions that would flip SHIP to HOLD

Hold upload if any of these occurs before pressing upload:

1. `submissions/v_final.zip` or `submissions/best_green.zip` sha256 differs from `e4b4a8f11f801ecef2eca53629241e83cc9bace8ec74004f19368375f22d9598`.
2. `v_final.zip` and `best_green.zip` differ from each other.
3. Engine validator fails on `submissions/v_final.zip`.
4. Leakage audit finds any strategy-identity hit in the packaged zip.
5. Release-branch LBR check fails caps (`preflop > 100 mbb/g` or `aggregate > 200 mbb/g`) or cannot be run with the real release CLI.
6. A real Docker smoke run against the locked zip shows bot load failure, bot errors, timeouts/OOM, invalid actions, or non-positive chip delta. A current-main smoke false-positive caused solely by early match termination with positive `+10000` chip delta and zero errors is not by itself a no-go; rerun with the release-branch smoke script or the A2-style smoke harness.
7. Any file under `submissions/` has been rebuilt, overwritten, copied over, renamed, deleted, or touched outside an explicit promotion gate.
8. `ext/fullhouse-engine/` has been modified since the green evidence.
9. The upload portal reports a different hash after upload.
10. A new explicit promotion gate fires and selects `MODIFY`; until then, there is no approved replacement artifact.

## Commands for the human to run manually before upload on 2026-06-01

Use the repo `.venv` (Python 3.10) for engine-dependent commands. In this shell, bare `python` may be Python 3.14 and can fail before exercising the bot.

```bash
cd /Users/farhad/Code/PokerBot

# 1. Artifact identity. Both lines must equal the canonical hash.
LC_ALL=C LANG=C shasum -a 256 submissions/v_final.zip submissions/best_green.zip

# 2. Engine-authoritative validator.
.venv/bin/python ext/fullhouse-engine/sandbox/validator.py submissions/v_final.zip

# 3. Packaged leakage audit.
.venv/bin/python tools/audit_strategy_leakage.py --zip submissions/v_final.zip

# 4. Import budget against packaged source, using release import_audit in a temp dir.
tmp=$(mktemp -d /private/tmp/pokerbot_zip_import.XXXXXX)
unzip -q submissions/v_final.zip -d "$tmp"
mkdir -p "$tmp/tools"
git show release/v_final-e4b4a8f1:tools/import_audit.py > "$tmp/tools/import_audit.py"
(cd "$tmp" && /Users/farhad/Code/PokerBot/.venv/bin/python tools/import_audit.py --max-seconds 1.5 --max-mb 400)

# 5. Edge cases against packaged source + release tests.
tmp=$(mktemp -d /private/tmp/pokerbot_zip_edge.XXXXXX)
unzip -q submissions/v_final.zip -d "$tmp"
git archive release/v_final-e4b4a8f1 tests | tar -x -C "$tmp"
(cd "$tmp" && /Users/farhad/Code/PokerBot/.venv/bin/python -m pytest tests/edge_cases -x)

# 6. Real LBR / exploit check with release CLI (--bot, not --zip).
tmp=$(mktemp -d /private/tmp/pokerbot_release_exploit.XXXXXX)
mkdir -p "$tmp/tools" "$tmp/submissions"
git show release/v_final-e4b4a8f1:tools/exploit_check.py > "$tmp/tools/exploit_check.py"
ln -sf /Users/farhad/Code/PokerBot/submissions/v_final.zip "$tmp/submissions/v_final.zip"
(cd "$tmp" && /Users/farhad/Code/PokerBot/.venv/bin/python tools/exploit_check.py --bot submissions/v_final.zip)

# 7. Smoke with the release-branch smoke script, to avoid current-main tool drift.
tmp=$(mktemp -d /private/tmp/pokerbot_release_smoke.XXXXXX)
mkdir -p "$tmp/tools" "$tmp/submissions" "$tmp/ext"
git show release/v_final-e4b4a8f1:tools/smoke_run.py > "$tmp/tools/smoke_run.py"
ln -sf /Users/farhad/Code/PokerBot/submissions/v_final.zip "$tmp/submissions/v_final.zip"
ln -s /Users/farhad/Code/PokerBot/ext/fullhouse-engine "$tmp/ext/fullhouse-engine"
(cd "$tmp" && /Users/farhad/Code/PokerBot/.venv/bin/python tools/smoke_run.py --zip submissions/v_final.zip --hands 200)

# 8. Size/layout sanity.
LC_ALL=C LANG=C du -h submissions/v_final.zip
LC_ALL=C LANG=C unzip -l submissions/v_final.zip | tail -8

# 9. Drift reminder: these are expected to differ; do not repackage from main.
LC_ALL=C LANG=C unzip -p submissions/v_final.zip bot.py | LC_ALL=C LANG=C shasum -a 256
LC_ALL=C LANG=C unzip -p submissions/v_final.zip src/bot.py | LC_ALL=C LANG=C shasum -a 256
LC_ALL=C LANG=C shasum -a 256 src/bot.py
```

Expected key outputs: canonical SHA on both artifacts; validator PASS; leakage PASS; import <1.5 s and <400 MB; 25 edge tests pass; LBR preflop `18.0`, aggregate `7.4`; smoke `200/200`, chip delta `+14500`, errors `{}` when using the release smoke script.

## Explicit warning: forbidden mutating commands

Until an explicit promotion gate fires, these are forbidden:

```bash
python tools/package.py --output submissions/v_final.zip --strict
python tools/package.py --output submissions/best_green.zip --strict
cp <anything> submissions/v_final.zip
cp <anything> submissions/best_green.zip
mv <anything> submissions/v_final.zip
mv <anything> submissions/best_green.zip
rm submissions/v_final.zip
rm submissions/best_green.zip
zip -u submissions/v_final.zip <anything>
unzip -o <anything> -d submissions/
touch submissions/v_final.zip submissions/best_green.zip
```

Read-only commands are acceptable: `shasum`, `unzip -l`, `unzip -p`, validator on the existing zip, import/edge checks in `/private/tmp`, smoke on the existing zip, leakage audit on the existing zip, and release-branch LBR on the existing zip.
