import math

import pandas as pd
import pytest

from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import (
    CORRECT_REPAIR,
    DELIVERED_AT_ISSUE,
    DURATION_ISSUE,
    MASTERY_CORRECT,
    ROUND1_ISSUES,
    ROUND2_ISSUES,
    SAFE_COLUMNS_CORRECT,
    SHIPMENT_ID_ISSUE,
    apply_round1,
    apply_round2,
    breach_rate,
    generate_mastery_export,
    generate_shipments,
    last_month_breach_rate,
    malformed_count,
)

GOOD_ROUND1 = {"shipment_id": "cast_to_text", "delivered_at": "coerce_keep_nat"}
GOOD_ROUND2 = {"duration_minutes": "fix_store_d_only"}


def test_raw_export_has_the_hand_verified_row_count():
    raw = generate_shipments()
    assert len(raw.frame) == 222  # 180 this month + 2 malformed + 40 last month
    assert raw.frame["shipment_id"].dtype == "int64"
    # Not yet a real timestamp - exactly the point of the delivered_at
    # issue. Plain text infers to pandas' modern "str" extension dtype in
    # this pandas version (future.infer_string), not the legacy "object" -
    # checking "not a real datetime yet" rather than a specific text dtype
    # name keeps this robust across pandas versions.
    assert not str(raw.frame["delivered_at"].dtype).startswith("datetime64")


def test_round1_replay_of_the_correct_resolution_produces_the_correct_dtypes():
    repaired = apply_round1(GOOD_ROUND1)
    assert repaired.frame["shipment_id"].dtype == "string"
    assert str(repaired.frame["delivered_at"].dtype).startswith("datetime64")
    assert malformed_count(repaired) == 2
    assert repaired.schema.columns[0].dtype == "string"  # displayed schema matches the real frame
    assert repaired.schema.columns[2].dtype == "datetime64[ns]"


def test_round1_replay_never_touches_an_unresolved_columns_own_schema():
    # Resolving only shipment_id must not silently mark delivered_at as
    # fixed too, even though the two issues used to share one Schema
    # object - the real bug this test guards against.
    partial = apply_round1({"shipment_id": "cast_to_text"})
    delivered_at_schema = next(c for c in partial.schema.columns if c.name == "delivered_at")
    assert delivered_at_schema.dtype == "object"
    assert delivered_at_schema.description_key == "lesson.l06.schema.delivered_at.description"


def test_round1_replay_reflects_whichever_real_shipment_id_option_was_picked():
    text = apply_round1({"shipment_id": "cast_to_text", "delivered_at": "coerce_keep_nat"})
    kept_int = apply_round1({"shipment_id": "recast_int", "delivered_at": "coerce_keep_nat"})
    category = apply_round1({"shipment_id": "cast_category", "delivered_at": "coerce_keep_nat"})
    assert text.schema.columns[0].dtype == text.frame["shipment_id"].dtype.name == "string"
    assert kept_int.schema.columns[0].dtype == kept_int.frame["shipment_id"].dtype.name == "int64"
    assert category.schema.columns[0].dtype == category.frame["shipment_id"].dtype.name == "category"


def test_this_months_shipments_total_180_across_four_stores():
    repaired = apply_round1(GOOD_ROUND1)
    this_month = repaired.frame[repaired.frame["delivered_at"].dt.strftime("%Y-%m") == "2026-09"]
    assert len(this_month) == 180
    counts = this_month["store"].value_counts().to_dict()
    assert counts == {"A": 60, "B": 60, "C": 24, "D": 36}


def test_naive_breach_rate_matches_the_hand_verified_29_percent():
    repaired = apply_round1(GOOD_ROUND1)
    assert breach_rate(repaired) == pytest.approx(53 / 180)


def test_corrected_breach_rate_matches_the_hand_verified_12_percent():
    repaired = apply_round2(GOOD_ROUND1, GOOD_ROUND2)
    assert breach_rate(repaired) == pytest.approx(22 / 180)


def test_breach_rate_reflects_whichever_real_duration_option_was_picked_not_a_ground_truth_override():
    correct = breach_rate(apply_round2(GOOD_ROUND1, {"duration_minutes": "fix_store_d_only"}))
    over_corrected = breach_rate(apply_round2(GOOD_ROUND1, {"duration_minutes": "fix_every_row"}))
    denied = breach_rate(apply_round2(GOOD_ROUND1, {"duration_minutes": "recast_float"}))

    assert correct == pytest.approx(22 / 180)
    assert denied == pytest.approx(53 / 180)  # unchanged - denies the problem
    assert over_corrected < correct  # breaks the majority (A/B/C) to fix the minority (D)


def test_breach_rate_is_nan_not_a_crash_when_no_row_this_month_parses():
    # wrong_format mismatches every real row's format (including last
    # month's own ISO strings), so every row becomes NaT - a real,
    # honest "can't compute this" consequence, not a crash.
    broken = apply_round1({"shipment_id": "cast_to_text", "delivered_at": "wrong_format"})
    assert math.isnan(breach_rate(broken))


def test_last_month_baseline_is_close_to_this_months_true_rate():
    repaired = apply_round2(GOOD_ROUND1, GOOD_ROUND2)
    baseline = last_month_breach_rate(repaired)
    assert baseline == pytest.approx(5 / 40)
    # The whole point of this baseline: nothing about delivery speed
    # really changed month over month - only how this month's numbers get
    # misread does.
    assert abs(baseline - breach_rate(repaired)) < 0.02


@pytest.mark.parametrize("issue", [SHIPMENT_ID_ISSUE, DELIVERED_AT_ISSUE, DURATION_ISSUE])
def test_every_issue_has_at_least_three_real_options(issue):
    assert len(issue.options) >= 3


def test_shipment_id_repair_options_produce_three_different_real_dtypes():
    raw = generate_shipments()
    dtypes = {option.key: option.apply(raw.frame)["shipment_id"].dtype.name for option in SHIPMENT_ID_ISSUE.options}
    assert dtypes["cast_to_text"] == "string"
    assert dtypes["recast_int"] == "int64"
    assert dtypes["cast_category"] == "category"


def test_shipment_id_correct_repair_accepts_either_valid_representation():
    # An identifier's own physical representation doesn't need to change
    # just because it's semantically an identifier - kept-int64 and
    # cast-to-text are both real, acceptable answers; only category is
    # a genuine misuse for ~220 nearly-unique values.
    assert CORRECT_REPAIR["shipment_id"] == frozenset({"cast_to_text", "recast_int"})
    assert "cast_category" not in CORRECT_REPAIR["shipment_id"]


def test_delivered_at_repair_options_handle_the_two_malformed_rows_differently():
    raw = generate_shipments()
    keep_nat = next(o for o in DELIVERED_AT_ISSUE.options if o.key == "coerce_keep_nat").apply(raw.frame)
    then_drop = next(o for o in DELIVERED_AT_ISSUE.options if o.key == "coerce_then_drop").apply(raw.frame)
    wrong_format = next(o for o in DELIVERED_AT_ISSUE.options if o.key == "wrong_format").apply(raw.frame)

    assert len(keep_nat) == 222 and int(keep_nat["delivered_at"].isna().sum()) == 2
    assert len(then_drop) == 220
    assert int(wrong_format["delivered_at"].isna().sum()) == 222  # the format doesn't match any real row


def test_malformed_count_reflects_the_real_chosen_repair_not_a_fixed_constant():
    # coerce_then_drop removes every trace of the malformed rows (0, not
    # 2); wrong_format turns every row into NaT - both real, honest
    # consequences of that specific choice.
    kept = apply_round1({"shipment_id": "cast_to_text", "delivered_at": "coerce_keep_nat"})
    dropped = apply_round1({"shipment_id": "cast_to_text", "delivered_at": "coerce_then_drop"})
    wrong_format = apply_round1({"shipment_id": "cast_to_text", "delivered_at": "wrong_format"})
    assert malformed_count(kept) == 2
    assert malformed_count(dropped) == 0
    assert malformed_count(wrong_format) == 222


def test_duration_repair_options_produce_three_different_breach_rates():
    correct = breach_rate(apply_round2(GOOD_ROUND1, {"duration_minutes": "fix_store_d_only"}))
    over_corrected = breach_rate(apply_round2(GOOD_ROUND1, {"duration_minutes": "fix_every_row"}))
    denied = breach_rate(apply_round2(GOOD_ROUND1, {"duration_minutes": "recast_float"}))

    assert correct == pytest.approx(22 / 180)
    assert denied == pytest.approx(53 / 180)  # unchanged - denies the problem
    assert over_corrected < correct  # breaks the majority to fix the minority


def test_duration_recast_float_is_a_real_no_op_and_keeps_the_original_description():
    # recast_float doesn't actually change anything (already float64) -
    # its schema description must stay the original migration note, not
    # flip to "fixed" for a fix that never happened.
    denied = apply_round2(GOOD_ROUND1, {"duration_minutes": "recast_float"})
    duration_schema = next(c for c in denied.schema.columns if c.name == "duration_minutes")
    assert duration_schema.description_key == "lesson.l06.schema.duration_minutes.description"


def test_round1_and_round2_issue_groupings_cover_all_three_real_problems():
    columns = {issue.column for issue in ROUND1_ISSUES} | {issue.column for issue in ROUND2_ISSUES}
    assert columns == {"shipment_id", "delivered_at", "duration_minutes"}
    assert set(CORRECT_REPAIR) == columns


def test_mastery_export_has_the_two_real_fixes_and_two_real_non_fixes():
    mastery = generate_mastery_export()
    assert set(mastery.frame.columns) == {"store_id", "revenue", "promo_code", "quantity"}
    assert MASTERY_CORRECT == frozenset({"store_id", "revenue"})
    assert mastery.frame["store_id"].dtype == "int64"  # looks fine, is an identifier
    assert not pd.api.types.is_numeric_dtype(mastery.frame["revenue"])  # looks wrong, is cleanly parseable


def test_safe_columns_correct_answer_excludes_duration_minutes_entirely():
    # duration_minutes is deliberately not offered as a prediction
    # candidate at all - nothing discoverable yet contradicts it at that
    # point, so it can't appear in either the correct or incorrect set.
    assert "duration_minutes" not in SAFE_COLUMNS_CORRECT
    assert SAFE_COLUMNS_CORRECT == frozenset({"item_count"})
