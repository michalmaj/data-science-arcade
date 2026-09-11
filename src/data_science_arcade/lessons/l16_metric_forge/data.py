import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Ground truth (hand-verified via a real pandas script, deterministic -
# no RNG anywhere in this module) ------------------------------------------
#
# One real 500-ticket NovaMart Support population, ticket-level grain
# (`ticket_id`), reused unmodified across every beat of this lesson rather
# than three separate mini-datasets. Difficulty is interleaved 35:6:9 per
# 50-ticket block (never a contiguous run) so it never correlates with
# ticket age - the same "no unintended block structure" discipline L14's
# own follow-up had to retrofit, applied here from the start.
#
#   difficulty    count   honest close delay
#   easy          350     2-5h (2h + (i%4)*1h)
#   quick_hard    60      20h
#   slow_hard     90      120h (5 days)
#
# Honest, full-maturity baseline (as_of = last_open + 30 days): every
# definition of "resolution rate" agrees at 82.0% (410/500 tickets close
# within 24h - the 90 slow_hard tickets never do), reopen rate 0.0%, aged
# backlog 0. This is the real, structural reason 82.0% recurs throughout:
# it's exactly (350 easy + 60 quick_hard) / 500.
#
# Honest, EARLY snapshot (as_of = last_open + 24h, most tickets closed but
# not all) - the "same metric name, different real number, zero gaming"
# beat: Definition A (eligible-population denominator) = 82.0%,
# Definition B (closed-only denominator) = 86.7%, durable resolution rate
# (mature cohort only, n=327) = 83.5%. Nobody's lying; B's own denominator
# just quietly excludes whatever hasn't closed yet.
#
# Two real, independently re-simulated stress tests, both starting from
# the SAME honest population and modifying the SAME 70-ticket subset of
# the 90 real slow_hard tickets - alternative pressure scenarios, never a
# shared timeline (stress test 2 does not happen "after" stress test 1).
#
#   Stress Test A - Close Fast (numerator/event gaming): those 70 tickets
#   are rushed closed at +20h instead of +120h, without being durably
#   fixed; 56 of the 70 (80%) genuinely reopen 3 days later. Both
#   Definition A and B read 96.0% (the denominator stops mattering once
#   nothing is left open) - durable resolution barely moves (82.0% ->
#   84.8%) while reopen rate is the real signal (0.0% -> 11.2%).
#
#   Stress Test B - Leave Hard Tickets Open (denominator/selection
#   gaming): those same 70 tickets are instead left open indefinitely
#   (never closed). Definition A stays exactly 82.0% - structurally
#   immune, since its denominator counts every opened ticket regardless of
#   closure state. Definition B jumps to a fake 95.3% while aged backlog
#   grows from 0 to 14.0% (70 tickets) - the real guardrail this loophole
#   needs.
#
# Durable resolution rate (Definition A's own population denominator,
# restricted to the mature cohort, requiring 24h close AND no reopen
# within 7 days) resists BOTH: 84.8% under Stress Test A (a real, small
# +2.8pp move, not the headline's fake +14pp) and 82.0% (flat) under
# Stress Test B.

N_TICKETS = 500
BLOCK_SIZE = 50
EASY_PER_BLOCK = 35
QUICK_HARD_PER_BLOCK = 6
SLOW_HARD_PER_BLOCK = 9
assert EASY_PER_BLOCK + QUICK_HARD_PER_BLOCK + SLOW_HARD_PER_BLOCK == BLOCK_SIZE

SPACING_MINUTES = 50
QUICK_HARD_HONEST_DELAY = pd.Timedelta(hours=20)
SLOW_HARD_HONEST_DELAY = pd.Timedelta(hours=120)
EASY_DELAY_BASE = pd.Timedelta(hours=2)
EASY_DELAY_STEP = pd.Timedelta(hours=1)

STRESS_SUBSET_SIZE = 70
STRESS_A_REOPEN_COUNT = 56  # 80% of the 70-ticket subset
STRESS_A_REOPEN_DELAY = pd.Timedelta(days=3)

MATURITY_WINDOW = pd.Timedelta(days=7)
RESOLUTION_WINDOW = pd.Timedelta(hours=24)

TICKETS_SCHEMA = Schema(
    columns=(
        ColumnSchema("ticket_id", "object"),
        ColumnSchema("opened_at", "datetime64[ns]"),
        ColumnSchema("closed_at", "datetime64[ns]", nullable=True, description_key="lesson.l16.schema.closed_at"),
        ColumnSchema("reopened_at", "datetime64[ns]", nullable=True, description_key="lesson.l16.schema.reopened_at"),
    )
)


def _difficulty_for(index: int) -> str:
    position = index % BLOCK_SIZE
    if position < EASY_PER_BLOCK:
        return "easy"
    if position < EASY_PER_BLOCK + QUICK_HARD_PER_BLOCK:
        return "quick_hard"
    return "slow_hard"


def _honest_ticket_rows() -> list[dict]:
    opened_at = pd.date_range("2024-01-01", periods=N_TICKETS, freq=f"{SPACING_MINUTES}min")
    rows = []
    for i in range(N_TICKETS):
        difficulty = _difficulty_for(i)
        opened = opened_at[i]
        if difficulty == "easy":
            closed = opened + EASY_DELAY_BASE + (i % 4) * EASY_DELAY_STEP
        elif difficulty == "quick_hard":
            closed = opened + QUICK_HARD_HONEST_DELAY
        else:
            closed = opened + SLOW_HARD_HONEST_DELAY
        rows.append(
            {"ticket_id": f"T-{i + 1:04d}", "difficulty": difficulty, "opened_at": opened, "closed_at": closed, "reopened_at": pd.NaT}
        )
    return rows


def _honest_frame() -> pd.DataFrame:
    return pd.DataFrame(_honest_ticket_rows())


def _stress_subset_ids(frame: pd.DataFrame) -> list[str]:
    """The same real 70-ticket subset both stress tests independently
    re-simulate from - the first 70 (by generation order) of the 90 real
    slow_hard tickets."""
    return frame.loc[frame["difficulty"] == "slow_hard", "ticket_id"].tolist()[:STRESS_SUBSET_SIZE]


def honest_tickets() -> pd.DataFrame:
    """The real honest population - no manipulation, no schema's own
    hidden `difficulty` column (dropped before this is player-facing;
    kept internally only to build the deterministic honest delays)."""
    return _honest_frame().drop(columns=["difficulty"])


def apply_stress_test_a(frame: pd.DataFrame) -> pd.DataFrame:
    """Stress Test A - Close Fast: the real 70-ticket subset is rushed
    closed at the same delay quick_hard tickets honestly use (20h),
    without being durably fixed - 56 of the 70 (80%) genuinely reopen 3
    days after their own rushed close."""
    subset_ids = _stress_subset_ids(_honest_frame())
    result = frame.copy()
    for i, ticket_id in enumerate(subset_ids):
        row_index = result.index[result["ticket_id"] == ticket_id][0]
        opened = result.at[row_index, "opened_at"]
        rushed_close = opened + QUICK_HARD_HONEST_DELAY
        result.at[row_index, "closed_at"] = rushed_close
        if i < STRESS_A_REOPEN_COUNT:
            result.at[row_index, "reopened_at"] = rushed_close + STRESS_A_REOPEN_DELAY
    return result


def apply_stress_test_b(frame: pd.DataFrame) -> pd.DataFrame:
    """Stress Test B - Leave Hard Tickets Open: the SAME real 70-ticket
    subset (an independent re-simulation from the same honest baseline,
    not a continuation of Stress Test A) is instead left open
    indefinitely - never closed, never reopened."""
    subset_ids = _stress_subset_ids(_honest_frame())
    result = frame.copy()
    for ticket_id in subset_ids:
        row_index = result.index[result["ticket_id"] == ticket_id][0]
        result.at[row_index, "closed_at"] = pd.NaT
    return result


def generate_tickets() -> Dataset:
    """The player-facing raw ticket feed - real, clean, no data-quality
    issues (this is a metric-definition lesson, not a cleaning one)."""
    frame = honest_tickets()
    step = PipelineStep("collected", python_code="tickets = pd.read_csv('novamart_support_tickets.csv', parse_dates=['opened_at', 'closed_at', 'reopened_at'])")
    return Dataset(name="tickets", frame=frame, schema=TICKETS_SCHEMA, history=(step,))


def last_open(frame: pd.DataFrame) -> pd.Timestamp:
    return frame["opened_at"].max()


def early_snapshot(frame: pd.DataFrame) -> pd.Timestamp:
    return last_open(frame) + pd.Timedelta(hours=24)


def mature_snapshot(frame: pd.DataFrame) -> pd.Timestamp:
    return last_open(frame) + pd.Timedelta(days=30)


# --- Real metric definitions - every one operates on the raw frame plus a
# single `as_of` timestamp, matching exactly what the Python Mirror shows. -


def _closed_by_asof(frame: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    return frame["closed_at"].notna() & (frame["closed_at"] <= as_of)


def _opened_by_asof(frame: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    return frame["opened_at"] <= as_of


def _resolved_within_24h(frame: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    return _closed_by_asof(frame, as_of) & ((frame["closed_at"] - frame["opened_at"]) <= RESOLUTION_WINDOW)


def definition_a_rate(frame: pd.DataFrame, as_of: pd.Timestamp) -> float:
    """Eligible-population denominator: every ticket opened by `as_of`,
    whether it has closed yet or not - structurally immune to denominator
    gaming, since leaving a ticket open can't shrink it out of the count."""
    opened = _opened_by_asof(frame, as_of)
    return float(_resolved_within_24h(frame, as_of)[opened].mean())


def definition_b_rate(frame: pd.DataFrame, as_of: pd.Timestamp) -> float:
    """Closed-only denominator: only tickets that have already closed -
    real and defensible, but a ticket left open simply drops out of the
    count entirely instead of counting against the rate."""
    closed = _closed_by_asof(frame, as_of)
    if not closed.any():
        return float("nan")
    return float(_resolved_within_24h(frame, as_of)[closed].mean())


def mature_mask(frame: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    """A ticket is eligible for durable-resolution evaluation once it has
    been open at least 7 days before `as_of` - old enough to have had its
    real reopen window elapse. An immature ticket is neither a durable
    success nor a durable failure yet; it simply isn't counted."""
    return _opened_by_asof(frame, as_of) & (frame["opened_at"] <= as_of - MATURITY_WINDOW)


def _reopened_within_window(frame: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    return frame["reopened_at"].notna() & (frame["reopened_at"] <= as_of) & ((frame["reopened_at"] - frame["closed_at"]) <= MATURITY_WINDOW)


def durable_resolution_rate(frame: pd.DataFrame, as_of: pd.Timestamp) -> float:
    """Definition A's own denominator, restricted to the mature cohort,
    requiring 24h close AND no reopen within the 7-day window - the one
    real candidate that resists both stress tests."""
    mature = mature_mask(frame, as_of)
    if not mature.any():
        return float("nan")
    durable = _resolved_within_24h(frame, as_of) & ~_reopened_within_window(frame, as_of)
    return float(durable[mature].mean())


def reopen_rate(frame: pd.DataFrame, as_of: pd.Timestamp) -> float:
    closed = _closed_by_asof(frame, as_of)
    if not closed.any():
        return float("nan")
    return float(_reopened_within_window(frame, as_of)[closed].mean())


def aged_backlog_rate(frame: pd.DataFrame, as_of: pd.Timestamp) -> float:
    opened = _opened_by_asof(frame, as_of)
    return float((~_closed_by_asof(frame, as_of))[opened].mean())


# --- Optional mastery - a different domain: NovaMart Logistics picker
# productivity. Real, row-level, hand-verified via script: 300 real
# tracked orders (3 small items @ 90s + 1 bulky item @ 240s each) plus an
# 800-order small-only backlog. Honest picking (every item, every order)
# spends 42.5 real labor-hours on 1200 items = 28.2 items/hour, 100% of
# the 300 tracked orders complete. Narrow optimization - skipping every
# bulky item and spending the freed-up time on backlog small items instead
# - spends the SAME 42.5 labor-hours on 1700 items = 40.0 items/hour, a
# real, large throughput increase, while all 300 tracked orders end up
# missing their one bulky item: 0% complete.

MASTERY_TRACKED_ORDERS = 300
MASTERY_SMALL_PER_ORDER = 3
MASTERY_BULKY_PER_ORDER = 1
MASTERY_SMALL_SECONDS = 90
MASTERY_BULKY_SECONDS = 240
MASTERY_BACKLOG_ORDERS = 800

PICKS_SCHEMA = Schema(
    columns=(
        ColumnSchema("order_id", "object"),
        ColumnSchema("item_id", "object"),
        ColumnSchema("category", "object"),
        ColumnSchema("seconds", "int64"),
        ColumnSchema("picked", "bool"),
    )
)


def _mastery_tracked_rows(bulky_picked: bool) -> list[dict]:
    rows = []
    for i in range(MASTERY_TRACKED_ORDERS):
        order_id = f"O-{i + 1:04d}"
        for s in range(MASTERY_SMALL_PER_ORDER):
            rows.append(
                {"order_id": order_id, "item_id": f"{order_id}-S{s + 1}", "category": "small", "seconds": MASTERY_SMALL_SECONDS, "picked": True}
            )
        rows.append(
            {"order_id": order_id, "item_id": f"{order_id}-B1", "category": "bulky", "seconds": MASTERY_BULKY_SECONDS, "picked": bulky_picked}
        )
    return rows


def generate_honest_picks() -> pd.DataFrame:
    return pd.DataFrame(_mastery_tracked_rows(bulky_picked=True))


def generate_narrow_picks() -> pd.DataFrame:
    rows = _mastery_tracked_rows(bulky_picked=False)
    for i in range(MASTERY_BACKLOG_ORDERS):
        order_id = f"BL-{i + 1:04d}"
        rows.append({"order_id": order_id, "item_id": f"{order_id}-S1", "category": "small", "seconds": MASTERY_SMALL_SECONDS, "picked": True})
    return pd.DataFrame(rows)


def picks_per_hour(frame: pd.DataFrame) -> float:
    picked = frame[frame["picked"]]
    labor_hours = picked["seconds"].sum() / 3600
    return float(len(picked) / labor_hours)


def tracked_order_completeness_pct(frame: pd.DataFrame) -> float:
    tracked = frame[frame["order_id"].str.startswith("O-")]
    per_order = tracked.groupby("order_id")["picked"].all()
    return float(per_order.mean() * 100)
