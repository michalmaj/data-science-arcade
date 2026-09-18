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
# crafted, not random - for one stated decision: should NovaMart keep
# the checkout redesign in production, and what should leadership
# monitor next? Three tiers, deliberately not a flat true/false split:
# (1) three headline-candidate findings (completion, payment-step
# abandonment, order-value/returns holding steady) that together cover
# three distinct facets of that decision - the direct outcome, the
# process/friction mechanism behind it, and a guardrail check for a
# hidden cost; (2) two real, on-topic findings that don't add a new
# facet under a short brief's budget - support_tickets is real,
# checkout-specific, and directionally consistent with payment-step
# abandonment, but doesn't tell leadership anything the abandonment
# number doesn't already say; competitor_completion_rate is real and
# relevant, but as a limitation on the story (see caveats), not as
# supporting evidence for it; (3) three real numbers with no stated
# connection to the checkout decision at all, given as provenance facts
# in their own descriptions (a viral social post, a market-wide stock
# rally, a routine engagement survey) - real and dramatic, but nothing
# in this dataset or its own given context connects them to the
# decision being briefed.
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


def point_change_mirror_code(finding_key: str, var_name: str) -> str:
    """FINAL {var_name} is the same real point_change() output - a real
    pandas row lookup and subtraction, ending on a named variable (never
    a bare expression an exec() couldn't inspect afterward), matching
    the same dataset_var="findings" every other Finding in this pool
    reads from."""
    return "\n".join(
        (
            f'{var_name}_row = findings[findings["finding_key"] == "{finding_key}"].iloc[0]',
            f'{var_name} = float({var_name}_row["after_value"] - {var_name}_row["before_value"])',
        )
    )


def percent_change_mirror_code(finding_key: str, var_name: str) -> str:
    """FINAL {var_name} is the same real percent_change() output - see
    point_change_mirror_code's own docstring for why this ends on a
    named variable rather than a bare expression."""
    return "\n".join(
        (
            f'{var_name}_row = findings[findings["finding_key"] == "{finding_key}"].iloc[0]',
            f'{var_name} = float(({var_name}_row["after_value"] - {var_name}_row["before_value"]) / {var_name}_row["before_value"])',
        )
    )
