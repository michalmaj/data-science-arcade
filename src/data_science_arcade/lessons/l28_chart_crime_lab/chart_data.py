import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.chart import chart_render_range

SATISFACTION_SCHEMA = Schema(
    columns=(
        ColumnSchema("quarter", "object"),
        ColumnSchema("satisfaction_score", "float64"),
    )
)

ACTIVE_USERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("month", "object"),
        ColumnSchema("month_index", "int64", description_key="lesson.l28.schema.month_index"),
        ColumnSchema("active_users", "int64"),
    )
)

RETURNS_SCHEMA = Schema(
    columns=(
        ColumnSchema("quarter", "object"),
        ColumnSchema("units_sold", "int64"),
        ColumnSchema("returns", "int64"),
        ColumnSchema("total_customers", "int64", description_key="lesson.l28.schema.total_customers"),
    )
)

# A real, modest improvement over the year - hand-crafted, not random.
SATISFACTION_ROWS = [("Q1", 72.0), ("Q2", 73.0), ("Q3", 74.0), ("Q4", 75.0)]

# A real decline through most of the year with a genuine late recovery -
# the full year tells a nuanced story; either 2-month slice alone tells a
# dramatically different, incomplete one.
ACTIVE_USERS_ROWS = [
    ("Jan", 1, 10000), ("Feb", 2, 9800), ("Mar", 3, 9600), ("Apr", 4, 9500),
    ("May", 5, 9400), ("Jun", 6, 9300), ("Jul", 7, 9200), ("Aug", 8, 9100),
    ("Sep", 9, 9000), ("Oct", 10, 8900), ("Nov", 11, 9400), ("Dec", 12, 10200),
]

# total_customers is a large, fixed, cumulative base - a real, valid
# number for other business questions, but not the population implied by
# a *return-rate-among-units-actually-sold* question: the numerator
# (returns) is generated from units_sold, not from total_customers, so a
# rate built on the latter answers a different, unstated question while
# looking like it answers the stated one.
RETURNS_ROWS = [
    ("Q1", 1800, 270, 50000),
    ("Q2", 2000, 320, 50000),
    ("Q3", 2200, 286, 50000),
    ("Q4", 2400, 408, 50000),
]


def generate_satisfaction_data() -> Dataset:
    frame = pd.DataFrame(SATISFACTION_ROWS, columns=["quarter", "satisfaction_score"])
    step = PipelineStep("collected", python_code="satisfaction = pd.read_csv('novamart_quarterly_satisfaction.csv')")
    return Dataset(name="novamart_quarterly_satisfaction", frame=frame, schema=SATISFACTION_SCHEMA, history=(step,))


def generate_active_users_data() -> Dataset:
    frame = pd.DataFrame(ACTIVE_USERS_ROWS, columns=["month", "month_index", "active_users"])
    step = PipelineStep("collected", python_code="active_users = pd.read_csv('novamart_monthly_active_users.csv')")
    return Dataset(name="novamart_monthly_active_users", frame=frame, schema=ACTIVE_USERS_SCHEMA, history=(step,))


def generate_returns_data() -> Dataset:
    frame = pd.DataFrame(RETURNS_ROWS, columns=["quarter", "units_sold", "returns", "total_customers"])
    step = PipelineStep("collected", python_code="returns = pd.read_csv('novamart_quarterly_returns.csv')")
    return Dataset(name="novamart_quarterly_returns", frame=frame, schema=RETURNS_SCHEMA, history=(step,))


def fair_return_rate(dataset: Dataset, quarter: str) -> float:
    row = dataset.frame[dataset.frame["quarter"] == quarter].iloc[0]
    return float(row["returns"] / row["units_sold"])


def flawed_return_rate(dataset: Dataset, quarter: str) -> float:
    row = dataset.frame[dataset.frame["quarter"] == quarter].iloc[0]
    return float(row["returns"] / row["total_customers"])


# --- Reveal Mirror helpers - each ends on the exact quantity shown in the
# reveal's own ComparisonValue, computed from the same real data (and, for
# the axis case, the same real chart_render_range the renderer itself
# uses) - never a hardcoded approximation. -------------------------------


def visual_amplification_ratio(values: tuple[float, ...]) -> float:
    """FINAL value is how many times more of the chart's own vertical
    plotting range the same real data gap occupies under the zoomed
    bar-axis rendering vs. the zero-based one - computed from the exact
    same chart_render_range() ChartDesignerScene itself calls to draw
    the bars, so this can never silently drift from what a screenshot
    would show. Algebraically the real data gap cancels out of the
    ratio (it's the same gap in both fractions), leaving the ratio of
    the two plotting spans themselves - kept as two explicit fractions
    here anyway, matching the Mirror code string's own readable steps."""
    gap = max(values) - min(values)
    zoomed_min, zoomed_max = chart_render_range("bar", "zoomed", values)
    zero_min, zero_max = chart_render_range("bar", "zero_based", values)
    zoomed_fraction = gap / (zoomed_max - zoomed_min)
    zero_based_fraction = gap / (zero_max - zero_min)
    return zoomed_fraction / zero_based_fraction


def visual_amplification_mirror_code(dataset_var: str, column: str, var_name: str) -> str:
    """FINAL {var_name} is the same ratio visual_amplification_ratio()
    returns - verified via direct exec to match exactly. Uses the same
    0.9/1.05/1.15 constants ChartDesignerScene._chart_range /
    chart_render_range() use, named here rather than imported, since the
    Python Mirror is a shown-to-the-student snippet, not a live import."""
    return "\n".join(
        (
            f'{var_name}_gap = {dataset_var}["{column}"].max() - {dataset_var}["{column}"].min()',
            f'{var_name}_zoomed_span = {dataset_var}["{column}"].max() * 1.05 - {dataset_var}["{column}"].min() * 0.9',
            f'{var_name}_zero_based_span = {dataset_var}["{column}"].max() * 1.15',
            f"{var_name}_zoomed_fraction = {var_name}_gap / {var_name}_zoomed_span",
            f"{var_name}_zero_based_fraction = {var_name}_gap / {var_name}_zero_based_span",
            f"{var_name} = float({var_name}_zoomed_fraction / {var_name}_zero_based_fraction)",
        )
    )


def window_percent_change(values: tuple[float, ...]) -> float:
    """FINAL value is the percent change from the first to the last value
    of whatever window is passed in - the same real slice semantics
    `ChartOption.values` overrides already use (a full 12-month slice,
    or the same `[-2:]`/`[:2]` 2-month slices `requests.py` renders),
    so a Mirror call against the full series vs. either 2-month slice
    reproduces exactly what each chart option itself would show."""
    return float((values[-1] - values[0]) / values[0])


def window_percent_change_mirror_code(dataset_var: str, column: str, window: str, var_name: str) -> str:
    """`window` is a real pandas slice expression string, e.g. "[:]",
    "[-2:]", "[:2]" - kept as a parameter rather than three near-duplicate
    functions, since the only real difference between the three reveal
    facts is which slice of the same real column they read."""
    return "\n".join(
        (
            f'{var_name}_values = {dataset_var}.sort_values("month_index")["{column}"]{window}',
            f"{var_name} = float(({var_name}_values.iloc[-1] - {var_name}_values.iloc[0]) / {var_name}_values.iloc[0])",
        )
    )


def fair_rate_minimum_quarter_number(dataset: Dataset) -> float:
    """FINAL value is the 1-indexed quarter number ("Q3" -> 3.0) where
    the fair (returns/units_sold) rate is lowest - displayed via a
    Q-prefixed value_format, never shown as a bare index."""
    frame = dataset.frame
    fair_rate = frame["returns"] / frame["units_sold"]
    quarter_label = frame.loc[fair_rate.idxmin(), "quarter"]
    return float(quarter_label[1:])


def flawed_rate_minimum_quarter_number(dataset: Dataset) -> float:
    """FINAL value is the 1-indexed quarter number where the flawed
    (returns/total_customers) rate is lowest - a real, independently
    computed minimum that lands on a *different* quarter than the fair
    rate's own minimum, verified via direct exec (fair -> Q3, flawed ->
    Q1)."""
    frame = dataset.frame
    flawed_rate = frame["returns"] / frame["total_customers"]
    quarter_label = frame.loc[flawed_rate.idxmin(), "quarter"]
    return float(quarter_label[1:])


_WINDOW_SLICE_BY_OPTION = {"full_year": "[:]", "last_two_months": "[-2:]", "first_two_months": "[:2]"}
_DENOMINATOR_COLUMN_BY_OPTION = {"per_customers": "total_customers", "per_units_sold": "units_sold"}
DENOMINATOR_SCALE_BY_OPTION = {"per_customers": 10000, "per_units_sold": 100}
"""The display scale each denominator option's own rate is shown at (per
10,000 customers vs. per 100 units sold) - a single shared source for
both `requests.py`'s own chart values and `chart_pick_mirror_code`'s
Mirror output below, so the two can't drift out of sync with each
other the way they previously did (the Mirror omitted this scale
entirely)."""


def chart_pick_mirror_code(request_key: str, option_key: str, var_name: str) -> str:
    """FINAL {var_name} is the exact real series `ChartDesignerScene`
    itself renders for this request/option pair - the same satisfaction
    column regardless of axis scale (only the axis differs, never the
    data), the same real month-window slice `requests.py`'s own
    `ChartOption.values` overrides use, or the same real rate column the
    picked denominator produces."""
    if request_key == "satisfaction_score_claim":
        return f'{var_name} = satisfaction["satisfaction_score"]'
    if request_key == "active_users_claim":
        window = _WINDOW_SLICE_BY_OPTION[option_key]
        return f'{var_name} = active_users.sort_values("month_index")["active_users"]{window}'
    if request_key == "returns_rate_claim":
        denominator = _DENOMINATOR_COLUMN_BY_OPTION[option_key]
        scale = DENOMINATOR_SCALE_BY_OPTION[option_key]
        return f'{var_name} = (returns["returns"] / returns["{denominator}"]) * {scale}'
    raise ValueError(f"no mirror code for request {request_key!r}")


def rate_minimum_quarter_mirror_code(denominator_column: str, var_name: str) -> str:
    """FINAL {var_name} is the same 1-indexed quarter number the two
    functions above return - verified via direct exec against both
    `denominator_column` values ("units_sold" -> 3.0, "total_customers"
    -> 1.0). dataset_var is always "returns", this lesson's own single
    returns dataset."""
    return "\n".join(
        (
            f'{var_name}_rate = returns["returns"] / returns["{denominator_column}"]',
            f'{var_name}_label = returns.loc[{var_name}_rate.idxmin(), "quarter"]',
            f"{var_name} = float({var_name}_label[1:])",
        )
    )
