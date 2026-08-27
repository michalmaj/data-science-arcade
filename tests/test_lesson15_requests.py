import pytest

from data_science_arcade.lessons.l15_segment_detective.requests import CORRECT_OPTION_BY_REQUEST, SEGMENT_REQUESTS


def test_every_request_has_a_correct_option_recorded():
    assert {request.key for request in SEGMENT_REQUESTS} == set(CORRECT_OPTION_BY_REQUEST)


def test_all_three_requests_are_present():
    assert {request.key for request in SEGMENT_REQUESTS} == {
        "mobile_conversion_complaint",
        "eu_region_complaint",
        "paid_channel_complaint",
    }


@pytest.mark.parametrize("request_", list(SEGMENT_REQUESTS))
def test_the_correct_option_is_among_the_offered_options(request_):
    correct = CORRECT_OPTION_BY_REQUEST[request_.key]
    assert correct in {option.key for option in request_.options}


@pytest.mark.parametrize("request_", list(SEGMENT_REQUESTS))
def test_every_request_offers_all_three_dimensions_exactly_once(request_):
    assert {option.key for option in request_.options} == {"device", "region", "channel"}


def test_correct_option_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in SEGMENT_REQUESTS:
        correct = CORRECT_OPTION_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.options) if option.key == correct))
    assert len(set(indexes)) > 1


@pytest.mark.parametrize("request_", list(SEGMENT_REQUESTS))
def test_every_offered_dimension_shows_both_segments_declining(request_):
    # Every dimension is a real Simpson's-paradox slice, not just the
    # correct one - picking any option and reading its table should show
    # the same within-segment decline pattern the twist later explains.
    for option in request_.options:
        for segment in option.segments:
            assert segment.after_rate < segment.before_rate
