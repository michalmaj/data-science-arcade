from data_science_arcade.lessons.framework.timeseries import LensOption, TimeSeriesRequest

NEARBY_DAYS_LABEL_KEY = "lesson.l23.option.nearby_days_only"
SAME_DAYS_PREVIOUS_LABEL_KEY = "lesson.l23.option.same_days_previous_period"

# The two predecessors of this request (deleted) shared the identical
# same_days_previous_period answer - one real decision, not three
# redundant ones. Their own real facts (the campaign-day lift, week 3's
# own normal rhythm) live on in the two mandatory reveals / Final Brief,
# never as their own duplicate interactive picks.
RELEASE_DIP_CLAIM = TimeSeriesRequest(
    key="release_dip_claim",
    prompt_key="lesson.l23.request.release_dip_claim.prompt",
    highlight_days=(13, 14),
    options=(
        LensOption("nearby_days_only", NEARBY_DAYS_LABEL_KEY, show_previous_period=False),
        LensOption("same_days_previous_period", SAME_DAYS_PREVIOUS_LABEL_KEY, show_previous_period=True),
    ),
)

TIME_SERIES_REQUESTS: tuple[TimeSeriesRequest, ...] = (RELEASE_DIP_CLAIM,)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "release_dip_claim": "same_days_previous_period",
}
