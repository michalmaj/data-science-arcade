from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l28_chart_crime_lab.twist_data import generate_spend_signups_data, percent_change


def test_generated_data_matches_its_schema():
    dataset = generate_spend_signups_data()
    dtesting.assert_matches_schema(dataset)


def test_spend_grew_far_more_than_signups_in_their_own_terms():
    dataset = generate_spend_signups_data()
    spend_change = percent_change(dataset, "marketing_spend")
    signups_change = percent_change(dataset, "signups")
    assert round(spend_change, 2) == 0.85
    assert round(signups_change, 2) == 0.12
    assert spend_change > signups_change * 5
