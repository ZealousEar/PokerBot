"""Per-seat opponent frequency tracker.

Tracks VPIP, PFR, AF (aggression factor), FoldToCBet. Exploit shifts apply
only after a 30-hand warmup per seat — before that, use baseline frequencies.

Updates from `state["match_action_log"]` injected by the engine each call —
the bot has no other channel to opponent history.

# Source: [[Libratus-Brown-Sandholm-2017]] — opponent fingerprint refinement
#         + [[Engine-Fullhouse]] — field-level exploit holes seed the priors
"""
from collections import defaultdict
import os
from typing import Dict, List, Optional

import numpy as np

WARMUP_HANDS = 30
DEFAULT_VPIP = 0.27
DEFAULT_PFR = 0.20
DEFAULT_AF = 1.4
DEFAULT_FOLD_TO_CBET = 0.50

# Bounded deviation: cap how far the overlay can shift baseline frequency.
MAX_DEVIATION_PP = 0.27  # Candidate C: larger but still bounded overlay vs overfolding field

SHIFT_KEYS = (
    "widen_open",
    "cbet_bluff_more",
    "value_thinner",
    "bluff_catch_less",
    "tighten_open",
    "fold_to_pressure_less",
    "value_widen_vs_aggro",
)

_DEFAULT_FEATURES = {
    "vpip": DEFAULT_VPIP,
    "pfr": DEFAULT_PFR,
    "af": DEFAULT_AF,
    "fold_to_cbet": DEFAULT_FOLD_TO_CBET,
}


def _neutral_shifts() -> Dict[str, float]:
    return {key: 0.0 for key in SHIFT_KEYS}


def _data_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.environ.get("BOT_DATA_DIR", os.path.join(os.path.dirname(here), "data"))


def _string_tuple(value) -> tuple:
    return tuple(str(x) for x in np.asarray(value).reshape(-1).tolist())


def _finite_2d(value, rows: int = None, cols: int = None) -> Optional[np.ndarray]:
    arr = np.asarray(value, dtype=np.float32)
    if arr.ndim != 2:
        return None
    if rows is not None and arr.shape[0] != rows:
        return None
    if cols is not None and arr.shape[1] != cols:
        return None
    if not np.all(np.isfinite(arr)):
        return None
    return arr


def _load_field_priors() -> Optional[dict]:
    """Load compact, anonymized field priors.

    The file is optional. Any missing or malformed array yields a clean neutral
    fallback rather than an import-time exception.
    """
    path = os.path.join(_data_dir(), "field_priors.npz")
    try:
        with np.load(path, allow_pickle=False) as data:
            version = int(np.asarray(data["schema_version"]).reshape(-1)[0])
            if version != 1:
                return None

            feature_names = _string_tuple(data["classifier_feature_names"])
            if not feature_names:
                return None
            for name in feature_names:
                if name not in _DEFAULT_FEATURES:
                    return None

            cluster_names = _string_tuple(data["cluster_names"])
            if not cluster_names:
                return None

            shift_names = _string_tuple(data["shift_names"])
            if shift_names != SHIFT_KEYS:
                return None

            centroids = _finite_2d(
                data["cluster_centroids"], rows=len(cluster_names), cols=len(feature_names)
            )
            if centroids is None:
                return None

            scales = np.asarray(data["cluster_scales"], dtype=np.float32).reshape(-1)
            if scales.shape != (len(feature_names),):
                return None
            if not np.all(np.isfinite(scales)):
                return None
            scales = np.maximum(scales, np.float32(0.01))

            shifts = _finite_2d(
                data["shift_by_cluster"], rows=len(cluster_names), cols=len(SHIFT_KEYS)
            )
            if shifts is None:
                return None
            shifts = np.clip(shifts, -MAX_DEVIATION_PP, MAX_DEVIATION_PP)

            return {
                "feature_names": feature_names,
                "cluster_names": cluster_names,
                "cluster_centroids": centroids,
                "cluster_scales": scales,
                "shift_by_cluster": shifts,
            }
    except Exception:
        return None


_FIELD_PRIORS = _load_field_priors()


class OpponentModel:
    """Singleton-style per-seat tracker. Lives across hands within a match
    process (one Python process per bot per match). Reset is implicit when
    the process restarts."""

    def __init__(self):
        self._counts = defaultdict(lambda: {
            "hands": 0,
            "vpip_chances": 0,
            "vpip_done": 0,
            "pfr_chances": 0,
            "pfr_done": 0,
            "bets_raises": 0,
            "calls": 0,
            "cbet_faced": 0,
            "cbet_folded": 0,
            "last_hand_id": None,
            "voluntarily_in_this_hand": False,
            "raised_this_hand": False,
        })

    def observe_log(self, match_action_log: List[dict], current_hand_id: str = None) -> None:
        """Replay a rolling match_action_log; idempotent counters keyed by
        hand_id boundaries. We rebuild rather than diff because the log is
        small (≤ 200 entries by engine cap)."""
        if not match_action_log:
            return
        # Reset per-hand flags
        seen_hands = set()
        for c in self._counts.values():
            c["voluntarily_in_this_hand"] = False
            c["raised_this_hand"] = False
        # Walk log in order.
        last_hand = None
        for entry in match_action_log:
            seat = entry.get("seat")
            act = entry.get("action")
            hand_num = entry.get("hand_num")
            if seat is None or act is None:
                continue
            c = self._counts[seat]
            if hand_num != last_hand:
                # New hand: commit previous flags first.
                if last_hand is not None:
                    for sc in self._counts.values():
                        if sc.get("_in_hand"):
                            sc["hands"] = sc.get("hands", 0)  # already counted
                last_hand = hand_num
                # Reset per-hand flags for everyone at the start of a new hand.
                for sc in self._counts.values():
                    sc["voluntarily_in_this_hand"] = False
                    sc["raised_this_hand"] = False
            if hand_num not in seen_hands:
                seen_hands.add(hand_num)
            # Update counters by action type. We track only preflop actions
            # for VPIP/PFR since the match_action_log doesn't carry street.
            # Best-effort: count first action per seat per hand for VPIP/PFR.
            if act in ("call", "raise", "all_in"):
                if not c["voluntarily_in_this_hand"]:
                    c["voluntarily_in_this_hand"] = True
                    c["vpip_done"] += 1
                if act in ("raise", "all_in"):
                    c["bets_raises"] += 1
                    if not c["raised_this_hand"]:
                        c["raised_this_hand"] = True
                        c["pfr_done"] += 1
                else:
                    c["calls"] += 1
        # Approximate hands seen = number of distinct hand_nums in log.
        for c in self._counts.values():
            c["hands"] = max(c["hands"], len(seen_hands))
            c["vpip_chances"] = max(c["vpip_chances"], c["hands"])
            c["pfr_chances"] = max(c["pfr_chances"], c["hands"])

    def is_warm(self, seat: int) -> bool:
        return self._counts[seat]["hands"] >= WARMUP_HANDS

    def features(self, seat: int) -> Dict[str, float]:
        c = self._counts[seat]
        hands = max(c["hands"], 1)
        return {
            "vpip": c["vpip_done"] / hands if c["vpip_chances"] else DEFAULT_VPIP,
            "pfr": c["pfr_done"] / hands if c["pfr_chances"] else DEFAULT_PFR,
            "af": (c["bets_raises"] / c["calls"]) if c["calls"] else DEFAULT_AF,
            "fold_to_cbet": (c["cbet_folded"] / c["cbet_faced"]) if c["cbet_faced"] else DEFAULT_FOLD_TO_CBET,
            "hands": c["hands"],
        }

    def archetype(self, seat: int) -> str:
        """Return a coarse tag used to bias overlay shifts. Tags:
        tight_passive, loose_passive, tight_aggressive, loose_aggressive, unknown."""
        if not self.is_warm(seat):
            return "unknown"
        f = self.features(seat)
        tight = f["vpip"] < 0.22
        agg = f["af"] > 2.0 or f["pfr"] > 0.18
        if tight and agg:
            return "tight_aggressive"
        if tight and not agg:
            return "tight_passive"
        if not tight and agg:
            return "loose_aggressive"
        return "loose_passive"

    def _prior_cluster_idx(self, seat: int) -> Optional[int]:
        if _FIELD_PRIORS is None:
            return None
        f = self.features(seat)
        values = np.array([
            float(f.get(name, _DEFAULT_FEATURES[name]))
            for name in _FIELD_PRIORS["feature_names"]
        ], dtype=np.float32)
        if not np.all(np.isfinite(values)):
            return None
        centered = (values - _FIELD_PRIORS["cluster_centroids"]) / _FIELD_PRIORS["cluster_scales"]
        distances = np.sum(centered * centered, axis=1)
        if not np.all(np.isfinite(distances)):
            return None
        return int(np.argmin(distances))

    def exploit_shift(self, seat: int) -> Dict[str, float]:
        """Return a complete, bounded overlay shift dictionary.

        Safe fallback policy:
        - cold seat (< WARMUP_HANDS): all zeros;
        - missing/malformed field priors: all zeros;
        - valid priors + warm behavioral sample: nearest-cluster shifts,
          clipped to MAX_DEVIATION_PP.

        Returned shift keys:
            widen_open              — open wider preflop
            cbet_bluff_more         — bump c-bet bluff frequency on dry boards
            value_thinner           — call/value continue wider vs loose ranges
            bluff_catch_less        — fold marginal bluff-catches more often
            tighten_open            — reserved preflop tightening knob
            fold_to_pressure_less   — call down more vs pressure-heavy ranges
            value_widen_vs_aggro    — value-bet wider vs aggressive callers
        """
        shifts = _neutral_shifts()
        if not self.is_warm(seat):
            return shifts

        idx = self._prior_cluster_idx(seat)
        if idx is None:
            return shifts

        prior_values = _FIELD_PRIORS["shift_by_cluster"][idx]
        for key, value in zip(SHIFT_KEYS, prior_values):
            shifts[key] = float(np.clip(value, -MAX_DEVIATION_PP, MAX_DEVIATION_PP))
        return shifts


# Module-level singleton so updates persist across decide() calls in one
# process. Engine spawns one process per bot per match (sandbox/match.py).
_MODEL = OpponentModel()


def get_model() -> OpponentModel:
    return _MODEL
