"""Pins the widened marginal-call gate (CALL_EQUITY_BUFFER) and the leak-fix cap.

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


def test_leak_fix_stack_cap_still_folds_big_commitments():
    # The Qual-II leak fix must survive: any call committing more than the cap
    # folds regardless of price, even a strong-equity hand.
    assert LARGE_CALL_MAX_OWED_FRACTION == 0.25
    assert can_call_large(0.99, 0.10, LARGE_CALL_MAX_OWED_FRACTION + 0.01) is False
