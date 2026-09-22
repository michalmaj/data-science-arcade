from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.framework.evaluation import LessonEvaluation
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.handbook_pagination import paginate
from data_science_arcade.ui.text import draw_centered_text, draw_single_line

CENTER_X = LOGICAL_SIZE[0] // 2
TITLE_Y = 60
SCORES_HEADER_Y = 110
FIRST_SCORE_Y = 140
SCORE_SPACING = 26
SCORE_LEFT_X = CENTER_X - 200
OBSERVATIONS_HEADER_GAP = 40  # below the last score line, however many dimensions there are
OBSERVATIONS_FIRST_LINE_GAP = 30  # below the observations header, to the first rendered line
OBSERVATION_LEFT_X = CENTER_X - 300
OBSERVATION_MAX_WIDTH = 600
OBSERVATION_FONT_SIZE = 15
OBSERVATION_LINE_SPACING = 4
# Two different bottom limits, tried in order (see __init__): most lessons'
# real observations (2-5 short-to-medium bullets) fit above the Continue
# button on their own with no nav row at all - reserving nav space for
# them unconditionally would paginate the common case for no reason. Only
# when content doesn't fit under NO_NAV_BOTTOM_LIMIT does __init__ redo the
# layout against the smaller WITH_NAV_BOTTOM_LIMIT, which leaves the nav
# row (PAGE_NAV_Y) real room above the Continue button.
NO_NAV_BOTTOM_LIMIT = 440
WITH_NAV_BOTTOM_LIMIT = 396
PAGE_NAV_Y = 422
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
    """Real, choice-sensitive feedback between decision and debrief - used
    by every one of the 30 lessons' own stage sequences. Dimension counts
    vary per lesson (2 to 6 today; nothing here assumes a fixed count);
    observations are paginated (see ui/handbook_pagination.py's own
    paginate()) rather than assuming they all fit on one screen, so a
    lesson with many independent failure modes worth surfacing (L07, L10,
    L30) renders exactly as legibly as one with two - real pages with a
    Back/Next row, never a shrunk-to-illegible font."""

    def __init__(self, app, evaluation: LessonEvaluation, on_complete: Callable[[], None]) -> None:
        super().__init__(app)
        self.evaluation = evaluation
        self.on_complete = on_complete
        self.page_index = 0

        loc = app.localization
        dimension_count = len(evaluation.dimension_scores)
        # However many dimensions this lesson declares, the observations
        # header starts a fixed gap below the last score line instead of a
        # hardcoded y that a longer list could grow past.
        last_score_y = FIRST_SCORE_Y + max(dimension_count - 1, 0) * SCORE_SPACING
        self._observations_header_y = last_score_y + OBSERVATIONS_HEADER_GAP
        self._first_observation_y = self._observations_header_y + OBSERVATIONS_FIRST_LINE_GAP

        font = get_font(OBSERVATION_FONT_SIZE)
        self._line_height = font.get_linesize() + OBSERVATION_LINE_SPACING
        paragraphs = [f"- {loc.t(observation.text_key)}" for observation in evaluation.observations]

        def _paginate_against(bottom_limit: int) -> list[list[str]]:
            available_height = max(bottom_limit - self._first_observation_y, self._line_height)
            max_lines_per_page = max(1, available_height // self._line_height)
            return paginate(paragraphs, font, OBSERVATION_MAX_WIDTH, max_lines_per_page) if paragraphs else [[]]

        self.pages = _paginate_against(NO_NAV_BOTTOM_LIMIT)
        if len(self.pages) > 1:
            # Didn't fit above the Continue button on its own - repaginate
            # against the smaller budget that leaves the nav row real room.
            self.pages = _paginate_against(WITH_NAV_BOTTOM_LIMIT)

        self._rebuild_buttons()

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []

        if len(self.pages) > 1:
            # Dedicated keys, not the shared brief.back/brief.next - those
            # both render as "Dalej" in Polish, identical to
            # runtime.continue_button, which would put two buttons reading
            # the same word directly above one another on this one screen
            # (a real collision only visible once a lesson had enough
            # observations to paginate at all - caught by a real PL
            # screenshot, not by any width or key-existence test).
            back_rect = pygame.Rect(0, 0, 120, 36)
            back_rect.center = (CENTER_X - 80, PAGE_NAV_Y)
            buttons.append(
                Button(back_rect, loc.t("runtime.feedback_previous_page"), self._previous_page, enabled=self.page_index > 0)
            )

            next_rect = pygame.Rect(0, 0, 120, 36)
            next_rect.center = (CENTER_X + 80, PAGE_NAV_Y)
            buttons.append(
                Button(
                    next_rect, loc.t("runtime.feedback_next_page"), self._next_page, enabled=self.page_index < len(self.pages) - 1
                )
            )

        continue_rect = pygame.Rect(0, 0, *CONTINUE_BUTTON_SIZE)
        continue_rect.center = (CENTER_X, CONTINUE_BUTTON_Y)
        self.continue_button = Button(continue_rect, loc.t("runtime.continue_button"), self.on_complete)
        buttons.append(self.continue_button)

        self.buttons = ButtonGroup(buttons)

    def _previous_page(self) -> None:
        if self.page_index > 0:
            self.page_index -= 1
            self._rebuild_buttons()

    def _next_page(self) -> None:
        if self.page_index < len(self.pages) - 1:
            self.page_index += 1
            self._rebuild_buttons()

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
        for index, (dimension, score) in enumerate(self.evaluation.dimension_scores.items()):
            y = FIRST_SCORE_Y + index * SCORE_SPACING
            line = f"{loc.t(DIMENSION_LABEL_KEYS[dimension])}: {score:.0f}"
            draw_centered_text(surface, line, (SCORE_LEFT_X, y), 15, colors.BUTTON_FOCUS_BORDER)

        draw_centered_text(surface, loc.t("runtime.observations_header"), (CENTER_X, self._observations_header_y), 18, colors.TEXT)
        page = self.pages[self.page_index] if self.pages else []
        for index, line in enumerate(page):
            if line:
                y = self._first_observation_y + index * self._line_height
                draw_single_line(surface, line, (OBSERVATION_LEFT_X, y), OBSERVATION_MAX_WIDTH, OBSERVATION_FONT_SIZE, colors.TEXT)

        if len(self.pages) > 1:
            progress = f"{self.page_index + 1} / {len(self.pages)}"
            draw_centered_text(surface, progress, (CENTER_X, PAGE_NAV_Y - 26), 13, colors.BUTTON_TEXT_DISABLED)

        self.buttons.draw(surface)
