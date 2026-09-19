import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

DEVICE_DASHBOARD_SCHEMA = Schema(
    columns=(
        ColumnSchema("device", "object"),
        ColumnSchema("week", "int64"),
        ColumnSchema("revenue", "float64"),
    )
)

# Marketing's own separately-maintained channel dashboard export - a real
# second source at a different grain than Finance's regional table, and
# deliberately not row-level-joinable to it (no per-order device flag
# exists anywhere in Finance's own data). Weeks 7-8 keep the exact figures
# this lesson's own math already depends on (they sum to Finance's real
# company totals for those two weeks); weeks 1-6 are generated at the same
# ~58.5% mobile / ~41.5% desktop split real Marketing data would show,
# computed here rather than hand-typed, so this source is a real
# DataFrame a lead can compute from, not an authored constant.
_MOBILE_SHARE = 0.585
_COMPANY_WEEKLY_REVENUE_WEEKS_1_TO_6 = (344400.0, 345600.0, 344400.0, 345600.0, 345600.0, 344200.0)
_WEEK_7_REVENUE = {"mobile": 246000.0, "desktop": 174000.0}
_WEEK_8_REVENUE = {"mobile": 201000.0, "desktop": 143100.0}


def _build_rows() -> list[tuple[str, int, float]]:
    rows = []
    for index, total in enumerate(_COMPANY_WEEKLY_REVENUE_WEEKS_1_TO_6):
        week = index + 1
        mobile = round(total * _MOBILE_SHARE, 2)
        desktop = round(total - mobile, 2)
        rows.append(("mobile", week, mobile))
        rows.append(("desktop", week, desktop))
    for device, revenue in _WEEK_7_REVENUE.items():
        rows.append((device, 7, revenue))
    for device, revenue in _WEEK_8_REVENUE.items():
        rows.append((device, 8, revenue))
    return rows


def generate_device_dashboard() -> Dataset:
    frame = pd.DataFrame(_build_rows(), columns=["device", "week", "revenue"])
    step = PipelineStep("collected", python_code="device_dashboard = pd.read_csv('novamart_marketing_device_dashboard.csv')")
    return Dataset(name="novamart_marketing_device_dashboard", frame=frame, schema=DEVICE_DASHBOARD_SCHEMA, history=(step,))


def device_revenue_at(dataset: Dataset, device: str, week: int) -> float:
    row = dataset.frame[(dataset.frame["device"] == device) & (dataset.frame["week"] == week)]
    return float(row["revenue"].iloc[0])
