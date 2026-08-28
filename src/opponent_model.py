"""Incremental, identity-stable opponent statistics.

The engine calls the bot with a cumulative ``action_log`` snapshot for the
current hand. :class:`OpponentModel` consumes only newly visible actions,
labels them from the current decision street, and keeps lifetime counts keyed
by ``bot_id``. Replaying a snapshot cannot inflate a profile, and a rolling
match log cannot erase observations older than its window.

Seat integers remain accepted by read APIs for compatibility. A seat resolves
through the latest trustworthy ``players`` mapping; profiles are never pooled
by seat when a bot identity is available. Malformed or ambiguous observations
are ignored. Reads with inconsistent or insufficient evidence are neutral.
"""

from collections import Counter, defaultdict
import math
import os
from typing import Dict, List, Optional, Union

import numpy as np


WARMUP_HANDS = 30
MIN_RELIABLE_HANDS = 5
PRIOR_STRENGTH = 12.0
DEFAULT_VPIP = 0.27
DEFAULT_PFR = 0.20
DEFAULT_AF = 1.4
DEFAULT_CBET = 0.55
DEFAULT_FOLD_TO_CBET = 0.50
MAX_AF = 10.0

MAX_DEVIATION_PP = 0.20

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
    "cbet": DEFAULT_CBET,
    "fold_to_cbet": DEFAULT_FOLD_TO_CBET,
}

_STREET_ORDER = {"preflop": 0, "flop": 1, "turn": 2, "river": 3}
_VOLUNTARY_ACTIONS = {"call", "bet", "raise", "all_in"}
_AGGRESSIVE_ACTIONS = {"bet", "raise"}
_CBET_RESPONSES = {"fold", "call", "raise", "all_in"}

Subject = Union[str, int]


def _neutral_shifts() -> Dict[str, float]:
    return {key: 0.0 for key in SHIFT_KEYS}


def _new_counts() -> dict:
    return {
        "hands": 0,
        "vpip_chances": 0,
        "vpip_done": 0,
        "pfr_chances": 0,
        "pfr_done": 0,
        "bets_raises": 0,
        "calls": 0,
        "cbet_opportunities": 0,
        "cbet_done": 0,
        "cbet_faced": 0,
        "cbet_folded": 0,
        "valid": True,
    }


def _new_hand() -> dict:
    return {
        "participants": set(),
        "seat_map": {},
        "preflop_opportunities": set(),
        "vpip": set(),
        "pfr": set(),
        "preflop_folded": set(),
        "preflop_aggressor": None,
        "street_max": defaultdict(float),
        "flop_bet_seen": False,
        "cbet_opportunity_recorded": False,
        "cbet_bettor": None,
        "cbet_responses": set(),
        "current_snapshot": tuple(),
        "current_snapshot_streets": tuple(),
        "last_observed_street": None,
        "seen_occurrences": Counter(),
        "match_sequence": tuple(),
        "match_sequence_streets": tuple(),
        "match_entries": tuple(),
    }


def _data_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.environ.get("BOT_DATA_DIR", os.path.join(os.path.dirname(here), "data"))


def _string_tuple(value) -> tuple:
    return tuple(str(x) for x in np.asarray(value).reshape(-1).tolist())


def _finite_2d(value, rows: int = None, cols: int = None) -> Optional[np.ndarray]:
    try:
        arr = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
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
    """Load optional compact field priors with a fail-closed schema check."""
    path = os.path.join(_data_dir(), "field_priors.npz")
    try:
        with np.load(path, allow_pickle=False) as data:
            version = int(np.asarray(data["schema_version"]).reshape(-1)[0])
            if version != 1:
                return None

            feature_names = _string_tuple(data["classifier_feature_names"])
            if not feature_names or any(name not in _DEFAULT_FEATURES for name in feature_names):
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
            if scales.shape != (len(feature_names),) or not np.all(np.isfinite(scales)):
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


def _normalise_street(value) -> Optional[str]:
    if not isinstance(value, str):
        return None
    street = value.strip().lower().replace("-", "_")
    street = {"pre_flop": "preflop", "pre": "preflop"}.get(street, street)
    return street if street in _STREET_ORDER else None


def _normalise_action(value) -> Optional[str]:
    if not isinstance(value, str):
        return None
    action = value.strip().lower().replace("-", "_").replace(" ", "_")
    action = {
        "allin": "all_in",
        "all_in_raise": "all_in",
        "smallblind": "small_blind",
        "bigblind": "big_blind",
        "sb": "small_blind",
        "bb": "big_blind",
    }.get(action, action)
    allowed = {
        "ante", "small_blind", "big_blind", "fold", "check", "call",
        "bet", "raise", "all_in",
    }
    return action if action in allowed else None


def _safe_seat(value) -> Optional[int]:
    if isinstance(value, bool):
        return None
    try:
        seat = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return seat if 0 <= seat <= 100 else None


def _safe_bot_id(value) -> Optional[str]:
    if value is None or isinstance(value, bool):
        return None
    try:
        bot_id = str(value).strip()
    except Exception:
        return None
    if not bot_id or len(bot_id) > 256:
        return None
    return bot_id


def _safe_amount(value) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(amount) or amount < 0:
        return None
    return amount


def _freeze(value, depth: int = 0):
    """Return a stable, bounded fingerprint component for a log entry."""
    if depth > 4:
        return "<depth>"
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "<nonfinite>"
    if isinstance(value, dict):
        return tuple(sorted((str(k), _freeze(v, depth + 1)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v, depth + 1) for v in value)
    return repr(value)[:128]


def _entry_signature(entry: dict) -> Optional[tuple]:
    return _freeze(entry) if isinstance(entry, dict) else None


def _valid_action_entry(entry) -> bool:
    if not isinstance(entry, dict) or _normalise_action(entry.get("action")) is None:
        return False
    if _safe_seat(entry.get("seat")) is None and _safe_bot_id(entry.get("bot_id")) is None:
        return False
    action = _normalise_action(entry.get("action"))
    if action in {"small_blind", "big_blind", "bet", "raise"}:
        return _safe_amount(entry.get("amount")) is not None
    amount = entry.get("amount")
    return amount is None or _safe_amount(amount) is not None


def _entry_street(entry: dict) -> Optional[str]:
    for key in ("street", "round", "betting_round"):
        street = _normalise_street(entry.get(key))
        if street is not None:
            return street
    return None


def _hand_key(value) -> Optional[str]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    try:
        key = str(value).strip()
    except Exception:
        return None
    return key if key and len(key) <= 256 else None


def _counter_value(counts: dict, key: str) -> Optional[int]:
    value = counts.get(key, 0)
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(numeric) or numeric < 0 or not numeric.is_integer():
        return None
    return int(numeric)


class OpponentModel:
    """Persistent per-``bot_id`` tracker for a single match process."""

    def __init__(self):
        self._counts = defaultdict(_new_counts)
        self._hands = defaultdict(_new_hand)
        self._seat_to_bot: Dict[int, str] = {}
        self._bot_to_seat: Dict[str, int] = {}

    # ------------------------------------------------------------------ identity
    def _bind_players(self, players) -> Dict[int, str]:
        """Validate a seat map and retain only unambiguous bot identities."""
        if not isinstance(players, (list, tuple)):
            return {}
        candidates: Dict[int, str] = {}
        bad_seats = set()
        seen_bots: Dict[str, int] = {}
        for player in players:
            if not isinstance(player, dict):
                continue
            seat = _safe_seat(player.get("seat"))
            bot_id = _safe_bot_id(player.get("bot_id"))
            if seat is None or bot_id is None:
                continue
            if seat in candidates and candidates[seat] != bot_id:
                bad_seats.add(seat)
                continue
            if bot_id in seen_bots and seen_bots[bot_id] != seat:
                bad_seats.update((seat, seen_bots[bot_id]))
                continue
            candidates[seat] = bot_id
            seen_bots[bot_id] = seat

        for seat in bad_seats:
            candidates.pop(seat, None)
        # ``players`` is a point-in-time full table snapshot. Rebuild the
        # lookup instead of retaining stale seats after busts/reindexing.
        self._seat_to_bot = dict(candidates)
        self._bot_to_seat = {bot_id: seat for seat, bot_id in candidates.items()}
        for bot_id in candidates.values():
            self._counts[bot_id]
        return candidates

    def identity_for(self, seat, players=None) -> Optional[str]:
        """Resolve a seat to a stable bot id, or ``None`` if unsafe."""
        if players is not None:
            mapping = self._bind_players(players)
            parsed = _safe_seat(seat)
            if parsed in mapping:
                return mapping[parsed]
        parsed = _safe_seat(seat)
        return self._seat_to_bot.get(parsed) if parsed is not None else None

    @staticmethod
    def _mapping_consistent(players, mapping: Dict[int, str]) -> bool:
        if not isinstance(players, (list, tuple)):
            return True
        for player in players:
            if not isinstance(player, dict):
                return False
            seat = _safe_seat(player.get("seat"))
            bot_id = _safe_bot_id(player.get("bot_id"))
            if seat is not None and bot_id is not None and mapping.get(seat) != bot_id:
                return False
        return True

    def _profile_key(self, subject: Subject, players=None, *, legacy: bool = True):
        if isinstance(subject, str):
            return _safe_bot_id(subject)
        seat = _safe_seat(subject)
        if seat is None:
            return None
        bot_id = self.identity_for(seat, players)
        if bot_id is not None:
            return bot_id
        return seat if legacy else None

    def _entry_identity(self, entry: dict, hand: dict):
        bot_id = _safe_bot_id(entry.get("bot_id"))
        seat = _safe_seat(entry.get("seat"))
        if bot_id is not None:
            mapped = hand["seat_map"].get(seat) if seat is not None else None
            if mapped is not None and mapped != bot_id:
                return None
            # Historical entries identify their actor, but must not rewrite
            # the current seat map after a bust or table reindex.
            self._counts[bot_id]
            return bot_id
        if seat is not None:
            return hand["seat_map"].get(seat, self._seat_to_bot.get(seat, seat))
        return None

    # -------------------------------------------------------------- observations
    def _participant_key(self, player: dict):
        seat = _safe_seat(player.get("seat")) if isinstance(player, dict) else None
        bot_id = _safe_bot_id(player.get("bot_id")) if isinstance(player, dict) else None
        if bot_id is not None:
            # An ambiguous/duplicate player row was omitted from the validated
            # current seat map and must not create an opportunity.
            return bot_id if seat is not None and self._seat_to_bot.get(seat) == bot_id else None
        if seat is not None and seat in self._seat_to_bot:
            return self._seat_to_bot[seat]
        return seat

    def _register_participants(self, hand: dict, players) -> None:
        if not isinstance(players, (list, tuple)):
            return
        for player in players:
            if not isinstance(player, dict):
                continue
            state = str(player.get("state", "")).strip().lower()
            if state in {"out", "busted", "eliminated", "sitting_out"}:
                continue
            key = self._participant_key(player)
            if key is not None:
                hand["participants"].add(key)

    def _register_preflop_opportunity(self, hand: dict, key) -> None:
        if key is None or key in hand["preflop_opportunities"]:
            return
        counts = self._counts[key]
        counts["hands"] += 1
        counts["vpip_chances"] += 1
        counts["pfr_chances"] += 1
        hand["preflop_opportunities"].add(key)
        hand["participants"].add(key)

    def _register_all_preflop_opportunities(self, hand: dict) -> None:
        for key in tuple(hand["participants"]):
            self._register_preflop_opportunity(hand, key)

    def _is_aggressive(self, hand: dict, street: str, action: str, amount) -> bool:
        if action in _AGGRESSIVE_ACTIONS:
            return True
        if action != "all_in":
            return False
        numeric = _safe_amount(amount)
        if numeric is None:
            return False  # all-in can be a call
        return numeric > hand["street_max"][street]

    def _update_street_max(self, hand: dict, street: str, entry: dict) -> None:
        amount = _safe_amount(entry.get("amount"))
        if amount is not None:
            hand["street_max"][street] = max(hand["street_max"][street], amount)

    def _observe_cbet(self, hand: dict, key, action: str, aggressive: bool) -> None:
        aggressor = hand["preflop_aggressor"]
        if aggressor is None:
            return

        bettor = hand["cbet_bettor"]
        if bettor is not None and key != bettor and key not in hand["cbet_responses"]:
            if action in _CBET_RESPONSES:
                counts = self._counts[key]
                counts["cbet_faced"] += 1
                if action == "fold":
                    counts["cbet_folded"] += 1
                hand["cbet_responses"].add(key)

        if hand["cbet_opportunity_recorded"]:
            return
        if hand["flop_bet_seen"] and key != aggressor:
            return

        if key == aggressor:
            if aggressive:
                counts = self._counts[key]
                counts["cbet_opportunities"] += 1
                counts["cbet_done"] += 1
                hand["cbet_opportunity_recorded"] = True
                hand["cbet_bettor"] = key
                hand["flop_bet_seen"] = True
            elif action == "check":
                self._counts[key]["cbet_opportunities"] += 1
                hand["cbet_opportunity_recorded"] = True
            return

        if aggressive:  # a donk bet removes the clean c-bet opportunity
            hand["flop_bet_seen"] = True
            hand["cbet_opportunity_recorded"] = True

    def _process_action(self, hand: dict, entry: dict, street: str) -> None:
        action = _normalise_action(entry.get("action"))
        if action is None:
            return
        key = self._entry_identity(entry, hand)
        if key is None:
            return
        aggressive = self._is_aggressive(hand, street, action, entry.get("amount"))

        if street == "preflop":
            self._register_preflop_opportunity(hand, key)
            if action in _VOLUNTARY_ACTIONS and key not in hand["vpip"]:
                self._counts[key]["vpip_done"] += 1
                hand["vpip"].add(key)
            if aggressive and key not in hand["pfr"]:
                self._counts[key]["pfr_done"] += 1
                hand["pfr"].add(key)
            if aggressive:
                hand["preflop_aggressor"] = key
            if action == "fold":
                hand["preflop_folded"].add(key)
        else:
            if aggressive:
                self._counts[key]["bets_raises"] += 1
            elif action in {"call", "all_in"}:
                self._counts[key]["calls"] += 1
            if street == "flop":
                self._observe_cbet(hand, key, action, aggressive)

        self._update_street_max(hand, street, entry)

    def _process_sequence(
        self, hand: dict, entries: List[dict], streets: List[Optional[str]]
    ) -> None:
        occurrence = Counter()
        for entry, street in zip(entries, streets):
            if street is None:
                continue
            signature = _entry_signature(entry)
            if signature is None:
                continue
            token = (street, signature)
            occurrence[token] += 1
            ordinal = occurrence[token]
            if ordinal <= hand["seen_occurrences"][token]:
                continue
            self._process_action(hand, entry, street)
            hand["seen_occurrences"][token] = ordinal

    def _ingest_current_snapshot(self, hand: dict, entries, current_street: str) -> None:
        if not isinstance(entries, (list, tuple)):
            return
        if any(not _valid_action_entry(entry) for entry in entries):
            return
        signatures = tuple(_entry_signature(entry) for entry in entries)
        if any(signature is None for signature in signatures):
            return

        old = hand["current_snapshot"]
        old_streets = hand["current_snapshot_streets"]
        common = 0
        limit = min(len(old), len(signatures))
        while common < limit and old[common] == signatures[common]:
            common += 1

        labels: List[Optional[str]] = list(old_streets[:common])
        if common < len(old) and hand["last_observed_street"] == current_street:
            return  # same-street rewrite is not a trustworthy append

        for index in range(common, len(entries)):
            explicit = _entry_street(entries[index])
            if explicit is not None:
                labels.append(explicit)
            elif current_street != "preflop" and (
                not old or hand["last_observed_street"] != current_street
            ):
                # First sight postflop, or a street transition: the unlabelled
                # suffix can contain our preceding-street action plus actions
                # from both rounds. There is no safe boundary to infer.
                labels.append(None)
            else:
                labels.append(current_street)

        self._process_sequence(hand, list(entries), labels)
        hand["current_snapshot"] = signatures
        hand["current_snapshot_streets"] = tuple(labels)
        hand["last_observed_street"] = current_street

    def observe_state(self, game_state: dict) -> None:
        """Incrementally ingest one engine ``decide`` observation."""
        if not isinstance(game_state, dict):
            return
        hand_id = _hand_key(game_state.get("hand_id", game_state.get("hand_num")))
        street = _normalise_street(game_state.get("street"))
        if hand_id is None or street is None:
            return
        players = game_state.get("players")
        mapping = self._bind_players(players)
        if not self._mapping_consistent(players, mapping):
            return
        actions = game_state.get("action_log") or []
        if not isinstance(actions, (list, tuple)) or any(
            not _valid_action_entry(entry) for entry in actions
        ):
            return
        hand = self._hands[hand_id]
        hand["seat_map"].update(mapping)
        self._register_participants(hand, players)
        if street == "preflop":
            self._register_all_preflop_opportunities(hand)
        self._ingest_current_snapshot(hand, actions, street)

    @staticmethod
    def _longest_overlap(left: tuple, right: tuple) -> int:
        for size in range(min(len(left), len(right)), 0, -1):
            if left[-size:] == right[:size]:
                return size
        return 0

    def _ingest_match_group(
        self, hand: dict, entries: List[dict], fallback_street: Optional[str]
    ) -> None:
        incoming = tuple(_entry_signature(entry) for entry in entries)
        if any(signature is None for signature in incoming):
            return
        labels = tuple(_entry_street(entry) or fallback_street for entry in entries)
        known = hand["match_sequence"]
        known_labels = hand["match_sequence_streets"]
        known_entries = hand["match_entries"]

        if not known:
            combined = incoming
            combined_labels = labels
            combined_entries = tuple(entries)
        elif len(incoming) <= len(known) and any(
            known[i:i + len(incoming)] == incoming
            for i in range(len(known) - len(incoming) + 1)
        ):
            return
        elif len(known) <= len(incoming) and incoming[:len(known)] == known:
            combined = incoming
            combined_labels = known_labels + labels[len(known):]
            combined_entries = tuple(entries)
        else:
            overlap = self._longest_overlap(known, incoming)
            if overlap == 0:
                return
            combined = known + incoming[overlap:]
            combined_labels = known_labels + labels[overlap:]
            combined_entries = known_entries + tuple(entries[overlap:])

        self._process_sequence(hand, list(combined_entries), list(combined_labels))
        hand["match_sequence"] = combined
        hand["match_sequence_streets"] = combined_labels
        hand["match_entries"] = combined_entries

    def observe_log(
        self,
        match_action_log: List[dict],
        current_hand_id: str = None,
        *,
        players=None,
        street: str = None,
    ) -> None:
        """Compatibility ingestion for a rolling historical log.

        Entries should carry ``hand_id``/``hand_num`` and ``street``. A caller
        may pass ``street`` only when the entire supplied log belongs to it.
        Unlabelled history is never guessed to be preflop.
        """
        if not isinstance(match_action_log, (list, tuple)) or not match_action_log:
            return
        if any(not _valid_action_entry(entry) for entry in match_action_log):
            return
        mapping = self._bind_players(players)
        if not self._mapping_consistent(players, mapping):
            return
        fallback = _normalise_street(street)
        groups: Dict[str, List[dict]] = {}
        order: List[str] = []
        for entry in match_action_log:
            entry_hand = None
            for key in ("hand_id", "hand_num", "hand"):
                entry_hand = _hand_key(entry.get(key))
                if entry_hand is not None:
                    break
            if entry_hand is None:
                entry_hand = _hand_key(current_hand_id)
            if entry_hand is None:
                continue
            if entry_hand not in groups:
                groups[entry_hand] = []
                order.append(entry_hand)
            groups[entry_hand].append(entry)

        for hand_id in order:
            hand = self._hands[hand_id]
            hand["seat_map"].update(mapping)
            self._register_participants(hand, players)
            entries = groups[hand_id]
            has_preflop = fallback == "preflop" or any(
                _entry_street(entry) == "preflop" for entry in entries
            )
            if has_preflop:
                self._register_all_preflop_opportunities(hand)
            self._ingest_match_group(hand, entries, fallback)

    # --------------------------------------------------------------------- reads
    def _validated_counts(self, key) -> Optional[dict]:
        if key is None or key not in self._counts:
            return None
        counts = self._counts[key]
        if counts.get("valid", True) is not True:
            return None
        names = (
            "hands", "vpip_chances", "vpip_done", "pfr_chances", "pfr_done",
            "bets_raises", "calls", "cbet_opportunities", "cbet_done",
            "cbet_faced", "cbet_folded",
        )
        clean = {name: _counter_value(counts, name) for name in names}
        if any(value is None for value in clean.values()):
            return None
        if clean["vpip_done"] > clean["vpip_chances"]:
            return None
        if clean["pfr_done"] > clean["pfr_chances"]:
            return None
        if clean["cbet_done"] > clean["cbet_opportunities"]:
            return None
        if clean["cbet_folded"] > clean["cbet_faced"]:
            return None
        return clean

    @staticmethod
    def _posterior(successes: int, chances: int, mean: float, strength: float) -> float:
        if chances <= 0:
            return float(np.clip(mean, 0.0, 1.0))
        value = (successes + mean * strength) / (chances + strength)
        return float(np.clip(value, 0.0, 1.0))

    @staticmethod
    def _sample_size(clean: Optional[dict]) -> int:
        if clean is None:
            return 0
        return max(clean["hands"], clean["vpip_chances"], clean["pfr_chances"])

    def confidence(self, subject: Subject, players=None) -> float:
        """Bayesian-style evidence ramp, normalised to 1 at 30 hands."""
        key = self._profile_key(subject, players)
        clean = self._validated_counts(key)
        n = self._sample_size(clean)
        if n < MIN_RELIABLE_HANDS:
            return 0.0
        raw = n / (n + PRIOR_STRENGTH)
        warm = WARMUP_HANDS / (WARMUP_HANDS + PRIOR_STRENGTH)
        return float(np.clip(raw / warm, 0.0, 1.0))

    def is_warm(self, subject: Subject, players=None) -> bool:
        key = self._profile_key(subject, players)
        return self._sample_size(self._validated_counts(key)) >= WARMUP_HANDS

    def features(self, subject: Subject, players=None) -> Dict[str, float]:
        key = self._profile_key(subject, players)
        clean = self._validated_counts(key)
        if clean is None:
            return {**_DEFAULT_FEATURES, "hands": 0, "confidence": 0.0}

        vpip = self._posterior(
            clean["vpip_done"], clean["vpip_chances"], DEFAULT_VPIP, PRIOR_STRENGTH
        )
        pfr = self._posterior(
            clean["pfr_done"], clean["pfr_chances"], DEFAULT_PFR, PRIOR_STRENGTH
        )
        cbet = self._posterior(
            clean["cbet_done"], clean["cbet_opportunities"], DEFAULT_CBET,
            PRIOR_STRENGTH / 2.0,
        )
        fold_to_cbet = self._posterior(
            clean["cbet_folded"], clean["cbet_faced"], DEFAULT_FOLD_TO_CBET,
            PRIOR_STRENGTH / 2.0,
        )

        aggression_actions = clean["bets_raises"] + clean["calls"]
        if aggression_actions:
            prior_p = DEFAULT_AF / (DEFAULT_AF + 1.0)
            p_aggressive = self._posterior(
                clean["bets_raises"], aggression_actions, prior_p, PRIOR_STRENGTH / 2.0
            )
            p_aggressive = float(np.clip(p_aggressive, 0.0, 0.99))
            af = float(np.clip(p_aggressive / max(1.0 - p_aggressive, 0.01), 0.0, MAX_AF))
        else:
            af = DEFAULT_AF

        return {
            "vpip": float(np.clip(vpip, 0.0, 1.0)),
            "pfr": float(np.clip(pfr, 0.0, 1.0)),
            "af": af,
            "cbet": float(np.clip(cbet, 0.0, 1.0)),
            "fold_to_cbet": float(np.clip(fold_to_cbet, 0.0, 1.0)),
            "hands": clean["hands"],
            "confidence": self.confidence(subject, players),
        }

    def raw_counts(self, subject: Subject, players=None) -> Dict[str, int]:
        """Return a defensive copy of validated counters for diagnostics."""
        key = self._profile_key(subject, players)
        clean = self._validated_counts(key)
        return dict(clean) if clean is not None else {}

    def archetype(self, subject: Subject, players=None) -> str:
        if self.confidence(subject, players) <= 0.0:
            return "unknown"
        features = self.features(subject, players)
        tight = features["vpip"] < 0.22
        aggressive = features["af"] > 2.0 or features["pfr"] > 0.18
        if tight and aggressive:
            return "tight_aggressive"
        if tight:
            return "tight_passive"
        if aggressive:
            return "loose_aggressive"
        return "loose_passive"

    def _prior_cluster_idx(self, subject: Subject, players=None) -> Optional[int]:
        priors = _FIELD_PRIORS
        if not isinstance(priors, dict):
            return None
        try:
            feature_names = tuple(priors["feature_names"])
            centroids = np.asarray(priors["cluster_centroids"], dtype=np.float32)
            scales = np.asarray(priors["cluster_scales"], dtype=np.float32).reshape(-1)
        except (KeyError, TypeError, ValueError):
            return None
        if not feature_names or any(name not in _DEFAULT_FEATURES for name in feature_names):
            return None
        if centroids.ndim != 2 or centroids.shape[1] != len(feature_names):
            return None
        if scales.shape != (len(feature_names),):
            return None
        if not np.all(np.isfinite(centroids)) or not np.all(np.isfinite(scales)):
            return None
        if np.any(scales <= 0):
            return None

        features = self.features(subject, players)
        values = np.array(
            [float(features.get(name, _DEFAULT_FEATURES[name])) for name in feature_names],
            dtype=np.float32,
        )
        if not np.all(np.isfinite(values)):
            return None
        centered = (values - centroids) / scales
        distances = np.sum(centered * centered, axis=1)
        if distances.size == 0 or not np.all(np.isfinite(distances)):
            return None
        return int(np.argmin(distances))

    def exploit_shift(self, subject: Subject, players=None) -> Dict[str, float]:
        """Return complete, bounded and confidence-scaled strategy shifts."""
        shifts = _neutral_shifts()
        confidence = self.confidence(subject, players)
        if confidence <= 0.0:
            return shifts
        index = self._prior_cluster_idx(subject, players)
        if index is None:
            return shifts
        try:
            table = np.asarray(_FIELD_PRIORS["shift_by_cluster"], dtype=np.float64)
            if table.ndim != 2 or table.shape[1] != len(SHIFT_KEYS):
                return shifts
            prior_values = table[index]
        except (KeyError, IndexError, TypeError, ValueError):
            return shifts
        if not np.all(np.isfinite(prior_values)):
            return shifts
        for key, value in zip(SHIFT_KEYS, prior_values):
            scaled = float(value) * confidence
            shifts[key] = float(np.clip(scaled, -MAX_DEVIATION_PP, MAX_DEVIATION_PP))
        return shifts


_MODEL = OpponentModel()


def get_model() -> OpponentModel:
    return _MODEL
