import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

LOYALTY_LTV_SCHEMA = Schema(
    columns=(
        ColumnSchema("group", "object"),
        ColumnSchema("customer_count", "int64"),
        ColumnSchema("avg_ltv", "float64"),
    )
)

# A different NovaMart investigation, a different program: loyalty
# signups vs. customer lifetime value. The observational gap (people who
# chose to join vs. people who didn't) was huge - and NovaMart spent big
# on the program based on it. A later randomized test (a random subset
# actually invited, not self-selected) showed the program's own real
# effect was a small fraction of that gap - most of it was always just
# self-selection: customers who were already going to spend more were
# also more likely to sign up.
LOYALTY_LTV_ROWS = [
    ("observational_member", 5000, 340.0),
    ("observational_nonmember", 5000, 180.0),
    ("randomized_treatment", 2000, 195.0),
    ("randomized_control", 2000, 180.0),
]


def generate_loyalty_ltv_data() -> Dataset:
    frame = pd.DataFrame(LOYALTY_LTV_ROWS, columns=["group", "customer_count", "avg_ltv"])
    step = PipelineStep("collected", python_code="loyalty_ltv = pd.read_csv('novamart_loyalty_ltv_study.csv')")
    return Dataset(name="novamart_loyalty_ltv_study", frame=frame, schema=LOYALTY_LTV_SCHEMA, history=(step,))


def average_ltv(dataset: Dataset, group: str) -> float:
    row = dataset.frame[dataset.frame["group"] == group].iloc[0]
    return float(row["avg_ltv"])
