from data_science_arcade.lessons.l10_validation_gate.twist_data import (
    generate_orders_feed,
    naive_average,
    true_average,
)


def test_naive_average_is_wildly_inflated_by_the_cents_mistake():
    dataset = generate_orders_feed()
    assert naive_average(dataset) == 3862.5


def test_true_average_once_units_are_corrected():
    dataset = generate_orders_feed()
    assert true_average(dataset) == 150.0


def test_the_cents_mistake_still_falls_within_a_sane_looking_order_range():
    # The whole point of the twist: nothing about these values looks
    # invalid on its own - a $0-$100,000 range check would never flag them.
    dataset = generate_orders_feed()
    assert dataset.frame["recorded_amount"].max() == 15_000.0
    assert dataset.frame["recorded_amount"].min() > 0


def test_two_hundred_orders_total():
    dataset = generate_orders_feed()
    assert len(dataset.frame) == 200
