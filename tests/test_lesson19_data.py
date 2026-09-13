import pytest

from data_science_arcade.lessons.framework.power import proportion_difference_ci
from data_science_arcade.lessons.l19_power_plant import data as d


def _pct(value: float) -> float:
    return round(value * 100, 3)


@pytest.mark.parametrize(
    "weeks,expected_n,expected_mde_pts,expected_meets",
    [
        (2, 4000, 2.675, False),
        (4, 8000, 1.892, False),
        (6, 12000, 1.545, False),
        (7, 14000, 1.430, True),
        (8, 16000, 1.338, True),
        (12, 24000, 1.092, True),
    ],
)
def test_mde_table_reconciles_exactly_for_the_given_weeks(weeks, expected_n, expected_mde_pts, expected_meets):
    assert d.n_per_arm_for_weeks(weeks) == expected_n
    assert _pct(d.mde_for_weeks(weeks)) == pytest.approx(expected_mde_pts, abs=0.001)
    assert d.meets_sensitivity_target(weeks) == expected_meets


def test_plan_mirror_code_reflects_the_real_weeks_value_not_a_canonical_one():
    code = d.plan_mirror_code(4)
    assert "weeks = 4" in code
    assert "weeks = 7" not in code


def test_reference_designs_detection_rates_reconcile_to_the_real_seeded_simulation():
    # These exact values belong only in data/test assertions - player-
    # facing copy must round to "about 60%" / "about 82%", never claim
    # this false precision (n_sims=2000 has a real ~1pp Monte Carlo
    # standard error near 80%).
    assert d.REFERENCE_DESIGN_A_DETECTION_RATE == pytest.approx(0.6025, abs=0.0001)
    assert d.REFERENCE_DESIGN_B_DETECTION_RATE == pytest.approx(0.818, abs=0.0001)
    # The 7-week reference design must detect a true +1.5pp effect
    # noticeably more often than the 4-week one - the whole point of the
    # reveal - without asserting simulation == exactly 80% (the formula
    # and the simulation are both approximations, never equal by
    # construction).
    assert d.REFERENCE_DESIGN_B_DETECTION_RATE > d.REFERENCE_DESIGN_A_DETECTION_RATE
    assert d.REFERENCE_DESIGN_A_DETECTION_RATE < 0.70
    assert d.REFERENCE_DESIGN_B_DETECTION_RATE > 0.75


def test_reference_design_mirror_code_matches_the_real_simulation_function():
    namespace: dict = {}
    import numpy as np

    from data_science_arcade.lessons.framework.power import Z_ALPHA_2, two_proportion_z_statistic

    namespace["np"] = np
    namespace["Z_ALPHA_2"] = Z_ALPHA_2
    namespace["two_proportion_z_statistic"] = two_proportion_z_statistic
    exec(d.REFERENCE_DESIGN_A_MIRROR, namespace)
    assert namespace["empirical_detection_rate_a"] == pytest.approx(d.REFERENCE_DESIGN_A_DETECTION_RATE, abs=1e-9)

    namespace_b: dict = {"np": np, "Z_ALPHA_2": Z_ALPHA_2, "two_proportion_z_statistic": two_proportion_z_statistic}
    exec(d.REFERENCE_DESIGN_B_MIRROR, namespace_b)
    assert namespace_b["empirical_detection_rate_b"] == pytest.approx(d.REFERENCE_DESIGN_B_DETECTION_RATE, abs=1e-9)


def test_underpowered_calibration_reconciles_to_the_real_verified_numbers():
    ds = d.generate_underpowered_calibration()
    assert _pct(d.calibration_rate(ds, "control")) == 24.0
    assert _pct(d.calibration_rate(ds, "treatment")) == 25.2
    control_conv, control_n = d.calibration_counts(ds, "control")
    treatment_conv, treatment_n = d.calibration_counts(ds, "treatment")
    lo, hi = proportion_difference_ci(control_conv, control_n, treatment_conv, treatment_n)
    assert round(lo * 100, 2) == -0.69
    assert round(hi * 100, 2) == 3.09
    # Crosses zero AND spans well above the +1.5pp business threshold -
    # genuinely inconclusive on both fronts.
    assert lo < 0 < hi
    assert hi > 0.015


def test_high_n_calibration_reconciles_to_the_real_verified_numbers():
    ds = d.generate_high_n_calibration()
    assert _pct(d.calibration_rate(ds, "control")) == 24.0
    assert _pct(d.calibration_rate(ds, "treatment")) == 24.4
    control_conv, control_n = d.calibration_counts(ds, "control")
    treatment_conv, treatment_n = d.calibration_counts(ds, "treatment")
    lo, hi = proportion_difference_ci(control_conv, control_n, treatment_conv, treatment_n)
    assert round(lo * 100, 3) == 0.025
    assert round(hi * 100, 3) == 0.775
    # Excludes zero, but the ENTIRE interval sits below the +1.5pp
    # threshold.
    assert lo > 0
    assert hi < 0.015


def test_mastery_design_options_are_one_inadequate_one_adequate():
    assert _pct(d.mastery_mde_for_weeks(d.MASTERY_INADEQUATE_WEEKS)) == 2.879
    assert d.mastery_mde_for_weeks(d.MASTERY_INADEQUATE_WEEKS) > d.MASTERY_MINIMUM_EFFECT
    assert _pct(d.mastery_mde_for_weeks(d.MASTERY_ADEQUATE_WEEKS)) == 1.821
    assert d.mastery_mde_for_weeks(d.MASTERY_ADEQUATE_WEEKS) <= d.MASTERY_MINIMUM_EFFECT


def test_mastery_result_reconciles_and_is_genuinely_inconclusive_on_both_fronts():
    ds = d.generate_mastery_result()
    assert _pct(d.calibration_rate(ds, "control")) == 12.0
    assert _pct(d.calibration_rate(ds, "treatment")) == 11.0
    control_conv, control_n = d.calibration_counts(ds, "control")
    treatment_conv, treatment_n = d.calibration_counts(ds, "treatment")
    lo, hi = proportion_difference_ci(control_conv, control_n, treatment_conv, treatment_n)
    assert round(lo * 100, 2) == -2.98
    assert round(hi * 100, 2) == 0.98
    # treatment - control is negative here (a real reduction in the
    # late-delivery rate - the improvement direction for this bad-outcome
    # metric). The interval crosses zero AND still contains the real
    # business-useful -2.0pp reduction (MASTERY_MINIMUM_EFFECT, expressed
    # as a reduction) - genuinely inconclusive on both "is there any
    # effect" and "is it the worthwhile size."
    assert lo < 0 < hi
    assert lo < -d.MASTERY_MINIMUM_EFFECT
