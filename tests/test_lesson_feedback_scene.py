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

# The real worst case today (see lesson_feedback_scene.py's own docstring):
# 6 real dimensions (L07, L10, L30) and, for L30 specifically, 7
# simultaneous observations (one per dimension plus hints_used - L30 has
# no mastery/trajectory observations). Built from L30's own real,
# genuinely long locale strings rather than synthetic placeholder text, so
# this exercises real wrapping behavior, not an artificially short stand-in.
WORST_CASE_EVALUATION = LessonEvaluation(
    dimension_scores={
        ScoreDimension.METHOD: 35.0,
        ScoreDimension.REASONING: 15.0,
        ScoreDimension.EVIDENCE: 50.0,
        ScoreDimension.COMMUNICATION: 35.0,
        ScoreDimension.UNCERTAINTY: 15.0,
        ScoreDimension.OVERCONFIDENCE: 25.0,
    },
    observations=(
        FeedbackObservation("lesson.l30.feedback.method_weak_execution", ScoreDimension.METHOD),
        FeedbackObservation("lesson.l30.feedback.claim_outruns_evidence", ScoreDimension.REASONING),
        FeedbackObservation("lesson.l30.feedback.evidence_missing_a_role", ScoreDimension.EVIDENCE),
        FeedbackObservation("lesson.l30.feedback.recommendation_not_coherent", ScoreDimension.COMMUNICATION),
        FeedbackObservation("lesson.l30.feedback.uncertainty_overclaimed", ScoreDimension.UNCERTAINTY),
        FeedbackObservation("lesson.l30.feedback.confidence_overclaimed", ScoreDimension.OVERCONFIDENCE),
        FeedbackObservation("lesson.feedback.hints_used"),
    ),
    hints_used=2,
    completed_thoughtfully=True,
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


def test_worst_case_layout_has_no_overlap_between_content_and_buttons():
    app = _init_app()
    try:
        for locale in ("en", "pl"):
            app.localization.set_locale(locale)
            scene = LessonFeedbackScene(app, WORST_CASE_EVALUATION, on_complete=lambda: None)
            scene.draw(app.logical_surface)  # must not crash or clip silently

            assert len(scene.pages) >= 1
            # Every real observation's own text must land somewhere across
            # the pages - nothing silently dropped by pagination.
            all_page_text = " ".join(line for page in scene.pages for line in page)
            for observation in WORST_CASE_EVALUATION.observations:
                expected_first_word = app.localization.t(observation.text_key).split()[0]
                assert expected_first_word in all_page_text, f"{locale}: {observation.text_key} missing from paginated output"

            max_lines_on_a_page = max(len(page) for page in scene.pages)
            content_bottom = scene._first_observation_y + max_lines_on_a_page * scene._line_height
            for button in scene.buttons.buttons:
                assert button.rect.top >= content_bottom, (
                    f"{locale}: button at top={button.rect.top} overlaps observation content ending at y={content_bottom}"
                )
    finally:
        pygame.quit()


def test_worst_case_needs_more_than_one_page():
    # A regression guard on the test fixture itself: if this ever collapses
    # back to one page (e.g. a future layout change frees up a lot more
    # vertical room), the overlap test above would pass vacuously without
    # ever exercising the Back/Next paging path this fix added.
    app = _init_app()
    try:
        scene = LessonFeedbackScene(app, WORST_CASE_EVALUATION, on_complete=lambda: None)
        assert len(scene.pages) > 1
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
