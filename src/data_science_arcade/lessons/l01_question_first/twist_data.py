import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "int64"),
        ColumnSchema("household_id", "int64"),
        ColumnSchema("order_date", "datetime64[ns]"),
        ColumnSchema("order_value", "float64"),
    )
)

REFERENCE_DATE = pd.Timestamp("2024-12-31")
RECENT_WINDOW_START = REFERENCE_DATE - pd.Timedelta(days=30)
TOTAL_CUSTOMERS = 40
"""4 segments of 10, 10, 12, 8 customers - see _order_rows() for exactly
what each segment is built to demonstrate. Chosen (not derived) so every
sensitivity comparison this lesson runs produces a real, meaningful gap,
by construction rather than by chance - same discipline the original
20-customer version already established."""


def _segment_recent_and_overall_repeaters() -> list[tuple[int, int, str, float]]:
    """Customers 1-10: repeat both across the full year AND within the
    last 30 days - household_id == customer_id throughout (no sharing in
    this segment)."""
    rows: list[tuple[int, int, str, float]] = []
    for customer_id in range(1, 11):
        value = 30.0 + (customer_id % 5) * 4.0
        rows += [
            (customer_id, customer_id, "2024-03-15", value),
            (customer_id, customer_id, "2024-12-05", value),
            (customer_id, customer_id, "2024-12-20", value),
        ]
    return rows


def _segment_overall_only_repeaters() -> list[tuple[int, int, str, float]]:
    """Customers 11-20: repeat across the year, but both orders land well
    outside the last-30-days window - present in the 12-month repeat rate,
    absent entirely from the 30-day one (not even a single order there)."""
    rows: list[tuple[int, int, str, float]] = []
    for customer_id in range(11, 21):
        value = 25.0 + (customer_id % 4) * 5.0
        rows += [
            (customer_id, customer_id, "2024-02-10", value),
            (customer_id, customer_id, "2024-07-22", value),
        ]
    return rows


def _segment_one_time_only() -> list[tuple[int, int, str, float]]:
    """Customers 21-32: exactly one order, ever - never a repeat under any
    definition this lesson uses. Placed *inside* the last-30-days window
    (not outside it) deliberately: repeat_rate()'s denominator is distinct
    entities actually present in a window, not TOTAL_CUSTOMERS, so a
    one-time order sitting outside the window entirely would just be
    invisible to it rather than diluting the window's own repeat rate the
    way a real one-time buyer showing up recently actually would."""
    rows: list[tuple[int, int, str, float]] = []
    for customer_id in range(21, 33):
        value = 20.0 + (customer_id % 6) * 6.0
        rows.append((customer_id, customer_id, "2024-12-14", value))
    return rows


def _segment_household_sharing() -> list[tuple[int, int, str, float]]:
    """Customers 33-40, paired into 4 households (1001-1004): each
    individual customer_id orders exactly once within the last 30 days -
    a one-time customer under the customer-level definition - but their
    household partner also orders within the same window, so the
    household itself has 2 orders there. This is what makes Act 6's
    entity-sensitivity comparison a real, computable fact about the data
    rather than a narrated claim: grouping the identical rows by
    household_id instead of customer_id changes which of these 4 units
    counts as a "repeat," with no new data and no time-window change."""
    pairs = ((33, 34, "2024-12-10", "2024-12-15"), (35, 36, "2024-12-08", "2024-12-22"), (37, 38, "2024-12-12", "2024-12-27"), (39, 40, "2024-12-03", "2024-12-18"))
    rows: list[tuple[int, int, str, float]] = []
    for index, (first_id, second_id, first_date, second_date) in enumerate(pairs):
        household_id = 1001 + index
        value = 45.0 + (index % 3) * 10.0
        rows.append((first_id, household_id, first_date, value))
        rows.append((second_id, household_id, second_date, value))
    return rows


def _order_rows() -> list[tuple[int, int, str, float]]:
    return (
        _segment_recent_and_overall_repeaters()
        + _segment_overall_only_repeaters()
        + _segment_one_time_only()
        + _segment_household_sharing()
    )


def generate_twist_orders() -> Dataset:
    """The real NovaMart orders export this lesson's whole investigation
    runs on - one continuous dataset, not a separate toy example per act
    (spec: a good question determines later transformations). Hand-crafted
    by construction, not randomly seeded, so every sensitivity comparison
    downstream (time-window, entity, and the coverage gap the dataset
    simply never captures) is guaranteed and hand-verifiable rather than
    hoping a seed lands right."""
    frame = pd.DataFrame(_order_rows(), columns=["customer_id", "household_id", "order_date", "order_value"])
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    step = PipelineStep(
        "prepared",
        python_code="orders = pd.read_csv('novamart_orders.csv', parse_dates=['order_date'])",
    )
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA, history=(step,))


def repeat_rate(dataset: Dataset, entity_column: str, window_start: pd.Timestamp | None) -> float:
    """Fraction of distinct entities (customer_id or household_id) with
    2+ orders in the window (None = all time) that show up as repeats
    under this specific entity+window definition. window_start filters
    rows before grouping, so an entity with orders both inside and
    outside the window may only count as a repeat when the window is wide
    enough to include both. The denominator is the count of *distinct
    entities present in the window* - not TOTAL_CUSTOMERS - since
    switching entity_column genuinely changes what's being counted, the
    same distinction the lesson's own grain content teaches."""
    frame = dataset.frame
    if window_start is not None:
        frame = frame[frame["order_date"] >= window_start]
    order_counts = frame.groupby(entity_column).size()
    if len(order_counts) == 0:
        return 0.0
    repeat_entities = int((order_counts >= 2).sum())
    return repeat_entities / len(order_counts)


def repeat_purchase_rate(dataset: Dataset, window_start: pd.Timestamp | None) -> float:
    """Back-compat alias for the original customer-level, TOTAL_CUSTOMERS-
    denominator computation - kept because it answers a subtly different
    question than repeat_rate("customer_id", ...) once household sharing
    exists (TOTAL_CUSTOMERS as the denominator vs. distinct customers
    actually present in the window), and every existing caller/test
    already depends on the TOTAL_CUSTOMERS-denominator behavior."""
    frame = dataset.frame
    if window_start is not None:
        frame = frame[frame["order_date"] >= window_start]
    order_counts = frame.groupby("customer_id").size()
    repeat_customers = int((order_counts >= 2).sum())
    return repeat_customers / TOTAL_CUSTOMERS


def is_returning_household(dataset: Dataset, household_id: int) -> bool:
    """True if this household placed 2+ orders across the full dataset -
    the real signal the optional mastery challenge's own comparison
    (returning vs. one-time households' total spend) is built on."""
    frame = dataset.frame
    return len(frame[frame["household_id"] == household_id]) >= 2


def total_value_by_household_group(dataset: Dataset, returning: bool) -> float:
    """Total order_value across every household that is/isn't returning
    (see is_returning_household) - the real computation the optional
    mastery challenge's own live-compute step runs."""
    frame = dataset.frame
    household_ids = frame["household_id"].unique()
    matching = [hid for hid in household_ids if is_returning_household(dataset, hid) == returning]
    return float(frame[frame["household_id"].isin(matching)]["order_value"].sum())
