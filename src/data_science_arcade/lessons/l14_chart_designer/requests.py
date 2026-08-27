from data_science_arcade.lessons.framework.chart import ChartOption, ChartRequest
from data_science_arcade.lessons.l14_chart_designer.store_metrics import DAILY_REVENUE, STORE_RETURNS, STORE_REVENUE

# Hand-crafted, no trap outside the twist (matching every prior lesson's
# discipline): each request has one genuinely correct chart recipe for
# what it actually needs to show. A zoomed bar scale is always a decoy
# here - it never wins - and a line chart connecting unordered store
# categories is the other recurring decoy, since a line implies a trend
# that doesn't exist between separate stores. Correct-option index
# varies across all three requests so no single index reveals the answer.
CHART_REQUESTS: tuple[ChartRequest, ...] = (
    ChartRequest(
        key="revenue_by_store",
        prompt_key="lesson.l14.request.revenue_by_store.prompt",
        hint_key="lesson.l14.request.revenue_by_store.hint",
        categories=tuple(STORE_REVENUE),
        values=tuple(STORE_REVENUE.values()),
        options=(
            ChartOption("line", "lesson.l14.option.line", "line", "zero_based"),
            ChartOption("bar_zoomed", "lesson.l14.option.bar_zoomed", "bar", "zoomed"),
            ChartOption("bar_zero", "lesson.l14.option.bar_zero", "bar", "zero_based"),
        ),
    ),
    ChartRequest(
        key="daily_revenue_trend",
        prompt_key="lesson.l14.request.daily_revenue_trend.prompt",
        hint_key="lesson.l14.request.daily_revenue_trend.hint",
        categories=tuple(DAILY_REVENUE),
        values=tuple(DAILY_REVENUE.values()),
        options=(
            ChartOption("bar_zero", "lesson.l14.option.bar_zero", "bar", "zero_based"),
            ChartOption("line", "lesson.l14.option.line", "line", "zero_based"),
            ChartOption("bar_zoomed", "lesson.l14.option.bar_zoomed", "bar", "zoomed"),
        ),
    ),
    ChartRequest(
        key="returns_by_store",
        prompt_key="lesson.l14.request.returns_by_store.prompt",
        hint_key="lesson.l14.request.returns_by_store.hint",
        categories=tuple(STORE_RETURNS),
        values=tuple(float(v) for v in STORE_RETURNS.values()),
        options=(
            ChartOption("bar_zoomed", "lesson.l14.option.bar_zoomed", "bar", "zoomed"),
            ChartOption("bar_zero", "lesson.l14.option.bar_zero", "bar", "zero_based"),
            ChartOption("line", "lesson.l14.option.line", "line", "zero_based"),
        ),
    ),
)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "revenue_by_store": "bar_zero",
    "daily_revenue_trend": "line",
    "returns_by_store": "bar_zero",
}
