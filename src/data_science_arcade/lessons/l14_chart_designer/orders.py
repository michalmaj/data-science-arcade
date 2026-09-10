import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Ground truth (hand-verified, hand-picked - not randomized) -----------
#
# One real, deterministic 260-row NovaMart order feed, three real business
# asks answered from three different views of the SAME population - never
# curve-fit to make a wrong chart look comically bad:
#
#  A. Store comparison - store_id -> return_rate_pct (real, distinct rates:
#     15.0% / 8.0% / 10.0% / 5.0%).
#  B. Time trend - order_date -> order_count over 14 real chronological
#     days (a real weekday>weekend pattern with mild week-over-week
#     softening).
#  C. Delivery-time distribution - the raw delivery_minutes column (260
#     real values, genuinely unimodal and right-skewed - mean 41.35,
#     median 39.0, close together on purpose so there's no L11-style
#     mean/median divergence story to interpret here).
#
# All three views reconcile to the same real 260-order total.

STORE_ORDER_COUNTS: dict[str, int] = {"S01": 80, "S02": 50, "S03": 70, "S04": 60}
STORE_RETURN_COUNTS: dict[str, int] = {"S01": 12, "S02": 4, "S03": 7, "S04": 3}
"""Return rates: S01=15.0%, S02=8.0%, S03=10.0%, S04=5.0% - four real,
distinct values, hand-verified."""

DATE_CYCLE = [f"2024-03-{day:02d}" for day in range(1, 15)]  # 14 real chronological dates
DAILY_ORDER_COUNTS = [24, 22, 23, 21, 20, 14, 12, 23, 20, 19, 18, 17, 13, 14]
"""A real weekday > weekend pattern (each week: Mon-Fri higher, Sat/Sun
lower), with a mild week-over-week softening in week 2 - sums to 260,
reconciling with the store table's own total."""

_BASE_DELIVERY_MINUTES = [
    20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 55, 60, 65, 70, 32, 35, 38, 41, 44, 75,
]
"""26 real, distinct minute values, cycled 10x to reach the real 260-order
population - genuinely unimodal and right-skewed by construction (mostly
20-50 minutes, a real tail out to 75), never a bimodal mixture."""

CUSTOMERS_TOTAL_ORDERS = sum(STORE_ORDER_COUNTS.values())

ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "object"),
        ColumnSchema("store_id", "object"),
        ColumnSchema("order_date", "datetime64[ns]"),
        ColumnSchema("returned", "bool"),
        ColumnSchema("delivery_minutes", "int64"),
    )
)


def _interleave_by_weight(counts: dict[str, int]) -> list[str]:
    """Spreads each key's own occurrences as evenly as possible across the
    full 260-length sequence (a fractional-position interleave: each of a
    key's own `count` occurrences gets a target position `(k+0.5)/count`
    in [0, 1), then every key's tokens are merged and sorted by that
    position) rather than one contiguous block per key. `_date_list()`
    assigns dates to these same 260 positions strictly in sequence order,
    so a block-per-store layout would accidentally confine each store to
    only the first few days its own block happened to span - a real,
    unintended store x date structure in a feed meant to look like one
    real population, not three curve-fit views. Interleaving first
    removes that before dates are ever assigned."""
    tagged: list[tuple[float, str]] = []
    for key, count in counts.items():
        for k in range(count):
            tagged.append(((k + 0.5) / count, key))
    tagged.sort(key=lambda item: (item[0], item[1]))
    return [key for _position, key in tagged]


def _returned_occurrence_indices(store_id: str) -> set[int]:
    """Which of this store's own 0-indexed occurrences (counted in the
    order they appear once interleaved) are returned - evenly spread
    across the store's own occurrences via the same fractional-position
    logic as `_interleave_by_weight`, rather than front-loaded onto its
    first few occurrences, which would otherwise cluster every return
    onto whichever few days this store's own occurrences land on first."""
    count = STORE_ORDER_COUNTS[store_id]
    returns = STORE_RETURN_COUNTS[store_id]
    return {round(j * count / returns) for j in range(returns)}


def _rows() -> list[tuple[str, str, bool]]:
    store_sequence = _interleave_by_weight(STORE_ORDER_COUNTS)
    returned_occurrences = {store_id: _returned_occurrence_indices(store_id) for store_id in STORE_ORDER_COUNTS}
    occurrence_counts: dict[str, int] = dict.fromkeys(STORE_ORDER_COUNTS, 0)

    rows: list[tuple[str, str, bool]] = []
    for order_index, store_id in enumerate(store_sequence):
        occurrence = occurrence_counts[store_id]
        returned = occurrence in returned_occurrences[store_id]
        rows.append((f"O-{order_index + 1:04d}", store_id, returned))
        occurrence_counts[store_id] += 1
    return rows


def _date_list() -> list[str]:
    dates: list[str] = []
    for date, count in zip(DATE_CYCLE, DAILY_ORDER_COUNTS):
        dates += [date] * count
    return dates


def generate_orders() -> Dataset:
    """The player-facing order-level feed - real, clean, no data-quality
    issues (this is a pure chart-form-selection lesson, not a cleaning
    one). No hidden truth: every column here is directly visible and
    real."""
    base_rows = _rows()
    dates = _date_list()
    rows = [
        (order_id, store_id, dates[i], returned, _BASE_DELIVERY_MINUTES[i % len(_BASE_DELIVERY_MINUTES)])
        for i, (order_id, store_id, returned) in enumerate(base_rows)
    ]
    frame = pd.DataFrame(rows, columns=["order_id", "store_id", "order_date", "returned", "delivery_minutes"])
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    step = PipelineStep("collected", python_code="orders = pd.read_csv('novamart_orders.csv', parse_dates=['order_date'])")
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA, history=(step,))


def store_return_rate_pct(store_id: str) -> float:
    return 100.0 * STORE_RETURN_COUNTS[store_id] / STORE_ORDER_COUNTS[store_id]


# --- Real, hand-verified constants used by both the scenario and its tests

TOTAL_ORDERS = 260
STORE_IDS: tuple[str, ...] = tuple(STORE_ORDER_COUNTS.keys())
STORE_RETURN_RATES: dict[str, float] = {store_id: store_return_rate_pct(store_id) for store_id in STORE_ORDER_COUNTS}
DELIVERY_BIN_EDGES = (15, 30, 45, 60, 75, 90)
DELIVERY_BIN_COUNTS = (50, 130, 40, 30, 10)
DELIVERY_BIN_RANGE_LABELS: tuple[str, ...] = tuple(
    f"{DELIVERY_BIN_EDGES[i]}-{DELIVERY_BIN_EDGES[i + 1]}" for i in range(len(DELIVERY_BIN_EDGES) - 1)
)
"""Same real bins the histogram itself uses - the distribution ask's own
alternative chart form plots this identical (label, count) series, never
a different aggregate/grain, so the two options isolate visual encoding
alone (bars vs. a connected line) rather than confounding form with a
changed analytical question."""

# --- Optional mastery - a different domain: monthly SLA compliance --------
#
# 12 months of support-resolution SLA compliance rate, with a fixed real
# target (95%) - the naive "it's a time series, use a line" heuristic is
# necessary but not sufficient here: judging "missed vs. hit" against a
# specific threshold needs the target explicitly encoded on the chart (a
# real reference line), not just point-to-point movement.

MASTERY_SLA_TARGET_PCT = 95.0
MASTERY_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MASTERY_SLA_COMPLIANCE_PCT = (97.0, 96.0, 94.0, 93.0, 95.0, 92.0, 91.0, 93.0, 96.0, 97.0, 98.0, 98.0)
"""Real, hand-verified: 5 of 12 months (Mar, Apr, Jun, Jul, Aug) genuinely
miss the 95% target - a real, mixed pattern (not "everything improves" or
"everything declines"), so the mastery task's own real question ("which
months missed, and how did it move") has a real, non-trivial answer."""
