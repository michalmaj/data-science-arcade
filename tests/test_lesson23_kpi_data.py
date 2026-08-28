from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l23_time_series_control_room.kpi_data import (
    CAMPAIGN_DAY,
    PERIOD_LENGTH_DAYS,
    RELEASE_DAY,
    build_time_series,
    conversion_rate,
    generate_kpi_data,
)


def test_generated_data_matches_its_schema():
    dataset = generate_kpi_data()
    dtesting.assert_matches_schema(dataset)


def test_both_periods_have_the_full_run_of_days():
    dataset = generate_kpi_data()
    current = build_time_series(dataset, "current", "x")
    previous = build_time_series(dataset, "previous", "x")
    assert len(current.points) == PERIOD_LENGTH_DAYS
    assert len(previous.points) == PERIOD_LENGTH_DAYS
    assert [point.day for point in current.points] == list(range(1, PERIOD_LENGTH_DAYS + 1))


def test_weekend_days_are_identical_between_periods_even_around_the_release():
    # Days 13-14 (the weekend right after the release, day 12) look like a
    # dip only if you don't compare them to anything - they are exactly
    # the same as an ordinary weekend in the previous period.
    dataset = generate_kpi_data()
    for day in (13, 14):
        assert conversion_rate(dataset, "current", day) == conversion_rate(dataset, "previous", day)


def test_the_release_day_itself_gets_no_special_adjustment():
    dataset = generate_kpi_data()
    assert conversion_rate(dataset, "current", RELEASE_DAY) == conversion_rate(dataset, "previous", RELEASE_DAY)


def test_the_campaign_day_carries_a_real_four_point_lift():
    dataset = generate_kpi_data()
    lift = conversion_rate(dataset, "current", CAMPAIGN_DAY) - conversion_rate(dataset, "previous", CAMPAIGN_DAY)
    assert round(lift, 2) == 0.04


def test_week_three_matches_the_previous_periods_equivalent_week_exactly():
    # Week 3 (days 15-21) only looks like a decline against week 2, which
    # the campaign inflated. Against a normal baseline it's flat.
    dataset = generate_kpi_data()
    week3_avg = sum(conversion_rate(dataset, "current", day) for day in range(15, 22)) / 7
    previous_equivalent_avg = sum(conversion_rate(dataset, "previous", day) for day in range(15, 22)) / 7
    assert abs(week3_avg - previous_equivalent_avg) < 1e-9


def test_week_three_looks_like_a_decline_only_against_the_inflated_week_two():
    dataset = generate_kpi_data()
    week2_avg = sum(conversion_rate(dataset, "current", day) for day in range(8, 15)) / 7
    week3_avg = sum(conversion_rate(dataset, "current", day) for day in range(15, 22)) / 7
    assert week3_avg < week2_avg
