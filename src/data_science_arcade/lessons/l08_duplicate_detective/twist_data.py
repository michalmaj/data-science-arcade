import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

MATCH_RESULTS_SCHEMA = Schema(
    columns=(
        ColumnSchema("pair_id", "int64"),
        ColumnSchema("is_true_duplicate", "bool", description="Hidden ground truth - confirmed by hand"),
        ColumnSchema("aggressive_merge", "bool"),
        ColumnSchema("conservative_merge", "bool"),
    )
)

# Hand-crafted (not random): 50 candidate pairs a fuzzy pre-matching pass
# flagged for review - 40 are genuinely the same person, 10 are two real,
# distinct people who happen to share one strong signal (a phone number, a
# name). The aggressive rule merges anything the pre-match flagged at all;
# the conservative rule only merges pairs where multiple signals agree.
TRUE_DUPLICATES_CAUGHT_BY_BOTH = 34
TRUE_DUPLICATES_MISSED_BY_CONSERVATIVE = 6
TRUE_NON_DUPLICATES_WRONGLY_MERGED_BY_AGGRESSIVE = 10


def _rows() -> list[tuple[int, bool, bool, bool]]:
    rows: list[tuple[int, bool, bool, bool]] = []
    pair_id = 1
    for _ in range(TRUE_DUPLICATES_CAUGHT_BY_BOTH):
        rows.append((pair_id, True, True, True))
        pair_id += 1
    for _ in range(TRUE_DUPLICATES_MISSED_BY_CONSERVATIVE):
        rows.append((pair_id, True, True, False))
        pair_id += 1
    for _ in range(TRUE_NON_DUPLICATES_WRONGLY_MERGED_BY_AGGRESSIVE):
        rows.append((pair_id, False, True, False))
        pair_id += 1
    return rows


def generate_match_results() -> Dataset:
    frame = pd.DataFrame(_rows(), columns=["pair_id", "is_true_duplicate", "aggressive_merge", "conservative_merge"])
    step = PipelineStep(
        "prepared",
        python_code="matches = pd.read_csv('novamart_dedup_review.csv')  # 50 candidate pairs, hand-reviewed",
    )
    return Dataset(name="matches", frame=frame, schema=MATCH_RESULTS_SCHEMA, history=(step,))


def precision(dataset: Dataset, rule_column: str) -> float:
    frame = dataset.frame
    merged = frame[frame[rule_column]]
    if len(merged) == 0:
        return 0.0
    return float(merged["is_true_duplicate"].mean())


def recall(dataset: Dataset, rule_column: str) -> float:
    frame = dataset.frame
    true_duplicates = frame[frame["is_true_duplicate"]]
    return float(true_duplicates[rule_column].mean())
