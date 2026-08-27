import pytest

from data_science_arcade.lessons.l14_chart_designer.requests import CHART_REQUESTS, CORRECT_OPTION_BY_REQUEST


def test_every_request_has_a_correct_option_recorded():
    assert {request.key for request in CHART_REQUESTS} == set(CORRECT_OPTION_BY_REQUEST)


def test_all_three_requests_are_present():
    assert {request.key for request in CHART_REQUESTS} == {
        "revenue_by_store",
        "daily_revenue_trend",
        "returns_by_store",
    }


@pytest.mark.parametrize("request_", list(CHART_REQUESTS))
def test_the_correct_option_is_among_the_offered_options(request_):
    correct = CORRECT_OPTION_BY_REQUEST[request_.key]
    assert correct in {option.key for option in request_.options}


@pytest.mark.parametrize("request_", list(CHART_REQUESTS))
def test_every_request_has_at_least_two_options(request_):
    assert len(request_.options) >= 2


@pytest.mark.parametrize("request_", list(CHART_REQUESTS))
def test_categories_and_values_line_up(request_):
    assert len(request_.categories) == len(request_.values)


def test_correct_option_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in CHART_REQUESTS:
        correct = CORRECT_OPTION_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.options) if option.key == correct))
    assert len(set(indexes)) > 1


def test_a_zoomed_bar_is_never_the_correct_option():
    for request_ in CHART_REQUESTS:
        correct = CORRECT_OPTION_BY_REQUEST[request_.key]
        correct_option = next(option for option in request_.options if option.key == correct)
        assert not (correct_option.chart_type == "bar" and correct_option.scale == "zoomed")
