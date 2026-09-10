import numpy as np

from data_science_arcade.lessons.l14_chart_designer.orders import (
    DAILY_ORDER_COUNTS,
    DATE_CYCLE,
    DELIVERY_BIN_COUNTS,
    DELIVERY_BIN_EDGES,
    MASTERY_MONTHS,
    MASTERY_SLA_COMPLIANCE_PCT,
    MASTERY_SLA_TARGET_PCT,
    STORE_IDS,
    STORE_ORDER_COUNTS,
    STORE_RETURN_COUNTS,
    STORE_RETURN_RATES,
    TOTAL_ORDERS,
    generate_orders,
)


def test_store_orders_and_returns_sum_to_the_real_260_total():
    assert sum(STORE_ORDER_COUNTS.values()) == TOTAL_ORDERS
    assert sum(STORE_ORDER_COUNTS.values()) == 260


def test_store_return_rates_are_real_and_distinct():
    assert STORE_RETURN_RATES == {"S01": 15.0, "S02": 8.0, "S03": 10.0, "S04": 5.0}
    assert len(set(STORE_RETURN_RATES.values())) == len(STORE_RETURN_RATES)


def test_daily_order_counts_are_real_chronological_and_sum_to_260():
    assert len(DATE_CYCLE) == 14
    assert len(DAILY_ORDER_COUNTS) == 14
    assert sum(DAILY_ORDER_COUNTS) == TOTAL_ORDERS
    assert DATE_CYCLE == sorted(DATE_CYCLE)  # already real chronological order


def test_histogram_bin_counts_reconcile_with_the_real_generated_frame():
    orders = generate_orders()
    counts, edges = np.histogram(orders.frame["delivery_minutes"], bins=list(DELIVERY_BIN_EDGES))
    assert tuple(int(c) for c in counts) == DELIVERY_BIN_COUNTS
    assert tuple(edges) == DELIVERY_BIN_EDGES
    assert sum(DELIVERY_BIN_COUNTS) == TOTAL_ORDERS


def test_all_three_views_reconcile_to_the_same_real_population():
    orders = generate_orders()
    assert len(orders.frame) == TOTAL_ORDERS
    assert orders.frame["store_id"].value_counts().to_dict() == STORE_ORDER_COUNTS
    assert int(orders.frame["returned"].sum()) == sum(STORE_RETURN_COUNTS.values())
    assert orders.frame.groupby("order_date").size().tolist() == DAILY_ORDER_COUNTS


def test_generated_orders_has_no_missing_values():
    orders = generate_orders()
    assert orders.frame.isna().sum().sum() == 0


def test_store_ids_are_real_and_stable_order():
    assert STORE_IDS == ("S01", "S02", "S03", "S04")


def test_mastery_domain_has_a_real_mixed_pattern_against_a_fixed_target():
    assert len(MASTERY_MONTHS) == 12
    assert len(MASTERY_SLA_COMPLIANCE_PCT) == 12
    missed = [month for month, pct in zip(MASTERY_MONTHS, MASTERY_SLA_COMPLIANCE_PCT) if pct < MASTERY_SLA_TARGET_PCT]
    hit = [month for month, pct in zip(MASTERY_MONTHS, MASTERY_SLA_COMPLIANCE_PCT) if pct >= MASTERY_SLA_TARGET_PCT]
    assert len(missed) == 5
    assert len(hit) == 7
