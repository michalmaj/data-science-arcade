from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l28_chart_crime_lab.chart_data import (
    fair_return_rate,
    flawed_return_rate,
    generate_active_users_data,
    generate_returns_data,
    generate_satisfaction_data,
)


def test_all_three_datasets_match_their_schema():
    for dataset in (generate_satisfaction_data(), generate_active_users_data(), generate_returns_data()):
        dtesting.assert_matches_schema(dataset)


def test_satisfaction_shows_a_real_modest_improvement():
    dataset = generate_satisfaction_data()
    scores = list(dataset.frame["satisfaction_score"])
    assert scores == [72.0, 73.0, 74.0, 75.0]


def test_active_users_decline_through_most_of_the_year_then_recover():
    dataset = generate_active_users_data()
    frame = dataset.frame.sort_values("month_index")
    values = list(frame["active_users"])
    assert values[9] < values[0]  # October is well below January - a real decline
    assert values[-1] > values[-2]  # December is above November - a real late recovery


def test_fair_return_rate_is_meaningfully_larger_than_the_flawed_one():
    dataset = generate_returns_data()
    for quarter in ("Q1", "Q2", "Q3", "Q4"):
        fair = fair_return_rate(dataset, quarter)
        flawed = flawed_return_rate(dataset, quarter)
        assert fair > 0.10
        assert flawed < 0.01
        assert fair > flawed * 10
