from dataclasses import dataclass


@dataclass(frozen=True)
class MetricRow:
    key: str
    label_key: str
    treatment_value: float
    control_value: float
    flagged: bool = False


@dataclass(frozen=True)
class MonitoringCheckpoint:
    day: int
    rows: tuple[MetricRow, ...]
