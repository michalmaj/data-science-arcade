from data_science_arcade.lessons.l23_time_series_control_room.kpi_data import build_time_series, generate_kpi_data
from data_science_arcade.lessons.l23_time_series_control_room.requests import CORRECT_OPTION_BY_REQUEST, TIME_SERIES_REQUESTS


def test_exactly_one_real_decision():
    """The two predecessor requests (campaign_lift_claim, week_over_week_claim)
    shared the identical same_days_previous_period answer - reduced to
    one real decision, not three redundant ones."""
    assert {request.key for request in TIME_SERIES_REQUESTS} == {"release_dip_claim"}


def test_every_request_has_a_correct_option_recorded():
    assert set(CORRECT_OPTION_BY_REQUEST) == {request.key for request in TIME_SERIES_REQUESTS}


def test_the_correct_option_is_among_the_offered_options():
    request = TIME_SERIES_REQUESTS[0]
    correct = CORRECT_OPTION_BY_REQUEST[request.key]
    assert correct in {option.key for option in request.options}


def test_the_request_offers_exactly_two_options():
    assert len(TIME_SERIES_REQUESTS[0].options) == 2


def test_the_same_days_previous_period_option_actually_shows_the_previous_period():
    option = next(option for option in TIME_SERIES_REQUESTS[0].options if option.key == "same_days_previous_period")
    assert option.show_previous_period is True


def test_the_nearby_days_only_option_does_not_show_the_previous_period():
    option = next(option for option in TIME_SERIES_REQUESTS[0].options if option.key == "nearby_days_only")
    assert option.show_previous_period is False


def test_every_highlighted_day_is_a_real_day_in_the_dataset():
    dataset = generate_kpi_data()
    current = build_time_series(dataset, "current", "x")
    real_days = {point.day for point in current.points}
    assert set(TIME_SERIES_REQUESTS[0].highlight_days) <= real_days
