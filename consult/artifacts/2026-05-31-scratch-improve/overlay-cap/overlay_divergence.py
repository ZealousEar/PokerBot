"""Noise-free measurement of the LANE-B overlay-magnitude reduction.

Two parts:

(A) CAPTURE the real preflop input distribution the overlay actually sees.
    We run the LOCKED hero (single reference, no pairing) across real fields,
    monkeypatching BotProcess.act to record the hero's preflop game_state on
    every decision. Chip-delta outcome noise is irrelevant here; we only need
    the *input distribution* of preflop states, whose firing-rate statistics
    are stable across runs even though outcomes are not.

(B) OFFLINE RE-EVALUATE three pure overlay functions (locked / cap015 / cap010)
    on each captured state, using the real OpponentModel.pressure_features and
    ranges.hand_score from the v_final source tree. This is deterministic
    re-evaluation of pure functions on identical fixed inputs => ZERO simulator
    noise. We report:
      * overlay firing rate per 1000 preflop hero decisions
      * of firings, fraction that cap015 / cap010 change
      * action-change breakdown (all_in -> check/fold/call)
    Labelled first-order: opponents' observed lines are held fixed. Once an
    action changes the trajectory diverges; the full dynamic effect is exactly
    what the unseeded-RNG pods cannot measure.

The three overlay variants are reproduced here as standalone pure functions
mirroring src/bot.py::_pressure_preflop_overlay so we can evaluate all three on
one captured corpus without re-running the engine.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/farhad/Code/PokerBot")
ENGINE_DIR = ROOT / "ext" / "fullhouse-engine"
VFINAL_SRC = Path("/tmp/vfinal_inspect/src")  # extracted locked source (authoritative)

sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(VFINAL_SRC))  # use the LOCKED opponent_model + ranges

from sandbox import match as match_mod  # noqa: E402
from opponent_model import OpponentModel  # noqa: E402  (locked v_final impl)
from ranges import canonical_hand, hand_score  # noqa: E402

HERO = "hero"
_OM = OpponentModel()


# --- three overlay variants as pure functions (mirror src/bot.py exactly) ----

def overlay_locked(features: dict, score: int):
    if features["fold_prone_pressure"]:
        if features["facing_raise"] and score >= 88:
            return "all_in"
        if features["facing_raise"] and score >= 58:
            return "call"
        return None
    if features["high_pressure"]:
        if score >= 72:
            return "all_in"
        if features["can_check"]:
            return "check"
        return "fold"
    return None


def overlay_cap015(features: dict, score: int):
    if features["fold_prone_pressure"]:
        if features["facing_raise"] and score >= 100:
            return "all_in"
        if features["facing_raise"] and score >= 58:
            return "call"
        return None
    if features["high_pressure"]:
        if score >= 96:
            return "all_in"
        if features["can_check"]:
            return "check"
        return "fold"
    return None


def overlay_cap010(features: dict, score: int):
    if features["fold_prone_pressure"]:
        if features["facing_raise"] and score >= 58:
            return "call"
        return None
    if features["high_pressure"]:
        if features["can_check"]:
            return "check"
        return "fold"
    return None


# --- capture ----------------------------------------------------------------

class PreflopCapture:
    """Monkeypatch BotProcess.act to record hero preflop game_states."""

    def __init__(self):
        self._orig_act = match_mod.BotProcess.act
        self._lock = threading.Lock()
        self.states: list[dict] = []
        self._installed = False

    def install(self):
        if self._installed:
            return
        cap = self

        def patched_act(proc_self, game_state):
            if (
                proc_self.bot_id == HERO
                and isinstance(game_state, dict)
                and game_state.get("street") == "preflop"
                and game_state.get("type") == "action_request"
            ):
                # store a minimal but faithful copy of what the overlay reads
                with cap._lock:
                    cap.states.append({
                        "seat_to_act": game_state.get("seat_to_act"),
                        "amount_owed": game_state.get("amount_owed"),
                        "can_check": bool(game_state.get("can_check")),
                        "your_cards": list(game_state.get("your_cards") or []),
                        "action_log": list(game_state.get("action_log") or []),
                        "match_action_log": list(game_state.get("match_action_log") or []),
                    })
            return cap._orig_act(proc_self, game_state)

        match_mod.BotProcess.act = patched_act
        self._installed = True

    def uninstall(self):
        if self._installed:
            match_mod.BotProcess.act = self._orig_act
            self._installed = False


def features_for(state: dict) -> dict:
    f = _OM.pressure_features(state)
    # pressure_features returns facing_raise but not can_check; overlay reads
    # can_check from game_state directly, so add it here.
    f = dict(f)
    f["can_check"] = bool(state.get("can_check"))
    return f


# --- field definitions (reuse the pod opponent zips) ------------------------

def build_fields(opp_dir: Path) -> dict:
    o = lambda n: str((opp_dir / f"{n}.zip").resolve())
    return {
        # deterministic reference field (C0-style)
        "F_DETERMINISTIC": {"template": o("template"), "aggressor": o("aggressor"),
                            "mathematician": o("mathematician"), "shark": o("shark"),
                            "ref_bot_2": o("ref_bot_2")},
        # toby-heavy weak field (C1-style)
        "F_TOBY_WEAK": {"toby_master": o("toby_master"), "template": o("template"),
                        "mathematician": o("mathematician"), "shark": o("shark"),
                        "ref_bot_2": o("ref_bot_2")},
        # toby+mehedi (C3-style)
        "F_TOBY_MEHEDI": {"toby_master": o("toby_master"), "mehedi_mybot": o("mehedi_mybot"),
                          "template": o("template"), "shark": o("shark"), "ref_bot_2": o("ref_bot_2")},
        # public nightmare (C4-style)
        "F_PUBLIC": {"toby_master": o("toby_master"), "mehedi_mybot": o("mehedi_mybot"),
                     "famadeo": o("famadeo"), "neel": o("neel"), "pav_skantbot7_9": o("pav_skantbot7_9")},
    }


def run_field(hero_zip: Path, field: dict, seeds: list[int], hands: int, cap: PreflopCapture):
    for seed in seeds:
        paths = {HERO: str(hero_zip.resolve()), **field}
        match_mod.run_match(f"cap_{seed}", paths, n_hands=hands, verbose=False, seed=seed)


def analyze(states: list[dict]) -> dict:
    n = len(states)
    fired_locked = 0
    fired_any_trigger = 0
    cap015_changed = 0
    cap010_changed = 0
    locked_action_dist = Counter()
    cap015_changes = Counter()  # "locked_action->cap015_action"
    cap010_changes = Counter()
    trigger_dist = Counter()
    for st in states:
        f = features_for(st)
        hand = canonical_hand(st.get("your_cards") or [])
        score = hand_score(hand)
        triggered = f["high_pressure"] or f["fold_prone_pressure"]
        if triggered:
            fired_any_trigger += 1
            trigger_dist["high_pressure" if f["high_pressure"] else "fold_prone_only"] += 1
        a_l = overlay_locked(f, score)
        a_15 = overlay_cap015(f, score)
        a_10 = overlay_cap010(f, score)
        if a_l is not None:
            fired_locked += 1
            locked_action_dist[a_l] += 1
        if a_l != a_15:
            cap015_changed += 1
            cap015_changes[f"{a_l}->{a_15}"] += 1
        if a_l != a_10:
            cap010_changed += 1
            cap010_changes[f"{a_l}->{a_10}"] += 1
    per1000 = lambda c: round(1000.0 * c / n, 2) if n else None
    return {
        "preflop_hero_decisions": n,
        "overlay_fired_locked": fired_locked,
        "overlay_fired_locked_per_1000": per1000(fired_locked),
        "trigger_detected": fired_any_trigger,
        "trigger_detected_per_1000": per1000(fired_any_trigger),
        "trigger_distribution": dict(trigger_dist),
        "locked_action_distribution": dict(locked_action_dist),
        "cap015_changed_vs_locked": cap015_changed,
        "cap015_changed_per_1000": per1000(cap015_changed),
        "cap015_change_breakdown": dict(cap015_changes),
        "cap010_changed_vs_locked": cap010_changed,
        "cap010_changed_per_1000": per1000(cap010_changed),
        "cap010_change_breakdown": dict(cap010_changes),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--hero-zip", default="/Users/farhad/Code/PokerBot/submissions/v_final.zip", type=Path)
    p.add_argument("--opp-dir", required=True, type=Path,
                   help="dir with the prepared opponent zips (from run_pods)")
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--seed-base", type=int, default=500)
    p.add_argument("--hands", type=int, default=400)
    p.add_argument("--fields", nargs="+", default=None)
    args = p.parse_args()

    fields = build_fields(args.opp_dir.resolve())
    selected = args.fields or list(fields)
    seeds = list(range(args.seed_base, args.seed_base + args.seeds))

    cap = PreflopCapture()
    cap.install()
    per_field = {}
    try:
        for fname in selected:
            cap.states = []
            run_field(args.hero_zip, fields[fname], seeds, args.hands, cap)
            per_field[fname] = analyze(cap.states)
            d = per_field[fname]
            print(f"[div] {fname}: preflop_dec={d['preflop_hero_decisions']} "
                  f"fired/1k={d['overlay_fired_locked_per_1000']} "
                  f"cap015_chg/1k={d['cap015_changed_per_1000']} "
                  f"cap010_chg/1k={d['cap010_changed_per_1000']} "
                  f"locked_actions={d['locked_action_distribution']}", flush=True)
    finally:
        cap.uninstall()

    out = {
        "hero_zip": str(args.hero_zip),
        "seeds": seeds,
        "hands_per_match": args.hands,
        "fields": {k: list(v.keys()) for k, v in fields.items() if k in selected},
        "results": per_field,
    }
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"[div] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
