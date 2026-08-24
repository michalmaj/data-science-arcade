from dataclasses import dataclass, field
from enum import Enum

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

    def state_of(self, lesson_number: int) -> LessonState:
        return self.lesson_states.get(lesson_number, LessonState.LOCKED)

    def unlock(self, lesson_number: int) -> None:
        if self.state_of(lesson_number) == LessonState.LOCKED:
            self.lesson_states[lesson_number] = LessonState.UNLOCKED

    def complete(self, lesson_number: int) -> None:
        self.lesson_states[lesson_number] = LessonState.COMPLETED
        if lesson_number < TOTAL_LESSONS:
            self.unlock(lesson_number + 1)
