import math

import pytest

from data_science_arcade.lessons.framework.power import minimum_detectable_effect


def test_zero_sample_size_is_an_undefined_infinite_effect():
    assert minimum_detectable_effect(0.24, 0) == math.inf


@pytest.mark.parametrize(
    "baseline_rate,sample_size_per_group,expected_pts",
    [
        (0.24, 14000, 1.43),
        (0.10, 3600, 1.98),
        (0.05, 900, 2.88),
    ],
)
def test_minimum_detectable_effect_matches_the_standard_formula(baseline_rate, sample_size_per_group, expected_pts):
    mde_pts = minimum_detectable_effect(baseline_rate, sample_size_per_group) * 100
    assert mde_pts == pytest.approx(expected_pts, abs=0.01)


def test_more_sample_always_yields_a_smaller_or_equal_detectable_effect():
    mde_small = minimum_detectable_effect(0.24, 2000)
    mde_large = minimum_detectable_effect(0.24, 20000)
    assert mde_large < mde_small
