from dataclasses import dataclass


@dataclass(frozen=True)
class SourceAttribute:
    label_key: str
    rating_key: str


@dataclass(frozen=True)
class DataSource:
    """One candidate data source on a comparison board (spec §25 Lesson 02
    'Source Scout'): a name plus an ordered list of trade-off attributes
    (freshness, coverage, cost, bias risk, schema quality, ...)."""

    key: str
    name_key: str
    attributes: tuple[SourceAttribute, ...]
