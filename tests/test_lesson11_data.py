import pytest

from data_science_arcade.lessons.l11_distribution_observatory.order_values import (
    BUSINESS_COUNT,
    CONSUMER_COUNT,
    PROCESS_A_VALUES,
    PROCESS_B_VALUES,
    generate_order_values,
    mastery_process_series,
    order_value_segments,
    order_values_list,
    segment_mean,
)


def test_generates_the_expected_row_count():
    dataset = generate_order_values()
    assert len(dataset.frame) == CONSUMER_COUNT + BUSINESS_COUNT == 100


def test_the_player_facing_frame_has_no_segment_column():
    # Segment-hiding by construction, not convention: the schema and the
    # frame it produces carry only order_id/order_value - no `segment`
    # column exists anywhere for a generic table view to leak.
    dataset = generate_order_values()
    assert list(dataset.frame.columns) == ["order_id", "order_value"]
    assert "segment" not in dataset.schema.column_names()


def test_the_two_segments_occupy_non_overlapping_value_ranges():
    consumer_values, business_values = (values for _key, _label, values in order_value_segments())
    assert max(consumer_values) < min(business_values)


def test_segment_counts_match_the_published_constants():
    segments = dict((key, values) for key, _label, values in order_value_segments())
    assert len(segments["consumer"]) == CONSUMER_COUNT == 70
    assert len(segments["business"]) == BUSINESS_COUNT == 30


def test_the_overall_mean_lands_in_the_real_gap_between_segments():
    # Verified independently via a real script, not hand-waved: the mean
    # sits in a range with zero real orders on either side.
    values = order_values_list()
    mean = sum(values) / len(values)
    consumer_values, business_values = (v for _k, _l, v in order_value_segments())
    assert mean == pytest.approx(256.8)
    assert max(consumer_values) < mean < min(business_values)


def test_the_overall_median_sits_inside_the_consumer_segment_only():
    dataset = generate_order_values()
    values = sorted(dataset.frame["order_value"].tolist())
    median = float(dataset.frame["order_value"].median())
    consumer_values, business_values = (v for _k, _l, v in order_value_segments())
    assert median == pytest.approx(60.0)
    assert max(consumer_values) >= median
    assert median < min(business_values)


def test_quantiles_match_the_hand_verified_arithmetic():
    dataset = generate_order_values()
    series = dataset.frame["order_value"]
    assert float(series.quantile(0.25)) == pytest.approx(40.0)
    assert float(series.quantile(0.75)) == pytest.approx(612.5)
    assert float(series.quantile(0.90)) == pytest.approx(800.0)


def test_segment_means_are_computed_not_hand_picked():
    assert segment_mean("consumer") == pytest.approx(49.0)
    assert segment_mean("business") == pytest.approx(741.6666666666666)


def test_segment_mean_rejects_an_unknown_segment():
    with pytest.raises(KeyError):
        segment_mean("wholesale")


# --- Optional mastery: same mean, wildly different distribution -----------


def test_process_a_and_process_b_share_the_exact_same_mean():
    mean_a = sum(PROCESS_A_VALUES) / len(PROCESS_A_VALUES)
    mean_b = sum(PROCESS_B_VALUES) / len(PROCESS_B_VALUES)
    assert mean_a == pytest.approx(30.0)
    assert mean_b == pytest.approx(30.0)
    assert mean_a == pytest.approx(mean_b)


def test_process_a_and_process_b_have_wildly_different_medians():
    sorted_a = sorted(PROCESS_A_VALUES)
    sorted_b = sorted(PROCESS_B_VALUES)
    median_a = sorted_a[len(sorted_a) // 2]
    median_b = sorted_b[len(sorted_b) // 2]
    assert median_a == pytest.approx(30.0)
    assert median_b == pytest.approx(20.0)
    assert median_a != median_b


def test_process_b_has_a_real_long_tail_process_a_does_not():
    assert len(PROCESS_A_VALUES) == len(PROCESS_B_VALUES) == 30
    assert max(PROCESS_B_VALUES) - min(PROCESS_B_VALUES) > max(PROCESS_A_VALUES) - min(PROCESS_A_VALUES)


def test_mastery_process_series_wraps_the_same_published_values():
    series = mastery_process_series()
    values_by_key = {key: values for key, _label, values in series}
    assert values_by_key["process_a"] == list(PROCESS_A_VALUES)
    assert values_by_key["process_b"] == list(PROCESS_B_VALUES)
