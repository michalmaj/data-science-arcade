import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.timeseries import DailyPoint, TimeSeries

DAILY_CONVERSION_SCHEMA = Schema(
    columns=(
        ColumnSchema("period", "object", description="'current' or 'previous'"),
        ColumnSchema("day", "int64", description="1-indexed day within its period; day 1 is a Monday"),
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
