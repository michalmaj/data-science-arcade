import pytest

from data_science_arcade.lessons.l14_chart_designer.store_metrics import (
    generate_daily_revenue,
    generate_returns,
    generate_store_revenue,
    return_rate,
)


def test_store_revenue_has_three_distinct_stores():
    dataset = generate_store_revenue()
    assert len(dataset.frame) == 3
    assert dataset.frame["revenue"].nunique() == 3


def test_daily_revenue_has_five_weekdays_with_a_tuesday_dip():
    dataset = generate_daily_revenue()
    assert len(dataset.frame) == 5
    tuesday = dataset.frame.loc[dataset.frame["day"] == "Tue", "revenue"].iloc[0]
    other_days = dataset.frame.loc[dataset.frame["day"] != "Tue", "revenue"]
    assert tuesday < other_days.min()


def test_return_rates_are_computed_not_hand_picked():
    # Real computed values (verified via a manual script before writing
    # this assertion): returns / orders per store.
    returns = generate_returns()
    assert return_rate(returns, "S01") == pytest.approx(0.25)
    assert return_rate(returns, "S02") == pytest.approx(0.03)
    assert return_rate(returns, "S03") == pytest.approx(0.08)


def test_raw_return_count_ranking_is_the_exact_opposite_of_the_rate_ranking():
    returns = generate_returns()
    frame = returns.frame
    by_count = list(frame.sort_values("returns", ascending=False)["store_id"])
    rates = {store_id: return_rate(returns, store_id) for store_id in frame["store_id"]}
    by_rate = sorted(rates, key=lambda store_id: rates[store_id], reverse=True)
    assert by_count == list(reversed(by_rate))
