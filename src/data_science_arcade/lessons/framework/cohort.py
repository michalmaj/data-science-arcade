from dataclasses import dataclass


@dataclass(frozen=True)
class CohortRow:
    key: str
    label_key: str
    months_observed: int  # how many columns (0..months_observed-1) this cohort actually has data for
    retention_by_month: tuple[float, ...]  # length == months_observed


@dataclass(frozen=True)
class CohortMatrix:
    rows: tuple[CohortRow, ...]  # oldest cohort first
    month_count: int  # total columns to draw (the oldest cohort's months_observed)


@dataclass(frozen=True)
class ComparisonOption:
    key: str
    label_key: str
    cohort_a: str
    month_a: int
    cohort_b: str
    month_b: int


@dataclass(frozen=True)
class CohortRequest:
    key: str
    prompt_key: str
    options: tuple[ComparisonOption, ...]
    hint_key: str | None = None


CohortChoices = dict[str, str]
