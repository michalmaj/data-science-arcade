import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

RERANKING_SCHEMA = Schema(
    columns=(
        ColumnSchema("period", "object", description="'before_rollout' or 'after_rollout' of the search re-ranking change"),
        ColumnSchema("week", "int64"),
        ColumnSchema("visits", "int64"),
        ColumnSchema("clicks", "int64"),
    )
)

# A separate experiment NovaMart already shipped on - a search re-ranking
# change, peeked at day 4 (looked like a clean win) and rolled out to
# everyone on the strength of that early read. This is the real, full-
# scale before/after once the new ranking had been live for a while - not
# the same checkout experiment the player just monitored, but the same
# failure mode acted on for real: the early peek didn't just overstate a
# real win, it pointed the wrong way entirely.
RERANKING_ROWS = [
    ("before_rollout", 1, 5000, 360),
    ("before_rollout", 2, 5000, 360),
    ("after_rollout", 1, 5000, 305),
    ("after_rollout", 2, 5000, 305),
]


def generate_reranking_data() -> Dataset:
    frame = pd.DataFrame(RERANKING_ROWS, columns=["period", "week", "visits", "clicks"])
    step = PipelineStep("collected", python_code="reranking = pd.read_csv('novamart_search_reranking_rollout.csv')")
    return Dataset(name="search_reranking_rollout", frame=frame, schema=RERANKING_SCHEMA, history=(step,))


def click_through_rate(dataset: Dataset, period: str) -> float:
    rows = dataset.frame[dataset.frame["period"] == period]
    return float(rows["clicks"].sum() / rows["visits"].sum())
