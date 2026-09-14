import pandas as pd
import pytest

from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.cohort import ComparisonOption
from data_science_arcade.lessons.l22_cohort_observatory.cohort_data import (
    build_cohort_matrix,
    cell_retention_mirror_code,
    cohort_comparison_mirror_code,
    generate_cohort_data,
    latest_observed_month,
    latest_observed_month_mirror_code,
    retention_rate,
)


def test_generated_data_matches_its_schema():
    dataset = generate_cohort_data()
    dtesting.assert_matches_schema(dataset)


def test_every_cohorts_month_zero_is_trivially_full_retention():
    dataset = generate_cohort_data()
    for cohort in ("jan", "feb", "mar", "apr", "may"):
        assert retention_rate(dataset, cohort, 0) == 1.0


def test_may_looks_better_than_jan_at_the_same_age():
    dataset = generate_cohort_data()
    assert retention_rate(dataset, "may", 1) == 0.76
    assert retention_rate(dataset, "jan", 1) == 0.68


def test_april_is_the_real_worst_cohort_at_month_one():
    dataset = generate_cohort_data()
    month_one_rates = {cohort: retention_rate(dataset, cohort, 1) for cohort in ("jan", "feb", "mar", "apr", "may")}
    assert min(month_one_rates, key=month_one_rates.get) == "apr"


def test_build_cohort_matrix_produces_the_real_triangular_shape():
    dataset = generate_cohort_data()
    matrix = build_cohort_matrix(dataset)
    observed_counts = {row.key: row.months_observed for row in matrix.rows}
    assert observed_counts == {"jan": 6, "feb": 5, "mar": 4, "apr": 3, "may": 2}
    assert matrix.month_count == 6


@pytest.mark.parametrize("cohort,month", [("jan", 6), ("may", 2), ("apr", 3)])
def test_retention_rate_raises_for_an_unobserved_month(cohort, month):
    dataset = generate_cohort_data()
    with pytest.raises(IndexError):
        retention_rate(dataset, cohort, month)


def test_latest_observed_month_is_a_real_horizon_never_a_row_count():
    """May has two real rows (month 0 and month 1) - its latest observed
    month is 1, never 2 (which is what a naive row-count would read as, a
    real bug this lesson is careful not to reintroduce as student-facing
    text)."""
    dataset = generate_cohort_data()
    assert latest_observed_month(dataset, "may") == 1
    assert latest_observed_month(dataset, "jan") == 5


def _exec_code(code: str, namespace: dict) -> dict:
    exec(code, namespace)
    return namespace


def test_cell_retention_mirror_code_reconciles_to_the_real_verified_numbers():
    cohorts = generate_cohort_data().frame
    ns = _exec_code(cell_retention_mirror_code("may", 1, "x"), {"cohorts": cohorts, "pd": pd})
    assert ns["x"] == 0.76


def test_latest_observed_month_mirror_code_reconciles_to_the_real_function():
    cohorts = generate_cohort_data().frame
    ns = _exec_code(latest_observed_month_mirror_code("may", "x"), {"cohorts": cohorts, "pd": pd})
    assert ns["x"] == 1


def test_cohort_comparison_mirror_code_reconciles_to_the_real_two_cells():
    cohorts = generate_cohort_data().frame
    option = ComparisonOption("same_month_comparison", "k", "may", 1, "jan", 1)
    ns = _exec_code(cohort_comparison_mirror_code(option, "z"), {"cohorts": cohorts, "pd": pd})
    result = ns["z"].set_index("cohort_key")["retention"]
    assert result["may"] == 0.76
    assert result["jan"] == 0.68


def test_may_never_appears_in_any_month_five_slice_no_fillna():
    """The load-bearing missing-cell-semantics invariant: a pivoted view of
    the real data must show NaN for May's unobserved later months, never a
    0 - May genuinely has no row for month 5, and nothing anywhere should
    ever backfill one."""
    cohorts = generate_cohort_data().frame
    rates = cohorts.assign(retention=cohorts["active_count"] / cohorts["cohort_size"])
    pivot = rates.pivot(index="cohort_key", columns="month", values="retention")
    assert pd.isna(pivot.loc["may", 5])
    assert pd.isna(pivot.loc["may", 2])
    may_rows = cohorts[cohorts["cohort_key"] == "may"]
    assert 5 not in set(may_rows["month"])
