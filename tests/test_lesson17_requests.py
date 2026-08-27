import pytest

from data_science_arcade.lessons.framework.prediction import DECREASE, INCREASE, NO_CHANGE
from data_science_arcade.lessons.l17_hypothesis_detective.requests import CORRECT_DIRECTION_BY_REQUEST, HYPOTHESIS_REQUESTS


def test_all_three_requests_are_present():
    assert {request.key for request in HYPOTHESIS_REQUESTS} == {
        "repeat_purchase_rate",
        "average_order_value",
        "support_contact_rate",
    }


def test_every_request_has_a_correct_direction_recorded():
    assert set(CORRECT_DIRECTION_BY_REQUEST) == {request.key for request in HYPOTHESIS_REQUESTS}


def test_the_three_requests_cover_all_three_directions():
    assert set(CORRECT_DIRECTION_BY_REQUEST.values()) == {INCREASE, DECREASE, NO_CHANGE}


@pytest.mark.parametrize("request_", list(HYPOTHESIS_REQUESTS))
def test_correct_direction_matches_the_requests_own_before_after_values(request_):
    assert CORRECT_DIRECTION_BY_REQUEST[request_.key] == request_.correct_direction
