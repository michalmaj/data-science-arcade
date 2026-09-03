from data_science_arcade.lessons.l04_event_log_factory.twist_data import (
    APPROVED_ATTEMPTS,
    DECLINED_ATTEMPTS,
    ERROR_ATTEMPTS,
    MASTERY_GOOGLE_OAUTH_SIGNUPS,
    MASTERY_RAW_ACCOUNT_CREATED,
    MASTERY_REAL_SIGNUPS,
    REPEAT_PURCHASE_SESSIONS,
    SINGLE_ORDER_SESSIONS,
    SLOW_GATEWAY_ORDERS,
    TOTAL_ATTEMPTS,
    TOTAL_ORDERS,
    TOTAL_SESSIONS,
    event_a_clean,
    event_a_state,
    generate_payment_attempts,
    order_confirmed_counts,
)


def test_hidden_ground_truth_totals_are_internally_consistent():
    assert SINGLE_ORDER_SESSIONS + REPEAT_PURCHASE_SESSIONS == TOTAL_SESSIONS == 90
    assert SINGLE_ORDER_SESSIONS + REPEAT_PURCHASE_SESSIONS * 2 == TOTAL_ORDERS == 96
    assert SLOW_GATEWAY_ORDERS == 18
    assert APPROVED_ATTEMPTS + DECLINED_ATTEMPTS + ERROR_ATTEMPTS == TOTAL_ATTEMPTS == 150
    assert APPROVED_ATTEMPTS == TOTAL_ORDERS  # every real order has exactly one successful attempt
    assert MASTERY_RAW_ACCOUNT_CREATED == MASTERY_REAL_SIGNUPS + MASTERY_GOOGLE_OAUTH_SIGNUPS == 102


def test_order_confirmed_counts_on_the_clean_path_shows_no_gap():
    raw, distinct, label_key = order_confirmed_counts(trigger_is_client_side=False, identifiers_include_order_id=True)
    assert raw == distinct == TOTAL_ORDERS == 96
    assert label_key == "lesson.l04.reveal.distinct_order_id_label"
    assert event_a_clean(False, True) is True
    assert event_a_state(False, True) == "clean"


def test_order_confirmed_counts_with_a_client_trigger_shows_a_real_recoverable_gap():
    # The core detective story: duplicates from a client-side trigger, but
    # order_id makes the true count (96) fully recoverable from the raw
    # 114 rows.
    raw, distinct, label_key = order_confirmed_counts(trigger_is_client_side=True, identifiers_include_order_id=True)
    assert raw == TOTAL_ORDERS + SLOW_GATEWAY_ORDERS == 114
    assert distinct == TOTAL_ORDERS == 96
    assert label_key == "lesson.l04.reveal.distinct_order_id_label"
    assert event_a_clean(True, True) is False
    assert event_a_state(True, True) == "trigger"


def test_order_confirmed_counts_without_order_id_falls_back_to_a_different_wrong_metric():
    # Without order_id, distinct session_id (90) is a genuinely different,
    # wrong answer to "how many orders" - not just less precise - since 6
    # sessions each placed two real orders.
    raw, distinct, label_key = order_confirmed_counts(trigger_is_client_side=False, identifiers_include_order_id=False)
    assert raw == TOTAL_ORDERS == 96
    assert distinct == TOTAL_SESSIONS == 90
    assert label_key == "lesson.l04.reveal.distinct_session_id_label"
    assert event_a_clean(False, False) is False
    assert event_a_state(False, False) == "identifiers"


def test_order_confirmed_counts_worst_case_stacks_both_real_problems():
    raw, distinct, label_key = order_confirmed_counts(trigger_is_client_side=True, identifiers_include_order_id=False)
    assert raw == 114
    assert distinct == TOTAL_SESSIONS == 90
    assert label_key == "lesson.l04.reveal.distinct_session_id_label"
    assert event_a_clean(True, False) is False


def test_event_a_state_names_both_as_its_own_real_state_not_identifiers_alone():
    # The regression case for the real bug: trigger and identifiers are
    # two independent real choices, not one combined flag - a student who
    # broke both needs that named as its own state, not silently folded
    # into "identifiers" (which would make root-cause content claim the
    # trigger is fine when it isn't).
    assert event_a_state(trigger_is_client_side=True, identifiers_include_order_id=False) == "both"
    assert event_a_state(trigger_is_client_side=False, identifiers_include_order_id=False) == "identifiers"
    assert event_a_state(trigger_is_client_side=True, identifiers_include_order_id=True) == "trigger"
    assert event_a_state(trigger_is_client_side=False, identifiers_include_order_id=True) == "clean"


def test_generate_payment_attempts_with_outcome_matches_the_real_breakdown():
    dataset = generate_payment_attempts(outcome_captured=True)
    frame = dataset.frame
    assert len(frame) == TOTAL_ATTEMPTS == 150
    assert set(frame.columns) == {"session_id", "order_id", "outcome"}
    assert set(frame.columns) == set(dataset.schema.column_names())
    counts = frame["outcome"].value_counts().to_dict()
    assert counts == {"approved": APPROVED_ATTEMPTS, "declined": DECLINED_ATTEMPTS, "error": ERROR_ATTEMPTS}
    # Only a successful attempt gets a real order_id - a declined or
    # errored attempt has none, by design.
    assert frame["order_id"].notna().sum() == APPROVED_ATTEMPTS
    assert frame["order_id"].dropna().nunique() == TOTAL_ORDERS


def test_generate_payment_attempts_without_outcome_drops_the_column_entirely():
    # The student sees the field genuinely missing from the schema, not
    # present-but-empty - this is what makes Growth's question
    # unanswerable, discovered by looking, not told.
    dataset = generate_payment_attempts(outcome_captured=False)
    assert "outcome" not in dataset.frame.columns
    assert "outcome" not in dataset.schema.column_names()
    assert len(dataset.frame) == TOTAL_ATTEMPTS == 150


def test_generate_payment_attempts_head_shows_a_real_mix_of_outcomes_immediately():
    # The interleaved row order means even a short head() slice already
    # shows all three outcomes, not 96 approved rows before a decline
    # ever appears.
    dataset = generate_payment_attempts(outcome_captured=True)
    head_outcomes = set(dataset.frame.head(6)["outcome"])
    assert head_outcomes == {"approved", "declined", "error"}
