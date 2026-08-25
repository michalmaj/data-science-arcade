from data_science_arcade.lessons.l04_event_log_factory.twist_data import (
    CONFIRMED_SESSIONS,
    MISSING_EVENT,
    TOTAL_SESSIONS,
    event_rate,
    generate_checkout_events,
)


def test_checkout_started_fires_for_every_session():
    dataset = generate_checkout_events()
    assert event_rate(dataset, "checkout_started") == 1.0


def test_the_missing_event_never_fires():
    dataset = generate_checkout_events()
    assert event_rate(dataset, MISSING_EVENT) == 0.0


def test_order_confirmed_matches_the_engineered_rate():
    dataset = generate_checkout_events()
    assert event_rate(dataset, "order_confirmed") == 0.62
    assert CONFIRMED_SESSIONS / TOTAL_SESSIONS == 0.62


def test_an_unrelated_event_name_also_has_a_zero_rate():
    dataset = generate_checkout_events()
    assert event_rate(dataset, "not_a_real_event") == 0.0
