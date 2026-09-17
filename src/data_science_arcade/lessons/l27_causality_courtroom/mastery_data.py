import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

EXPRESS_SHIPPING_SCHEMA = Schema(
    columns=(
        ColumnSchema("group", "object"),
        ColumnSchema("customer_count", "int64"),
        ColumnSchema("repeat_purchase_rate", "float64"),
    )
)

# A new NovaMart domain for mastery - no existing L27 dataset was left
# over to promote here (checkout_beta is this lesson's own mandatory
# Twist, not available for mastery). Express shipping was initially
# optional, and customers who were already frequent, repeat shoppers were
# disproportionately the ones who opted in - a given operational fact,
# not derived from any baseline column in this small dataset (matching
# every one of the three main cases' own "given fact, never a
# stratifiable one" shape). A later randomized free-trial offer found a
# much smaller effect than the naive opt-in comparison suggested -
# mirroring checkout_beta's own dramatic-naive/modest-real shape
# deliberately, since mastery tests the same reflex in a new context, not
# a different one.
EXPRESS_SHIPPING_ROWS = [
    ("opt_in", 400, 0.68),
    ("non_opt_in", 400, 0.31),
    ("randomized_treatment", 250, 0.36),
    ("randomized_control", 250, 0.31),
]


def generate_express_shipping_data() -> Dataset:
    frame = pd.DataFrame(EXPRESS_SHIPPING_ROWS, columns=["group", "customer_count", "repeat_purchase_rate"])
    step = PipelineStep("collected", python_code="express_shipping = pd.read_csv('novamart_express_shipping_selection.csv')")
    return Dataset(name="novamart_express_shipping_selection", frame=frame, schema=EXPRESS_SHIPPING_SCHEMA, history=(step,))


def repeat_purchase_rate(dataset: Dataset, group: str) -> float:
    row = dataset.frame[dataset.frame["group"] == group].iloc[0]
    return float(row["repeat_purchase_rate"])


def group_gap_mirror_code(dataset_var: str, group_a: str, group_b: str, var_name: str) -> str:
    """FINAL {var_name} is the real difference between two named groups'
    own repeat_purchase_rate - covers both the naive gap (0.37) and the
    randomized gap (0.05)."""
    return "\n".join(
        (
            f'{var_name}_a = {dataset_var}[{dataset_var}["group"] == "{group_a}"]["repeat_purchase_rate"].iloc[0]',
            f'{var_name}_b = {dataset_var}[{dataset_var}["group"] == "{group_b}"]["repeat_purchase_rate"].iloc[0]',
            f"{var_name} = float({var_name}_a - {var_name}_b)",
        )
    )
