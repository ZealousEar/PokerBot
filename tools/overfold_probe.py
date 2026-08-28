"""Historical over-fold probe over a fixed synthetic pressure grid.

The linked post-mortem records an earlier maintained revision. Running this
tool today measures the current source policy on the same grid; it does not
reproduce the historical percentages after strategy changes.

What this is NOT
----------------
This reports action frequencies only. It does **not** estimate EV, chip deltas,
or bb/100 — those require the engine match harness and a real opponent
distribution. A high fold frequency on
marginal hands is a description of the strategy's shape, not a loss figure.

Engine-free and deterministic: decide() loads the committed JSON sizing policy
(or falls back safely) and needs no engine; equity is stably seeded.

Usage:
    python tools/overfold_probe.py            # markdown report to stdout
    python tools/overfold_probe.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.bot import decide
from src.equity import hand_strength

# Fixed pressure grid. Marginal-to-strong hero holdings on two textures, run out
# across flop/turn/river, facing four bet sizes. Boards are chosen so the same
# hand spans bluff-catcher -> made-hand as the strength tiers below show.
TEXTURES = {
    "dry_A_high": ["Ac", "Kd", "7h", "2s", "9c"],
    "wet_QJ9": ["Qh", "Jh", "9c", "4s", "2h"],
}
STREETS = {"flop": 3, "turn": 4, "river": 5}
HERO_HANDS = [
    ("Kh", "Qd"),  # overcards / second pair
    ("9h", "9d"),  # underpair on high boards
    ("Ah", "Jc"),  # ace-high / top pair weak-ish
    ("7s", "7c"),  # small/medium pair, makes a set on 7x
    ("Tc", "Td"),  # medium pair
    ("Ah", "5h"),  # ace-low + backdoor wheel/flush
    ("Js", "Th"),  # draws / middle made hand on QJ9
    ("Kc", "Kd"),  # strong overpair / set on Kx
]
BET_FRACTIONS = (0.33, 0.66, 1.0, 1.5)  # of pot; 1.5 = overbet
POT = 1000
HERO_STACK = 9000  # deep, so these are call/fold spots, not stack-off math


def _player(seat, stack=9000, bet=0, folded=False):
    return {
        "seat": seat,
        "bot_id": f"seat_{seat}",
        "stack": stack,
        "state": "folded" if folded else "active",
        "is_folded": folded,
        "is_all_in": False,
        "bet_this_street": bet,
        "hole_cards": None,
    }


def _pressure_state(hero, board, bet):
    """Heads-up postflop spot: hero is OOP facing villain's bet of `bet`."""
    return {
        "type": "action_request",
        "hand_id": "overfold_probe",
        "street": {3: "flop", 4: "turn", 5: "river"}[len(board)],
        "seat_to_act": 0,
        "pot": POT + bet,
        "community_cards": board,
        "current_bet": bet,
        "min_raise_to": bet * 2,
        "amount_owed": bet,
        "can_check": False,
        "your_cards": list(hero),
        "your_stack": HERO_STACK,
        "your_bet_this_street": 0,
        "players": [_player(0, stack=HERO_STACK), _player(1, stack=HERO_STACK, bet=bet)],
        "action_log": [{"seat": 1, "action": "raise", "amount": bet}],
        "match_action_log": [],
    }


def _verb(action):
    raw = str(action.get("action", "")).lower().strip()
    if raw in ("raise", "all_in"):
        return "raise+"
    if raw in ("fold", "call", "check"):
        return raw
    return raw or "unknown"


def _strength_tier(equity):
    if equity < 0.45:
        return "weak (<0.45)"
    if equity < 0.65:
        return "medium (0.45-0.65)"
    return "strong (>=0.65)"


def run_probe():
    rows = []
    for tex_name, full_board in TEXTURES.items():
        for street, n in STREETS.items():
            board = full_board[:n]
            for hero in HERO_HANDS:
                eq = hand_strength(hero, board, trials=400)
                tier = _strength_tier(eq)
                for frac in BET_FRACTIONS:
                    bet = int(round(frac * POT))
                    action = decide(_pressure_state(hero, board, bet))
                    rows.append(
                        {
                            "texture": tex_name,
                            "street": street,
                            "hero": "".join(hero),
                            "equity_vs_random": round(eq, 3),
                            "tier": tier,
                            "bet_fraction": frac,
                            "verb": _verb(action),
                        }
                    )
    return rows


def _pct(counter, key, total):
    return 100.0 * counter.get(key, 0) / total if total else 0.0


def summarize(rows):
    total = len(rows)
    overall = Counter(r["verb"] for r in rows)

    by_bet = defaultdict(Counter)
    by_street = defaultdict(Counter)
    by_tier = defaultdict(Counter)
    for r in rows:
        by_bet[r["bet_fraction"]][r["verb"]] += 1
        by_street[r["street"]][r["verb"]] += 1
        by_tier[r["tier"]][r["verb"]] += 1

    return {
        "total_spots": total,
        "overall": dict(overall),
        "fold_pct_overall": round(_pct(overall, "fold", total), 1),
        "by_bet_fraction": {
            f: {"n": sum(c.values()), "fold_pct": round(_pct(c, "fold", sum(c.values())), 1)}
            for f, c in sorted(by_bet.items())
        },
        "by_street": {
            s: {"n": sum(c.values()), "fold_pct": round(_pct(c, "fold", sum(c.values())), 1)}
            for s, c in by_street.items()
        },
        "by_strength_tier": {
            t: {"n": sum(c.values()), "fold_pct": round(_pct(c, "fold", sum(c.values())), 1)}
            for t, c in sorted(by_tier.items())
        },
    }


def to_markdown(summary):
    lines = []
    o = summary["overall"]
    lines.append(f"**Synthetic postflop pressure grid — {summary['total_spots']} spots.** "
                 "Action frequencies only; no EV / chip / bb-100 estimate.")
    lines.append("")
    lines.append("| Action | Count | Share |")
    lines.append("| --- | --- | --- |")
    for verb in ("fold", "call", "check", "raise+"):
        cnt = o.get(verb, 0)
        share = 100.0 * cnt / summary["total_spots"]
        lines.append(f"| {verb} | {cnt} | {share:.1f}% |")
    lines.append("")
    lines.append(f"Overall fold frequency: **{summary['fold_pct_overall']:.1f}%**.")
    lines.append("")
    lines.append("| Bet faced (× pot) | Spots | Fold % |")
    lines.append("| --- | --- | --- |")
    for frac, d in summary["by_bet_fraction"].items():
        lines.append(f"| {frac:g} | {d['n']} | {d['fold_pct']:.1f}% |")
    lines.append("")
    lines.append("| Street | Spots | Fold % |")
    lines.append("| --- | --- | --- |")
    for street in ("flop", "turn", "river"):
        d = summary["by_street"].get(street)
        if d:
            lines.append(f"| {street} | {d['n']} | {d['fold_pct']:.1f}% |")
    lines.append("")
    lines.append("| Hand strength (equity vs random) | Spots | Fold % |")
    lines.append("| --- | --- | --- |")
    for tier, d in summary["by_strength_tier"].items():
        lines.append(f"| {tier} | {d['n']} | {d['fold_pct']:.1f}% |")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = p.parse_args()

    rows = run_probe()
    summary = summarize(rows)
    if args.json:
        print(json.dumps({"summary": summary, "rows": rows}, indent=2))
    else:
        print(to_markdown(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
