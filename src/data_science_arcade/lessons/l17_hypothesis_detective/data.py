import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Ground truth (hand-verified via a real pandas script, deterministic -
# no RNG anywhere in this module) ------------------------------------------
#
# One real 1200-customer NovaMart one-click reorder pilot. Grain: one row
# per customer (`customer_id`, `variant`, `device`, `repeat_purchase_14d`).
# The metric contract is GIVEN from L16, not redesigned here: 14-day repeat
# purchase rate among eligible returning customers.
#
# Primary (variant x repeat_purchase_14d): control 150/600 = 25.0%,
# one_click 156/600 = 26.0% - a real, observed +1.0pp difference in the
# pre-specified direction. Never called "significant" or "proved" - that's
# L19/L20 territory.
#
# Device composition is IDENTICAL in both variants (360 app / 240 web, a
# real 60/40 split both sides, by construction) - deliberately unlike L15's
# own composition-confound story. Exploratory device split (real, only
# discovered by slicing after the primary result was already visible):
# app control 120/360=33.3%, one_click 144/360=40.0% (+6.7pp); web control
# 30/240=12.5%, one_click 12/240=5.0% (-7.5pp). Sums reconcile exactly
# (120+30=150, 144+12=156). A real, observed variant difference by device -
# never called a "treatment effect" here; L18 sets up random assignment,
# L19 uncertainty/power, L20 the experiment decision - this lesson's own
# job is only pre-specification discipline.

N_CUSTOMERS_PER_VARIANT = 600
APP_PER_VARIANT = 360
WEB_PER_VARIANT = 240
assert APP_PER_VARIANT + WEB_PER_VARIANT == N_CUSTOMERS_PER_VARIANT

CONTROL_APP_REPEAT = 120
CONTROL_WEB_REPEAT = 30
ONE_CLICK_APP_REPEAT = 144
ONE_CLICK_WEB_REPEAT = 12

PILOT_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "object"),
        ColumnSchema("variant", "object", description="'control' or 'one_click'"),
        ColumnSchema("device", "object", description="'app' or 'web'"),
        ColumnSchema("repeat_purchase_14d", "bool"),
    )
)


def _variant_rows(variant: str, n_app_repeat: int, n_web_repeat: int, start_id: int) -> tuple[list[dict], int]:
    rows: list[dict] = []
    customer_id = start_id
    for i in range(APP_PER_VARIANT):
        rows.append(
            {"customer_id": f"C-{customer_id:04d}", "variant": variant, "device": "app", "repeat_purchase_14d": i < n_app_repeat}
        )
        customer_id += 1
    for i in range(WEB_PER_VARIANT):
        rows.append(
            {"customer_id": f"C-{customer_id:04d}", "variant": variant, "device": "web", "repeat_purchase_14d": i < n_web_repeat}
        )
        customer_id += 1
    return rows, customer_id


def _pilot_rows() -> list[dict]:
    rows, next_id = _variant_rows("control", CONTROL_APP_REPEAT, CONTROL_WEB_REPEAT, 1)
    more_rows, _ = _variant_rows("one_click", ONE_CLICK_APP_REPEAT, ONE_CLICK_WEB_REPEAT, next_id)
    return rows + more_rows


def generate_pilot() -> Dataset:
    """The player-facing pilot feed - real, clean, no data-quality issues
    (this is a pre-specification lesson, not a cleaning one). Assignment
    is taken as validly supplied throughout this lesson - L18 is where
    random assignment itself gets examined."""
    frame = pd.DataFrame(_pilot_rows())
    step = PipelineStep("collected", python_code="pilot = pd.read_csv('novamart_one_click_pilot.csv')")
    return Dataset(name="pilot", frame=frame, schema=PILOT_SCHEMA, history=(step,))


def primary_rate(frame: pd.DataFrame, variant: str) -> float:
    return float(frame.loc[frame["variant"] == variant, "repeat_purchase_14d"].mean())


def device_rate(frame: pd.DataFrame, device: str, variant: str) -> float:
    rows = frame[(frame["device"] == device) & (frame["variant"] == variant)]
    return float(rows["repeat_purchase_14d"].mean())


# --- Optional mastery - a different domain: NovaMart Logistics route
# planner. Real, row-level, hand-verified via script: 2000 deliveries total
# across 2 periods (before/after), 600 urban / 400 rural per period,
# identical composition both periods. Pre-specified hypothesis: the new
# route planner reduces the overall late-delivery rate. Honest result:
# overall late rate 10.0% -> 10.5% (a real, small increase - the
# hypothesis is NOT borne out). Post-hoc: urban late rate 15.0% -> 10.0%
# (-5.0pp, a real observed improvement - never called "the route planner
# worked in cities," only "the observed late rate improved"); rural late
# rate 2.5% -> 11.25% (+8.75pp, a real observed deterioration). Sums
# reconcile exactly (90+10=100 before, 60+45=105 after).

MASTERY_URBAN_PER_PERIOD = 600
MASTERY_RURAL_PER_PERIOD = 400
MASTERY_BEFORE_URBAN_LATE = 90
MASTERY_BEFORE_RURAL_LATE = 10
MASTERY_AFTER_URBAN_LATE = 60
MASTERY_AFTER_RURAL_LATE = 45

DELIVERIES_SCHEMA = Schema(
    columns=(
        ColumnSchema("delivery_id", "object"),
        ColumnSchema("period", "object", description="'before' or 'after' the new route planner shipped"),
        ColumnSchema("route_type", "object", description="'urban' or 'rural'"),
        ColumnSchema("late", "bool"),
    )
)


def _delivery_rows(period: str, n_urban_late: int, n_rural_late: int, start_id: int) -> tuple[list[dict], int]:
    rows: list[dict] = []
    delivery_id = start_id
    for i in range(MASTERY_URBAN_PER_PERIOD):
        rows.append({"delivery_id": f"D-{delivery_id:04d}", "period": period, "route_type": "urban", "late": i < n_urban_late})
        delivery_id += 1
    for i in range(MASTERY_RURAL_PER_PERIOD):
        rows.append({"delivery_id": f"D-{delivery_id:04d}", "period": period, "route_type": "rural", "late": i < n_rural_late})
        delivery_id += 1
    return rows, delivery_id


def generate_deliveries() -> pd.DataFrame:
    rows, next_id = _delivery_rows("before", MASTERY_BEFORE_URBAN_LATE, MASTERY_BEFORE_RURAL_LATE, 1)
    more_rows, _ = _delivery_rows("after", MASTERY_AFTER_URBAN_LATE, MASTERY_AFTER_RURAL_LATE, next_id)
    return pd.DataFrame(rows + more_rows)


def late_rate(frame: pd.DataFrame, period: str) -> float:
    return float(frame.loc[frame["period"] == period, "late"].mean())


def route_late_rate(frame: pd.DataFrame, route_type: str, period: str) -> float:
    rows = frame[(frame["route_type"] == route_type) & (frame["period"] == period)]
    return float(rows["late"].mean())
