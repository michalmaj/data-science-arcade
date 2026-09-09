import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Ground truth (hand-verified, hand-picked - not randomized) -----------
#
# NovaMart Retail's order_value feed mixes two real customer populations:
# consumer orders cluster low ($25-75); business orders cluster high
# ($600-900) - nothing in between, a real, hard, non-overlapping gap
# (consumer max $75 < business min $600). No `segment` column exists
# anywhere in this player-facing frame or its own schema - unlike the
# original slice, which listed a `segment` column with only a "hidden
# ground truth" comment as its own protection. The real segment mapping
# lives only in order_value_segments() below, called only by the
# segment-reveal stage / scoring / tests, and is never threaded into any
# player-facing scene before that stage - see the L11 rebuild's own
# construction tests (test_lesson11_data.py) for the real, structural
# guarantee this gives, not just a documentation comment.

CONSUMER_COUNT = 70
CONSUMER_MIN = 25.0
CONSUMER_STEP = 5.0
CONSUMER_CYCLE = 11  # values 25, 30, ..., 75

BUSINESS_COUNT = 30
BUSINESS_MIN = 600.0
BUSINESS_STEP = 50.0
BUSINESS_CYCLE = 7  # values 600, 650, ..., 900

ORDER_VALUES_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "string"),
        ColumnSchema("order_value", "float64"),
    )
)


def _consumer_values() -> list[float]:
    return [CONSUMER_MIN + (i % CONSUMER_CYCLE) * CONSUMER_STEP for i in range(CONSUMER_COUNT)]


def _business_values() -> list[float]:
    return [BUSINESS_MIN + (i % BUSINESS_CYCLE) * BUSINESS_STEP for i in range(BUSINESS_COUNT)]


def order_values_list() -> list[float]:
    return _consumer_values() + _business_values()


def generate_order_values() -> Dataset:
    """The player-facing feed - order_id/order_value only. No segment
    column, no hidden field of any kind: every column in this frame is
    genuinely visible from the first stage onward."""
    values = order_values_list()
    frame = pd.DataFrame(
        {
            "order_id": [f"ORD-{index + 1:04d}" for index in range(len(values))],
            "order_value": values,
        }
    )
    step = PipelineStep("collected", python_code="orders = pd.read_csv('novamart_order_values.csv')")
    return Dataset(name="order_values", frame=frame, schema=ORDER_VALUES_SCHEMA, history=(step,))


def order_value_segments() -> tuple[tuple[str, str, list[float]], ...]:
    """The real segment mapping - (key, label_key, values) triples. Called
    only by the segment-reveal stage, scoring, and tests; never merged
    into generate_order_values()'s own Dataset/Schema, and never passed
    into any scene before the reveal stage."""
    return (
        ("consumer", "lesson.l11.segment.consumer_label", _consumer_values()),
        ("business", "lesson.l11.segment.business_label", _business_values()),
    )


def segment_mean(segment: str) -> float:
    for key, _label_key, values in order_value_segments():
        if key == segment:
            return sum(values) / len(values)
    raise KeyError(segment)


# --- Optional mastery - same mean, wildly different distribution ----------
#
# Two hand-verified processes, deliberately not a repeat of the bimodal-
# mix shape: Process A (tight, symmetric, 30 rows across 27-33 minutes)
# and Process B (real right-skew, 24 rows at 20 minutes + 6 rows at 70
# minutes) share the exact same mean (30.0) but a wildly different
# median/spread/shape - the real transfer question is whether "same
# mean" alone lets you call two processes practically the same.

PROCESS_A_VALUES: tuple[float, ...] = tuple(
    float(v)
    for v in (
        [27] * 3
        + [28] * 4
        + [29] * 5
        + [30] * 6
        + [31] * 5
        + [32] * 4
        + [33] * 3
    )
)  # 30 rows, mean=30.0, median=30.0

PROCESS_B_VALUES: tuple[float, ...] = tuple(float(v) for v in ([20] * 24 + [70] * 6))  # 30 rows, mean=30.0, median=20.0


def mastery_process_series() -> tuple[tuple[str, str, list[float]], ...]:
    return (
        ("process_a", "lesson.l11.mastery.process_a_label", list(PROCESS_A_VALUES)),
        ("process_b", "lesson.l11.mastery.process_b_label", list(PROCESS_B_VALUES)),
    )
