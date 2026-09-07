from data_science_arcade.lessons.l09_outlier_patrol.twist_data import (
    ANOMALY_ISSUE,
    ANOMALY_ORDER,
    BULK_ISSUE,
    BULK_ORDER,
    CORRECT_ANOMALY_KEY,
    CORRECT_BULK_KEY,
    CORRECT_DECIMAL_KEY,
    CORRECT_ROUND1_KEY,
    DECIMAL_ERROR_ORDER,
    DECIMAL_ISSUE,
    HIGH_REPRODUCIBILITY_ROUND1_KEYS,
    HIGH_REPRODUCIBILITY_ROUND2_KEYS,
    MEDIUM_REPRODUCIBILITY_ROUND1_KEYS,
    MEDIUM_REPRODUCIBILITY_ROUND2_KEYS,
    ROUND1_ISSUE,
    ROUND2_ISSUES,
    apply_round1,
    apply_round2,
    flagged_count,
    generate_orders,
    generate_support_tickets,
    global_fence,
    total_exposure_state,
    typical_standard_order_state,
    zone_fence,
    zone_flag_rate,
)

GOOD_ROUND1_RESOLUTION = {"fulfillment_cost": "no_blanket_action"}
GOOD_ROUND2_RESOLUTION = {
    "fulfillment_cost": "correct_via_invoice",
    "order_type": "keep_as_is",
    "incident_reference": "keep_and_flag_as_documented_incident",
}


def test_raw_feed_has_89_rows():
    dataset = generate_orders()
    assert len(dataset.frame) == 89


def test_global_fence_flags_exactly_11_rows():
    dataset = generate_orders()
    lower, upper = global_fence(dataset)
    assert (lower, upper) == (31.0, 63.0)
    assert flagged_count(dataset, lower, upper) == 11


def test_remote_zone_is_flagged_globally_but_clears_its_own_fence():
    dataset = generate_orders()
    lower, upper = global_fence(dataset)
    assert zone_flag_rate(dataset, "remote", lower, upper) == 1.0

    remote_low, remote_up = zone_fence(dataset, "remote")
    assert (remote_low, remote_up) == (63.0, 91.0)
    assert zone_flag_rate(dataset, "remote", remote_low, remote_up) == 0.0


def test_urban_zone_flag_rate_is_the_same_globally_and_locally():
    # The 3 special rows are genuinely unusual regardless of scope - only
    # the remote zone shows a real global-vs-own-fence discrepancy.
    dataset = generate_orders()
    lower, upper = global_fence(dataset)
    urban_low, urban_up = zone_fence(dataset, "urban")
    assert zone_flag_rate(dataset, "urban", lower, upper) == zone_flag_rate(dataset, "urban", urban_low, urban_up)


def test_raw_typical_and_total_state():
    dataset = generate_orders()
    assert typical_standard_order_state(dataset) == (88, 47.0)
    assert total_exposure_state(dataset) == (89, 10164.0)


def test_correct_full_pipeline_gives_the_real_typical_and_total_numbers():
    dataset = apply_round2(GOOD_ROUND1_RESOLUTION, GOOD_ROUND2_RESOLUTION)
    assert typical_standard_order_state(dataset) == (88, 47.0)
    assert total_exposure_state(dataset) == (89, 5610.0)


def test_naive_blanket_drop_gives_a_deceptively_clean_but_wrong_number():
    dataset = apply_round1({"fulfillment_cost": "drop_outside_fence"})
    assert typical_standard_order_state(dataset) == (78, 46.0)
    assert total_exposure_state(dataset) == (78, 3588.0)


def test_decimal_uncorrected_leaves_the_median_looking_identical():
    # The median is robust enough that leaving the $4,600.00 error
    # uncorrected produces the exact same (88, 47.0) typical-cost number
    # as the correct pipeline - the "looks resolved" trap this lesson is
    # built around. The total, unlike the median, does move.
    dataset = apply_round2(
        GOOD_ROUND1_RESOLUTION,
        {"fulfillment_cost": "keep_as_is", "order_type": "keep_as_is", "incident_reference": "keep_and_flag_as_documented_incident"},
    )
    assert typical_standard_order_state(dataset) == (88, 47.0)
    assert total_exposure_state(dataset) == (89, 10164.0)


def test_bulk_order_wrongly_dropped_understates_total_exposure():
    dataset = apply_round2(
        GOOD_ROUND1_RESOLUTION,
        {"fulfillment_cost": "correct_via_invoice", "order_type": "drop_row", "incident_reference": "keep_and_flag_as_documented_incident"},
    )
    assert total_exposure_state(dataset) == (88, 4660.0)


def test_bulk_order_is_scoped_out_by_its_own_order_type_not_by_being_dropped():
    # keep_as_is (the correct treatment) never touches order_type -
    # population membership for the typical-standard-order metric comes
    # purely from that real business field.
    dataset = apply_round2(GOOD_ROUND1_RESOLUTION, GOOD_ROUND2_RESOLUTION)
    bulk_row = dataset.frame[dataset.frame["order_id"] == BULK_ORDER].iloc[0]
    assert bulk_row["order_type"] == "enterprise_bulk"
    assert bulk_row["fulfillment_cost"] == 950.0


def test_decimal_error_correction_uses_the_real_invoice_reference():
    dataset = apply_round2(GOOD_ROUND1_RESOLUTION, GOOD_ROUND2_RESOLUTION)
    row = dataset.frame[dataset.frame["order_id"] == DECIMAL_ERROR_ORDER].iloc[0]
    assert row["fulfillment_cost"] == 46.0


def test_anomaly_row_keeps_its_real_value_and_incident_reference():
    dataset = apply_round2(GOOD_ROUND1_RESOLUTION, GOOD_ROUND2_RESOLUTION)
    row = dataset.frame[dataset.frame["order_id"] == ANOMALY_ORDER].iloc[0]
    assert row["fulfillment_cost"] == 410.0
    assert row["incident_reference"] is not None


def test_round1_and_round2_option_keys_match_the_answer_key():
    assert {option.key for option in ROUND1_ISSUE.options} == {"drop_outside_fence", "no_blanket_action", "cap_at_fence"}
    assert CORRECT_ROUND1_KEY in {option.key for option in ROUND1_ISSUE.options}
    assert {option.key for option in DECIMAL_ISSUE.options} == {"drop_row", "correct_via_invoice", "keep_as_is"}
    assert CORRECT_DECIMAL_KEY in {option.key for option in DECIMAL_ISSUE.options}
    assert {option.key for option in BULK_ISSUE.options} == {"drop_row", "keep_as_is", "correct_to_typical_value"}
    assert CORRECT_BULK_KEY in {option.key for option in BULK_ISSUE.options}
    assert {option.key for option in ANOMALY_ISSUE.options} == {
        "drop_row",
        "keep_silently",
        "keep_and_flag_as_documented_incident",
    }
    assert CORRECT_ANOMALY_KEY in {option.key for option in ANOMALY_ISSUE.options}


def test_round2_issues_use_three_distinct_columns():
    # RepairResolution is a plain {column: option_key} dict - the 3
    # Round 2 issues must never share a column, or one issue's pick
    # would silently overwrite another's in the same resolution dict.
    columns = [issue.column for issue in ROUND2_ISSUES]
    assert len(columns) == len(set(columns)) == 3


def test_every_round1_and_round2_option_has_a_reproducibility_tier():
    round1_keys = {option.key for option in ROUND1_ISSUE.options}
    assert round1_keys == HIGH_REPRODUCIBILITY_ROUND1_KEYS | MEDIUM_REPRODUCIBILITY_ROUND1_KEYS
    assert HIGH_REPRODUCIBILITY_ROUND1_KEYS.isdisjoint(MEDIUM_REPRODUCIBILITY_ROUND1_KEYS)
    round2_tier_keys = HIGH_REPRODUCIBILITY_ROUND2_KEYS | MEDIUM_REPRODUCIBILITY_ROUND2_KEYS
    for issue in ROUND2_ISSUES:
        keys = {option.key for option in issue.options}
        assert keys.issubset(round2_tier_keys)
        assert keys & HIGH_REPRODUCIBILITY_ROUND2_KEYS, f"{issue.column} has no high-tier (correct) option"
    assert HIGH_REPRODUCIBILITY_ROUND2_KEYS.isdisjoint(MEDIUM_REPRODUCIBILITY_ROUND2_KEYS)


def test_mastery_support_tickets_have_one_real_extreme_and_one_real_error():
    dataset = generate_support_tickets()
    assert len(dataset.frame) == 42
    negative = dataset.frame[dataset.frame["resolution_minutes"] < 0]
    assert len(negative) == 1
    extreme = dataset.frame[dataset.frame["resolution_minutes"] > 100]
    assert len(extreme) == 1
    assert extreme.iloc[0]["incident_reference"] is not None
