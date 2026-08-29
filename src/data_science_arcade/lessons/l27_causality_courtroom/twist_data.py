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
# randomized test (real random assignment, not opt-in) found the new
# checkout's actual effect was a small fraction of that gap - the rest
# was just beta users already being more engaged shoppers.
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
