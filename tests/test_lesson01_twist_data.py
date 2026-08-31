import pandas as pd

from data_science_arcade.lessons.l01_question_first.twist_data import (
    RECENT_WINDOW_START,
    TOTAL_CUSTOMERS,
    generate_twist_orders,
    is_returning_household,
    repeat_purchase_rate,
    repeat_rate,
    total_value_by_household_group,
)


def test_total_customers_matches_the_unique_customer_ids():
    dataset = generate_twist_orders()
    assert dataset.frame["customer_id"].nunique() == TOTAL_CUSTOMERS


def test_full_year_repeat_purchase_rate_is_50_percent():
    dataset = generate_twist_orders()
    assert repeat_purchase_rate(dataset, window_start=None) == 0.50


def test_last_30_days_repeat_purchase_rate_is_25_percent():
    dataset = generate_twist_orders()
    assert repeat_purchase_rate(dataset, window_start=RECENT_WINDOW_START) == 0.25


def test_time_window_sensitivity_is_a_real_reversal_not_just_a_different_number():
    # The whole pedagogical point of Act 5: same customer-level definition,
    # same data - only the window changed, and the story changes with it.
    dataset = generate_twist_orders()
    recent = repeat_rate(dataset, "customer_id", RECENT_WINDOW_START)
    full_year = repeat_rate(dataset, "customer_id", None)
    assert recent < full_year
    assert round(recent, 3) == round(1 / 3, 3)  # 10 repeaters of 30 present in the window
    assert full_year == 0.50


def test_entity_sensitivity_is_a_real_shift_at_the_same_fixed_window():
    # Act 6's own point: only entity_column changes here, window stays
    # fixed at RECENT_WINDOW_START throughout - still a real, computable
    # difference, not the window doing the work a second time.
    dataset = generate_twist_orders()
    by_customer = repeat_rate(dataset, "customer_id", RECENT_WINDOW_START)
    by_household = repeat_rate(dataset, "household_id", RECENT_WINDOW_START)
    assert by_household > by_customer
    assert round(by_household, 3) == round(14 / 26, 3)


def test_repeat_rate_denominator_is_distinct_entities_present_in_the_window_not_total_customers():
    # A real methodological distinction Act 5 depends on: someone absent
    # from a window entirely is neither a repeat nor a non-repeat within
    # it - repeat_purchase_rate's own TOTAL_CUSTOMERS-denominator version
    # answers a different (also real, kept for back-compat) question.
    dataset = generate_twist_orders()
    present_in_window = dataset.frame[dataset.frame["order_date"] >= RECENT_WINDOW_START]["customer_id"].nunique()
    assert present_in_window < TOTAL_CUSTOMERS
    assert repeat_rate(dataset, "customer_id", RECENT_WINDOW_START) != repeat_purchase_rate(
        dataset, RECENT_WINDOW_START
    )


def test_household_sharing_customers_are_individually_one_time_but_jointly_repeat():
    dataset = generate_twist_orders()
    shared_household_frame = dataset.frame[dataset.frame["customer_id"] >= 33]
    assert shared_household_frame["household_id"].nunique() == 4  # 8 customers, 4 households
    per_customer_counts = shared_household_frame.groupby("customer_id").size()
    assert (per_customer_counts == 1).all()  # each individual customer: exactly one order
    per_household_counts = shared_household_frame.groupby("household_id").size()
    assert (per_household_counts == 2).all()  # each household: two orders (one per member)


def test_returning_households_spend_more_in_total_than_one_time_households():
    # The real signal the optional mastery challenge's own comparison runs.
    dataset = generate_twist_orders()
    returning_total = total_value_by_household_group(dataset, returning=True)
    one_time_total = total_value_by_household_group(dataset, returning=False)
    assert returning_total > 0
    assert one_time_total > 0
    returning_households = {hid for hid in dataset.frame["household_id"].unique() if is_returning_household(dataset, hid)}
    one_time_households = set(dataset.frame["household_id"].unique()) - returning_households
    returning_avg = returning_total / len(returning_households)
    one_time_avg = one_time_total / len(one_time_households)
    assert returning_avg > one_time_avg


def test_repeat_rate_returns_zero_for_an_entirely_empty_window():
    dataset = generate_twist_orders()
    far_future = RECENT_WINDOW_START + pd.Timedelta(days=3650)
    assert repeat_rate(dataset, "customer_id", far_future) == 0.0
