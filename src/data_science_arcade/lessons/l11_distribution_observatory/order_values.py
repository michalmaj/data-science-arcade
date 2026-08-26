import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

ORDER_VALUES_SCHEMA = Schema(
    columns=(
        ColumnSchema("segment", "object", description="Hidden ground truth - never shown until the twist"),
        ColumnSchema("order_value", "float64"),
    )
)

# Hand-crafted (not random): two real customer populations mixed into one
# "order value" feed, not a single skewed-but-unimodal group. Consumer
# orders cluster low ($25-$75); business orders cluster high ($600-$900) -
# nothing in between. Any single summary computed over the mix either
# lands inside one cluster (blind to the other) or in the empty gap
# between them (representing neither).
CONSUMER_COUNT = 70
CONSUMER_MIN = 25.0
CONSUMER_STEP = 5.0
CONSUMER_CYCLE = 11  # values 25, 30, ..., 75

BUSINESS_COUNT = 30
BUSINESS_MIN = 600.0
BUSINESS_STEP = 50.0
BUSINESS_CYCLE = 7  # values 600, 650, ..., 900


def _rows() -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for i in range(CONSUMER_COUNT):
        rows.append(("consumer", CONSUMER_MIN + (i % CONSUMER_CYCLE) * CONSUMER_STEP))
    for i in range(BUSINESS_COUNT):
        rows.append(("business", BUSINESS_MIN + (i % BUSINESS_CYCLE) * BUSINESS_STEP))
    return rows


def generate_order_values() -> Dataset:
    frame = pd.DataFrame(_rows(), columns=["segment", "order_value"])
    step = PipelineStep(
        "collected",
        python_code="orders = pd.read_csv('novamart_order_values.csv')",
    )
    return Dataset(name="order_values", frame=frame, schema=ORDER_VALUES_SCHEMA, history=(step,))


def segment_mean(dataset: Dataset, segment: str) -> float:
    frame = dataset.frame
    return float(frame.loc[frame["segment"] == segment, "order_value"].mean())
