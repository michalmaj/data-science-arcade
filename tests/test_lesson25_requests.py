import pytest

from data_science_arcade.lessons.l25_kpi_emergency_room.incident_log import generate_incident_log, simulate_monitoring
from data_science_arcade.lessons.l25_kpi_emergency_room.requests import CORRECT_COMBO_BY_REQUEST, MONITORING_REQUESTS


def test_all_three_requests_are_present():
    assert {request.key for request in MONITORING_REQUESTS} == {
        "checkout_incident_focus",
        "delivery_incident_focus",
        "monitor_everything_temptation",
    }


def test_every_request_has_a_correct_combo_recorded():
    assert set(CORRECT_COMBO_BY_REQUEST) == {request.key for request in MONITORING_REQUESTS}


@pytest.mark.parametrize("request_", list(MONITORING_REQUESTS))
def test_the_correct_metric_is_among_the_offered_options(request_):
    correct_metric, _correct_threshold = CORRECT_COMBO_BY_REQUEST[request_.key]
    assert correct_metric in {option.key for option in request_.metric_options}


@pytest.mark.parametrize("request_", list(MONITORING_REQUESTS))
def test_the_correct_threshold_is_among_the_offered_options(request_):
    _correct_metric, correct_threshold = CORRECT_COMBO_BY_REQUEST[request_.key]
    assert correct_threshold in {option.key for option in request_.threshold_options}


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
        correct_metric, _ = CORRECT_COMBO_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.metric_options) if option.key == correct_metric))
    assert len(set(indexes)) > 1


def test_correct_threshold_position_varies_across_requests():
    indexes = []
    for request_ in MONITORING_REQUESTS:
        _, correct_threshold = CORRECT_COMBO_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.threshold_options) if option.key == correct_threshold))
    assert len(set(indexes)) > 1


@pytest.mark.parametrize("request_", list(MONITORING_REQUESTS))
def test_the_flawed_metric_option_never_catches_this_requests_own_incident(request_):
    dataset = generate_incident_log()
    correct_metric, _ = CORRECT_COMBO_BY_REQUEST[request_.key]
    flawed_metric = next(option for option in request_.metric_options if option.key != correct_metric)
    for threshold in request_.threshold_options:
        _, caught = simulate_monitoring(dataset, flawed_metric, threshold, request_.target_incident_day)
        assert caught is False


@pytest.mark.parametrize("request_", list(MONITORING_REQUESTS))
def test_the_correct_combo_catches_this_requests_incident_with_no_false_alarms(request_):
    dataset = generate_incident_log()
    correct_metric_key, correct_threshold_key = CORRECT_COMBO_BY_REQUEST[request_.key]
    metric = next(option for option in request_.metric_options if option.key == correct_metric_key)
    threshold = next(option for option in request_.threshold_options if option.key == correct_threshold_key)
    false_alarms, caught = simulate_monitoring(dataset, metric, threshold, request_.target_incident_day)
    assert caught is True
    assert false_alarms == 0
