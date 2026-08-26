import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

FLAGGED_SCHEMA = Schema(
    columns=(
        ColumnSchema("transaction_id", "int64"),
        ColumnSchema("true_category", "object", description="fraud, legitimate, or unit_error - confirmed by hand"),
    )
)

# Hand-crafted (not random): 20 transactions a blanket "exclude anything
# over $20,000" rule flagged and threw out. Only a fraction are actually
# fraud - most are real enterprise orders the rule had no way to
# distinguish from fraud, plus a few fixable data-entry errors it
# discarded instead of correcting.
FRAUD_COUNT = 5
LEGITIMATE_COUNT = 12
UNIT_ERROR_COUNT = 3


def _rows() -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    transaction_id = 1
    for _ in range(FRAUD_COUNT):
        rows.append((transaction_id, "fraud"))
        transaction_id += 1
    for _ in range(LEGITIMATE_COUNT):
        rows.append((transaction_id, "legitimate"))
        transaction_id += 1
    for _ in range(UNIT_ERROR_COUNT):
        rows.append((transaction_id, "unit_error"))
        transaction_id += 1
    return rows


def generate_flagged_transactions() -> Dataset:
    frame = pd.DataFrame(_rows(), columns=["transaction_id", "true_category"])
    step = PipelineStep(
        "prepared",
        python_code="flagged = transactions[transactions['amount'] > 20_000]  # one global threshold, every category",
    )
    return Dataset(name="flagged", frame=frame, schema=FLAGGED_SCHEMA, history=(step,))


def category_rate(dataset: Dataset, category: str) -> float:
    return float((dataset.frame["true_category"] == category).mean())
