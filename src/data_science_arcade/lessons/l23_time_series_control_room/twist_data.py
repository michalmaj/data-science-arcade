import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

DELIVERY_ALERT_SCHEMA = Schema(
    columns=(
        ColumnSchema("day_label", "object"),
        ColumnSchema("orders", "int64"),
        ColumnSchema("on_time_count", "int64"),
    )
)

# A different NovaMart KPI, a different quarter: on-time delivery rate.
# The day after any public holiday always shows this same dip - the
# courier network runs a backlog the day after a holiday, every time -
# not a one-off system failure, and it clears on its own within two days
# with nobody changing anything.
DELIVERY_ALERT_ROWS = [
    ("day_after_spring_holiday", 1000, 710),
    ("normal_weekday", 1000, 890),
    ("day_after_autumn_holiday", 1000, 700),
    ("two_days_after_spring_holiday", 1000, 880),
]


def generate_delivery_alert_data() -> Dataset:
    frame = pd.DataFrame(DELIVERY_ALERT_ROWS, columns=["day_label", "orders", "on_time_count"])
    step = PipelineStep("collected", python_code="delivery_alert = pd.read_csv('novamart_delivery_holiday_alert.csv')")
    return Dataset(name="novamart_delivery_holiday_alert", frame=frame, schema=DELIVERY_ALERT_SCHEMA, history=(step,))


def on_time_rate(dataset: Dataset, day_label: str) -> float:
    row = dataset.frame[dataset.frame["day_label"] == day_label].iloc[0]
    return float(row["on_time_count"] / row["orders"])
