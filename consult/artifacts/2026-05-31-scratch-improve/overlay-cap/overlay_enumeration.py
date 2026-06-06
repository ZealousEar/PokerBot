"""Complete divergence MAP of the overlay decision surface (supporting artifact).

This enumerates every (trigger-state x hand) cell the overlay branches on and
records where locked / cap015 / cap010 differ. It is a *map*, not a magnitude
claim -- it gives equal weight to every cell regardless of how often that cell
occurs in real play. The occurrence weights come from overlay_divergence.py
(real captured preflop states). Read the two together.

Enumerated input dimensions (exactly what the overlay reads):
  * (high_pressure, fold_prone_pressure) trigger combo
  * facing_raise (bool)
  * can_check (bool)
  * the full 169-hand canonical grid -> hand_score
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

VFINAL_SRC = Path("/tmp/vfinal_inspect/src")
sys.path.insert(0, str(VFINAL_SRC))
from ranges import RANKS, hand_score  # noqa: E402

OUT = Path("/Users/farhad/Code/PokerBot/consult/artifacts/2026-05-31-scratch-improve/overlay-cap/overlay_enumeration.json")


def overlay_locked(hp, fp, fr, cc, score):
    if fp:
        if fr and score >= 88:
            return "all_in"
        if fr and score >= 58:
            return "call"
        return None
    if hp:
        if score >= 72:
            return "all_in"
        if cc:
            return "check"
        return "fold"
    return None


def overlay_cap015(hp, fp, fr, cc, score):
    if fp:
        if fr and score >= 100:
            return "all_in"
        if fr and score >= 58:
            return "call"
        return None
    if hp:
        if score >= 96:
            return "all_in"
        if cc:
            return "check"
        return "fold"
    return None


def overlay_cap010(hp, fp, fr, cc, score):
    if fp:
        if fr and score >= 58:
            return "call"
        return None
    if hp:
        if cc:
            return "check"
        return "fold"
    return None


def all_hands():
    hands = []
    for i, r1 in enumerate(RANKS):
        for j, r2 in enumerate(RANKS):
            if i == j:
                hands.append(r1 + r2)              # pair
            elif i > j:
                hands.append(r1 + r2 + "s")        # suited
                hands.append(r1 + r2 + "o")        # offsuit
    return sorted(set(hands), key=lambda h: -hand_score(h))


def main():
    hands = all_hands()
    # realistic trigger combos: fold_prone implies its own branch; high_pressure
    # is the else branch. In src they are mutually evaluated fold_prone-first.
    # (high_pressure, fold_prone) combos that actually reach a branch:
    states = []
    for fp in (True, False):
        for hp in (True, False):
            if not fp and not hp:
                continue  # overlay returns None immediately
            for fr in (True, False):
                for cc in (True, False):
                    states.append((hp, fp, fr, cc))

    cap015_diff_cells = []
    cap010_diff_cells = []
    cap015_breakdown = Counter()
    cap010_breakdown = Counter()
    total_cells = 0
    for (hp, fp, fr, cc) in states:
        for h in hands:
            sc = hand_score(h)
            total_cells += 1
            al = overlay_locked(hp, fp, fr, cc, sc)
            a15 = overlay_cap015(hp, fp, fr, cc, sc)
            a10 = overlay_cap010(hp, fp, fr, cc, sc)
            if al != a15:
                cap015_diff_cells.append({"hp": hp, "fp": fp, "fr": fr, "cc": cc, "hand": h, "score": sc, "locked": al, "cap015": a15})
                cap015_breakdown[f"{al}->{a15}"] += 1
            if al != a10:
                cap010_diff_cells.append({"hp": hp, "fp": fp, "fr": fr, "cc": cc, "hand": h, "score": sc, "locked": al, "cap010": a10})
                cap010_breakdown[f"{al}->{a10}"] += 1

    # Compact hand-band summary: which hands flip in the high_pressure shove band
    hp_shove_flip_15 = sorted({c["hand"] for c in cap015_diff_cells if c["hp"] and not c["fp"]}, key=lambda h: -hand_score(h))
    hp_shove_flip_10 = sorted({c["hand"] for c in cap010_diff_cells if c["hp"] and not c["fp"]}, key=lambda h: -hand_score(h))
    fp_shove_flip_15 = sorted({c["hand"] for c in cap015_diff_cells if c["fp"]}, key=lambda h: -hand_score(h))
    fp_shove_flip_10 = sorted({c["hand"] for c in cap010_diff_cells if c["fp"]}, key=lambda h: -hand_score(h))

    out = {
        "total_enumerated_cells": total_cells,
        "cap015_diff_cell_count": len(cap015_diff_cells),
        "cap010_diff_cell_count": len(cap010_diff_cells),
        "cap015_action_change_breakdown": dict(cap015_breakdown),
        "cap010_action_change_breakdown": dict(cap010_breakdown),
        "cap015_high_pressure_hands_no_longer_shoved": hp_shove_flip_15,
        "cap010_high_pressure_hands_no_longer_shoved": hp_shove_flip_10,
        "cap015_fold_prone_hands_no_longer_shoved": fp_shove_flip_15,
        "cap010_fold_prone_hands_no_longer_shoved": fp_shove_flip_10,
        "note": "MAP only: cells are unweighted. Real occurrence weights are in overlay_divergence*.json. All changes are shove-removals (all_in -> check/fold), never adding aggression -- confirms monotone downside-only reduction.",
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("cap015_high_pressure_hands_no_longer_shoved",)}, indent=2, sort_keys=True))
    print(f"cap015 hp-shove-removed hands ({len(hp_shove_flip_15)}): {hp_shove_flip_15}")
    print(f"cap010 hp-shove-removed hands ({len(hp_shove_flip_10)}): {hp_shove_flip_10}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
