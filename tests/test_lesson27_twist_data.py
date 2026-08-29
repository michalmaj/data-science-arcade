from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l27_causality_courtroom.twist_data import conversion_rate, generate_checkout_beta_data


def test_generated_data_matches_its_schema():
    dataset = generate_checkout_beta_data()
    dtesting.assert_matches_schema(dataset)


def test_the_observational_gap_looks_large():
    dataset = generate_checkout_beta_data()
    gap = conversion_rate(dataset, "beta_opt_in") - conversion_rate(dataset, "non_beta")
    assert round(gap, 2) == 0.25


def test_the_randomized_true_effect_is_much_smaller_than_the_observational_gap():
    dataset = generate_checkout_beta_data()
    observational_gap = conversion_rate(dataset, "beta_opt_in") - conversion_rate(dataset, "non_beta")
    true_effect = conversion_rate(dataset, "randomized_treatment") - conversion_rate(dataset, "randomized_control")
    assert round(true_effect, 2) == 0.02
    assert true_effect < observational_gap / 5
