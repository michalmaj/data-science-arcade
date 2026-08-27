import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

CUSTOMERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "object"),
        ColumnSchema("name", "object"),
    )
)
ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "int64"),
        ColumnSchema("customer_id", "object"),
        ColumnSchema("revenue", "float64"),
    )
)

# Hand-crafted (not random): customers and orders that only partially
# overlap on customer_id, on both sides at once - not the tidy
# every-order-has-a-customer, every-customer-has-an-order case a demo
# would default to. 6 customers place exactly one order each. 2 more
# customers (C07, C08) have never ordered - unmatched if you keep every
# customer. 3 orders reference a customer_id that isn't in the customer
# table at all (a signup that never completed, a data entry slip) -
# unmatched if you keep every order. Inner/left/right joins on the same
# two tables genuinely disagree about how many rows come back: 6/9/8.
MATCHED_CUSTOMERS = [(f"C{i:02d}", f"Customer {i:02d}") for i in range(1, 7)]
UNORDERED_CUSTOMERS = [("C07", "Customer 07"), ("C08", "Customer 08")]
MATCHED_REVENUE = {"C01": 80.0, "C02": 50.0, "C03": 30.0, "C04": 60.0, "C05": 40.0, "C06": 90.0}
ORPHAN_ORDER_CUSTOMER_IDS = ["C97", "C98", "C99"]
ORPHAN_REVENUE = 20.0


def generate_customers() -> Dataset:
    rows = MATCHED_CUSTOMERS + UNORDERED_CUSTOMERS
    frame = pd.DataFrame(rows, columns=["customer_id", "name"])
    step = PipelineStep("collected", python_code="customers = pd.read_csv('novamart_customers.csv')")
    return Dataset(name="customers", frame=frame, schema=CUSTOMERS_SCHEMA, history=(step,))


def generate_orders() -> Dataset:
    rows: list[tuple[int, str, float]] = []
    order_id = 1
    for customer_id, revenue in MATCHED_REVENUE.items():
        rows.append((order_id, customer_id, revenue))
        order_id += 1
    for customer_id in ORPHAN_ORDER_CUSTOMER_IDS:
        rows.append((order_id, customer_id, ORPHAN_REVENUE))
        order_id += 1
    frame = pd.DataFrame(rows, columns=["order_id", "customer_id", "revenue"])
    step = PipelineStep("collected", python_code="orders = pd.read_csv('novamart_orders.csv')")
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA, history=(step,))


def row_count_for(orders: Dataset, customers: Dataset, how: str) -> int:
    merged = orders.frame.merge(customers.frame, on="customer_id", how=how)
    return len(merged)
