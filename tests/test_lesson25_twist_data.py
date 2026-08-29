from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l25_kpi_emergency_room.twist_data import alert_count, generate_alert_fatigue_data, response_minutes


def test_generated_data_matches_its_schema():
    dataset = generate_alert_fatigue_data()
    dtesting.assert_matches_schema(dataset)


def test_false_alarms_vastly_outnumber_the_one_real_incident():
    dataset = generate_alert_fatigue_data()
    assert alert_count(dataset, "false_alarm") == 46
    assert alert_count(dataset, "real_incident") == 1


def test_the_real_incident_took_far_longer_to_notice_than_a_typical_false_alarm():
    dataset = generate_alert_fatigue_data()
    assert response_minutes(dataset, "false_alarm") == 4
    assert response_minutes(dataset, "real_incident") == 360
    assert response_minutes(dataset, "real_incident") > response_minutes(dataset, "false_alarm")
