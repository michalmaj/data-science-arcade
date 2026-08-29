import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

APP_UPDATE_SCHEMA = Schema(
    columns=(
        ColumnSchema("metric", "object"),
        ColumnSchema("before_value", "float64"),
        ColumnSchema("after_value", "float64"),
    )
)

# A different NovaMart brief, a different quarter: marketing led with
# "app downloads spiked 500% this week" to justify a UI investment - a
# real number, driven entirely by an unrelated App Store feature. The
# metric that actually mattered for whether the UI change worked
# (session length) barely moved and never made the brief.
APP_UPDATE_ROWS = [
    ("app_downloads", 2000.0, 12000.0),
    ("session_length_minutes", 4.2, 4.3),
]


def generate_app_update_data() -> Dataset:
    frame = pd.DataFrame(APP_UPDATE_ROWS, columns=["metric", "before_value", "after_value"])
    step = PipelineStep("collected", python_code="app_update = pd.read_csv('novamart_app_update_brief.csv')")
    return Dataset(name="novamart_app_update_brief", frame=frame, schema=APP_UPDATE_SCHEMA, history=(step,))


def percent_change(dataset: Dataset, metric: str) -> float:
    row = dataset.frame[dataset.frame["metric"] == metric].iloc[0]
    return float((row["after_value"] - row["before_value"]) / row["before_value"])
