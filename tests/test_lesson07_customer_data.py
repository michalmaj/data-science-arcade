from data_science_arcade.lessons.l07_missing_data_clinic.customer_data import (
    drop_rows_mean,
    generate_customers,
    mean_imputed_mean,
    median_imputed_mean,
    missing_count,
    present_count,
    segment_imputed_mean,
    true_population_mean,
)


def test_missingness_is_concentrated_entirely_in_the_at_risk_segment():
    dataset = generate_customers()
    frame = dataset.frame
    missing = frame[frame["engagement_score"].isna()]
    assert len(missing) == missing_count(dataset)
    assert set(missing["segment"]) == {"at_risk"}


def test_missing_and_present_counts():
    dataset = generate_customers()
    assert missing_count(dataset) == 15
    assert present_count(dataset) == 175
    assert len(dataset.frame) == 190


def test_drop_rows_and_mean_imputation_land_on_the_same_overall_mean():
    # A real, not-obvious property: filling NaNs with the mean of the
    # present values can't change the overall mean - only mean-imputation's
    # extra rows (variance-shrinking) differ from drop-rows.
    dataset = generate_customers()
    assert drop_rows_mean(dataset) == 68.0
    assert mean_imputed_mean(dataset) == 68.0


def test_median_imputation_gives_a_different_number_than_mean_imputation():
    dataset = generate_customers()
    assert round(median_imputed_mean(dataset), 1) == 68.9


def test_segment_aware_imputation_lands_closest_to_the_true_mean():
    dataset = generate_customers()
    true_mean = true_population_mean(dataset)
    segment_error = abs(segment_imputed_mean(dataset) - true_mean)
    drop_error = abs(drop_rows_mean(dataset) - true_mean)
    median_error = abs(median_imputed_mean(dataset) - true_mean)
    assert segment_error < drop_error
    assert segment_error < median_error


def test_true_population_mean_matches_the_engineered_value():
    dataset = generate_customers()
    assert round(true_population_mean(dataset), 1) == 64.2
