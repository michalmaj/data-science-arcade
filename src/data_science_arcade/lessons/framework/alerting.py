from dataclasses import dataclass


@dataclass(frozen=True)
class MetricOption:
    key: str
    label_key: str
    metric_key: str  # which column in the historical log this refers to


@dataclass(frozen=True)
class ThresholdOption:
    key: str
    label_key: str
    multiplier: float  # stdev multiplier applied to the metric's own 14-day spread; smaller = tighter


@dataclass(frozen=True)
class MonitoringRequest:
    key: str
    prompt_key: str
    target_incident_day: int  # 1-indexed day this scenario's real incident actually happened on
    metric_options: tuple[MetricOption, ...]
    threshold_options: tuple[ThresholdOption, ...]
    hint_key: str | None = None


MonitoringChoice = tuple[str, str]  # (metric_key, threshold_key)
MonitoringChoices = dict[str, MonitoringChoice]
