import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

COMPLAINTS_SCHEMA = Schema(
    columns=(
        ColumnSchema("quarter", "object"),
        ColumnSchema("complaints", "int64"),
        ColumnSchema("orders_this_quarter", "int64", description_key="lesson.l28.schema.orders_this_quarter"),
        ColumnSchema("lifetime_customers", "int64", description_key="lesson.l28.schema.lifetime_customers"),
    )
)

# A new NovaMart domain for mastery - no existing L28 dataset was left
# over to promote (the dual-axis spend/signups dataset is this lesson's
# own mandatory Twist, not available for mastery). Mirrors the main
# lesson's own returns case deliberately: lifetime_customers is fixed
# every quarter (90000), so the flawed rate essentially just tracks raw
# complaint counts - and, like the returns case, the wrong denominator
# doesn't just scale the numbers, it changes which quarter looks best.
# Fair rate's own minimum (Q3) and flawed rate's own minimum (Q4) land on
# genuinely different quarters, verified via script.
COMPLAINTS_ROWS = [
    ("Q1", 45, 3000, 90000),
    ("Q2", 50, 2000, 90000),
    ("Q3", 38, 3800, 90000),
    ("Q4", 36, 2400, 90000),
]


def generate_complaints_data() -> Dataset:
    frame = pd.DataFrame(COMPLAINTS_ROWS, columns=["quarter", "complaints", "orders_this_quarter", "lifetime_customers"])
    step = PipelineStep("collected", python_code="complaints = pd.read_csv('novamart_quarterly_complaints.csv')")
    return Dataset(name="novamart_quarterly_complaints", frame=frame, schema=COMPLAINTS_SCHEMA, history=(step,))


def fair_complaint_rate(dataset: Dataset, quarter: str) -> float:
    row = dataset.frame[dataset.frame["quarter"] == quarter].iloc[0]
    return float(row["complaints"] / row["orders_this_quarter"])


def flawed_complaint_rate(dataset: Dataset, quarter: str) -> float:
    row = dataset.frame[dataset.frame["quarter"] == quarter].iloc[0]
    return float(row["complaints"] / row["lifetime_customers"])


def fair_rate_minimum_quarter_number(dataset: Dataset) -> float:
    frame = dataset.frame
    fair_rate = frame["complaints"] / frame["orders_this_quarter"]
    quarter_label = frame.loc[fair_rate.idxmin(), "quarter"]
    return float(quarter_label[1:])


def flawed_rate_minimum_quarter_number(dataset: Dataset) -> float:
    frame = dataset.frame
    flawed_rate = frame["complaints"] / frame["lifetime_customers"]
    quarter_label = frame.loc[flawed_rate.idxmin(), "quarter"]
    return float(quarter_label[1:])


def rate_minimum_quarter_mirror_code(denominator_column: str, var_name: str) -> str:
    """FINAL {var_name} is the same 1-indexed quarter number the two
    functions above return - verified via direct exec ("orders_this_
    quarter" -> 3.0, "lifetime_customers" -> 4.0)."""
    return "\n".join(
        (
            f'{var_name}_rate = complaints["complaints"] / complaints["{denominator_column}"]',
            f'{var_name}_label = complaints.loc[{var_name}_rate.idxmin(), "quarter"]',
            f"{var_name} = float({var_name}_label[1:])",
        )
    )
