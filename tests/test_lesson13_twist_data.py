import pytest

from data_science_arcade.lessons.l13_join_junction.customers_orders import generate_orders
from data_science_arcade.lessons.l13_join_junction.twist_data import generate_promotions, naive_joined_revenue, true_total_revenue


def test_true_total_revenue_matches_the_original_order_amounts():
    assert true_total_revenue() == pytest.approx(350.0)


def test_naive_joined_revenue_is_inflated_by_the_many_to_many_join():
    # Real computed values (verified via a manual script before writing
    # this assertion), not hand-picked.
    orders = generate_orders()
    promotions = generate_promotions()
    assert naive_joined_revenue(orders, promotions) == pytest.approx(560.0)


def test_c01_order_is_tripled_and_c02_order_is_doubled_by_the_join():
    orders = generate_orders()
    promotions = generate_promotions()
    merged = orders.frame.merge(promotions.frame, on="customer_id", how="inner")
    assert (merged["customer_id"] == "C01").sum() == 3
    assert (merged["customer_id"] == "C02").sum() == 2
    assert (merged["customer_id"] == "C03").sum() == 1
