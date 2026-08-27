import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.l13_join_junction.customers_orders import MATCHED_REVENUE

PROMOTIONS_SCHEMA = Schema(
    columns=(
        ColumnSchema("promotion_id", "int64"),
        ColumnSchema("customer_id", "object"),
        ColumnSchema("discount_pct", "int64"),
    )
)

# Hand-crafted (not random): most customers have exactly one active
# promotion, but C01 has three and C02 has two - a genuine many-to-many
# join key (an order's customer_id can match more than one promotion
# row), not a one-to-many the player already practiced. Joining orders
# to promotions on customer_id duplicates C01's and C02's order rows,
# so a naive .sum() over the joined table counts their revenue 3x and 2x
# respectively instead of once.
PROMOTION_COUNTS = {"C01": 3, "C02": 2, "C03": 1, "C04": 1, "C05": 1, "C06": 1}


def generate_promotions() -> Dataset:
    rows: list[tuple[int, str, int]] = []
    promotion_id = 1
    for customer_id, count in PROMOTION_COUNTS.items():
        for _ in range(count):
            rows.append((promotion_id, customer_id, 10))
            promotion_id += 1
    frame = pd.DataFrame(rows, columns=["promotion_id", "customer_id", "discount_pct"])
    step = PipelineStep("collected", python_code="promotions = pd.read_csv('novamart_promotions.csv')")
    return Dataset(name="promotions", frame=frame, schema=PROMOTIONS_SCHEMA, history=(step,))


def true_total_revenue() -> float:
    return float(sum(MATCHED_REVENUE.values()))


def naive_joined_revenue(orders: Dataset, promotions: Dataset) -> float:
    """What a naive .sum() gives after joining orders to promotions on
    customer_id and summing revenue over the joined table - each
    customer's order row is duplicated once per matching promotion, so
    C01's $80 order counts 3x and C02's $50 order counts 2x."""
    merged = orders.frame.merge(promotions.frame, on="customer_id", how="inner")
    return float(merged["revenue"].sum())
