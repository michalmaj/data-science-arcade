import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

ASSIGNMENT_SCHEMA = Schema(
    columns=(
        ColumnSchema("experiment_key", "object"),
        ColumnSchema("rule_key", "object", description="the candidate assignment rule being diagnosed"),
        ColumnSchema("group", "object", description="'treatment' or 'control' under that rule"),
        ColumnSchema("customer_count", "int64"),
        ColumnSchema("covariate_count", "int64", description="customers with the one attribute this experiment cares about"),
        ColumnSchema("tenure_sum", "int64", description="sum of tenure_days across this group, for a real average"),
    )
)

# Hand-crafted (not random) per-rule assignment outcomes for three
# candidate rules across three experiments. Every rule guarantees nothing
# by its label alone - each is deterministic (alternate request order,
# customer-ID parity, signup-week parity), and exactly one per experiment
# turns out balanced on both sample size and the covariate that experiment
# actually cares about; the other two are each broken in a different real
# way (a covariate correlated with the rule despite perfect group sizes,
# or a rule that breaks group size and a covariate at once). Percentages
# and averages anywhere in this lesson are computed from these counts, not
# hand-picked headline numbers.
ROWS = [
    # checkout_redesign - covariate: mobile_share. Correct rule: order_alternation.
    ("checkout_redesign", "order_alternation", "treatment", 510, 280, 108120),
    ("checkout_redesign", "order_alternation", "control", 490, 250, 101920),
    ("checkout_redesign", "id_parity", "treatment", 500, 355, 105000),
    ("checkout_redesign", "id_parity", "control", 500, 175, 104500),
    ("checkout_redesign", "signup_week", "treatment", 640, 339, 115200),
    ("checkout_redesign", "signup_week", "control", 360, 198, 93600),
    # loyalty_discount_test - covariate: referral_share. Correct rule: id_parity.
    ("loyalty_discount_test", "order_alternation", "treatment", 495, 188, 94050),
    ("loyalty_discount_test", "order_alternation", "control", 505, 71, 98475),
    ("loyalty_discount_test", "id_parity", "treatment", 500, 120, 100000),
    ("loyalty_discount_test", "id_parity", "control", 500, 110, 99000),
    ("loyalty_discount_test", "signup_week", "treatment", 580, 133, 101500),
    ("loyalty_discount_test", "signup_week", "control", 420, 105, 100800),
    # notification_frequency_test - covariate: high_spend_share. Correct rule: signup_week.
    ("notification_frequency_test", "order_alternation", "treatment", 505, 152, 110595),
    ("notification_frequency_test", "order_alternation", "control", 495, 74, 109395),
    ("notification_frequency_test", "id_parity", "treatment", 500, 95, 97500),
    ("notification_frequency_test", "id_parity", "control", 500, 90, 125000),
    ("notification_frequency_test", "signup_week", "treatment", 498, 85, 111054),
    ("notification_frequency_test", "signup_week", "control", 502, 95, 109938),
]


def generate_assignment_data() -> Dataset:
    frame = pd.DataFrame(ROWS, columns=["experiment_key", "rule_key", "group", "customer_count", "covariate_count", "tenure_sum"])
    step = PipelineStep("collected", python_code="assignments = pd.read_csv('novamart_experiment_assignments.csv')")
    return Dataset(name="experiment_assignments", frame=frame, schema=ASSIGNMENT_SCHEMA, history=(step,))


def _rows(dataset: Dataset, experiment_key: str, rule_key: str, group: str) -> pd.DataFrame:
    frame = dataset.frame
    return frame[(frame["experiment_key"] == experiment_key) & (frame["rule_key"] == rule_key) & (frame["group"] == group)]


def group_size(dataset: Dataset, experiment_key: str, rule_key: str, group: str) -> int:
    return int(_rows(dataset, experiment_key, rule_key, group)["customer_count"].sum())


def covariate_rate(dataset: Dataset, experiment_key: str, rule_key: str, group: str) -> float:
    rows = _rows(dataset, experiment_key, rule_key, group)
    return float(rows["covariate_count"].sum() / rows["customer_count"].sum())


def average_tenure(dataset: Dataset, experiment_key: str, rule_key: str, group: str) -> float:
    rows = _rows(dataset, experiment_key, rule_key, group)
    return float(rows["tenure_sum"].sum() / rows["customer_count"].sum())


def relative_imbalance(before: float, after: float) -> bool:
    """A magnitude-based imbalance check for SegmentSlicerScene's flag_check
    (Lesson 18's reuse): flags a row whenever the gap between the two sides
    is large relative to their average, regardless of which side is bigger
    - unlike a before/after decline, an imbalanced treatment/control split
    isn't inherently "bad" in one particular direction."""
    average = (before + after) / 2
    if average == 0:
        return before != after
    return abs(after - before) / average > 0.15
