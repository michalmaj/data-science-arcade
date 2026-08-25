import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

CUSTOMERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "int64"),
        ColumnSchema("age_bracket", "string"),
        ColumnSchema("opted_in", "bool"),
    )
)

AGE_BRACKETS = ("18-34", "35-54", "55+")
BRACKET_SIZE = 30
# Opted-in counts per bracket, by construction (not random) - guarantees
# the twist's overall-vs-breakdown contrast every time: 90% / 60% / 30%
# by bracket, 60% overall, exactly.
OPTED_IN_COUNTS = {"18-34": 27, "35-54": 18, "55+": 9}


def _customer_rows() -> list[tuple[int, str, bool]]:
    rows: list[tuple[int, str, bool]] = []
    customer_id = 1
    for bracket in AGE_BRACKETS:
        opted_in_count = OPTED_IN_COUNTS[bracket]
        for position in range(BRACKET_SIZE):
            rows.append((customer_id, bracket, position < opted_in_count))
            customer_id += 1
    return rows


def generate_analytics_opt_in() -> Dataset:
    """A small, hand-crafted (not random) customer roster: 90 customers
    across three age brackets, with opt-in-to-tracking rates engineered so
    the overall rate (60%) looks fine but the per-bracket breakdown
    (90% / 60% / 30%) reveals a systematic skew toward younger customers."""
    frame = pd.DataFrame(_customer_rows(), columns=["customer_id", "age_bracket", "opted_in"])
    step = PipelineStep(
        "prepared",
        python_code="customers = pd.read_csv('app_analytics_opt_in.csv')",
    )
    return Dataset(name="customers", frame=frame, schema=CUSTOMERS_SCHEMA, history=(step,))


def opt_in_rate(dataset: Dataset, age_bracket: str | None) -> float:
    frame = dataset.frame
    if age_bracket is not None:
        frame = frame[frame["age_bracket"] == age_bracket]
    return frame["opted_in"].mean()
