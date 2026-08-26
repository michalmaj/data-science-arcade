from data_science_arcade.lessons.l09_outlier_patrol.twist_data import (
    category_rate,
    generate_flagged_transactions,
)


def test_most_flagged_transactions_are_actually_legitimate():
    dataset = generate_flagged_transactions()
    assert category_rate(dataset, "legitimate") == 0.6


def test_only_a_quarter_of_flagged_transactions_are_actually_fraud():
    dataset = generate_flagged_transactions()
    assert category_rate(dataset, "fraud") == 0.25


def test_a_small_share_are_fixable_unit_errors():
    dataset = generate_flagged_transactions()
    assert category_rate(dataset, "unit_error") == 0.15


def test_twenty_flagged_transactions_total():
    dataset = generate_flagged_transactions()
    assert len(dataset.frame) == 20
