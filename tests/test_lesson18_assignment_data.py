import pytest

from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l18_randomization_control_room.assignment_data import (
    average_tenure,
    covariate_rate,
    generate_assignment_data,
    group_size,
    relative_imbalance,
)

CORRECT_RULE_BY_EXPERIMENT = {
    "checkout_redesign": "order_alternation",
    "loyalty_discount_test": "id_parity",
    "notification_frequency_test": "signup_week",
}
ALL_RULES = ("order_alternation", "id_parity", "signup_week")


def test_generated_data_matches_its_schema():
    dataset = generate_assignment_data()
    dtesting.assert_matches_schema(dataset)


@pytest.mark.parametrize("relative_imbalance_case", [(100, 100, False), (100, 115, False), (100, 140, True), (0, 0, False), (0, 5, True)])
def test_relative_imbalance_flags_a_large_relative_gap(relative_imbalance_case):
    before, after, expected = relative_imbalance_case
    assert relative_imbalance(before, after) == expected


@pytest.mark.parametrize("experiment_key,correct_rule", list(CORRECT_RULE_BY_EXPERIMENT.items()))
def test_only_the_correct_rule_is_balanced_on_every_check(experiment_key, correct_rule):
    dataset = generate_assignment_data()
    for rule_key in ALL_RULES:
        t_size = group_size(dataset, experiment_key, rule_key, "treatment")
        c_size = group_size(dataset, experiment_key, rule_key, "control")
        t_cov = covariate_rate(dataset, experiment_key, rule_key, "treatment")
        c_cov = covariate_rate(dataset, experiment_key, rule_key, "control")
        t_tenure = average_tenure(dataset, experiment_key, rule_key, "treatment")
        c_tenure = average_tenure(dataset, experiment_key, rule_key, "control")
        any_flagged = (
            relative_imbalance(t_size, c_size) or relative_imbalance(t_cov, c_cov) or relative_imbalance(t_tenure, c_tenure)
        )
        if rule_key == correct_rule:
            assert any_flagged is False, f"{experiment_key}/{rule_key} should be balanced on every check"
        else:
            assert any_flagged is True, f"{experiment_key}/{rule_key} should be flawed on at least one check"
