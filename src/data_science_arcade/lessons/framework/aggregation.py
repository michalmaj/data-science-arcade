from dataclasses import dataclass


@dataclass(frozen=True)
class GroupByOption:
    key: str
    label_key: str
    column: str


@dataclass(frozen=True)
class AggregateOption:
    key: str
    label_key: str
    func: str  # a pandas-recognized aggregation function name: "sum", "mean", "count"


@dataclass(frozen=True)
class AggregationRequest:
    key: str
    prompt_key: str
    value_column: str
    group_by_options: tuple[GroupByOption, ...]
    aggregate_options: tuple[AggregateOption, ...]
    hint_key: str | None = None


PipelineChoice = tuple[str, str]  # (group_by_key, aggregate_key)
PipelineChoices = dict[str, PipelineChoice]
