import pytest

from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l26_correlation_crime_scene.correlation_data import (
    compute_correlation,
    compute_correlation_within,
    compute_device_group_correlation,
    correlation_mirror_code,
    correlation_within_mirror_code,
    device_group_correlation_mirror_code,
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


def test_device_group_correlates_with_spend_even_more_strongly_than_dark_mode_does():
    """The real number behind the confounding reveal's own claim: device
    group is a stronger candidate explanation than dark mode itself."""
    dataset = generate_dark_mode_data()
    device_group_corr = compute_device_group_correlation(dataset, "device_group", "modern", "weekly_spend")
    dark_mode_corr = compute_correlation(dataset, "dark_mode_enabled", "weekly_spend")
    assert device_group_corr > dark_mode_corr
    assert device_group_corr > 0.9


def test_older_device_group_has_zero_variance_in_dark_mode_usage():
    """The reason the within-older-group correlation is undefined and
    must never be computed or shown to the student - confirmed directly
    rather than assumed."""
    dataset = generate_dark_mode_data()
    older = dataset.frame[dataset.frame["device_group"] == "older"]
    assert older["dark_mode_enabled"].nunique() == 1
    assert not older["dark_mode_enabled"].any()


def _exec_code(code: str, namespace: dict) -> dict:
    exec(code, namespace)
    return namespace


@pytest.mark.parametrize(
    "request_key,dataset_var,column_a,column_b",
    [
        ("push_opens_claim", "push_spend", "push_opens_per_week", "weekly_spend"),
        ("shipment_sales_claim", "shipment_sales", "shipment_received", "daily_sales"),
        ("dark_mode_claim", "dark_mode", "dark_mode_enabled", "weekly_spend"),
    ],
)
def test_correlation_mirror_code_matches_the_real_correlation(request_key, dataset_var, column_a, column_b):
    generators = {
        "push_spend": generate_push_spend_data,
        "shipment_sales": generate_shipment_sales_data,
        "dark_mode": generate_dark_mode_data,
    }
    dataset = generators[dataset_var]()
    real = compute_correlation(dataset, column_a, column_b)
    ns = _exec_code(correlation_mirror_code(request_key, "x"), {dataset_var: dataset.frame})
    assert ns["x"] == real


def test_correlation_within_mirror_code_matches_the_real_subgroup_correlation():
    dataset = generate_dark_mode_data()
    real = compute_correlation_within(dataset, "device_group", "modern", "dark_mode_enabled", "weekly_spend")
    ns = _exec_code(
        correlation_within_mirror_code("device_group", "modern", "dark_mode_enabled", "weekly_spend", "x"),
        {"dark_mode": dataset.frame},
    )
    assert ns["x"] == real
    assert -0.09 < ns["x"] < -0.08  # the real, verified within-modern figure - never the general one


def test_device_group_correlation_mirror_code_matches_the_real_correlation():
    dataset = generate_dark_mode_data()
    real = compute_device_group_correlation(dataset, "device_group", "modern", "weekly_spend")
    ns = _exec_code(device_group_correlation_mirror_code("device_group", "modern", "weekly_spend", "x"), {"dark_mode": dataset.frame})
    assert ns["x"] == real


def test_device_group_correlation_mirror_code_never_mutates_the_real_dataset():
    dataset = generate_dark_mode_data()
    original_columns = list(dataset.frame.columns)
    _exec_code(device_group_correlation_mirror_code("device_group", "modern", "weekly_spend", "x"), {"dark_mode": dataset.frame})
    assert list(dataset.frame.columns) == original_columns  # no "is_modern" column leaked onto the real frame
