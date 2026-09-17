from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l27_causality_courtroom.case_data import (
    compute_correlation,
    compute_group_mean_difference,
    correlation_mirror_code,
    generate_resolution_satisfaction_data,
    generate_tool_spend_data,
    generate_training_performance_data,
    group_mean_difference_mirror_code,
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


def test_group_mean_difference_is_real_and_signed_never_absolute_valued():
    tool_spend_diff = compute_group_mean_difference(generate_tool_spend_data(), "tool_used", "impulse_spend")
    resolution_diff = compute_group_mean_difference(generate_resolution_satisfaction_data(), "resolved_under_1hr", "satisfaction_score")
    training_diff = compute_group_mean_difference(generate_training_performance_data(), "completed_training", "performance_score")
    assert round(tool_spend_diff, 2) == -20.0
    assert round(resolution_diff, 2) == 22.4
    assert round(training_diff, 2) == 17.6


def test_group_mean_difference_mirror_code_matches_the_real_computation_exactly():
    cases = (
        ("tool_spend", "tool_used", "impulse_spend", generate_tool_spend_data()),
        ("resolution_satisfaction", "resolved_under_1hr", "satisfaction_score", generate_resolution_satisfaction_data()),
        ("training_performance", "completed_training", "performance_score", generate_training_performance_data()),
    )
    for dataset_var, predictor_col, outcome_col, dataset in cases:
        expected = compute_group_mean_difference(dataset, predictor_col, outcome_col)
        namespace = {dataset_var: dataset.frame}
        exec(group_mean_difference_mirror_code(dataset_var, predictor_col, outcome_col, "diff"), namespace)
        assert namespace["diff"] == expected


def test_correlation_mirror_code_matches_the_real_correlation_exactly():
    cases = (
        ("tool_spend_claim", "tool_spend", "tool_used", "impulse_spend", generate_tool_spend_data()),
        (
            "resolution_satisfaction_claim",
            "resolution_satisfaction",
            "resolved_under_1hr",
            "satisfaction_score",
            generate_resolution_satisfaction_data(),
        ),
        (
            "training_performance_claim",
            "training_performance",
            "completed_training",
            "performance_score",
            generate_training_performance_data(),
        ),
    )
    for request_key, dataset_var, column_a, column_b, dataset in cases:
        expected = compute_correlation(dataset, column_a, column_b)
        namespace = {dataset_var: dataset.frame}
        exec(correlation_mirror_code(request_key, "r"), namespace)
        assert namespace["r"] == expected
