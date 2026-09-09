import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Ground truth (hand-verified, hand-picked - not randomized) -----------
#
# NovaMart Retail's own order-level source: order_id, customer_id,
# store_id, order_date, revenue. 4 stores, 90 orders total, with two
# real, load-bearing properties, both independently re-verified via a
# real script during planning (see test_lesson12_data.py for the
# programmatic version of the same checks):
#
# 1. Very different store volumes AND a real repeat-heavy store (S02):
#    30 orders from just 6 real customers - the row-count-vs-nunique
#    trap for the `unique_customers` metric.
# 2. Real cross-store customer overlap: 8 customers order at more than
#    one store, so sum(per-store distinct customers) = 62 overcounts
#    the real network-wide distinct count of 54.
#
# order_date cycles through 7 real dates across all 90 orders - not for
# its own sake, but so a student who (wrongly) groups by order_date at
# the very first build step sees a REAL, different, path-aware grain
# consequence (7 date rows), not a canonical store table substituted in
# regardless of what they actually picked.

S01_STORE_ID = "S01"
S02_STORE_ID = "S02"
S03_STORE_ID = "S03"
S04_STORE_ID = "S04"

S01_REVENUE_PER_ORDER = 50.0
S02_REVENUE_PER_ORDER = 40.0
S03_REVENUE_PER_ORDER = 90.0
S04_REVENUE_PER_ORDER = 70.0

DATE_CYCLE = [f"2024-01-{day:02d}" for day in range(1, 8)]  # 7 real dates


def _s01_customers() -> list[str]:
    # 16 distinct (C1..C16), plus C1/C2 twice more - 20 orders, 16 distinct.
    return [f"C{i}" for i in range(1, 17)] + ["C1", "C2", "C1", "C2"]


def _s02_customers() -> list[str]:
    # The repeat-heavy trap store: 6 distinct customers, 5 orders each.
    values: list[str] = []
    for i in range(101, 107):
        values += [f"C{i}"] * 5
    return values


def _s03_customers() -> list[str]:
    # 12 distinct (C201..C212) plus 3 real cross-store customers already
    # seen at S01 (C1) and S02 (C101), plus C301 (S04-native, appearing
    # here first) - 15 orders, 15 distinct within S03's own frame.
    return [f"C{i}" for i in range(201, 213)] + ["C1", "C101", "C301"]


def _s04_customers() -> list[str]:
    # 20 distinct (C301..C320) plus 5 real cross-store customers already
    # seen at S01 (C2) and S02 (C102), and at S03 (C202, C203, C204) -
    # 25 orders, 25 distinct within S04's own frame.
    return [f"C{i}" for i in range(301, 321)] + ["C2", "C102", "C202", "C203", "C204"]


STORE_CUSTOMERS: dict[str, list[str]] = {
    S01_STORE_ID: _s01_customers(),
    S02_STORE_ID: _s02_customers(),
    S03_STORE_ID: _s03_customers(),
    S04_STORE_ID: _s04_customers(),
}
STORE_REVENUE_PER_ORDER: dict[str, float] = {
    S01_STORE_ID: S01_REVENUE_PER_ORDER,
    S02_STORE_ID: S02_REVENUE_PER_ORDER,
    S03_STORE_ID: S03_REVENUE_PER_ORDER,
    S04_STORE_ID: S04_REVENUE_PER_ORDER,
}

ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "string"),
        ColumnSchema("customer_id", "string"),
        ColumnSchema("store_id", "string"),
        ColumnSchema("order_date", "datetime64[ns]"),
        ColumnSchema("revenue", "float64"),
    )
)


def _rows() -> list[tuple[str, str, str, str, float]]:
    rows: list[tuple[str, str, str, str, float]] = []
    order_index = 0
    for store_id, customers in STORE_CUSTOMERS.items():
        for customer_id in customers:
            order_id = f"ORD-{order_index + 1:04d}"
            order_date = DATE_CYCLE[order_index % len(DATE_CYCLE)]
            rows.append((order_id, customer_id, store_id, order_date, STORE_REVENUE_PER_ORDER[store_id]))
            order_index += 1
    return rows


def generate_orders() -> Dataset:
    """The player-facing order-level feed - real, clean, no data-quality
    issues (this is a pure aggregation-semantics lesson, not a cleaning
    one)."""
    frame = pd.DataFrame(_rows(), columns=["order_id", "customer_id", "store_id", "order_date", "revenue"])
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    step = PipelineStep("collected", python_code="orders = pd.read_csv('novamart_orders.csv', parse_dates=['order_date'])")
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA, history=(step,))


def store_order_count(store_id: str) -> int:
    return len(STORE_CUSTOMERS[store_id])


def store_distinct_customers(store_id: str) -> int:
    return len(set(STORE_CUSTOMERS[store_id]))


def network_distinct_customers() -> int:
    all_customers: set[str] = set()
    for customers in STORE_CUSTOMERS.values():
        all_customers |= set(customers)
    return len(all_customers)


def sum_of_store_distinct_customers() -> int:
    return sum(store_distinct_customers(store_id) for store_id in STORE_CUSTOMERS)


def cross_store_customers() -> tuple[str, ...]:
    """Customers present at 2+ stores - the real, named root cause of
    sum(per-store distinct) overcounting the real network distinct
    count."""
    membership: dict[str, set[str]] = {}
    for store_id, customers in STORE_CUSTOMERS.items():
        for customer_id in set(customers):
            membership.setdefault(customer_id, set()).add(store_id)
    return tuple(sorted(c for c, stores in membership.items() if len(stores) > 1))


def store_revenue(store_id: str) -> float:
    return STORE_REVENUE_PER_ORDER[store_id] * store_order_count(store_id)


def total_revenue() -> float:
    return sum(store_revenue(store_id) for store_id in STORE_CUSTOMERS)


def total_orders() -> int:
    return sum(store_order_count(store_id) for store_id in STORE_CUSTOMERS)


def network_aov() -> float:
    return total_revenue() / total_orders()


def naive_mean_of_store_aovs() -> float:
    return sum(STORE_REVENUE_PER_ORDER.values()) / len(STORE_REVENUE_PER_ORDER)


def weighted_aov() -> float:
    return sum(STORE_REVENUE_PER_ORDER[s] * store_order_count(s) for s in STORE_CUSTOMERS) / total_orders()


def distinct_dates() -> int:
    return len(DATE_CYCLE)


# --- Optional mastery - marketing-channel attribution transfer ------------
#
# Different domain (not a repeated store name): a channel-level
# attribution log where the same customer can appear in multiple
# channels. Real, hand-verified numbers, same construction discipline
# as the main dataset.

CHANNEL_CONVERSIONS: dict[str, int] = {"email": 40, "social": 60, "search": 25}
CHANNEL_VALUE_PER_CONVERSION: dict[str, float] = {"email": 30.0, "social": 15.0, "search": 60.0}
"""social is the repeat-heavy channel (only 20 real distinct customers
across 60 conversions - retargeting churn), mirroring S02's own role in
the main dataset in a genuinely different setting."""
CHANNEL_DISTINCT_CUSTOMERS: dict[str, int] = {"email": 35, "social": 20, "search": 25}


def mastery_total_conversions() -> int:
    return sum(CHANNEL_CONVERSIONS.values())


def mastery_total_revenue() -> float:
    return sum(CHANNEL_CONVERSIONS[c] * CHANNEL_VALUE_PER_CONVERSION[c] for c in CHANNEL_CONVERSIONS)


def mastery_network_avg_value() -> float:
    return mastery_total_revenue() / mastery_total_conversions()


def mastery_naive_mean_of_channel_avgs() -> float:
    return sum(CHANNEL_VALUE_PER_CONVERSION.values()) / len(CHANNEL_VALUE_PER_CONVERSION)


def mastery_weighted_avg_value() -> float:
    return sum(CHANNEL_VALUE_PER_CONVERSION[c] * CHANNEL_CONVERSIONS[c] for c in CHANNEL_CONVERSIONS) / mastery_total_conversions()
