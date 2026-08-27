from data_science_arcade.lessons.l13_join_junction.customers_orders import (
    MATCHED_REVENUE,
    ORPHAN_ORDER_CUSTOMER_IDS,
    generate_customers,
    generate_orders,
    row_count_for,
)


def test_generates_the_expected_row_counts():
    customers = generate_customers()
    orders = generate_orders()
    assert len(customers.frame) == 8
    assert len(orders.frame) == 9


def test_inner_left_and_right_joins_disagree_on_row_count():
    # Real computed values (verified via a manual script before writing
    # this assertion), not hand-picked: inner/left/right joins on the
    # same two tables genuinely return different row counts.
    customers = generate_customers()
    orders = generate_orders()
    assert row_count_for(orders, customers, "inner") == 6
    assert row_count_for(orders, customers, "left") == 9
    assert row_count_for(orders, customers, "right") == 8


def test_every_matched_customer_has_exactly_one_order():
    orders = generate_orders()
    matched_orders = orders.frame[orders.frame["customer_id"].isin(MATCHED_REVENUE)]
    assert matched_orders["customer_id"].value_counts().max() == 1
    assert len(matched_orders) == len(MATCHED_REVENUE)


def test_orphan_orders_reference_a_customer_id_that_does_not_exist():
    customers = generate_customers()
    orders = generate_orders()
    known_ids = set(customers.frame["customer_id"])
    orphan_orders = orders.frame[orders.frame["customer_id"].isin(ORPHAN_ORDER_CUSTOMER_IDS)]
    assert len(orphan_orders) == len(ORPHAN_ORDER_CUSTOMER_IDS)
    assert known_ids.isdisjoint(set(orphan_orders["customer_id"]))


def test_some_customers_have_never_ordered():
    customers = generate_customers()
    orders = generate_orders()
    customers_with_orders = set(orders.frame["customer_id"]) & set(customers.frame["customer_id"])
    never_ordered = set(customers.frame["customer_id"]) - customers_with_orders
    assert len(never_ordered) == 2
