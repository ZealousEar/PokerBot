"""Per-seat opponent frequency tracker.

Tracks VPIP, PFR, AF (aggression factor), FoldToCBet. Exploit shifts apply
only after a 30-hand warmup per seat — before that, use baseline frequencies.

# Source: [[PokerBot/OpponentModeling/Billings-Davidson-Schauenberg]]
"""
WARMUP_HANDS = 30


class OpponentModel:
    """Rolling counters per seat. Updated from each hand's action_log."""

    def __init__(self):
        # TODO (G3): per-seat dict of counters {vpip, pfr, af, fold_to_cbet, hands}
        self._hands_seen = 0

    def observe_hand(self, hand_event: dict) -> None:
        """Update counters from a completed-hand event."""
        self._hands_seen += 1

    def is_warm_for(self, seat_id: int) -> bool:
        return self._hands_seen >= WARMUP_HANDS

    def features(self, seat_id: int) -> dict:
        """Return {vpip, pfr, af, fold_to_cbet} for the given seat."""
        # TODO (G3): implement
        return {}
