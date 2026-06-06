## 3. Round 1 forensic summary

**Round 1 = Qualifier I (Swiss).** All numbers below measure the **DEPLOYED** bot, which the recon confirms was the *elaborate equity-driven* build, NOT the simple `v_final.zip` (RECON_REPORT.md L5 "Deployed source audited: `PokerBot-claude/src` (elaborate build that actually shipped)"; qual2-patch/FINDINGS.md L11 "deployed bot is the **elaborate equity-driven** version (NOT the simple `v_final.zip`)"). The SIMPLE/DEPLOYED hash→bot lineage table referenced in my assignment (`e4b4a8f1` / `d54640e0`) was **NOT PROVIDED** in this task; I therefore tag every figure as **[DEPLOYED]** with its source path and do not invent a hash mapping.

Two diagnoses exist for the same 6,915-hand dataset; **RECON_REPORT.md (2026-06-03 04:17) supersedes qual2-patch/FINDINGS.md (01:19)** because RECON is chip-exact-validated and FINDINGS' headline figures were a conflation (detailed in §3.4). I lead with RECON and present FINDINGS as the earlier, partly-corrected diagnosis.

### 3.1 Hand-history corpus / manifest (own spot-check of `data/portal_histories/`)
- **56 directory entries, 9.3 MB** (own `ls`/`du` of `data/portal_histories/`). Filenames are stable portal **UUIDs** (e.g. `0c18615c-cb01-4381-8a2b-b906eac65023.json`). The directory also holds the **truncated-fragment filenames** the spec flags — own listing shows `-.json`, `2.json`, `4.json`, `5.json`, `8.json`, `9.json`, `b.json`, `c.json`, and one UUID-fragment `46-a921-dffe25725f2a.json`; these are 27–28-byte stubs (empty payloads), not match data.
- **~16 large files (125 KB–877 KB)** carry real hands; their stems match the recon's "16 matches / 9,058 hands" (RECON_REPORT.md L54). Of these, **12 are Thorp's matches / 6,915 hands** (RECON L67, "exactly matches qual2-patch FINDINGS"). The 12 Thorp file-stems appearing in the CSVs: `0c18615c, 35272026, 3f055acd, 55a52ba6, 5ff29149, 60875d32, b03aa014, d717930b, e2272b43, f5a45e55` plus `18fc0a11` and `c5899b02` (the latter two are showdown-only in `showdown_spots.csv`). `e612f705 / 70ddeaab / ed36423c / f492174e` are additional with-hands field files (the 16-match field set).
- **Reconstruction validation [DEPLOYED, RECON_REPORT.md L56-61]:** showdown revealed-set match **571/571**; `winners` sum == `pot` **9,058/9,058**; non-all-in last-street == board length **8,801/8,801**; per-match net == declared `chip_delta` **11/11** (12th = `d717930b` "Final3", **truncated** — 100 hands stored but declares one bot holding all 60,000 chips; excluded from net aggregates only).

### 3.2 Thorp's own fingerprint & field archetypes [DEPLOYED, RECON_REPORT.md L72-92]
Thorp is an **extreme raise-or-fold outlier**: VPIP **0.49** / PFR **0.48**, **call freq 0.022 (2.2%)**, **AF ~26**, raise freq 0.57, fold 0.40, **bust rate 0.42 (42% of matches)**, **showdown-win 0.62**, big-commit rate 0.011 (RECON L90-92). Field = 74 identities, rule-clustered (RECON L78-82):

| cluster | n |
|---|---|
| nit_tight_passive | 23 |
| TAG | 20 |
| LAG | 9 |
| maniac_boombust | 7 |
| loose_passive_station | 3 |
| insufficient_data (<60 hands) | 12 |

Field is "**aggressive and boom/bust**" (top bots bust 31–64%, RECON L84-87; `qual2-patch/opponents_top25_stats.md`). Note `Bot1` is ambiguous — two distinct UUIDs share that name (RECON L88).

### 3.3 Stack-off / large-pot aggregates [DEPLOYED, RECON_REPORT.md L95-103]
- **211 large-pot hands** (final pot ≥ 5,000); **608 Thorp decisions** logged (`large_pot_decisions.csv`).
- **59 stack-offs** (≥40% start stack): **net −32,041**, **gross loss −104,407**, gross win +72,366, **won 37/59 (63%)**. Signature = wins most big pots but loses *bigger* on losers (asymmetric equity-vs-random tail, not variance).
- **Origin:** postflop-escalation **47 (−8,670)** · preflop-raise **7 (−8,086)** · preflop-flat **2 (−18,961)** · none **3 (+3,676)**. The leak is **overwhelmingly postflop** — the class the `_can_commit` fix gates.

### 3.4 Realization & the FINDINGS reconciliation [DEPLOYED]
- **Equity at commit street by outcome (RECON L113, `showdown_spots.csv`, 115 showdown hands):** WON mean **0.906**, LOST mean **0.059** → on losses Thorp was near-drawing-dead *when he committed*; this is committing dominated, not getting unlucky.
- **Raise-or-fold under-realization (RECON L117-121):** call ~2.2% forgoes pot-control / check-call lines on the medium/marginal class. Fold-side magnitude is **inferred from frequencies** — Thorp's folded cards are never revealed, so over-fold is not directly measurable (RECON L40-42, L121).
- **RECON corrects FINDINGS on TWO fronts (same bot, same dataset, different metric defs):**
  - **(a) The −81k headline.** FINDINGS.md L10 reported "**16 all-ins, 12% won, net −81,149**; 6 deep stack-offs = −73,434". RECON L105-110: chip-exact reconstruction shows **literal all-ins are only 12–13 hands, 38–42% won, net −18k to −29k**; the −81k/−96k magnitude is the **≥40%-stack commitment class measured as GROSS loss**, and "12% won" is not reproducible (Thorp wins 42% of true all-ins, 63% of ≥40% commits). Direction (postflop stack-off discipline) right; magnitude overstated by conflation.
  - **(b) The profile numbers.** FINDINGS.md L9: **AF 5.45, BUST 56%, CALL 6.4%, SCOOP 0%**. RECON: **AF ~26, bust 42%, call 2.2%**. Treat RECON's as authoritative (validated dataset); the gaps are metric-definition/subset artifacts.

### 3.5 Illegal actions / timeouts / crashes / warmup / validator (Round 1 play)
- **Hero errors = 0.** Source: qual2-patch/FINDINGS.md L10 — "`bot_errors = 0` (**not crashes**)." No illegal-action / timeout / warmup-error count is recorded *for Qualifier I live play* in either artifact beyond this. RECON_REPORT.md does not contradict it. **NOT AVAILABLE:** a per-hand timeout/validator-warning log for Round 1 (the recon replays portal `action_log`, which records no engine-side error events).
- The **smoke 200/200 (0 errors), edge 48/48, LBR preflop 32.1 / aggregate 81.2 mbb/g, validator 4/4** figures (FINDINGS.md L23; RECON L162-164) measure the **v_qual2 patch-candidate pre-upload gauntlet**, NOT Round 1 play — kept separate by design.

### 3.6 Failure-class spots [DEPLOYED]
- **Overbluff / over-commit on wet & paired boards** (the proven leak): RECON's named worst hands are postflop jams drawing dead — `2sKd` two-pair into a made straight (−11,500), `JhJs` into a flush board, `QhAc` two-pair into a set (RECON L103). Mechanism (FINDINGS L11): `eq>=0.80 → raise current_bet*3` where `eq = hand_strength = equity vs RANDOM`; on range-capped boards this re-raised into full-stack jams at ~12% real equity.
- **Multiway/wet-board:** stack-offs are essentially all heads-up at commit (every `showdown_spots.csv` stack-off row is `n_villains=1`); the wet-board failures are HU flush/straight/paired boards (see table §3.7).
- **3-bet-pot / blind-defense:** preflop-flat origin is the smallest count (2 hands) but the **worst net (−18,961)** — both are deep flats that bloated postflop (RECON L99-101; e.g. `e2272b43#56` JJ flat vs AA, `0c18615c#555` flat vs straight). The preflop audit found **no preflop/sizing threshold bug** (range-gated; all-in tag limited to `{AA,KK,AKs,AKo}` at `len(raises)>=3`; sizing caps at stack) — RECON §4 / PREFLOP_AUDIT.md.
- **River decision failures:** the dominant pattern — most large losers commit the bulk on the river (`stackoff_decisions.csv` shows the largest `river_invested` slices on the losing rows, e.g. `3f055acd#223` river 8,129; `0c18615c#81` river 4,630).
- **Overfold:** inferred only (frequencies), not directly measurable (see §3.4).

### 3.7 MANDATORY — 10 most diagnostic hands (individual)
Built by my own row-read of `showdown_spots.csv` (the only CSV with `thorp_cards` + `villain_cards` + `equity_at_commit`), cross-referenced to `stackoff_decisions.csv` for the **action / `went_all_in` / commit-street** fields. **Equity semantics:** river-commit equity is *realized* (all five cards out → 0.0/0.5/1.0); preflop/turn-commit equity is a genuine probabilistic all-in equity. Hands 1–3 are the RECON-named worst trio (RECON L103) — confirmed here against my own CSV read; hands 4–10 are my own selection of the highest-signal remaining spots.

| # | match/hand | board | Thorp cards | villain | commit street | Thorp action (stackoff CSV) | eq@commit | chip Δ | note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `3f055acd` #223 | `Kh Qs Tc Td Ah` | 2s Kd (two pair) | Jh As (Broadway) | river | river RAISE, not all-in (`went_all_in=0`, commit_frac 0.584) | **0.0** (realized) | **−11,500** | RECON worst loss; biggest single stack-off loss |
| 2 | `0c18615c` #81 | `8d Ah 2h 7c 3h` (3-flush) | Jh Js | Ad Qc | river | river RAISE, not all-in (`went_all_in=0`, frac 0.567) | **0.0** (realized) | **−7,988** | RECON-named "JhJs into flush board" |
| 3 | `3f055acd` #170 | `Qd Tc As 3h 8d` | Qh Ac (two pair) | Qs Qc (set) | river | river RAISE, not all-in (`went_all_in=0`, frac 0.53) | **0.0** (realized) | **−5,650** | RECON-named "QhAc two-pair into a set" |
| 4 | `b03aa014` #75 | `5d 2c 6s Js Th` | Kd Ad (A-high) | Td Ts (set) | river | river RAISE, not all-in (`went_all_in=0`, frac 0.619) | **0.0** (realized) | **−7,863** | own pick: jam with no pair, no draw |
| 5 | `55a52ba6` #149 | `Kh Ah 8s 9h Ac` (3-flush) | Td 6h (nothing) | 6s 6c | river | river RAISE, not all-in (`went_all_in=0`, frac 0.652) | **0.0** (realized) | **−3,710** | own pick: stack-off with air on wet board |
| 6 | `e2272b43` #56 | `As Ad 2h 8d 8h` | Jh Js | Ah Ks | preflop | preflop ALL-IN flat (`went_all_in=1`, frac 1.0, **preflop-flat**) | **0.592** (prob.) | **−8,350** | 3-bet-pot cooler; bust hand; flat vs AA |
| 7 | `0c18615c` #555 | `7s 3c Ac 4c 2s` | Ts 9c | Jd Th (straight) | preflop | preflop ALL-IN flat (`went_all_in=1`, frac 1.0, **preflop-flat**) | **0.262** (prob.) | **−10,611** | worst preflop-flat; bust; dominated all-in |
| 8 | `35272026` #143 | `9h 8s Kc Ah 7h` | Ks Qs | Ac Ad | preflop | preflop ALL-IN raise (`went_all_in=1`, frac 1.0, **preflop-raise**) | **0.162** (prob.) | **−8,966** | bust; KsQs jam into AA |
| 9 | `5ff29149` #100 | `4d 3s Tc 7d Ts` | Ad Ah | Qs Qh | river | river RAISE, not all-in (`went_all_in=0`, frac 0.546) | **1.0** (realized) | **+11,488** | biggest GAIN; correct nut stack-off (overpair holds) |
| 10 | `5ff29149` #43 | `Jd 3d 5c 4d 8c` | Qs Ac | Qc 2c | preflop | preflop ALL-IN raise (`went_all_in=1`, frac 1.0, **preflop-raise**) | **0.728** (prob.) | **+9,110** | 2nd-biggest GAIN; flips to 1.0 by river |

Field notes: `showdown_spots.csv` has **no action-verb column** — "Thorp action" is reconstructed from `stackoff_decisions.csv` (`went_all_in`, `origin`, per-street invested). The marquee **losses #1–#5 were river RAISES to showdown, NOT literal all-ins** (`went_all_in=0`), which is exactly the over-confident `current_bet*3` re-raise mechanism and the empirical basis for RECON's "−81k ≈ gross-loss-of-commit-class, not 16 literal all-ins" correction (§3.4). Biggest single GAIN = `5ff29149#100` (+11,488); biggest single LOSS = `3f055acd#223` (−11,500) — a near-symmetric pair that captures the whole thesis: same commit behaviour, opposite equity.
