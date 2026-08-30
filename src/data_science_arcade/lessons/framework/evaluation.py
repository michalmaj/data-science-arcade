from dataclasses import dataclass
from typing import Protocol

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

COMPLETED_BASE_SCORE = 75.0
INCOMPLETE_BASE_SCORE = 40.0
PER_HINT_PENALTY = 5.0
MINIMUM_SCORE = 20.0


@dataclass(frozen=True)
class FeedbackObservation:
    text_key: str
    dimension: ScoreDimension | None = None


@dataclass(frozen=True)
class LessonEvaluation:
    """A real, persisted per-attempt result - not just 'completed: bool'.
    dimension_scores covers exactly the dimensions the lesson's own
    LessonDefinition declares, never dimensions it doesn't."""

    dimension_scores: dict[ScoreDimension, float]
    observations: tuple[FeedbackObservation, ...]
    hints_used: int
    completed_thoughtfully: bool


class HasCompletedThoughtfully(Protocol):
    def completed_thoughtfully(self) -> bool: ...


def default_scorer(result: HasCompletedThoughtfully, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    """The one scorer every lesson gets for free, using the only signal
    every LessonXResult already exposes identically: completed_thoughtfully().
    Real and persisted, but not yet choice-aware - it can't tell reasoning
    quality apart from finished-without-much-help, since that needs
    per-lesson content knowledge. Lessons get a smarter, content-aware
    scorer as they go through their own content-deepening pass."""
    completed = result.completed_thoughtfully()
    base = COMPLETED_BASE_SCORE if completed else INCOMPLETE_BASE_SCORE
    score = max(MINIMUM_SCORE, base - PER_HINT_PENALTY * hints_used)

    observations = [FeedbackObservation("lesson.feedback.completed" if completed else "lesson.feedback.incomplete")]
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores={dimension: score for dimension in definition.scoring_dimensions},
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=completed,
    )
