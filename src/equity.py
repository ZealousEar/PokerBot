"""Monte Carlo equity vs range using eval7.

Budget: ≤ 5 ms per call at default trials. Pre-warm eval7 LUTs at module
import so the live 2 s decisions don't pay a cold-start cost.
"""
# TODO (G3): import eval7, pre-warm LUTs.


def equity_vs_range(hero: tuple, board: tuple, villain_range, trials: int = 2000) -> float:
    """Return hero's equity vs villain_range as a float in [0, 1]."""
    raise NotImplementedError("G3")
