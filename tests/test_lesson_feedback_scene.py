import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

EVALUATION = LessonEvaluation(
    dimension_scores={ScoreDimension.REASONING: 75.0, ScoreDimension.EVIDENCE: 60.0},
    observations=(
        FeedbackObservation("lesson.feedback.completed"),
        FeedbackObservation("lesson.feedback.hints_used", dimension=ScoreDimension.REASONING),
    ),
    hints_used=1,
    completed_thoughtfully=True,
)

ALL_DIMENSIONS_EVALUATION = LessonEvaluation(
    dimension_scores={dimension: 50.0 for dimension in ScoreDimension},
    observations=(),
    hints_used=0,
    completed_thoughtfully=False,
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_continue_button_calls_on_complete():
    app = _init_app()
    try:
        calls = []
        scene = LessonFeedbackScene(app, EVALUATION, on_complete=lambda: calls.append("done"))

        scene.buttons.buttons[0].on_activate()

        assert calls == ["done"]
    finally:
        pygame.quit()


def test_draw_does_not_crash_with_a_typical_evaluation():
    app = _init_app()
    try:
        scene = LessonFeedbackScene(app, EVALUATION, on_complete=lambda: None)
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_draw_does_not_crash_with_no_observations():
    app = _init_app()
    try:
        scene = LessonFeedbackScene(app, ALL_DIMENSIONS_EVALUATION, on_complete=lambda: None)
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_every_score_dimension_has_a_display_label():
    app = _init_app()
    try:
        from data_science_arcade.ui.lesson_feedback_scene import DIMENSION_LABEL_KEYS

        assert set(DIMENSION_LABEL_KEYS) == set(ScoreDimension)
        loc = app.localization
        for key in DIMENSION_LABEL_KEYS.values():
            text = loc.t(key)
            assert not text.startswith("??")  # a real translation exists, not a missing-key placeholder
    finally:
        pygame.quit()
