import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

DATES_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "int64"),
        ColumnSchema("market", "object"),
        ColumnSchema("correctly_dated", "bool"),
    )
)

# Hand-crafted (not random): 150 orders. A single global "parse as
# MM/DD/YYYY" rule - the format the majority (US) source system actually
# uses - correctly dates every US order. But DE orders were recorded as
# DD/MM/YYYY, and every DE order in this export happens to have a day
# number <= 12, so the swap never produces an out-of-range, obviously-
# wrong date - it's silently misdated into the wrong month instead.
US_ORDERS = 120
DE_ORDERS = 30


def _rows() -> list[tuple[int, str, bool]]:
    rows: list[tuple[int, str, bool]] = [(order_id, "US", True) for order_id in range(1, US_ORDERS + 1)]
    rows += [
        (order_id, "DE", False) for order_id in range(US_ORDERS + 1, US_ORDERS + DE_ORDERS + 1)
    ]
    return rows


def generate_date_parse_results() -> Dataset:
    frame = pd.DataFrame(_rows(), columns=["order_id", "market", "correctly_dated"])
    step = PipelineStep(
        "prepared",
        python_code=(
            "orders['order_date'] = pd.to_datetime(orders['order_date_raw'], format='%m/%d/%Y')"
            "  # one global rule, applied to every market"
        ),
    )
    return Dataset(name="orders", frame=frame, schema=DATES_SCHEMA, history=(step,))


def correctly_dated_rate(dataset: Dataset, market: str | None = None) -> float:
    frame = dataset.frame
    if market is not None:
        frame = frame[frame["market"] == market]
    return float(frame["correctly_dated"].mean())
