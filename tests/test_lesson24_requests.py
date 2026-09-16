from data_science_arcade.lessons.l24_survey_bureau.requests import CORRECT_COMBO_BY_REQUEST, SURVEY_REQUESTS


def test_exactly_one_real_decision():
    """The two predecessor requests (fast_turnaround_temptation,
    advisory_panel_temptation) shared the identical (neutral, broad_email)
    answer - reduced to one real decision, widened rather than narrowed."""
    assert {request.key for request in SURVEY_REQUESTS} == {"general_satisfaction_check"}


def test_every_request_has_a_correct_combo_recorded():
    assert set(CORRECT_COMBO_BY_REQUEST) == {request.key for request in SURVEY_REQUESTS}


def test_the_correct_wording_is_among_the_offered_options():
    request = SURVEY_REQUESTS[0]
    correct_wording, _correct_channel = CORRECT_COMBO_BY_REQUEST[request.key]
    assert correct_wording in {option.key for option in request.wording_options}


def test_the_correct_channel_is_among_the_offered_options():
    request = SURVEY_REQUESTS[0]
    _correct_wording, correct_channel = CORRECT_COMBO_BY_REQUEST[request.key]
    assert correct_channel in {option.key for option in request.channel_options}


def test_the_request_offers_two_wording_options_and_all_three_channel_options():
    request = SURVEY_REQUESTS[0]
    assert len(request.wording_options) == 2
    assert len(request.channel_options) == 3


def test_correct_combo_is_neutral_broad_email():
    assert CORRECT_COMBO_BY_REQUEST["general_satisfaction_check"] == ("neutral", "broad_email")


def test_neutral_wording_never_carries_a_bias():
    request = SURVEY_REQUESTS[0]
    neutral = next(option for option in request.wording_options if option.key == "neutral")
    assert neutral.bias == 0.0


def test_leading_wording_always_carries_a_positive_bias():
    request = SURVEY_REQUESTS[0]
    leading = next(option for option in request.wording_options if option.key == "leading")
    assert leading.bias > 0.0


def test_broad_email_never_filters_anyone_out():
    request = SURVEY_REQUESTS[0]
    broad_email = next(option for option in request.channel_options if option.key == "broad_email")
    assert broad_email.reach_query is None


def test_in_app_popup_and_power_user_panel_both_filter_reach():
    request = SURVEY_REQUESTS[0]
    in_app_popup = next(option for option in request.channel_options if option.key == "in_app_popup")
    power_user_panel = next(option for option in request.channel_options if option.key == "power_user_panel")
    assert in_app_popup.reach_query is not None
    assert power_user_panel.reach_query is not None
    assert in_app_popup.reach_query != power_user_panel.reach_query
