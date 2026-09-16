from data_science_arcade.lessons.framework.survey import ChannelOption, SurveyRequest, WordingOption

NEUTRAL_WORDING = WordingOption("neutral", "lesson.l24.option.wording.neutral", bias=0.0)
LEADING_WORDING = WordingOption("leading", "lesson.l24.option.wording.leading", bias=0.15)

BROAD_EMAIL = ChannelOption("broad_email", "lesson.l24.option.channel.broad_email", reach_query=None)
IN_APP_POPUP = ChannelOption("in_app_popup", "lesson.l24.option.channel.in_app_popup", reach_query="still_active == True")
POWER_USER_PANEL = ChannelOption("power_user_panel", "lesson.l24.option.channel.power_user_panel", reach_query="is_power_user == True")

# The three predecessors of this request (deleted) all shared the
# identical (neutral, broad_email) answer - one real decision, not three
# redundant ones. Widened rather than narrowed: all 3 real channels are
# offered alongside both wordings at once (6 real combos, 1 correct) -
# the live result preview already shows every combo's respondent count
# and recorded average before commit, so nothing about 6 visible combos
# hides information a 2-option version wouldn't also expose in isolation,
# and the correct answer (52.9%) is also the worst-looking number on
# screen - a stronger trap than any 2-option version could build.
GENERAL_SATISFACTION_CHECK = SurveyRequest(
    key="general_satisfaction_check",
    prompt_key="lesson.l24.request.general_satisfaction_check.prompt",
    wording_options=(NEUTRAL_WORDING, LEADING_WORDING),
    channel_options=(BROAD_EMAIL, IN_APP_POPUP, POWER_USER_PANEL),
)

SURVEY_REQUESTS: tuple[SurveyRequest, ...] = (GENERAL_SATISFACTION_CHECK,)

CORRECT_COMBO_BY_REQUEST: dict[str, tuple[str, str]] = {
    "general_satisfaction_check": ("neutral", "broad_email"),
}
