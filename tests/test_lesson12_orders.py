import pytest

from data_science_arcade.lessons.l12_groupby_kitchen.orders import (
    distinct_customers_by_store,
    generate_orders,
    order_count_by_store,
)


def test_generates_the_expected_row_count():
    dataset = generate_orders()
    assert len(dataset.frame) == 25


def test_sum_per_store_matches_the_hand_crafted_revenue_values():
    dataset = generate_orders()
    totals = dataset.frame.groupby("store_id")["revenue"].sum()
    assert totals["S01"] == pytest.approx(800.0)
    assert totals["S02"] == pytest.approx(1200.0)
    assert totals["S03"] == pytest.approx(1000.0)


def test_count_per_day_is_uniform_across_all_five_days():
    dataset = generate_orders()
    counts = dataset.frame.groupby("order_date")["revenue"].count()
    assert len(counts) == 5
    assert set(counts) == {5}


def test_grouping_by_order_id_produces_one_row_per_order():
    dataset = generate_orders()
    grouped = dataset.frame.groupby("order_id")["revenue"].count()
    assert len(grouped) == len(dataset.frame)


def test_store_s01_and_s03_have_no_repeat_customers():
    dataset = generate_orders()
    assert order_count_by_store(dataset, "S01") == distinct_customers_by_store(dataset, "S01")
    assert order_count_by_store(dataset, "S03") == distinct_customers_by_store(dataset, "S03")


def test_store_s02_order_count_overcounts_its_real_customer_base():
    # Real computed values (verified via a manual script before writing
    # this assertion), not hand-picked: S02's 10 orders came from just 4
    # repeat customers, not 10 different people.
    dataset = generate_orders()
    assert order_count_by_store(dataset, "S02") == 10
    assert distinct_customers_by_store(dataset, "S02") == 4


def test_total_order_rows_overcount_total_distinct_customers():
    dataset = generate_orders()
    assert len(dataset.frame) == 25
    assert dataset.frame["customer_id"].nunique() == 19
