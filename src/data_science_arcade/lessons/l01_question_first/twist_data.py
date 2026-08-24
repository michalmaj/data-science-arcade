import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "int64"),
        ColumnSchema("order_date", "datetime64[ns]"),
    )
)

REFERENCE_DATE = pd.Timestamp("2024-12-31")
RECENT_WINDOW_START = REFERENCE_DATE - pd.Timedelta(days=30)
TOTAL_CUSTOMERS = 20


def _order_rows() -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    # Customers 1-5: a repeat purchase both across the year AND within the
    # last 30 days.
    for customer_id in range(1, 6):
        rows += [
            (customer_id, "2024-03-15"),
            (customer_id, "2024-12-05"),
            (customer_id, "2024-12-20"),
        ]
    # Customers 6-12: a repeat purchase across the year, but not recently -
    # their second order happened months ago.
    for customer_id in range(6, 13):
        rows += [(customer_id, "2024-02-10"), (customer_id, "2024-07-22")]
    # Customers 13-20: only ever ordered once, all year.
    for customer_id in range(13, 21):
        rows += [(customer_id, "2024-05-01")]
    return rows


def generate_twist_orders() -> Dataset:
    """A small, hand-crafted (not random) order history: exactly 12 of 20
    customers repeat-purchase somewhere across the year, but only 5 of them
    do so within the last 30 days - by construction, not by chance, so the
    lesson's twist is guaranteed rather than hoping a seed lands right."""
    frame = pd.DataFrame(_order_rows(), columns=["customer_id", "order_date"])
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    step = PipelineStep(
        "prepared",
        python_code="orders = pd.read_csv('novamart_orders.csv', parse_dates=['order_date'])",
    )
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA, history=(step,))


def repeat_purchase_rate(dataset: Dataset, window_start: pd.Timestamp | None) -> float:
    """Fraction of all customers with 2+ orders in the window (None = all
    time). window_start filters rows before counting, so a customer with
    orders both inside and outside the window may only count as a repeat
    when the window is wide enough to include both."""
    frame = dataset.frame
    if window_start is not None:
        frame = frame[frame["order_date"] >= window_start]
    order_counts = frame.groupby("customer_id").size()
    repeat_customers = int((order_counts >= 2).sum())
    return repeat_customers / TOTAL_CUSTOMERS
