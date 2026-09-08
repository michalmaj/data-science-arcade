from data_science_arcade.lessons.l10_validation_gate.twist_data import (
    BAD_ORDERS,
    BAD_SOURCE,
    CORRECT_BATCH_ACTION_KEY,
    CORRECT_ROUND1_KEY,
    GOOD_ORDERS,
    amount_in_range_rate,
    apply_batch_action,
    apply_replay,
    apply_round1,
    baseline_checks_passed,
    final_dataset,
    freshness_within_window_rate,
    generate_inventory_feed,
    generate_orders,
    invariant_fail_count,
    invariant_fail_rate_by_source,
    naive_total,
    null_rate_required_fields,
    quarantine_trap_total,
    referral_null_count_and_rate,
    unique_order_id_rate,
    valid_customer_rate,
    valid_status_rate,
)


def test_two_hundred_orders_total():
    dataset = generate_orders()
    assert len(dataset.frame) == GOOD_ORDERS + BAD_ORDERS == 200


def test_every_baseline_check_passes_on_the_raw_feed():
    dataset = generate_orders()
    assert unique_order_id_rate(dataset) == 1.0
    assert null_rate_required_fields(dataset) == 0.0
    assert valid_customer_rate(dataset) == 1.0
    assert valid_status_rate(dataset) == 1.0
    assert freshness_within_window_rate(dataset) == 1.0
    assert amount_in_range_rate(dataset) == 1.0
    assert baseline_checks_passed(dataset) == 6


def test_the_systemic_bug_still_falls_within_the_wide_range_check():
    # The whole point of the twist: nothing about the bad rows looks
    # invalid on its own - a $0-$25,000 range check would never flag them.
    dataset = generate_orders()
    bad_rows = dataset.frame[dataset.frame["source_system"] == BAD_SOURCE]
    assert (bad_rows["recorded_amount_usd"] == 15_000.0).all()
    assert amount_in_range_rate(dataset) == 1.0


def test_referral_source_nulls_are_the_same_rate_in_both_segments():
    dataset = generate_orders()
    count, rate = referral_null_count_and_rate(dataset)
    assert count == 12
    assert rate == 0.06


def test_naive_total_at_face_value():
    dataset = generate_orders()
    assert naive_total(dataset) == 772_500.0


def test_quarantine_trap_total_silently_understates_real_exposure():
    dataset = generate_orders()
    trap_total = quarantine_trap_total(dataset)
    assert trap_total == 22_500.0
    # The trap's own gap from the real corrected total is exactly the 50
    # dropped orders' own real value - not an approximation.
    corrected = naive_total(apply_replay(dataset))
    assert corrected - trap_total == 7_500.0


def test_corrected_total_after_a_real_replay():
    dataset = generate_orders()
    corrected = apply_replay(dataset)
    assert naive_total(corrected) == 30_000.0
    assert invariant_fail_count(corrected) == 0


def test_invariant_check_flags_exactly_the_systemic_block():
    dataset = generate_orders()
    assert invariant_fail_count(dataset) == 50
    rates = invariant_fail_rate_by_source(dataset)
    assert rates["checkout_v2"] == 0.0
    assert rates["legacy_pos_v1"] == 1.0


def test_apply_round1_replays_the_students_own_pick():
    approved = apply_round1({"review_status": "approve_for_publication"})
    assert (approved.frame["review_status"] == "published_naive").all()

    held = apply_round1({"review_status": CORRECT_ROUND1_KEY})
    assert (held.frame["review_status"] == "held_for_validation").all()


def test_final_dataset_only_replays_when_the_batch_action_is_correct():
    round1_resolution = {"review_status": CORRECT_ROUND1_KEY}

    blocked = final_dataset(round1_resolution, {"review_status": CORRECT_BATCH_ACTION_KEY})
    assert naive_total(blocked) == 30_000.0
    assert invariant_fail_count(blocked) == 0

    quarantined = final_dataset(round1_resolution, {"review_status": "quarantine_and_report_rest"})
    assert naive_total(quarantined) == 22_500.0

    published_anyway = final_dataset(round1_resolution, {"review_status": "publish_anyway"})
    assert naive_total(published_anyway) == 772_500.0
    assert invariant_fail_count(published_anyway) == 50


def test_apply_batch_action_never_replays_on_its_own():
    round1_resolution = {"review_status": CORRECT_ROUND1_KEY}
    blocked_not_yet_replayed = apply_batch_action(round1_resolution, {"review_status": CORRECT_BATCH_ACTION_KEY})
    assert invariant_fail_count(blocked_not_yet_replayed) == 50
    assert naive_total(blocked_not_yet_replayed) == 772_500.0


def test_inventory_mastery_feed_has_one_real_cross_field_violation():
    dataset = generate_inventory_feed()
    frame = dataset.frame
    assert (frame["stock_on_hand"] >= 0).all()
    violating = frame[frame["available_to_promise"] > frame["stock_on_hand"]]
    assert len(violating) > 0
    assert set(violating["source_batch"]) == {"legacy_wms_sync"}
    clean = frame[frame["source_batch"] != "legacy_wms_sync"]
    assert (clean["available_to_promise"] <= clean["stock_on_hand"]).all()
