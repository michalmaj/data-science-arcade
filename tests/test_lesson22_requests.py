import pytest

from data_science_arcade.lessons.l22_cohort_observatory.cohort_data import generate_cohort_data, retention_rate
from data_science_arcade.lessons.l22_cohort_observatory.requests import COHORT_REQUESTS, CORRECT_OPTION_BY_REQUEST


def test_all_three_requests_are_present():
    assert {request.key for request in COHORT_REQUESTS} == {
        "newest_cohort_claim",
        "april_complaint",
        "march_product_change_claim",
    }


def test_every_request_has_a_correct_option_recorded():
    assert set(CORRECT_OPTION_BY_REQUEST) == {request.key for request in COHORT_REQUESTS}


@pytest.mark.parametrize("request_", list(COHORT_REQUESTS))
def test_the_correct_option_is_among_the_offered_options(request_):
    correct = CORRECT_OPTION_BY_REQUEST[request_.key]
    assert correct in {option.key for option in request_.options}


@pytest.mark.parametrize("request_", list(COHORT_REQUESTS))
def test_every_request_offers_exactly_two_options(request_):
    assert len(request_.options) == 2


def test_correct_option_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in COHORT_REQUESTS:
        correct = CORRECT_OPTION_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.options) if option.key == correct))
    assert len(set(indexes)) > 1


@pytest.mark.parametrize("request_", list(COHORT_REQUESTS))
def test_every_same_month_option_actually_compares_the_same_month(request_):
    same_month_option = next(option for option in request_.options if option.key == "same_month_comparison")
    assert same_month_option.month_a == same_month_option.month_b


@pytest.mark.parametrize("request_", list(COHORT_REQUESTS))
def test_every_mismatched_option_actually_compares_different_months(request_):
    mismatched_option = next(option for option in request_.options if option.key == "mismatched_month_comparison")
    assert mismatched_option.month_a != mismatched_option.month_b


@pytest.mark.parametrize("request_", list(COHORT_REQUESTS))
def test_both_cells_every_option_points_at_are_real_observed_cells(request_):
    dataset = generate_cohort_data()
    for option in request_.options:
        retention_rate(dataset, option.cohort_a, option.month_a)  # raises if unobserved
        retention_rate(dataset, option.cohort_b, option.month_b)
