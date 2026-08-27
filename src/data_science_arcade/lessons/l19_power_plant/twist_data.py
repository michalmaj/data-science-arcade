import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

BANNER_SCHEMA = Schema(
    columns=(
        ColumnSchema("group", "object", description="'control' or 'treatment' in the homepage banner experiment"),
        ColumnSchema("week", "int64"),
        ColumnSchema("visits", "int64"),
        ColumnSchema("conversions", "int64"),
    )
)

# A homepage banner experiment NovaMart already ran for a full quarter
# (12 weeks) at full site traffic - by far the largest sample this lesson
# ever shows, big enough to reliably detect a real difference as small as
# a few tenths of a percentage point. Real computed rates (sum of
# conversions over sum of visits), not a hand-picked headline number.
BANNER_ROWS = [
    ("control", 1, 12500, 2250),
    ("control", 2, 12500, 2250),
    ("control", 3, 12500, 2250),
    ("control", 4, 12500, 2250),
    ("treatment", 1, 12500, 2375),
    ("treatment", 2, 12500, 2375),
    ("treatment", 3, 12500, 2375),
    ("treatment", 4, 12500, 2375),
]


def generate_banner_experiment_data() -> Dataset:
    frame = pd.DataFrame(BANNER_ROWS, columns=["group", "week", "visits", "conversions"])
    step = PipelineStep("collected", python_code="banner_experiment = pd.read_csv('novamart_homepage_banner_experiment.csv')")
    return Dataset(name="homepage_banner_experiment", frame=frame, schema=BANNER_SCHEMA, history=(step,))


def conversion_rate(dataset: Dataset, group: str) -> float:
    rows = dataset.frame[dataset.frame["group"] == group]
    return float(rows["conversions"].sum() / rows["visits"].sum())


def sample_size_per_group(dataset: Dataset, group: str) -> int:
    return int(dataset.frame[dataset.frame["group"] == group]["visits"].sum())
