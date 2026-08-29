import pytest

from data_science_arcade.lessons.l27_causality_courtroom.requests import CORRECT_OPTION_BY_REQUEST, CORRELATION_REQUESTS


def test_all_three_requests_are_present():
    assert {request.key for request in CORRELATION_REQUESTS} == {
        "tool_spend_claim",
        "resolution_satisfaction_claim",
        "training_performance_claim",
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


@pytest.mark.parametrize("request_", list(CORRELATION_REQUESTS))
def test_every_request_offers_a_right_verdict_for_the_wrong_reason_decoy(request_):
    # Every case deliberately includes an option that reaches the same
    # top-level verdict as the correct one (sustain vs. overrule) but for
    # an unrelated or irrelevant reason - not just an opposite-verdict
    # decoy - so picking the right *side* isn't enough on its own.
    correct_key = CORRECT_OPTION_BY_REQUEST[request_.key]
    correct_side = correct_key.split("_", 1)[0]
    same_side_options = [option for option in request_.options if option.key != correct_key and option.key.split("_", 1)[0] == correct_side]
    assert len(same_side_options) >= 1
