import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

SPEND_SIGNUPS_SCHEMA = Schema(
    columns=(
        ColumnSchema("metric", "object"),
        ColumnSchema("start_value", "float64"),
        ColumnSchema("end_value", "float64"),
    )
)

# A different NovaMart chart, a different team: marketing spend and
# sign-ups plotted on a dual-axis chart, scaled so the two lines traced
# nearly the same shape - every dollar looked like it was buying a
# sign-up. Real numbers, in their own terms, tell a very different story.
SPEND_SIGNUPS_ROWS = [
    ("marketing_spend", 40000.0, 74000.0),
    ("signups", 1000.0, 1120.0),
]


def generate_spend_signups_data() -> Dataset:
    frame = pd.DataFrame(SPEND_SIGNUPS_ROWS, columns=["metric", "start_value", "end_value"])
    step = PipelineStep("collected", python_code="spend_signups = pd.read_csv('novamart_dual_axis_spend_signups.csv')")
    return Dataset(name="novamart_dual_axis_spend_signups", frame=frame, schema=SPEND_SIGNUPS_SCHEMA, history=(step,))


def percent_change(dataset: Dataset, metric: str) -> float:
    row = dataset.frame[dataset.frame["metric"] == metric].iloc[0]
    return float((row["end_value"] - row["start_value"]) / row["start_value"])
