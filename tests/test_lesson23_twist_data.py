from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l23_time_series_control_room.twist_data import generate_delivery_alert_data, on_time_rate


def test_generated_data_matches_its_schema():
    dataset = generate_delivery_alert_data()
    dtesting.assert_matches_schema(dataset)


def test_the_alert_day_looks_much_worse_than_a_normal_weekday():
    dataset = generate_delivery_alert_data()
    assert on_time_rate(dataset, "day_after_spring_holiday") == 0.71
    assert on_time_rate(dataset, "normal_weekday") == 0.89
    assert on_time_rate(dataset, "day_after_spring_holiday") < on_time_rate(dataset, "normal_weekday")


def test_a_different_holiday_shows_the_exact_same_dip():
    dataset = generate_delivery_alert_data()
    assert on_time_rate(dataset, "day_after_autumn_holiday") == 0.70


def test_it_recovers_on_its_own_two_days_later():
    dataset = generate_delivery_alert_data()
    assert on_time_rate(dataset, "two_days_after_spring_holiday") == 0.88
    assert on_time_rate(dataset, "two_days_after_spring_holiday") > on_time_rate(dataset, "day_after_spring_holiday")
