import pytest

from data_science_arcade.lessons.l16_metric_forge.requests import CORRECT_OPTION_BY_REQUEST, METRIC_REQUESTS


def test_every_request_has_a_correct_option_recorded():
    assert {request.key for request in METRIC_REQUESTS} == set(CORRECT_OPTION_BY_REQUEST)


def test_all_three_requests_are_present():
    assert {request.key for request in METRIC_REQUESTS} == {
        "support_speed_initiative",
        "sales_growth_initiative",
        "app_engagement_initiative",
    }


@pytest.mark.parametrize("request_", list(METRIC_REQUESTS))
def test_the_correct_option_is_among_the_offered_options(request_):
    correct = CORRECT_OPTION_BY_REQUEST[request_.key]
    assert correct in {option.key for option in request_.options}


@pytest.mark.parametrize("request_", list(METRIC_REQUESTS))
def test_every_request_offers_exactly_three_metric_options(request_):
    assert len(request_.options) == 3


def test_correct_option_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in METRIC_REQUESTS:
        correct = CORRECT_OPTION_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.options) if option.key == correct))
    assert len(set(indexes)) > 1


@pytest.mark.parametrize("request_", list(METRIC_REQUESTS))
def test_every_option_has_a_primary_and_a_guardrail_row(request_):
    for option in request_.options:
        assert {segment.key for segment in option.segments} == {"primary", "guardrail"}


@pytest.mark.parametrize("request_", list(METRIC_REQUESTS))
def test_every_options_primary_row_improves(request_):
    for option in request_.options:
        primary = next(segment for segment in option.segments if segment.key == "primary")
        assert primary.after_rate > primary.before_rate


@pytest.mark.parametrize("request_", list(METRIC_REQUESTS))
def test_only_the_correct_options_guardrail_holds_or_improves(request_):
    correct = CORRECT_OPTION_BY_REQUEST[request_.key]
    for option in request_.options:
        guardrail = next(segment for segment in option.segments if segment.key == "guardrail")
        if option.key == correct:
            assert guardrail.after_rate >= guardrail.before_rate
        else:
            assert guardrail.after_rate < guardrail.before_rate
