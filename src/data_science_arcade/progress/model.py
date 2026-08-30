from dataclasses import dataclass, field
from enum import Enum

from data_science_arcade.lessons.framework.evaluation import LessonEvaluation

LESSONS_PER_CHAPTER = 5
CHAPTER_COUNT = 6
TOTAL_LESSONS = LESSONS_PER_CHAPTER * CHAPTER_COUNT
FIRST_LESSON = 1


class LessonState(Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    COMPLETED = "completed"


def chapter_of(lesson_number: int) -> int:
    return (lesson_number - 1) // LESSONS_PER_CHAPTER + 1


@dataclass(frozen=True)
class LessonCheckpoint:
    """Where a player was mid-lesson when they last quit without finishing.
    stage_fingerprint guards resuming into a stage sequence a later change
    has since reshaped - a mismatch is treated the same as no checkpoint at
    all rather than trusting a stale stage_index/collected shape."""

    stage_index: int
    stage_fingerprint: str
    collected: dict


@dataclass
class Progress:
    """Everything about a student's save: language/display settings plus
    where they are in the course. Lesson numbers not present in
    lesson_states are implicitly LOCKED - only deviations from that default
    need to be stored."""

    language: str = "en"
    fullscreen: bool = False
    lesson_states: dict[int, LessonState] = field(
        default_factory=lambda: {FIRST_LESSON: LessonState.UNLOCKED}
    )
    checkpoints: dict[int, LessonCheckpoint] = field(default_factory=dict)
    evaluations: dict[int, LessonEvaluation] = field(default_factory=dict)
    hints_used: dict[int, int] = field(default_factory=dict)

    def state_of(self, lesson_number: int) -> LessonState:
        return self.lesson_states.get(lesson_number, LessonState.LOCKED)

    def unlock(self, lesson_number: int) -> None:
        if self.state_of(lesson_number) == LessonState.LOCKED:
            self.lesson_states[lesson_number] = LessonState.UNLOCKED

    def complete(self, lesson_number: int) -> None:
        self.checkpoints.pop(lesson_number, None)
        self.lesson_states[lesson_number] = LessonState.COMPLETED
        if lesson_number < TOTAL_LESSONS:
            self.unlock(lesson_number + 1)

    def checkpoint_for(self, lesson_number: int) -> LessonCheckpoint | None:
        return self.checkpoints.get(lesson_number)

    def save_checkpoint(self, lesson_number: int, checkpoint: LessonCheckpoint) -> None:
        self.checkpoints[lesson_number] = checkpoint

    def record_evaluation(self, lesson_number: int, evaluation: LessonEvaluation) -> None:
        self.evaluations[lesson_number] = evaluation
        self.hints_used[lesson_number] = evaluation.hints_used
