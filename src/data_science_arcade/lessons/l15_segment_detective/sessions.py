import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Ground truth (hand-verified, hand-picked - not randomized) -----------
#
# One real, deterministic 2000-session NovaMart Go checkout feed, a genuine
# Simpson reversal: the blended checkout-completion rate rises Q1 -> Q2
# while BOTH device segments' own rates fall, because the population
# shifted hard toward the higher-converting device (mobile).
#
#   device    Q1 sessions / conv / rate     Q2 sessions / conv / rate
#   mobile    200 / 84  / 42.0%             700 / 266 / 38.0%
#   desktop   800 / 200 / 25.0%             300 / 66  / 22.0%
#   overall  1000 / 284 / 28.4%            1000 / 332 / 33.2%
#
# Device mix: mobile 20% -> 70%, desktop 80% -> 30%. Real deltas: overall
# +4.8pp, mobile -4.0pp, desktop -3.0pp - a real reversal, not a rounding
# artifact (hand-verified twice via a real pandas script).
#
# `region` is a real, exactly neutral first slice: a deterministic 50/50
# split inside every one of the 8 real (period, device, converted) cells
# (all 8 counts are even, so the split has zero rounding drift). Both EU
# and US independently reproduce the exact 28.4% -> 33.2% overall move,
# and the region mix stays exactly 50/50 both periods - region simply
# doesn't explain the reversal, and that's only knowable by looking.

STORE_METRIC_LABEL = "checkout completion rate"

Q1_MOBILE_SESSIONS = 200
Q1_MOBILE_CONVERSIONS = 84
Q1_DESKTOP_SESSIONS = 800
Q1_DESKTOP_CONVERSIONS = 200

Q2_MOBILE_SESSIONS = 700
Q2_MOBILE_CONVERSIONS = 266
Q2_DESKTOP_SESSIONS = 300
Q2_DESKTOP_CONVERSIONS = 66

TOTAL_SESSIONS = 2000
SESSIONS_PER_PERIOD = 1000

PERIODS: tuple[str, ...] = ("Q1", "Q2")
DEVICES: tuple[str, ...] = ("mobile", "desktop")
REGIONS: tuple[str, ...] = ("EU", "US")

SESSIONS_SCHEMA = Schema(
    columns=(
        ColumnSchema("session_id", "object"),
        ColumnSchema("period", "object"),
        ColumnSchema("device", "object"),
        ColumnSchema("region", "object"),
        ColumnSchema("converted", "bool"),
    )
)

_CELL_SPEC: dict[tuple[str, str], tuple[int, int]] = {
    ("Q1", "mobile"): (Q1_MOBILE_SESSIONS, Q1_MOBILE_CONVERSIONS),
    ("Q1", "desktop"): (Q1_DESKTOP_SESSIONS, Q1_DESKTOP_CONVERSIONS),
    ("Q2", "mobile"): (Q2_MOBILE_SESSIONS, Q2_MOBILE_CONVERSIONS),
    ("Q2", "desktop"): (Q2_DESKTOP_SESSIONS, Q2_DESKTOP_CONVERSIONS),
}


def _rows() -> list[tuple[str, str, str, bool]]:
    rows: list[tuple[str, str, str, bool]] = []
    session_index = 0
    for period in PERIODS:
        for device in DEVICES:
            sessions, conversions = _CELL_SPEC[(period, device)]
            for converted in (True, False):
                count = conversions if converted else sessions - conversions
                half = count // 2
                assert half * 2 == count, f"({period}, {device}, converted={converted}) cell isn't evenly splittable: {count}"
                for i in range(count):
                    region = "EU" if i < half else "US"
                    session_id = f"S-{session_index + 1:04d}"
                    rows.append((session_id, period, device, region, converted))
                    session_index += 1
    return rows


def generate_sessions() -> Dataset:
    """The player-facing session-level feed - real, clean, no data-quality
    issues (this is a composition-vs-behavior lesson, not a cleaning one).
    No hidden truth: every column here is directly visible and real."""
    frame = pd.DataFrame(_rows(), columns=["session_id", "period", "device", "region", "converted"])
    step = PipelineStep("collected", python_code="sessions = pd.read_csv('novamart_go_sessions.csv')")
    return Dataset(name="sessions", frame=frame, schema=SESSIONS_SCHEMA, history=(step,))


def rate_pct(sessions: int, conversions: int) -> float:
    return 100.0 * conversions / sessions


# --- Real, hand-verified constants used by both the scenario and its tests

OVERALL_RATE_PCT: dict[str, float] = {
    "Q1": rate_pct(SESSIONS_PER_PERIOD, Q1_MOBILE_CONVERSIONS + Q1_DESKTOP_CONVERSIONS),
    "Q2": rate_pct(SESSIONS_PER_PERIOD, Q2_MOBILE_CONVERSIONS + Q2_DESKTOP_CONVERSIONS),
}
DEVICE_RATE_PCT: dict[str, dict[str, float]] = {
    "Q1": {"mobile": rate_pct(Q1_MOBILE_SESSIONS, Q1_MOBILE_CONVERSIONS), "desktop": rate_pct(Q1_DESKTOP_SESSIONS, Q1_DESKTOP_CONVERSIONS)},
    "Q2": {"mobile": rate_pct(Q2_MOBILE_SESSIONS, Q2_MOBILE_CONVERSIONS), "desktop": rate_pct(Q2_DESKTOP_SESSIONS, Q2_DESKTOP_CONVERSIONS)},
}
DEVICE_SHARE_PCT: dict[str, dict[str, float]] = {
    "Q1": {"mobile": rate_pct(SESSIONS_PER_PERIOD, Q1_MOBILE_SESSIONS), "desktop": rate_pct(SESSIONS_PER_PERIOD, Q1_DESKTOP_SESSIONS)},
    "Q2": {"mobile": rate_pct(SESSIONS_PER_PERIOD, Q2_MOBILE_SESSIONS), "desktop": rate_pct(SESSIONS_PER_PERIOD, Q2_DESKTOP_SESSIONS)},
}
REGION_RATE_PCT: dict[str, dict[str, float]] = {period: {"EU": OVERALL_RATE_PCT[period], "US": OVERALL_RATE_PCT[period]} for period in PERIODS}
REGION_SHARE_PCT: dict[str, dict[str, float]] = {period: {"EU": 50.0, "US": 50.0} for period in PERIODS}

# Q2's own within-device rates, weighted by Q1's own device mix - real
# descriptive reweighting/standardization, never a causal estimate.
Q2_AT_Q1_MIX_PCT = (Q1_DESKTOP_SESSIONS / SESSIONS_PER_PERIOD) * DEVICE_RATE_PCT["Q2"]["desktop"] + (
    Q1_MOBILE_SESSIONS / SESSIONS_PER_PERIOD
) * DEVICE_RATE_PCT["Q2"]["mobile"]

# --- Optional mastery - a different domain: fulfillment on-time delivery --
#
# In-house vs. third-party courier, Q1 -> Q2 - a real NON-reversal: both
# segments improve AND the overall improves, but the mix shifted toward
# the weaker-but-improving third-party courier, shrinking the overall
# improvement without reversing its direction. Hand-verified: in-house
# 90%->94% (+4pp), third-party 70%->78% (+8pp), overall 82.0%->82.8%
# (+0.8pp, much smaller than either segment's own real gain).

MASTERY_Q1_IN_HOUSE_SESSIONS = 600
MASTERY_Q1_IN_HOUSE_ON_TIME = 540
MASTERY_Q1_THIRD_PARTY_SESSIONS = 400
MASTERY_Q1_THIRD_PARTY_ON_TIME = 280
MASTERY_Q2_IN_HOUSE_SESSIONS = 300
MASTERY_Q2_IN_HOUSE_ON_TIME = 282
MASTERY_Q2_THIRD_PARTY_SESSIONS = 700
MASTERY_Q2_THIRD_PARTY_ON_TIME = 546

MASTERY_OVERALL_PCT = {
    "Q1": rate_pct(1000, MASTERY_Q1_IN_HOUSE_ON_TIME + MASTERY_Q1_THIRD_PARTY_ON_TIME),
    "Q2": rate_pct(1000, MASTERY_Q2_IN_HOUSE_ON_TIME + MASTERY_Q2_THIRD_PARTY_ON_TIME),
}
MASTERY_CARRIER_PCT = {
    "Q1": {
        "in_house": rate_pct(MASTERY_Q1_IN_HOUSE_SESSIONS, MASTERY_Q1_IN_HOUSE_ON_TIME),
        "third_party": rate_pct(MASTERY_Q1_THIRD_PARTY_SESSIONS, MASTERY_Q1_THIRD_PARTY_ON_TIME),
    },
    "Q2": {
        "in_house": rate_pct(MASTERY_Q2_IN_HOUSE_SESSIONS, MASTERY_Q2_IN_HOUSE_ON_TIME),
        "third_party": rate_pct(MASTERY_Q2_THIRD_PARTY_SESSIONS, MASTERY_Q2_THIRD_PARTY_ON_TIME),
    },
}
MASTERY_CARRIER_SHARE_PCT = {
    "Q1": {"in_house": 60.0, "third_party": 40.0},
    "Q2": {"in_house": 30.0, "third_party": 70.0},
}
