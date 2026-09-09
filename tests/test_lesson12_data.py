import pytest

from data_science_arcade.lessons.l12_groupby_kitchen.orders import (
    STORE_CUSTOMERS,
    cross_store_customers,
    distinct_dates,
    generate_orders,
    mastery_naive_mean_of_channel_avgs,
    mastery_network_avg_value,
    mastery_total_conversions,
    mastery_weighted_avg_value,
    naive_mean_of_store_aovs,
    network_aov,
    network_distinct_customers,
    store_distinct_customers,
    store_order_count,
    sum_of_store_distinct_customers,
    total_orders,
    total_revenue,
    weighted_aov,
)


def test_generates_the_expected_row_count():
    dataset = generate_orders()
    assert len(dataset.frame) == total_orders() == 90


def test_the_player_facing_frame_has_the_expected_columns():
    dataset = generate_orders()
    assert list(dataset.frame.columns) == ["order_id", "customer_id", "store_id", "order_date", "revenue"]


def test_per_store_order_counts_and_distinct_customers():
    assert store_order_count("S01") == 20
    assert store_distinct_customers("S01") == 16
    assert store_order_count("S02") == 30
    assert store_distinct_customers("S02") == 6
    assert store_order_count("S03") == 15
    assert store_distinct_customers("S03") == 15
    assert store_order_count("S04") == 25
    assert store_distinct_customers("S04") == 25


def test_s02_is_the_real_repeat_heavy_trap_store():
    # 30 order rows from just 6 real customers - the row-count-vs-nunique
    # trap for the unique_customers metric.
    assert store_order_count("S02") == 30
    assert store_distinct_customers("S02") == 6


def test_real_cross_store_customer_overlap_and_the_network_mismatch():
    dataset = generate_orders()
    assert sum_of_store_distinct_customers() == 62
    assert network_distinct_customers() == 54
    assert dataset.frame["customer_id"].nunique() == 54
    overlap = cross_store_customers()
    assert len(overlap) == 8
    # sum(per-store distinct) overcounts real network distinct by exactly
    # the number of cross-store customers, each double-counted once.
    assert sum_of_store_distinct_customers() - network_distinct_customers() == len(overlap)


def test_real_revenue_and_order_counts_reconcile_safely_across_stores():
    dataset = generate_orders()
    assert total_revenue() == 5300.0
    assert dataset.frame["revenue"].sum() == 5300.0
    assert sum(store_order_count(s) for s in STORE_CUSTOMERS) == total_orders() == len(dataset.frame)


def test_the_real_aov_triple_mismatch_and_weighted_equivalence():
    dataset = generate_orders()
    assert network_aov() == pytest.approx(58.888888888888886)
    assert float(dataset.frame["revenue"].mean()) == pytest.approx(network_aov())
    assert naive_mean_of_store_aovs() == pytest.approx(62.5)
    assert weighted_aov() == pytest.approx(network_aov())
    assert naive_mean_of_store_aovs() != pytest.approx(network_aov())


def test_order_date_cycles_through_seven_real_dates():
    dataset = generate_orders()
    assert distinct_dates() == 7
    assert dataset.frame["order_date"].nunique() == 7


# --- Optional mastery: channel attribution transfer ------------------------


def test_mastery_channel_attribution_numbers():
    assert mastery_total_conversions() == 125
    assert mastery_network_avg_value() == pytest.approx(28.8)
    assert mastery_naive_mean_of_channel_avgs() == pytest.approx(35.0)
    assert mastery_weighted_avg_value() == pytest.approx(mastery_network_avg_value())
    assert mastery_naive_mean_of_channel_avgs() != pytest.approx(mastery_network_avg_value())
