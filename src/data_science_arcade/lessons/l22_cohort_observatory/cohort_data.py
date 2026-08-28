import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.cohort import CohortMatrix, CohortRow

COHORT_RETENTION_SCHEMA = Schema(
    columns=(
        ColumnSchema("cohort_key", "object"),
        ColumnSchema("cohort_order", "int64", description="0 = oldest cohort"),
        ColumnSchema("month", "int64", description="months since that cohort's own acquisition"),
        ColumnSchema("cohort_size", "int64"),
        ColumnSchema("active_count", "int64"),
    )
)

_COHORT_LABEL_KEYS = {
    "jan": "lesson.l22.cohort.jan",
    "feb": "lesson.l22.cohort.feb",
    "mar": "lesson.l22.cohort.mar",
    "apr": "lesson.l22.cohort.apr",
    "may": "lesson.l22.cohort.may",
}
COHORT_ORDER = ("jan", "feb", "mar", "apr", "may")

# Five real NovaMart Plus acquisition cohorts (hand-crafted, not random),
# observed as of the end of the "May" cohort's first month - a genuinely
# triangular matrix, exactly like a real retention report: the newer a
# cohort, the fewer months it has actually had a chance to churn in.
# Every cohort's month-0 is trivially 100% (everyone who joined this
# month is still "in" this month) - the real signal starts at month 1.
# Real computed rates (active_count / cohort_size), not hand-picked
# headline numbers.
ROWS = [
    ("jan", 0, 0, 1000, 1000),
    ("jan", 0, 1, 1000, 680),
    ("jan", 0, 2, 1000, 580),
    ("jan", 0, 3, 1000, 520),
    ("jan", 0, 4, 1000, 480),
    ("jan", 0, 5, 1000, 460),
    ("feb", 1, 0, 1000, 1000),
    ("feb", 1, 1, 1000, 690),
    ("feb", 1, 2, 1000, 590),
    ("feb", 1, 3, 1000, 530),
    ("feb", 1, 4, 1000, 490),
    ("mar", 2, 0, 1000, 1000),
    ("mar", 2, 1, 1000, 720),
    ("mar", 2, 2, 1000, 600),
    ("mar", 2, 3, 1000, 540),
    ("apr", 3, 0, 1000, 1000),
    ("apr", 3, 1, 1000, 640),
    ("apr", 3, 2, 1000, 550),
    ("may", 4, 0, 1000, 1000),
    ("may", 4, 1, 1000, 760),
]


def generate_cohort_data() -> Dataset:
    frame = pd.DataFrame(ROWS, columns=["cohort_key", "cohort_order", "month", "cohort_size", "active_count"])
    step = PipelineStep("collected", python_code="cohorts = pd.read_csv('novamart_plus_cohort_retention.csv')")
    return Dataset(name="novamart_plus_cohort_retention", frame=frame, schema=COHORT_RETENTION_SCHEMA, history=(step,))


def retention_rate(dataset: Dataset, cohort_key: str, month: int) -> float:
    rows = dataset.frame[(dataset.frame["cohort_key"] == cohort_key) & (dataset.frame["month"] == month)]
    row = rows.iloc[0]
    return float(row["active_count"] / row["cohort_size"])


def build_cohort_matrix(dataset: Dataset) -> CohortMatrix:
    rows = []
    for cohort_key in COHORT_ORDER:
        cohort_frame = dataset.frame[dataset.frame["cohort_key"] == cohort_key].sort_values("month")
        months_observed = len(cohort_frame)
        retention = tuple(float(row.active_count / row.cohort_size) for row in cohort_frame.itertuples())
        rows.append(CohortRow(cohort_key, _COHORT_LABEL_KEYS[cohort_key], months_observed, retention))
    return CohortMatrix(rows=tuple(rows), month_count=max(row.months_observed for row in rows))
