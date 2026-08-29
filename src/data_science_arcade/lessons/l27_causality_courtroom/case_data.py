import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

TOOL_SPEND_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "int64"),
        ColumnSchema("tool_used", "bool", description="Entirely opt-in - nobody was assigned to use it"),
        ColumnSchema("impulse_spend", "float64"),
    )
)

RESOLUTION_SATISFACTION_SCHEMA = Schema(
    columns=(
        ColumnSchema("ticket_id", "int64"),
        ColumnSchema("resolved_under_1hr", "bool"),
        ColumnSchema("satisfaction_score", "float64"),
    )
)

TRAINING_PERFORMANCE_SCHEMA = Schema(
    columns=(
        ColumnSchema("employee_id", "int64"),
        ColumnSchema("completed_training", "bool", description="Entirely optional, unadvertised beyond a single email"),
        ColumnSchema("performance_score", "float64"),
    )
)

# Case 1: customers who turned on the budgeting tool chose to, themselves -
# nobody was assigned. Hand-crafted, not random, verified via script.
TOOL_SPEND_ROWS = [
    (1, True, 42.0), (2, True, 45.0), (3, True, 48.0), (4, True, 40.0), (5, True, 44.0),
    (6, True, 47.0), (7, True, 43.0), (8, True, 46.0), (9, True, 41.0), (10, True, 49.0),
    (11, False, 62.0), (12, False, 65.0), (13, False, 68.0), (14, False, 60.0), (15, False, 64.0),
    (16, False, 67.0), (17, False, 63.0), (18, False, 66.0), (19, False, 61.0), (20, False, 69.0),
]

# Case 2: tickets resolved within an hour are overwhelmingly the simple
# ones - resolution speed is selected by ticket difficulty, not the other
# way around.
RESOLUTION_SATISFACTION_ROWS = [
    (1, True, 92.0), (2, True, 95.0), (3, True, 90.0), (4, True, 96.0), (5, True, 93.0),
    (6, True, 94.0), (7, True, 91.0), (8, True, 97.0), (9, True, 90.0), (10, True, 95.0),
    (11, False, 70.0), (12, False, 72.0), (13, False, 68.0), (14, False, 75.0), (15, False, 71.0),
    (16, False, 69.0), (17, False, 74.0), (18, False, 67.0), (19, False, 73.0), (20, False, 70.0),
]

# Case 3: the training was optional and barely advertised - almost no one
# who wasn't already a strong performer bothered to sign up.
TRAINING_PERFORMANCE_ROWS = [
    (1, True, 85.0), (2, True, 88.0), (3, True, 82.0), (4, True, 90.0), (5, True, 86.0),
    (6, True, 84.0), (7, True, 89.0), (8, True, 83.0), (9, True, 87.0), (10, True, 91.0),
    (11, False, 68.0), (12, False, 70.0), (13, False, 65.0), (14, False, 72.0), (15, False, 69.0),
    (16, False, 67.0), (17, False, 71.0), (18, False, 66.0), (19, False, 73.0), (20, False, 68.0),
]


def generate_tool_spend_data() -> Dataset:
    frame = pd.DataFrame(TOOL_SPEND_ROWS, columns=["customer_id", "tool_used", "impulse_spend"])
    step = PipelineStep("collected", python_code="tool_spend = pd.read_csv('novamart_budget_tool_vs_spend.csv')")
    return Dataset(name="novamart_budget_tool_vs_spend", frame=frame, schema=TOOL_SPEND_SCHEMA, history=(step,))


def generate_resolution_satisfaction_data() -> Dataset:
    frame = pd.DataFrame(RESOLUTION_SATISFACTION_ROWS, columns=["ticket_id", "resolved_under_1hr", "satisfaction_score"])
    step = PipelineStep("collected", python_code="resolution_satisfaction = pd.read_csv('novamart_resolution_vs_satisfaction.csv')")
    return Dataset(name="novamart_resolution_vs_satisfaction", frame=frame, schema=RESOLUTION_SATISFACTION_SCHEMA, history=(step,))


def generate_training_performance_data() -> Dataset:
    frame = pd.DataFrame(TRAINING_PERFORMANCE_ROWS, columns=["employee_id", "completed_training", "performance_score"])
    step = PipelineStep("collected", python_code="training_performance = pd.read_csv('novamart_training_vs_performance.csv')")
    return Dataset(name="novamart_training_vs_performance", frame=frame, schema=TRAINING_PERFORMANCE_SCHEMA, history=(step,))


def compute_correlation(dataset: Dataset, column_a: str, column_b: str) -> float:
    return float(dataset.frame[column_a].astype(float).corr(dataset.frame[column_b].astype(float)))
