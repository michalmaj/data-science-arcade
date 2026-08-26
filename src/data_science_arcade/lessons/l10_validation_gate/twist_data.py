import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "int64"),
        ColumnSchema("recorded_amount", "float64", description="As stored in the feed - unit not verified"),
        ColumnSchema("true_amount_usd", "float64", description="Hidden ground truth - never shown during play"),
    )
)

# Hand-crafted (not random): 200 orders that pass every one of the 6
# standard checks - unique IDs, amounts within a sane range, no excess
# nulls, valid customer references, a fresh timestamp, valid status
# categories. But 50 of them were exported by a system that records cents,
# not dollars, and nothing downstream caught it - "15000" reads as a
# perfectly plausible large order, not a $150 order off by 100x.
NORMAL_ORDERS = 150
NORMAL_AMOUNT = 150.0
CENTS_MISTAKE_ORDERS = 50
CENTS_MISTAKE_RECORDED = 15_000.0  # actually 150.00 in cents, mis-stored as if dollars


def _rows() -> list[tuple[int, float, float]]:
    rows: list[tuple[int, float, float]] = []
    order_id = 1
    for _ in range(NORMAL_ORDERS):
        rows.append((order_id, NORMAL_AMOUNT, NORMAL_AMOUNT))
        order_id += 1
    for _ in range(CENTS_MISTAKE_ORDERS):
        rows.append((order_id, CENTS_MISTAKE_RECORDED, CENTS_MISTAKE_RECORDED / 100))
        order_id += 1
    return rows


def generate_orders_feed() -> Dataset:
    frame = pd.DataFrame(_rows(), columns=["order_id", "recorded_amount", "true_amount_usd"])
    step = PipelineStep(
        "validated",
        python_code="orders = pd.read_csv('novamart_daily_orders.csv')  # passed uniqueness/range/null/FK/freshness/category checks",
    )
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA, history=(step,))


def naive_average(dataset: Dataset) -> float:
    """What the feed appears to average, taking every recorded_amount at
    face value - exactly what "passed every check" leaves you with."""
    return float(dataset.frame["recorded_amount"].mean())


def true_average(dataset: Dataset) -> float:
    return float(dataset.frame["true_amount_usd"].mean())
