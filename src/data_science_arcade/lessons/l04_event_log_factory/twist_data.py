import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

EVENTS_SCHEMA = Schema(
    columns=(
        ColumnSchema("session_id", "int64"),
        ColumnSchema("event_name", "object"),
    )
)

# Hand-crafted (not random): every session that starts checkout fires
# checkout_started, and a clean majority go on to fire order_confirmed - but
# payment_info_entered never fires at all. Not a shortfall like Lesson 03's
# partial pages - the event was never wired up on the NovaMart Go side, so
# it's not "incomplete," it's completely absent from the log.
TOTAL_SESSIONS = 200
CONFIRMED_SESSIONS = 124
MISSING_EVENT = "payment_info_entered"


def _event_rows() -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = [(session_id, "checkout_started") for session_id in range(1, TOTAL_SESSIONS + 1)]
    rows += [(session_id, "order_confirmed") for session_id in range(1, CONFIRMED_SESSIONS + 1)]
    return rows


def generate_checkout_events() -> Dataset:
    frame = pd.DataFrame(_event_rows(), columns=["session_id", "event_name"])
    step = PipelineStep(
        "prepared",
        python_code="events = pd.read_csv('novamart_go_events.csv')  # one row per event firing",
    )
    return Dataset(name="events", frame=frame, schema=EVENTS_SCHEMA, history=(step,))


def event_rate(dataset: Dataset, event_name: str) -> float:
    """Fraction of all checkout sessions where this event fired at least
    once. payment_info_entered falls out to 0.0 here not by special-casing
    it, but because the rows genuinely don't exist in the frame."""
    sessions_with_event = dataset.frame.loc[dataset.frame["event_name"] == event_name, "session_id"].nunique()
    return sessions_with_event / TOTAL_SESSIONS
