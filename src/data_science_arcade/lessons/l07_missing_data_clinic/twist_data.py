import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairOption, RepairResolution, apply_resolution

# --- Hidden ground truth: 400 Go orders this period, crossed into 4 real
# cells by scanner_type x hour_bucket. pick_minutes is stored in minutes;
# SLA_MINUTES = 12. Observed durations cluster at two exact, hand-picked
# values - PASS_MINUTES (8.0) and FAIL_MINUTES (16.0), no per-row jitter -
# the same "hand-picked, not random" discipline L06's own STORES table
# used, and what *guarantees* every cluster stays unambiguously on one
# side of the SLA threshold (asserted directly in tests, not assumed).
SLA_MINUTES = 12
PASS_MINUTES = 8.0
FAIL_MINUTES = 16.0

# Legacy handheld scanners drop the completion-scan event far more often
# during peak-hour, high-session-load conditions - the same cells that
# lose more completion events also perform differently on the ones they
# do capture (legacy+peak is the only cell where captured picks are
# majority-fail, not majority-pass). true_fail_missing/true_pass_missing
# are the hidden, never-surfaced true outcomes for that cell's own
# missing rows - known only to the generator (for internal consistency
# and deterministic tests), never computed by any player-facing function.
CELLS: dict[tuple[str, str], dict[str, int]] = {
    ("legacy", "peak"): dict(obs_pass=12, obs_fail=18, missing=30, true_fail_missing=24, true_pass_missing=6),
    ("legacy", "offpeak"): dict(obs_pass=68, obs_fail=8, missing=14, true_fail_missing=8, true_pass_missing=6),
    ("current", "peak"): dict(obs_pass=90, obs_fail=4, missing=6, true_fail_missing=2, true_pass_missing=4),
    ("current", "offpeak"): dict(obs_pass=140, obs_fail=4, missing=6, true_fail_missing=1, true_pass_missing=5),
}

STORES: tuple[str, ...] = ("A", "B", "C", "D")
"""Legacy/current scanners are both scattered unevenly across all 4
stores, not tied to any one store - so per-store missing rates land
close to flat, a real absence of signal, not a scripted one. Exactly 4,
matching SegmentSlicerScene's own existing precedent (L30's by_region)
for how many segments fit its fixed table layout."""

PROMO_CODES: tuple[str, ...] = ("SAVE10", "FREESHIP", "WELCOME5")
CHILLED_TEMPS: tuple[float, ...] = (3.5, 4.0, 4.5)

RAW_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "int64"),
        ColumnSchema("scanner_type", "object"),
        ColumnSchema("hour_bucket", "object"),
        ColumnSchema("store", "object"),
        ColumnSchema("basket_size", "object"),
        ColumnSchema("contains_chilled", "bool"),
        ColumnSchema(
            "pick_minutes", "float64", nullable=True, description_key="lesson.l07.schema.pick_minutes.description"
        ),
        ColumnSchema(
            "cold_pack_temp_c",
            "float64",
            nullable=True,
            description_key="lesson.l07.schema.cold_pack_temp_c.description",
        ),
        ColumnSchema(
            "promo_code", "object", nullable=True, description_key="lesson.l07.schema.promo_code.description"
        ),
    )
)


def _rows() -> list[dict]:
    rows: list[dict] = []
    order_id = 1
    index = 0
    for (scanner_type, hour_bucket), cell in CELLS.items():
        for _ in range(cell["obs_pass"]):
            rows.append(_row(order_id, scanner_type, hour_bucket, index, PASS_MINUTES))
            order_id += 1
            index += 1
        for _ in range(cell["obs_fail"]):
            rows.append(_row(order_id, scanner_type, hour_bucket, index, FAIL_MINUTES))
            order_id += 1
            index += 1
        for _ in range(cell["missing"]):
            rows.append(_row(order_id, scanner_type, hour_bucket, index, float("nan")))
            order_id += 1
            index += 1
    return rows


def _row(order_id: int, scanner_type: str, hour_bucket: str, index: int, pick_minutes: float) -> dict:
    # store/basket_size cycle by a global position counter, independent of
    # which cell (and therefore which pass/fail/missing block) a row came
    # from - real, near-flat dimensions, not scripted ones.
    store = STORES[index % len(STORES)]
    basket_size = "small" if index % 2 == 0 else "large"
    # Exactly 100 of 400 orders (25%) contain a chilled item - every 4th
    # position, deterministic.
    contains_chilled = index % 4 == 0
    cold_pack_temp_c = CHILLED_TEMPS[index % len(CHILLED_TEMPS)] if contains_chilled else float("nan")
    # Exactly 120 of 400 orders (30%) used a real promo - 3 of every 10
    # positions, deterministic.
    promo_used = index % 10 < 3
    promo_code = PROMO_CODES[index % len(PROMO_CODES)] if promo_used else float("nan")
    return {
        "order_id": order_id,
        "scanner_type": scanner_type,
        "hour_bucket": hour_bucket,
        "store": store,
        "basket_size": basket_size,
        "contains_chilled": contains_chilled,
        "pick_minutes": pick_minutes,
        "cold_pack_temp_c": cold_pack_temp_c,
        "promo_code": promo_code,
    }


def generate_orders() -> Dataset:
    frame = pd.DataFrame(_rows())
    step = PipelineStep(
        "raw_export", python_code="orders = pd.read_csv('novamart_go_picking.csv')  # this period's Go orders"
    )
    return Dataset(name="orders", frame=frame, schema=RAW_SCHEMA, history=(step,))


def apply_round1(resolution: RepairResolution) -> Dataset:
    """Replays whatever the student actually picked for cold_pack_temp_c
    and promo_code against the real raw export - right or wrong. Every
    downstream stage works from this, never from a ground-truth
    substitute for what actually happened."""
    return apply_resolution(generate_orders(), ROUND1_ISSUES, resolution)


def apply_round2(round1_resolution: RepairResolution, round2_resolution: RepairResolution) -> Dataset:
    """Round 1's real result, with Round 2's real pick_minutes pick
    replayed on top of it."""
    return apply_resolution(apply_round1(round1_resolution), ROUND2_ISSUES, round2_resolution)


def missing_rate_by(dataset: Dataset, column: str) -> dict[str, float]:
    """Real missing_rate per distinct value of `column`, computed live
    from whatever dataset is passed in - never a hand-typed table. Powers
    the missingness-investigation stage's own SegmentSlicerScene content,
    so a decoy dimension's "nothing here" table is a real computation,
    not a scripted flat number."""
    frame = dataset.frame
    return {str(value): float(group["pick_minutes"].isna().mean()) for value, group in frame.groupby(column)}


def overall_missing_rate(dataset: Dataset) -> float:
    return float(dataset.frame["pick_minutes"].isna().mean())


def complete_case_rate(dataset: Dataset) -> float:
    """The naive, plausible-looking first attempt: drop every row without
    a captured pick_minutes, then read the SLA rate off what's left."""
    frame = dataset.frame
    observed = frame[frame["pick_minutes"].notna()]
    return float((observed["pick_minutes"] <= SLA_MINUTES).mean())


def sla_bounds(dataset: Dataset) -> tuple[float, float]:
    """The one real sensitivity computation this lesson needs: read
    whatever the current pick_minutes column actually holds, no ground-
    truth override. Lower bound assumes every still-missing row is a
    fail; upper bound assumes every still-missing row is a pass. If a
    treatment has already filled every gap (any fill-based RepairOption),
    there is nothing left missing - lower and upper collapse to the same
    single point, a real, honest mathematical consequence of imputation
    (erased uncertainty, not resolved uncertainty), not a special case
    this function has to detect."""
    frame = dataset.frame
    total = len(frame)
    observed_mask = frame["pick_minutes"].notna()
    observed_pass = int((frame.loc[observed_mask, "pick_minutes"] <= SLA_MINUTES).sum())
    missing_count = int((~observed_mask).sum())
    lower = observed_pass / total
    upper = (observed_pass + missing_count) / total
    return lower, upper


def complete_case_rate_python_code() -> str:
    return "complete = orders.dropna(subset=['pick_minutes'])\n(complete['pick_minutes'] <= 12).mean()"


def sla_lower_bound_python_code() -> str:
    return "observed_pass = (orders['pick_minutes'] <= 12).sum()\nlower_bound = observed_pass / len(orders)"


def sla_upper_bound_python_code() -> str:
    return (
        "observed_pass = (orders['pick_minutes'] <= 12).sum()\n"
        "still_missing = orders['pick_minutes'].isna().sum()\n"
        "upper_bound = (observed_pass + still_missing) / len(orders)"
    )


def _hidden_true_sla_rate() -> float:
    """Never called by any player-facing code or the scorer - internal-
    only, for confirming the constructed scenario's own consistency
    (does the true rate actually fall inside the honest sensitivity
    range, and below the 85% target) via a deterministic test."""
    observed_pass = sum(cell["obs_pass"] for cell in CELLS.values())
    true_pass_missing = sum(cell["true_pass_missing"] for cell in CELLS.values())
    total = sum(cell["obs_pass"] + cell["obs_fail"] + cell["missing"] for cell in CELLS.values())
    return (observed_pass + true_pass_missing) / total


# --- Round 1 repair issues: cold_pack_temp_c (structural / not-applicable)
# and promo_code (a null with real business meaning) - both discoverable
# immediately, declared and executed up front. ---


def _cold_pack_leave_as_missing(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(cold_pack_temp_c=frame["cold_pack_temp_c"])


def _cold_pack_impute_segment_average(frame: pd.DataFrame) -> pd.DataFrame:
    average = frame["cold_pack_temp_c"].mean()
    return frame.assign(cold_pack_temp_c=frame["cold_pack_temp_c"].fillna(average))


def _cold_pack_fill_zero(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(cold_pack_temp_c=frame["cold_pack_temp_c"].fillna(0.0))


def _cold_pack_drop_missing(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.dropna(subset=["cold_pack_temp_c"]).reset_index(drop=True)


def _promo_recode_no_promo(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(promo_code=frame["promo_code"].fillna("NO_PROMO"))


def _promo_drop_missing(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.dropna(subset=["promo_code"]).reset_index(drop=True)


def _promo_leave_as_nan(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(promo_code=frame["promo_code"])


COLD_PACK_ISSUE = RepairIssue(
    column="cold_pack_temp_c",
    prompt_key="lesson.l07.issue.cold_pack_temp_c.prompt",
    hint_key="lesson.l07.issue.cold_pack_temp_c.hint",
    evidence_key="lesson.l07.issue.cold_pack_temp_c.evidence",
    options=(
        RepairOption(
            "leave_as_missing",
            "lesson.l07.option.cold_pack_temp_c.leave_as_missing",
            _cold_pack_leave_as_missing,
            python_code="# left as-is - not applicable for ambient-only orders, never imputed",
            result_description_key="lesson.l07.schema.cold_pack_temp_c.description_fixed",
        ),
        RepairOption(
            "impute_segment_average",
            "lesson.l07.option.cold_pack_temp_c.impute_segment_average",
            _cold_pack_impute_segment_average,
            python_code="orders['cold_pack_temp_c'] = orders['cold_pack_temp_c'].fillna(orders['cold_pack_temp_c'].mean())",
            result_nullable=False,
            result_description_key="lesson.l07.schema.cold_pack_temp_c.description_fabricated_average",
        ),
        RepairOption(
            "fill_zero_c",
            "lesson.l07.option.cold_pack_temp_c.fill_zero_c",
            _cold_pack_fill_zero,
            python_code="orders['cold_pack_temp_c'] = orders['cold_pack_temp_c'].fillna(0.0)",
            result_nullable=False,
            result_description_key="lesson.l07.schema.cold_pack_temp_c.description_fabricated_zero",
        ),
        RepairOption(
            "drop_missing_cold_pack",
            "lesson.l07.option.cold_pack_temp_c.drop_missing_cold_pack",
            _cold_pack_drop_missing,
            python_code="orders = orders.dropna(subset=['cold_pack_temp_c'])",
            result_nullable=False,
            result_description_key="lesson.l07.schema.cold_pack_temp_c.description_dropped",
        ),
    ),
)

PROMO_CODE_ISSUE = RepairIssue(
    column="promo_code",
    prompt_key="lesson.l07.issue.promo_code.prompt",
    hint_key="lesson.l07.issue.promo_code.hint",
    evidence_key="lesson.l07.issue.promo_code.evidence",
    options=(
        RepairOption(
            "recode_no_promo",
            "lesson.l07.option.promo_code.recode_no_promo",
            _promo_recode_no_promo,
            python_code="orders['promo_code'] = orders['promo_code'].fillna('NO_PROMO')",
            result_nullable=False,
            result_description_key="lesson.l07.schema.promo_code.description_fixed",
        ),
        RepairOption(
            "drop_missing_promo",
            "lesson.l07.option.promo_code.drop_missing_promo",
            _promo_drop_missing,
            python_code="orders = orders.dropna(subset=['promo_code'])",
            result_nullable=False,
            result_description_key="lesson.l07.schema.promo_code.description_dropped",
        ),
        RepairOption(
            "leave_as_nan",
            "lesson.l07.option.promo_code.leave_as_nan",
            _promo_leave_as_nan,
            python_code="# left as NaN - not recoded to an explicit category",
        ),
    ),
)

ROUND1_ISSUES: tuple[RepairIssue, ...] = (COLD_PACK_ISSUE, PROMO_CODE_ISSUE)


# --- Round 2 repair issue: pick_minutes, declared and executed only after
# the investigation - the lesson's own central, twist-bearing problem. ---


def _pick_preserve_and_report(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(pick_minutes=frame["pick_minutes"])


def _pick_fill_global_median(frame: pd.DataFrame) -> pd.DataFrame:
    median = frame["pick_minutes"].median()
    return frame.assign(pick_minutes=frame["pick_minutes"].fillna(median))


def _pick_fill_group_median(frame: pd.DataFrame) -> pd.DataFrame:
    group_median = frame.groupby(["scanner_type", "hour_bucket"])["pick_minutes"].transform("median")
    return frame.assign(pick_minutes=frame["pick_minutes"].fillna(group_median))


def _pick_fill_zero(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(pick_minutes=frame["pick_minutes"].fillna(0.0))


PICK_MINUTES_ISSUE = RepairIssue(
    column="pick_minutes",
    prompt_key="lesson.l07.issue.pick_minutes.prompt",
    hint_key="lesson.l07.issue.pick_minutes.hint",
    evidence_key="lesson.l07.issue.pick_minutes.evidence",
    options=(
        RepairOption(
            "preserve_and_report",
            "lesson.l07.option.pick_minutes.preserve_and_report",
            _pick_preserve_and_report,
            python_code="orders['pick_minutes_missing'] = orders['pick_minutes'].isna()  # kept missing, reported as a range",
            result_description_key="lesson.l07.schema.pick_minutes.description_preserved",
        ),
        RepairOption(
            "fill_global_median",
            "lesson.l07.option.pick_minutes.fill_global_median",
            _pick_fill_global_median,
            python_code="orders['pick_minutes'] = orders['pick_minutes'].fillna(orders['pick_minutes'].median())",
            result_nullable=False,
            result_description_key="lesson.l07.schema.pick_minutes.description_global_median",
        ),
        RepairOption(
            "fill_group_median",
            "lesson.l07.option.pick_minutes.fill_group_median",
            _pick_fill_group_median,
            python_code=(
                "group_median = orders.groupby(['scanner_type', 'hour_bucket'])['pick_minutes'].transform('median')\n"
                "orders['pick_minutes'] = orders['pick_minutes'].fillna(group_median)"
            ),
            result_nullable=False,
            result_description_key="lesson.l07.schema.pick_minutes.description_group_median",
        ),
        RepairOption(
            "fill_zero",
            "lesson.l07.option.pick_minutes.fill_zero",
            _pick_fill_zero,
            python_code="orders['pick_minutes'] = orders['pick_minutes'].fillna(0.0)",
            result_nullable=False,
            result_description_key="lesson.l07.schema.pick_minutes.description_zero",
        ),
    ),
)

ROUND2_ISSUES: tuple[RepairIssue, ...] = (PICK_MINUTES_ISSUE,)

CORRECT_TREATMENT: dict[str, frozenset[str]] = {
    "cold_pack_temp_c": frozenset({"leave_as_missing"}),
    "promo_code": frozenset({"recode_no_promo"}),
    "pick_minutes": frozenset({"preserve_and_report"}),
}
"""The one objectively correct executed treatment for each real column -
shared by the scorer (REPRODUCIBILITY) and, in principle, by anything
that needs to check a student's own real final pick against it."""


# --- Optional mastery: a new, small inventory/restocking export - a
# different mechanism, transfer not repetition. ---

MASTERY_SCHEMA = Schema(
    columns=(
        ColumnSchema("sku", "object"),
        ColumnSchema(
            "restock_date", "object", nullable=True, description_key="lesson.l07.mastery.schema.restock_date.description"
        ),
        ColumnSchema(
            "supplier_lead_days",
            "float64",
            nullable=True,
            description_key="lesson.l07.mastery.schema.supplier_lead_days.description",
        ),
        ColumnSchema("warehouse_zone", "object", description_key="lesson.l07.mastery.schema.warehouse_zone.description"),
        ColumnSchema(
            "unit_cost", "float64", nullable=True, description_key="lesson.l07.mastery.schema.unit_cost.description"
        ),
    )
)

_MASTERY_ROWS = [
    ("SKU-1001", None, 5.0, "north", 12.50),
    ("SKU-1002", "2026-08-14", 7.0, "south", 8.75),
    ("SKU-1003", None, None, "north", 14.00),
    ("SKU-1004", "2026-07-30", 6.0, "south", 9.20),
    ("SKU-1005", None, 5.5, "east", 11.10),
    ("SKU-1006", "2026-08-02", 6.5, "west", 6.40),
]
"""restock_date is missing exactly when an item has never been restocked
yet (structural, not a data-quality problem) - 3 of 6 rows here.
supplier_lead_days has one genuine, real measurement loss (row 3 - a
lead-time record that should exist and doesn't). warehouse_zone is fully
populated (nothing to flag). unit_cost's one real gap (row 3 again) is
small, low-rate, and unpatterned - present specifically so the student
sees that not every missingness situation calls for a dramatic
block-the-decision response."""

MASTERY_CORRECT: frozenset[str] = frozenset({"supplier_lead_days"})
"""restock_date's own gap is structural, not a fix candidate. unit_cost's
one real gap is real but low-rate and unpatterned - not the same class
of problem pick_minutes was. warehouse_zone has no missingness at all.
Only supplier_lead_days is a genuine, real measurement loss that needs
real follow-up before use - the same distinction the core lesson taught,
applied to a mechanism that isn't the legacy-scanner story again."""


def generate_mastery_export() -> Dataset:
    frame = pd.DataFrame(
        _MASTERY_ROWS, columns=["sku", "restock_date", "supplier_lead_days", "warehouse_zone", "unit_cost"]
    )
    step = PipelineStep("mastery_export", python_code="inventory = pd.read_csv('novamart_go_inventory.csv')")
    return Dataset(name="inventory", frame=frame, schema=MASTERY_SCHEMA, history=(step,))
