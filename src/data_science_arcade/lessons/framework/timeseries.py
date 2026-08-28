from dataclasses import dataclass


@dataclass(frozen=True)
class DailyPoint:
    day: int  # 1-indexed within its period; day 1 is always a Monday
    value: float


@dataclass(frozen=True)
class TimeSeries:
    label_key: str
    points: tuple[DailyPoint, ...]


def is_weekend(day: int) -> bool:
    return (day - 1) % 7 in (5, 6)


@dataclass(frozen=True)
class LensOption:
    key: str
    label_key: str
    show_previous_period: bool


@dataclass(frozen=True)
class TimeSeriesRequest:
    key: str
    prompt_key: str
    highlight_days: tuple[int, ...]  # which days (1-indexed) this claim is actually about
    options: tuple[LensOption, ...]
    hint_key: str | None = None


TimeSeriesChoices = dict[str, str]
