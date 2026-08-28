import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.funnel import FunnelDefinition, FunnelStep

CHECKOUT_EVENTS_SCHEMA = Schema(
    columns=(
        ColumnSchema("definition_key", "object", description="which candidate way of counting this event was used"),
        ColumnSchema("step_key", "object"),
        ColumnSchema("step_order", "int64"),
        ColumnSchema("count", "int64"),
    )
)

_STEP_LABEL_KEYS = {
    "site_visit": "lesson.l21.step.site_visit",
    "product_view": "lesson.l21.step.product_view",
    "add_to_cart": "lesson.l21.step.add_to_cart",
    "checkout_started": "lesson.l21.step.checkout_started",
    "order_confirmed": "lesson.l21.step.order_confirmed",
}

# Three ways of counting the same checkout funnel, all built on the same
# real site_visit/product_view/checkout_started/order_confirmed counts -
# only how "add_to_cart" gets counted differs between them. Real numbers,
# not hand-picked headlines: "legacy_cart_tracking" only captures cart
# adds from an older tracking pixel that's missing on newer app builds
# (an instrumentation gap); "raw_cart_events" counts every add-to-cart
# click, including repeat clicks from the same session, instead of
# unique sessions; "complete_cart_tracking" is the properly-instrumented,
# session-deduplicated count - the one defensible baseline both
# request 1 and request 3 converge on as "correct" from different angles.
ROWS = [
    ("legacy_cart_tracking", "site_visit", 0, 10000),
    ("legacy_cart_tracking", "product_view", 1, 8200),
    ("legacy_cart_tracking", "add_to_cart", 2, 2100),
    ("legacy_cart_tracking", "checkout_started", 3, 1900),
    ("legacy_cart_tracking", "order_confirmed", 4, 1500),
    ("complete_cart_tracking", "site_visit", 0, 10000),
    ("complete_cart_tracking", "product_view", 1, 8200),
    ("complete_cart_tracking", "add_to_cart", 2, 4900),
    ("complete_cart_tracking", "checkout_started", 3, 1900),
    ("complete_cart_tracking", "order_confirmed", 4, 1500),
    ("raw_cart_events", "site_visit", 0, 10000),
    ("raw_cart_events", "product_view", 1, 8200),
    ("raw_cart_events", "add_to_cart", 2, 7300),
    ("raw_cart_events", "checkout_started", 3, 1900),
    ("raw_cart_events", "order_confirmed", 4, 1500),
]


def generate_checkout_events() -> Dataset:
    frame = pd.DataFrame(ROWS, columns=["definition_key", "step_key", "step_order", "count"])
    step = PipelineStep("collected", python_code="checkout_events = pd.read_csv('novamart_checkout_events.csv')")
    return Dataset(name="checkout_events", frame=frame, schema=CHECKOUT_EVENTS_SCHEMA, history=(step,))


def build_funnel_definition(
    dataset: Dataset,
    dataset_definition_key: str,
    key: str,
    label_key: str,
    percent_basis: str = "previous",
    step_label_overrides: dict[str, str] | None = None,
) -> FunnelDefinition:
    frame = dataset.frame[dataset.frame["definition_key"] == dataset_definition_key].sort_values("step_order")
    overrides = step_label_overrides or {}
    steps = tuple(
        FunnelStep(
            key=row.step_key,
            label_key=overrides.get(row.step_key, _STEP_LABEL_KEYS[row.step_key]),
            count=int(row.count),
        )
        for row in frame.itertuples()
    )
    return FunnelDefinition(key=key, label_key=label_key, steps=steps, percent_basis=percent_basis)
