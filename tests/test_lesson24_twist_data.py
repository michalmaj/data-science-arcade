from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l24_survey_bureau.twist_data import blended_satisfaction_rate, generate_delivery_survey_data, satisfaction_rate


def test_generated_data_matches_its_schema():
    dataset = generate_delivery_survey_data()
    dtesting.assert_matches_schema(dataset)


def test_the_surveyed_group_looks_great_on_its_own():
    dataset = generate_delivery_survey_data()
    assert satisfaction_rate(dataset, "delivery_succeeded") == 0.88


def test_the_never_surveyed_group_is_much_worse():
    dataset = generate_delivery_survey_data()
    assert satisfaction_rate(dataset, "delivery_failed_or_delayed") == 0.20


def test_the_blended_rate_across_everyone_is_meaningfully_lower_than_the_headline():
    dataset = generate_delivery_survey_data()
    blended = blended_satisfaction_rate(dataset)
    assert round(blended, 4) == 0.7780
    assert blended < satisfaction_rate(dataset, "delivery_succeeded")
