#!/usr/bin/env python3
"""Deterministically build triage_table.tsv for the 2026-06-01 public-fork drift sweep.

Reads staged inputs (triage_targets.json = 38 targets + baseline_sha + pushed_at;
inputs.json = 05-29 baseline bot inventories + priorInventory) and merges
read-only `gh api` facts gathered live on 2026-06-01 for the repos whose HEAD or
pushed_at moved after the 05-29 baseline. Classification is by BOT-FILE change vs
the 2026-05-29 baseline, NOT raw pushed_at.

No benchmarks were run. No submissions/src/data/ext/tests files were touched.
"""
import json
import os

ART = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(ART, "triage_targets.json")) as f:
    TARGETS = json.load(f)
with open(os.path.join(ART, "inputs.json")) as f:
    INPUTS = json.load(f)

# Live facts gathered 2026-06-01 via read-only `gh api` (HEAD SHA + bot inventory).
# Only repos that needed verification: post-baseline pushes, not-in-fork-api existence
# checks, and new forks. Everything else is classified from staged baseline data.
# Fields: head_sha (current), classification, drifted (bool), changed_bot_files (list),
#         note (one-line what-changed).
LIVE = {
    "vladimirfilip/fullhouse-engine": {
        "head_sha": "0701e08097a2e7ad60b87581ad0b4be70ddbf90d",
        "classification": "DRIFTED_BOT",
        "drifted": True,
        "changed_bot_files": ["bots/vlad/bot.py"],
        "note": "HEAD moved f8b8723->0701e08 ('fix oom in preflop cfr'); vlad/bot.py 30111->46115B; bots/ exploded 6->87 dirs (mirrors of rival bots + neel_v6 sweeps + vlad_gto variants); gto_strategy.npz still ABSENT",
    },
    "Benjamin-Yu-Sheng-Chang/fullhouse-hackathon": {
        "head_sha": "cd841b5e0fc37401f42b8be4acf944cbe8080a72",
        "classification": "NEW_BOT",
        "drifted": True,
        "changed_bot_files": ["bots/cfr/bot.py", "bots/adaptive_hybrid/", "bots/hybrid_mix/", "bots/abstract_value/", "bots/equity_position/", "bots/trap_steal/", "bots/position_bully/", "bots/short_stack_survivor/", "bots/anti_aggro/", "bots/abstract_control/", "bots/abstract_pressure/", "bots/equity_guard/"],
        "note": "HEAD moved 725e898->cd841b5 ('add multiple bots'); went from template-only (0 non-template) to 17 bot dirs incl cfr (8103B, has trainer/), adaptive_hybrid, equity_position, trap_steal",
    },
    "Mehedi-dev-2404/fullhouse-engine": {
        "head_sha": "a30fd7730d715e26baeec343c3d44179fab604ee",
        "classification": "DRIFTED_BOT",
        "drifted": True,
        "changed_bot_files": ["bots/mybot/bot.py"],
        "note": "HEAD moved aa14a35->a30fd77 ('Add Axiom poker bot submission'); mybot/bot.py 25993->36278B (+40%); Axiom landed inside existing mybot path, no new dir; was RED on 05-29",
    },
    "Pav1602/fullhouse-engine": {
        "head_sha": "d512bf428ffcbae7ff036e2a7382dca1396dd2ce",
        "classification": "DRIFTED_BOT",
        "drifted": True,
        "changed_bot_files": ["bots/skantbot7.10/bot.py", "bots/skantbot7.11/bot.py", "bots/skantbot7.12/bot.py", "bots/skantbot7.13/bot.py", "bots/skantbot8/bot.py", "bots/skantbot8.1/bot.py"],
        "note": "HEAD moved 555c84f->d512bf4 (pushed 05-30); canonical default advanced skantbot7.9->7.13 (73385->98324B); new skantbot8 (100483B)/8.1 (100522B); not in fork API, inspected directly",
    },
    "MatusGib/fullhouse-engine": {
        "head_sha": None,
        "classification": "GONE",
        "drifted": False,
        "changed_bot_files": [],
        "note": "gh api repos/MatusGib/fullhouse-engine -> HTTP 404 (deleted or made private); template-only at 05-29 baseline anyway",
    },
    "TobyCoad/fullhouse-engine": {
        "head_sha": "93516f33675d32beaeb3228a554c1323926cd71d",
        "classification": "UNCHANGED",
        "drifted": False,
        "changed_bot_files": [],
        "note": "Exists (not in fork API but live); HEAD == baseline 93516f3, pushed_at 05-16 (pre-baseline). bots/master unchanged. Was RED on 05-29; prior H2H still applies",
    },
    "stoppedtime24/fullhouse-engine": {
        "head_sha": "52951cb7242eb1e3abc638ccd287a08ce37ff34a",
        "classification": "UNCHANGED",
        "drifted": False,
        "changed_bot_files": [],
        "note": "HEAD == baseline 52951cb; mybot/bot.py 13890B unchanged. Prior 05-29 H2H GREEN still applies",
    },
    "Con-TI/fullhouse-engine": {
        "head_sha": "8c66033af4341c74a7f70bae0a1c21d40b73dcb3",
        "classification": "UNCHANGED",
        "drifted": False,
        "changed_bot_files": [],
        "note": "Has bots/mybot (1572B, near-template stub) present since baseline; pushed 05-25 (pre-baseline). Not deep-dived on 05-29 (baseline_sha null). Low threat",
    },
    # New forks confirmed template-only (mirror) on 2026-06-01.
    "gonfdcg/fullhouse-engine": {"head_sha": None, "classification": "MIRROR_NO_BOT", "drifted": False, "changed_bot_files": [], "note": "New fork (05-29); bots/ = template set only (aggressor,mathematician,ref_bot_2,shark,template)"},
    "joshmhc/fullhouse-engine": {"head_sha": None, "classification": "MIRROR_NO_BOT", "drifted": False, "changed_bot_files": [], "note": "New fork; bots/ = template set only"},
    "avj26/fullhouse-engine": {"head_sha": None, "classification": "MIRROR_NO_BOT", "drifted": False, "changed_bot_files": [], "note": "New fork; bots/ = template set only"},
    "Hebobeb0/fullhouse-engine-fork": {"head_sha": None, "classification": "MIRROR_NO_BOT", "drifted": False, "changed_bot_files": [], "note": "New fork; bots/ = template set only"},
    "Akash1Siva/fullhouse-engine-akash": {"head_sha": None, "classification": "MIRROR_NO_BOT", "drifted": False, "changed_bot_files": [], "note": "New fork; bots/ = template set only"},
}

# famadeo + agrawalneel25 are tracked with baselines but were NOT post-baseline pushes
# (pushed 05-22 / 05-12, both <= 05-29). Staged baseline already captured their latest
# state. Both retain a non-template bot -> UNCHANGED (prior H2H still applies).
STAGED_UNCHANGED_WITH_BOT = {
    "famadeo/fullhouse-engine": ("c94dace1c6bf523aa49e9c149d897c6b71a19c5e", "bots/codex_holdem present (88634B + data/model.json); unchanged since baseline; prior 05-29 H2H GREEN"),
    "agrawalneel25/fullhouse-engine": ("071d54c302cbd2d9d5fcc773260e7f5f894c642f", "tracked branch neel-work; bots/neel unchanged; prior 05-29 H2H GREEN (+14.69 scheduled)"),
}


def classify_staged(t):
    """Classify a target that did NOT require a live fetch, from staged data only."""
    full = t["full_name"]
    pushed = t.get("pushed_at")
    prior_bot = (t.get("prior_non_template_bots") or "").strip()
    base = t.get("baseline_sha")

    if full in STAGED_UNCHANGED_WITH_BOT:
        head, note = STAGED_UNCHANGED_WITH_BOT[full]
        return head, "UNCHANGED", False, [], note

    # Has a recorded non-template bot dir at baseline -> UNCHANGED (bot present, no
    # post-baseline push observed).
    if prior_bot:
        return (base, "UNCHANGED", False, [],
                f"bot(s) '{prior_bot}' present at baseline; pushed_at {pushed} (<= 05-29 baseline); no post-baseline push observed")

    # No non-template bot at baseline, pushed at/before baseline -> template mirror.
    return (base, "MIRROR_NO_BOT", False, [],
            f"template-only fork; pushed_at {pushed}; no non-template bot at 05-29 baseline")


rows = []
for t in TARGETS:
    full = t["full_name"]
    base = t.get("baseline_sha")
    pushed = t.get("pushed_at")
    if full in LIVE:
        lv = LIVE[full]
        # GONE repos 404 -> no reachable current head; leave current_head blank.
        if lv["classification"] == "GONE":
            head = ""
        else:
            head = lv["head_sha"] if lv["head_sha"] else (base or "")
        cls = lv["classification"]
        drifted = lv["drifted"]
        changed = lv["changed_bot_files"]
        note = lv["note"]
    else:
        head, cls, drifted, changed, note = classify_staged(t)
        head = head or ""
    rows.append({
        "full_name": full,
        "classification": cls,
        "current_head_sha": head or "",
        "baseline_sha": base or "",
        "drifted_since_baseline": "yes" if drifted else "no",
        "bot_files_changed": str(len(changed)),
        "changed_bot_files": ";".join(changed),
        "_note": note,
        "_pushed_at": pushed or "",
    })

# Sort: drifted/new first (by classification priority), then by pushed_at desc.
PRIO = {"DRIFTED_BOT": 0, "NEW_BOT": 1, "UNCHANGED": 2, "MIRROR_NO_BOT": 3, "GONE": 4}
rows.sort(key=lambda r: (PRIO.get(r["classification"], 9), r["_pushed_at"]), reverse=False)
# stable: within same prio keep most-recent pushed_at first
rows.sort(key=lambda r: (PRIO.get(r["classification"], 9), ), )
# secondary sort by pushed_at desc inside group
from itertools import groupby
final = []
for _, grp in groupby(rows, key=lambda r: PRIO.get(r["classification"], 9)):
    g = sorted(grp, key=lambda r: r["_pushed_at"], reverse=True)
    final.extend(g)
rows = final

cols = ["full_name", "classification", "current_head_sha", "baseline_sha",
        "drifted_since_baseline", "bot_files_changed", "changed_bot_files"]
out_tsv = os.path.join(ART, "triage_table.tsv")
with open(out_tsv, "w") as f:
    f.write("\t".join(cols) + "\n")
    for r in rows:
        f.write("\t".join(r[c] for c in cols) + "\n")

# Counts for the report
from collections import Counter
counts = Counter(r["classification"] for r in rows)
print("WROTE", out_tsv, "rows=", len(rows))
print("COUNTS", dict(counts))
print("DRIFTED:", [r["full_name"] for r in rows if r["classification"] == "DRIFTED_BOT"])
print("NEW:", [r["full_name"] for r in rows if r["classification"] == "NEW_BOT"])
print("GONE:", [r["full_name"] for r in rows if r["classification"] == "GONE"])
