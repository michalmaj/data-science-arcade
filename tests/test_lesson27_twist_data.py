from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l27_causality_courtroom.twist_data import conversion_rate, generate_checkout_beta_data, group_gap_mirror_code


def test_generated_data_matches_its_schema():
    dataset = generate_checkout_beta_data()
    dtesting.assert_matches_schema(dataset)


def test_the_observational_gap_looks_large():
    dataset = generate_checkout_beta_data()
    gap = conversion_rate(dataset, "beta_opt_in") - conversion_rate(dataset, "non_beta")
    assert round(gap, 2) == 0.25


def test_the_randomized_estimate_is_much_smaller_than_the_observational_gap():
    dataset = generate_checkout_beta_data()
    observational_gap = conversion_rate(dataset, "beta_opt_in") - conversion_rate(dataset, "non_beta")
    randomized_estimate = conversion_rate(dataset, "randomized_treatment") - conversion_rate(dataset, "randomized_control")
    assert round(randomized_estimate, 2) == 0.02
    assert randomized_estimate < observational_gap / 5


def test_group_gap_mirror_code_matches_both_real_gaps_exactly():
    dataset = generate_checkout_beta_data()
    namespace = {"checkout_beta": dataset.frame}

    observational_expected = conversion_rate(dataset, "beta_opt_in") - conversion_rate(dataset, "non_beta")
    exec(group_gap_mirror_code("checkout_beta", "beta_opt_in", "non_beta", "gap"), namespace)
    assert namespace["gap"] == observational_expected

    randomized_expected = conversion_rate(dataset, "randomized_treatment") - conversion_rate(dataset, "randomized_control")
    exec(group_gap_mirror_code("checkout_beta", "randomized_treatment", "randomized_control", "gap"), namespace)
    assert namespace["gap"] == randomized_expected
