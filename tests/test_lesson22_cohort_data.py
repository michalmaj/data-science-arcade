import pytest

from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l22_cohort_observatory.cohort_data import build_cohort_matrix, generate_cohort_data, retention_rate


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
