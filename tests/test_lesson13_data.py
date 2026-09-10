import pandas as pd
import pytest

from data_science_arcade.lessons.l13_join_junction.orders import (
    ACTIVE_PROMOTIONS_DISTINCT_CUSTOMERS,
    ACTIVE_PROMOTIONS_ROWS,
    CONCRETE_EXAMPLE_CUSTOMER_ID,
    CONCRETE_EXAMPLE_ORDER_ID,
    CONCRETE_EXAMPLE_REVENUE,
    CUSTOMERS_NEVER_ORDERED,
    CUSTOMERS_TOTAL,
    CUSTOMERS_WITH_ORDERS,
    GUEST_ORDERS,
    JOIN1_INNER_ROW_COUNT,
    JOIN1_LEFT_ROW_COUNT,
    JOIN1_OUTER_ROW_COUNT,
    MATCHED_ORDERS,
    ORDERS_DISTINCT_CUSTOMER_IDS,
    RAW_PROMO_JOIN_ROW_COUNT,
    REPAIRED_PROMO_JOIN_ROW_COUNT,
    TOTAL_ORDERS,
    generate_active_promotions,
    generate_customers,
    generate_orders,
)


@pytest.fixture()
def customers():
    return generate_customers()


@pytest.fixture()
def orders():
    return generate_orders()


@pytest.fixture()
def active_promotions():
    return generate_active_promotions()


def test_customers_table_is_the_real_declared_size_with_a_unique_key(customers):
    assert len(customers.frame) == CUSTOMERS_TOTAL
    assert customers.frame["customer_id"].is_unique


def test_orders_table_is_the_real_declared_size(orders):
    assert len(orders.frame) == TOTAL_ORDERS


def test_orders_split_into_real_matched_and_guest_rows(orders, customers):
    matched = orders.frame["customer_id"].isin(customers.frame["customer_id"])
    assert int(matched.sum()) == MATCHED_ORDERS
    assert int((~matched).sum()) == GUEST_ORDERS


def test_customers_split_into_real_ordering_and_never_ordered(orders, customers):
    ordering_customers = set(orders.frame.loc[orders.frame["customer_id"].isin(customers.frame["customer_id"]), "customer_id"])
    assert len(ordering_customers) == CUSTOMERS_WITH_ORDERS
    never_ordered = set(customers.frame["customer_id"]) - ordering_customers
    assert len(never_ordered) == CUSTOMERS_NEVER_ORDERED


def test_orders_customer_id_genuinely_repeats(orders):
    # Some customers order more than once - customer_id is NOT unique in
    # orders, the real fact stage 2's own key-cardinality inspection
    # shows before any join happens.
    assert orders.frame["customer_id"].nunique() == ORDERS_DISTINCT_CUSTOMER_IDS
    assert orders.frame["customer_id"].nunique() < len(orders.frame)


def test_join1_inner_left_outer_genuinely_disagree(orders, customers):
    inner = orders.frame.merge(customers.frame, on="customer_id", how="inner")
    left = orders.frame.merge(customers.frame, on="customer_id", how="left")
    outer = orders.frame.merge(customers.frame, on="customer_id", how="outer")
    assert len(inner) == JOIN1_INNER_ROW_COUNT == 108
    assert len(left) == JOIN1_LEFT_ROW_COUNT == 120
    assert len(outer) == JOIN1_OUTER_ROW_COUNT == 140
    assert len({len(inner), len(left), len(outer)}) == 3


def test_left_join_keeps_every_real_order_including_guests(orders, customers):
    left = orders.frame.merge(customers.frame, on="customer_id", how="left")
    assert len(left) == TOTAL_ORDERS


def test_active_promotions_is_a_real_one_to_many_key(active_promotions):
    assert len(active_promotions.frame) == ACTIVE_PROMOTIONS_ROWS == 47
    assert active_promotions.frame["customer_id"].nunique() == ACTIVE_PROMOTIONS_DISTINCT_CUSTOMERS == 20
    assert active_promotions.frame["customer_id"].nunique() < len(active_promotions.frame)


def test_raw_promotions_join_fans_out_to_the_real_acceptance_test_number(orders, active_promotions):
    raw = orders.frame.merge(active_promotions.frame, on="customer_id", how="left")
    assert len(raw) == RAW_PROMO_JOIN_ROW_COUNT == 147


def test_validate_many_to_one_raises_on_the_raw_promotions_join(orders, active_promotions):
    with pytest.raises(pd.errors.MergeError):
        orders.frame.merge(active_promotions.frame, on="customer_id", how="left", validate="many_to_one")


def test_preaggregating_promotions_produces_a_real_unique_key(active_promotions):
    promo_per_customer = active_promotions.frame.groupby("customer_id", as_index=False).agg(
        active_promotion_count=("promotion_code", "size")
    )
    assert len(promo_per_customer) == ACTIVE_PROMOTIONS_DISTINCT_CUSTOMERS
    assert promo_per_customer["customer_id"].is_unique


def test_the_repaired_join_returns_to_the_real_orders_row_count(orders, active_promotions):
    promo_per_customer = active_promotions.frame.groupby("customer_id", as_index=False).agg(
        active_promotion_count=("promotion_code", "size")
    )
    repaired = orders.frame.merge(promo_per_customer, on="customer_id", how="left", validate="many_to_one")
    assert len(repaired) == REPAIRED_PROMO_JOIN_ROW_COUNT == 120


def test_revenue_reconciles_after_the_repair_but_not_after_the_raw_join(orders, active_promotions):
    promo_per_customer = active_promotions.frame.groupby("customer_id", as_index=False).agg(
        active_promotion_count=("promotion_code", "size")
    )
    repaired = orders.frame.merge(promo_per_customer, on="customer_id", how="left", validate="many_to_one")
    raw = orders.frame.merge(active_promotions.frame, on="customer_id", how="left")

    real_total = orders.frame["revenue"].sum()
    assert repaired["revenue"].sum() == real_total
    assert raw["revenue"].sum() > real_total  # the raw join triple/double-counts fan-out customers' own revenue


def test_the_concrete_example_customer_has_exactly_one_order_and_three_promotions(orders, active_promotions):
    example_orders = orders.frame[orders.frame["customer_id"] == CONCRETE_EXAMPLE_CUSTOMER_ID]
    assert len(example_orders) == 1
    assert example_orders.iloc[0]["order_id"] == CONCRETE_EXAMPLE_ORDER_ID
    assert example_orders.iloc[0]["revenue"] == CONCRETE_EXAMPLE_REVENUE

    example_promos = active_promotions.frame[active_promotions.frame["customer_id"] == CONCRETE_EXAMPLE_CUSTOMER_ID]
    assert len(example_promos) == 3

    raw = orders.frame.merge(active_promotions.frame, on="customer_id", how="left")
    example_after_join = raw[raw["customer_id"] == CONCRETE_EXAMPLE_CUSTOMER_ID]
    assert len(example_after_join) == 3  # the real, concrete fan-out - never described as "duplicates"
