from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.prediction import DECREASE, INCREASE, NO_CHANGE, actual_direction
from data_science_arcade.lessons.l17_hypothesis_detective.launch_data import generate_launch_data, metric_mean


def test_generated_data_matches_its_schema():
    dataset = generate_launch_data()
    dtesting.assert_matches_schema(dataset)


def test_repeat_purchase_rate_really_increases():
    dataset = generate_launch_data()
    before = metric_mean(dataset, "repeat_purchase_rate", "before")
    after = metric_mean(dataset, "repeat_purchase_rate", "after")
    assert before == 0.24
    assert round(after, 3) == 0.34
    assert actual_direction(before, after) == INCREASE


def test_average_order_value_really_decreases():
    dataset = generate_launch_data()
    before = metric_mean(dataset, "average_order_value", "before")
    after = metric_mean(dataset, "average_order_value", "after")
    assert before == 58.0
    assert after == 51.0
    assert actual_direction(before, after) == DECREASE


def test_support_contact_rate_is_basically_unchanged():
    dataset = generate_launch_data()
    before = metric_mean(dataset, "support_contact_rate", "before")
    after = metric_mean(dataset, "support_contact_rate", "after")
    assert round(before, 3) == 0.06
    assert round(after, 3) == 0.062
    assert actual_direction(before, after) == NO_CHANGE
