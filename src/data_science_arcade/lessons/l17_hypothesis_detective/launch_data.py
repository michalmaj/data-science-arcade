import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

LAUNCH_SCHEMA = Schema(
    columns=(
        ColumnSchema("period", "object", description="'before' or 'after' one-click reorder shipped"),
        ColumnSchema("week", "int64"),
        ColumnSchema("repeat_purchase_rate", "float64"),
        ColumnSchema("average_order_value", "float64"),
        ColumnSchema("support_contact_rate", "float64"),
    )
)

# Hand-crafted (not random) weekly observations, two weeks before and two
# weeks after NovaMart shipped one-click reorder - before/after values used
# anywhere in this lesson are real pandas means over these rows, not
# hand-picked headline numbers, even though the scenario itself (what a
# team would observe after a launch) is a designed simulation rather than
# a historical fact.
LAUNCH_ROWS = [
    ("before", 1, 0.22, 57.00, 0.058),
    ("before", 2, 0.26, 59.00, 0.062),
    ("after", 1, 0.32, 50.00, 0.061),
    ("after", 2, 0.36, 52.00, 0.063),
]


def generate_launch_data() -> Dataset:
    frame = pd.DataFrame(LAUNCH_ROWS, columns=["period", "week", "repeat_purchase_rate", "average_order_value", "support_contact_rate"])
    step = PipelineStep("collected", python_code="launch_impact = pd.read_csv('novamart_launch_impact.csv')")
    return Dataset(name="launch_impact", frame=frame, schema=LAUNCH_SCHEMA, history=(step,))


def metric_mean(dataset: Dataset, column: str, period: str) -> float:
    rows = dataset.frame[dataset.frame["period"] == period]
    return float(rows[column].mean())
