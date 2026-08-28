import pytest

from data_science_arcade.lessons.l21_funnel_factory.requests import CORRECT_DEFINITION_BY_REQUEST, FUNNEL_REQUESTS


def test_all_three_requests_are_present():
    assert {request.key for request in FUNNEL_REQUESTS} == {
        "mobile_dropout_complaint",
        "payment_step_complaint",
        "cart_abandonment_complaint",
    }


def test_every_request_has_a_correct_definition_recorded():
    assert set(CORRECT_DEFINITION_BY_REQUEST) == {request.key for request in FUNNEL_REQUESTS}


@pytest.mark.parametrize("request_", list(FUNNEL_REQUESTS))
def test_the_correct_definition_is_among_the_offered_definitions(request_):
    correct = CORRECT_DEFINITION_BY_REQUEST[request_.key]
    assert correct in {definition.key for definition in request_.definitions}


@pytest.mark.parametrize("request_", list(FUNNEL_REQUESTS))
def test_every_request_offers_exactly_two_definitions(request_):
    assert len(request_.definitions) == 2


def test_correct_definition_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in FUNNEL_REQUESTS:
        correct = CORRECT_DEFINITION_BY_REQUEST[request_.key]
        indexes.append(next(i for i, definition in enumerate(request_.definitions) if definition.key == correct))
    assert len(set(indexes)) > 1
