import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

PUSH_SPEND_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "int64"),
        ColumnSchema("push_opens_per_week", "int64"),
        ColumnSchema("weekly_spend", "float64"),
    )
)

SHIPMENT_SALES_SCHEMA = Schema(
    columns=(
        ColumnSchema("store_day_id", "int64"),
        ColumnSchema("shipment_received", "bool"),
        ColumnSchema("daily_sales", "float64"),
    )
)

DARK_MODE_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "int64"),
        ColumnSchema("device_group", "object", description_key="lesson.l26.schema.device_group"),
        ColumnSchema("dark_mode_enabled", "bool"),
        ColumnSchema("weekly_spend", "float64"),
    )
)

# Scenario 1: push notification opens vs. weekly spend - hand-crafted, not
# random. A real, strong, consistent relationship (real people, real
# purchases), with no additional evidence given that would distinguish
# direct causation, reverse causation, or a lurking variable - all three
# stay genuinely open. Only pure coincidence is implausible for a pattern
# this consistent across every customer tracked.
PUSH_SPEND_ROWS = [
    (1, 1, 22.0), (2, 2, 28.0), (3, 3, 30.0), (4, 3, 35.0), (5, 4, 34.0),
    (6, 5, 42.0), (7, 6, 45.0), (8, 7, 50.0), (9, 8, 55.0), (10, 9, 60.0),
]

# Scenario 2: shipment days vs. daily sales at the same stores. The
# shipment calendar is fixed by logistics months in advance, independent
# of real-time sales - that fact (given at the scenario, not derived from
# this data) rules out reverse causality specifically. The pattern is
# consistent across every day tracked, ruling out coincidence too.
SHIPMENT_SALES_ROWS = [
    (1, True, 5200.0), (2, False, 3800.0), (3, True, 5400.0), (4, False, 3600.0),
    (5, True, 5100.0), (6, False, 3900.0), (7, True, 5300.0), (8, False, 3700.0),
    (9, True, 5000.0), (10, False, 3850.0), (11, True, 5250.0), (12, False, 3750.0),
]

# Scenario 3: dark mode usage vs. weekly spend. Dark mode is only
# available on newer devices, which is exactly the same group that
# spends more regardless of the toggle - device group is a real lurking
# variable. Controlling for it (looking only within the "modern" group)
# makes the relationship between dark mode and spend vanish.
DARK_MODE_ROWS = [
    (1, "modern", True, 65.0), (2, "modern", True, 62.0), (3, "modern", True, 68.0), (4, "modern", True, 60.0),
    (5, "modern", True, 64.0), (6, "modern", True, 66.0), (7, "modern", True, 61.0), (8, "modern", True, 69.0),
    (9, "modern", False, 63.0), (10, "modern", False, 67.0),
    (11, "older", False, 22.0), (12, "older", False, 25.0), (13, "older", False, 20.0), (14, "older", False, 28.0),
    (15, "older", False, 24.0), (16, "older", False, 26.0), (17, "older", False, 21.0), (18, "older", False, 29.0),
    (19, "older", False, 23.0), (20, "older", False, 27.0),
]


def generate_push_spend_data() -> Dataset:
    frame = pd.DataFrame(PUSH_SPEND_ROWS, columns=["customer_id", "push_opens_per_week", "weekly_spend"])
    step = PipelineStep("collected", python_code="push_spend = pd.read_csv('novamart_push_opens_vs_spend.csv')")
    return Dataset(name="novamart_push_opens_vs_spend", frame=frame, schema=PUSH_SPEND_SCHEMA, history=(step,))


def generate_shipment_sales_data() -> Dataset:
    frame = pd.DataFrame(SHIPMENT_SALES_ROWS, columns=["store_day_id", "shipment_received", "daily_sales"])
    step = PipelineStep("collected", python_code="shipment_sales = pd.read_csv('novamart_shipment_vs_sales.csv')")
    return Dataset(name="novamart_shipment_vs_sales", frame=frame, schema=SHIPMENT_SALES_SCHEMA, history=(step,))


def generate_dark_mode_data() -> Dataset:
    frame = pd.DataFrame(DARK_MODE_ROWS, columns=["customer_id", "device_group", "dark_mode_enabled", "weekly_spend"])
    step = PipelineStep("collected", python_code="dark_mode = pd.read_csv('novamart_dark_mode_vs_spend.csv')")
    return Dataset(name="novamart_dark_mode_vs_spend", frame=frame, schema=DARK_MODE_SCHEMA, history=(step,))


def compute_correlation(dataset: Dataset, column_a: str, column_b: str) -> float:
    return float(dataset.frame[column_a].astype(float).corr(dataset.frame[column_b].astype(float)))


def compute_correlation_within(dataset: Dataset, group_column: str, group_value: str, column_a: str, column_b: str) -> float:
    subset = dataset.frame[dataset.frame[group_column] == group_value]
    return float(subset[column_a].astype(float).corr(subset[column_b].astype(float)))


def compute_device_group_correlation(dataset: Dataset, group_column: str, group_value: str, column_b: str) -> float:
    """A derived 0/1 "is this row the candidate group" column, built on
    the fly - never mutates the dataset's own real schema/columns."""
    is_group = (dataset.frame[group_column] == group_value).astype(float)
    return float(is_group.corr(dataset.frame[column_b].astype(float)))


_MIRROR_SOURCE_BY_REQUEST = {
    "push_opens_claim": ("push_spend", "push_opens_per_week", "weekly_spend"),
    "shipment_sales_claim": ("shipment_sales", "shipment_received", "daily_sales"),
    "dark_mode_claim": ("dark_mode", "dark_mode_enabled", "weekly_spend"),
}


def correlation_mirror_code(request_key: str, var_name: str) -> str:
    """FINAL {var_name} is the same Pearson r CorrelationRequest.correlation
    already displays - verified via direct exec against all three real
    scenarios. dataset_var matches that scenario's own PipelineStep load
    line (push_spend/shipment_sales/dark_mode) - three separate real
    DataFrames, not one shared dataset."""
    dataset_var, column_a, column_b = _MIRROR_SOURCE_BY_REQUEST[request_key]
    return f'{var_name} = float({dataset_var}["{column_a}"].astype(float).corr({dataset_var}["{column_b}"].astype(float)))'


def correlation_within_mirror_code(group_column: str, group_value: str, column_a: str, column_b: str, var_name: str) -> str:
    """FINAL {var_name} is the real SUBGROUP correlation - never the
    general one - matching compute_correlation_within()'s own output
    exactly. Only ever called for the modern-device subgroup, where
    dark_mode_enabled actually varies; the older-device subgroup has zero
    variance (every row is False) and its own correlation is undefined -
    never computed or shown here."""
    return "\n".join(
        (
            f'{var_name}_subset = dark_mode[dark_mode["{group_column}"] == "{group_value}"]',
            f'{var_name} = float({var_name}_subset["{column_a}"].astype(float).corr({var_name}_subset["{column_b}"].astype(float)))',
        )
    )


def device_group_correlation_mirror_code(group_column: str, group_value: str, column_b: str, var_name: str) -> str:
    """A derived 0/1 "is this row the candidate group" column, built on
    the fly - never mutates dark_mode's own real schema. FINAL {var_name}
    matches compute_device_group_correlation()'s own real output."""
    return "\n".join(
        (
            f'{var_name}_is_group = (dark_mode["{group_column}"] == "{group_value}").astype(float)',
            f'{var_name} = float({var_name}_is_group.corr(dark_mode["{column_b}"].astype(float)))',
        )
    )
