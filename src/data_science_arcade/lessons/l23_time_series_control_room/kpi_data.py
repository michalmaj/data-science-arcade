import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.timeseries import DailyPoint, LensOption, TimeSeries, TimeSeriesRequest

DAILY_CONVERSION_SCHEMA = Schema(
    columns=(
        ColumnSchema("period", "object", description_key="lesson.l23.schema.period"),
        ColumnSchema("day", "int64", description_key="lesson.l23.schema.day"),
        ColumnSchema("visits", "int64"),
        ColumnSchema("conversions", "int64"),
    )
)

# Mon..Sun checkout conversions per 1000 visits - a real weekly rhythm
# (weekends run lower), hand-crafted, not random.
WEEKDAY_CONVERSIONS = (250, 260, 250, 240, 230, 200, 190)
VISITS_PER_DAY = 1000

# Day 8 (a Monday, week 2) carries a real marketing campaign: a genuine
# +4pt lift on top of that day's normal weekday baseline. Day 12 (a
# Friday) is when the release shipped - it gets no special adjustment at
# all, so days 13-14 right after it are just an ordinary Sat/Sun, exactly
# like every other weekend in this dataset.
CAMPAIGN_DAY = 8
CAMPAIGN_LIFT_CONVERSIONS = 40
RELEASE_DAY = 12
PERIOD_LENGTH_DAYS = 21


def _current_period_rows() -> list[tuple[str, int, int, int]]:
    rows = []
    for day in range(1, PERIOD_LENGTH_DAYS + 1):
        conversions = WEEKDAY_CONVERSIONS[(day - 1) % 7]
        if day == CAMPAIGN_DAY:
            conversions += CAMPAIGN_LIFT_CONVERSIONS
        rows.append(("current", day, VISITS_PER_DAY, conversions))
    return rows


def _previous_period_rows() -> list[tuple[str, int, int, int]]:
    return [("previous", day, VISITS_PER_DAY, WEEKDAY_CONVERSIONS[(day - 1) % 7]) for day in range(1, PERIOD_LENGTH_DAYS + 1)]


ROWS = _current_period_rows() + _previous_period_rows()


def generate_kpi_data() -> Dataset:
    frame = pd.DataFrame(ROWS, columns=["period", "day", "visits", "conversions"])
    step = PipelineStep("collected", python_code="daily_kpi = pd.read_csv('novamart_daily_conversion_rate.csv')")
    return Dataset(name="novamart_daily_conversion_rate", frame=frame, schema=DAILY_CONVERSION_SCHEMA, history=(step,))


def conversion_rate(dataset: Dataset, period: str, day: int) -> float:
    row = dataset.frame[(dataset.frame["period"] == period) & (dataset.frame["day"] == day)].iloc[0]
    return float(row["conversions"] / row["visits"])


def build_time_series(dataset: Dataset, period: str, label_key: str) -> TimeSeries:
    period_frame = dataset.frame[dataset.frame["period"] == period].sort_values("day")
    points = tuple(DailyPoint(int(row.day), float(row.conversions / row.visits)) for row in period_frame.itertuples())
    return TimeSeries(label_key=label_key, points=points)


def day_rate_with_baseline_mirror_code(period: str, day: int, var_name: str) -> str:
    """The real rate for one (period, day) cell, computed alongside its own
    weekday-aligned baseline (mean over every `previous`-period occurrence
    of that weekday - a real 3-week average, never a single day's own
    previous-period value) and the residual between them. The FINAL
    `{var_name}` variable is always the plain rate - the same quantity a
    ComparisonValue built from this day actually displays - never the
    residual; `_expected_rate`/`_residual` are extra, real, auxiliary
    computed context in the same snippet, not what's asserted equal to
    the displayed value. `weekday_baseline` is only ever built from the
    `previous` period, so a `current`-period day's own possible deviation
    (e.g. the campaign lift) can never leak into its own baseline."""
    return "\n".join(
        (
            f'{var_name}_daily = daily_kpi.assign(rate=daily_kpi["conversions"] / daily_kpi["visits"], weekday=(daily_kpi["day"] - 1) % 7)',
            f'{var_name}_reference = {var_name}_daily[{var_name}_daily["period"] == "previous"]',
            f'{var_name}_weekday_baseline = {var_name}_reference.groupby("weekday")["rate"].mean()',
            f'{var_name}_row = {var_name}_daily[({var_name}_daily["period"] == "{period}") & ({var_name}_daily["day"] == {day})].iloc[0]',
            f'{var_name} = float({var_name}_row["rate"])',
            f'{var_name}_expected_rate = float({var_name}_weekday_baseline[{var_name}_row["weekday"]])',
            f'{var_name}_residual = {var_name} - {var_name}_expected_rate',
        )
    )


def weekday_baseline_mirror_code(weekday: int, var_name: str) -> str:
    """The real weekday-aligned baseline itself (mean over every
    `previous`-period occurrence of that weekday) - what a citable
    "baseline" ComparisonValue's own displayed rate actually is, computed
    from the full 3-week reference period, never a single day's lookup.
    `weekday` is 0=Monday..6=Sunday, matching `(day - 1) % 7`."""
    return "\n".join(
        (
            f'{var_name}_reference = daily_kpi[daily_kpi["period"] == "previous"].assign(rate=daily_kpi["conversions"] / daily_kpi["visits"], weekday=(daily_kpi["day"] - 1) % 7)',
            f'{var_name}_weekday_baseline = {var_name}_reference.groupby("weekday")["rate"].mean()',
            f'{var_name} = float({var_name}_weekday_baseline[{weekday}])',
        )
    )


def timeseries_lens_mirror_code(request: TimeSeriesRequest, option: LensOption, var_name: str) -> str:
    """The real pandas equivalent of an interactive TimeSeriesScene pick:
    filters `daily_kpi` down to the request's own `highlight_days` for the
    current period, plus (only when the chosen lens shows it) the same
    days in the previous period - real, inspectable, no delta pre-computed
    for the student. Mirrors CohortMatrixScene's own
    `cohort_comparison_mirror_code` shape (filters real rows, never
    forces a scalar)."""
    days = list(request.highlight_days)
    lines = [
        f"{var_name}_days = {days}",
        f'{var_name} = daily_kpi[(daily_kpi["period"] == "current") & (daily_kpi["day"].isin({var_name}_days))]',
    ]
    if option.show_previous_period:
        lines.append(f'{var_name}_reference = daily_kpi[(daily_kpi["period"] == "previous") & (daily_kpi["day"].isin({var_name}_days))]')
    return "\n".join(lines)
