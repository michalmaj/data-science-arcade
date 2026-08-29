from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l27_causality_courtroom.case_data import (
    compute_correlation,
    generate_resolution_satisfaction_data,
    generate_tool_spend_data,
    generate_training_performance_data,
)


def test_all_three_datasets_match_their_schema():
    for dataset in (generate_tool_spend_data(), generate_resolution_satisfaction_data(), generate_training_performance_data()):
        dtesting.assert_matches_schema(dataset)


def test_tool_use_and_impulse_spend_are_strongly_negatively_correlated():
    dataset = generate_tool_spend_data()
    corr = compute_correlation(dataset, "tool_used", "impulse_spend")
    assert corr < -0.7


def test_fast_resolution_and_satisfaction_are_strongly_correlated():
    dataset = generate_resolution_satisfaction_data()
    corr = compute_correlation(dataset, "resolved_under_1hr", "satisfaction_score")
    assert corr > 0.7


def test_training_and_performance_are_strongly_correlated():
    dataset = generate_training_performance_data()
    corr = compute_correlation(dataset, "completed_training", "performance_score")
    assert corr > 0.7


def test_tool_users_actually_spend_much_less_on_impulse_purchases():
    dataset = generate_tool_spend_data()
    frame = dataset.frame
    used = frame[frame["tool_used"]]["impulse_spend"].mean()
    not_used = frame[~frame["tool_used"]]["impulse_spend"].mean()
    assert used < not_used * 0.8
