from data_science_arcade.lessons.framework.timeseries import LensOption, TimeSeriesRequest

NEARBY_DAYS_LABEL_KEY = "lesson.l23.option.nearby_days_only"
SAME_DAYS_PREVIOUS_LABEL_KEY = "lesson.l23.option.same_days_previous_period"

RELEASE_DIP_CLAIM = TimeSeriesRequest(
    key="release_dip_claim",
    prompt_key="lesson.l23.request.release_dip_claim.prompt",
    hint_key="lesson.l23.request.release_dip_claim.hint",
    highlight_days=(13, 14),
    options=(
        LensOption("nearby_days_only", NEARBY_DAYS_LABEL_KEY, show_previous_period=False),
        LensOption("same_days_previous_period", SAME_DAYS_PREVIOUS_LABEL_KEY, show_previous_period=True),
    ),
)
CAMPAIGN_LIFT_CLAIM = TimeSeriesRequest(
    key="campaign_lift_claim",
    prompt_key="lesson.l23.request.campaign_lift_claim.prompt",
    hint_key="lesson.l23.request.campaign_lift_claim.hint",
    highlight_days=(8,),
    options=(
        LensOption("same_days_previous_period", SAME_DAYS_PREVIOUS_LABEL_KEY, show_previous_period=True),
        LensOption("nearby_days_only", NEARBY_DAYS_LABEL_KEY, show_previous_period=False),
    ),
)
WEEK_OVER_WEEK_CLAIM = TimeSeriesRequest(
    key="week_over_week_claim",
    prompt_key="lesson.l23.request.week_over_week_claim.prompt",
    hint_key="lesson.l23.request.week_over_week_claim.hint",
    highlight_days=(15, 16, 17, 18, 19, 20, 21),
    options=(
        LensOption("nearby_days_only", NEARBY_DAYS_LABEL_KEY, show_previous_period=False),
        LensOption("same_days_previous_period", SAME_DAYS_PREVIOUS_LABEL_KEY, show_previous_period=True),
    ),
)

TIME_SERIES_REQUESTS: tuple[TimeSeriesRequest, ...] = (RELEASE_DIP_CLAIM, CAMPAIGN_LIFT_CLAIM, WEEK_OVER_WEEK_CLAIM)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "release_dip_claim": "same_days_previous_period",
    "campaign_lift_claim": "same_days_previous_period",
    "week_over_week_claim": "same_days_previous_period",
}
