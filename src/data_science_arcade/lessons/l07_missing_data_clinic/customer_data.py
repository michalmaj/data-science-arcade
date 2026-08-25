import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

FULL_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "int64"),
        ColumnSchema("segment", "object"),
        ColumnSchema("engagement_score", "float64", nullable=True, description="Missing for some at-risk customers"),
        ColumnSchema("true_engagement_score", "float64", description="Hidden ground truth - never shown during play"),
    )
)

# Hand-crafted (not random): missingness is NOT random - it's concentrated
# entirely in the at-risk segment, and correlated with how disengaged those
# customers already are (the ones who still bother to respond skew higher
# than the ones who don't). Regular customers: mostly high engagement with
# a low-scoring minority (creates a real mean/median gap). At-risk
# customers: those who responded score moderately; those who didn't
# (missing) would have scored even lower, had anyone recorded it.
REGULAR_HIGH = (130, 80.0)
REGULAR_LOW = (10, 10.0)
AT_RISK_PRESENT = (35, 40.0)
AT_RISK_MISSING = (15, 20.0)  # true_engagement_score only - engagement_score is NaN


def generate_customers() -> Dataset:
    rows: list[tuple[int, str, float, float]] = []
    customer_id = 1
    for _ in range(REGULAR_HIGH[0]):
        rows.append((customer_id, "regular", REGULAR_HIGH[1], REGULAR_HIGH[1]))
        customer_id += 1
    for _ in range(REGULAR_LOW[0]):
        rows.append((customer_id, "regular", REGULAR_LOW[1], REGULAR_LOW[1]))
        customer_id += 1
    for _ in range(AT_RISK_PRESENT[0]):
        rows.append((customer_id, "at_risk", AT_RISK_PRESENT[1], AT_RISK_PRESENT[1]))
        customer_id += 1
    for _ in range(AT_RISK_MISSING[0]):
        rows.append((customer_id, "at_risk", float("nan"), AT_RISK_MISSING[1]))
        customer_id += 1

    frame = pd.DataFrame(rows, columns=["customer_id", "segment", "engagement_score", "true_engagement_score"])
    step = PipelineStep(
        "prepared",
        python_code="customers = pd.read_csv('novamart_plus_engagement.csv')  # engagement_score missing for some at-risk customers",
    )
    return Dataset(name="customers", frame=frame, schema=FULL_SCHEMA, history=(step,))


def true_population_mean(dataset: Dataset) -> float:
    """The hidden ground truth - what the average would be if every
    customer's real engagement had been recorded. Never shown until the
    twist reveal."""
    return float(dataset.frame["true_engagement_score"].mean())


def drop_rows_mean(dataset: Dataset) -> float:
    return float(dataset.frame["engagement_score"].dropna().mean())


def mean_imputed_mean(dataset: Dataset) -> float:
    filled = dataset.frame["engagement_score"].fillna(dataset.frame["engagement_score"].mean())
    return float(filled.mean())


def median_imputed_mean(dataset: Dataset) -> float:
    filled = dataset.frame["engagement_score"].fillna(dataset.frame["engagement_score"].median())
    return float(filled.mean())


def segment_imputed_mean(dataset: Dataset) -> float:
    frame = dataset.frame
    segment_means = frame.groupby("segment")["engagement_score"].transform("mean")
    filled = frame["engagement_score"].fillna(segment_means)
    return float(filled.mean())


def missing_count(dataset: Dataset) -> int:
    return int(dataset.frame["engagement_score"].isna().sum())


def present_count(dataset: Dataset) -> int:
    return int(dataset.frame["engagement_score"].notna().sum())
