import pytest

from data_science_arcade.lessons.l25_kpi_emergency_room.incident_log import generate_incident_log, simulate_monitoring
from data_science_arcade.lessons.l25_kpi_emergency_room.requests import CORRECT_METRIC_BY_REQUEST, MONITORING_REQUESTS


def test_exactly_two_requests_are_present():
    """Two genuinely distinct real incidents, each needing its own real
    interactive decision - not padded up or collapsed down to match any
    sibling lesson's own request count."""
    assert {request.key for request in MONITORING_REQUESTS} == {"checkout_incident_focus", "delivery_incident_focus"}


def test_every_request_has_a_correct_metric_recorded():
    assert set(CORRECT_METRIC_BY_REQUEST) == {request.key for request in MONITORING_REQUESTS}


@pytest.mark.parametrize("request_", list(MONITORING_REQUESTS))
def test_the_correct_metric_is_among_the_offered_options(request_):
    correct_metric = CORRECT_METRIC_BY_REQUEST[request_.key]
    assert correct_metric in {option.key for option in request_.metric_options}


@pytest.mark.parametrize("request_", list(MONITORING_REQUESTS))
def test_every_request_offers_exactly_two_metric_and_two_threshold_options(request_):
    assert len(request_.metric_options) == 2
    assert len(request_.threshold_options) == 2


def test_correct_metric_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in MONITORING_REQUESTS:
        correct_metric = CORRECT_METRIC_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.metric_options) if option.key == correct_metric))
    assert len(set(indexes)) > 1


@pytest.mark.parametrize("request_", list(MONITORING_REQUESTS))
def test_the_flawed_metric_option_never_catches_this_requests_own_incident(request_):
    dataset = generate_incident_log()
    correct_metric = CORRECT_METRIC_BY_REQUEST[request_.key]
    flawed_metric = next(option for option in request_.metric_options if option.key != correct_metric)
    for threshold in request_.threshold_options:
        _, caught = simulate_monitoring(dataset, flawed_metric, threshold, request_.target_incident_day)
        assert caught is False


@pytest.mark.parametrize("request_", list(MONITORING_REQUESTS))
def test_the_correct_metric_catches_this_requests_incident_regardless_of_threshold(request_):
    """Conflict 1's own central invariant: for the metric that actually
    reflects this request's real incident, tight and balanced are
    byte-identical - 0 false alarms, incident caught, either way. This is
    exactly why METHOD scores metric selection only, never threshold."""
    dataset = generate_incident_log()
    correct_metric_key = CORRECT_METRIC_BY_REQUEST[request_.key]
    metric = next(option for option in request_.metric_options if option.key == correct_metric_key)
    for threshold in request_.threshold_options:
        false_alarms, caught = simulate_monitoring(dataset, metric, threshold, request_.target_incident_day)
        assert caught is True
        assert false_alarms == 0


def test_no_single_metric_and_threshold_combo_catches_both_real_incidents():
    """The structural reason this lesson needs 2 real interactive
    decisions, not 1: checkout_error_rate never flags day 11, and
    on_time_delivery_rate never flags day 5, at any threshold."""
    dataset = generate_incident_log()
    checkout_request = next(r for r in MONITORING_REQUESTS if r.key == "checkout_incident_focus")
    delivery_request = next(r for r in MONITORING_REQUESTS if r.key == "delivery_incident_focus")
    checkout_metric = next(o for o in checkout_request.metric_options if o.key == "checkout_error_rate")
    delivery_metric = next(o for o in delivery_request.metric_options if o.key == "on_time_delivery_rate")
    for threshold in checkout_request.threshold_options:
        _, caught = simulate_monitoring(dataset, checkout_metric, threshold, target_incident_day=11)
        assert caught is False
    for threshold in delivery_request.threshold_options:
        _, caught = simulate_monitoring(dataset, delivery_metric, threshold, target_incident_day=5)
        assert caught is False
