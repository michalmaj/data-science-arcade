import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Event A: order_confirmed --------------------------------------------
#
# 90 real sessions reach and complete payment: 84 place exactly one order,
# 6 place two separate real orders in the same session (a real
# repeat-purchase case) -> 84*1 + 6*2 = 96 real distinct orders. Of these
# 96 orders, 18 hit a real "slow gateway response" - the case that
# double-fires order_confirmed if a client-side trigger was chosen.
# Hand-verified: see decisions/IMPLEMENTATION_STATE.md for the arithmetic
# this was checked against before implementation.

SINGLE_ORDER_SESSIONS = 84
REPEAT_PURCHASE_SESSIONS = 6
TOTAL_SESSIONS = SINGLE_ORDER_SESSIONS + REPEAT_PURCHASE_SESSIONS  # 90
TOTAL_ORDERS = SINGLE_ORDER_SESSIONS + REPEAT_PURCHASE_SESSIONS * 2  # 96
SLOW_GATEWAY_ORDERS = 18


def event_a_state(trigger_is_client_side: bool, identifiers_include_order_id: bool) -> str:
    """The 4 real, independent states - trigger and identifiers are two
    separate real choices, not one combined "is Event A okay" flag, and a
    student who broke both needs that named as its own real state, not
    silently folded into whichever single-problem state happened to come
    first in an if/elif chain. Root cause content and Required Change
    scoring both branch on this directly, so a "both" student gets a real
    diagnosis of both mechanisms, not a root-cause line that tells them
    their trigger is fine when it isn't."""
    if trigger_is_client_side and not identifiers_include_order_id:
        return "both"
    if not identifiers_include_order_id:
        return "identifiers"
    if trigger_is_client_side:
        return "trigger"
    return "clean"


def event_a_clean(trigger_is_client_side: bool, identifiers_include_order_id: bool) -> bool:
    """Collapses the 4 real states to the one flag EVIDENCE's own expected-
    category-count still uses (2 categories on the clean path, 3
    otherwise, regardless of which specific problem - or both - a
    not-clean student actually has). Ship-readiness/Required-change no
    longer use this collapsed flag directly - see event_a_state above."""
    return event_a_state(trigger_is_client_side, identifiers_include_order_id) == "clean"


def order_confirmed_counts(
    trigger_is_client_side: bool, identifiers_include_order_id: bool
) -> tuple[int, int, str]:
    """(raw row count, the honest second value, that value's label key)
    for Event A's reveal. The second value is the real distinct order_id
    count (96, always the true order count, whenever order_id was
    captured) or the distinct session_id count (90) when it wasn't - a
    genuinely different, wrong answer to "how many orders," not just a
    less precise one, since 6 sessions each placed two real orders."""
    raw = TOTAL_ORDERS + (SLOW_GATEWAY_ORDERS if trigger_is_client_side else 0)
    if identifiers_include_order_id:
        return raw, TOTAL_ORDERS, "lesson.l04.reveal.distinct_order_id_label"
    return raw, TOTAL_SESSIONS, "lesson.l04.reveal.distinct_session_id_label"


ORDER_CONFIRMED_RAW_PYTHON_CODE = (
    "orders = pd.read_csv('novamart_go_order_confirmed.csv')  # one row per event firing\n"
    "len(orders)"
)
ORDER_CONFIRMED_DISTINCT_ORDER_PYTHON_CODE = "orders['order_id'].nunique()"
ORDER_CONFIRMED_DISTINCT_SESSION_PYTHON_CODE = (
    "orders['session_id'].nunique()  # order_id was never captured - this is the closest available count"
)

# --- Event B: payment_attempted -------------------------------------------
#
# 150 total payment attempts: 96 succeed (matching the 96 real orders
# above 1:1), 40 are declined, 14 error out (96+40+14=150). Only the 96
# successful attempts get a real order_id (assigned once an order is
# actually placed) - a declined or errored attempt has none, by design,
# not as a data quality bug.

APPROVED_ATTEMPTS = 96
DECLINED_ATTEMPTS = 40
ERROR_ATTEMPTS = 14
TOTAL_ATTEMPTS = APPROVED_ATTEMPTS + DECLINED_ATTEMPTS + ERROR_ATTEMPTS  # 150

PAYMENT_ATTEMPTED_SCHEMA_WITH_OUTCOME = Schema(
    columns=(
        ColumnSchema("session_id", "int64", description_key="lesson.l04.schema.session_id.description"),
        ColumnSchema("order_id", "float64", nullable=True, description_key="lesson.l04.schema.order_id.description"),
        ColumnSchema("outcome", "object", description_key="lesson.l04.schema.outcome.description"),
    )
)
PAYMENT_ATTEMPTED_SCHEMA_WITHOUT_OUTCOME = Schema(
    columns=(
        ColumnSchema("session_id", "int64", description_key="lesson.l04.schema.session_id.description"),
        ColumnSchema("order_id", "float64", nullable=True, description_key="lesson.l04.schema.order_id.description"),
    )
)
"""No `outcome` column at all when it wasn't captured - the student sees
the field genuinely missing from the schema, not present-but-empty."""


def _interleaved_outcomes() -> list[str]:
    """Round-robins through the three outcome buckets instead of leaving
    them grouped, so even a short head() slice of the table shows a real
    mix of approved/declined/error rather than 96 approved rows before a
    decline ever appears."""
    buckets = [["approved"] * APPROVED_ATTEMPTS, ["declined"] * DECLINED_ATTEMPTS, ["error"] * ERROR_ATTEMPTS]
    ordered: list[str] = []
    while any(buckets):
        for bucket in buckets:
            if bucket:
                ordered.append(bucket.pop(0))
    return ordered


def _approved_session_sequence() -> list[int]:
    """96 session_id values, one per approved payment attempt: sessions
    1-84 appear once each (single-order sessions), sessions 85-90 appear
    twice each (the real repeat-purchase sessions) - 84 + 6*2 = 96,
    matching TOTAL_ORDERS exactly."""
    single_sessions = list(range(1, SINGLE_ORDER_SESSIONS + 1))
    repeat_sessions = range(SINGLE_ORDER_SESSIONS + 1, TOTAL_SESSIONS + 1)
    repeated_twice = [session_id for session_id in repeat_sessions for _ in range(2)]
    return single_sessions + repeated_twice


def _payment_attempt_rows() -> list[tuple[int, float | None, str]]:
    outcomes = _interleaved_outcomes()
    approved_sessions = _approved_session_sequence()
    rows: list[tuple[int, float | None, str]] = []
    next_order_id = 1
    approved_index = 0
    next_failure_session = TOTAL_SESSIONS + 1  # 91+ - failed attempts get their own distinct sessions
    for outcome in outcomes:
        if outcome == "approved":
            session_id = approved_sessions[approved_index]
            approved_index += 1
            rows.append((session_id, float(next_order_id), outcome))
            next_order_id += 1
        else:
            rows.append((next_failure_session, None, outcome))
            next_failure_session += 1
    return rows


def _payment_attempted_frame() -> pd.DataFrame:
    rows = _payment_attempt_rows()
    return pd.DataFrame(rows, columns=["session_id", "order_id", "outcome"])


def generate_payment_attempts(outcome_captured: bool) -> Dataset:
    frame = _payment_attempted_frame()
    if outcome_captured:
        step = PipelineStep(
            "prepared", python_code="payments = pd.read_csv('novamart_go_payment_attempted.csv')"
        )
        return Dataset(
            name="payment_attempted",
            frame=frame,
            schema=PAYMENT_ATTEMPTED_SCHEMA_WITH_OUTCOME,
            history=(step,),
        )
    step = PipelineStep(
        "prepared",
        python_code="payments = pd.read_csv('novamart_go_payment_attempted.csv')  # no outcome column recorded",
    )
    return Dataset(
        name="payment_attempted",
        frame=frame.drop(columns=["outcome"]),
        schema=PAYMENT_ATTEMPTED_SCHEMA_WITHOUT_OUTCOME,
        history=(step,),
    )


def outcome_breakdown_python_code() -> str:
    return "payments['outcome'].value_counts()"


# --- Optional mastery: a different flow, a real transfer -----------------
#
# 80 real signups; 22 used "Sign up with Google," whose OAuth callback
# fires account_created once on the initial redirect and again on the
# callback confirmation - raw 80+22=102, distinct user_id 80. The same
# raw-vs-distinct skill as Event A's own duplicate-trigger story,
# transferred to a different flow and a different concrete mechanism
# (OAuth callback vs. slow-gateway retry), not a repeat of the required
# path's own trap.

MASTERY_REAL_SIGNUPS = 80
MASTERY_GOOGLE_OAUTH_SIGNUPS = 22
MASTERY_RAW_ACCOUNT_CREATED = MASTERY_REAL_SIGNUPS + MASTERY_GOOGLE_OAUTH_SIGNUPS  # 102

MASTERY_RAW_PYTHON_CODE = (
    "signups = pd.read_csv('novamart_go_account_created.csv')\nlen(signups)"
)
MASTERY_DISTINCT_PYTHON_CODE = "signups['user_id'].nunique()"
