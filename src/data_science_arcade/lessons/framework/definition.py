from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class ScoreDimension(Enum):
    """Cross-course scoring dimensions. A lesson uses whichever subset
    actually matters for it - not every dimension in every lesson."""

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
    """Static metadata about a lesson, as a Python dataclass rather than
    literal YAML - nothing else in this project parses YAML."""

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
    linking to this Handbook entry (handbook/registry.py). Lessons 01, 02,
    and 06 set this today - a real, recurring pattern where a lesson's own
    content genuinely needs the Handbook's deeper theory layer, not
    something every lesson needs to adopt."""
    scorer: Callable[[object, "LessonDefinition", int], object] | None = None
    """A lesson-specific replacement for evaluation.py's default_scorer,
    same (result, definition, hints_used) -> LessonEvaluation shape -
    course_map_scene.py's _start_lesson uses `definition.scorer or
    default_scorer` for the evaluation it actually persists, so leaving
    this None silently falls back to the generic completed/incomplete
    score even for a lesson whose own scenario.py already computes and
    displays a real content-aware evaluation inline. Every lesson with a
    dedicated score_lesson_* function must set this - a regression test
    (test_lesson_scoring_persistence.py) enforces it. Typed loosely
    (object, not LessonEvaluation) to avoid a circular import -
    evaluation.py already imports LessonDefinition from this module."""
