from data_science_arcade.data_engine.generators.customers import generate_customers
from data_science_arcade.data_engine.generators.orders import generate_orders
from data_science_arcade.data_engine.testing import assert_matches_schema, assert_unique


def test_same_seed_produces_identical_data():
    customers = generate_customers(seed=1, count=50)

    first = generate_orders(seed=42, customers=customers, count=100)
    second = generate_orders(seed=42, customers=customers, count=100)

    assert first.frame.equals(second.frame)


def test_row_count_matches_the_requested_count():
    customers = generate_customers(seed=1, count=50)
    assert len(generate_orders(seed=1, customers=customers, count=321).frame) == 321


def test_matches_its_own_schema():
    customers = generate_customers(seed=1, count=50)
    assert_matches_schema(generate_orders(seed=1, customers=customers, count=200))


def test_order_id_is_unique():
    customers = generate_customers(seed=1, count=50)
    assert_unique(generate_orders(seed=1, customers=customers, count=200), "order_id")


def test_every_order_references_a_real_customer():
    customers = generate_customers(seed=1, count=50)
    orders = generate_orders(seed=2, customers=customers, count=500)

    known_ids = set(customers.frame["customer_id"])
    assert set(orders.frame["customer_id"]).issubset(known_ids)


def test_an_inner_join_back_to_customers_matches_every_order():
    customers = generate_customers(seed=1, count=50)
    orders = generate_orders(seed=2, customers=customers, count=500)

    joined = orders.frame.merge(customers.frame, on="customer_id", how="inner")

    assert len(joined) == len(orders.frame)


def test_revenue_is_always_positive():
    customers = generate_customers(seed=1, count=50)
    orders = generate_orders(seed=1, customers=customers, count=500)

    assert (orders.frame["revenue"] > 0).all()
