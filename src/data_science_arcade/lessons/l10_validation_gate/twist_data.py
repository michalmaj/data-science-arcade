from dataclasses import dataclass

import numpy as np
import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairOption, RepairResolution, apply_resolution

# --- Ground truth (hand-verified, hand-picked - not randomized) -----------
#
# NovaMart's daily orders export. 200 orders, two source systems. 150 from
# checkout_v2: real economics subtotal=$140.00, tax=$10.00, shipping=$5.00,
# discount=$5.00 -> recorded_amount_usd=$150.00, exactly reconciling. 50
# from legacy_pos_v1: the *same* real economics (identical subtotal/tax/
# shipping/discount), but recorded_amount_usd=$15,000.00 - a real x100
# unit-convention bug (cents recorded as if dollars). Every one of those
# 50 rows is still individually numeric, non-null, inside a wide allowed
# range, has a valid status/customer/timestamp - it only breaks the
# cross-field invariant recorded_amount_usd = subtotal+tax+shipping-
# discount, badly (a $14,850 gap, nowhere near any real tolerance). No
# hidden ground-truth column anywhere in this frame - the real "truth" is
# always derivable from the other real, visible columns via
# expected_amount() below.

GOOD_SOURCE = "checkout_v2"
GOOD_EXPORT_VERSION = "v2.3"
GOOD_ORDERS = 150
GOOD_REFERRAL_NULLS = 9  # of 150 - ~6%, deliberately the same rate as the bad segment below

BAD_SOURCE = "legacy_pos_v1"
BAD_EXPORT_VERSION = "v1.8"
BAD_ORDERS = 50
BAD_REFERRAL_NULLS = 3  # of 50 - ~6%, deliberately uncorrelated with the systemic failure

SUBTOTAL = 140.00
TAX = 10.00
SHIPPING = 5.00
DISCOUNT = 5.00
GOOD_RECORDED = 150.00  # subtotal + tax + shipping - discount, reconciles exactly
BAD_RECORDED = 15_000.00  # same real economics, recorded x100 - the systemic bug

WIDE_RANGE_LOW = 0.0
WIDE_RANGE_HIGH = 25_000.0
"""Comfortably lets $15,000 pass (not borderline) while staying a
defensible real business range - not a strawman a real data engineer
would never actually configure."""

ALLOWED_STATUSES: tuple[str, ...] = ("completed", "processing", "refunded")
VALID_CUSTOMER_COUNT = 100

EXPORTED_AT = pd.Timestamp("2026-09-07 06:00:00")
FRESHNESS_REFERENCE = pd.Timestamp("2026-09-07 09:00:00")
FRESHNESS_WINDOW_HOURS = 24.0
"""A fixed reference moment, not wall-clock time - keeps the freshness
check deterministic across every run, matching this project's seeded/
deterministic-dataset discipline."""

REQUIRED_COLUMNS: tuple[str, ...] = (
    "order_id",
    "source_system",
    "export_version",
    "recorded_amount_usd",
    "subtotal_usd",
    "tax_usd",
    "shipping_usd",
    "discount_usd",
    "status",
    "customer_id",
    "exported_at",
    "review_status",
)
ORDER_COLUMNS: tuple[str, ...] = REQUIRED_COLUMNS + ("referral_source",)

ORDERS_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "string"),
        ColumnSchema("source_system", "string"),
        ColumnSchema("export_version", "string"),
        ColumnSchema("recorded_amount_usd", "float64"),
        ColumnSchema("subtotal_usd", "float64"),
        ColumnSchema("tax_usd", "float64"),
        ColumnSchema("shipping_usd", "float64"),
        ColumnSchema("discount_usd", "float64"),
        ColumnSchema("status", "string"),
        ColumnSchema("customer_id", "string"),
        ColumnSchema("exported_at", "datetime64[ns]"),
        ColumnSchema("review_status", "string"),
        ColumnSchema(
            "referral_source", "string", nullable=True, description_key="lesson.l10.schema.referral_source"
        ),
    )
)


def _build_rows() -> list[dict]:
    rows: list[dict] = []
    counter = 0
    for source, export_version, count, recorded, referral_nulls in (
        (GOOD_SOURCE, GOOD_EXPORT_VERSION, GOOD_ORDERS, GOOD_RECORDED, GOOD_REFERRAL_NULLS),
        (BAD_SOURCE, BAD_EXPORT_VERSION, BAD_ORDERS, BAD_RECORDED, BAD_REFERRAL_NULLS),
    ):
        for index in range(count):
            counter += 1
            rows.append(
                {
                    "order_id": f"ORD-{counter:04d}",
                    "source_system": source,
                    "export_version": export_version,
                    "recorded_amount_usd": recorded,
                    "subtotal_usd": SUBTOTAL,
                    "tax_usd": TAX,
                    "shipping_usd": SHIPPING,
                    "discount_usd": DISCOUNT,
                    "status": ALLOWED_STATUSES[counter % len(ALLOWED_STATUSES)],
                    "customer_id": f"CUST-{(counter % VALID_CUSTOMER_COUNT) + 1:04d}",
                    "exported_at": EXPORTED_AT,
                    "review_status": "pending_review",
                    "referral_source": None if index < referral_nulls else "organic",
                }
            )
    return rows


def generate_orders() -> Dataset:
    """The raw, untouched daily orders feed - 200 rows, deterministic,
    hand-verified (see module docstring). Every downstream stage replays
    a student's own real resolution against this via apply_round1/
    apply_batch_action/apply_replay, never a ground-truth substitute."""
    frame = pd.DataFrame(_build_rows())[list(ORDER_COLUMNS)]
    return Dataset(name="orders", frame=frame, schema=ORDERS_SCHEMA)


# --- Baseline gate - the 6 real, given checks, all real, all green --------


def unique_order_id_rate(dataset: Dataset) -> float:
    ids = dataset.frame["order_id"]
    return float(ids.nunique()) / float(len(ids))


def null_rate_required_fields(dataset: Dataset) -> float:
    frame = dataset.frame[list(REQUIRED_COLUMNS)]
    return float(frame.isna().sum().sum()) / float(frame.size)


def valid_customer_rate(dataset: Dataset) -> float:
    valid_ids = {f"CUST-{n:04d}" for n in range(1, VALID_CUSTOMER_COUNT + 1)}
    return float(dataset.frame["customer_id"].isin(valid_ids).mean())


def valid_status_rate(dataset: Dataset) -> float:
    return float(dataset.frame["status"].isin(ALLOWED_STATUSES).mean())


def freshness_within_window_rate(dataset: Dataset) -> float:
    age_hours = (FRESHNESS_REFERENCE - dataset.frame["exported_at"]).dt.total_seconds() / 3600.0
    return float((age_hours <= FRESHNESS_WINDOW_HOURS).mean())


def amount_in_range_rate(dataset: Dataset) -> float:
    amounts = dataset.frame["recorded_amount_usd"]
    return float(((amounts >= WIDE_RANGE_LOW) & (amounts <= WIDE_RANGE_HIGH)).mean())


def baseline_checks_passed(dataset: Dataset) -> int:
    """How many of the 6 baseline checks pass, out of 6 - the real
    "6/6 CHECKS PASSED" figure the baseline gate reveal shows. Every
    check genuinely passes on this dataset by construction; this stays a
    real computation (not a hardcoded 6) so a future change to the
    dataset can never silently drift out of sync with what the reveal
    claims."""
    checks = (
        unique_order_id_rate(dataset) == 1.0,
        null_rate_required_fields(dataset) == 0.0,
        valid_customer_rate(dataset) == 1.0,
        valid_status_rate(dataset) == 1.0,
        freshness_within_window_rate(dataset) == 1.0,
        amount_in_range_rate(dataset) == 1.0,
    )
    return sum(1 for passed in checks if passed)


def baseline_checks_python_code() -> str:
    return (
        "checks = [\n"
        "    orders['order_id'].is_unique,\n"
        "    orders[required_columns].isna().sum().sum() == 0,\n"
        "    orders['customer_id'].isin(known_customers).all(),\n"
        "    orders['status'].isin(['completed', 'processing', 'refunded']).all(),\n"
        "    ((now - orders['exported_at']).dt.total_seconds() / 3600 <= 24).all(),\n"
        "    orders['recorded_amount_usd'].between(0, 25_000).all(),\n"
        "]\n"
        "sum(checks)"
    )


# --- KPI, at face value - what a green gate leaves you with ---------------


def naive_total(dataset: Dataset) -> float:
    return float(dataset.frame["recorded_amount_usd"].sum())


def quarantine_trap_total(dataset: Dataset) -> float:
    """The tempting-wrong number: drop the bad-source rows and report the
    total over the rest, as if nothing happened. Silently understates
    real exposure by exactly those rows' own real value - never shown
    live in-lesson, but real and worth asserting in tests."""
    frame = dataset.frame
    return float(frame.loc[frame["source_system"] != BAD_SOURCE, "recorded_amount_usd"].sum())


def total_python_code() -> str:
    return "orders['recorded_amount_usd'].sum()"


# --- The cross-field invariant and the optional-field WARN signal ---------

CANONICAL_ATOL = 1.0
"""Used only by the decoupled concentration investigation below (a
manual, mentor-led "let's look at where this really concentrates,
independent of whatever your own gate found" beat) - never by gate
execution itself. Gate outcomes (evaluate_gate below) are driven entirely
by the student's own real Gate Builder configuration; a check the
student never authored can never flag anything, regardless of what this
canonical calibration would have found. Real financial floats deserve an
explicit small tolerance, not bit-exact equality relying on np.isclose's
own undocumented default rtol - every real comparison in this module
passes rtol explicitly (see invariant_mismatch_mask)."""


def expected_amount(frame: pd.DataFrame) -> pd.Series:
    return frame["subtotal_usd"] + frame["tax_usd"] + frame["shipping_usd"] - frame["discount_usd"]


def invariant_mismatch_mask(frame: pd.DataFrame, atol: float = CANONICAL_ATOL, rtol: float = 0.0) -> pd.Series:
    return ~np.isclose(frame["recorded_amount_usd"], expected_amount(frame), atol=atol, rtol=rtol)


def invariant_fail_count(dataset: Dataset) -> int:
    return int(invariant_mismatch_mask(dataset.frame).sum())


def invariant_fail_rate_by_source(dataset: Dataset) -> dict[str, float]:
    frame = dataset.frame.copy()
    frame["_mismatch"] = invariant_mismatch_mask(frame)
    return frame.groupby("source_system")["_mismatch"].mean().to_dict()


def invariant_python_code(atol: float = CANONICAL_ATOL, rtol: float = 0.0) -> str:
    return (
        "expected = orders['subtotal_usd'] + orders['tax_usd'] + orders['shipping_usd'] - orders['discount_usd']\n"
        f"mismatch = ~np.isclose(orders['recorded_amount_usd'], expected, atol={atol}, rtol={rtol})\n"
        "mismatch.sum()"
    )


def concentration_python_code() -> str:
    return "orders.assign(mismatch=mismatch).groupby('source_system')['mismatch'].mean()"


# --- Gate execution - the authored config is what actually runs -----------
#
# Contract: authored rule -> real execution -> real PASS/WARN/BLOCK result.
# A check the student never authored (an "opt out" pick - no_check,
# no_invariant_check) simply doesn't exist: it never flags anything,
# regardless of what the canonical calibration above would have found.
# This is what makes the Gate Builder actually control the gate that
# runs next, rather than the gate silently re-running a fixed reference
# check underneath whatever the student picked.

_OPTIONAL_SEVERITY_BY_KEY: dict[str, str] = {
    "info_only": "info",
    "warn_at_threshold": "warn",
    "block": "block",
}
_OPTIONAL_THRESHOLD_BY_KEY: dict[str, float] = {
    "zero_tolerance": 0.0,
    "flag_over_2pct": 0.02,
    "flag_over_10pct": 0.10,
}
_INVARIANT_SEVERITY_BY_KEY: dict[str, str] = {
    "no_action": "none",
    "info_only": "info",
    "warn_only": "warn",
    "block": "block",
}
_INVARIANT_ATOL_BY_KEY: dict[str, float] = {
    "exact_match_atol_0": 0.0,
    "small_tolerance_atol_1": 1.0,
}


@dataclass(frozen=True)
class CheckOutcome:
    """One authored (or never-authored) check's own real, executed
    result - three separate facts, deliberately never collapsed into
    one: whether the check was authored at all (`exists`), whether the
    real assertion it runs actually held (`assertion_passed`), and the
    severity the student themselves assigned it (`severity`). A
    WARN-level check whose assertion fails is a real, triggered warning
    - never a "passed check," and never a BLOCK either."""

    key: str
    exists: bool
    assertion_passed: bool | None
    severity: str | None
    """"info" | "warn" | "block" | "none" (authored with no real action) |
    None (never authored)."""
    affected_count: int
    affected_total: int

    def triggered(self) -> bool:
        """A real, existing check whose own assertion failed."""
        return self.exists and self.assertion_passed is False


def evaluate_optional_check(dataset: Dataset, gate_resolution: dict) -> CheckOutcome:
    severity_key = gate_resolution.get("optional_field_severity")
    total = len(dataset.frame)
    if severity_key not in _OPTIONAL_SEVERITY_BY_KEY:
        return CheckOutcome("optional_field", False, None, None, 0, total)
    threshold = _OPTIONAL_THRESHOLD_BY_KEY.get(gate_resolution.get("optional_field_threshold"), 0.0)
    count, rate = referral_null_count_and_rate(dataset)
    return CheckOutcome("optional_field", True, rate <= threshold, _OPTIONAL_SEVERITY_BY_KEY[severity_key], count, total)


def evaluate_invariant_check(dataset: Dataset, gate_resolution: dict) -> CheckOutcome:
    tolerance_key = gate_resolution.get("invariant_tolerance")
    total = len(dataset.frame)
    if tolerance_key not in _INVARIANT_ATOL_BY_KEY:
        return CheckOutcome("invariant", False, None, None, 0, total)
    atol = _INVARIANT_ATOL_BY_KEY[tolerance_key]
    count = int(invariant_mismatch_mask(dataset.frame, atol=atol, rtol=0.0).sum())
    severity = _INVARIANT_SEVERITY_BY_KEY.get(gate_resolution.get("invariant_severity"), "info")
    return CheckOutcome("invariant", True, count == 0, severity, count, total)


@dataclass(frozen=True)
class GateOutcome:
    baseline_passed: int
    baseline_total: int
    optional_check: CheckOutcome
    invariant_check: CheckOutcome

    def _authored_checks(self) -> tuple[CheckOutcome, ...]:
        return (self.optional_check, self.invariant_check)

    def assertions_run(self) -> int:
        return self.baseline_total + sum(1 for c in self._authored_checks() if c.exists)

    def assertions_passed(self) -> int:
        return self.baseline_passed + sum(1 for c in self._authored_checks() if c.exists and c.assertion_passed)

    def warn_triggered(self) -> tuple[CheckOutcome, ...]:
        return tuple(c for c in self._authored_checks() if c.triggered() and c.severity == "warn")

    def block_triggered(self) -> tuple[CheckOutcome, ...]:
        return tuple(c for c in self._authored_checks() if c.triggered() and c.severity == "block")

    def outcome(self) -> str:
        """"blocked" | "pass_with_warning" | "pass" - the real, aggregate
        gate verdict, derived only from checks the student actually
        authored and only from severities that actually act (a triggered
        "info"/"none"-severity check changes neither)."""
        if self.block_triggered():
            return "blocked"
        if self.warn_triggered():
            return "pass_with_warning"
        return "pass"


def evaluate_gate(dataset: Dataset, gate_resolution: dict) -> GateOutcome:
    return GateOutcome(
        baseline_passed=baseline_checks_passed(dataset),
        baseline_total=6,
        optional_check=evaluate_optional_check(dataset, gate_resolution),
        invariant_check=evaluate_invariant_check(dataset, gate_resolution),
    )


def referral_null_count_and_rate(dataset: Dataset) -> tuple[int, float]:
    col = dataset.frame["referral_source"]
    count = int(col.isna().sum())
    return count, count / float(len(col))


def referral_null_python_code() -> str:
    return "orders['referral_source'].isna().mean()"


# --- Round 1: approve for publication, or hold? ----------------------------
#
# A real batch-level call, modeled on its own dedicated review_status
# column (never overloaded onto the order's own real `status` field,
# which the baseline category-validity check judges on its own terms).


def _set_review_status(value: str):
    def _apply(frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        result["review_status"] = value
        return result

    return _apply


ROUND1_ISSUE = RepairIssue(
    column="review_status",
    prompt_key="lesson.l10.issue.round1.prompt",
    options=(
        RepairOption(
            "approve_for_publication",
            "lesson.l10.option.round1.approve_for_publication",
            _set_review_status("published_naive"),
            python_code="orders['review_status'] = 'published_naive'  # KPI computed and shipped as-is",
        ),
        RepairOption(
            "hold_for_further_validation",
            "lesson.l10.option.round1.hold_for_further_validation",
            _set_review_status("held_for_validation"),
            python_code="orders['review_status'] = 'held_for_validation'  # nothing published yet",
        ),
    ),
    hint_key="lesson.l10.issue.round1.hint",
)
CORRECT_ROUND1_KEY = "hold_for_further_validation"


def apply_round1(resolution: RepairResolution) -> Dataset:
    return apply_resolution(generate_orders(), (ROUND1_ISSUE,), resolution)


# --- Batch-action decision - after the invariant check has run for real ---


def _quarantine_bad_source(frame: pd.DataFrame) -> pd.DataFrame:
    """The tempting-wrong pick's own real transform: silently drops the
    bad-source rows and reports a total over the rest, "as if nothing
    happened" - genuinely different from every other batch-action option,
    which only ever relabels review_status without touching a single row."""
    result = frame[frame["source_system"] != BAD_SOURCE].reset_index(drop=True)
    result["review_status"] = "quarantined_reported"
    return result


BATCH_ACTION_ISSUE = RepairIssue(
    column="review_status",
    prompt_key="lesson.l10.issue.batch_action.prompt",
    options=(
        RepairOption(
            "block_and_request_replay",
            "lesson.l10.option.batch_action.block_and_request_replay",
            _set_review_status("blocked_pending_replay"),
            python_code="orders['review_status'] = 'blocked_pending_replay'  # source asked to resend the corrected batch",
        ),
        RepairOption(
            "quarantine_and_report_rest",
            "lesson.l10.option.batch_action.quarantine_and_report_rest",
            _quarantine_bad_source,
            python_code=(
                "orders = orders[orders['source_system'] != 'legacy_pos_v1']\n"
                "orders['review_status'] = 'quarantined_reported'"
            ),
        ),
        RepairOption(
            "publish_anyway",
            "lesson.l10.option.batch_action.publish_anyway",
            _set_review_status("published_anyway"),
            python_code="orders['review_status'] = 'published_anyway'  # KPI ships with the mismatch still in it",
        ),
        RepairOption(
            "investigate_only",
            "lesson.l10.option.batch_action.investigate_only",
            _set_review_status("investigating"),
            python_code="orders['review_status'] = 'investigating'  # nothing decided yet",
        ),
    ),
    hint_key="lesson.l10.issue.batch_action.hint",
)
CORRECT_BATCH_ACTION_KEY = "block_and_request_replay"


def apply_batch_action(round1_resolution: RepairResolution, batch_action_resolution: RepairResolution) -> Dataset:
    dataset = apply_round1(round1_resolution)
    return apply_resolution(dataset, (BATCH_ACTION_ISSUE,), batch_action_resolution)


# --- Simulated source replay - a real, shared transform --------------------
#
# Never a second hand-authored dataset (drift risk between "the bug" and
# "the fix"): the same expected_amount() the invariant check itself uses
# is what corrects the batch, applied only to the affected source's own
# rows. Automatic and narrated, never a player pick - the gate never
# touches values, only the upstream source does (validation != cleaning).

REPLAY_PYTHON_CODE = (
    "expected = orders['subtotal_usd'] + orders['tax_usd'] + orders['shipping_usd'] - orders['discount_usd']\n"
    "mask = orders['source_system'] == 'legacy_pos_v1'\n"
    "orders.loc[mask, 'recorded_amount_usd'] = expected.loc[mask]"
)


def _replay_source_correction(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    mask = result["source_system"] == BAD_SOURCE
    result.loc[mask, "recorded_amount_usd"] = expected_amount(result.loc[mask])
    result.loc[mask, "review_status"] = "replayed_and_published"
    return result


def apply_replay(dataset: Dataset) -> Dataset:
    return dataset.then("source_replay_correction", _replay_source_correction, python_code=REPLAY_PYTHON_CODE)


def final_dataset(round1_resolution: RepairResolution, batch_action_resolution: RepairResolution) -> Dataset:
    """Replays the student's own real Round 1 + batch-action picks - and,
    only when the batch-action pick is genuinely correct, the simulated
    source replay - never a ground-truth substitute."""
    dataset = apply_batch_action(round1_resolution, batch_action_resolution)
    if batch_action_resolution.get("review_status") == CORRECT_BATCH_ACTION_KEY:
        dataset = apply_replay(dataset)
    return dataset


# --- Optional mastery - transfer, not repetition ---------------------------
#
# Different domain, different shape: an inventory feed where every basic
# check passes and stock_on_hand >= 0 holds everywhere, but
# available_to_promise > stock_on_hand breaks for one source batch - a
# real cross-field invariant violation, never a repeat of the cents/
# dollars mechanism.

INVENTORY_GOOD_SKUS = 30
INVENTORY_BAD_BATCH = "legacy_wms_sync"
INVENTORY_BAD_SKUS = 6
INVENTORY_UPDATED_AT = pd.Timestamp("2026-09-07 07:00:00")

INVENTORY_COLUMNS: tuple[str, ...] = (
    "sku",
    "source_batch",
    "stock_on_hand",
    "available_to_promise",
    "warehouse_id",
    "updated_at",
)

INVENTORY_SCHEMA = Schema(
    columns=(
        ColumnSchema("sku", "string"),
        ColumnSchema("source_batch", "string"),
        ColumnSchema("stock_on_hand", "int64"),
        ColumnSchema("available_to_promise", "int64"),
        ColumnSchema("warehouse_id", "string"),
        ColumnSchema("updated_at", "datetime64[ns]"),
    )
)


def _inventory_rows() -> list[dict]:
    rows: list[dict] = []
    for index in range(INVENTORY_GOOD_SKUS):
        stock = 20 + index
        rows.append(
            {
                "sku": f"SKU-{index + 1:04d}",
                "source_batch": "warehouse_sync_v3",
                "stock_on_hand": stock,
                "available_to_promise": stock - 2,
                "warehouse_id": "WH-EAST",
                "updated_at": INVENTORY_UPDATED_AT,
            }
        )
    for index in range(INVENTORY_BAD_SKUS):
        stock = 10 + index
        rows.append(
            {
                "sku": f"SKU-B{index + 1:03d}",
                "source_batch": INVENTORY_BAD_BATCH,
                "stock_on_hand": stock,
                "available_to_promise": stock + 15,  # a real cross-field invariant break
                "warehouse_id": "WH-WEST",
                "updated_at": INVENTORY_UPDATED_AT,
            }
        )
    return rows


def generate_inventory_feed() -> Dataset:
    frame = pd.DataFrame(_inventory_rows())[list(INVENTORY_COLUMNS)]
    return Dataset(name="inventory", frame=frame, schema=INVENTORY_SCHEMA)
