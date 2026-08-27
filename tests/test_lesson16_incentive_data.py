import pytest

from data_science_arcade.lessons.l16_metric_forge.incentive_data import (
    generate_app_data,
    generate_sales_data,
    generate_support_data,
    guardrail_mean,
    metric_mean,
)

DIMENSIONS = (
    (generate_support_data, ("quick_close_share", "first_contact_resolution_rate", "tickets_closed_rate"), "first_contact_resolution_rate"),
    (generate_sales_data, ("signup_conversion_rate", "activated_customer_rate", "leads_contacted_rate"), "activated_customer_rate"),
    (generate_app_data, ("daily_open_rate", "task_completion_rate", "notification_click_rate"), "task_completion_rate"),
)


@pytest.mark.parametrize("generate,metrics,correct", DIMENSIONS)
def test_every_candidate_metric_improves_when_targeted(generate, metrics, correct):
    # Whatever gets measured gets optimized - true for gameable and
    # trustworthy metrics alike.
    dataset = generate()
    for metric in metrics:
        assert metric_mean(dataset, metric, "after") > metric_mean(dataset, metric, "before")


@pytest.mark.parametrize("generate,metrics,correct", DIMENSIONS)
def test_only_the_correct_metrics_guardrail_holds_or_improves(generate, metrics, correct):
    # Real computed values (verified via a manual script before writing
    # this assertion), not hand-picked: the two gameable decoys drag
    # their guardrail down; the metric resistant to gaming doesn't.
    dataset = generate()
    for metric in metrics:
        guardrail_before = guardrail_mean(dataset, metric, "before")
        guardrail_after = guardrail_mean(dataset, metric, "after")
        if metric == correct:
            assert guardrail_after >= guardrail_before
        else:
            assert guardrail_after < guardrail_before


def test_support_means_match_the_verified_manual_computation():
    dataset = generate_support_data()
    assert metric_mean(dataset, "quick_close_share", "before") == pytest.approx(0.60)
    assert metric_mean(dataset, "quick_close_share", "after") == pytest.approx(0.85)
    assert guardrail_mean(dataset, "quick_close_share", "before") == pytest.approx(0.88)
    assert guardrail_mean(dataset, "quick_close_share", "after") == pytest.approx(0.68)
