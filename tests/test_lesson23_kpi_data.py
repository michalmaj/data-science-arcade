import pandas as pd
import pytest

from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.timeseries import LensOption, TimeSeriesRequest
from data_science_arcade.lessons.l23_time_series_control_room.kpi_data import (
    CAMPAIGN_DAY,
    PERIOD_LENGTH_DAYS,
    RELEASE_DAY,
    build_time_series,
    conversion_rate,
    day_rate_with_baseline_mirror_code,
    generate_kpi_data,
    timeseries_lens_mirror_code,
    weekday_baseline_mirror_code,
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


def _exec_code(code: str, namespace: dict) -> dict:
    exec(code, namespace)
    return namespace


@pytest.mark.parametrize(
    "period,day,expected_pct",
    [("current", 13, 20.0), ("previous", 13, 20.0), ("current", 14, 19.0), ("previous", 14, 19.0), ("current", 8, 29.0), ("previous", 8, 25.0)],
)
def test_day_rate_with_baseline_mirror_code_final_variable_matches_the_displayed_rate(period, day, expected_pct):
    """The P0 regression: the FINAL {var_name} variable this snippet
    assigns must equal the plain rate - the exact same quantity a
    ComparisonValue built from this day actually displays - never the
    residual, which is only ever an auxiliary computed extra."""
    daily_kpi = generate_kpi_data().frame
    ns = _exec_code(day_rate_with_baseline_mirror_code(period, day, "x"), {"daily_kpi": daily_kpi, "pd": pd})
    assert round(ns["x"] * 100, 1) == expected_pct


def test_day_rate_with_baseline_mirror_code_residual_is_a_real_auxiliary_not_the_final_value():
    daily_kpi = generate_kpi_data().frame
    ns = _exec_code(day_rate_with_baseline_mirror_code("current", CAMPAIGN_DAY, "x"), {"daily_kpi": daily_kpi, "pd": pd})
    assert round(ns["x_residual"], 2) == 0.04
    assert ns["x"] != ns["x_residual"]  # displayed value and auxiliary residual are genuinely different quantities


@pytest.mark.parametrize("day", [12, 13, 14])
def test_release_window_and_release_day_residuals_are_zero(day):
    daily_kpi = generate_kpi_data().frame
    ns = _exec_code(day_rate_with_baseline_mirror_code("current", day, "x"), {"daily_kpi": daily_kpi, "pd": pd})
    assert abs(ns["x_residual"]) < 1e-9


def test_weekday_baseline_mirror_code_uses_the_full_three_week_reference_period_not_a_single_day():
    """weekday=0 is Monday - the baseline must equal the mean of every
    Monday in the `previous` period (3 occurrences), never a single
    day's own previous-period lookup."""
    daily_kpi = generate_kpi_data().frame
    ns = _exec_code(weekday_baseline_mirror_code(0, "x"), {"daily_kpi": daily_kpi, "pd": pd})
    reference_mondays = daily_kpi[(daily_kpi["period"] == "previous") & (((daily_kpi["day"] - 1) % 7) == 0)]
    assert len(reference_mondays) == 3
    expected = (reference_mondays["conversions"] / reference_mondays["visits"]).mean()
    assert ns["x"] == expected


@pytest.mark.parametrize("weekday,expected_pct", [(0, 25.0), (5, 20.0), (6, 19.0)])
def test_weekday_baseline_mirror_code_reconciles_to_the_real_verified_numbers(weekday, expected_pct):
    daily_kpi = generate_kpi_data().frame
    ns = _exec_code(weekday_baseline_mirror_code(weekday, "x"), {"daily_kpi": daily_kpi, "pd": pd})
    assert round(ns["x"] * 100, 1) == expected_pct


def test_timeseries_lens_mirror_code_with_same_days_previous_period_shows_both_periods():
    daily_kpi = generate_kpi_data().frame
    request = TimeSeriesRequest(key="release_dip_claim", prompt_key="x", highlight_days=(13, 14), options=())
    option = LensOption("same_days_previous_period", "x", show_previous_period=True)
    ns = _exec_code(timeseries_lens_mirror_code(request, option, "x"), {"daily_kpi": daily_kpi, "pd": pd})
    assert set(ns["x"]["day"]) == {13, 14}
    assert set(ns["x_reference"]["day"]) == {13, 14}
    assert (ns["x"]["period"] == "current").all()
    assert (ns["x_reference"]["period"] == "previous").all()


def test_timeseries_lens_mirror_code_with_nearby_days_only_shows_no_reference():
    daily_kpi = generate_kpi_data().frame
    request = TimeSeriesRequest(key="release_dip_claim", prompt_key="x", highlight_days=(13, 14), options=())
    option = LensOption("nearby_days_only", "x", show_previous_period=False)
    ns = _exec_code(timeseries_lens_mirror_code(request, option, "x"), {"daily_kpi": daily_kpi, "pd": pd})
    assert "x_reference" not in ns
