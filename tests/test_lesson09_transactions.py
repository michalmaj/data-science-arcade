import pytest

from data_science_arcade.lessons.l09_outlier_patrol.transactions import CORRECT_ACTION_BY_CASE, OUTLIER_CASES


def test_every_case_has_a_correct_action_recorded():
    assert {case.key for case in OUTLIER_CASES} == set(CORRECT_ACTION_BY_CASE)


def test_the_five_spec_actions_are_each_the_correct_answer_exactly_once():
    assert sorted(CORRECT_ACTION_BY_CASE.values()) == ["cap", "exclude", "flag", "investigate", "retain"]


@pytest.mark.parametrize("case", list(OUTLIER_CASES))
def test_every_case_has_at_least_two_options(case):
    assert len(case.options) >= 2


@pytest.mark.parametrize("case", list(OUTLIER_CASES))
def test_the_correct_action_is_among_the_offered_options(case):
    correct = CORRECT_ACTION_BY_CASE[case.key]
    assert correct in {option.key for option in case.options}
