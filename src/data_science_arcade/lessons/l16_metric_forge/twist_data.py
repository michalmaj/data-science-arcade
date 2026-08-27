import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

CHURN_SCHEMA = Schema(
    columns=(
        ColumnSchema("period", "object"),
        ColumnSchema("week", "int64"),
        ColumnSchema("churn_rate", "float64"),
    )
)

# Hand-crafted weekly churn rate, four weeks before and four weeks after
# support adopted quick_close_share as its official target - a metric
# nobody was tracking during the guided/independent investigation (which
# only ever showed CSAT as the guardrail). The real cost shows up a layer
# further out than the guardrail already checked.
CHURN_ROWS = [
    ("before", 1, 0.04),
    ("before", 2, 0.05),
    ("before", 3, 0.06),
    ("before", 4, 0.05),
    ("after", 1, 0.16),
    ("after", 2, 0.19),
    ("after", 3, 0.18),
    ("after", 4, 0.19),
]


def generate_churn_data() -> Dataset:
    frame = pd.DataFrame(CHURN_ROWS, columns=["period", "week", "churn_rate"])
    step = PipelineStep("collected", python_code="churn = pd.read_csv('novamart_support_churn.csv')")
    return Dataset(name="support_churn", frame=frame, schema=CHURN_SCHEMA, history=(step,))


def churn_mean(dataset: Dataset, period: str) -> float:
    return float(dataset.frame.loc[dataset.frame["period"] == period, "churn_rate"].mean())
