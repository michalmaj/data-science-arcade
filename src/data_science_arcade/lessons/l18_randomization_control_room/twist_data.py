import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

PLATFORM_SPLIT_SCHEMA = Schema(
    columns=(
        ColumnSchema("group", "object", description="'treatment' or 'control' under the rule NovaMart actually shipped"),
        ColumnSchema("customer_count", "int64"),
        ColumnSchema("ios_count", "int64", description="customers on iOS - a platform, never checked before this rollout shipped"),
    )
)

# NovaMart already shipped a referral-bonus rollout using customer-ID
# parity, the same rule the player just diagnosed elsewhere in this
# lesson - the team checked group size before launch (500/500, a clean
# sample-ratio check) and stopped there. A platform migration had
# allocated iOS customers' IDs from a mostly-even block, so the "random-
# looking" parity split is actually a near-even/rest-of-the-world split -
# a confound nobody thought to check because the sample-ratio check alone
# looked fine.
PLATFORM_ROWS = [
    ("treatment", 500, 340),
    ("control", 500, 120),
]


def generate_platform_split_data() -> Dataset:
    frame = pd.DataFrame(PLATFORM_ROWS, columns=["group", "customer_count", "ios_count"])
    step = PipelineStep("collected", python_code="referral_rollout = pd.read_csv('novamart_referral_bonus_rollout.csv')")
    return Dataset(name="referral_bonus_rollout", frame=frame, schema=PLATFORM_SPLIT_SCHEMA, history=(step,))


def ios_share(dataset: Dataset, group: str) -> float:
    row = dataset.frame[dataset.frame["group"] == group].iloc[0]
    return float(row["ios_count"] / row["customer_count"])
