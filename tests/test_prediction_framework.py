import pytest

from data_science_arcade.lessons.framework.prediction import DECREASE, INCREASE, NO_CHANGE, HypothesisRequest, actual_direction


@pytest.mark.parametrize(
    "before,after,expected",
    [
        (0.24, 0.34, INCREASE),  # +41.7% relative
        (58.0, 51.0, DECREASE),  # -12.1% relative, works for a dollar metric too
        (0.060, 0.062, NO_CHANGE),  # +3.3% relative, below the noise threshold
        (0.060, 0.058, NO_CHANGE),  # -3.3% relative
        (0.10, 0.105, NO_CHANGE),  # exactly at the edge of "basically flat"
    ],
)
def test_actual_direction_matches_the_real_relative_change(before, after, expected):
    assert actual_direction(before, after) == expected


def test_hypothesis_request_correct_direction_is_derived_not_authored():
    request = HypothesisRequest(
        key="k",
        prompt_key="app.title",
        metric_label_key="common.on",
        before_value=0.20,
        after_value=0.30,
    )
    assert request.correct_direction == INCREASE
