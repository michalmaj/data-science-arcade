import pytest

from data_science_arcade.lessons.l23_time_series_control_room.kpi_data import build_time_series, generate_kpi_data
from data_science_arcade.lessons.l23_time_series_control_room.requests import CORRECT_OPTION_BY_REQUEST, TIME_SERIES_REQUESTS


def test_all_three_requests_are_present():
    assert {request.key for request in TIME_SERIES_REQUESTS} == {
        "release_dip_claim",
        "campaign_lift_claim",
        "week_over_week_claim",
    }


def test_every_request_has_a_correct_option_recorded():
    assert set(CORRECT_OPTION_BY_REQUEST) == {request.key for request in TIME_SERIES_REQUESTS}


@pytest.mark.parametrize("request_", list(TIME_SERIES_REQUESTS))
def test_the_correct_option_is_among_the_offered_options(request_):
    correct = CORRECT_OPTION_BY_REQUEST[request_.key]
    assert correct in {option.key for option in request_.options}


@pytest.mark.parametrize("request_", list(TIME_SERIES_REQUESTS))
def test_every_request_offers_exactly_two_options(request_):
    assert len(request_.options) == 2


def test_correct_option_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in TIME_SERIES_REQUESTS:
        correct = CORRECT_OPTION_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.options) if option.key == correct))
    assert len(set(indexes)) > 1


@pytest.mark.parametrize("request_", list(TIME_SERIES_REQUESTS))
def test_the_same_days_previous_period_option_actually_shows_the_previous_period(request_):
    option = next(option for option in request_.options if option.key == "same_days_previous_period")
    assert option.show_previous_period is True


@pytest.mark.parametrize("request_", list(TIME_SERIES_REQUESTS))
def test_the_nearby_days_only_option_does_not_show_the_previous_period(request_):
    option = next(option for option in request_.options if option.key == "nearby_days_only")
    assert option.show_previous_period is False


@pytest.mark.parametrize("request_", list(TIME_SERIES_REQUESTS))
def test_every_highlighted_day_is_a_real_day_in_the_dataset(request_):
    dataset = generate_kpi_data()
    current = build_time_series(dataset, "current", "x")
    real_days = {point.day for point in current.points}
    assert set(request_.highlight_days) <= real_days
