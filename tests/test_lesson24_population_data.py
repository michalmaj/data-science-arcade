from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.survey import ChannelOption, WordingOption
from data_science_arcade.lessons.l24_survey_bureau.population_data import generate_population_data, simulate_survey, true_population_mean

NEUTRAL = WordingOption("neutral", "x", bias=0.0)
LEADING = WordingOption("leading", "x", bias=0.15)
BROAD_EMAIL = ChannelOption("broad_email", "x", reach_query=None)
IN_APP_POPUP = ChannelOption("in_app_popup", "x", reach_query="still_active == True")
POWER_USER_PANEL = ChannelOption("power_user_panel", "x", reach_query="is_power_user == True")


def test_generated_data_matches_its_schema():
    dataset = generate_population_data()
    dtesting.assert_matches_schema(dataset)


def test_population_size_and_true_mean():
    dataset = generate_population_data()
    assert len(dataset.frame) == 300
    assert round(true_population_mean(dataset), 4) == 0.5850


def test_broad_email_reaches_every_segment_including_churned_critics():
    dataset = generate_population_data()
    reached = dataset.frame.query(BROAD_EMAIL.reach_query) if BROAD_EMAIL.reach_query else dataset.frame
    assert len(reached[reached["segment"] == "vocal_critic"]) == 45


def test_in_app_popup_cannot_reach_churned_critics():
    dataset = generate_population_data()
    reached = dataset.frame.query(IN_APP_POPUP.reach_query)
    assert len(reached[reached["segment"] == "vocal_critic"]) == 18  # the 27 who already quit are excluded


def test_power_user_panel_cannot_reach_any_critic_at_all():
    dataset = generate_population_data()
    reached = dataset.frame.query(POWER_USER_PANEL.reach_query)
    assert len(reached[reached["segment"] == "vocal_critic"]) == 0


def test_broad_email_with_neutral_wording_is_the_defensible_baseline():
    dataset = generate_population_data()
    count, mean_value = simulate_survey(dataset, BROAD_EMAIL, NEUTRAL)
    assert count == 102
    assert round(mean_value, 4) == 0.5294


def test_in_app_popup_skews_the_recorded_average_upward_versus_broad_email():
    dataset = generate_population_data()
    _, broad_mean = simulate_survey(dataset, BROAD_EMAIL, NEUTRAL)
    _, inapp_mean = simulate_survey(dataset, IN_APP_POPUP, NEUTRAL)
    assert inapp_mean > broad_mean


def test_power_user_panel_skews_the_recorded_average_upward_even_more():
    dataset = generate_population_data()
    _, inapp_mean = simulate_survey(dataset, IN_APP_POPUP, NEUTRAL)
    _, panel_mean = simulate_survey(dataset, POWER_USER_PANEL, NEUTRAL)
    assert panel_mean > inapp_mean


def test_leading_wording_inflates_the_result_for_every_channel():
    dataset = generate_population_data()
    for channel in (BROAD_EMAIL, IN_APP_POPUP, POWER_USER_PANEL):
        _, neutral_mean = simulate_survey(dataset, channel, NEUTRAL)
        _, leading_mean = simulate_survey(dataset, channel, LEADING)
        assert leading_mean > neutral_mean
