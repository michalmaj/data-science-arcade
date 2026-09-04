import pandas as pd
import pytest

from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import (
    DELIVERED_AT_ISSUE,
    DURATION_ISSUE,
    MASTERY_CORRECT,
    ROUND1_ISSUES,
    ROUND2_ISSUES,
    SAFE_COLUMNS_CORRECT,
    SHIPMENT_ID_ISSUE,
    breach_rate,
    generate_mastery_export,
    generate_shipments,
    generate_shipments_after_round1,
    last_month_breach_rate,
    malformed_count,
)


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


def test_round1_repair_produces_the_correct_dtypes_and_malformed_count():
    repaired = generate_shipments_after_round1()
    assert repaired.frame["shipment_id"].dtype == "string"
    assert str(repaired.frame["delivered_at"].dtype).startswith("datetime64")
    assert malformed_count(repaired) == 2


def test_this_months_shipments_total_180_across_four_stores():
    repaired = generate_shipments_after_round1()
    this_month = repaired.frame[repaired.frame["delivered_at"].dt.strftime("%Y-%m") == "2026-09"]
    assert len(this_month) == 180
    counts = this_month["store"].value_counts().to_dict()
    assert counts == {"A": 60, "B": 60, "C": 24, "D": 36}


def test_naive_breach_rate_matches_the_hand_verified_29_percent():
    repaired = generate_shipments_after_round1()
    assert breach_rate(repaired, corrected=False) == pytest.approx(53 / 180)


def test_corrected_breach_rate_matches_the_hand_verified_12_percent():
    repaired = generate_shipments_after_round1()
    assert breach_rate(repaired, corrected=True) == pytest.approx(22 / 180)


def test_last_month_baseline_is_close_to_this_months_true_rate():
    repaired = generate_shipments_after_round1()
    baseline = last_month_breach_rate(repaired)
    assert baseline == pytest.approx(5 / 40)
    # The whole point of this baseline: nothing about delivery speed
    # really changed month over month - only how this month's numbers get
    # misread does.
    assert abs(baseline - breach_rate(repaired, corrected=True)) < 0.02


@pytest.mark.parametrize("issue", [SHIPMENT_ID_ISSUE, DELIVERED_AT_ISSUE, DURATION_ISSUE])
def test_every_issue_has_at_least_three_real_options(issue):
    assert len(issue.options) >= 3


def test_shipment_id_repair_options_produce_three_different_real_dtypes():
    raw = generate_shipments()
    dtypes = {option.key: option.apply(raw.frame)["shipment_id"].dtype.name for option in SHIPMENT_ID_ISSUE.options}
    assert dtypes["cast_to_text"] == "string"
    assert dtypes["recast_int"] == "int64"
    assert dtypes["cast_category"] == "category"


def test_delivered_at_repair_options_handle_the_two_malformed_rows_differently():
    raw = generate_shipments()
    keep_nat = next(o for o in DELIVERED_AT_ISSUE.options if o.key == "coerce_keep_nat").apply(raw.frame)
    then_drop = next(o for o in DELIVERED_AT_ISSUE.options if o.key == "coerce_then_drop").apply(raw.frame)
    wrong_format = next(o for o in DELIVERED_AT_ISSUE.options if o.key == "wrong_format").apply(raw.frame)

    assert len(keep_nat) == 222 and int(keep_nat["delivered_at"].isna().sum()) == 2
    assert len(then_drop) == 220
    assert int(wrong_format["delivered_at"].isna().sum()) == 222  # the format doesn't match any real row


def test_duration_repair_options_produce_three_different_breach_rates():
    repaired = generate_shipments_after_round1()
    from data_science_arcade.data_engine.dataset import Dataset
    from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import ROUND2_FIXED_SCHEMA

    def _rate_after(option_key: str) -> float:
        option = next(o for o in DURATION_ISSUE.options if o.key == option_key)
        fixed_frame = option.apply(repaired.frame)
        fixed = Dataset(name="shipments", frame=fixed_frame, schema=ROUND2_FIXED_SCHEMA, history=())
        return breach_rate(fixed, corrected=False)

    correct = _rate_after("fix_store_d_only")
    over_corrected = _rate_after("fix_every_row")
    denied = _rate_after("recast_float")

    assert correct == pytest.approx(22 / 180)
    assert denied == pytest.approx(53 / 180)  # unchanged - denies the problem
    assert over_corrected < correct  # breaks the majority to fix the minority


def test_round1_and_round2_issue_groupings_cover_all_three_real_problems():
    columns = {issue.column for issue in ROUND1_ISSUES} | {issue.column for issue in ROUND2_ISSUES}
    assert columns == {"shipment_id", "delivered_at", "duration_minutes"}


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
