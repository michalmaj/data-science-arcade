import pytest

from data_science_arcade.lessons.l19_power_plant.experiments import EXPERIMENTS, TOTAL_WEEKS, detectable_effect_for, weeks_needed_for_threshold


def test_all_three_experiments_are_present():
    assert {plan.key for plan in EXPERIMENTS} == {
        "checkout_redesign",
        "pricing_page_test",
        "loyalty_settings_test",
    }


@pytest.mark.parametrize(
    "experiment_key,expected_weeks",
    [
        ("checkout_redesign", 7),
        ("pricing_page_test", 6),
        ("loyalty_settings_test", 6),
    ],
)
def test_weeks_needed_matches_the_real_power_formula(experiment_key, expected_weeks):
    assert weeks_needed_for_threshold(experiment_key) == expected_weeks


def test_fully_satisfying_every_experiment_at_once_exceeds_the_budget():
    # The whole point of "limited traffic and limited time": there isn't
    # enough budget to hit every experiment's own bar simultaneously, so
    # the player has to make a real trade-off rather than just spending
    # evenly - verified from the real formula, not asserted by fiat.
    total_needed = sum(weeks_needed_for_threshold(plan.key) for plan in EXPERIMENTS)
    assert total_needed > TOTAL_WEEKS


@pytest.mark.parametrize("plan", list(EXPERIMENTS))
def test_more_weeks_never_makes_the_detectable_effect_worse(plan):
    fewer = detectable_effect_for(plan.key, 1)
    more = detectable_effect_for(plan.key, TOTAL_WEEKS)
    assert more < fewer
