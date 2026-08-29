import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

SATISFACTION_SCHEMA = Schema(
    columns=(
        ColumnSchema("quarter", "object"),
        ColumnSchema("satisfaction_score", "float64"),
    )
)

ACTIVE_USERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("month", "object"),
        ColumnSchema("month_index", "int64", description="1-12, for ordering"),
        ColumnSchema("active_users", "int64"),
    )
)

RETURNS_SCHEMA = Schema(
    columns=(
        ColumnSchema("quarter", "object"),
        ColumnSchema("units_sold", "int64"),
        ColumnSchema("returns", "int64"),
        ColumnSchema("total_customers", "int64", description="Cumulative registered customers - irrelevant as a returns denominator"),
    )
)

# A real, modest improvement over the year - hand-crafted, not random.
SATISFACTION_ROWS = [("Q1", 72.0), ("Q2", 73.0), ("Q3", 74.0), ("Q4", 75.0)]

# A real decline through most of the year with a genuine late recovery -
# the full year tells a nuanced story; either 2-month slice alone tells a
# dramatically different, incomplete one.
ACTIVE_USERS_ROWS = [
    ("Jan", 1, 10000), ("Feb", 2, 9800), ("Mar", 3, 9600), ("Apr", 4, 9500),
    ("May", 5, 9400), ("Jun", 6, 9300), ("Jul", 7, 9200), ("Aug", 8, 9100),
    ("Sep", 9, 9000), ("Oct", 10, 8900), ("Nov", 11, 9400), ("Dec", 12, 10200),
]

# total_customers is a large, fixed, cumulative base - real, but the
# wrong denominator for a *rate of returns among units actually sold*.
RETURNS_ROWS = [
    ("Q1", 1800, 270, 50000),
    ("Q2", 2000, 320, 50000),
    ("Q3", 2200, 286, 50000),
    ("Q4", 2400, 408, 50000),
]


def generate_satisfaction_data() -> Dataset:
    frame = pd.DataFrame(SATISFACTION_ROWS, columns=["quarter", "satisfaction_score"])
    step = PipelineStep("collected", python_code="satisfaction = pd.read_csv('novamart_quarterly_satisfaction.csv')")
    return Dataset(name="novamart_quarterly_satisfaction", frame=frame, schema=SATISFACTION_SCHEMA, history=(step,))


def generate_active_users_data() -> Dataset:
    frame = pd.DataFrame(ACTIVE_USERS_ROWS, columns=["month", "month_index", "active_users"])
    step = PipelineStep("collected", python_code="active_users = pd.read_csv('novamart_monthly_active_users.csv')")
    return Dataset(name="novamart_monthly_active_users", frame=frame, schema=ACTIVE_USERS_SCHEMA, history=(step,))


def generate_returns_data() -> Dataset:
    frame = pd.DataFrame(RETURNS_ROWS, columns=["quarter", "units_sold", "returns", "total_customers"])
    step = PipelineStep("collected", python_code="returns = pd.read_csv('novamart_quarterly_returns.csv')")
    return Dataset(name="novamart_quarterly_returns", frame=frame, schema=RETURNS_SCHEMA, history=(step,))


def fair_return_rate(dataset: Dataset, quarter: str) -> float:
    row = dataset.frame[dataset.frame["quarter"] == quarter].iloc[0]
    return float(row["returns"] / row["units_sold"])


def flawed_return_rate(dataset: Dataset, quarter: str) -> float:
    row = dataset.frame[dataset.frame["quarter"] == quarter].iloc[0]
    return float(row["returns"] / row["total_customers"])
