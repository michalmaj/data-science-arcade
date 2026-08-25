from data_science_arcade.lessons.l05_sampling_mission.twist_data import (
    DOMINANT_GROUP,
    apparent_satisfaction,
    generate_survey_responses,
    group_share_of_responses,
    unweighted_average_satisfaction,
)


def test_apparent_satisfaction_matches_the_engineered_rate():
    dataset = generate_survey_responses()
    assert apparent_satisfaction(dataset) == 0.82


def test_the_dominant_group_is_three_quarters_of_all_responses():
    dataset = generate_survey_responses()
    assert group_share_of_responses(dataset, DOMINANT_GROUP) == 0.75


def test_unweighted_average_is_lower_than_the_apparent_result():
    dataset = generate_survey_responses()
    assert round(unweighted_average_satisfaction(dataset), 2) == 0.67
    assert unweighted_average_satisfaction(dataset) < apparent_satisfaction(dataset)


def test_total_response_count_is_two_hundred():
    dataset = generate_survey_responses()
    assert len(dataset.frame) == 200
