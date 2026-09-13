import pytest

from data_science_arcade.lessons.framework.power import proportion_difference_ci
from data_science_arcade.lessons.l20_ab_test_commander import data as d


def _pct(value: float) -> float:
    return round(value * 100, 2)


@pytest.fixture
def dataset():
    return d.generate_checkout_experiment()


@pytest.mark.parametrize(
    "week,control_events,n,treatment_events,expected_diff_pp,expected_lo_pp,expected_hi_pp",
    [
        (1, 480, 2000, 560, 4.00, 1.28, 6.72),
        (3, 1440, 6000, 1632, 3.20, 1.64, 4.76),
        (7, 3360, 14000, 3745, 2.75, 1.73, 3.77),
    ],
)
def test_primary_reconciles_to_the_real_verified_numbers(dataset, week, control_events, n, treatment_events, expected_diff_pp, expected_lo_pp, expected_hi_pp):
    # Recomputed independently via proportion_difference_ci, never just
    # re-asserting a hand-typed status constant against itself.
    lo, hi = proportion_difference_ci(control_events, n, treatment_events, n)
    diff = treatment_events / n - control_events / n
    assert _pct(diff) == expected_diff_pp
    assert _pct(lo) == expected_lo_pp
    assert _pct(hi) == expected_hi_pp

    got_diff, got_lo, got_hi = d.diff_and_ci_at_checkpoint(dataset, week, d.PRIMARY)
    assert got_diff == pytest.approx(diff)
    assert got_lo == pytest.approx(lo)
    assert got_hi == pytest.approx(hi)


def test_primary_fails_the_strict_launch_criterion_at_week_one(dataset):
    _diff, lo, _hi = d.diff_and_ci_at_checkpoint(dataset, 1, d.PRIMARY)
    assert d.primary_passes(lo) is False


@pytest.mark.parametrize("week", [3, 7])
def test_primary_passes_the_strict_launch_criterion_under_the_same_unmodified_rule(dataset, week):
    _diff, lo, _hi = d.diff_and_ci_at_checkpoint(dataset, week, d.PRIMARY)
    assert d.primary_passes(lo) is True


@pytest.mark.parametrize("week", [1, 3])
def test_support_guardrail_does_not_breach_before_the_planned_end(dataset, week):
    _diff, lo, _hi = d.diff_and_ci_at_checkpoint(dataset, week, d.SUPPORT_GUARDRAIL)
    assert d.guardrail_breached(lo) is False


def test_support_guardrail_breaches_only_at_the_full_planned_sample(dataset):
    diff, lo, hi = d.diff_and_ci_at_checkpoint(dataset, 7, d.SUPPORT_GUARDRAIL)
    assert _pct(diff) == 1.20
    assert _pct(lo) == 0.66
    assert _pct(hi) == 1.74
    assert d.guardrail_breached(lo) is True


@pytest.mark.parametrize("week", [1, 3, 7])
def test_refund_guardrail_never_breaches_at_any_checkpoint(dataset, week):
    _diff, lo, _hi = d.diff_and_ci_at_checkpoint(dataset, week, d.REFUND_GUARDRAIL)
    assert d.guardrail_breached(lo) is False


def test_checkpoint_mirror_code_uses_week_prefixed_names_for_interim_weeks(dataset):
    code = d.checkpoint_mirror_code(dataset, 1)
    assert "week1_primary_diff" in code
    assert "\nprimary_diff" not in code
    assert not code.startswith("primary_diff")

    code = d.checkpoint_mirror_code(dataset, 3)
    assert "week3_support_guardrail_diff" in code


def test_checkpoint_mirror_code_uses_bare_canonical_names_only_at_the_planned_end(dataset):
    code = d.checkpoint_mirror_code(dataset, 7)
    assert "primary_ci_lower, primary_ci_upper" in code
    assert "primary_diff = primary_treatment_rate - primary_control_rate" in code
    assert "week7_primary_diff" not in code
    assert "week1_" not in code
    assert "week3_" not in code


def test_checkpoint_mirror_code_execs_to_the_real_verified_values(dataset):
    namespace: dict = {"proportion_difference_ci": proportion_difference_ci}
    exec(d.checkpoint_mirror_code(dataset, 7), namespace)
    assert _pct(namespace["primary_diff"]) == 2.75
    assert _pct(namespace["support_guardrail_diff"]) == 1.20
    assert _pct(namespace["refund_guardrail_diff"]) == 0.10


def test_mastery_safety_rule_is_genuinely_met_at_its_own_scheduled_threshold():
    mastery = d.generate_mastery_safety_check()
    diff, lo, hi = d.mastery_diff_and_ci(mastery)
    assert _pct(diff) == 2.50
    assert _pct(lo) == 1.05
    assert _pct(hi) == 3.95
    assert d.mastery_safety_rule_met(lo) is True
    # And the entire interval clears the pre-specified +1.0pp bar, not
    # merely zero - a stricter, explicit threshold, matching the main
    # case's own contract shape.
    assert lo > d.MASTERY_SAFETY_THRESHOLD


def test_mastery_mirror_code_execs_to_the_real_verified_values():
    namespace: dict = {"proportion_difference_ci": proportion_difference_ci}
    exec(d.mastery_mirror_code(), namespace)
    assert _pct(namespace["mastery_damage_claim_diff"]) == 2.50
