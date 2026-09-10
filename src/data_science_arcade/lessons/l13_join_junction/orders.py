import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Ground truth (hand-verified, hand-picked - not randomized) -----------
#
# NovaMart Retail again, a genuinely different problem shape from L12's own
# aggregation focus: three real tables - orders, customers, active_
# promotions. No hidden truth anywhere: nothing in any player-facing frame
# signals which rows are the trap - every fact below is either directly
# visible in the real columns or has to be computed.
#
# 100 customers, C001-C100, segmented by real order/promotion behavior:
#  - C001-C003 (3 customers): 1 order each, 1 active promotion each
#  - C004-C010 (7 customers): 1 order each, 2 active promotions each
#  - C011-C020 (10 customers): 1 order each, 3 active promotions each
#  - C021-C052 (32 customers): 1 order each, 0 promotions
#  - C053-C080 (28 customers): 2 orders each, 0 promotions
#  - C081-C100 (20 customers): 0 orders, 0 promotions
# Real orders from real customers: (3+7+10)*1 + 32*1 + 28*2 = 20+32+56 = 108.
# Plus 12 guest orders (C201-C212 - a real, ordinary scenario: checkout
# completed before account setup finished - never in `customers` at all,
# no special prefix, nothing that telegraphs "this is the trap") = 120
# orders total.
# active_promotions: 3+14+30 = 47 rows, over exactly 20 distinct customers
# (C001-C020) - a genuine one-to-many key from the promotions side, never
# entangled with Join 1's own clean one-to-many-from-customers shape.

GUEST_CUSTOMER_IDS = tuple(f"C{i:03d}" for i in range(201, 213))  # 12 guest orders
PROMO_CODES = (("SPRING10", 10.0), ("LOYALTY5", 5.0), ("FLASH20", 20.0))
"""A given promotion always carries the same discount_pct system-wide - a
customer with N active promotions is assigned the first N of these, so a
1-promo customer's own real promotion is always SPRING10, a 2-promo
customer's are SPRING10+LOYALTY5, and a 3-promo customer's are all three -
real, deterministic, never independently randomized per customer."""

# The one hand-picked customer used for the concrete "show real rows, not
# an aggregate" fan-out example - the first (and lowest-numbered, so it's
# easy to find in a real screenshot) of the 10 triple-promotion customers.
CONCRETE_EXAMPLE_CUSTOMER_ID = "C011"
CONCRETE_EXAMPLE_ORDER_ID = "O-0011"
CONCRETE_EXAMPLE_REVENUE = 85.0

CUSTOMERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "object"),
        ColumnSchema("name", "object"),
        ColumnSchema("signup_date", "datetime64[ns]"),
    )
)
ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "object"),
        ColumnSchema("customer_id", "object"),
        ColumnSchema("order_date", "datetime64[ns]"),
        ColumnSchema("revenue", "float64"),
    )
)
ACTIVE_PROMOTIONS_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "object"),
        ColumnSchema("promotion_code", "object"),
        ColumnSchema("discount_pct", "float64"),
    )
)

_DATE_CYCLE = [f"2024-02-{day:02d}" for day in range(1, 8)]  # 7 real dates, cycled


def _customer_segments() -> list[tuple[str, int, int]]:
    """(customer_id, real_order_count, active_promotion_count) for all 100
    customers - the single source of truth every generator below reads
    from, so the three tables can never quietly drift out of sync with
    each other."""
    segments: list[tuple[str, int, int]] = []
    for i in range(1, 4):
        segments.append((f"C{i:03d}", 1, 1))
    for i in range(4, 11):
        segments.append((f"C{i:03d}", 1, 2))
    for i in range(11, 21):
        segments.append((f"C{i:03d}", 1, 3))
    for i in range(21, 53):
        segments.append((f"C{i:03d}", 1, 0))
    for i in range(53, 81):
        segments.append((f"C{i:03d}", 2, 0))
    for i in range(81, 101):
        segments.append((f"C{i:03d}", 0, 0))
    return segments


CUSTOMER_SEGMENTS = _customer_segments()


def generate_customers() -> Dataset:
    rows = [
        (customer_id, f"Customer {customer_id[1:]}", _DATE_CYCLE[index % len(_DATE_CYCLE)])
        for index, (customer_id, _orders, _promos) in enumerate(CUSTOMER_SEGMENTS)
    ]
    frame = pd.DataFrame(rows, columns=["customer_id", "name", "signup_date"])
    frame["signup_date"] = pd.to_datetime(frame["signup_date"])
    step = PipelineStep("collected", python_code="customers = pd.read_csv('novamart_customers.csv', parse_dates=['signup_date'])")
    return Dataset(name="customers", frame=frame, schema=CUSTOMERS_SCHEMA, history=(step,))


def _order_revenue(order_index: int) -> float:
    return 40.0 + (order_index % 9) * 5.0


def generate_orders() -> Dataset:
    rows: list[tuple[str, str, str, float]] = []
    order_index = 0
    for customer_id, order_count, _promos in CUSTOMER_SEGMENTS:
        for _ in range(order_count):
            order_id = f"O-{order_index + 1:04d}"
            revenue = CONCRETE_EXAMPLE_REVENUE if customer_id == CONCRETE_EXAMPLE_CUSTOMER_ID else _order_revenue(order_index)
            order_date = _DATE_CYCLE[order_index % len(_DATE_CYCLE)]
            rows.append((order_id, customer_id, order_date, revenue))
            order_index += 1
    for guest_customer_id in GUEST_CUSTOMER_IDS:
        order_id = f"O-{order_index + 1:04d}"
        order_date = _DATE_CYCLE[order_index % len(_DATE_CYCLE)]
        rows.append((order_id, guest_customer_id, order_date, _order_revenue(order_index)))
        order_index += 1
    frame = pd.DataFrame(rows, columns=["order_id", "customer_id", "order_date", "revenue"])
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    step = PipelineStep("collected", python_code="orders = pd.read_csv('novamart_orders.csv', parse_dates=['order_date'])")
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA, history=(step,))


def generate_active_promotions() -> Dataset:
    rows: list[tuple[str, str, float]] = []
    for customer_id, _orders, promo_count in CUSTOMER_SEGMENTS:
        for code, discount_pct in PROMO_CODES[:promo_count]:
            rows.append((customer_id, code, discount_pct))
    frame = pd.DataFrame(rows, columns=["customer_id", "promotion_code", "discount_pct"])
    step = PipelineStep("collected", python_code="active_promotions = pd.read_csv('novamart_active_promotions.csv')")
    return Dataset(name="active_promotions", frame=frame, schema=ACTIVE_PROMOTIONS_SCHEMA, history=(step,))


# --- Real, hand-verified constants used by both the scenario and its tests

TOTAL_ORDERS = 120
MATCHED_ORDERS = 108
GUEST_ORDERS = 12
CUSTOMERS_TOTAL = 100
CUSTOMERS_WITH_ORDERS = 80
CUSTOMERS_NEVER_ORDERED = 20

# Join 1 (orders <-> customers on customer_id) - a clean one-to-many join
# from customers' own unique key; nothing multiplies here, only rows get
# kept or dropped.
JOIN1_INNER_ROW_COUNT = 108
JOIN1_LEFT_ROW_COUNT = 120
JOIN1_OUTER_ROW_COUNT = 140

# The promotions join (orders <-> active_promotions on customer_id) - a
# real one-to-many key from the promotions side (20 customers have 1-3
# rows each in active_promotions).
ACTIVE_PROMOTIONS_ROWS = 47
ACTIVE_PROMOTIONS_DISTINCT_CUSTOMERS = 20
ORDERS_DISTINCT_CUSTOMER_IDS = 92  # 80 real ordering customers + 12 guest ids
RAW_PROMO_JOIN_ROW_COUNT = 147  # 100 unmatched-once + 47 fan-out rows
REPAIRED_PROMO_JOIN_ROW_COUNT = 120  # back to orders' own real row count
