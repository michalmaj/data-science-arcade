import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.power import proportion_difference_ci

# --- NovaMart Go / Quick Pay, continued from L18 (assignment) and L19
# (power plan) - L18/L19's own outcomes stay fully sealed here too. The
# pre-specified decision contract itself is fixed NovaMart policy, stated
# before any checkpoint data and NEVER adjusted to fit it:
#   - primary launch criterion: the 95% CI for (treatment - control) lies
#     ENTIRELY above +1.5pp (L19's own business minimum useful effect) -
#     not "point estimate clears the bar AND CI excludes zero."
#   - guardrail (support/refund) breach criterion: the 95% CI lies
#     ENTIRELY above a pre-set +0.5pp harmful-increase threshold - a
#     stricter, explicit NovaMart policy number, not a generic
#     "excludes zero" significance test.
#   - planned end = week 7 (n=14,000/arm, L19's own chosen 7-week design);
#     no pre-specified efficacy-based interim stopping rule.
# ------------------------------------------------------------------------

BASELINE_RATE = 0.24
BUSINESS_MINIMUM_EFFECT = 0.015
GUARDRAIL_HARM_THRESHOLD = 0.005
WEEKLY_N_PER_ARM = 2000
PLANNED_END_WEEK = 7
CHECKPOINT_WEEKS = (1, 3, 7)

PRIMARY = "primary"
SUPPORT_GUARDRAIL = "support_guardrail"
REFUND_GUARDRAIL = "refund_guardrail"
METRIC_KEYS = (PRIMARY, SUPPORT_GUARDRAIL, REFUND_GUARDRAIL)

CHECKOUT_EXPERIMENT_SCHEMA = Schema(
    columns=(
        ColumnSchema("checkpoint", "int64"),
        ColumnSchema("week", "int64"),
        ColumnSchema("metric_key", "object", description_key="lesson.l20.schema.metric_key"),
        ColumnSchema("group", "object", description_key="lesson.l20.schema.group"),
        ColumnSchema("n", "int64"),
        ColumnSchema("events", "int64", description_key="lesson.l20.schema.events"),
    )
)

# Real cumulative aggregate-count reads at week 1 / 3 / 7 - verified this
# session via a real script against proportion_difference_ci, evaluated
# against the FIXED contract above, never the other way around:
#
# PRIMARY (checkout completion, baseline 24.0%, entire-CI > +1.5pp):
#   week 1  control 480/2000 (24.0%)  treatment  560/2000 (28.00%)  diff +4.00pp  CI [+1.28pp,+6.72pp]  FAILS strict rule (lower bound below +1.5pp)
#   week 3  control 1440/6000 (24.0%) treatment 1632/6000 (27.20%)  diff +3.20pp  CI [+1.64pp,+4.76pp]  PASSES strict rule - genuinely tempting, but not a pre-specified decision point
#   week 7  control 3360/14000(24.0%) treatment 3745/14000(26.75%)  diff +2.75pp  CI [+1.73pp,+3.77pp]  PASSES strict rule at the planned end
#
# SUPPORT GUARDRAIL (support contact rate, higher=worse, baseline 5.0%, entire-CI > +0.5pp):
#   week 1  control 100/2000 (5.00%)  treatment  102/2000 (5.10%)   diff +0.10pp  CI [-1.26pp,+1.46pp]  no breach
#   week 3  control 300/6000 (5.00%)  treatment  324/6000 (5.40%)   diff +0.40pp  CI [-0.39pp,+1.19pp]  no breach
#   week 7  control 700/14000(5.00%)  treatment  868/14000(6.20%)   diff +1.20pp  CI [+0.66pp,+1.74pp]  BREACHES - only at the full planned sample
#
# REFUND GUARDRAIL (refund rate, higher=worse, baseline 2.0%, neutral non-breach case):
#   week 1  control 40/2000 (2.00%)   treatment   42/2000 (2.10%)   diff +0.10pp  CI [-0.78pp,+0.98pp]  no breach
#   week 3  control 120/6000 (2.00%)  treatment  126/6000 (2.10%)   diff +0.10pp  CI [-0.41pp,+0.61pp]  no breach
#   week 7  control 280/14000(2.00%)  treatment  294/14000(2.10%)   diff +0.10pp  CI [-0.23pp,+0.43pp]  no breach, at any checkpoint
ROWS = [
    (1, 1, PRIMARY, "control", 2000, 480),
    (1, 1, PRIMARY, "treatment", 2000, 560),
    (1, 1, SUPPORT_GUARDRAIL, "control", 2000, 100),
    (1, 1, SUPPORT_GUARDRAIL, "treatment", 2000, 102),
    (1, 1, REFUND_GUARDRAIL, "control", 2000, 40),
    (1, 1, REFUND_GUARDRAIL, "treatment", 2000, 42),
    (2, 3, PRIMARY, "control", 6000, 1440),
    (2, 3, PRIMARY, "treatment", 6000, 1632),
    (2, 3, SUPPORT_GUARDRAIL, "control", 6000, 300),
    (2, 3, SUPPORT_GUARDRAIL, "treatment", 6000, 324),
    (2, 3, REFUND_GUARDRAIL, "control", 6000, 120),
    (2, 3, REFUND_GUARDRAIL, "treatment", 6000, 126),
    (3, 7, PRIMARY, "control", 14000, 3360),
    (3, 7, PRIMARY, "treatment", 14000, 3745),
    (3, 7, SUPPORT_GUARDRAIL, "control", 14000, 700),
    (3, 7, SUPPORT_GUARDRAIL, "treatment", 14000, 868),
    (3, 7, REFUND_GUARDRAIL, "control", 14000, 280),
    (3, 7, REFUND_GUARDRAIL, "treatment", 14000, 294),
]


def generate_checkout_experiment() -> Dataset:
    frame = pd.DataFrame(ROWS, columns=["checkpoint", "week", "metric_key", "group", "n", "events"])
    step = PipelineStep("collected", python_code="checkout_experiment = pd.read_csv('novamart_go_quickpay_checkpoints.csv')")
    return Dataset(name="checkout_experiment", frame=frame, schema=CHECKOUT_EXPERIMENT_SCHEMA, history=(step,))


def counts_at_checkpoint(dataset: Dataset, week: int, metric_key: str, group: str) -> tuple[int, int]:
    """(events, n) for one metric/group at one real week."""
    frame = dataset.frame
    rows = frame[(frame["week"] == week) & (frame["metric_key"] == metric_key) & (frame["group"] == group)]
    row = rows.iloc[0]
    return int(row["events"]), int(row["n"])


def rate_at_checkpoint(dataset: Dataset, week: int, metric_key: str, group: str) -> float:
    events, n = counts_at_checkpoint(dataset, week, metric_key, group)
    return events / n


def diff_and_ci_at_checkpoint(dataset: Dataset, week: int, metric_key: str) -> tuple[float, float, float]:
    """(diff, ci_lower, ci_upper) for treatment - control at one real week."""
    control_events, control_n = counts_at_checkpoint(dataset, week, metric_key, "control")
    treatment_events, treatment_n = counts_at_checkpoint(dataset, week, metric_key, "treatment")
    ci_lower, ci_upper = proportion_difference_ci(control_events, control_n, treatment_events, treatment_n)
    diff = treatment_events / treatment_n - control_events / control_n
    return diff, ci_lower, ci_upper


def primary_passes(ci_lower: float) -> bool:
    """The ENTIRE interval must clear the pre-set +1.5pp threshold - the
    point estimate is irrelevant to pass/fail. Fixed NovaMart policy,
    never softened to fit a checkpoint's own numbers."""
    return ci_lower > BUSINESS_MINIMUM_EFFECT


def guardrail_breached(ci_lower: float) -> bool:
    """Same 'entire interval clears a pre-set bar' shape as
    primary_passes, a different (stricter) threshold constant. Both
    guardrails (support, refund) use this one helper."""
    return ci_lower > GUARDRAIL_HARM_THRESHOLD


# --- Python Mirror - built directly from the real counts above, so a
# change to ROWS can never silently desync the mirror text from the real
# data. Every interim checkpoint (week 1, week 3) prefixes EVERY variable
# it assigns with week{N}_; the week-7 (planned end) checkpoint is the
# ONLY place in the whole lesson that ever assigns the bare canonical
# names (primary_diff, support_ci_lower, ...) - the canonical-substitution
# guard against the recurring L18 bug class. -----------------------------


def _metric_mirror(var_prefix: str, metric_key: str, control_events: int, n: int, treatment_events: int) -> str:
    return (
        f"{var_prefix}{metric_key}_control_rate = {control_events} / {n}\n"
        f"{var_prefix}{metric_key}_treatment_rate = {treatment_events} / {n}\n"
        f"{var_prefix}{metric_key}_diff = {var_prefix}{metric_key}_treatment_rate - {var_prefix}{metric_key}_control_rate\n"
        f"{var_prefix}{metric_key}_ci_lower, {var_prefix}{metric_key}_ci_upper = "
        f"proportion_difference_ci({control_events}, {n}, {treatment_events}, {n})"
    )


def checkpoint_mirror_code(dataset: Dataset, week: int) -> str:
    """The only code that ever assigns each metric's own diff/CI - reflects
    the real counts at this real week. `week == PLANNED_END_WEEK` gets the
    bare canonical variable names; every other week gets a week{N}_ prefix
    on every variable it assigns, so no interim checkpoint's own code can
    ever collide with (and silently overwrite) the final canonical state."""
    var_prefix = "" if week == PLANNED_END_WEEK else f"week{week}_"
    blocks = []
    for metric_key in METRIC_KEYS:
        control_events, n = counts_at_checkpoint(dataset, week, metric_key, "control")
        treatment_events, _n = counts_at_checkpoint(dataset, week, metric_key, "treatment")
        blocks.append(_metric_mirror(var_prefix, metric_key, control_events, n, treatment_events))
    return "\n".join(blocks)


# --- Optional mastery: NovaMart Logistics courier route-batching, a
# pre-specified SAFETY stopping rule - a deliberate opposite-lesson
# contrast. The rule is stated explicitly, BEFORE the result, exactly
# like the main case's own primary/guardrail criteria: "At the scheduled
# week-2 safety review, stop if the entire 95% CI for damage-claim harm
# lies above +1.0pp." Result at that scheduled review, n=800/arm: control
# 8/800 (1.00%), treatment 28/800 (3.50%), diff +2.50pp, 95% CI
# [+1.05pp, +3.95pp] - the entire interval clears the pre-set +1.0pp
# safety threshold, so the rule genuinely fires. ------------------------

MASTERY_SAFETY_THRESHOLD = 0.01
MASTERY_N_PER_ARM = 800
MASTERY_ROWS = [("control", 800, 8), ("treatment", 800, 28)]

MASTERY_SCHEMA = Schema(
    columns=(
        ColumnSchema("group", "object", description_key="lesson.l20.schema.group"),
        ColumnSchema("n", "int64"),
        ColumnSchema("events", "int64", description_key="lesson.l20.schema.events_mastery"),
    )
)


def generate_mastery_safety_check() -> Dataset:
    frame = pd.DataFrame(MASTERY_ROWS, columns=["group", "n", "events"])
    step = PipelineStep("collected", python_code="mastery_safety_check = pd.read_csv('novamart_logistics_safety_review.csv')")
    return Dataset(name="mastery_safety_check", frame=frame, schema=MASTERY_SCHEMA, history=(step,))


def mastery_counts(dataset: Dataset, group: str) -> tuple[int, int]:
    row = dataset.frame[dataset.frame["group"] == group].iloc[0]
    return int(row["events"]), int(row["n"])


def mastery_rate(dataset: Dataset, group: str) -> float:
    events, n = mastery_counts(dataset, group)
    return events / n


def mastery_diff_and_ci(dataset: Dataset) -> tuple[float, float, float]:
    control_events, control_n = mastery_counts(dataset, "control")
    treatment_events, treatment_n = mastery_counts(dataset, "treatment")
    ci_lower, ci_upper = proportion_difference_ci(control_events, control_n, treatment_events, treatment_n)
    diff = treatment_events / treatment_n - control_events / control_n
    return diff, ci_lower, ci_upper


def mastery_safety_rule_met(ci_lower: float) -> bool:
    return ci_lower > MASTERY_SAFETY_THRESHOLD


def mastery_mirror_code() -> str:
    control_events, n = mastery_counts(generate_mastery_safety_check(), "control")
    treatment_events, _n = mastery_counts(generate_mastery_safety_check(), "treatment")
    return _metric_mirror("mastery_", "damage_claim", control_events, n, treatment_events)
