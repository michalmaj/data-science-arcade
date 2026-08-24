import numpy as np
import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "int64", description="Unique order identifier"),
        ColumnSchema("customer_id", "int64", description="Customer who placed the order (see customers table)"),
        ColumnSchema("order_date", "datetime64[ns]", description="Date the order was placed"),
        ColumnSchema("revenue", "float64", description="Order revenue in the local currency"),
    )
)


def generate_orders(seed: int, customers: Dataset, count: int = 2000) -> Dataset:
    """Deterministic synthetic orders table. Every customer_id is drawn from
    an existing customers Dataset, so a plain inner join between the two
    always matches every row - referential integrity holds by construction.
    Lesson-specific data-quality issues (spec §62) get layered on later by
    whichever lesson wants to teach them, not baked into this shared
    generator."""
    rng = np.random.default_rng(seed)
    customer_ids = customers.frame["customer_id"].to_numpy()
    frame = pd.DataFrame(
        {
            "order_id": np.arange(1, count + 1),
            "customer_id": rng.choice(customer_ids, count),
            "order_date": pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 365, count), unit="D"),
            "revenue": rng.gamma(shape=2.0, scale=25.0, size=count).round(2),
        }
    )
    step = PipelineStep(
        "generated",
        python_code=f"orders = generate_orders(seed={seed}, customers=customers, count={count})  # synthetic",
    )
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA, history=(step,))
