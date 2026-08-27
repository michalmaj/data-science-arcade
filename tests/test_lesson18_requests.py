import pytest

from data_science_arcade.lessons.l18_randomization_control_room.assignment_data import relative_imbalance
from data_science_arcade.lessons.l18_randomization_control_room.requests import ASSIGNMENT_REQUESTS, CORRECT_RULE_BY_REQUEST


def test_every_request_has_a_correct_rule_recorded():
    assert {request.key for request in ASSIGNMENT_REQUESTS} == set(CORRECT_RULE_BY_REQUEST)


def test_all_three_experiments_are_present():
    assert {request.key for request in ASSIGNMENT_REQUESTS} == {
        "checkout_redesign",
        "loyalty_discount_test",
        "notification_frequency_test",
    }


@pytest.mark.parametrize("request_", list(ASSIGNMENT_REQUESTS))
def test_the_correct_rule_is_among_the_offered_options(request_):
    correct = CORRECT_RULE_BY_REQUEST[request_.key]
    assert correct in {option.key for option in request_.options}


@pytest.mark.parametrize("request_", list(ASSIGNMENT_REQUESTS))
def test_every_request_offers_exactly_three_rules(request_):
    assert len(request_.options) == 3


def test_correct_rule_position_varies_across_requests_and_avoids_index_zero():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer that always sat there would be
    # visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in ASSIGNMENT_REQUESTS:
        correct = CORRECT_RULE_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.options) if option.key == correct))
    assert len(set(indexes)) > 1
    assert 0 not in indexes


@pytest.mark.parametrize("request_", list(ASSIGNMENT_REQUESTS))
def test_every_option_has_group_size_covariate_and_tenure_rows(request_):
    for option in request_.options:
        assert {segment.key for segment in option.segments} == {"group_size", "covariate", "tenure"}


@pytest.mark.parametrize("request_", list(ASSIGNMENT_REQUESTS))
def test_only_the_correct_rules_option_is_balanced_on_every_row(request_):
    correct = CORRECT_RULE_BY_REQUEST[request_.key]
    for option in request_.options:
        any_flagged = any(relative_imbalance(segment.before_rate, segment.after_rate) for segment in option.segments)
        if option.key == correct:
            assert any_flagged is False
        else:
            assert any_flagged is True
