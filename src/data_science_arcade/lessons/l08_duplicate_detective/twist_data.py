import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.duplicate_group import DuplicateGroup
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairOption, RepairResolution, apply_resolution

# --- Ground truth (hand-verified, hand-picked - not randomized) -----------
#
# Grain hierarchy: order_id (business order) -> payment_id (one payment
# attempt; more than one only if a first attempt was declined and
# retried) -> event_id (one lifecycle event tied to one attempt; normally
# appears exactly once in the raw feed).
#
# 20 orders. 15 (O01-O15) succeed on their only attempt (created ->
# authorized -> captured, 3 events each = 45). 5 (O16-O20) have a
# declined first attempt (created -> declined, 2 events each = 10) then
# a successful retry (created -> authorized -> captured, 3 events each =
# 15). 45 + 10 + 15 = 70 real, distinct lifecycle events, 20 of them
# `captured` (one per order - every order eventually succeeds here).
#
# Every captured amount is a flat $50.00 except the one injected
# conflict below. 6 of the 70 real events get a byte-identical transport
# replay (+6 raw rows). Order O10's own `captured` event additionally
# gets a conflicting redelivery with a DIFFERENT amount, $45.00 instead
# of the correct $50.00 (+1 raw row) - deliberately appended last, after
# the 6 pure replays, so the correct $50 row always precedes the
# erroneous $45 one in raw feed order: this is what makes
# `keep='first'` "accidentally" land on the right number and
# `keep='last'` land on the wrong one, a reproducible fact, not an
# assertion. Orders O05 and O13 share a customer and the same $50.00
# amount within the same short window, but are fully genuine, fully
# distinct purchases throughout - a real "checked, not a duplicate"
# finding. Total raw rows = 70 + 6 + 1 = 77.
#
# No transport-metadata column (no ingestion timestamp) exists in this
# schema, by deliberate choice - a real webhook replay would differ on
# receipt time even with an identical business payload, which would
# break the exact "6 pure duplicates" arithmetic below. `event_time` is
# a plain integer sequence (raw feed position), not a real datetime.

CAPTURED_AMOUNT = 50.00
CONFLICTING_AMOUNT = 45.00

SINGLE_ATTEMPT_ORDERS: tuple[str, ...] = tuple(f"O{n:02d}" for n in range(1, 16))  # O01-O15
RETRY_ORDERS: tuple[str, ...] = tuple(f"O{n:02d}" for n in range(16, 21))  # O16-O20
ALL_ORDERS: tuple[str, ...] = SINGLE_ATTEMPT_ORDERS + RETRY_ORDERS

DECOY_ORDER_A = "O05"
DECOY_ORDER_B = "O13"
DECOY_CUSTOMER = "C-DECOY"
CONFLICT_ORDER = "O10"
REPLAY_CAPTURED_ORDERS: tuple[str, ...] = ("O01", "O02", "O03", "O04")
REPLAY_AUTHORIZED_ORDERS: tuple[str, ...] = ("O06", "O07")

EVENT_COLUMNS: tuple[str, ...] = ("event_id", "event_type", "payment_id", "order_id", "customer_id", "amount")
"""Deliberately no ingestion-time/transport-metadata column - real feed
row order (preserved by pandas, never sorted away) already carries the
"which copy arrived first" fact this lesson's own keep='first'-vs-
keep='last' story depends on, so no separate column is needed for it. A
column that changes per delivery (even a plain integer sequence) would
make every row trivially unique, which would silently break the "6 pure
transport replays" premise a bare `duplicated()`/`drop_duplicates()`
call depends on."""

EVENTS_SCHEMA = Schema(
    columns=(
        ColumnSchema(name="event_id", dtype="string"),
        ColumnSchema(name="event_type", dtype="string"),
        ColumnSchema(name="payment_id", dtype="string"),
        ColumnSchema(name="order_id", dtype="string"),
        ColumnSchema(name="customer_id", dtype="string"),
        ColumnSchema(name="amount", dtype="float64"),
    )
)


def _customer_id_for(order_id: str) -> str:
    if order_id in (DECOY_ORDER_A, DECOY_ORDER_B):
        return DECOY_CUSTOMER
    return f"C-{order_id[1:]}"


def _build_raw_rows() -> list[dict]:
    event_counter = 0
    payment_counter = 0

    def next_event_id() -> str:
        nonlocal event_counter
        event_counter += 1
        return f"E{event_counter:03d}"

    def next_payment_id() -> str:
        nonlocal payment_counter
        payment_counter += 1
        return f"P{payment_counter:02d}"

    real_events: list[dict] = []

    for order_id in SINGLE_ATTEMPT_ORDERS:
        payment_id = next_payment_id()
        customer_id = _customer_id_for(order_id)
        for event_type in ("created", "authorized", "captured"):
            real_events.append(
                {
                    "event_id": next_event_id(),
                    "event_type": event_type,
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "amount": CAPTURED_AMOUNT,
                }
            )

    for order_id in RETRY_ORDERS:
        customer_id = _customer_id_for(order_id)
        declined_payment_id = next_payment_id()
        for event_type in ("created", "declined"):
            real_events.append(
                {
                    "event_id": next_event_id(),
                    "event_type": event_type,
                    "payment_id": declined_payment_id,
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "amount": CAPTURED_AMOUNT,
                }
            )
        retry_payment_id = next_payment_id()
        for event_type in ("created", "authorized", "captured"):
            real_events.append(
                {
                    "event_id": next_event_id(),
                    "event_type": event_type,
                    "payment_id": retry_payment_id,
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "amount": CAPTURED_AMOUNT,
                }
            )

    assert len(real_events) == 70

    def find_event(order_id: str, event_type: str) -> dict:
        return next(e for e in real_events if e["order_id"] == order_id and e["event_type"] == event_type)

    rows = list(real_events)

    for order_id in REPLAY_CAPTURED_ORDERS:
        rows.append(dict(find_event(order_id, "captured")))
    for order_id in REPLAY_AUTHORIZED_ORDERS:
        rows.append(dict(find_event(order_id, "authorized")))

    conflicting_copy = dict(find_event(CONFLICT_ORDER, "captured"))
    conflicting_copy["amount"] = CONFLICTING_AMOUNT
    rows.append(conflicting_copy)

    return rows


def generate_events() -> Dataset:
    """The raw, untouched payment-event feed - 77 rows, deterministic,
    hand-verified (see the module docstring above). Every downstream
    stage replays a student's own real resolution against this via
    apply_round1/apply_round2, never a ground-truth substitute."""
    frame = pd.DataFrame(_build_raw_rows())[list(EVENT_COLUMNS)]
    return Dataset(name="events", frame=frame, schema=EVENTS_SCHEMA)


def true_captured_gmv() -> float:
    """Hidden true GMV - generator/tests only, never shown to the player
    or the scorer. The $50 copy was always the correct one in this
    dataset; used only to confirm the generator's own internal
    consistency, exactly like L07's hidden true SLA rate."""
    return len(ALL_ORDERS) * CAPTURED_AMOUNT


# --- Real, live-computed stats - never a hand-typed number -----------------


def unique_event_count(dataset: Dataset) -> int:
    return int(dataset.frame["event_id"].nunique())


def full_row_duplicate_count(dataset: Dataset) -> int:
    return int(dataset.frame.duplicated().sum())


def duplicate_count_by(dataset: Dataset, column: str) -> int:
    return int(dataset.frame.duplicated(subset=[column], keep=False).sum())


def captured_summary(dataset: Dataset) -> tuple[int, float]:
    """(captured row count, captured GMV) - computed live from whatever
    dataset is passed in, so a naive/correct/in-between pipeline all
    produce their own real, honest numbers. Used only pre-conflict-
    resolution (the Round 1 consequence reveal), where every captured
    row's own amount is still a real, known value - see captured_state()
    for the post-Round-2 case, where a quarantined row's own amount can
    be genuinely unresolved (NaN, skipped by .sum() automatically)."""
    captured = dataset.frame[dataset.frame["event_type"] == "captured"]
    return int(len(captured)), float(captured["amount"].sum())


def captured_state(dataset: Dataset) -> tuple[int, float, float]:
    """(captured order count, confirmed-GMV low bound, confirmed-GMV high
    bound) - low == high whenever every captured row's own amount is
    fully resolved. A conflict in one attribute (amount) doesn't erase
    every fact the two conflicting records actually agreed on (event_id,
    event_type, payment_id, order_id, customer_id) - so the correct
    quarantine policy keeps the row (a real captured order, still
    counted) and only nulls its own disputed amount, rather than
    dropping the row outright. `.sum()` skips NaN by default, which is
    exactly the "confirmed GMV, excluding whatever's still disputed"
    number this function needs - the disputed amount's own real range
    (never a single hidden "true" value) is recovered by looking up the
    raw feed's own two real observed values for that one event."""
    captured = dataset.frame[dataset.frame["event_type"] == "captured"]
    count = int(len(captured))
    disputed = captured[captured["amount"].isna()]
    confirmed_gmv = float(captured["amount"].sum())
    if disputed.empty:
        return count, confirmed_gmv, confirmed_gmv
    raw_captured = generate_events().frame.pipe(lambda f: f[f["event_type"] == "captured"])
    disputed_amounts = raw_captured[raw_captured["event_id"].isin(disputed["event_id"])]["amount"]
    return count, confirmed_gmv + float(disputed_amounts.min()), confirmed_gmv + float(disputed_amounts.max())


def unique_event_count_python_code() -> str:
    return "events.event_id.nunique()"


def full_row_duplicate_count_python_code() -> str:
    return "events.duplicated().sum()"


def duplicate_count_by_python_code(column: str) -> str:
    return f"events.duplicated(subset=['{column}'], keep=False).sum()"


def captured_count_python_code() -> str:
    return "events[events.event_type == 'captured'].shape[0]"


def captured_gmv_python_code() -> str:
    return "events[events.event_type == 'captured']['amount'].sum()"


# --- Round 1: which key decides two rows are "the same event" -------------


def _dedupe_by_order_id(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop_duplicates(subset=["order_id"], keep="first").reset_index(drop=True)


def _dedupe_by_event_id_keep_first(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop_duplicates(subset=["event_id"], keep="first").reset_index(drop=True)


def _remove_exact_repeats_only(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop_duplicates(keep="first").reset_index(drop=True)


ROUND1_ISSUE = RepairIssue(
    column="event_id",
    prompt_key="lesson.l08.issue.event_id.prompt",
    options=(
        RepairOption(
            "dedupe_by_order_id",
            "lesson.l08.option.event_id.dedupe_by_order_id",
            _dedupe_by_order_id,
            python_code="events = events.drop_duplicates(subset=['order_id'], keep='first')",
        ),
        RepairOption(
            "dedupe_by_event_id_keep_first",
            "lesson.l08.option.event_id.dedupe_by_event_id_keep_first",
            _dedupe_by_event_id_keep_first,
            python_code="events = events.drop_duplicates(subset=['event_id'], keep='first')",
        ),
        RepairOption(
            "remove_exact_repeats_only",
            "lesson.l08.option.event_id.remove_exact_repeats_only",
            _remove_exact_repeats_only,
            python_code="events = events.drop_duplicates(keep='first')",
        ),
    ),
    hint_key="lesson.l08.issue.event_id.hint",
    evidence_key="lesson.l08.issue.event_id.evidence",
)

CORRECT_DEDUPE_KEY = "remove_exact_repeats_only"
"""Removes only rows with zero informational difference from another row
(the 6 pure transport replays), leaving the one real conflict fully
intact and visible for Round 2 to actually handle - never silently
resolving something that hasn't been investigated yet."""

HIGH_REPRODUCIBILITY_ROUND1_KEYS = frozenset({"remove_exact_repeats_only"})
"""Removes a row only when it's byte-for-byte identical to another one -
which of the two identical copies physically survives never changes the
real result, so this option's own outcome doesn't depend on row order
at all, regardless of whether it's also the objectively correct pick
(METHOD's own separate question)."""
MEDIUM_REPRODUCIBILITY_ROUND1_KEYS = frozenset({"dedupe_by_order_id", "dedupe_by_event_id_keep_first"})
"""Both are real, stated, deterministic rules - but which specific row
survives when two rows genuinely disagree depends on physical row
order, an implicit assumption about arrival order rather than an
explicit, order-independent criterion."""


# --- Round 2: what to do about the one conflicting duplicate ---------------


def _quarantine_and_disclose(frame: pd.DataFrame) -> pd.DataFrame:
    """A conflict in one attribute (amount) doesn't erase every fact the
    two conflicting records actually agree on (event_id, event_type,
    payment_id, order_id, customer_id) - so this keeps the row (a real
    captured order, still counted) and only nulls its own disputed
    amount, instead of dropping the row outright. Once every conflicting
    copy's own amount reads NaN, they're identical on every remaining
    column, so keep='first' is no longer an arbitrary pick - there's
    nothing left to arbitrate between."""
    result = frame.copy()
    conflicted = result.groupby("event_id")["amount"].transform("nunique") > 1
    result.loc[conflicted, "amount"] = float("nan")
    return result.drop_duplicates(subset=["event_id"], keep="first").reset_index(drop=True)


def _keep_first_by_event_id(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop_duplicates(subset=["event_id"], keep="first").reset_index(drop=True)


def _keep_last_by_event_id(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop_duplicates(subset=["event_id"], keep="last").reset_index(drop=True)


def _keep_higher_amount(frame: pd.DataFrame) -> pd.DataFrame:
    idx = frame.groupby("event_id")["amount"].idxmax()
    return frame.loc[idx].reset_index(drop=True)


ROUND2_ISSUE = RepairIssue(
    column="amount",
    prompt_key="lesson.l08.issue.amount.prompt",
    options=(
        RepairOption(
            "keep_first_by_event_id",
            "lesson.l08.option.amount.keep_first_by_event_id",
            _keep_first_by_event_id,
            python_code="events = events.drop_duplicates(subset=['event_id'], keep='first')",
        ),
        RepairOption(
            "quarantine_and_disclose",
            "lesson.l08.option.amount.quarantine_and_disclose",
            _quarantine_and_disclose,
            python_code=(
                "conflicted = events.groupby('event_id')['amount'].transform('nunique') > 1\n"
                "events.loc[conflicted, 'amount'] = float('nan')  # keep the row, drop only the disputed amount\n"
                "events = events.drop_duplicates(subset=['event_id'], keep='first')"
            ),
            result_nullable=True,
        ),
        RepairOption(
            "keep_last_by_event_id",
            "lesson.l08.option.amount.keep_last_by_event_id",
            _keep_last_by_event_id,
            python_code="events = events.drop_duplicates(subset=['event_id'], keep='last')",
        ),
        RepairOption(
            "keep_higher_amount",
            "lesson.l08.option.amount.keep_higher_amount",
            _keep_higher_amount,
            python_code="idx = events.groupby('event_id')['amount'].idxmax()\nevents = events.loc[idx]",
        ),
    ),
    hint_key="lesson.l08.issue.amount.hint",
    evidence_key="lesson.l08.issue.amount.evidence",
)

CORRECT_CONFLICT_POLICY = "quarantine_and_disclose"

HIGH_REPRODUCIBILITY_ROUND2_KEYS = frozenset({"quarantine_and_disclose", "keep_higher_amount"})
"""Both decide purely from the values themselves (a real computed
conflict check; a real value comparison) - the result never depends on
which physical row happened to arrive first, regardless of whether the
rule itself is also the objectively correct one (METHOD's own separate
question - keep_higher_amount is a real, stated rule and scores well
here, even though it isn't the disclosed quarantine policy METHOD
requires)."""
MEDIUM_REPRODUCIBILITY_ROUND2_KEYS = frozenset({"keep_first_by_event_id", "keep_last_by_event_id"})
"""Real, stated rules - but which row survives a genuine conflict
depends on physical row order, an implicit assumption rather than an
explicit, order-independent criterion."""


def apply_round1(resolution: RepairResolution) -> Dataset:
    return apply_resolution(generate_events(), (ROUND1_ISSUE,), resolution)


def apply_round2(round1_resolution: RepairResolution, round2_resolution: RepairResolution) -> Dataset:
    dataset = apply_round1(round1_resolution)
    return apply_resolution(dataset, (ROUND2_ISSUE,), round2_resolution)


# --- Duplicate group investigation - real, representative row clusters ----

GROUP_DISPLAY_COLUMNS: tuple[str, ...] = ("event_id", "event_type", "payment_id", "order_id", "customer_id", "amount")


def _format_cell(value) -> str:
    if isinstance(value, float):
        return f"${value:.2f}"
    return str(value)


def _stringify_rows(frame: pd.DataFrame) -> tuple[dict[str, str], ...]:
    return tuple(
        {column: _format_cell(row[column]) for column in GROUP_DISPLAY_COLUMNS} for _, row in frame.iterrows()
    )


def build_replay_group(dataset: Dataset) -> DuplicateGroup:
    frame = dataset.frame
    rows = frame[(frame["order_id"] == REPLAY_CAPTURED_ORDERS[0]) & (frame["event_type"] == "captured")]
    return DuplicateGroup(
        key="replay_group",
        key_column="event_id",
        columns=GROUP_DISPLAY_COLUMNS,
        rows=_stringify_rows(rows),
        prompt_key="lesson.l08.group.replay.prompt",
        hint_key="lesson.l08.group.replay.hint",
    )


LIFECYCLE_GROUP_ORDER = "O08"  # untouched by any replay/conflict/decoy injection


def build_lifecycle_group(dataset: Dataset) -> DuplicateGroup:
    frame = dataset.frame
    rows = frame[frame["order_id"] == LIFECYCLE_GROUP_ORDER]
    return DuplicateGroup(
        key="lifecycle_group",
        key_column="payment_id",
        columns=GROUP_DISPLAY_COLUMNS,
        rows=_stringify_rows(rows),
        prompt_key="lesson.l08.group.lifecycle.prompt",
        hint_key="lesson.l08.group.lifecycle.hint",
    )


def build_retry_group(dataset: Dataset) -> DuplicateGroup:
    frame = dataset.frame
    rows = frame[frame["order_id"] == RETRY_ORDERS[0]]
    return DuplicateGroup(
        key="retry_group",
        key_column="order_id",
        columns=GROUP_DISPLAY_COLUMNS,
        rows=_stringify_rows(rows),
        prompt_key="lesson.l08.group.retry.prompt",
        hint_key="lesson.l08.group.retry.hint",
    )


def build_decoy_group(dataset: Dataset) -> DuplicateGroup:
    frame = dataset.frame
    rows = frame[(frame["customer_id"] == DECOY_CUSTOMER) & (frame["event_type"] == "captured")]
    return DuplicateGroup(
        key="decoy_group",
        key_column="customer_id",
        columns=GROUP_DISPLAY_COLUMNS,
        rows=_stringify_rows(rows),
        prompt_key="lesson.l08.group.decoy.prompt",
        hint_key="lesson.l08.group.decoy.hint",
    )


def build_conflict_group(dataset: Dataset) -> DuplicateGroup:
    frame = dataset.frame
    rows = frame[(frame["order_id"] == CONFLICT_ORDER) & (frame["event_type"] == "captured")]
    return DuplicateGroup(
        key="conflict_group",
        key_column="event_id",
        columns=GROUP_DISPLAY_COLUMNS,
        rows=_stringify_rows(rows),
        prompt_key="lesson.l08.group.conflict.prompt",
        hint_key="lesson.l08.group.conflict.hint",
    )


CORRECT_VERDICT_BY_GROUP: dict[str, str] = {
    "replay_group": "safe_to_remove_duplicate",
    "lifecycle_group": "keep_all_not_a_duplicate",
    "retry_group": "keep_all_not_a_duplicate",
    "decoy_group": "keep_all_not_a_duplicate",
    "conflict_group": "conflict_needs_reconciliation",
}

GROUP_EVIDENCE_KEY: dict[str, str] = {
    "retry_group": "lesson.l08.group.retry.evidence",
    "decoy_group": "lesson.l08.group.decoy.evidence",
    "conflict_group": "lesson.l08.group.conflict.evidence",
}
"""Only 3 of the 5 groups carry their own citable evidence fact (retry/
decoy/conflict) - replay and lifecycle are real, correct verdicts too,
but their own underlying facts are already covered by the stage 3
profiling numbers, matching every prior lesson's discipline of not
recording every single correct click as a separate Evidence entry."""


# --- Optional mastery - transfer, not repetition ---------------------------
#
# Different domain, different shape: a warehouse scan log. 8 packages
# (PKG-01..PKG-08), each legitimately scanned at 3 checkpoints (intake,
# sort, dispatch) = 24 real scan events. PKG-03 gets one genuine extra
# QC re-scan at the sort checkpoint - a real, distinct scan_event_id (a
# miniature of the payment feed's own O05/O13 decoy: looks like a
# repeat, is actually a second real occurrence). 2 of the 24 base scans
# (PKG-01's intake, PKG-05's dispatch) get a byte-identical scanner-
# retry replay, reusing their own real scan_event_id. Total real events
# = 24 + 1 = 25; total raw rows = 25 + 2 = 27.

WAREHOUSE_PACKAGES: tuple[str, ...] = tuple(f"PKG-{n:02d}" for n in range(1, 9))
WAREHOUSE_CHECKPOINTS: tuple[str, ...] = ("intake", "sort", "dispatch")
QC_RESCAN_PACKAGE = "PKG-03"
SCANNER_RETRY_PACKAGE_A = "PKG-01"
SCANNER_RETRY_CHECKPOINT_A = "intake"
SCANNER_RETRY_PACKAGE_B = "PKG-05"
SCANNER_RETRY_CHECKPOINT_B = "dispatch"

SCAN_LOG_SCHEMA = Schema(
    columns=(
        ColumnSchema(name="scan_event_id", dtype="string"),
        ColumnSchema(name="package_id", dtype="string"),
        ColumnSchema(name="checkpoint", dtype="string"),
    )
)


def generate_scan_log() -> Dataset:
    scan_counter = 0

    def next_scan_id() -> str:
        nonlocal scan_counter
        scan_counter += 1
        return f"S{scan_counter:03d}"

    real_scans: list[dict] = []
    for package_id in WAREHOUSE_PACKAGES:
        for checkpoint in WAREHOUSE_CHECKPOINTS:
            real_scans.append({"scan_event_id": next_scan_id(), "package_id": package_id, "checkpoint": checkpoint})
    real_scans.append({"scan_event_id": next_scan_id(), "package_id": QC_RESCAN_PACKAGE, "checkpoint": "sort"})

    def find_scan(package_id: str, checkpoint: str) -> dict:
        return next(s for s in real_scans if s["package_id"] == package_id and s["checkpoint"] == checkpoint)

    rows = list(real_scans)
    rows.append(dict(find_scan(SCANNER_RETRY_PACKAGE_A, SCANNER_RETRY_CHECKPOINT_A)))
    rows.append(dict(find_scan(SCANNER_RETRY_PACKAGE_B, SCANNER_RETRY_CHECKPOINT_B)))

    frame = pd.DataFrame(rows)[["scan_event_id", "package_id", "checkpoint"]]
    return Dataset(name="scan_log", frame=frame, schema=SCAN_LOG_SCHEMA)


MASTERY_CORRECT_KEY = "scan_event_id"
MASTERY_CORRECT_PRESERVE = frozenset({"checkpoint_scans", "qc_rescan"})
