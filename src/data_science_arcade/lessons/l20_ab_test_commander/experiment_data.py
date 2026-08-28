import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

CHECKOUT_EXPERIMENT_SCHEMA = Schema(
    columns=(
        ColumnSchema("checkpoint", "int64"),
        ColumnSchema("day", "int64"),
        ColumnSchema("metric_key", "object"),
        ColumnSchema("group", "object", description="'treatment' or 'control'"),
        ColumnSchema("visits", "int64"),
        ColumnSchema("conversions", "int64", description="a hit for whatever metric_key tracks - not always a purchase"),
    )
)

CHECKPOINT_DAYS = {1: 3, 2: 10, 3: 21}
TOTAL_RUNTIME_DAYS = 21

# Hand-crafted (not random) cumulative reads of one real checkout
# experiment at three points in its run - day 3, day 10, and day 21 (the
# planned end). The primary metric's early read (a striking +4.5pt lift on
# a small, 2,000-visit sample) narrows every checkpoint and is nearly gone
# by the full 21-day sample (+0.3pt on 16,000 visits) - real cumulative
# rates from real counts, not a hand-picked headline number. Both
# guardrails and the mobile segment stay essentially flat the entire run:
# this experiment's problem is never a guardrail breach, it's an early
# statistical illusion that more data resolves - a different failure mode
# than Lesson 18's biased assignment or Lesson 19's too-small-to-matter
# effect, deliberately not repeating either.
ROWS = [
    (1, 3, "primary_conversion", "treatment", 2000, 530),
    (1, 3, "primary_conversion", "control", 2000, 440),
    (1, 3, "guardrail_refund", "treatment", 2000, 60),
    (1, 3, "guardrail_refund", "control", 2000, 58),
    (1, 3, "guardrail_support", "treatment", 2000, 98),
    (1, 3, "guardrail_support", "control", 2000, 96),
    (1, 3, "segment_mobile", "treatment", 1200, 300),
    (1, 3, "segment_mobile", "control", 1200, 264),
    (2, 10, "primary_conversion", "treatment", 8000, 1904),
    (2, 10, "primary_conversion", "control", 8000, 1768),
    (2, 10, "guardrail_refund", "treatment", 8000, 232),
    (2, 10, "guardrail_refund", "control", 8000, 240),
    (2, 10, "guardrail_support", "treatment", 8000, 384),
    (2, 10, "guardrail_support", "control", 8000, 392),
    (2, 10, "segment_mobile", "treatment", 4800, 1104),
    (2, 10, "segment_mobile", "control", 4800, 1056),
    (3, 21, "primary_conversion", "treatment", 16000, 3568),
    (3, 21, "primary_conversion", "control", 16000, 3520),
    (3, 21, "guardrail_refund", "treatment", 16000, 480),
    (3, 21, "guardrail_refund", "control", 16000, 464),
    (3, 21, "guardrail_support", "treatment", 16000, 768),
    (3, 21, "guardrail_support", "control", 16000, 784),
    (3, 21, "segment_mobile", "treatment", 9600, 2112),
    (3, 21, "segment_mobile", "control", 9600, 2112),
]


def generate_checkout_experiment_data() -> Dataset:
    frame = pd.DataFrame(ROWS, columns=["checkpoint", "day", "metric_key", "group", "visits", "conversions"])
    step = PipelineStep("collected", python_code="checkout_experiment = pd.read_csv('novamart_checkout_experiment.csv')")
    return Dataset(name="checkout_experiment", frame=frame, schema=CHECKOUT_EXPERIMENT_SCHEMA, history=(step,))


def rate_at_checkpoint(dataset: Dataset, checkpoint: int, metric_key: str, group: str) -> float:
    frame = dataset.frame
    rows = frame[(frame["checkpoint"] == checkpoint) & (frame["metric_key"] == metric_key) & (frame["group"] == group)]
    return float(rows["conversions"].sum() / rows["visits"].sum())
