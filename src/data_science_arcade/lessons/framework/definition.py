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
    estimated_minutes: int
    """Current honest single-pass playtime, not the spec's 70-90 minute
    target these lessons don't hit yet - a false "70 min" estimate on a
    15-minute lesson would just be a second misleading number. Revised
    upward lesson by lesson as each one gets its own content-deepening
    pass."""
    related_handbook_entry_id: str | None = None
    """When set, MissionBriefingScene shows an extra "Learn More" button
    linking to this Handbook entry (handbook/registry.py). Only Lesson 01
    sets this today - proof-of-concept, not a pattern the other 29 lessons
    need to adopt."""
