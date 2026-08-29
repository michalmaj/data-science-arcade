import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

DELIVERY_SURVEY_SCHEMA = Schema(
    columns=(
        ColumnSchema("group_label", "object"),
        ColumnSchema("customer_count", "int64"),
        ColumnSchema("was_surveyed", "bool", description="False if the survey trigger never fires for this group at all"),
        ColumnSchema("satisfied_count", "int64"),
    )
)

# A different NovaMart survey, a different quarter: post-delivery
# satisfaction. The survey only ever fires on a "delivery confirmed"
# event - customers whose delivery failed or was significantly delayed
# never see it at all, so the headline number only ever describes the
# 85% of customers the trigger can even reach. The other 15%'s figure
# comes from a separate source (support-ticket sentiment), not the
# survey - they were never asked.
DELIVERY_SURVEY_ROWS = [
    ("delivery_succeeded", 850, True, 748),
    ("delivery_failed_or_delayed", 150, False, 30),
]


def generate_delivery_survey_data() -> Dataset:
    frame = pd.DataFrame(DELIVERY_SURVEY_ROWS, columns=["group_label", "customer_count", "was_surveyed", "satisfied_count"])
    step = PipelineStep("collected", python_code="delivery_survey = pd.read_csv('novamart_delivery_survey_reach.csv')")
    return Dataset(name="novamart_delivery_survey_reach", frame=frame, schema=DELIVERY_SURVEY_SCHEMA, history=(step,))


def satisfaction_rate(dataset: Dataset, group_label: str) -> float:
    row = dataset.frame[dataset.frame["group_label"] == group_label].iloc[0]
    return float(row["satisfied_count"] / row["customer_count"])


def blended_satisfaction_rate(dataset: Dataset) -> float:
    total_customers = int(dataset.frame["customer_count"].sum())
    total_satisfied = int(dataset.frame["satisfied_count"].sum())
    return total_satisfied / total_customers
