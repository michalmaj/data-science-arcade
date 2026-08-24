from data_science_arcade.lessons.l01_question_first.twist_data import (
    RECENT_WINDOW_START,
    TOTAL_CUSTOMERS,
    generate_twist_orders,
    repeat_purchase_rate,
)


def test_total_customers_matches_the_unique_customer_ids():
    dataset = generate_twist_orders()
    assert dataset.frame["customer_id"].nunique() == TOTAL_CUSTOMERS


def test_full_year_repeat_rate_is_60_percent():
    dataset = generate_twist_orders()
    assert repeat_purchase_rate(dataset, window_start=None) == 0.60


def test_last_30_days_repeat_rate_is_25_percent():
    dataset = generate_twist_orders()
    assert repeat_purchase_rate(dataset, window_start=RECENT_WINDOW_START) == 0.25


def test_the_twist_is_a_real_reversal_not_just_a_different_number():
    dataset = generate_twist_orders()
    recent = repeat_purchase_rate(dataset, window_start=RECENT_WINDOW_START)
    full_year = repeat_purchase_rate(dataset, window_start=None)
    assert recent < full_year  # the whole pedagogical point: same data, opposite-reading story
