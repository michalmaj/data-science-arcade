import pytest

from data_science_arcade.lessons.l12_groupby_kitchen.requests import AGGREGATION_REQUESTS, CORRECT_PIPELINE_BY_REQUEST


def test_every_request_has_a_correct_pipeline_recorded():
    assert {request.key for request in AGGREGATION_REQUESTS} == set(CORRECT_PIPELINE_BY_REQUEST)


def test_all_three_requests_are_present():
    assert {request.key for request in AGGREGATION_REQUESTS} == {
        "revenue_per_store",
        "orders_per_day",
        "average_order_value_per_store",
    }


@pytest.mark.parametrize("request_", list(AGGREGATION_REQUESTS))
def test_the_correct_group_by_is_among_the_offered_options(request_):
    correct_group_by, _correct_aggregate = CORRECT_PIPELINE_BY_REQUEST[request_.key]
    assert correct_group_by in {option.key for option in request_.group_by_options}


@pytest.mark.parametrize("request_", list(AGGREGATION_REQUESTS))
def test_the_correct_aggregate_is_among_the_offered_options(request_):
    _correct_group_by, correct_aggregate = CORRECT_PIPELINE_BY_REQUEST[request_.key]
    assert correct_aggregate in {option.key for option in request_.aggregate_options}


@pytest.mark.parametrize("request_", list(AGGREGATION_REQUESTS))
def test_every_request_has_at_least_two_group_by_and_aggregate_options(request_):
    assert len(request_.group_by_options) >= 2
    assert len(request_.aggregate_options) >= 2


def test_correct_group_by_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in AGGREGATION_REQUESTS:
        correct_group_by, _ = CORRECT_PIPELINE_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.group_by_options) if option.key == correct_group_by))
    assert len(set(indexes)) > 1
