import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

ALERT_FATIGUE_SCHEMA = Schema(
    columns=(
        ColumnSchema("category", "object"),
        ColumnSchema("alert_count", "int64"),
        ColumnSchema("avg_response_minutes", "int64"),
    )
)

# A different NovaMart team, a different quarter: Warehouse Ops watched
# every metric it could with tight thresholds. 46 of the 47 alerts that
# month meant nothing, and everyone got fast at dismissing them - so when
# the one real incident finally fired, on the same over-alerted channel,
# it took six hours to notice instead of the usual eighteen minutes.
ALERT_FATIGUE_ROWS = [
    ("false_alarm", 46, 4),
    ("real_incident", 1, 360),
]


def generate_alert_fatigue_data() -> Dataset:
    frame = pd.DataFrame(ALERT_FATIGUE_ROWS, columns=["category", "alert_count", "avg_response_minutes"])
    step = PipelineStep("collected", python_code="alert_fatigue = pd.read_csv('novamart_warehouse_alert_fatigue.csv')")
    return Dataset(name="novamart_warehouse_alert_fatigue", frame=frame, schema=ALERT_FATIGUE_SCHEMA, history=(step,))


def alert_count(dataset: Dataset, category: str) -> int:
    row = dataset.frame[dataset.frame["category"] == category].iloc[0]
    return int(row["alert_count"])


def response_minutes(dataset: Dataset, category: str) -> float:
    row = dataset.frame[dataset.frame["category"] == category].iloc[0]
    return float(row["avg_response_minutes"])
