import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

FUNNEL_SCHEMA = Schema(
    columns=(
        ColumnSchema("period", "object"),
        ColumnSchema("segment", "object"),
        ColumnSchema("visitors", "int64"),
        ColumnSchema("conversions", "int64"),
    )
)

# Hand-crafted (not random): three independent slices, each with the same
# shape - a higher-converting segment whose share of total traffic grows
# enough between Q1 and Q2 that the blended company-wide rate improves,
# even though BOTH segments' own conversion rates individually declined.
# Simpson's paradox by construction, not by accident.
DEVICE_ROWS = {
    ("Q1", "mobile"): (200, 84),  # 42%
    ("Q1", "desktop"): (800, 200),  # 25%
    ("Q2", "mobile"): (700, 266),  # 38%
    ("Q2", "desktop"): (300, 66),  # 22%
}
REGION_ROWS = {
    ("Q1", "eu"): (300, 135),  # 45%
    ("Q1", "us"): (700, 140),  # 20%
    ("Q2", "eu"): (750, 300),  # 40%
    ("Q2", "us"): (250, 45),  # 18%
}
CHANNEL_ROWS = {
    ("Q1", "organic"): (400, 200),  # 50%
    ("Q1", "paid"): (600, 90),  # 15%
    ("Q2", "organic"): (800, 360),  # 45%
    ("Q2", "paid"): (200, 24),  # 12%
}


def _build(name: str, rows: dict[tuple[str, str], tuple[int, int]]) -> Dataset:
    frame = pd.DataFrame(
        [(period, segment, visitors, conversions) for (period, segment), (visitors, conversions) in rows.items()],
        columns=["period", "segment", "visitors", "conversions"],
    )
    step = PipelineStep("collected", python_code=f"{name} = pd.read_csv('novamart_{name}.csv')")
    return Dataset(name=name, frame=frame, schema=FUNNEL_SCHEMA, history=(step,))


def generate_device_funnel() -> Dataset:
    return _build("device_funnel", DEVICE_ROWS)


def generate_region_funnel() -> Dataset:
    return _build("region_funnel", REGION_ROWS)


def generate_channel_funnel() -> Dataset:
    return _build("channel_funnel", CHANNEL_ROWS)


def segment_rate(dataset: Dataset, period: str, segment: str) -> float:
    row = dataset.frame.loc[(dataset.frame["period"] == period) & (dataset.frame["segment"] == segment)].iloc[0]
    return float(row["conversions"]) / float(row["visitors"])


def overall_rate(dataset: Dataset, period: str) -> float:
    rows = dataset.frame.loc[dataset.frame["period"] == period]
    return float(rows["conversions"].sum()) / float(rows["visitors"].sum())
