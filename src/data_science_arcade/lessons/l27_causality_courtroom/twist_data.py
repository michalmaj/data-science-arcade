import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

CHECKOUT_BETA_SCHEMA = Schema(
    columns=(
        ColumnSchema("group", "object"),
        ColumnSchema("customer_count", "int64"),
        ColumnSchema("conversion_rate", "float64"),
    )
)

# A different NovaMart case, a different quarter: an opt-in checkout beta
# looked like a huge win - beta users converted far more than everyone
# else. But beta access was entirely self-selected, not assigned. A later
# randomized test (real random assignment, not opt-in) found a much
# smaller effect than the observational gap suggested. The observational
# comparison mixes the checkout's own effect with the fact that customers
# who opt into a beta are already different shoppers - real, but not
# something this toy dataset can cleanly decompose into an exact
# percentage. Student-facing copy must say the randomized comparison
# ESTIMATES a much smaller effect than the observational gap, never claim
# a precise "X% was selection, Y% was the real effect" breakdown, and
# never call the randomized number "the true effect" - it is what a
# randomized comparison estimates, not a known exact causal ground truth.
CHECKOUT_BETA_ROWS = [
    ("beta_opt_in", 500, 0.42),
    ("non_beta", 500, 0.17),
    ("randomized_treatment", 300, 0.19),
    ("randomized_control", 300, 0.17),
]


def generate_checkout_beta_data() -> Dataset:
    frame = pd.DataFrame(CHECKOUT_BETA_ROWS, columns=["group", "customer_count", "conversion_rate"])
    step = PipelineStep("collected", python_code="checkout_beta = pd.read_csv('novamart_checkout_beta_selection.csv')")
    return Dataset(name="novamart_checkout_beta_selection", frame=frame, schema=CHECKOUT_BETA_SCHEMA, history=(step,))


def conversion_rate(dataset: Dataset, group: str) -> float:
    row = dataset.frame[dataset.frame["group"] == group].iloc[0]
    return float(row["conversion_rate"])


def group_gap_mirror_code(dataset_var: str, group_a: str, group_b: str, var_name: str) -> str:
    """FINAL {var_name} is the real difference between two named groups'
    own conversion_rate - covers both the observational gap and the
    randomized gap with one function. Verified via direct exec (0.25 for
    beta_opt_in-non_beta, 0.02 for randomized_treatment-randomized_control)."""
    return "\n".join(
        (
            f'{var_name}_a = {dataset_var}[{dataset_var}["group"] == "{group_a}"]["conversion_rate"].iloc[0]',
            f'{var_name}_b = {dataset_var}[{dataset_var}["group"] == "{group_b}"]["conversion_rate"].iloc[0]',
            f"{var_name} = float({var_name}_a - {var_name}_b)",
        )
    )
