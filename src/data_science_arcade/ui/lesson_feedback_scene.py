from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.framework.evaluation import LessonEvaluation
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
TITLE_Y = 60
SCORES_HEADER_Y = 110
FIRST_SCORE_Y = 140
SCORE_SPACING = 26
SCORE_LEFT_X = CENTER_X - 200
OBSERVATIONS_HEADER_GAP = 40  # below the last score line, however many dimensions there are
OBSERVATION_SPACING = 30
OBSERVATION_LEFT_X = CENTER_X - 300
OBSERVATION_MAX_WIDTH = 600
CONTINUE_BUTTON_SIZE = (200, 48)
CONTINUE_BUTTON_Y = 480

DIMENSION_LABEL_KEYS = {
    ScoreDimension.DATA_QUALITY: "score_dimension.data_quality",
    ScoreDimension.METHOD: "score_dimension.method",
    ScoreDimension.REASONING: "score_dimension.reasoning",
    ScoreDimension.EVIDENCE: "score_dimension.evidence",
    ScoreDimension.UNCERTAINTY: "score_dimension.uncertainty",
    ScoreDimension.REPRODUCIBILITY: "score_dimension.reproducibility",
    ScoreDimension.COMMUNICATION: "score_dimension.communication",
    ScoreDimension.OVERCONFIDENCE: "score_dimension.overconfidence",
}


class LessonFeedbackScene(Scene):
    """Real, choice-sensitive feedback between decision and debrief (spec:
    a final decision should lead to feedback referencing what the student
    actually did, not just a static narrative debrief regardless of their
    choices) - built and tested against a synthetic LessonEvaluation here,
    not yet inserted into any of the 30 lessons' own stage sequences.
    Doing that now would add a new screen to all 30 lessons' real
    playthrough for content that's currently only the generic "completed"/
    "hints used" pair evaluation.py's default_scorer produces; real
    choice-sensitive observation text is per-lesson content work for each
    lesson's own content-deepening pass, so this scene exists and is
    proven ahead of that, rather than needing to be built twice."""

    def __init__(self, app, evaluation: LessonEvaluation, on_complete: Callable[[], None]) -> None:
        super().__init__(app)
        self.evaluation = evaluation
        self.on_complete = on_complete

        loc = app.localization
        continue_rect = pygame.Rect(0, 0, *CONTINUE_BUTTON_SIZE)
        continue_rect.center = (CENTER_X, CONTINUE_BUTTON_Y)
        self.buttons = ButtonGroup([Button(continue_rect, loc.t("runtime.continue_button"), self.on_complete)])

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every
        # stage in Pausable, which intercepts Escape before this scene
        # sees it - same discipline as every other stage scene.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t("runtime.feedback_title"), (CENTER_X, TITLE_Y), 28, colors.TEXT)

        draw_centered_text(surface, loc.t("runtime.scores_header"), (CENTER_X, SCORES_HEADER_Y), 18, colors.TEXT)
        dimension_count = len(self.evaluation.dimension_scores)
        for index, (dimension, score) in enumerate(self.evaluation.dimension_scores.items()):
            y = FIRST_SCORE_Y + index * SCORE_SPACING
            line = f"{loc.t(DIMENSION_LABEL_KEYS[dimension])}: {score:.0f}"
            draw_centered_text(surface, line, (SCORE_LEFT_X, y), 15, colors.BUTTON_FOCUS_BORDER)

        # However many dimensions this lesson declares (every one of the 30
        # lessons today declares 2-3, but nothing here assumes a fixed
        # count), the observations header starts a fixed gap below the
        # last score line instead of a hardcoded y that a longer list
        # could grow past.
        last_score_y = FIRST_SCORE_Y + max(dimension_count - 1, 0) * SCORE_SPACING
        observations_header_y = last_score_y + OBSERVATIONS_HEADER_GAP
        draw_centered_text(surface, loc.t("runtime.observations_header"), (CENTER_X, observations_header_y), 18, colors.TEXT)
        first_observation_y = observations_header_y + OBSERVATION_SPACING
        for index, observation in enumerate(self.evaluation.observations):
            y = first_observation_y + index * OBSERVATION_SPACING
            draw_wrapped_text(surface, f"- {loc.t(observation.text_key)}", (OBSERVATION_LEFT_X, y), OBSERVATION_MAX_WIDTH, 15, colors.TEXT)

        self.buttons.draw(surface)
