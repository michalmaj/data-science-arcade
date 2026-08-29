from data_science_arcade.lessons.framework.survey import ChannelOption, SurveyRequest, WordingOption

NEUTRAL_WORDING = WordingOption("neutral", "lesson.l24.option.wording.neutral", bias=0.0)
LEADING_WORDING = WordingOption("leading", "lesson.l24.option.wording.leading", bias=0.15)

BROAD_EMAIL = ChannelOption("broad_email", "lesson.l24.option.channel.broad_email", reach_query=None)
IN_APP_POPUP = ChannelOption("in_app_popup", "lesson.l24.option.channel.in_app_popup", reach_query="still_active == True")
POWER_USER_PANEL = ChannelOption("power_user_panel", "lesson.l24.option.channel.power_user_panel", reach_query="is_power_user == True")

# Three scenarios, each tempting a different flawed combo, but always for
# a concrete, real reason (matching every prior lesson's discipline of
# real, resolvable decoys rather than an arbitrary wrong answer) - fast
# turnaround, ready-made infrastructure, or "our most engaged customers
# already give thoughtful feedback." The defensible pair (neutral wording,
# broad email) never changes, but its position varies across both option
# columns so it isn't recognizable by position alone.
SURVEY_REQUESTS: tuple[SurveyRequest, ...] = (
    SurveyRequest(
        key="general_satisfaction_check",
        prompt_key="lesson.l24.request.general_satisfaction_check.prompt",
        hint_key="lesson.l24.request.general_satisfaction_check.hint",
        wording_options=(NEUTRAL_WORDING, LEADING_WORDING),
        channel_options=(BROAD_EMAIL, POWER_USER_PANEL),
    ),
    SurveyRequest(
        key="fast_turnaround_temptation",
        prompt_key="lesson.l24.request.fast_turnaround_temptation.prompt",
        hint_key="lesson.l24.request.fast_turnaround_temptation.hint",
        wording_options=(LEADING_WORDING, NEUTRAL_WORDING),
        channel_options=(IN_APP_POPUP, BROAD_EMAIL),
    ),
    SurveyRequest(
        key="advisory_panel_temptation",
        prompt_key="lesson.l24.request.advisory_panel_temptation.prompt",
        hint_key="lesson.l24.request.advisory_panel_temptation.hint",
        wording_options=(NEUTRAL_WORDING, LEADING_WORDING),
        channel_options=(POWER_USER_PANEL, BROAD_EMAIL),
    ),
)

CORRECT_COMBO_BY_REQUEST: dict[str, tuple[str, str]] = {
    "general_satisfaction_check": ("neutral", "broad_email"),
    "fast_turnaround_temptation": ("neutral", "broad_email"),
    "advisory_panel_temptation": ("neutral", "broad_email"),
}
