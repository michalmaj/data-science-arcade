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
    evaluate_gate,
    evaluate_invariant_check,
    evaluate_optional_check,
    final_dataset,
    freshness_within_window_rate,
    generate_inventory_feed,
    generate_orders,
    invariant_fail_count,
    invariant_fail_rate_by_source,
    invariant_mismatch_mask,
    naive_total,
    null_rate_required_fields,
    quarantine_trap_total,
    referral_null_count_and_rate,
    unique_order_id_rate,
    valid_customer_rate,
    valid_status_rate,
)

GOOD_GATE_RESOLUTION = {
    "optional_field_severity": "warn_at_threshold",
    "optional_field_threshold": "flag_over_2pct",
    "invariant_tolerance": "small_tolerance_atol_1",
    "invariant_severity": "block",
}


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


# --- Gate execution model: the authored config is what actually runs ------


def test_optional_check_does_not_exist_when_never_authored():
    dataset = generate_orders()
    outcome = evaluate_optional_check(dataset, {"optional_field_severity": "no_check"})
    assert outcome.exists is False
    assert outcome.assertion_passed is None
    assert outcome.severity is None


def test_optional_check_triggers_a_real_warning_at_the_correct_threshold():
    # The user's own reported P0 #2 example: ~6% null rate, 2% threshold,
    # WARN severity - the assertion must FAIL and the severity must be
    # "warn," never silently counted as a passed check.
    dataset = generate_orders()
    outcome = evaluate_optional_check(dataset, GOOD_GATE_RESOLUTION)
    assert outcome.exists is True
    assert outcome.assertion_passed is False
    assert outcome.severity == "warn"
    assert outcome.affected_count == 12
    assert outcome.affected_total == 200


def test_optional_check_passes_at_a_lenient_enough_threshold():
    dataset = generate_orders()
    outcome = evaluate_optional_check(dataset, dict(GOOD_GATE_RESOLUTION, optional_field_threshold="flag_over_10pct"))
    assert outcome.assertion_passed is True


def test_invariant_check_does_not_exist_when_never_authored():
    dataset = generate_orders()
    outcome = evaluate_invariant_check(dataset, {"invariant_tolerance": "no_invariant_check"})
    assert outcome.exists is False
    assert outcome.assertion_passed is None
    assert outcome.affected_count == 0


def test_invariant_check_flags_the_real_systemic_block_when_authored():
    dataset = generate_orders()
    outcome = evaluate_invariant_check(dataset, GOOD_GATE_RESOLUTION)
    assert outcome.exists is True
    assert outcome.assertion_passed is False
    assert outcome.severity == "block"
    assert outcome.affected_count == 50


def test_gate_never_flags_anything_when_the_invariant_check_was_never_authored():
    # The user's own reported P0 #1 example: picking no_invariant_check
    # must mean the gate genuinely never catches the systemic failure.
    dataset = generate_orders()
    outcome = evaluate_gate(dataset, {"optional_field_severity": "no_check", "invariant_tolerance": "no_invariant_check"})
    assert outcome.assertions_run() == 6
    assert outcome.assertions_passed() == 6
    assert outcome.block_triggered() == ()
    assert outcome.warn_triggered() == ()
    assert outcome.outcome() == "pass"


def test_gate_outcome_is_blocked_when_invariant_block_severity_triggers():
    dataset = generate_orders()
    outcome = evaluate_gate(dataset, GOOD_GATE_RESOLUTION)
    assert outcome.outcome() == "blocked"
    assert outcome.assertions_run() == 8
    assert outcome.assertions_passed() == 6


def test_gate_outcome_is_pass_with_warning_once_the_invariant_is_corrected():
    # The user's own worked example: after a real source replay, the
    # invariant check clears but the optional-field WARN can still be
    # real and triggered - 7/8 assertions passed, 1 WARN, 0 BLOCK.
    dataset = apply_replay(generate_orders())
    outcome = evaluate_gate(dataset, GOOD_GATE_RESOLUTION)
    assert outcome.assertions_run() == 8
    assert outcome.assertions_passed() == 7
    assert len(outcome.warn_triggered()) == 1
    assert outcome.block_triggered() == ()
    assert outcome.outcome() == "pass_with_warning"


def test_invariant_tolerance_is_explicit_about_rtol():
    # Both a real, explicit exact match and a real, explicit small
    # tolerance must use rtol=0.0, never np.isclose's own undocumented
    # default relative tolerance.
    dataset = generate_orders()
    exact = invariant_mismatch_mask(dataset.frame, atol=0.0, rtol=0.0)
    small = invariant_mismatch_mask(dataset.frame, atol=1.0, rtol=0.0)
    assert int(exact.sum()) == int(small.sum()) == 50


def test_quarantining_the_bad_rows_silently_clears_the_gate_even_though_the_kpi_stays_wrong():
    # A real, deliberately uncomfortable consequence: dropping the
    # bad-source rows removes them from the frame entirely, so the
    # invariant check has nothing left to flag - the gate can genuinely
    # read PASS even though the reported total ($22,500) is still wrong.
    # This is exactly what lets the batch-scope Final Decision field (not
    # the gate reveal) carry the real defensibility judgment.
    round1_resolution = {"review_status": CORRECT_ROUND1_KEY}
    quarantined = final_dataset(round1_resolution, {"review_status": "quarantine_and_report_rest"})
    outcome = evaluate_gate(quarantined, GOOD_GATE_RESOLUTION)
    assert outcome.invariant_check.assertion_passed is True
    assert outcome.outcome() in ("pass", "pass_with_warning")
    assert naive_total(quarantined) == 22_500.0
