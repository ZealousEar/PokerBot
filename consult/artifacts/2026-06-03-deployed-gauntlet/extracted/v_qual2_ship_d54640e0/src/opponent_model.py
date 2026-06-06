"""Per-seat opponent frequency tracker — behavior-based overlay.

The bot has one observation channel: `state["match_action_log"]`, a rolling
log of every action the engine has seen since the match started (capped at
~200 entries). We replay it each `decide()` to rebuild per-seat counters:

  - aggression: fraction of voluntary actions that were raise / all_in
  - vpip_proxy: fraction of hands where seat put money in beyond the blinds
  - pfr_proxy:  fraction of hands where seat raised at least once
  - n_actions:  total observed actions (gates warmup)
  - last_actions: bounded ring of last K actions for fast "recent aggression"
                  trigger (catches bot-style behavior in < 10 hands)

The overlay returns a `shift` dict — bounded deviation magnitudes that the
preflop and postflop modules read. No identity / name / label is used; all
keys are derived from observed actions and frequencies.

# Source: [[Libratus-Brown-Sandholm-2017]] — opponent fingerprint refinement
#         + [[Engine-Fullhouse]] — observed bot behaviors seed thresholds
"""
from collections import defaultdict, deque
from typing import Deque, Dict, List

# Trigger thresholds. Lower n_actions = faster warmup; higher = more stable.
EARLY_WARMUP_ACTIONS = 8     # crude classification kicks in here
STABLE_WARMUP_ACTIONS = 30   # full archetype lock-in here
RECENT_WINDOW = 30           # ring buffer size for "recent aggression"

# Aggression-fraction cutoffs (recent_aggression / voluntary actions).
HYPER_AGG_THRESHOLD = 0.55   # >= 55 % of voluntary acts were raise/all_in
AGG_THRESHOLD = 0.35

# Bounded deviation: cap how far the overlay can shift baseline frequencies.
MAX_DEVIATION_PP = 0.20


DEFAULT_SHIFT = {
    "widen_open": 0.0,
    "tighten_open": 0.0,
    "cbet_bluff_more": 0.0,
    "value_thinner": 0.0,
    "bluff_catch_less": 0.0,
    "value_widen_vs_aggro": 0.0,
    "fold_to_pressure_less": 0.0,
}


class OpponentModel:
    """One per process. Lives across hands within a match; reset implicit on
    process restart (engine spawns one process per bot per match)."""

    def __init__(self):
        # Per-seat counters. Defaultdict so unseen seats return zeros.
        self._c: Dict[int, dict] = defaultdict(self._new_counter)

    @staticmethod
    def _new_counter() -> dict:
        return {
            "n_actions": 0,
            "voluntary_acts": 0,   # call + raise + all_in
            "agg_acts": 0,         # raise + all_in
            "hands_seen": 0,
            "hands_voluntary": 0,
            "hands_raised": 0,
            "all_in_count": 0,
            "_last_hand_id": None,
            "_in_hand_voluntary": False,
            "_in_hand_raised": False,
            "_recent": deque(maxlen=RECENT_WINDOW),
        }

    def observe_log(self, match_action_log: List[dict],
                    current_hand_id=None) -> None:
        """Rebuild from the rolling log. Idempotent (engine sends the full
        rolling window each turn, capped at ~200 entries)."""
        if not match_action_log:
            return
        # Reset all counters and replay. The log is small so this is cheap.
        self._c.clear()
        last_hand_seen: Dict[int, object] = {}
        for entry in match_action_log:
            seat = entry.get("seat")
            act = entry.get("action")
            if seat is None or act is None:
                continue
            hid = entry.get("hand_num") or entry.get("hand_id")
            c = self._c[seat]
            # Hand boundary: close out per-hand flags for this seat.
            if last_hand_seen.get(seat) != hid:
                if last_hand_seen.get(seat) is not None:
                    c["hands_seen"] += 1
                    if c["_in_hand_voluntary"]:
                        c["hands_voluntary"] += 1
                    if c["_in_hand_raised"]:
                        c["hands_raised"] += 1
                c["_in_hand_voluntary"] = False
                c["_in_hand_raised"] = False
                last_hand_seen[seat] = hid
            # Skip blinds — not voluntary.
            if act in ("small_blind", "big_blind"):
                continue
            c["n_actions"] += 1
            if act in ("call", "raise", "all_in"):
                c["voluntary_acts"] += 1
                c["_in_hand_voluntary"] = True
                c["_recent"].append(1 if act in ("raise", "all_in") else 0)
                if act in ("raise", "all_in"):
                    c["agg_acts"] += 1
                    c["_in_hand_raised"] = True
                if act == "all_in":
                    c["all_in_count"] += 1
            elif act == "fold":
                c["_recent"].append(0)
        # Close out final hand for every seat we touched.
        for seat, c in self._c.items():
            if last_hand_seen.get(seat) is not None and c.get("hands_seen", 0) == 0:
                # Still in first hand — count it as seen so warmup can advance.
                c["hands_seen"] = 1
            if c["_in_hand_voluntary"]:
                # Don't double-count the in-progress hand; commit only on next.
                pass

    # --- read API ---------------------------------------------------------

    def features(self, seat: int) -> Dict[str, float]:
        c = self._c.get(seat) or self._new_counter()
        n_acts = max(c["n_actions"], 1)
        v_acts = max(c["voluntary_acts"], 1)
        recent = list(c["_recent"])
        n_recent_vol = sum(1 for x in recent if x == 1) + \
                       sum(1 for x in recent if x == 0)
        recent_agg = sum(recent) / max(len(recent), 1)
        return {
            "n_actions": c["n_actions"],
            "aggression": c["agg_acts"] / v_acts,
            "voluntary_rate": c["voluntary_acts"] / n_acts,
            "all_in_rate": c["all_in_count"] / n_acts,
            "recent_aggression": recent_agg,
            "hands_seen": c["hands_seen"],
        }

    def archetype(self, seat: int) -> str:
        """Coarse classification ∈ {hyper_aggressive, aggressive,
        loose_passive, tight_passive, unknown}.

        Behavior-based — no opponent names used. Faster warmup tier
        (EARLY_WARMUP_ACTIONS) catches obvious extremes; stable tier
        (STABLE_WARMUP_ACTIONS) refines passive subtypes.
        """
        f = self.features(seat)
        n = f["n_actions"]
        if n < EARLY_WARMUP_ACTIONS:
            return "unknown"
        recent_agg = f["recent_aggression"]
        agg = f["aggression"]
        all_in_rate = f["all_in_rate"]
        # Hyperaggressive: dominated by raises / all-ins. Catches engine
        # `aggressor` (raises every street, jams light) within ~5-10 hands.
        if all_in_rate > 0.15 or recent_agg > HYPER_AGG_THRESHOLD or agg > HYPER_AGG_THRESHOLD:
            return "hyper_aggressive"
        if n < STABLE_WARMUP_ACTIONS:
            if agg > AGG_THRESHOLD:
                return "aggressive"
            return "unknown"
        # Stable tier — refine passive subtypes.
        vpip = f["voluntary_rate"]
        if agg > AGG_THRESHOLD:
            return "aggressive"
        if vpip > 0.40:
            return "loose_passive"
        return "tight_passive"

    def exploit_shift(self, seat: int) -> Dict[str, float]:
        """Return bounded shift deltas. Keys read by preflop_lookup +
        decide_postflop. All magnitudes capped at MAX_DEVIATION_PP.
        """
        arch = self.archetype(seat)
        s = dict(DEFAULT_SHIFT)
        if arch == "hyper_aggressive":
            # Counter-strategy vs raise-heavy villains:
            #   - tighten our open ranges (their light 3-bets punish wides)
            #   - don't fold marginal river hands to large bets (they barrel
            #     air more than value)
            #   - widen our value-bet threshold (they call lighter than GTO)
            s["tighten_open"] = MAX_DEVIATION_PP
            s["fold_to_pressure_less"] = MAX_DEVIATION_PP
            s["value_widen_vs_aggro"] = 0.10
            s["cbet_bluff_more"] = -0.05   # bluff less; they don't fold
            s["bluff_catch_less"] = -0.05  # call down lighter
        elif arch == "aggressive":
            s["tighten_open"] = 0.08
            s["fold_to_pressure_less"] = 0.08
            s["value_widen_vs_aggro"] = 0.05
        elif arch == "tight_passive":
            s["widen_open"] = 0.12
            s["cbet_bluff_more"] = MAX_DEVIATION_PP
            s["bluff_catch_less"] = 0.10
        elif arch == "loose_passive":
            s["widen_open"] = 0.06
            s["value_thinner"] = MAX_DEVIATION_PP
            s["cbet_bluff_more"] = -0.05
        else:  # unknown
            # Mild baseline widen — vs random villain, blueprint + slight
            # widen is small positive EV without exposing us to large counter.
            s["widen_open"] = 0.04
        # Final cap pass — defensive.
        for k, v in s.items():
            s[k] = max(-MAX_DEVIATION_PP, min(MAX_DEVIATION_PP, v))
        return s


_MODEL = OpponentModel()


def get_model() -> OpponentModel:
    return _MODEL


def reset_model() -> None:
    """Test hook — drop all state. Not used in production decide()."""
    global _MODEL
    _MODEL = OpponentModel()
