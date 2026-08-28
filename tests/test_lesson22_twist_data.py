from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l22_cohort_observatory.cohort_data import generate_cohort_data, retention_rate
from data_science_arcade.lessons.l22_cohort_observatory.twist_data import generate_november_cohort_data, november_retention_rate


def test_generated_data_matches_its_schema():
    dataset = generate_november_cohort_data()
    dtesting.assert_matches_schema(dataset)


def test_november_looked_better_than_january_at_month_one():
    november = generate_november_cohort_data()
    january = generate_cohort_data()
    assert november_retention_rate(november, 1) == 0.75
    assert retention_rate(january, "jan", 1) == 0.68
    assert november_retention_rate(november, 1) > retention_rate(january, "jan", 1)


def test_november_ended_up_worse_than_january_by_month_five():
    november = generate_november_cohort_data()
    january = generate_cohort_data()
    assert november_retention_rate(november, 5) == 0.38
    assert retention_rate(january, "jan", 5) == 0.46
    assert november_retention_rate(november, 5) < retention_rate(january, "jan", 5)
