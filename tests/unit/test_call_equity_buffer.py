"""Pins range-aware call pricing without an arbitrary stack-fraction cap.

Engine-free: exercises src.commitment.can_call_large directly.
"""
from src.commitment import can_call_large, CALL_EQUITY_BUFFER, LARGE_CALL_MAX_OWED_FRACTION


def test_buffer_is_widened():
    # The marginal-call buffer was eased 0.03 -> 0.015 to reduce the documented
    # marginal-tier (equity 0.45-0.65) postflop over-fold. Lock the new value.
    assert CALL_EQUITY_BUFFER == 0.015


def test_marginal_hand_now_calls_at_widened_buffer():
    # A hand priced just inside the *new* buffer but outside the old one:
    # eq_strong = pot_odds + 0.02  ->  was a fold at 0.03, now a call at 0.015.
    pot_odds = 0.30
    owed_frac = 0.15  # below the stack cap, so the buffer governs
    eq_strong = pot_odds + 0.02
    assert can_call_large(eq_strong, pot_odds, owed_frac) is True
    # And a hand below the new buffer still folds.
    assert can_call_large(pot_odds + 0.01, pot_odds, owed_frac) is False


def test_priced_in_all_in_call_is_not_blocked_by_old_25pct_cap():
    assert LARGE_CALL_MAX_OWED_FRACTION == 1.0
    # With no future street, an all-in call realizes all equity and needs no
    # arbitrary 1.5-point realization buffer.
    assert can_call_large(0.31, 0.30, 1.0) is True
    assert can_call_large(0.29, 0.30, 1.0) is False
