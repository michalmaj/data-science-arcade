from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l30_the_data_incident.incident_data import generate_incident_data, region_series
from data_science_arcade.lessons.l30_the_data_incident.promo_log_data import (
    generate_promo_log,
    raw_event_count,
    unique_redemption_count,
    weekly_redemption_counts,
)


def test_generated_log_matches_its_schema():
    dataset = generate_promo_log()
    dtesting.assert_matches_schema(dataset)


def test_true_unique_redemptions_are_3000_but_raw_rows_are_3450():
    dataset = generate_promo_log()
    assert unique_redemption_count(dataset) == 3000
    assert raw_event_count(dataset) == 3450


def test_weekly_join_preserves_one_row_per_week_no_fan_out():
    # The real cardinality check this pipeline exists to teach: a left
    # join of an already-per-week-aggregated log onto Finance's 8-week
    # revenue table must never produce more or fewer than 8 rows.
    dataset = generate_promo_log()
    weeks = tuple(range(1, 9))
    deduped = weekly_redemption_counts(dataset, "east", weeks, dedupe=True)
    raw = weekly_redemption_counts(dataset, "east", weeks, dedupe=False)
    assert len(deduped) == 8
    assert len(raw) == 8


def test_deduped_weekly_counts_are_zero_except_the_real_promo_week():
    dataset = generate_promo_log()
    weeks = tuple(range(1, 9))
    deduped = weekly_redemption_counts(dataset, "east", weeks, dedupe=True)
    assert deduped == (0, 0, 0, 0, 0, 0, 3000, 0)

    raw = weekly_redemption_counts(dataset, "east", weeks, dedupe=False)
    assert raw == (0, 0, 0, 0, 0, 0, 3450, 0)


def test_dedup_choice_does_not_change_the_qualitative_correlation_verdict():
    # Root-cause reasoning is deliberately isolated from the dedup choice
    # (spec correction #12): both a correct and a naive count are
    # dominated by the same single-week spike, so the correlation stays
    # effectively identical either way - only the cited redemption COUNT
    # should differ downstream, not the verdict.
    import pandas as pd

    incident = generate_incident_data()
    log = generate_promo_log()
    weeks = tuple(range(1, 9))
    revenue = pd.Series(region_series(incident, "east", "revenue"))

    deduped_corr = pd.Series(weekly_redemption_counts(log, "east", weeks, dedupe=True), dtype=float).corr(revenue)
    raw_corr = pd.Series(weekly_redemption_counts(log, "east", weeks, dedupe=False), dtype=float).corr(revenue)

    assert deduped_corr > 0.99
    assert raw_corr > 0.99
    assert abs(deduped_corr - raw_corr) < 0.001
