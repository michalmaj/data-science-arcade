from data_science_arcade.lessons.framework.cohort import ComparisonOption, CohortRequest

MISMATCHED_LABEL_KEY = "lesson.l22.option.mismatched_month_comparison"
SAME_MONTH_LABEL_KEY = "lesson.l22.option.same_month_comparison"

# All three of this request's predecessors (deleted) tested the identical
# same-age-vs-mismatched-age competency under different cohort-pair
# dressings - one real decision, not three redundant ones. Retargeted from
# an arbitrary jan/4 to jan/5 (January's own most-mature observed number):
# a more realistic, more tempting Finance trap ("May's already at 76% -
# beating our best cohort's own month-5 number of 46%!") than an arbitrary
# mid-horizon pairing, and it sets up the horizon reveal's own point that
# a mature cohort's own month-5 rate is mechanically lower than its own
# month-1 rate.
MAY_RETENTION_COMPARISON = CohortRequest(
    key="may_retention_comparison",
    prompt_key="lesson.l22.request.may_retention_comparison.prompt",
    options=(
        ComparisonOption("same_month_comparison", SAME_MONTH_LABEL_KEY, "may", 1, "jan", 1),
        ComparisonOption("mismatched_month_comparison", MISMATCHED_LABEL_KEY, "may", 1, "jan", 5),
    ),
)

COHORT_REQUESTS: tuple[CohortRequest, ...] = (MAY_RETENTION_COMPARISON,)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "may_retention_comparison": "same_month_comparison",
}
