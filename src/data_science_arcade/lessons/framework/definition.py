from dataclasses import dataclass
from enum import Enum


class ScoreDimension(Enum):
    """Cross-course scoring dimensions (spec §20). A lesson uses whichever
    subset actually matters for it - not every dimension in every lesson."""

    DATA_QUALITY = "data_quality"
    METHOD = "method"
    REASONING = "reasoning"
    EVIDENCE = "evidence"
    UNCERTAINTY = "uncertainty"
    REPRODUCIBILITY = "reproducibility"
    COMMUNICATION = "communication"
    OVERCONFIDENCE = "overconfidence"


@dataclass(frozen=True)
class LessonDefinition:
    """Static metadata about a lesson (spec §27/§28's lesson.yaml, as a
    Python dataclass rather than literal YAML - nothing else in this
    project parses YAML, and the spec explicitly says not to treat that
    example schema as a frozen API)."""

    id: str
    chapter: int
    number: int
    title_key: str
    objective_keys: tuple[str, ...]
    scoring_dimensions: tuple[ScoreDimension, ...]
