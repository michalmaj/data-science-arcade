import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

DEVICE_SPLIT_SCHEMA = Schema(
    columns=(
        ColumnSchema("period", "object", description="'before' or 'after' one-click reorder shipped"),
        ColumnSchema("week", "int64"),
        ColumnSchema("device", "object"),
        ColumnSchema("repeat_purchase_rate", "float64"),
    )
)

# The same repeat_purchase_rate the player already confirmed increases,
# resliced by a dimension nobody pre-specified as a hypothesis - a
# never-tested "explanation" a team member spots only after seeing the
# overall result move. App and website users start at very different
# baselines (app users were always the more frequent repeat buyers), but
# both rise by the exact same +10 points after launch - the device split
# doesn't explain *why* the rate moved, it was just already there.
DEVICE_ROWS = [
    ("before", 1, "app", 0.38),
    ("before", 2, "app", 0.42),
    ("after", 1, "app", 0.48),
    ("after", 2, "app", 0.52),
    ("before", 1, "website", 0.11),
    ("before", 2, "website", 0.15),
    ("after", 1, "website", 0.21),
    ("after", 2, "website", 0.25),
]


def generate_device_split_data() -> Dataset:
    frame = pd.DataFrame(DEVICE_ROWS, columns=["period", "week", "device", "repeat_purchase_rate"])
    step = PipelineStep("collected", python_code="by_device = pd.read_csv('novamart_launch_impact_by_device.csv')")
    return Dataset(name="launch_impact_by_device", frame=frame, schema=DEVICE_SPLIT_SCHEMA, history=(step,))


def device_repeat_rate(dataset: Dataset, device: str, period: str) -> float:
    rows = dataset.frame[(dataset.frame["device"] == device) & (dataset.frame["period"] == period)]
    return float(rows["repeat_purchase_rate"].mean())
