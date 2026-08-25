import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

PAGES_SCHEMA = Schema(
    columns=(
        ColumnSchema("page_number", "int64"),
        ColumnSchema("expected_count", "int64"),
        ColumnSchema("actual_count", "int64"),
    )
)

# Hand-crafted (not random): every page expects 20 records; page 4 silently
# returns fewer, with a 200 status - no error, just an incomplete payload.
EXPECTED_PER_PAGE = 20
ACTUAL_COUNTS = {1: 20, 2: 20, 3: 20, 4: 12, 5: 20}
SHORTFALL_PAGE = 4


def generate_page_completeness() -> Dataset:
    frame = pd.DataFrame(
        {
            "page_number": list(ACTUAL_COUNTS.keys()),
            "expected_count": [EXPECTED_PER_PAGE] * len(ACTUAL_COUNTS),
            "actual_count": list(ACTUAL_COUNTS.values()),
        }
    )
    step = PipelineStep(
        "prepared",
        python_code="pages = pd.DataFrame(request_log)  # one row per page actually received",
    )
    return Dataset(name="pages", frame=frame, schema=PAGES_SCHEMA, history=(step,))


def overall_completeness(dataset: Dataset) -> float:
    return dataset.frame["actual_count"].sum() / dataset.frame["expected_count"].sum()


def page_completeness(dataset: Dataset, page_number: int) -> float:
    row = dataset.frame[dataset.frame["page_number"] == page_number].iloc[0]
    return row["actual_count"] / row["expected_count"]
