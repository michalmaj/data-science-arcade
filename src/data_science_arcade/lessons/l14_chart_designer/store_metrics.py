import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

STORE_REVENUE_SCHEMA = Schema(columns=(ColumnSchema("store_id", "object"), ColumnSchema("revenue", "float64")))
DAILY_REVENUE_SCHEMA = Schema(columns=(ColumnSchema("day", "object"), ColumnSchema("revenue", "float64")))
RETURNS_SCHEMA = Schema(
    columns=(
        ColumnSchema("store_id", "object"),
        ColumnSchema("returns", "int64"),
        ColumnSchema("orders", "int64"),
    )
)

# Hand-crafted (not random): three independent small series, each sized
# for exactly one request's correct chart type/scale, plus a fourth
# (orders, alongside returns) that stays hidden until the twist.
STORE_REVENUE = {"S01": 4000.0, "S02": 6000.0, "S03": 5000.0}
DAILY_REVENUE = {"Mon": 500.0, "Tue": 200.0, "Wed": 520.0, "Thu": 510.0, "Fri": 530.0}

# Store S01 has the fewest raw returns but the fewest orders too - its
# return RATE is actually the worst of the three. Store S02 has the most
# raw returns but by far the most orders - its rate is the best. A chart
# of raw counts alone (this lesson's request 3) tells the opposite story
# from a chart of rates (the twist).
STORE_RETURNS = {"S01": 5, "S02": 15, "S03": 8}
STORE_ORDERS = {"S01": 20, "S02": 500, "S03": 100}


def generate_store_revenue() -> Dataset:
    frame = pd.DataFrame(list(STORE_REVENUE.items()), columns=["store_id", "revenue"])
    step = PipelineStep("collected", python_code="revenue = pd.read_csv('novamart_store_revenue.csv')")
    return Dataset(name="store_revenue", frame=frame, schema=STORE_REVENUE_SCHEMA, history=(step,))


def generate_daily_revenue() -> Dataset:
    frame = pd.DataFrame(list(DAILY_REVENUE.items()), columns=["day", "revenue"])
    step = PipelineStep("collected", python_code="revenue = pd.read_csv('novamart_daily_revenue.csv')")
    return Dataset(name="daily_revenue", frame=frame, schema=DAILY_REVENUE_SCHEMA, history=(step,))


def generate_returns() -> Dataset:
    rows = [(store_id, STORE_RETURNS[store_id], STORE_ORDERS[store_id]) for store_id in STORE_RETURNS]
    frame = pd.DataFrame(rows, columns=["store_id", "returns", "orders"])
    step = PipelineStep("collected", python_code="returns = pd.read_csv('novamart_store_returns.csv')")
    return Dataset(name="returns", frame=frame, schema=RETURNS_SCHEMA, history=(step,))


def return_rate(dataset: Dataset, store_id: str) -> float:
    row = dataset.frame.loc[dataset.frame["store_id"] == store_id].iloc[0]
    return float(row["returns"]) / float(row["orders"])
