import pandas as pd

from data_science_arcade.lessons.l15_segment_detective.sessions import (
    DEVICE_RATE_PCT,
    DEVICE_SHARE_PCT,
    MASTERY_CARRIER_PCT,
    MASTERY_CARRIER_SHARE_PCT,
    MASTERY_OVERALL_PCT,
    OVERALL_RATE_PCT,
    Q2_AT_Q1_MIX_PCT,
    REGION_RATE_PCT,
    REGION_SHARE_PCT,
    TOTAL_SESSIONS,
    generate_sessions,
)


def test_total_sessions_and_per_period_split():
    sessions = generate_sessions()
    assert len(sessions.frame) == TOTAL_SESSIONS == 2000
    assert sessions.frame.groupby("period").size().to_dict() == {"Q1": 1000, "Q2": 1000}


def test_overall_rate_is_the_real_simpson_reversal():
    assert OVERALL_RATE_PCT == {"Q1": 28.4, "Q2": 33.2}


def test_device_rates_both_decline_within_device():
    assert DEVICE_RATE_PCT["Q1"] == {"mobile": 42.0, "desktop": 25.0}
    assert DEVICE_RATE_PCT["Q2"] == {"mobile": 38.0, "desktop": 22.0}
    assert DEVICE_RATE_PCT["Q2"]["mobile"] < DEVICE_RATE_PCT["Q1"]["mobile"]
    assert DEVICE_RATE_PCT["Q2"]["desktop"] < DEVICE_RATE_PCT["Q1"]["desktop"]


def test_device_share_shifts_sharply_toward_mobile():
    assert DEVICE_SHARE_PCT["Q1"] == {"mobile": 20.0, "desktop": 80.0}
    assert DEVICE_SHARE_PCT["Q2"] == {"mobile": 70.0, "desktop": 30.0}


def test_region_is_an_exactly_neutral_slice():
    for period in ("Q1", "Q2"):
        assert REGION_RATE_PCT[period]["EU"] == REGION_RATE_PCT[period]["US"] == OVERALL_RATE_PCT[period]
        assert REGION_SHARE_PCT[period] == {"EU": 50.0, "US": 50.0}


def test_region_neutrality_holds_in_the_real_generated_frame_too():
    sessions = generate_sessions().frame
    region_rates = sessions.groupby(["period", "region"])["converted"].mean().unstack() * 100
    for period in ("Q1", "Q2"):
        assert round(region_rates.loc[period, "EU"], 1) == round(region_rates.loc[period, "US"], 1) == OVERALL_RATE_PCT[period]
    region_mix = pd.crosstab(sessions["period"], sessions["region"], normalize="index") * 100
    for period in ("Q1", "Q2"):
        assert round(region_mix.loc[period, "EU"], 1) == round(region_mix.loc[period, "US"], 1) == 50.0


def test_weighted_reconstruction_matches_the_observed_aggregate_exactly():
    sessions = generate_sessions().frame
    device_rates = sessions.groupby(["period", "device"])["converted"].mean().unstack()
    device_mix = pd.crosstab(sessions["period"], sessions["device"], normalize="index")
    reconstructed = (device_rates * device_mix).sum(axis=1) * 100
    overall = sessions.groupby("period")["converted"].mean() * 100
    for period in ("Q1", "Q2"):
        assert round(reconstructed[period], 6) == round(overall[period], 6)


def test_standardized_q2_at_q1_mix_is_below_q1_observed():
    assert round(Q2_AT_Q1_MIX_PCT, 1) == 25.2
    assert Q2_AT_Q1_MIX_PCT < OVERALL_RATE_PCT["Q1"]


def test_generated_sessions_has_no_missing_values():
    sessions = generate_sessions()
    assert sessions.frame.isna().sum().sum() == 0


def test_mastery_domain_is_a_real_non_reversal():
    assert MASTERY_OVERALL_PCT["Q2"] > MASTERY_OVERALL_PCT["Q1"]
    assert MASTERY_CARRIER_PCT["Q2"]["in_house"] > MASTERY_CARRIER_PCT["Q1"]["in_house"]
    assert MASTERY_CARRIER_PCT["Q2"]["third_party"] > MASTERY_CARRIER_PCT["Q1"]["third_party"]
    overall_gain = MASTERY_OVERALL_PCT["Q2"] - MASTERY_OVERALL_PCT["Q1"]
    in_house_gain = MASTERY_CARRIER_PCT["Q2"]["in_house"] - MASTERY_CARRIER_PCT["Q1"]["in_house"]
    third_party_gain = MASTERY_CARRIER_PCT["Q2"]["third_party"] - MASTERY_CARRIER_PCT["Q1"]["third_party"]
    assert overall_gain < in_house_gain
    assert overall_gain < third_party_gain
    assert MASTERY_CARRIER_SHARE_PCT["Q1"]["third_party"] < MASTERY_CARRIER_SHARE_PCT["Q2"]["third_party"]
