"""Accuracy tests for the Monte-Carlo equity estimator.

Two checks, both engine-free:

* **Anchor** — the MC estimate of a well-known all-in equity (AKs vs an exact
  pair of queens, ~46% preflop) matches the published figure.
* **Convergence** — on a turn spot the remaining board is small enough to
  enumerate exactly, so we can confirm the MC estimate converges to the
  enumerated ground truth as the trial count grows.

These test the estimator's accuracy, not `numpy`/`eval7` internals.
"""
from src.equity import equity_vs_range
from tools.equity_study import exact_equity_vs_range


def test_mc_anchor_aks_vs_qq():
    """AKs vs a fixed QQ is ~46% all-in preflop (a standard, published number)."""
    eq = equity_vs_range(["Ah", "Kh"], [], ["QQ"], trials=20000)
    assert 0.44 <= eq <= 0.48, eq


def test_mc_converges_to_exact_on_turn():
    """On the turn (one card to come) enumerate the exact equity, then show the
    MC estimate lands within ~1 pt of it and beats a low-trial estimate."""
    hero, board = ["Ah", "Kd"], ["Qs", "Jc", "2d", "7h"]
    villain_range = ["QJ", "TT", "AQ", "KK", "99"]

    exact = exact_equity_vs_range(hero, board, villain_range)
    assert 0.0 <= exact <= 1.0

    coarse = equity_vs_range(hero, board, villain_range, trials=100)
    fine = equity_vs_range(hero, board, villain_range, trials=10000)

    assert abs(fine - exact) < 0.015, (fine, exact)
    assert abs(fine - exact) < abs(coarse - exact), (coarse, fine, exact)


def test_exact_enumeration_is_deterministic_ground_truth():
    """The enumerated baseline does no sampling, so it is bit-for-bit stable."""
    hero, board = ["Ah", "Kd"], ["Qs", "Jc", "2d", "7h", "Ad"]
    villain_range = ["QJ", "TT", "AQ", "KK"]
    first = exact_equity_vs_range(hero, board, villain_range)
    second = exact_equity_vs_range(hero, board, villain_range)
    assert first == second
    assert 0.0 <= first <= 1.0
