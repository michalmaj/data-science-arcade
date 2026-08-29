import pytest

from data_science_arcade.lessons.l24_survey_bureau.requests import CORRECT_COMBO_BY_REQUEST, SURVEY_REQUESTS


def test_all_three_requests_are_present():
    assert {request.key for request in SURVEY_REQUESTS} == {
        "general_satisfaction_check",
        "fast_turnaround_temptation",
        "advisory_panel_temptation",
    }


def test_every_request_has_a_correct_combo_recorded():
    assert set(CORRECT_COMBO_BY_REQUEST) == {request.key for request in SURVEY_REQUESTS}


@pytest.mark.parametrize("request_", list(SURVEY_REQUESTS))
def test_the_correct_wording_is_among_the_offered_options(request_):
    correct_wording, _correct_channel = CORRECT_COMBO_BY_REQUEST[request_.key]
    assert correct_wording in {option.key for option in request_.wording_options}


@pytest.mark.parametrize("request_", list(SURVEY_REQUESTS))
def test_the_correct_channel_is_among_the_offered_options(request_):
    _correct_wording, correct_channel = CORRECT_COMBO_BY_REQUEST[request_.key]
    assert correct_channel in {option.key for option in request_.channel_options}


@pytest.mark.parametrize("request_", list(SURVEY_REQUESTS))
def test_every_request_offers_exactly_two_wording_and_two_channel_options(request_):
    assert len(request_.wording_options) == 2
    assert len(request_.channel_options) == 2


def test_correct_wording_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in SURVEY_REQUESTS:
        correct_wording, _ = CORRECT_COMBO_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.wording_options) if option.key == correct_wording))
    assert len(set(indexes)) > 1


def test_correct_channel_position_varies_across_requests():
    indexes = []
    for request_ in SURVEY_REQUESTS:
        _, correct_channel = CORRECT_COMBO_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.channel_options) if option.key == correct_channel))
    assert len(set(indexes)) > 1


@pytest.mark.parametrize("request_", list(SURVEY_REQUESTS))
def test_neutral_wording_never_carries_a_bias(request_):
    neutral = next(option for option in request_.wording_options if option.key == "neutral")
    assert neutral.bias == 0.0


@pytest.mark.parametrize("request_", list(SURVEY_REQUESTS))
def test_leading_wording_always_carries_a_positive_bias(request_):
    leading = next(option for option in request_.wording_options if option.key == "leading")
    assert leading.bias > 0.0


@pytest.mark.parametrize("request_", list(SURVEY_REQUESTS))
def test_broad_email_never_filters_anyone_out(request_):
    broad_email = next((option for option in request_.channel_options if option.key == "broad_email"), None)
    if broad_email is not None:
        assert broad_email.reach_query is None
