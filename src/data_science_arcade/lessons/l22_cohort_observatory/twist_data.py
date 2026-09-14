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
# Back when it was the newest cohort, its month-1 number (75%) was a real,
# true rate - not an artifact, not inflated, exactly as real as May's own
# 76% is right now. It simply didn't guarantee anything about month 5: a
# cohort that leads at one horizon can trail at another. By month 5, once
# fully observed, November settled at 38% - worse than January's own 46%,
# the cohort it once appeared to be beating. The lesson is never "the
# early number was fake" - it's that month-1 superiority and month-5
# superiority are different claims, and only one of them was actually
# being measured back when November was new.
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


def november_retention_mirror_code(month: int, var_name: str) -> str:
    """Deliberately its own dataset variable (`november_cohort`, never
    `cohorts`) and its own var_name namespace - never allowed to mutate or
    redefine anything the main May-vs-January comparison already
    computed."""
    return "\n".join(
        (
            f'{var_name}_row = november_cohort[november_cohort["month"] == {month}].iloc[0]',
            f'{var_name} = float({var_name}_row["active_count"] / {var_name}_row["cohort_size"])',
        )
    )
