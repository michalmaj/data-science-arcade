import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

NOVEMBER_COHORT_SCHEMA = Schema(
    columns=(
        ColumnSchema("month", "int64"),
        ColumnSchema("cohort_size", "int64"),
        ColumnSchema("active_count", "int64"),
    )
)

# The November cohort - fully mature now, unlike May in the main matrix.
# Back when it was the newest cohort, its month-1 number (75%) looked like
# a clear win over every older cohort at the time, the same way May's 76%
# looks exciting right now. It just hadn't had time to churn yet: by
# month 5, once fully observed, it settled at 38% - worse than January's
# eventual 46%, the cohort it once appeared to be beating.
NOVEMBER_ROWS = [
    (0, 1000, 1000),
    (1, 1000, 750),
    (2, 1000, 570),
    (3, 1000, 490),
    (4, 1000, 420),
    (5, 1000, 380),
]


def generate_november_cohort_data() -> Dataset:
    frame = pd.DataFrame(NOVEMBER_ROWS, columns=["month", "cohort_size", "active_count"])
    step = PipelineStep("collected", python_code="november_cohort = pd.read_csv('novamart_plus_november_cohort.csv')")
    return Dataset(name="november_cohort", frame=frame, schema=NOVEMBER_COHORT_SCHEMA, history=(step,))


def november_retention_rate(dataset: Dataset, month: int) -> float:
    row = dataset.frame[dataset.frame["month"] == month].iloc[0]
    return float(row["active_count"] / row["cohort_size"])
