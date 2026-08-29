import pytest

from data_science_arcade.lessons.l28_chart_crime_lab.requests import CHART_REQUESTS, CORRECT_OPTION_BY_REQUEST


def test_all_three_requests_are_present():
    assert {request.key for request in CHART_REQUESTS} == {
        "satisfaction_score_claim",
        "active_users_claim",
        "returns_rate_claim",
    }


def test_every_request_has_a_correct_option_recorded():
    assert set(CORRECT_OPTION_BY_REQUEST) == {request.key for request in CHART_REQUESTS}


@pytest.mark.parametrize("request_", list(CHART_REQUESTS))
def test_the_correct_option_is_among_the_offered_options(request_):
    correct = CORRECT_OPTION_BY_REQUEST[request_.key]
    assert correct in {option.key for option in request_.options}


def test_correct_option_position_varies_across_requests():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for request_ in CHART_REQUESTS:
        correct = CORRECT_OPTION_BY_REQUEST[request_.key]
        indexes.append(next(i for i, option in enumerate(request_.options) if option.key == correct))
    assert len(set(indexes)) > 1


def test_the_cherry_picked_options_actually_use_a_different_slice_than_the_full_year():
    request = next(r for r in CHART_REQUESTS if r.key == "active_users_claim")
    full_year = next(o for o in request.options if o.key == "full_year")
    last_two = next(o for o in request.options if o.key == "last_two_months")
    first_two = next(o for o in request.options if o.key == "first_two_months")

    assert full_year.categories is None  # falls back to the request's own full series
    assert last_two.categories == request.categories[-2:]
    assert last_two.values == request.values[-2:]
    assert first_two.categories == request.categories[:2]
    assert first_two.values == request.values[:2]


def test_the_cherry_picked_slices_tell_opposite_stories_from_the_same_real_data():
    request = next(r for r in CHART_REQUESTS if r.key == "active_users_claim")
    last_two = next(o for o in request.options if o.key == "last_two_months")
    first_two = next(o for o in request.options if o.key == "first_two_months")

    assert last_two.values[-1] > last_two.values[0]  # looks like growth
    assert first_two.values[-1] < first_two.values[0]  # looks like decline


def test_the_denominator_options_use_the_same_categories_but_different_values():
    request = next(r for r in CHART_REQUESTS if r.key == "returns_rate_claim")
    per_customers = next(o for o in request.options if o.key == "per_customers")
    per_units_sold = next(o for o in request.options if o.key == "per_units_sold")

    assert per_customers.categories is None
    assert per_units_sold.categories == request.categories
    assert per_units_sold.values != request.values
