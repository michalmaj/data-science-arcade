import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairOption, RepairResolution, apply_resolution

# --- Hidden ground truth: 180 "this month" shipments across 4 stores,
# plus 40 "last month" shipments that must be excluded by a real date
# filter, plus 2 genuinely malformed delivery timestamps. Hand-picked, not
# random - every count and rate below is independently re-derivable by
# summing this table.
#
# Store -> (rows at the "normal" duration, that duration in true minutes,
# rows at the "breach" duration, that duration in true minutes). Store D
# migrated to the new WMS this month; its own duration_minutes column
# actually holds *seconds* (true_minutes * 60) - since even a short true
# delivery multiplies well past 60, every one of D's 36 rows reads as an
# SLA breach once misread as minutes, regardless of its real value.
STORES: dict[str, tuple[int, int, int, int]] = {
    "A": (54, 30, 6, 75),
    "B": (53, 30, 7, 75),
    "C": (20, 30, 4, 90),
    "D": (31, 32, 5, 85),
}
THIS_MONTH = "2026-09"
LAST_MONTH = "2026-08"
# Last month predates the WMS migration entirely (no unit-drift issue) -
# a real, independently-computed breach rate (5/40 = 12.5%), close to this
# month's own true 12.2%, so nothing about delivery speed actually changed
# month over month. This is Reveal 1's own comparison baseline: this
# month's naive 29.4% looking like it more than doubled is itself a real,
# honest reason to double-check, discovered from two genuine numbers, not
# hinted at directly.
LAST_MONTH_NORMAL_ROWS = 35
LAST_MONTH_NORMAL_MINUTES = 30
LAST_MONTH_BREACH_ROWS = 5
LAST_MONTH_BREACH_MINUTES = 80
MALFORMED_ROWS = 2  # folded into Store A's own "this month" rows, see _rows()
SLA_MINUTES = 60

RAW_SCHEMA = Schema(
    columns=(
        ColumnSchema("shipment_id", "int64", description_key="lesson.l06.schema.shipment_id.description"),
        ColumnSchema("store", "object"),
        ColumnSchema("delivered_at", "object", description_key="lesson.l06.schema.delivered_at.description"),
        ColumnSchema("duration_minutes", "float64", description_key="lesson.l06.schema.duration_minutes.description"),
        ColumnSchema("item_count", "int64", description_key="lesson.l06.schema.item_count.description"),
    )
)


def _rows() -> list[dict]:
    rows: list[dict] = []
    shipment_id = 100001
    day = 1
    for store, (n_normal, normal_minutes, n_breach, breach_minutes) in STORES.items():
        for _ in range(n_normal):
            rows.append(_row(shipment_id, store, day, f"{THIS_MONTH}-{day:02d}", normal_minutes))
            shipment_id += 1
            day = day % 28 + 1
        for _ in range(n_breach):
            rows.append(_row(shipment_id, store, day, f"{THIS_MONTH}-{day:02d}", breach_minutes))
            shipment_id += 1
            day = day % 28 + 1

    # 2 genuinely malformed timestamps - real shipments this month, but
    # their own delivered_at string can't be parsed at all, so they must
    # be explicitly excluded (and counted), not silently coerced away or
    # force-matched.
    rows.append(_row(shipment_id, "A", day, "2026-13-45", 30))
    shipment_id += 1
    rows.append(_row(shipment_id, "A", day, "not-a-timestamp", 30))
    shipment_id += 1

    # 40 last-month shipments - must be excluded from this month's KPI by
    # a real date filter, never by store or any other shortcut. Predates
    # the WMS migration entirely, so every row here is genuinely in
    # minutes - a real, independent baseline for Reveal 1 (see LAST_MONTH_*
    # above), not decoration.
    for _ in range(LAST_MONTH_NORMAL_ROWS):
        rows.append(_row(shipment_id, "A", day, f"{LAST_MONTH}-{day:02d}", LAST_MONTH_NORMAL_MINUTES))
        shipment_id += 1
        day = day % 28 + 1
    for _ in range(LAST_MONTH_BREACH_ROWS):
        rows.append(_row(shipment_id, "A", day, f"{LAST_MONTH}-{day:02d}", LAST_MONTH_BREACH_MINUTES))
        shipment_id += 1
        day = day % 28 + 1

    return rows


def _row(shipment_id: int, store: str, _day: int, delivered_at: str, true_minutes: int) -> dict:
    stored_minutes = float(true_minutes * 60) if store == "D" else float(true_minutes)
    return {
        "shipment_id": shipment_id,
        "store": store,
        "delivered_at": delivered_at,
        "duration_minutes": stored_minutes,
        "item_count": (shipment_id % 8) + 1,
    }


def generate_shipments() -> Dataset:
    frame = pd.DataFrame(_rows())
    step = PipelineStep(
        "raw_export",
        python_code="shipments = pd.read_csv('novamart_wms_shipments.csv')  # exported from the new WMS",
    )
    return Dataset(name="shipments", frame=frame, schema=RAW_SCHEMA, history=(step,))


def apply_round1(resolution: RepairResolution) -> Dataset:
    """Replays whatever the student actually picked for shipment_id and
    delivered_at against the real raw export - right or wrong. Every
    downstream stage works from this, never from a ground-truth
    substitute for what actually happened; an unresolved column (not yet
    in `resolution`) is simply left as-is, matching apply_resolution's
    own contract."""
    return apply_resolution(generate_shipments(), ROUND1_ISSUES, resolution)


def apply_round2(round1_resolution: RepairResolution, round2_resolution: RepairResolution) -> Dataset:
    """Round 1's real result, with Round 2's real duration_minutes pick
    replayed on top of it - the actual final dataset every KPI reveal
    from Reveal 2 onward is computed against."""
    return apply_resolution(apply_round1(round1_resolution), ROUND2_ISSUES, round2_resolution)


def _this_month(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["delivered_at"].dt.strftime("%Y-%m") == THIS_MONTH]


def malformed_count(dataset: Dataset) -> int:
    """How many rows currently hold an unparseable (NaT) delivered_at -
    computed on whatever the student's own delivered_at repair actually
    produced, not assumed. The true 2 malformed rows only show up as 2
    here if they were kept visible (coerce_keep_nat); a repair that
    drops them instead removes any trace (0), and one that mismatches
    the real format turns every row into NaT (very large) - both real,
    honest consequences of that choice, not a fixed constant."""
    return int(dataset.frame["delivered_at"].isna().sum())


def breach_rate(dataset: Dataset) -> float:
    """The one real KPI this lesson reports: the fraction of this
    month's shipments whose delivery duration exceeded the 60-minute
    SLA, read at face value from duration_minutes on whatever dataset is
    passed in - never a separately-applied "correct" conversion. Before
    duration_minutes is repaired this is the naive, plausible-but-wrong
    reading (Store D's rows are all misread as breaching); after a real
    repair has actually changed the underlying values, this reads
    whatever that repair really produced, right or wrong. Returns NaN if
    no row this month has a parseable timestamp at all (a real, honest
    "can't compute this" consequence of a badly chosen delivered_at
    repair, not a crash)."""
    frame = _this_month(dataset.frame)
    if len(frame) == 0:
        return float("nan")
    return float((frame["duration_minutes"] > SLA_MINUTES).mean())


def last_month_breach_rate(dataset: Dataset) -> float:
    """A real, independent baseline from before the WMS migration - no
    unit-drift issue exists in last month's own data, so this is a
    genuinely correct number, computed the same simple way this month's
    naive (uncorrected) rate is. Reveal 1 pairs this against this month's
    own naive rate - the apparent jump is real evidence something is
    worth checking, discovered from two honest numbers, not stated."""
    frame = dataset.frame
    last_month = frame[frame["delivered_at"].dt.strftime("%Y-%m") == LAST_MONTH]
    return float((last_month["duration_minutes"] > SLA_MINUTES).mean())


def last_month_breach_rate_python_code() -> str:
    return "last_month = shipments[shipments['delivered_at'].dt.strftime('%Y-%m') == '2026-08']\n(last_month['duration_minutes'] > 60).mean()"


def breach_rate_python_code() -> str:
    # The same one-liner regardless of which reveal shows it: any real
    # duration_minutes repair already happened upstream (and is shown
    # there, in the Workbench's own Python Mirror) - this just reads
    # whatever the column currently holds, honestly, at either point.
    return (
        "this_month = shipments[shipments['delivered_at'].dt.strftime('%Y-%m') == '2026-09']\n"
        "(this_month['duration_minutes'] > 60).mean()"
    )


# --- Round 1 repair issues: shipment_id (identifier, not a measure) and
# delivered_at (needs real parsing, malformed rows handled explicitly) ---


def _shipment_id_as_text(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(shipment_id=frame["shipment_id"].astype("string"))


def _shipment_id_recast_int(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(shipment_id=frame["shipment_id"].astype("int64"))


def _shipment_id_as_category(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(shipment_id=frame["shipment_id"].astype("category"))


def _delivered_at_coerce_keep_nat(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(delivered_at=pd.to_datetime(frame["delivered_at"], errors="coerce"))


def _delivered_at_coerce_then_drop(frame: pd.DataFrame) -> pd.DataFrame:
    parsed = frame.assign(delivered_at=pd.to_datetime(frame["delivered_at"], errors="coerce"))
    return parsed.dropna(subset=["delivered_at"]).reset_index(drop=True)


def _delivered_at_wrong_format(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(delivered_at=pd.to_datetime(frame["delivered_at"], format="%d-%m-%Y", errors="coerce"))


SHIPMENT_ID_ISSUE = RepairIssue(
    column="shipment_id",
    prompt_key="lesson.l06.issue.shipment_id.prompt",
    hint_key="lesson.l06.issue.shipment_id.hint",
    evidence_key="lesson.l06.issue.shipment_id.evidence",
    options=(
        # An identifier can be validly kept numeric or cast to text - both
        # protect it from being treated as a quantity by accident; only
        # category (a poor fit for ~220 nearly-unique values) is the real
        # wrong pick here. See CORRECT_REPAIR below.
        RepairOption(
            "cast_to_text",
            "lesson.l06.option.shipment_id.cast_to_text",
            _shipment_id_as_text,
            python_code="shipments['shipment_id'] = shipments['shipment_id'].astype('string')",
            result_dtype="string",
            result_description_key="lesson.l06.schema.shipment_id.description_fixed",
        ),
        RepairOption(
            "recast_int",
            "lesson.l06.option.shipment_id.recast_int",
            _shipment_id_recast_int,
            python_code="shipments['shipment_id'] = shipments['shipment_id'].astype('int64')",
            result_dtype="int64",
            result_description_key="lesson.l06.schema.shipment_id.description_fixed",
        ),
        RepairOption(
            "cast_category",
            "lesson.l06.option.shipment_id.cast_category",
            _shipment_id_as_category,
            python_code="shipments['shipment_id'] = shipments['shipment_id'].astype('category')",
            result_dtype="category",
        ),
    ),
)

DELIVERED_AT_ISSUE = RepairIssue(
    column="delivered_at",
    prompt_key="lesson.l06.issue.delivered_at.prompt",
    hint_key="lesson.l06.issue.delivered_at.hint",
    evidence_key="lesson.l06.issue.delivered_at.evidence",
    options=(
        RepairOption(
            "coerce_keep_nat",
            "lesson.l06.option.delivered_at.coerce_keep_nat",
            _delivered_at_coerce_keep_nat,
            python_code="shipments['delivered_at'] = pd.to_datetime(shipments['delivered_at'], errors='coerce')",
            result_dtype="datetime64[ns]",
            result_description_key="lesson.l06.schema.delivered_at.description_fixed",
        ),
        RepairOption(
            "coerce_then_drop",
            "lesson.l06.option.delivered_at.coerce_then_drop",
            _delivered_at_coerce_then_drop,
            python_code=(
                "shipments['delivered_at'] = pd.to_datetime(shipments['delivered_at'], errors='coerce')\n"
                "shipments = shipments.dropna(subset=['delivered_at'])"
            ),
            result_dtype="datetime64[ns]",
            result_description_key="lesson.l06.schema.delivered_at.description_fixed_dropped",
        ),
        RepairOption(
            "wrong_format",
            "lesson.l06.option.delivered_at.wrong_format",
            _delivered_at_wrong_format,
            python_code="shipments['delivered_at'] = pd.to_datetime(shipments['delivered_at'], format='%d-%m-%Y', errors='coerce')",
            result_dtype="datetime64[ns]",
            result_description_key="lesson.l06.schema.delivered_at.description_fixed_wrong_format",
        ),
    ),
)

ROUND1_ISSUES: tuple[RepairIssue, ...] = (SHIPMENT_ID_ISSUE, DELIVERED_AT_ISSUE)


# --- Round 2 repair issue: duration_minutes's own unit drift on Store D ---


def _duration_fix_store_d_only(frame: pd.DataFrame) -> pd.DataFrame:
    fixed = frame["duration_minutes"].where(frame["store"] != "D", frame["duration_minutes"] / 60)
    return frame.assign(duration_minutes=fixed)


def _duration_fix_every_row(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(duration_minutes=frame["duration_minutes"] / 60)


def _duration_recast_float(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(duration_minutes=frame["duration_minutes"].astype("float64"))


DURATION_ISSUE = RepairIssue(
    column="duration_minutes",
    prompt_key="lesson.l06.issue.duration_minutes.prompt",
    hint_key="lesson.l06.issue.duration_minutes.hint",
    evidence_key="lesson.l06.issue.duration_minutes.evidence",
    options=(
        RepairOption(
            "fix_store_d_only",
            "lesson.l06.option.duration_minutes.fix_store_d_only",
            _duration_fix_store_d_only,
            python_code="shipments.loc[shipments['store'] == 'D', 'duration_minutes'] /= 60",
            result_description_key="lesson.l06.schema.duration_minutes.description_fixed",
        ),
        RepairOption(
            "fix_every_row",
            "lesson.l06.option.duration_minutes.fix_every_row",
            _duration_fix_every_row,
            python_code="shipments['duration_minutes'] /= 60",
            result_description_key="lesson.l06.schema.duration_minutes.description_fixed_every_row",
        ),
        RepairOption(
            "recast_float",
            "lesson.l06.option.duration_minutes.recast_float",
            _duration_recast_float,
            python_code="shipments['duration_minutes'] = shipments['duration_minutes'].astype('float64')",
            # No result_description_key: this option is a real no-op (the
            # column was already float64), so nothing about the migration
            # note has actually stopped being true - flipping it to the
            # "fixed" description here would claim a fix that never
            # happened.
        ),
    ),
)

ROUND2_ISSUES: tuple[RepairIssue, ...] = (DURATION_ISSUE,)

CORRECT_REPAIR: dict[str, frozenset[str]] = {
    "shipment_id": frozenset({"cast_to_text", "recast_int"}),
    "delivered_at": frozenset({"coerce_keep_nat"}),
    "duration_minutes": frozenset({"fix_store_d_only"}),
}
"""The objectively acceptable resolution(s) for each real schema problem -
shipment_id has *two*, deliberately: an identifier's own physical
representation doesn't need to change just because its semantic type is
"identifier" (keeping it int64 is just as valid as casting it to text, as
long as nothing aggregates it) - only delivered_at and duration_minutes
have exactly one real fix. Shared by the scorer (which resolution counts
as REPRODUCIBILITY) and by the scenario itself (which Round-1 issues get
a real second chance in Round 2, once their own consequence has actually
been seen)."""


# --- Optional mastery: a new, small export - transfer, not repetition ---

MASTERY_SCHEMA = Schema(
    columns=(
        ColumnSchema("store_id", "int64", description_key="lesson.l06.mastery.schema.store_id.description"),
        ColumnSchema("revenue", "object", description_key="lesson.l06.mastery.schema.revenue.description"),
        ColumnSchema("promo_code", "object", description_key="lesson.l06.mastery.schema.promo_code.description"),
        ColumnSchema("quantity", "int64", description_key="lesson.l06.mastery.schema.quantity.description"),
    )
)

_MASTERY_ROWS = [
    (1042, "$128.50", "PROMO007", 3),
    (1043, "$64.00", "SUMMER2026", 1),
    (1044, "$212.75", "PROMO007", 5),
    (1045, "$19.99", "WELCOME10", 2),
    (1046, "$340.10", "SUMMER2026", 7),
    (1047, "$88.25", "PROMO007", 4),
]


MASTERY_CORRECT: frozenset[str] = frozenset({"store_id", "revenue"})
"""store_id looks fine (int64) but is an identifier that still needs its
contract declared and protected from aggregation, even though its own
physical dtype doesn't need to change; revenue looks wrong (object) but
is a cleanly parseable currency string that does need a real fix. A
"schema fix" here means resolving the real contract gap, not necessarily
a dtype cast - the same distinction the shipment_id issue itself teaches.
promo_code and quantity are deliberately not in this set - one *looks*
unusual but is already correctly typed, the other already correctly is a
measure."""

SAFE_COLUMNS_CORRECT: frozenset[str] = frozenset({"item_count"})
"""shipment_id (an identifier) and delivered_at (unparsed text) are never
safe to summarize; item_count already is. duration_minutes isn't offered
at prediction time at all - nothing discoverable yet contradicts it."""


def generate_mastery_export() -> Dataset:
    frame = pd.DataFrame(_MASTERY_ROWS, columns=["store_id", "revenue", "promo_code", "quantity"])
    step = PipelineStep(
        "mastery_export",
        python_code="orders = pd.read_csv('novamart_store_orders.csv')",
    )
    return Dataset(name="orders", frame=frame, schema=MASTERY_SCHEMA, history=(step,))
