from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l26_correlation_crime_scene.twist_data import average_ltv, generate_loyalty_ltv_data


def test_generated_data_matches_its_schema():
    dataset = generate_loyalty_ltv_data()
    dtesting.assert_matches_schema(dataset)


def test_the_observational_gap_looks_large():
    dataset = generate_loyalty_ltv_data()
    gap = average_ltv(dataset, "observational_member") - average_ltv(dataset, "observational_nonmember")
    assert gap == 160.0


def test_the_randomized_true_effect_is_much_smaller_than_the_observational_gap():
    dataset = generate_loyalty_ltv_data()
    observational_gap = average_ltv(dataset, "observational_member") - average_ltv(dataset, "observational_nonmember")
    true_effect = average_ltv(dataset, "randomized_treatment") - average_ltv(dataset, "randomized_control")
    assert true_effect == 15.0
    assert true_effect < observational_gap / 5
