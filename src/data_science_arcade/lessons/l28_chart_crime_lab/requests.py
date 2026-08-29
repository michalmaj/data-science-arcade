from data_science_arcade.lessons.framework.chart import ChartOption, ChartRequest
from data_science_arcade.lessons.l28_chart_crime_lab.chart_data import (
    fair_return_rate,
    flawed_return_rate,
    generate_active_users_data,
    generate_returns_data,
    generate_satisfaction_data,
)

_satisfaction = generate_satisfaction_data()
_active_users = generate_active_users_data()
_returns = generate_returns_data()

_QUARTERS = ("Q1", "Q2", "Q3", "Q4")
_PER_UNITS_SOLD_VALUES = tuple(fair_return_rate(_returns, q) * 100 for q in _QUARTERS)
_PER_CUSTOMERS_VALUES = tuple(flawed_return_rate(_returns, q) * 10000 for q in _QUARTERS)

_ALL_MONTHS = tuple(_active_users.frame.sort_values("month_index")["month"])
_ALL_ACTIVE_USERS = tuple(float(v) for v in _active_users.frame.sort_values("month_index")["active_users"])

# Three requests, each a real chart flaw distinct from the others - a
# truncated/zoomed axis, a cherry-picked date window, and a rate computed
# against the wrong denominator - hand-crafted, not random, verified via
# script before any of this was written. Correct-option index varies
# across all three requests (1, 0, 1) so no single index reveals the
# answer.
CHART_REQUESTS: tuple[ChartRequest, ...] = (
    ChartRequest(
        key="satisfaction_score_claim",
        prompt_key="lesson.l28.request.satisfaction_score_claim.prompt",
        hint_key="lesson.l28.request.satisfaction_score_claim.hint",
        categories=("Q1", "Q2", "Q3", "Q4"),
        values=tuple(float(v) for v in _satisfaction.frame["satisfaction_score"]),
        options=(
            ChartOption("zoomed", "lesson.l28.option.satisfaction_score_claim.zoomed", "bar", "zoomed"),
            ChartOption("zero_based", "lesson.l28.option.satisfaction_score_claim.zero_based", "bar", "zero_based"),
        ),
    ),
    ChartRequest(
        key="active_users_claim",
        prompt_key="lesson.l28.request.active_users_claim.prompt",
        hint_key="lesson.l28.request.active_users_claim.hint",
        categories=_ALL_MONTHS,
        values=_ALL_ACTIVE_USERS,
        options=(
            ChartOption("full_year", "lesson.l28.option.active_users_claim.full_year", "line", "zero_based"),
            ChartOption(
                "last_two_months",
                "lesson.l28.option.active_users_claim.last_two_months",
                "line",
                "zero_based",
                categories=_ALL_MONTHS[-2:],
                values=_ALL_ACTIVE_USERS[-2:],
            ),
            ChartOption(
                "first_two_months",
                "lesson.l28.option.active_users_claim.first_two_months",
                "line",
                "zero_based",
                categories=_ALL_MONTHS[:2],
                values=_ALL_ACTIVE_USERS[:2],
            ),
        ),
    ),
    ChartRequest(
        key="returns_rate_claim",
        prompt_key="lesson.l28.request.returns_rate_claim.prompt",
        hint_key="lesson.l28.request.returns_rate_claim.hint",
        categories=_QUARTERS,
        values=_PER_CUSTOMERS_VALUES,
        options=(
            ChartOption("per_customers", "lesson.l28.option.returns_rate_claim.per_customers", "bar", "zero_based"),
            ChartOption(
                "per_units_sold",
                "lesson.l28.option.returns_rate_claim.per_units_sold",
                "bar",
                "zero_based",
                categories=_QUARTERS,
                values=_PER_UNITS_SOLD_VALUES,
            ),
        ),
    ),
)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "satisfaction_score_claim": "zero_based",
    "active_users_claim": "full_year",
    "returns_rate_claim": "per_units_sold",
}
