import statistics

import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.alerting import MetricOption, ThresholdOption

INCIDENT_LOG_SCHEMA = Schema(
    columns=(
        ColumnSchema("day", "int64", description="1-indexed day within the 14-day window"),
        ColumnSchema("metric_key", "object"),
        ColumnSchema("value", "float64"),
    )
)

# Two real incidents this quarter (days 5 and 11), each visible in exactly
# one metric - hand-crafted, not random. checkout_error_rate and
# on_time_delivery_rate are the metrics that actually matter; social_mentions
# is a vanity metric that never reflects either incident, and page_load_time
# is a genuinely noisy operational metric that also never reflects either
# incident, but is noisy enough to fire false alarms under a tight threshold.
METRIC_VALUES = {
    "checkout_error_rate": [2.1, 2.3, 2.0, 2.2, 9.0, 2.4, 2.1, 2.3, 2.0, 2.2, 2.1, 2.3, 2.0, 2.2],
    "on_time_delivery_rate": [92, 93, 91, 92, 93, 91, 92, 93, 91, 92, 78, 91, 92, 93],
    "social_mentions": [100, 110, 95, 120, 105, 115, 100, 125, 98, 112, 102, 118, 108, 95],
    "page_load_time": [2.1, 2.3, 1.9, 2.4, 2.0, 2.5, 2.2, 1.8, 2.6, 2.1, 2.3, 1.9, 2.4, 2.0],
}

# Whether a HIGHER value is the bad direction for this metric - checkout
# errors and load time going up is bad, but delivery-on-time going down is.
HIGHER_IS_WORSE = {
    "checkout_error_rate": True,
    "on_time_delivery_rate": False,
    "social_mentions": True,
    "page_load_time": True,
}

REAL_INCIDENT_DAYS = {5, 11}


def generate_incident_log() -> Dataset:
    rows = [(day, metric_key, value) for metric_key, values in METRIC_VALUES.items() for day, value in enumerate(values, start=1)]
    frame = pd.DataFrame(rows, columns=["day", "metric_key", "value"])
    step = PipelineStep("collected", python_code="incident_log = pd.read_csv('novamart_kpi_incident_log.csv')")
    return Dataset(name="novamart_kpi_incident_log", frame=frame, schema=INCIDENT_LOG_SCHEMA, history=(step,))


def metric_series(dataset: Dataset, metric_key: str) -> list[float]:
    metric_frame = dataset.frame[dataset.frame["metric_key"] == metric_key].sort_values("day")
    return [float(value) for value in metric_frame["value"]]


def flagged_days(dataset: Dataset, metric_key: str, multiplier: float) -> set[int]:
    """Real computed anomaly detection: flags any day whose value sits more
    than `multiplier` standard deviations from the metric's own 14-day
    mean, in whichever direction counts as "worse" for that metric."""
    values = metric_series(dataset, metric_key)
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)
    higher_is_worse = HIGHER_IS_WORSE[metric_key]
    flagged = set()
    for day, value in enumerate(values, start=1):
        is_abnormal = value > mean + multiplier * stdev if higher_is_worse else value < mean - multiplier * stdev
        if is_abnormal:
            flagged.add(day)
    return flagged


def simulate_monitoring(dataset: Dataset, metric: MetricOption, threshold: ThresholdOption, target_incident_day: int) -> tuple[int, bool]:
    flagged = flagged_days(dataset, metric.metric_key, threshold.multiplier)
    false_alarm_count = len(flagged - REAL_INCIDENT_DAYS)
    incident_caught = target_incident_day in flagged
    return false_alarm_count, incident_caught


def false_alarm_count(dataset: Dataset, metric_key: str, multiplier: float) -> int:
    """The same false-alarm count simulate_monitoring computes internally,
    independent of any one target day - len(flagged - REAL_INCIDENT_DAYS).
    Used directly by reveals whose ComparisonValue isn't tied to a single
    request's own target_incident_day."""
    return len(flagged_days(dataset, metric_key, multiplier) - REAL_INCIDENT_DAYS)


def real_incidents_caught(dataset: Dataset, metric_key: str, multiplier: float) -> int:
    """How many of the two real incidents (REAL_INCIDENT_DAYS) this
    metric+threshold combo actually flags - a genuine count across BOTH
    real incidents in the observed window, never a single target-day
    boolean (simulate_monitoring's own `incident_caught`) mislabeled as
    this plural quantity. Used by reveals whose copy talks about "the
    real incidents" collectively, not one request's own target day."""
    return len(flagged_days(dataset, metric_key, multiplier) & REAL_INCIDENT_DAYS)


def _flagged_days_mirror_lines(metric_key: str, multiplier: float, var_name: str) -> list[str]:
    """Shared body reused by every mirror function below - reimplements
    flagged_days()'s own mean/pstdev-over-the-full-series logic (not a
    shortcut). FINAL {var_name} is the real flagged-day set."""
    return [
        f'{var_name}_values = incident_log[incident_log["metric_key"] == "{metric_key}"].sort_values("day")["value"].tolist()',
        f"{var_name}_mean = statistics.mean({var_name}_values)",
        f"{var_name}_stdev = statistics.pstdev({var_name}_values)",
        f"{var_name}_higher_is_worse = {HIGHER_IS_WORSE[metric_key]!r}",
        f"{var_name} = set()",
        f"for day, value in enumerate({var_name}_values, start=1):",
        f"    is_abnormal = value > {var_name}_mean + {multiplier} * {var_name}_stdev if {var_name}_higher_is_worse else value < {var_name}_mean - {multiplier} * {var_name}_stdev",
        "    if is_abnormal:",
        f"        {var_name}.add(day)",
    ]


def flagged_days_mirror_code(metric_key: str, multiplier: float, var_name: str) -> str:
    """Verified this session via direct exec against METRIC_VALUES for all
    4 metrics x both real threshold multipliers - the FINAL {var_name}
    matches flagged_days()'s own real output exactly in every case."""
    return "\n".join(_flagged_days_mirror_lines(metric_key, multiplier, var_name))


def false_alarm_count_mirror_code(metric_key: str, multiplier: float, var_name: str) -> str:
    """FINAL {var_name} is the same false_alarm_count simulate_monitoring
    computes internally - len(flagged - REAL_INCIDENT_DAYS)."""
    flagged_var = f"{var_name}_flagged"
    return "\n".join(
        (
            *_flagged_days_mirror_lines(metric_key, multiplier, flagged_var),
            f"{var_name}_real_incident_days = {REAL_INCIDENT_DAYS!r}",
            f"{var_name} = len({flagged_var} - {var_name}_real_incident_days)",
        )
    )


def real_incidents_caught_mirror_code(metric_key: str, multiplier: float, var_name: str) -> str:
    """FINAL {var_name} is the same real_incidents_caught() this module's
    own function returns - len(flagged & REAL_INCIDENT_DAYS), a genuine
    count across both real incidents, never a single target-day boolean."""
    flagged_var = f"{var_name}_flagged"
    return "\n".join(
        (
            *_flagged_days_mirror_lines(metric_key, multiplier, flagged_var),
            f"{var_name}_real_incident_days = {REAL_INCIDENT_DAYS!r}",
            f"{var_name} = len({flagged_var} & {var_name}_real_incident_days)",
        )
    )


def monitoring_outcome_mirror_code(metric: MetricOption, threshold: ThresholdOption, target_incident_day: int, var_name: str) -> str:
    """Builds on the flagged-days logic to produce the same
    (false_alarm_count, incident_caught) pair simulate_monitoring returns
    for ONE target day - the same quantities the interactive scene's own
    live result preview shows. Deliberately distinct from
    real_incidents_caught_mirror_code above: this is the single-target-
    day boolean the live preview actually displays, not the plural
    across-both-incidents count a reveal's own copy might describe."""
    flagged_var = f"{var_name}_flagged"
    return "\n".join(
        (
            *_flagged_days_mirror_lines(metric.metric_key, threshold.multiplier, flagged_var),
            f"{var_name}_real_incident_days = {REAL_INCIDENT_DAYS!r}",
            f"{var_name}_false_alarm_count = len({flagged_var} - {var_name}_real_incident_days)",
            f"{var_name}_incident_caught = {target_incident_day} in {flagged_var}",
            f"{var_name} = ({var_name}_false_alarm_count, {var_name}_incident_caught)",
        )
    )
