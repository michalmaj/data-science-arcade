from data_science_arcade.lessons.framework.aggregation import AggregateOption, AggregationRequest, GroupByOption

# Hand-crafted, no trap outside the twist (matching every prior lesson's
# discipline): each request has one genuinely correct (group by, aggregate)
# pair. Decoys are real, resolvable mistakes - grouping at the wrong grain
# (per-order instead of per-store, blurring days together) or applying the
# wrong operation (averaging instead of summing, summing instead of
# counting). The double-counting/distinct-customer trap is reserved
# entirely for the twist.
AGGREGATION_REQUESTS: tuple[AggregationRequest, ...] = (
    AggregationRequest(
        key="revenue_per_store",
        prompt_key="lesson.l12.request.revenue_per_store.prompt",
        hint_key="lesson.l12.request.revenue_per_store.hint",
        value_column="revenue",
        group_by_options=(
            GroupByOption("store_id", "lesson.l12.group_by.store_id", "store_id"),
            GroupByOption("order_id", "lesson.l12.group_by.order_id", "order_id"),
            GroupByOption("customer_id", "lesson.l12.group_by.customer_id", "customer_id"),
        ),
        aggregate_options=(
            AggregateOption("mean", "lesson.l12.aggregate.mean", "mean"),
            AggregateOption("sum", "lesson.l12.aggregate.sum", "sum"),
            AggregateOption("count", "lesson.l12.aggregate.count", "count"),
        ),
    ),
    AggregationRequest(
        key="orders_per_day",
        prompt_key="lesson.l12.request.orders_per_day.prompt",
        hint_key="lesson.l12.request.orders_per_day.hint",
        value_column="revenue",
        group_by_options=(
            GroupByOption("store_id", "lesson.l12.group_by.store_id", "store_id"),
            GroupByOption("order_date", "lesson.l12.group_by.order_date", "order_date"),
            GroupByOption("order_id", "lesson.l12.group_by.order_id", "order_id"),
        ),
        aggregate_options=(
            AggregateOption("sum", "lesson.l12.aggregate.sum", "sum"),
            AggregateOption("mean", "lesson.l12.aggregate.mean", "mean"),
            AggregateOption("count", "lesson.l12.aggregate.count", "count"),
        ),
    ),
    AggregationRequest(
        key="average_order_value_per_store",
        prompt_key="lesson.l12.request.average_order_value_per_store.prompt",
        hint_key="lesson.l12.request.average_order_value_per_store.hint",
        value_column="revenue",
        group_by_options=(
            GroupByOption("order_id", "lesson.l12.group_by.order_id", "order_id"),
            GroupByOption("customer_id", "lesson.l12.group_by.customer_id", "customer_id"),
            GroupByOption("store_id", "lesson.l12.group_by.store_id", "store_id"),
        ),
        aggregate_options=(
            AggregateOption("count", "lesson.l12.aggregate.count", "count"),
            AggregateOption("mean", "lesson.l12.aggregate.mean", "mean"),
            AggregateOption("sum", "lesson.l12.aggregate.sum", "sum"),
        ),
    ),
)

CORRECT_PIPELINE_BY_REQUEST: dict[str, tuple[str, str]] = {
    "revenue_per_store": ("store_id", "sum"),
    "orders_per_day": ("order_date", "count"),
    "average_order_value_per_store": ("store_id", "mean"),
}
