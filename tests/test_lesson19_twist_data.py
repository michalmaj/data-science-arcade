from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.power import minimum_detectable_effect
from data_science_arcade.lessons.l19_power_plant.twist_data import conversion_rate, generate_banner_experiment_data, sample_size_per_group

MINIMUM_USEFUL_EFFECT_FOR_HOMEPAGE_CHANGES = 0.02


def test_generated_data_matches_its_schema():
    dataset = generate_banner_experiment_data()
    dtesting.assert_matches_schema(dataset)


def test_the_lift_is_real_and_statistically_detectable_but_not_worth_shipping():
    dataset = generate_banner_experiment_data()
    control = conversion_rate(dataset, "control")
    treatment = conversion_rate(dataset, "treatment")
    n = sample_size_per_group(dataset, "control")
    lift = treatment - control
    mde = minimum_detectable_effect(control, n)

    assert control == 0.18
    assert treatment == 0.19
    assert lift >= mde  # genuinely detectable at this sample size
    assert lift < MINIMUM_USEFUL_EFFECT_FOR_HOMEPAGE_CHANGES  # still too small to matter operationally


def test_sample_size_is_far_larger_than_any_guided_experiment_reaches():
    dataset = generate_banner_experiment_data()
    n = sample_size_per_group(dataset, "control")
    # Largest guided-play experiment tops out at 12 weeks x 2000/week/group.
    assert n > 12 * 2000
