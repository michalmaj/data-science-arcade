import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

FINDINGS_SCHEMA = Schema(
    columns=(
        ColumnSchema("finding_key", "object"),
        ColumnSchema("before_value", "float64"),
        ColumnSchema("after_value", "float64"),
    )
)

# Nine real findings from the same checkout-redesign quarter - hand-
# crafted, not random. Three (completion, payment-step abandonment,
# order-value/returns holding steady) are the actually decision-relevant
# ones; the rest are real numbers that moved for unrelated reasons
# (a viral social post, a market-wide stock rally, a routine engagement
# survey) or are secondary/redundant with a stronger finding already in
# the set.
FINDINGS_ROWS = [
    ("checkout_completion", 68.0, 72.0),
    ("payment_step_abandonment", 22.0, 17.0),
    ("average_order_value", 54.00, 54.20),
    ("return_rate", 8.0, 8.1),
    ("social_mentions", 2000.0, 8000.0),
    ("stock_price", 50.0, 54.5),
    ("employee_satisfaction", 72.0, 77.0),
    ("support_tickets_confusing_checkout", 500.0, 200.0),
    ("competitor_completion_rate", 65.0, 66.0),
]


def generate_findings_data() -> Dataset:
    frame = pd.DataFrame(FINDINGS_ROWS, columns=["finding_key", "before_value", "after_value"])
    step = PipelineStep("collected", python_code="findings = pd.read_csv('novamart_checkout_findings_pool.csv')")
    return Dataset(name="novamart_checkout_findings_pool", frame=frame, schema=FINDINGS_SCHEMA, history=(step,))


def percent_change(dataset: Dataset, finding_key: str) -> float:
    row = dataset.frame[dataset.frame["finding_key"] == finding_key].iloc[0]
    return float((row["after_value"] - row["before_value"]) / row["before_value"])


def point_change(dataset: Dataset, finding_key: str) -> float:
    row = dataset.frame[dataset.frame["finding_key"] == finding_key].iloc[0]
    return float(row["after_value"] - row["before_value"])
