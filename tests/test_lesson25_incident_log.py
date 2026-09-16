import statistics

import pytest

from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.alerting import MetricOption, ThresholdOption
from data_science_arcade.lessons.l25_kpi_emergency_room.incident_log import (
    HIGHER_IS_WORSE,
    REAL_INCIDENT_DAYS,
    false_alarm_count,
    false_alarm_count_mirror_code,
    flagged_days,
    flagged_days_mirror_code,
    generate_incident_log,
    monitoring_outcome_mirror_code,
    real_incidents_caught,
    real_incidents_caught_mirror_code,
    simulate_monitoring,
)

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


def test_tight_and_balanced_are_byte_identical_for_checkout_on_its_own_real_incident():
    """The central invariant behind Conflict 1's resolution (METHOD scores
    metric selection only, never threshold): for the metric that actually
    reflects the checkout incident, tight and balanced produce the exact
    same real outcome - 0 false alarms, incident caught, regardless of
    threshold. Scoring threshold choice here would mark an equivalent-
    outcome pick as wrong."""
    dataset = generate_incident_log()
    assert simulate_monitoring(dataset, CHECKOUT_ERROR_RATE, TIGHT, target_incident_day=5) == (0, True)
    assert simulate_monitoring(dataset, CHECKOUT_ERROR_RATE, BALANCED, target_incident_day=5) == (0, True)


def test_tight_and_balanced_are_byte_identical_for_delivery_on_its_own_real_incident():
    dataset = generate_incident_log()
    assert simulate_monitoring(dataset, ON_TIME_DELIVERY_RATE, TIGHT, target_incident_day=11) == (0, True)
    assert simulate_monitoring(dataset, ON_TIME_DELIVERY_RATE, BALANCED, target_incident_day=11) == (0, True)


def test_false_alarm_count_matches_simulate_monitorings_own_count():
    dataset = generate_incident_log()
    assert false_alarm_count(dataset, "page_load_time", multiplier=1.0) == 2
    assert false_alarm_count(dataset, "page_load_time", multiplier=3.0) == 0
    assert false_alarm_count(dataset, "social_mentions", multiplier=1.0) == 3
    assert false_alarm_count(dataset, "social_mentions", multiplier=3.0) == 0


def test_real_incidents_caught_is_a_plural_count_never_a_single_target_day_boolean():
    """The P0 fix behind the reveal-copy correction: this counts across
    BOTH real incidents, distinct from simulate_monitoring's own
    single-target-day incident_caught boolean."""
    dataset = generate_incident_log()
    assert real_incidents_caught(dataset, "checkout_error_rate", multiplier=3.0) == 1  # catches day 5 only
    assert real_incidents_caught(dataset, "on_time_delivery_rate", multiplier=3.0) == 1  # catches day 11 only
    assert real_incidents_caught(dataset, "page_load_time", multiplier=1.0) == 0  # catches neither
    assert real_incidents_caught(dataset, "social_mentions", multiplier=1.0) == 0  # 3 false alarms, none real


def _exec_code(code: str, namespace: dict) -> dict:
    exec(code, namespace)
    return namespace


@pytest.mark.parametrize("metric_key", list(HIGHER_IS_WORSE))
@pytest.mark.parametrize("multiplier", [1.0, 3.0])
def test_flagged_days_mirror_code_matches_the_real_flagged_set(metric_key, multiplier):
    dataset = generate_incident_log()
    real_flagged = flagged_days(dataset, metric_key, multiplier)
    ns = _exec_code(flagged_days_mirror_code(metric_key, multiplier, "x"), {"incident_log": dataset.frame, "statistics": statistics})
    assert ns["x"] == real_flagged


@pytest.mark.parametrize("metric_key", list(HIGHER_IS_WORSE))
@pytest.mark.parametrize("multiplier", [1.0, 3.0])
def test_false_alarm_count_mirror_code_matches_the_real_count(metric_key, multiplier):
    dataset = generate_incident_log()
    ns = _exec_code(false_alarm_count_mirror_code(metric_key, multiplier, "x"), {"incident_log": dataset.frame, "statistics": statistics})
    assert ns["x"] == false_alarm_count(dataset, metric_key, multiplier)


@pytest.mark.parametrize("metric_key", list(HIGHER_IS_WORSE))
@pytest.mark.parametrize("multiplier", [1.0, 3.0])
def test_real_incidents_caught_mirror_code_matches_the_real_count(metric_key, multiplier):
    dataset = generate_incident_log()
    ns = _exec_code(real_incidents_caught_mirror_code(metric_key, multiplier, "x"), {"incident_log": dataset.frame, "statistics": statistics})
    assert ns["x"] == real_incidents_caught(dataset, metric_key, multiplier)


@pytest.mark.parametrize("metric", [CHECKOUT_ERROR_RATE, ON_TIME_DELIVERY_RATE, SOCIAL_MENTIONS, PAGE_LOAD_TIME])
@pytest.mark.parametrize("threshold", [TIGHT, BALANCED])
@pytest.mark.parametrize("target_day", list(REAL_INCIDENT_DAYS))
def test_monitoring_outcome_mirror_code_matches_simulate_monitorings_own_output(metric, threshold, target_day):
    dataset = generate_incident_log()
    real = simulate_monitoring(dataset, metric, threshold, target_day)
    ns = _exec_code(monitoring_outcome_mirror_code(metric, threshold, target_day, "x"), {"incident_log": dataset.frame, "statistics": statistics})
    assert ns["x"] == real
