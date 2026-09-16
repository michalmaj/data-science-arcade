import pandas as pd
import pytest

from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.survey import ChannelOption, WordingOption
from data_science_arcade.lessons.l24_survey_bureau.population_data import (
    RESPONSE_RATE_BY_SEGMENT,
    generate_population_data,
    response_rate_mirror_code,
    simulate_survey,
    survey_mean_mirror_code,
    survey_reach_count_mirror_code,
    true_population_mean,
)

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


def _exec_code(code: str, namespace: dict) -> dict:
    exec(code, namespace)
    return namespace


@pytest.mark.parametrize(
    "channel,wording,expected_pct",
    [
        (BROAD_EMAIL, NEUTRAL, 52.9),
        (BROAD_EMAIL, LEADING, 66.9),
        (IN_APP_POPUP, NEUTRAL, 62.0),
        (IN_APP_POPUP, LEADING, 75.7),
        (POWER_USER_PANEL, NEUTRAL, 83.8),
        (POWER_USER_PANEL, LEADING, 94.9),
    ],
)
def test_survey_mean_mirror_code_final_variable_matches_the_displayed_mean(channel, wording, expected_pct):
    """The P0 regression, matching L23's own established discipline: the
    FINAL {var_name} variable this snippet assigns must equal exactly the
    same mean_satisfaction simulate_survey (and the live result preview)
    actually produce - across all 6 real channel x wording combos."""
    customers = generate_population_data().frame
    ns = _exec_code(survey_mean_mirror_code(channel, wording, "x"), {"customers": customers, "pd": pd})
    assert round(ns["x"] * 100, 1) == expected_pct
    _, real_mean = simulate_survey(generate_population_data(), channel, wording)
    assert abs(ns["x"] - real_mean) < 1e-9


def test_survey_reach_count_mirror_code_in_app_popup_excluded_churned():
    customers = generate_population_data().frame
    ns = _exec_code(survey_reach_count_mirror_code("vocal_critic", "still_active == False", "x"), {"customers": customers})
    assert ns["x"] == 27


def test_survey_reach_count_mirror_code_power_user_panel_reachable_critics():
    customers = generate_population_data().frame
    ns = _exec_code(survey_reach_count_mirror_code("vocal_critic", "is_power_user == True", "x"), {"customers": customers})
    assert ns["x"] == 0


@pytest.mark.parametrize("segment,expected_rate", list(RESPONSE_RATE_BY_SEGMENT.items()))
def test_response_rate_mirror_code_matches_the_real_response_rate_by_segment_data(segment, expected_rate):
    customers = generate_population_data().frame
    ns = _exec_code(response_rate_mirror_code(segment, "x"), {"customers": customers})
    assert ns["x"] == expected_rate


def test_broad_email_respondent_counts_by_segment_match_the_reveal_copy():
    """The nonresponse reveal's own narrative cites real respondent counts
    (36/21/45) computed from the existing data, never invented - this
    regression keeps that claim honest."""
    dataset = generate_population_data()
    counts = dataset.frame.groupby("segment").size()
    expected = {"vocal_critic": 36, "vocal_fan": 21, "quiet_majority": 45}
    for segment, rate in RESPONSE_RATE_BY_SEGMENT.items():
        assert round(counts[segment] * rate) == expected[segment]


def test_power_user_panel_bias_is_never_the_same_mechanism_as_in_app_popup():
    """power_user_panel's own bias is a sampling-frame exclusion (zero
    critics can ever appear, regardless of response propensity) - a
    structurally different mechanism from in_app_popup's coverage
    exclusion (which excludes only the already-churned subset of one
    segment). This regression keeps the two from silently collapsing
    into the same claim."""
    dataset = generate_population_data()
    in_app_popup_reached_critics = dataset.frame.query("still_active == True")
    in_app_popup_reached_critics = in_app_popup_reached_critics[in_app_popup_reached_critics["segment"] == "vocal_critic"]
    power_panel_reached_critics = dataset.frame.query("is_power_user == True")
    power_panel_reached_critics = power_panel_reached_critics[power_panel_reached_critics["segment"] == "vocal_critic"]
    assert len(in_app_popup_reached_critics) == 18  # in_app_popup DOES still reach some critics
    assert len(power_panel_reached_critics) == 0  # power_user_panel reaches NONE - a structural frame exclusion


def test_true_population_mean_stays_internal_ground_truth_never_a_locale_string():
    """58.5% must never appear as a translated, student-facing string
    anywhere - it stays authoring/regression ground truth only."""
    import json
    from pathlib import Path

    dataset = generate_population_data()
    mean = true_population_mean(dataset)
    assert round(mean, 4) == 0.5850

    locales_dir = Path(__file__).resolve().parents[1] / "src" / "data_science_arcade" / "localization" / "locales"
    for locale_file in ("en.json", "pl.json"):
        strings = json.loads((locales_dir / locale_file).read_text(encoding="utf-8"))
        l24_values = " ".join(v for k, v in strings.items() if k.startswith(("lesson.l24.", "dialogue.l24_")))
        assert "58.5" not in l24_values
        assert "58,5" not in l24_values
