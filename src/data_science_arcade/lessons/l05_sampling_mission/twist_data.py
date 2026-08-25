import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

RESPONSES_SCHEMA = Schema(
    columns=(
        ColumnSchema("respondent_id", "int64"),
        ColumnSchema("group", "object"),
        ColumnSchema("satisfied", "bool"),
    )
)

# Hand-crafted (not random): four equally-weighted customer groups, but
# Plus subscribers respond far more often than anyone else AND skew more
# satisfied - so they end up 75% of all responses even though they're just
# one of four groups, pulling the raw aggregate well above what any single
# group actually reports.
GROUP_RESPONSES: dict[str, tuple[int, int]] = {
    # group -> (respondent_count, satisfied_count)
    "new": (20, 15),
    "regular": (20, 13),
    "plus": (150, 132),
    "lapsed": (10, 4),
}
DOMINANT_GROUP = "plus"


def _response_rows() -> list[tuple[int, str, bool]]:
    rows: list[tuple[int, str, bool]] = []
    respondent_id = 1
    for group, (respondent_count, satisfied_count) in GROUP_RESPONSES.items():
        for offset in range(respondent_count):
            rows.append((respondent_id, group, offset < satisfied_count))
            respondent_id += 1
    return rows


def generate_survey_responses() -> Dataset:
    frame = pd.DataFrame(_response_rows(), columns=["respondent_id", "group", "satisfied"])
    step = PipelineStep(
        "prepared",
        python_code="responses = pd.read_csv('novamart_satisfaction_responses.csv')  # one row per respondent",
    )
    return Dataset(name="responses", frame=frame, schema=RESPONSES_SCHEMA, history=(step,))


def apparent_satisfaction(dataset: Dataset) -> float:
    """The raw, respondent-weighted average - what you'd report if you
    just averaged every response you got, ignoring which group it came
    from."""
    return float(dataset.frame["satisfied"].mean())


def group_share_of_responses(dataset: Dataset, group: str) -> float:
    return float((dataset.frame["group"] == group).mean())


def unweighted_average_satisfaction(dataset: Dataset) -> float:
    """The average of each group's OWN satisfaction rate, each group
    counted once regardless of how many people from it responded - what
    the result would look like if no group could drown out the others."""
    per_group_rates = dataset.frame.groupby("group")["satisfied"].mean()
    return float(per_group_rates.mean())
