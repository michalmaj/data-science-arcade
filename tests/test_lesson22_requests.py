from data_science_arcade.lessons.l22_cohort_observatory.cohort_data import generate_cohort_data, retention_rate
from data_science_arcade.lessons.l22_cohort_observatory.requests import COHORT_REQUESTS, CORRECT_OPTION_BY_REQUEST


def test_exactly_one_real_decision():
    """The three predecessor requests all tested the identical same-age-
    vs-mismatched-age competency under different cohort-pair dressings -
    reduced to one real decision, not three redundant ones."""
    assert {request.key for request in COHORT_REQUESTS} == {"may_retention_comparison"}


def test_every_request_has_a_correct_option_recorded():
    assert set(CORRECT_OPTION_BY_REQUEST) == {request.key for request in COHORT_REQUESTS}


def test_the_correct_option_is_among_the_offered_options():
    request = COHORT_REQUESTS[0]
    correct = CORRECT_OPTION_BY_REQUEST[request.key]
    assert correct in {option.key for option in request.options}


def test_the_request_offers_exactly_two_options():
    assert len(COHORT_REQUESTS[0].options) == 2


def test_the_same_month_option_actually_compares_the_same_month():
    request = COHORT_REQUESTS[0]
    same_month_option = next(option for option in request.options if option.key == "same_month_comparison")
    assert same_month_option.month_a == same_month_option.month_b == 1


def test_the_mismatched_option_is_retargeted_to_januarys_own_month_five():
    """Retargeted from an arbitrary jan/4 to jan/5 - January's own most-
    mature observed number, a more realistic and more tempting trap than
    an arbitrary mid-horizon pairing."""
    request = COHORT_REQUESTS[0]
    mismatched_option = next(option for option in request.options if option.key == "mismatched_month_comparison")
    assert mismatched_option.cohort_a == "may"
    assert mismatched_option.month_a == 1
    assert mismatched_option.cohort_b == "jan"
    assert mismatched_option.month_b == 5


def test_both_cells_the_request_points_at_are_real_observed_cells():
    dataset = generate_cohort_data()
    for option in COHORT_REQUESTS[0].options:
        retention_rate(dataset, option.cohort_a, option.month_a)  # raises if unobserved
        retention_rate(dataset, option.cohort_b, option.month_b)
