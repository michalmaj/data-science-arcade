import pytest

from data_science_arcade.lessons.l10_validation_gate.checks import CORRECT_RULE_BY_CHECK, VALIDATION_CHECKS


def test_every_check_has_a_correct_rule_recorded():
    assert {check.key for check in VALIDATION_CHECKS} == set(CORRECT_RULE_BY_CHECK)


def test_all_six_spec_listed_checks_are_present():
    assert {check.key for check in VALIDATION_CHECKS} == {
        "uniqueness",
        "allowed_range",
        "null_limit",
        "referential_integrity",
        "freshness",
        "category_validity",
    }


@pytest.mark.parametrize("check", list(VALIDATION_CHECKS))
def test_the_correct_rule_is_among_the_offered_options(check):
    correct = CORRECT_RULE_BY_CHECK[check.key]
    assert correct in {option.key for option in check.options}


@pytest.mark.parametrize("check", list(VALIDATION_CHECKS))
def test_every_check_has_at_least_two_options(check):
    assert len(check.options) >= 2
