import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

ONBOARDING_SCHEMA = Schema(
    columns=(
        ColumnSchema("metric_key", "object"),
        ColumnSchema("count", "int64"),
    )
)

# A separate, already-closed investigation: the mobile app team's
# onboarding funnel, which used a flawed signup-completion event (missing
# on one login provider) - not the checkout funnel the player just built.
# The flawed count made signup look like the funnel's worst step, so the
# team spent a quarter redesigning signup; profile completion, the real
# worst step once signup is counted correctly, was never investigated
# because the flawed funnel never made it look like a problem.
ONBOARDING_ROWS = [
    ("app_install", 5000),
    ("signup_completed_flawed", 1750),
    ("signup_completed_correct", 4050),
    ("profile_completed", 1701),
]


def generate_onboarding_data() -> Dataset:
    frame = pd.DataFrame(ONBOARDING_ROWS, columns=["metric_key", "count"])
    step = PipelineStep("collected", python_code="onboarding = pd.read_csv('novamart_app_onboarding_funnel.csv')")
    return Dataset(name="app_onboarding_funnel", frame=frame, schema=ONBOARDING_SCHEMA, history=(step,))


def _count(dataset: Dataset, metric_key: str) -> int:
    return int(dataset.frame[dataset.frame["metric_key"] == metric_key]["count"].iloc[0])


def signup_rate(dataset: Dataset, flawed: bool) -> float:
    install = _count(dataset, "app_install")
    completed = _count(dataset, "signup_completed_flawed" if flawed else "signup_completed_correct")
    return completed / install


def profile_completion_rate(dataset: Dataset) -> float:
    signup = _count(dataset, "signup_completed_correct")
    profile = _count(dataset, "profile_completed")
    return profile / signup
