import pytest

from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l20_ab_test_commander.experiment_data import generate_checkout_experiment_data, rate_at_checkpoint


def test_generated_data_matches_its_schema():
    dataset = generate_checkout_experiment_data()
    dtesting.assert_matches_schema(dataset)


def test_the_early_primary_lift_is_dramatically_larger_than_the_final_lift():
    dataset = generate_checkout_experiment_data()
    early_lift = rate_at_checkpoint(dataset, 1, "primary_conversion", "treatment") - rate_at_checkpoint(
        dataset, 1, "primary_conversion", "control"
    )
    final_lift = rate_at_checkpoint(dataset, 3, "primary_conversion", "treatment") - rate_at_checkpoint(
        dataset, 3, "primary_conversion", "control"
    )
    assert round(early_lift, 4) == 0.045
    assert round(final_lift, 4) == 0.003
    assert early_lift > final_lift * 10  # a real, not subtle, regression toward parity


def test_the_primary_lift_narrows_monotonically_across_checkpoints():
    dataset = generate_checkout_experiment_data()
    lifts = [
        rate_at_checkpoint(dataset, cp, "primary_conversion", "treatment") - rate_at_checkpoint(dataset, cp, "primary_conversion", "control")
        for cp in (1, 2, 3)
    ]
    assert lifts[0] > lifts[1] > lifts[2]


@pytest.mark.parametrize("metric_key", ["guardrail_refund", "guardrail_support", "segment_mobile"])
def test_guardrails_and_the_segment_check_stay_essentially_flat(metric_key):
    # This experiment's problem is never a guardrail breach - only the
    # primary metric's early read is misleading.
    dataset = generate_checkout_experiment_data()
    for checkpoint in (1, 2, 3):
        treatment = rate_at_checkpoint(dataset, checkpoint, metric_key, "treatment")
        control = rate_at_checkpoint(dataset, checkpoint, metric_key, "control")
        assert abs(treatment - control) <= 0.03
