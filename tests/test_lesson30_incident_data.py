from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.alerting import MetricOption, ThresholdOption
from data_science_arcade.lessons.l30_the_data_incident.incident_data import (
    correlation_promo_redemptions_vs_revenue,
    correlation_ticket_change_vs_revenue_change,
    generate_incident_data,
    percent_change,
    region_baseline_average,
    region_week_over_week_change,
    simulate_monitoring,
    value_at,
    weekly_company_revenue,
)


def test_generated_data_matches_its_schema():
    dataset = generate_incident_data()
    dtesting.assert_matches_schema(dataset)


def test_the_dataset_has_32_rows_four_regions_by_eight_weeks():
    dataset = generate_incident_data()
    assert len(dataset.frame) == 32


def test_only_east_actually_declined_week_7_to_8():
    dataset = generate_incident_data()
    for region in ("north", "south", "west"):
        before, after = region_week_over_week_change(dataset, region)
        assert abs(percent_change(before, after)) < 0.01  # flat, ordinary week-to-week noise

    east_before, east_after = region_week_over_week_change(dataset, "east")
    assert east_after < east_before
    assert round(percent_change(east_before, east_after), 4) == -0.5067


def test_east_week_7_is_the_real_outlier_not_week_8():
    dataset = generate_incident_data()
    baseline = region_baseline_average(dataset, "east")
    assert baseline == 75000.0

    week_7 = value_at(dataset, "east", 7, "revenue")
    week_8 = value_at(dataset, "east", 8, "revenue")
    assert round(percent_change(baseline, week_7), 4) == 1.0
    assert abs(percent_change(baseline, week_8)) < 0.02  # unremarkable, within 2%


def test_company_total_revenue_looks_like_an_18_percent_drop_week_7_to_8():
    dataset = generate_incident_data()
    totals = weekly_company_revenue(dataset)
    assert len(totals) == 8
    assert round(percent_change(totals[6], totals[7]), 3) == -0.181


def test_support_tickets_barely_move_despite_the_redesign_theory():
    # If the redesign had broken checkout, a bigger revenue drop should
    # come with *more* tickets, not fewer or the same.
    dataset = generate_incident_data()
    correlation = correlation_ticket_change_vs_revenue_change(dataset)
    assert 0 < correlation < 0.5  # real, but too weak and too small a sample to mean much


def test_promo_redemptions_correlate_almost_perfectly_with_east_revenue():
    dataset = generate_incident_data()
    correlation = correlation_promo_redemptions_vs_revenue(dataset, "east")
    assert correlation > 0.99


def test_east_revenue_monitoring_catches_the_real_week_at_every_threshold_with_no_false_alarms():
    dataset = generate_incident_data()
    metric = MetricOption("east_revenue", "x", metric_key="east_revenue")
    for multiplier in (0.05, 0.15, 0.30):
        false_alarms, caught = simulate_monitoring(dataset, metric, ThresholdOption("x", "x", multiplier), 7)
        assert caught is True
        assert false_alarms == 0


def test_company_total_revenue_monitoring_misses_the_real_week_if_the_threshold_is_too_loose():
    dataset = generate_incident_data()
    metric = MetricOption("company_total_revenue", "x", metric_key="company_total_revenue")
    _, caught_tight = simulate_monitoring(dataset, metric, ThresholdOption("x", "x", 0.05), 7)
    _, caught_balanced = simulate_monitoring(dataset, metric, ThresholdOption("x", "x", 0.15), 7)
    false_alarms_loose, caught_loose = simulate_monitoring(dataset, metric, ThresholdOption("x", "x", 0.30), 7)
    assert caught_tight is True
    assert caught_balanced is True
    assert caught_loose is False
    assert false_alarms_loose == 0


def test_east_support_tickets_monitoring_is_either_noisy_or_blind():
    dataset = generate_incident_data()
    metric = MetricOption("east_support_tickets", "x", metric_key="east_support_tickets")
    false_alarms_tight, caught_tight = simulate_monitoring(dataset, metric, ThresholdOption("x", "x", 0.05), 7)
    _, caught_balanced = simulate_monitoring(dataset, metric, ThresholdOption("x", "x", 0.15), 7)
    assert caught_tight is True
    assert false_alarms_tight > 0  # noisy - crosses a tight threshold constantly on ordinary weeks too
    assert caught_balanced is False  # the real signal never shows up in ticket counts at all
