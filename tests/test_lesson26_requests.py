import pytest

from data_science_arcade.lessons.l26_correlation_crime_scene.requests import CORRECT_OPTION_BY_REQUEST, CORRELATION_REQUESTS


def test_all_three_requests_are_present():
    assert {request.key for request in CORRELATION_REQUESTS} == {
        "push_opens_claim",
        "shipment_sales_claim",
        "dark_mode_claim",
    }


def test_every_request_has_a_correct_option_recorded():
    assert set(CORRECT_OPTION_BY_REQUEST) == {request.key for request in CORRELATION_REQUESTS}


@pytest.mark.parametrize("request_", list(CORRELATION_REQUESTS))
def test_the_correct_option_is_among_the_offered_options(request_):
    correct = CORRECT_OPTION_BY_REQUEST[request_.key]
    assert correct in {option.key for option in request_.options}


@pytest.mark.parametrize("request_", list(CORRELATION_REQUESTS))
def test_every_request_offers_exactly_three_options(request_):
    assert len(request_.options) == 3


def test_correct_option_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in CORRELATION_REQUESTS:
        correct = CORRECT_OPTION_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.options) if option.key == correct))
    assert len(set(indexes)) > 1


@pytest.mark.parametrize("request_", list(CORRELATION_REQUESTS))
def test_every_request_has_a_real_computed_correlation_and_sample_size(request_):
    assert -1.0 <= request_.correlation <= 1.0
    assert request_.sample_size > 0


@pytest.mark.parametrize("request_", list(CORRELATION_REQUESTS))
def test_every_option_has_its_own_explanation_key(request_):
    for option in request_.options:
        assert option.explanation_key
        assert option.explanation_key != option.label_key
