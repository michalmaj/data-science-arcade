from collections.abc import Callable

from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l01_question_first.scenario import build_lesson_one_runner
from data_science_arcade.lessons.l02_source_scout.scenario import build_lesson_two_runner

RunnerBuilder = Callable[..., tuple[LessonRunner, dict]]

LESSON_RUNNERS: dict[int, RunnerBuilder] = {
    1: build_lesson_one_runner,
    2: build_lesson_two_runner,
}
"""Lesson number -> its build_lesson_*_runner(app, on_finished) factory.
The single place CourseMapScene (or anything else that wants to launch a
lesson) needs to know about, instead of importing and special-casing each
lesson's scenario module individually. Lessons not listed here have no
runtime yet - spec Phase 8+ adds them."""
