import pytest

from data_science_arcade.lessons.l11_distribution_observatory.order_values import (
    BUSINESS_COUNT,
    CONSUMER_COUNT,
    generate_order_values,
    segment_mean,
)


def test_generates_the_expected_row_count():
    dataset = generate_order_values()
    assert len(dataset.frame) == CONSUMER_COUNT + BUSINESS_COUNT == 100


def test_two_segments_are_present_with_the_expected_counts():
    dataset = generate_order_values()
    counts = dataset.frame["segment"].value_counts()
    assert counts["consumer"] == CONSUMER_COUNT
    assert counts["business"] == BUSINESS_COUNT


def test_the_two_segments_occupy_non_overlapping_value_ranges():
    dataset = generate_order_values()
    frame = dataset.frame
    consumer_max = frame.loc[frame["segment"] == "consumer", "order_value"].max()
    business_min = frame.loc[frame["segment"] == "business", "order_value"].min()
    assert consumer_max < business_min


def test_the_overall_mean_is_pulled_well_above_the_typical_consumer_order():
    # Real computed values (verified via a manual script before writing
    # this assertion), not hand-picked: the mean lands far from either
    # segment's own typical value because a minority of high-value business
    # orders drags it upward.
    dataset = generate_order_values()
    overall_mean = float(dataset.frame["order_value"].mean())
    assert overall_mean == pytest.approx(256.8)
    assert overall_mean > segment_mean(dataset, "consumer") * 2


def test_the_overall_median_sits_inside_the_consumer_segment_only():
    dataset = generate_order_values()
    overall_median = float(dataset.frame["order_value"].median())
    consumer_max = dataset.frame.loc[dataset.frame["segment"] == "consumer", "order_value"].max()
    business_min = dataset.frame.loc[dataset.frame["segment"] == "business", "order_value"].min()
    assert consumer_max >= overall_median
    assert overall_median < business_min


def test_segment_means_are_computed_not_hand_picked():
    dataset = generate_order_values()
    assert segment_mean(dataset, "consumer") == pytest.approx(49.0)
    assert segment_mean(dataset, "business") == pytest.approx(741.6666666666666)
