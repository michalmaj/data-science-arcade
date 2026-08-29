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
