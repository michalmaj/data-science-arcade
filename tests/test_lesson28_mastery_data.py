from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l28_chart_crime_lab.mastery_data import (
    fair_complaint_rate,
    fair_rate_minimum_quarter_number,
    flawed_complaint_rate,
    flawed_rate_minimum_quarter_number,
    generate_complaints_data,
    rate_minimum_quarter_mirror_code,
)


def test_dataset_matches_its_own_schema():
    dtesting.assert_matches_schema(generate_complaints_data())


def test_fair_and_flawed_rates_disagree_on_which_quarter_is_lowest():
    dataset = generate_complaints_data()
    assert fair_rate_minimum_quarter_number(dataset) == 3.0  # Q3
    assert flawed_rate_minimum_quarter_number(dataset) == 4.0  # Q4


def test_fair_rate_is_meaningfully_larger_than_the_flawed_one():
    dataset = generate_complaints_data()
    for quarter in ("Q1", "Q2", "Q3", "Q4"):
        fair = fair_complaint_rate(dataset, quarter)
        flawed = flawed_complaint_rate(dataset, quarter)
        assert fair > 0.005
        assert flawed < 0.001
        assert fair > flawed * 10


def test_the_flawed_denominator_is_fixed_every_quarter():
    dataset = generate_complaints_data()
    assert dataset.frame["lifetime_customers"].nunique() == 1


def test_rate_minimum_quarter_mirror_code_matches_both_real_minimums_exactly():
    dataset = generate_complaints_data()
    namespace_fair = {"complaints": dataset.frame}
    exec(rate_minimum_quarter_mirror_code("orders_this_quarter", "fm"), namespace_fair)
    assert namespace_fair["fm"] == fair_rate_minimum_quarter_number(dataset)

    namespace_flawed = {"complaints": dataset.frame}
    exec(rate_minimum_quarter_mirror_code("lifetime_customers", "flm"), namespace_flawed)
    assert namespace_flawed["flm"] == flawed_rate_minimum_quarter_number(dataset)
