import pytest

from src.equity import equity_vs_ranges, hand_strength, range_to_weighted_combos


def test_weighted_range_expansion_does_not_double_count_overlaps():
    combos = range_to_weighted_combos({"QQ+": 0.4, "AA": 0.9})
    weights = {(str(c1), str(c2)): weight for (c1, c2), weight in combos}
    assert len(combos) == 18  # 6 combos each of QQ, KK, AA
    aa = [weight for (c1, c2), weight in weights.items()
          if c1[0] == "A" and c2[0] == "A"]
    assert aa and set(aa) == {0.9}


def test_exact_multiway_equity_conditions_on_card_collisions():
    hero = ["Th", "Td"]
    board = ["2c", "3d", "4h", "7s", "Jc"]
    villain_one = [(("As", "Ah"), 1.0), (("8s", "8h"), 1.0)]
    villain_two = [(("As", "Ah"), 1.0), (("9s", "9h"), 1.0)]
    # Four independent assignments exist, but AA/AA is physically impossible.
    # Of the three valid assignments, hero wins only 88/99.
    eq = equity_vs_ranges(hero, board, [villain_one, villain_two])
    assert eq == pytest.approx(1 / 3)


def test_three_way_tie_awards_one_third_not_one_half():
    hero = ["2c", "3d"]
    board = ["As", "Ks", "Qs", "Js", "Ts"]
    ranges = [
        [(("4c", "5d"), 1.0)],
        [(("6c", "7d"), 1.0)],
    ]
    assert equity_vs_ranges(hero, board, ranges) == pytest.approx(1 / 3)


def test_joint_random_equity_declines_from_heads_up_to_six_max():
    hero = ["Ah", "Kh"]
    board = ["As", "7d", "2c"]
    heads_up = hand_strength(hero, board, trials=2500, opponents=1)
    six_max = hand_strength(hero, board, trials=2500, opponents=5)
    assert 0.0 <= six_max <= heads_up <= 1.0
    assert heads_up - six_max > 0.10


def test_multiway_sampling_is_reproducible():
    args = (["Ah", "Kh"], ["As", "7d", "2c"], [["22+", "A2+"], ["22+", "K9+"]])
    first = equity_vs_ranges(*args, trials=600, adaptive=False, use_native=False)
    second = equity_vs_ranges(*args, trials=600, adaptive=False, use_native=False)
    assert first == second
