import numpy as np
import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

REGIONS = ("North", "South", "East", "West", "Central")
PLANS = ("Free", "Plus", "Premium")
PLAN_WEIGHTS = (0.5, 0.3, 0.2)

CUSTOMERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "int64", description="Unique customer identifier"),
        ColumnSchema("signup_date", "datetime64[ns]", description="Date the account was created"),
        ColumnSchema("region", "string", description="NovaMart operating region"),
        ColumnSchema("plan", "string", description="Subscription plan at signup"),
    )
)


def generate_customers(seed: int, count: int = 500) -> Dataset:
    """Deterministic synthetic customers table. Same seed + count always
    produces the exact same data - see spec §14.3/§23.4."""
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "customer_id": np.arange(1, count + 1),
            "signup_date": pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 365, count), unit="D"),
            "region": pd.array(rng.choice(REGIONS, count), dtype="string"),
            "plan": pd.array(rng.choice(PLANS, count, p=PLAN_WEIGHTS), dtype="string"),
        }
    )
    return Dataset(name="customers", frame=frame, schema=CUSTOMERS_SCHEMA, history=("generated",))
