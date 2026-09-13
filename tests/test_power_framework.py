import math

import pytest

from data_science_arcade.lessons.framework.power import (
    minimum_detectable_effect,
    proportion_difference_ci,
    two_proportion_z_statistic,
)


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


# --- proportion_difference_ci - verified this session against L19's own
# real calibration cases, not invented numbers. ----------------------------


def test_proportion_difference_ci_matches_the_underpowered_calibration_case():
    lo, hi = proportion_difference_ci(960, 4000, 1008, 4000)
    assert round(lo * 100, 2) == -0.69
    assert round(hi * 100, 2) == 3.09


def test_proportion_difference_ci_matches_the_high_n_calibration_case():
    lo, hi = proportion_difference_ci(24000, 100000, 24400, 100000)
    assert round(lo * 100, 3) == 0.025
    assert round(hi * 100, 3) == 0.775


def test_proportion_difference_ci_is_narrower_with_more_observations():
    small_n_lo, small_n_hi = proportion_difference_ci(240, 2000, 280, 2000)
    large_n_lo, large_n_hi = proportion_difference_ci(2400, 20000, 2800, 20000)
    assert (large_n_hi - large_n_lo) < (small_n_hi - small_n_lo)


def test_proportion_difference_ci_sign_is_treatment_minus_control():
    lo, hi = proportion_difference_ci(1000, 10000, 1200, 10000)
    diff = 0.12 - 0.10
    assert lo < diff < hi


# --- two_proportion_z_statistic - a real, pinned-method hypothesis test
# (pooled SE under the null of no difference), deliberately distinct from
# proportion_difference_ci's own unpooled/Wald SE. --------------------


def test_two_proportion_z_statistic_is_zero_for_identical_rates():
    z = two_proportion_z_statistic(500, 5000, 500, 5000)
    assert z == 0.0


def test_two_proportion_z_statistic_is_positive_when_treatment_exceeds_control():
    z = two_proportion_z_statistic(960, 4000, 1200, 4000)
    assert z > 0


def test_two_proportion_z_statistic_grows_with_more_observations_at_the_same_rates():
    z_small = two_proportion_z_statistic(240, 2000, 280, 2000)
    z_large = two_proportion_z_statistic(2400, 20000, 2800, 20000)
    assert z_large > z_small
