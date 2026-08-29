from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l26_correlation_crime_scene.correlation_data import (
    compute_correlation,
    compute_correlation_within,
    generate_dark_mode_data,
    generate_push_spend_data,
    generate_shipment_sales_data,
)


def test_all_three_datasets_match_their_schema():
    for dataset in (generate_push_spend_data(), generate_shipment_sales_data(), generate_dark_mode_data()):
        dtesting.assert_matches_schema(dataset)


def test_push_opens_and_spend_are_strongly_correlated():
    dataset = generate_push_spend_data()
    corr = compute_correlation(dataset, "push_opens_per_week", "weekly_spend")
    assert corr > 0.9


def test_shipment_and_sales_are_strongly_correlated():
    dataset = generate_shipment_sales_data()
    corr = compute_correlation(dataset, "shipment_received", "daily_sales")
    assert corr > 0.9


def test_dark_mode_and_spend_correlate_overall_but_not_within_the_modern_group():
    dataset = generate_dark_mode_data()
    overall = compute_correlation(dataset, "dark_mode_enabled", "weekly_spend")
    within_modern = compute_correlation_within(dataset, "device_group", "modern", "dark_mode_enabled", "weekly_spend")
    assert overall > 0.7
    assert abs(within_modern) < 0.2


def test_modern_devices_spend_far_more_than_older_devices_regardless_of_dark_mode():
    dataset = generate_dark_mode_data()
    frame = dataset.frame
    modern_spend = frame[frame["device_group"] == "modern"]["weekly_spend"].mean()
    older_spend = frame[frame["device_group"] == "older"]["weekly_spend"].mean()
    assert modern_spend > older_spend * 1.5
