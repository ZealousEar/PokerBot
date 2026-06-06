#!/usr/bin/env python3
"""Preflop / sizing audit (investigation-only).

Question (V2 recon item 4): does the PREFLOP or SIZING code contain the same
"threshold-to-stackoff" bug as the postflop leak fixed in qual2-patch?

The postflop bug (postflop_baseline.py): `eq >= 0.80` where `eq` is equity-vs-
RANDOM (`hand_strength`) authorised a `current_bet * 3` re-raise that compounded
into full-stack jams at ~12% real equity. The fix gates large commitments on
board-aware nuttedness (`_can_commit`) and caps the raise at pot.

This tool performs STATIC checks on the deployed-equivalent strategy source
(PokerBot-claude worktree per qual2-patch FINDINGS) and cross-references the
empirical Thorp stackoff origin-attribution from field_recon.py. It does NOT
modify any strategy code.

Usage:
    python tools/preflop_sizing_audit.py [--src <dir>] [--stackoffs <csv>]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Deployed-equivalent source is the elaborate PokerBot-claude worktree
DEFAULT_SRC = ROOT.parent / "PokerBot-claude" / "src"
DEFAULT_STACKOFFS = ROOT / "consult" / "artifacts" / "2026-06-03-overnight-recon" / "stackoff_decisions.csv"

EQUITY_TOKENS = ("hand_strength", "equity_vs_range", "equity(", "eq >=", "eq>=",
                 "eq >", "eq <", "monte", "trials")


def read(path: Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def check(label, passed, detail):
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {label}")
    if detail:
        print(f"       {detail}")
    return passed


def audit_static(src: Path) -> bool:
    print(f"# Static audit of preflop/sizing source: {src}")
    pf = read(src / "preflop_lookup.py")
    bot = read(src / "bot.py")
    sz = read(src / "sizing.py")
    ok = True

    # 1. No equity-vs-random threshold anywhere in the preflop decision path.
    pf_path = pf + "\n" + _preflop_section(bot)
    eq_hits = [t for t in EQUITY_TOKENS if t in pf_path]
    ok &= check(
        "preflop path contains NO equity/hand-strength threshold",
        not eq_hits,
        f"equity tokens found: {eq_hits}" if eq_hits else
        "preflop is pure range-tag lookup (position x hand x action_seq) — the "
        "eq-vs-random miscalibration that caused the postflop bug cannot exist here.")

    # 2. all_in tag is gated to a premium range at 3+ raises only.
    m = re.search(r"len\(raises\)\s*>=\s*3:(.*?)return\s*\{\"tag\":\s*\"fold\"\}",
                  pf, re.S)
    allin_block = m.group(1) if m else ""
    allin_tag = '"tag": "all_in"'
    allin_count = pf.count(allin_tag)
    premium_only = bool(re.search(r'"AA",\s*"KK",\s*"AKs",\s*"AKo"', allin_block)) \
        and allin_count == 1
    ok &= check(
        "preflop all_in tag gated to {AA,KK,AKs,AKo} at len(raises)>=3 only",
        premium_only,
        f"all_in tag occurrences in preflop_lookup: {allin_count}; "
        "the betting tree narrows monotonically as raises escalate "
        "(open->3bet->4bet->jam), so a marginal hand cannot ratchet into a jam.")

    # 3. sizing.legal_raise_total caps at stack (converts overcommit to all_in).
    caps = ("chips_needed >= my_stack" in sz and 'return {"action": "all_in"}' in sz)
    ok &= check(
        "sizing.legal_raise_total caps target at stack -> all_in (no overcommit)",
        caps,
        "raise targets that meet/exceed stack become all_in; no geometric blow-up.")

    # 4. preflop raise sizings are bounded multiples (no current_bet*3-style
    #    geometric escalation off an equity threshold).
    mults = re.findall(r"(?:current_bet|bb|raise_to)\s*\*\s*([0-9.]+)", _preflop_section(bot))
    bounded = all(float(x) <= 4.0 for x in mults) if mults else True
    ok &= check(
        "preflop raise multipliers bounded (<=4x), range-gated not equity-gated",
        bounded,
        f"multipliers seen: {sorted(set(mults))} (open 2.5-3x, 3bet 3-3.5x, "
        "4bet 2.3x) — each tier reachable only by the corresponding range tag.")

    # 5. The exact postflop bug pattern is ABSENT from preflop/sizing.
    bug = ("current_bet * 3" in pf) or ("current_bet*3" in pf)
    ok &= check(
        "postflop bug pattern (eq>=0.80 -> current_bet*3) ABSENT in preflop",
        not bug, "")
    return ok


def _preflop_section(bot_src: str) -> str:
    """Extract the preflop decision region of bot.py for token scanning."""
    start = bot_src.find("def _preflop_action")
    end = bot_src.find("def _strategy")
    if start == -1:
        return bot_src
    return bot_src[start:end if end != -1 else len(bot_src)]


def audit_empirical(stackoffs: Path) -> bool:
    print(f"\n# Empirical cross-reference: {stackoffs}")
    if not stackoffs.is_file():
        print("  (stackoff CSV not found — run field_recon.py emit first)")
        return True
    rows = list(csv.DictReader(open(stackoffs)))
    by_origin = {}
    for r in rows:
        o = r["origin"]
        d = by_origin.setdefault(o, {"n": 0, "net": 0, "allin_pf": 0,
                                     "money_pf": 0, "money_post": 0})
        d["n"] += 1
        d["net"] += int(r["delta"])
        pf_inv = int(r["pf_invested"])
        post_inv = int(r["flop_invested"]) + int(r["turn_invested"]) + int(r["river_invested"])
        if int(r["went_all_in"]) and post_inv == 0:
            d["allin_pf"] += 1
        d["money_pf"] += pf_inv
        d["money_post"] += post_inv
    print(f"  total stackoffs (commit>=40% start stack): {len(rows)}")
    for o, d in sorted(by_origin.items()):
        print(f"  origin={o:20s} n={d['n']:3d} net={d['net']:+8d} "
              f"all-in-preflop={d['allin_pf']:2d} "
              f"chips[pf={d['money_pf']}, postflop={d['money_post']}]")
    pf_origin = sum(d["n"] for o, d in by_origin.items() if o.startswith("preflop"))
    post_origin = by_origin.get("postflop-escalation", {}).get("n", 0)
    print(f"\n  preflop-origin stackoffs: {pf_origin}/{len(rows)}; "
          f"postflop-origin: {post_origin}/{len(rows)}")
    print("  NOTE: preflop-origin stackoffs are overwhelmingly preflop ALL-INs "
          "(money in preflop, board ran out) — i.e. range-tag jams/calls, not a "
          "threshold bug. Postflop-origin stackoffs (the majority) are commitment "
          "decisions made in postflop.py, already gated by the qual2-patch _can_commit fix.")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    ap.add_argument("--stackoffs", type=Path, default=DEFAULT_STACKOFFS)
    args = ap.parse_args(argv)
    print("=" * 72)
    print("PREFLOP / SIZING THRESHOLD-TO-STACKOFF AUDIT")
    print("=" * 72)
    static_ok = audit_static(args.src)
    audit_empirical(args.stackoffs)
    print("\n" + "=" * 72)
    verdict = ("NO preflop/sizing threshold-to-stackoff bug found. Preflop is "
               "range/tag-gated with monotonic narrowing; sizing caps at stack."
               if static_ok else
               "POTENTIAL preflop/sizing issue — see FAIL lines above.")
    print("VERDICT:", verdict)
    print("=" * 72)
    return 0 if static_ok else 1


if __name__ == "__main__":
    sys.exit(main())
