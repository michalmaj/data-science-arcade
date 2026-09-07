import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairOption, RepairResolution, apply_resolution

# --- Ground truth (hand-verified, hand-picked - not randomized) -----------
#
# NovaMart Logistics' fulfillment_cost (dollars per order), two delivery
# zones. 89 orders. Urban: 13 distinct integer dollar values $40-$52,
# each appearing exactly 6 times (78 rows) - a real, tight, unremarkable
# distribution - plus 3 hand-injected special rows, each a genuinely
# different mechanism, deliberately all in the urban zone so the segment
# story (case 3) stays isolated to zone rather than tangled up with the
# individual-row cases:
#
#   U-9001 - a real data-entry/decimal error. Its own recorded
#   fulfillment_cost ($4,600.00) is wrong; a separate, real
#   invoice_reference_amount ($46.00) - populated only for this one row -
#   is the actual provenance a correction has to be grounded in. Never
#   "4600 looks weird so it must be 46."
#
#   U-9002 - a rare-but-legitimate enterprise/bulk order ($950.00), real
#   and correctly recorded. Its own order_type="enterprise_bulk" is what
#   actually excludes it from the standard-order population - a real
#   business-metadata fact, independent of how large its own cost value
#   happens to be, never inferred from the value itself.
#
#   U-9003 - a real, documented operational anomaly ($410.00, genuinely
#   correct). Its own incident_reference names a real logged incident -
#   it must be kept and flagged, never silently corrected or dropped.
#
# Remote zone - 8 rows, all normal ($70-$84, one each) - a real,
# structural segment effect (distance/fuel surcharge), not noise: every
# one of them reads as an outlier against the *global* IQR fence, and
# none of them do against the zone's own.
#
# The decimal error stays exactly one isolated row, deliberately never a
# systemic/block-wide pattern - Lesson 10 ("Validation Gate") already
# owns that shape (a block of rows recorded in the wrong unit); this
# lesson's own error is one person's typo, not a recording convention.

URBAN_NORMAL_VALUES: tuple[float, ...] = tuple(float(v) for v in range(40, 53))  # $40..$52, 13 values
URBAN_NORMAL_REPEATS = 6  # 13 x 6 = 78 rows

DECIMAL_ERROR_ORDER = "U-9001"
DECIMAL_ERROR_RECORDED = 4600.00
DECIMAL_ERROR_TRUE = 46.00

BULK_ORDER = "U-9002"
BULK_ORDER_COST = 950.00

ANOMALY_ORDER = "U-9003"
ANOMALY_ORDER_COST = 410.00
ANOMALY_INCIDENT_REFERENCE = "INC-2026-0091: warehouse WMS outage, emergency courier dispatch"

REMOTE_VALUES: tuple[float, ...] = (70.0, 72.0, 74.0, 76.0, 78.0, 80.0, 82.0, 84.0)  # 8 rows

ORDER_COLUMNS: tuple[str, ...] = (
    "order_id",
    "zone",
    "fulfillment_cost",
    "order_type",
    "invoice_reference_amount",
    "incident_reference",
)

ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema(name="order_id", dtype="string"),
        ColumnSchema(name="zone", dtype="string"),
        ColumnSchema(name="fulfillment_cost", dtype="float64"),
        ColumnSchema(name="order_type", dtype="string"),
        ColumnSchema(
            name="invoice_reference_amount",
            dtype="float64",
            nullable=True,
            description_key="lesson.l09.schema.invoice_reference_amount",
        ),
        ColumnSchema(
            name="incident_reference",
            dtype="string",
            nullable=True,
            description_key="lesson.l09.schema.incident_reference",
        ),
    )
)


def _build_raw_rows() -> list[dict]:
    rows: list[dict] = []
    counter = 0
    for value in URBAN_NORMAL_VALUES:
        for _ in range(URBAN_NORMAL_REPEATS):
            counter += 1
            rows.append(
                {
                    "order_id": f"U-{counter:03d}",
                    "zone": "urban",
                    "fulfillment_cost": value,
                    "order_type": "standard",
                    "invoice_reference_amount": float("nan"),
                    "incident_reference": None,
                }
            )

    rows.append(
        {
            "order_id": DECIMAL_ERROR_ORDER,
            "zone": "urban",
            "fulfillment_cost": DECIMAL_ERROR_RECORDED,
            "order_type": "standard",
            "invoice_reference_amount": DECIMAL_ERROR_TRUE,
            "incident_reference": None,
        }
    )
    rows.append(
        {
            "order_id": BULK_ORDER,
            "zone": "urban",
            "fulfillment_cost": BULK_ORDER_COST,
            "order_type": "enterprise_bulk",
            "invoice_reference_amount": float("nan"),
            "incident_reference": None,
        }
    )
    rows.append(
        {
            "order_id": ANOMALY_ORDER,
            "zone": "urban",
            "fulfillment_cost": ANOMALY_ORDER_COST,
            "order_type": "standard",
            "invoice_reference_amount": float("nan"),
            "incident_reference": ANOMALY_INCIDENT_REFERENCE,
        }
    )

    for index, value in enumerate(REMOTE_VALUES, start=1):
        rows.append(
            {
                "order_id": f"R-{index:03d}",
                "zone": "remote",
                "fulfillment_cost": value,
                "order_type": "standard",
                "invoice_reference_amount": float("nan"),
                "incident_reference": None,
            }
        )

    return rows


def generate_orders() -> Dataset:
    """The raw, untouched fulfillment-cost feed - 89 rows, deterministic,
    hand-verified (see the module docstring above). Every downstream
    stage replays a student's own real resolution against this via
    apply_round1/apply_round2, never a ground-truth substitute."""
    frame = pd.DataFrame(_build_raw_rows())[list(ORDER_COLUMNS)]
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA)


# --- Real, live-computed stats - never a hand-typed number -----------------


def _fence(costs: pd.Series) -> tuple[float, float]:
    q1, q3 = float(costs.quantile(0.25)), float(costs.quantile(0.75))
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def global_fence(dataset: Dataset) -> tuple[float, float]:
    return _fence(dataset.frame["fulfillment_cost"])


def flagged_count(dataset: Dataset, lower: float, upper: float) -> int:
    costs = dataset.frame["fulfillment_cost"]
    return int(((costs < lower) | (costs > upper)).sum())


def zone_fence(dataset: Dataset, zone: str) -> tuple[float, float]:
    return _fence(dataset.frame[dataset.frame["zone"] == zone]["fulfillment_cost"])


def zone_flag_rate(dataset: Dataset, zone: str, lower: float, upper: float) -> float:
    """The share of `zone`'s own rows that fall outside [lower, upper] -
    used with the GLOBAL fence to show over-flagging, and with the zone's
    OWN fence to show it clears once judged on its own terms."""
    zone_costs = dataset.frame[dataset.frame["zone"] == zone]["fulfillment_cost"]
    flagged = int(((zone_costs < lower) | (zone_costs > upper)).sum())
    return float(flagged) / float(len(zone_costs))


def typical_standard_order_state(dataset: Dataset) -> tuple[int, float]:
    """(n, median) for the typical-standard-order metric. Population
    membership comes from the order's own real order_type field, never
    from how large its own cost value happens to be - a bulk order stays
    excluded from this population even after every real correction, and
    an urban order at the low end of the range stays included even
    though it's nowhere near the median."""
    standard = dataset.frame[dataset.frame["order_type"] == "standard"]
    return int(len(standard)), float(standard["fulfillment_cost"].median())


def total_exposure_state(dataset: Dataset) -> tuple[int, float]:
    """(n, sum) for total fulfillment exposure - every real order,
    regardless of type. The same bulk order excluded from the metric
    above is required here: NovaMart really paid that $950, and total
    exposure has to reflect it."""
    return int(len(dataset.frame)), float(dataset.frame["fulfillment_cost"].sum())


def median_python_code() -> str:
    return "orders[orders.order_type == 'standard']['fulfillment_cost'].median()"


def sum_python_code() -> str:
    return "orders['fulfillment_cost'].sum()"


def fence_python_code() -> str:
    return (
        "q1, q3 = orders['fulfillment_cost'].quantile([0.25, 0.75])\n"
        "iqr = q3 - q1\n"
        "lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr"
    )


def zone_describe_python_code() -> str:
    return "orders.groupby('zone')['fulfillment_cost'].describe()"


# --- Round 1: the blanket policy pick for every row the fence flags -------


def _drop_outside_fence(frame: pd.DataFrame) -> pd.DataFrame:
    costs = frame["fulfillment_cost"]
    lower, upper = _fence(costs)
    return frame[(costs >= lower) & (costs <= upper)].reset_index(drop=True)


def _cap_at_fence(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    lower, upper = _fence(result["fulfillment_cost"])
    result["fulfillment_cost"] = result["fulfillment_cost"].clip(lower, upper)
    return result


def _no_blanket_action(frame: pd.DataFrame) -> pd.DataFrame:
    return frame


ROUND1_ISSUE = RepairIssue(
    column="fulfillment_cost",
    prompt_key="lesson.l09.issue.fulfillment_cost.round1.prompt",
    options=(
        RepairOption(
            "drop_outside_fence",
            "lesson.l09.option.round1.drop_outside_fence",
            _drop_outside_fence,
            python_code=(
                "q1, q3 = orders['fulfillment_cost'].quantile([0.25, 0.75])\n"
                "iqr = q3 - q1\n"
                "lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr\n"
                "orders = orders[(orders['fulfillment_cost'] >= lower) & (orders['fulfillment_cost'] <= upper)]"
            ),
        ),
        RepairOption(
            "no_blanket_action",
            "lesson.l09.option.round1.no_blanket_action",
            _no_blanket_action,
            python_code="# no blanket rule - every flagged row is investigated individually before anything changes",
        ),
        RepairOption(
            "cap_at_fence",
            "lesson.l09.option.round1.cap_at_fence",
            _cap_at_fence,
            python_code=(
                "q1, q3 = orders['fulfillment_cost'].quantile([0.25, 0.75])\n"
                "iqr = q3 - q1\n"
                "lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr\n"
                "orders['fulfillment_cost'] = orders['fulfillment_cost'].clip(lower, upper)"
            ),
        ),
    ),
    hint_key="lesson.l09.issue.fulfillment_cost.round1.hint",
)

CORRECT_ROUND1_KEY = "no_blanket_action"

HIGH_REPRODUCIBILITY_ROUND1_KEYS = frozenset({"no_blanket_action"})
MEDIUM_REPRODUCIBILITY_ROUND1_KEYS = frozenset({"drop_outside_fence", "cap_at_fence"})
"""Both drop_outside_fence and cap_at_fence are real, explicit,
deterministic rules - wrong per METHOD (a blanket rule applied before any
row has actually been looked at), but not automatically zero on
REPRODUCIBILITY, which judges whether the rule is explicit and
repeatable, not whether it's also the right call."""


# --- Round 2: case-by-case treatment, one issue per special row -----------
#
# Each issue is flagged under a different real column so the three can
# coexist in one RepairResolution dict (column -> chosen option.key) -
# fulfillment_cost for the row whose own value needs fixing,
# order_type/incident_reference for the two rows whose own real business
# metadata is what the correct call actually rests on.


def _correct_decimal_via_invoice(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    mask = result["order_id"] == DECIMAL_ERROR_ORDER
    result.loc[mask, "fulfillment_cost"] = result.loc[mask, "invoice_reference_amount"]
    return result


def _drop_row(order_id: str):
    def _drop(frame: pd.DataFrame) -> pd.DataFrame:
        return frame[frame["order_id"] != order_id].reset_index(drop=True)

    return _drop


def _keep_row_unchanged(frame: pd.DataFrame) -> pd.DataFrame:
    return frame


def _correct_bulk_to_typical_value(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    mask = result["order_id"] == BULK_ORDER
    result.loc[mask, "fulfillment_cost"] = float(result.loc[~mask, "fulfillment_cost"].median())
    return result


DECIMAL_ISSUE = RepairIssue(
    column="fulfillment_cost",
    prompt_key="lesson.l09.issue.fulfillment_cost.round2.prompt",
    options=(
        RepairOption(
            "drop_row",
            "lesson.l09.option.decimal.drop_row",
            _drop_row(DECIMAL_ERROR_ORDER),
            python_code="orders = orders[orders['order_id'] != 'U-9001']",
        ),
        RepairOption(
            "correct_via_invoice",
            "lesson.l09.option.decimal.correct_via_invoice",
            _correct_decimal_via_invoice,
            python_code=(
                "mask = orders['order_id'] == 'U-9001'\n"
                "orders.loc[mask, 'fulfillment_cost'] = orders.loc[mask, 'invoice_reference_amount']"
            ),
        ),
        RepairOption(
            "keep_as_is",
            "lesson.l09.option.decimal.keep_as_is",
            _keep_row_unchanged,
            python_code="# leaves the recorded $4,600.00 value untouched",
        ),
    ),
    hint_key="lesson.l09.issue.fulfillment_cost.round2.hint",
    evidence_key="lesson.l09.issue.fulfillment_cost.evidence",
)

BULK_ISSUE = RepairIssue(
    column="order_type",
    prompt_key="lesson.l09.issue.order_type.prompt",
    options=(
        RepairOption(
            "drop_row",
            "lesson.l09.option.bulk.drop_row",
            _drop_row(BULK_ORDER),
            python_code="orders = orders[orders['order_id'] != 'U-9002']",
        ),
        RepairOption(
            "keep_as_is",
            "lesson.l09.option.bulk.keep_as_is",
            _keep_row_unchanged,
            python_code="# a real, correctly recorded order - no change",
        ),
        RepairOption(
            "correct_to_typical_value",
            "lesson.l09.option.bulk.correct_to_typical_value",
            _correct_bulk_to_typical_value,
            python_code="orders.loc[orders['order_id'] == 'U-9002', 'fulfillment_cost'] = orders['fulfillment_cost'].median()",
        ),
    ),
    hint_key="lesson.l09.issue.order_type.hint",
    evidence_key="lesson.l09.issue.order_type.evidence",
)

ANOMALY_ISSUE = RepairIssue(
    column="incident_reference",
    prompt_key="lesson.l09.issue.incident_reference.prompt",
    options=(
        RepairOption(
            "drop_row",
            "lesson.l09.option.anomaly.drop_row",
            _drop_row(ANOMALY_ORDER),
            python_code="orders = orders[orders['order_id'] != 'U-9003']",
        ),
        RepairOption(
            "keep_silently",
            "lesson.l09.option.anomaly.keep_silently",
            _keep_row_unchanged,
            python_code="# kept, but its own documented incident_reference is never surfaced",
        ),
        RepairOption(
            "keep_and_flag_as_documented_incident",
            "lesson.l09.option.anomaly.keep_and_flag_as_documented_incident",
            _keep_row_unchanged,
            python_code="# real, correctly recorded - kept, its own incident_reference is the flag",
        ),
    ),
    hint_key="lesson.l09.issue.incident_reference.hint",
    evidence_key="lesson.l09.issue.incident_reference.evidence",
)

ROUND2_ISSUES: tuple[RepairIssue, ...] = (DECIMAL_ISSUE, BULK_ISSUE, ANOMALY_ISSUE)

CORRECT_DECIMAL_KEY = "correct_via_invoice"
CORRECT_BULK_KEY = "keep_as_is"
CORRECT_ANOMALY_KEY = "keep_and_flag_as_documented_incident"

HIGH_REPRODUCIBILITY_ROUND2_KEYS = frozenset(
    {"correct_via_invoice", "keep_as_is", "keep_and_flag_as_documented_incident"}
)
MEDIUM_REPRODUCIBILITY_ROUND2_KEYS = frozenset(
    {"drop_row", "keep_silently", "correct_to_typical_value"}
)
"""Every option in Round 2 is a real, deterministic action - none of them
depend on row order or an unstated tie-break. What separates the tiers is
whether the action is actually grounded in the row's own real evidence
(its invoice reference, its order_type, its incident_reference) or not:
dropping a real order, silently keeping a real incident unflagged, or
"correcting" a value that was never wrong are all real, repeatable
choices - just ones that ignore the one fact that would have grounded a
different call."""


def apply_round1(resolution: RepairResolution) -> Dataset:
    return apply_resolution(generate_orders(), (ROUND1_ISSUE,), resolution)


def apply_round2(round1_resolution: RepairResolution, round2_resolution: RepairResolution) -> Dataset:
    dataset = apply_round1(round1_resolution)
    return apply_resolution(dataset, ROUND2_ISSUES, round2_resolution)


# --- Optional mastery - transfer, not repetition ---------------------------
#
# Different domain, different unit: employee support-ticket resolution
# times, in minutes. 40 tickets resolved in a tight, unremarkable 20-40
# minute range (a real, hand-picked spread, not every ticket identical),
# plus one genuine extreme-but-valid escalation (a real, correctly
# recorded incident that legitimately took far longer) and one confirmed
# data-entry error (a negative resolution time - physically impossible,
# a real typo, not a judgment call).

TICKET_NORMAL_VALUES: tuple[int, ...] = tuple(range(20, 40))  # 20 distinct values
TICKET_NORMAL_REPEATS = 2  # 20 x 2 = 40 tickets

ESCALATION_TICKET = "T-901"
ESCALATION_MINUTES = 480.0
ESCALATION_INCIDENT_REFERENCE = "INC-2026-0114: vendor outage escalated to Tier 3, real multi-hour resolution"

ERROR_TICKET = "T-902"
ERROR_MINUTES = -15.0

TICKET_COLUMNS: tuple[str, ...] = ("ticket_id", "resolution_minutes", "incident_reference")

TICKETS_SCHEMA = Schema(
    columns=(
        ColumnSchema(name="ticket_id", dtype="string"),
        ColumnSchema(name="resolution_minutes", dtype="float64"),
        ColumnSchema(name="incident_reference", dtype="string", nullable=True),
    )
)


def generate_support_tickets() -> Dataset:
    rows: list[dict] = []
    counter = 0
    for value in TICKET_NORMAL_VALUES:
        for _ in range(TICKET_NORMAL_REPEATS):
            counter += 1
            rows.append({"ticket_id": f"T-{counter:03d}", "resolution_minutes": float(value), "incident_reference": None})
    rows.append(
        {"ticket_id": ESCALATION_TICKET, "resolution_minutes": ESCALATION_MINUTES, "incident_reference": ESCALATION_INCIDENT_REFERENCE}
    )
    rows.append({"ticket_id": ERROR_TICKET, "resolution_minutes": ERROR_MINUTES, "incident_reference": None})
    frame = pd.DataFrame(rows)[list(TICKET_COLUMNS)]
    return Dataset(name="support_tickets", frame=frame, schema=TICKETS_SCHEMA)


MASTERY_CORRECT_MUST_NOT_REMOVE = frozenset({"escalation_ticket"})
MASTERY_CORRECT_NEEDS_CORRECTION = frozenset({"error_ticket"})


# --- Diagnosis Builder answer key ------------------------------------------

DIAGNOSIS_CORRECT_BY_FIELD: dict[str, str] = {
    "decimal_row_diagnosis": "data_entry_error",
    "bulk_row_diagnosis": "rare_but_legitimate",
    "anomaly_row_diagnosis": "documented_anomaly",
}
