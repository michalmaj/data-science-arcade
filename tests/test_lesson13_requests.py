import pytest

from data_science_arcade.lessons.l13_join_junction.requests import CORRECT_HOW_BY_REQUEST, JOIN_REQUESTS


def test_every_request_has_a_correct_how_recorded():
    assert {request.key for request in JOIN_REQUESTS} == set(CORRECT_HOW_BY_REQUEST)


def test_all_three_requests_are_present():
    assert {request.key for request in JOIN_REQUESTS} == {
        "orders_missing_customers",
        "confident_customer_match",
        "full_customer_outreach_list",
    }


@pytest.mark.parametrize("request_", list(JOIN_REQUESTS))
def test_the_correct_option_is_among_the_offered_options(request_):
    correct_how = CORRECT_HOW_BY_REQUEST[request_.key]
    assert correct_how in {option.how for option in request_.options}


@pytest.mark.parametrize("request_", list(JOIN_REQUESTS))
def test_every_request_offers_all_three_join_types_exactly_once(request_):
    assert {option.how for option in request_.options} == {"inner", "left", "right"}


def test_correct_option_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in JOIN_REQUESTS:
        correct_how = CORRECT_HOW_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.options) if option.how == correct_how))
    assert len(set(indexes)) > 1
