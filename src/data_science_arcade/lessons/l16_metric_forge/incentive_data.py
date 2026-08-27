import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

INCENTIVE_SCHEMA = Schema(
    columns=(
        ColumnSchema("metric_key", "object"),
        ColumnSchema("period", "object", description="'before' or 'after' the metric became the official target"),
        ColumnSchema("week", "int64"),
        ColumnSchema("primary_value", "float64"),
        ColumnSchema("guardrail_value", "float64"),
    )
)

# Hand-crafted (not random) weekly observations - two weeks before and two
# weeks after each candidate metric became the official target for its
# team, simulating how a rational-but-narrow optimizer responds to
# whatever gets measured. Before/after values are real pandas means over
# these rows, not hand-picked headline numbers. Two of every three
# candidates per request are genuinely gameable (the primary number
# improves sharply, but the guardrail - customer satisfaction, retention -
# drops with it); one is resistant to gaming and the guardrail holds or
# improves alongside it.
SUPPORT_ROWS = [
    ("quick_close_share", "before", 1, 0.58, 0.87),
    ("quick_close_share", "before", 2, 0.62, 0.89),
    ("quick_close_share", "after", 1, 0.83, 0.66),
    ("quick_close_share", "after", 2, 0.87, 0.70),
    ("first_contact_resolution_rate", "before", 1, 0.68, 0.87),
    ("first_contact_resolution_rate", "before", 2, 0.72, 0.89),
    ("first_contact_resolution_rate", "after", 1, 0.80, 0.89),
    ("first_contact_resolution_rate", "after", 2, 0.84, 0.91),
    ("tickets_closed_rate", "before", 1, 0.73, 0.87),
    ("tickets_closed_rate", "before", 2, 0.77, 0.89),
    ("tickets_closed_rate", "after", 1, 0.90, 0.69),
    ("tickets_closed_rate", "after", 2, 0.94, 0.73),
]
SALES_ROWS = [
    ("signup_conversion_rate", "before", 1, 0.10, 0.66),
    ("signup_conversion_rate", "before", 2, 0.14, 0.64),
    ("signup_conversion_rate", "after", 1, 0.26, 0.42),
    ("signup_conversion_rate", "after", 2, 0.30, 0.38),
    ("activated_customer_rate", "before", 1, 0.43, 0.66),
    ("activated_customer_rate", "before", 2, 0.47, 0.64),
    ("activated_customer_rate", "after", 1, 0.56, 0.68),
    ("activated_customer_rate", "after", 2, 0.60, 0.66),
    ("leads_contacted_rate", "before", 1, 0.48, 0.66),
    ("leads_contacted_rate", "before", 2, 0.52, 0.64),
    ("leads_contacted_rate", "after", 1, 0.78, 0.46),
    ("leads_contacted_rate", "after", 2, 0.82, 0.42),
]
APP_ROWS = [
    ("daily_open_rate", "before", 1, 0.28, 0.61),
    ("daily_open_rate", "before", 2, 0.32, 0.59),
    ("daily_open_rate", "after", 1, 0.53, 0.40),
    ("daily_open_rate", "after", 2, 0.57, 0.36),
    ("task_completion_rate", "before", 1, 0.38, 0.61),
    ("task_completion_rate", "before", 2, 0.42, 0.59),
    ("task_completion_rate", "after", 1, 0.50, 0.65),
    ("task_completion_rate", "after", 2, 0.54, 0.61),
    ("notification_click_rate", "before", 1, 0.18, 0.61),
    ("notification_click_rate", "before", 2, 0.22, 0.59),
    ("notification_click_rate", "after", 1, 0.43, 0.43),
    ("notification_click_rate", "after", 2, 0.47, 0.39),
]


def _build(name: str, rows: list[tuple[str, str, int, float, float]]) -> Dataset:
    frame = pd.DataFrame(rows, columns=["metric_key", "period", "week", "primary_value", "guardrail_value"])
    step = PipelineStep("collected", python_code=f"{name} = pd.read_csv('novamart_{name}.csv')")
    return Dataset(name=name, frame=frame, schema=INCENTIVE_SCHEMA, history=(step,))


def generate_support_data() -> Dataset:
    return _build("support_metrics", SUPPORT_ROWS)


def generate_sales_data() -> Dataset:
    return _build("sales_metrics", SALES_ROWS)


def generate_app_data() -> Dataset:
    return _build("app_metrics", APP_ROWS)


def metric_mean(dataset: Dataset, metric_key: str, period: str) -> float:
    rows = dataset.frame[(dataset.frame["metric_key"] == metric_key) & (dataset.frame["period"] == period)]
    return float(rows["primary_value"].mean())


def guardrail_mean(dataset: Dataset, metric_key: str, period: str) -> float:
    rows = dataset.frame[(dataset.frame["metric_key"] == metric_key) & (dataset.frame["period"] == period)]
    return float(rows["guardrail_value"].mean())
