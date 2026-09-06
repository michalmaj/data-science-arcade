from data_science_arcade.lessons.l08_duplicate_detective.twist_data import (
    ALL_ORDERS,
    CONFLICT_ORDER,
    CORRECT_CONFLICT_POLICY,
    CORRECT_DEDUPE_KEY,
    ROUND1_ISSUE,
    ROUND2_ISSUE,
    apply_round1,
    apply_round2,
    build_conflict_group,
    build_decoy_group,
    build_lifecycle_group,
    build_replay_group,
    build_retry_group,
    captured_summary,
    duplicate_count_by,
    full_row_duplicate_count,
    generate_events,
    generate_scan_log,
    true_captured_gmv,
    unique_event_count,
)


def test_raw_feed_has_77_rows():
    dataset = generate_events()
    assert len(dataset.frame) == 77


def test_20_orders_25_payment_attempts_70_unique_events():
    dataset = generate_events()
    assert len(ALL_ORDERS) == 20
    assert dataset.frame["payment_id"].nunique() == 25
    assert unique_event_count(dataset) == 70


def test_full_row_duplicate_count_misses_the_conflicting_row():
    dataset = generate_events()
    # 6 pure replays are full-row identical; the conflicting row is NOT
    # (different amount), so a naive full-row check undercounts by 1.
    assert full_row_duplicate_count(dataset) == 6


def test_event_id_level_duplicate_count_catches_all_7():
    dataset = generate_events()
    assert duplicate_count_by(dataset, "event_id") == 14  # 7 event_ids x 2 rows each


def test_order_id_level_duplicate_count_is_every_row():
    dataset = generate_events()
    # Every order has >= 2 raw event rows by construction, so at this
    # grain every single row "looks duplicated" - a real, deliberate
    # demonstration that the check is meaningless at this grain.
    assert duplicate_count_by(dataset, "order_id") == 77


def test_naive_order_id_dedupe_leaves_zero_captured_rows():
    dataset = apply_round1({"event_id": "dedupe_by_order_id"})
    count, gmv = captured_summary(dataset)
    assert count == 0
    assert gmv == 0.0


def test_naive_event_id_keep_first_lands_on_the_correct_number_by_luck():
    dataset = apply_round1({"event_id": "dedupe_by_event_id_keep_first"})
    count, gmv = captured_summary(dataset)
    assert count == 20
    assert gmv == 1000.0


def test_removing_only_exact_repeats_leaves_the_conflict_visible():
    dataset = apply_round1({"event_id": "remove_exact_repeats_only"})
    count, gmv = captured_summary(dataset)
    assert count == 21
    assert gmv == 1045.0
    assert CORRECT_DEDUPE_KEY == "remove_exact_repeats_only"


def test_correct_full_pipeline_gives_19_orders_950_dollars():
    dataset = apply_round2({"event_id": CORRECT_DEDUPE_KEY}, {"amount": CORRECT_CONFLICT_POLICY})
    count, gmv = captured_summary(dataset)
    assert count == 19
    assert gmv == 950.0


def test_keep_last_after_correct_round1_gives_the_wrong_995():
    dataset = apply_round2({"event_id": CORRECT_DEDUPE_KEY}, {"amount": "keep_last_by_event_id"})
    count, gmv = captured_summary(dataset)
    assert count == 20
    assert gmv == 995.0


def test_keep_higher_amount_after_correct_round1_gives_1000():
    dataset = apply_round2({"event_id": CORRECT_DEDUPE_KEY}, {"amount": "keep_higher_amount"})
    count, gmv = captured_summary(dataset)
    assert count == 20
    assert gmv == 1000.0


def test_conflicting_row_amount_precedes_erroneous_replay_in_raw_order():
    # Determinism the keep='first' vs keep='last' story depends on: the
    # correct $50 copy must come before the erroneous $45 one, in the
    # raw feed's own natural row order (never sorted).
    dataset = generate_events()
    conflict_rows = dataset.frame[
        (dataset.frame["order_id"] == CONFLICT_ORDER) & (dataset.frame["event_type"] == "captured")
    ]
    amounts = conflict_rows["amount"].tolist()
    assert amounts == [50.0, 45.0]


def test_hidden_true_gmv_matches_the_correct_amount_for_every_order():
    assert true_captured_gmv() == 1000.0


def test_round1_issue_and_round2_issue_have_the_expected_option_keys():
    assert {option.key for option in ROUND1_ISSUE.options} == {
        "dedupe_by_order_id",
        "dedupe_by_event_id_keep_first",
        "remove_exact_repeats_only",
    }
    assert {option.key for option in ROUND2_ISSUE.options} == {
        "quarantine_and_disclose",
        "keep_first_by_event_id",
        "keep_last_by_event_id",
        "keep_higher_amount",
    }


def test_replay_group_rows_are_identical_on_every_non_key_column():
    dataset = generate_events()
    group = build_replay_group(dataset)
    assert len(group.rows) == 2
    assert group.rows[0]["amount"] == group.rows[1]["amount"] == "$50.00"
    assert group.rows[0]["event_id"] == group.rows[1]["event_id"]


def test_lifecycle_group_shares_payment_id_but_differs_on_event_type():
    dataset = generate_events()
    group = build_lifecycle_group(dataset)
    assert len(group.rows) == 3
    assert len({row["payment_id"] for row in group.rows}) == 1
    assert len({row["event_type"] for row in group.rows}) == 3


def test_retry_group_shares_order_id_but_has_two_distinct_payment_ids():
    dataset = generate_events()
    group = build_retry_group(dataset)
    assert len(group.rows) == 5  # 2 declined-attempt events + 3 successful-attempt events
    assert len({row["payment_id"] for row in group.rows}) == 2


def test_decoy_group_shares_customer_but_has_distinct_orders_and_events():
    dataset = generate_events()
    group = build_decoy_group(dataset)
    assert len(group.rows) == 2
    assert len({row["order_id"] for row in group.rows}) == 2
    assert len({row["event_id"] for row in group.rows}) == 2
    assert len({row["amount"] for row in group.rows}) == 1  # both $50, genuinely coincidental


def test_conflict_group_shares_event_id_but_differs_on_amount():
    dataset = generate_events()
    group = build_conflict_group(dataset)
    assert len(group.rows) == 2
    assert len({row["event_id"] for row in group.rows}) == 1
    assert {row["amount"] for row in group.rows} == {"$50.00", "$45.00"}


def test_scan_log_has_27_rows_25_unique_scan_events_8_packages():
    dataset = generate_scan_log()
    assert len(dataset.frame) == 27
    assert dataset.frame["scan_event_id"].nunique() == 25
    assert dataset.frame["package_id"].nunique() == 8


def test_scan_log_full_row_duplicate_count_is_exactly_the_2_replays():
    dataset = generate_scan_log()
    assert full_row_duplicate_count(dataset) == 2
