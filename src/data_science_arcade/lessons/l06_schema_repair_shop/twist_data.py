import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairOption

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

# shipment_id and delivered_at are the two Round-1 issues, both fixed in the
# same WorkbenchScene visit - both get this one, shared, fully-repaired
# schema as their schema_after, so the schema tab is correct regardless of
# which of the two the student resolves first (a single-issue schema_after
# for either one alone would, for whichever issue resolves second, still
# show the *other* one as unfixed even after it's genuinely fixed).
ROUND1_FIXED_SCHEMA = Schema(
    columns=(
        ColumnSchema("shipment_id", "string", description_key="lesson.l06.schema.shipment_id.description_fixed"),
        ColumnSchema("store", "object"),
        ColumnSchema(
            "delivered_at", "datetime64[ns]", description_key="lesson.l06.schema.delivered_at.description_fixed"
        ),
        ColumnSchema("duration_minutes", "float64", description_key="lesson.l06.schema.duration_minutes.description"),
        ColumnSchema("item_count", "int64", description_key="lesson.l06.schema.item_count.description"),
    )
)

# duration_minutes's own dtype never changes (float64 throughout) - only
# its *values* change for Store D, and only its *description* needs to
# change (the migration note is no longer relevant once fixed) - the same
# "value/description change, no dtype change" shape the original L06's
# own currency issue used.
ROUND2_FIXED_SCHEMA = Schema(
    columns=(
        ColumnSchema("shipment_id", "string", description_key="lesson.l06.schema.shipment_id.description_fixed"),
        ColumnSchema("store", "object"),
        ColumnSchema(
            "delivered_at", "datetime64[ns]", description_key="lesson.l06.schema.delivered_at.description_fixed"
        ),
        ColumnSchema(
            "duration_minutes", "float64", description_key="lesson.l06.schema.duration_minutes.description_fixed"
        ),
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


def generate_shipments_after_round1() -> Dataset:
    """The same population, with Round 1's two fixes (shipment_id cast to
    text, delivered_at parsed with malformed rows excluded and counted)
    already baked in - regenerated fresh rather than carrying forward the
    real WorkbenchScene's own resulting Dataset, since on_complete only
    returns the RepairResolution dict, not the dataset itself. Matches
    this project's own established pattern (the original L06's two rounds
    each call generate_sales_export() fresh; L04's evidence_review
    regenerates from an earlier declaration) - the correct fix always
    applies regardless of what the student actually picked, the same way
    L04's own Combined Workbench visit doesn't depend on an earlier
    stage's real correctness either."""
    frame = pd.DataFrame(_rows())
    frame["shipment_id"] = frame["shipment_id"].astype("string")
    frame["delivered_at"] = pd.to_datetime(frame["delivered_at"], errors="coerce")
    step = PipelineStep(
        "round1_repaired",
        python_code=(
            "shipments['shipment_id'] = shipments['shipment_id'].astype('string')\n"
            "shipments['delivered_at'] = pd.to_datetime(shipments['delivered_at'], errors='coerce')"
        ),
    )
    return Dataset(name="shipments", frame=frame, schema=ROUND1_FIXED_SCHEMA, history=(step,))


def _this_month(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["delivered_at"].dt.strftime("%Y-%m") == THIS_MONTH]


def malformed_count(dataset: Dataset) -> int:
    """How many rows failed to parse as a real timestamp at all - a NaT
    delivered_at can't itself be dated as "this month" or not, so this
    counts every parse failure directly (all 2 of them are genuinely this
    month's own shipments in this generator, not last-month noise)."""
    return int(dataset.frame["delivered_at"].isna().sum())


def breach_rate(dataset: Dataset, corrected: bool) -> float:
    """The one real KPI this lesson reports: the fraction of this month's
    shipments whose delivery duration exceeded the 60-minute SLA.
    `corrected=False` reads duration_minutes at face value (the naive,
    plausible-but-wrong 29.4% - Store D's rows are all misread as
    breaching); `corrected=True` first converts Store D's rows from
    seconds to minutes (12.2%, the true rate)."""
    frame = _this_month(dataset.frame)
    duration = frame["duration_minutes"]
    if corrected:
        duration = duration.where(frame["store"] != "D", duration / 60)
    return float((duration > SLA_MINUTES).mean())


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


def breach_rate_python_code(corrected: bool) -> str:
    if not corrected:
        return (
            "this_month = shipments[shipments['delivered_at'].dt.strftime('%Y-%m') == '2026-09']\n"
            "(this_month['duration_minutes'] > 60).mean()"
        )
    return (
        "this_month = shipments[shipments['delivered_at'].dt.strftime('%Y-%m') == '2026-09']\n"
        "corrected = this_month['duration_minutes'].where(this_month['store'] != 'D', this_month['duration_minutes'] / 60)\n"
        "(corrected > 60).mean()"
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
    schema_after=ROUND1_FIXED_SCHEMA,
    options=(
        RepairOption(
            "cast_to_text",
            "lesson.l06.option.shipment_id.cast_to_text",
            _shipment_id_as_text,
            python_code="shipments['shipment_id'] = shipments['shipment_id'].astype('string')",
        ),
        RepairOption(
            "recast_int",
            "lesson.l06.option.shipment_id.recast_int",
            _shipment_id_recast_int,
            python_code="shipments['shipment_id'] = shipments['shipment_id'].astype('int64')",
        ),
        RepairOption(
            "cast_category",
            "lesson.l06.option.shipment_id.cast_category",
            _shipment_id_as_category,
            python_code="shipments['shipment_id'] = shipments['shipment_id'].astype('category')",
        ),
    ),
)

DELIVERED_AT_ISSUE = RepairIssue(
    column="delivered_at",
    prompt_key="lesson.l06.issue.delivered_at.prompt",
    hint_key="lesson.l06.issue.delivered_at.hint",
    evidence_key="lesson.l06.issue.delivered_at.evidence",
    schema_after=ROUND1_FIXED_SCHEMA,
    options=(
        RepairOption(
            "coerce_keep_nat",
            "lesson.l06.option.delivered_at.coerce_keep_nat",
            _delivered_at_coerce_keep_nat,
            python_code="shipments['delivered_at'] = pd.to_datetime(shipments['delivered_at'], errors='coerce')",
        ),
        RepairOption(
            "coerce_then_drop",
            "lesson.l06.option.delivered_at.coerce_then_drop",
            _delivered_at_coerce_then_drop,
            python_code=(
                "shipments['delivered_at'] = pd.to_datetime(shipments['delivered_at'], errors='coerce')\n"
                "shipments = shipments.dropna(subset=['delivered_at'])"
            ),
        ),
        RepairOption(
            "wrong_format",
            "lesson.l06.option.delivered_at.wrong_format",
            _delivered_at_wrong_format,
            python_code="shipments['delivered_at'] = pd.to_datetime(shipments['delivered_at'], format='%d-%m-%Y', errors='coerce')",
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
    schema_after=ROUND2_FIXED_SCHEMA,
    options=(
        RepairOption(
            "fix_store_d_only",
            "lesson.l06.option.duration_minutes.fix_store_d_only",
            _duration_fix_store_d_only,
            python_code="shipments.loc[shipments['store'] == 'D', 'duration_minutes'] /= 60",
        ),
        RepairOption(
            "fix_every_row",
            "lesson.l06.option.duration_minutes.fix_every_row",
            _duration_fix_every_row,
            python_code="shipments['duration_minutes'] /= 60",
        ),
        RepairOption(
            "recast_float",
            "lesson.l06.option.duration_minutes.recast_float",
            _duration_recast_float,
            python_code="shipments['duration_minutes'] = shipments['duration_minutes'].astype('float64')",
        ),
    ),
)

ROUND2_ISSUES: tuple[RepairIssue, ...] = (DURATION_ISSUE,)


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
"""store_id looks fine (int64) but is an identifier; revenue looks wrong
(object) but is a cleanly parseable currency string - both genuinely need
a fix. promo_code and quantity are deliberately not in this set - one
*looks* unusual but is already correctly typed, the other already
correctly is a measure."""

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
