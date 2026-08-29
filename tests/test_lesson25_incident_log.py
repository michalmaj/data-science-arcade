from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.alerting import MetricOption, ThresholdOption
from data_science_arcade.lessons.l25_kpi_emergency_room.incident_log import flagged_days, generate_incident_log, simulate_monitoring

TIGHT = ThresholdOption("tight", "x", multiplier=1.0)
BALANCED = ThresholdOption("balanced", "x", multiplier=3.0)
CHECKOUT_ERROR_RATE = MetricOption("checkout_error_rate", "x", metric_key="checkout_error_rate")
ON_TIME_DELIVERY_RATE = MetricOption("on_time_delivery_rate", "x", metric_key="on_time_delivery_rate")
SOCIAL_MENTIONS = MetricOption("social_mentions", "x", metric_key="social_mentions")
PAGE_LOAD_TIME = MetricOption("page_load_time", "x", metric_key="page_load_time")


def test_generated_data_matches_its_schema():
    dataset = generate_incident_log()
    dtesting.assert_matches_schema(dataset)


def test_checkout_error_rate_flags_only_its_real_incident_day():
    dataset = generate_incident_log()
    assert flagged_days(dataset, "checkout_error_rate", multiplier=3.0) == {5}
    assert flagged_days(dataset, "checkout_error_rate", multiplier=1.0) == {5}


def test_on_time_delivery_rate_flags_only_its_real_incident_day():
    dataset = generate_incident_log()
    assert flagged_days(dataset, "on_time_delivery_rate", multiplier=3.0) == {11}
    assert flagged_days(dataset, "on_time_delivery_rate", multiplier=1.0) == {11}


def test_social_mentions_never_flags_anything_with_a_balanced_threshold():
    dataset = generate_incident_log()
    assert flagged_days(dataset, "social_mentions", multiplier=3.0) == set()


def test_social_mentions_fires_false_alarms_with_a_tight_threshold():
    dataset = generate_incident_log()
    flagged = flagged_days(dataset, "social_mentions", multiplier=1.0)
    assert len(flagged) > 0
    assert 5 not in flagged and 11 not in flagged  # never coincides with a real incident


def test_page_load_time_fires_false_alarms_with_a_tight_threshold_but_never_catches_real_incidents():
    dataset = generate_incident_log()
    flagged = flagged_days(dataset, "page_load_time", multiplier=1.0)
    assert len(flagged) > 0
    assert 5 not in flagged and 11 not in flagged


def test_the_correct_metric_and_balanced_threshold_catches_its_incident_with_no_false_alarms():
    dataset = generate_incident_log()
    assert simulate_monitoring(dataset, CHECKOUT_ERROR_RATE, BALANCED, target_incident_day=5) == (0, True)
    assert simulate_monitoring(dataset, ON_TIME_DELIVERY_RATE, BALANCED, target_incident_day=11) == (0, True)


def test_a_vanity_or_noisy_metric_never_catches_a_real_incident_regardless_of_threshold():
    dataset = generate_incident_log()
    for threshold in (TIGHT, BALANCED):
        _, caught = simulate_monitoring(dataset, SOCIAL_MENTIONS, threshold, target_incident_day=5)
        assert caught is False
        _, caught = simulate_monitoring(dataset, PAGE_LOAD_TIME, threshold, target_incident_day=11)
        assert caught is False


def test_balanced_never_produces_more_false_alarms_than_tight_for_any_metric():
    dataset = generate_incident_log()
    for metric in (CHECKOUT_ERROR_RATE, ON_TIME_DELIVERY_RATE, SOCIAL_MENTIONS, PAGE_LOAD_TIME):
        tight_alarms, _ = simulate_monitoring(dataset, metric, TIGHT, target_incident_day=1)
        balanced_alarms, _ = simulate_monitoring(dataset, metric, BALANCED, target_incident_day=1)
        assert balanced_alarms <= tight_alarms
