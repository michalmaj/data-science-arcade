import math

import pandas as pd
import pytest

from data_science_arcade.lessons.l07_missing_data_clinic.twist_data import (
    CORRECT_TREATMENT,
    MASTERY_CORRECT,
    PICK_MINUTES_ISSUE,
    ROUND1_ISSUES,
    ROUND2_ISSUES,
    SLA_MINUTES,
    STORES,
    apply_round1,
    apply_round2,
    complete_case_rate,
    generate_mastery_export,
    generate_orders,
    missing_rate_by,
    overall_missing_rate,
    sla_bounds,
    _hidden_true_sla_rate,
)

GOOD_ROUND1 = {"cold_pack_temp_c": "leave_as_missing", "promo_code": "recode_no_promo"}


def test_raw_export_has_the_hand_verified_row_count_and_missing_rate():
    raw = generate_orders()
    assert len(raw.frame) == 400
    assert overall_missing_rate(raw) == pytest.approx(0.14)
    assert int(raw.frame["pick_minutes"].isna().sum()) == 56


def test_missing_rate_by_scanner_and_hour_matches_the_hand_verified_table():
    raw = generate_orders()
    by_scanner = missing_rate_by(raw, "scanner_type")
    by_hour = missing_rate_by(raw, "hour_bucket")
    assert by_scanner["legacy"] == pytest.approx(44 / 150)
    assert by_scanner["current"] == pytest.approx(12 / 250)
    assert by_hour["peak"] == pytest.approx(36 / 160)
    assert by_hour["offpeak"] == pytest.approx(20 / 240)


def test_missing_rate_by_store_and_basket_size_is_genuinely_flat():
    raw = generate_orders()
    by_store = missing_rate_by(raw, "store")
    by_basket = missing_rate_by(raw, "basket_size")
    assert set(by_store) == set(STORES)
    for rate in by_store.values():
        assert rate == pytest.approx(0.14)
    for rate in by_basket.values():
        assert rate == pytest.approx(0.14)


def test_no_observed_pick_minutes_value_sits_on_the_wrong_side_of_the_sla_threshold():
    # This is what guarantees (not coincidentally) that a global median
    # fill lands exactly on the upper sensitivity bound - see the module
    # docstring on STORES.
    raw = generate_orders()
    observed = raw.frame[raw.frame["pick_minutes"].notna()]
    values = set(observed["pick_minutes"].unique())
    assert values == {8.0, 16.0}
    assert all(v < SLA_MINUTES for v in values if v == 8.0)
    assert all(v > SLA_MINUTES for v in values if v == 16.0)


def test_cold_pack_temp_c_is_missing_exactly_when_contains_chilled_is_false():
    raw = generate_orders()
    mismatch = (raw.frame["contains_chilled"] != raw.frame["cold_pack_temp_c"].notna()).sum()
    assert mismatch == 0
    assert int(raw.frame["contains_chilled"].sum()) == 100


def test_promo_code_is_used_on_exactly_120_of_400_orders():
    raw = generate_orders()
    assert int(raw.frame["promo_code"].notna().sum()) == 120


def test_complete_case_rate_matches_the_hand_verified_90_percent():
    dataset = apply_round1(GOOD_ROUND1)
    assert complete_case_rate(dataset) == pytest.approx(310 / 344)


def test_sla_bounds_match_the_hand_verified_range_when_preserved():
    dataset = apply_round2(GOOD_ROUND1, {"pick_minutes": "preserve_and_report"})
    lower, upper = sla_bounds(dataset)
    assert lower == pytest.approx(310 / 400)
    assert upper == pytest.approx(366 / 400)


def test_sla_bounds_collapse_to_a_single_point_once_every_gap_is_filled():
    for option_key in ("fill_global_median", "fill_group_median", "fill_zero"):
        dataset = apply_round2(GOOD_ROUND1, {"pick_minutes": option_key})
        lower, upper = sla_bounds(dataset)
        assert lower == pytest.approx(upper), option_key


def test_global_median_fill_lands_exactly_on_the_upper_bound():
    dataset = apply_round2(GOOD_ROUND1, {"pick_minutes": "fill_global_median"})
    lower, upper = sla_bounds(dataset)
    assert lower == pytest.approx(upper) == pytest.approx(366 / 400)


def test_zero_fill_produces_the_same_rate_as_global_median_but_visibly_impossible_values():
    dataset = apply_round2(GOOD_ROUND1, {"pick_minutes": "fill_zero"})
    lower, upper = sla_bounds(dataset)
    assert lower == pytest.approx(upper) == pytest.approx(366 / 400)
    assert (dataset.frame["pick_minutes"] == 0.0).sum() == 56


def test_group_median_fill_matches_the_hand_verified_84_percent():
    dataset = apply_round2(GOOD_ROUND1, {"pick_minutes": "fill_group_median"})
    lower, upper = sla_bounds(dataset)
    assert lower == pytest.approx(upper) == pytest.approx(336 / 400)


def test_hidden_true_rate_falls_inside_the_honest_range_and_below_target():
    true_rate = _hidden_true_sla_rate()
    assert true_rate == pytest.approx(0.8275)
    assert 310 / 400 < true_rate < 366 / 400
    assert true_rate < 0.85


def test_round1_replay_never_touches_an_unresolved_columns_own_schema():
    partial = apply_round1({"cold_pack_temp_c": "leave_as_missing"})
    promo_schema = next(c for c in partial.schema.columns if c.name == "promo_code")
    assert promo_schema.description_key == "lesson.l07.schema.promo_code.description"
    assert promo_schema.nullable is True


def test_cold_pack_repair_options_produce_the_expected_real_consequences():
    raw = generate_orders()
    leave = next(o for o in PICK_MINUTES_ISSUE.options if o.key == "preserve_and_report")
    assert leave.apply(raw.frame)["pick_minutes"].isna().sum() == 56  # sanity: identity transform

    from data_science_arcade.lessons.l07_missing_data_clinic.twist_data import COLD_PACK_ISSUE

    dropped = next(o for o in COLD_PACK_ISSUE.options if o.key == "drop_missing_cold_pack").apply(raw.frame)
    assert len(dropped) == 100  # only the 100 chilled orders remain
    fabricated_zero = next(o for o in COLD_PACK_ISSUE.options if o.key == "fill_zero_c").apply(raw.frame)
    assert fabricated_zero["cold_pack_temp_c"].isna().sum() == 0
    assert (fabricated_zero.loc[raw.frame["contains_chilled"] == False, "cold_pack_temp_c"] == 0.0).all()  # noqa: E712


def test_promo_code_repair_options_produce_the_expected_real_consequences():
    from data_science_arcade.lessons.l07_missing_data_clinic.twist_data import PROMO_CODE_ISSUE

    raw = generate_orders()
    recoded = next(o for o in PROMO_CODE_ISSUE.options if o.key == "recode_no_promo").apply(raw.frame)
    assert recoded["promo_code"].isna().sum() == 0
    assert (recoded["promo_code"] == "NO_PROMO").sum() == 280
    dropped = next(o for o in PROMO_CODE_ISSUE.options if o.key == "drop_missing_promo").apply(raw.frame)
    assert len(dropped) == 120


def test_correct_treatment_has_exactly_one_answer_per_column():
    assert CORRECT_TREATMENT == {
        "cold_pack_temp_c": frozenset({"leave_as_missing"}),
        "promo_code": frozenset({"recode_no_promo"}),
        "pick_minutes": frozenset({"preserve_and_report"}),
    }


def test_round1_and_round2_issue_groupings_cover_all_three_real_problems():
    columns = {issue.column for issue in ROUND1_ISSUES} | {issue.column for issue in ROUND2_ISSUES}
    assert columns == {"cold_pack_temp_c", "promo_code", "pick_minutes"}
    assert set(CORRECT_TREATMENT) == columns


@pytest.mark.parametrize("issue", [*ROUND1_ISSUES, *ROUND2_ISSUES])
def test_every_issue_has_at_least_three_real_options(issue):
    assert len(issue.options) >= 3


def test_mastery_export_has_the_one_real_fix_and_three_real_non_fixes():
    mastery = generate_mastery_export()
    assert set(mastery.frame.columns) == {"sku", "restock_date", "supplier_lead_days", "warehouse_zone", "unit_cost"}
    assert MASTERY_CORRECT == frozenset({"supplier_lead_days"})
    assert mastery.frame["restock_date"].isna().sum() == 3  # structural, not a fix candidate
    assert mastery.frame["warehouse_zone"].isna().sum() == 0  # fully populated
    assert mastery.frame["supplier_lead_days"].isna().sum() == 1  # the one genuine gap
