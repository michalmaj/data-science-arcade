import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "int64"),
        ColumnSchema("customer_id", "object"),
        ColumnSchema("store_id", "object"),
        ColumnSchema("order_date", "datetime64[ns]"),
        ColumnSchema("revenue", "float64"),
    )
)

# Hand-crafted (not random): three stores, five order days, and a
# customer base where most customers order once but a few are repeat
# visitors - concentrated entirely in store S02, not spread evenly. That
# concentration is what makes "count of order rows" and "count of
# distinct customers" diverge sharply for one store but not the others.
STORE_REVENUE = {"S01": 80.0, "S02": 120.0, "S03": 200.0}
DAY_COUNT = 5

# (store_id, customer_ids) - repeats in the list mean repeat orders from
# the same customer. S01 and S03: one order per customer. S02: only 4
# distinct customers across all 10 orders.
STORE_CUSTOMERS: dict[str, list[str]] = {
    "S01": [f"C{i:02d}" for i in range(1, 11)],
    "S02": ["C11", "C11", "C11", "C12", "C12", "C12", "C13", "C13", "C14", "C14"],
    "S03": [f"C{i:02d}" for i in range(15, 20)],
}


def _rows() -> list[tuple[int, str, str, str, float]]:
    rows: list[tuple[int, str, str, str, float]] = []
    order_id = 1
    for store_id, customers in STORE_CUSTOMERS.items():
        for index, customer_id in enumerate(customers):
            day = f"2024-01-{index % DAY_COUNT + 1:02d}"
            rows.append((order_id, customer_id, store_id, day, STORE_REVENUE[store_id]))
            order_id += 1
    return rows


def generate_orders() -> Dataset:
    frame = pd.DataFrame(_rows(), columns=["order_id", "customer_id", "store_id", "order_date", "revenue"])
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    step = PipelineStep(
        "collected",
        python_code="orders = pd.read_csv('novamart_orders.csv', parse_dates=['order_date'])",
    )
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA, history=(step,))


def order_count_by_store(dataset: Dataset, store_id: str) -> int:
    """The naive count a groupby(store_id).size() gives - one per order
    row, not one per distinct customer."""
    frame = dataset.frame
    return int((frame["store_id"] == store_id).sum())


def distinct_customers_by_store(dataset: Dataset, store_id: str) -> int:
    frame = dataset.frame
    return int(frame.loc[frame["store_id"] == store_id, "customer_id"].nunique())
