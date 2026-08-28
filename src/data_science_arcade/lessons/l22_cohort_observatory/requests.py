from data_science_arcade.lessons.framework.cohort import CohortRequest, ComparisonOption

MISMATCHED_LABEL_KEY = "lesson.l22.option.mismatched_month_comparison"
SAME_MONTH_LABEL_KEY = "lesson.l22.option.same_month_comparison"

NEWEST_COHORT_CLAIM = CohortRequest(
    key="newest_cohort_claim",
    prompt_key="lesson.l22.request.newest_cohort_claim.prompt",
    hint_key="lesson.l22.request.newest_cohort_claim.hint",
    options=(
        ComparisonOption("mismatched_month_comparison", MISMATCHED_LABEL_KEY, "may", 1, "jan", 4),
        ComparisonOption("same_month_comparison", SAME_MONTH_LABEL_KEY, "may", 1, "jan", 1),
    ),
)
APRIL_COMPLAINT = CohortRequest(
    key="april_complaint",
    prompt_key="lesson.l22.request.april_complaint.prompt",
    hint_key="lesson.l22.request.april_complaint.hint",
    options=(
        ComparisonOption("same_month_comparison", SAME_MONTH_LABEL_KEY, "apr", 1, "jan", 1),
        ComparisonOption("mismatched_month_comparison", MISMATCHED_LABEL_KEY, "apr", 1, "jan", 4),
    ),
)
MARCH_PRODUCT_CHANGE_CLAIM = CohortRequest(
    key="march_product_change_claim",
    prompt_key="lesson.l22.request.march_product_change_claim.prompt",
    hint_key="lesson.l22.request.march_product_change_claim.hint",
    options=(
        ComparisonOption("mismatched_month_comparison", MISMATCHED_LABEL_KEY, "mar", 1, "feb", 4),
        ComparisonOption("same_month_comparison", SAME_MONTH_LABEL_KEY, "mar", 1, "feb", 1),
    ),
)

COHORT_REQUESTS: tuple[CohortRequest, ...] = (NEWEST_COHORT_CLAIM, APRIL_COMPLAINT, MARCH_PRODUCT_CHANGE_CLAIM)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "newest_cohort_claim": "same_month_comparison",
    "april_complaint": "same_month_comparison",
    "march_product_change_claim": "same_month_comparison",
}
