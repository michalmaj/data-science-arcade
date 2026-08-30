from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.definition import LessonDefinition
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text, wrap_text

CENTER_X = LOGICAL_SIZE[0] // 2
TITLE_Y = 70
DURATION_Y = 108
OBJECTIVES_HEADER_Y = 150
FIRST_OBJECTIVE_Y = 182
OBJECTIVE_FONT_SIZE = 15
OBJECTIVE_LINE_SPACING = 4
OBJECTIVE_GAP = 10  # extra vertical gap between one objective and the next
OBJECTIVE_LEFT_X = CENTER_X - 300
OBJECTIVE_MAX_WIDTH = 600
START_BUTTON_SIZE = (240, 48)
START_BUTTON_Y = 460


class MissionBriefingScene(Scene):
    """Shown once, before a lesson's own first stage: real title, real
    objectives (LessonDefinition.objective_keys - already authored for
    every lesson since Phase 7, just never shown to the player until now),
    and an honest estimated duration. Auto-prepended by LessonRunner
    whenever it's given a `definition`, so no lesson's own scenario.py
    needs a new stage function to get this."""

    def __init__(self, app, definition: LessonDefinition, on_start: Callable[[], None]) -> None:
        super().__init__(app)
        self.definition = definition
        self.on_start = on_start

        loc = app.localization
        start_rect = pygame.Rect(0, 0, *START_BUTTON_SIZE)
        start_rect.center = (CENTER_X, START_BUTTON_Y)
        self.buttons = ButtonGroup([Button(start_rect, loc.t("runtime.start_mission"), self.on_start)])

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps this stage
        # in Pausable, which intercepts Escape before this scene sees it -
        # same discipline as every other stage scene.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.definition.title_key), (CENTER_X, TITLE_Y), 30, colors.TEXT)
        duration_line = f"{loc.t('runtime.estimated_duration_label')}: {self.definition.estimated_minutes} min"
        draw_centered_text(surface, duration_line, (CENTER_X, DURATION_Y), 15, colors.BUTTON_TEXT_DISABLED)

        draw_centered_text(surface, loc.t("runtime.objectives_header"), (CENTER_X, OBJECTIVES_HEADER_Y), 18, colors.TEXT)
        self._draw_objectives(surface)

        self.buttons.draw(surface)

    def _draw_objectives(self, surface: pygame.Surface) -> None:
        # Each objective can wrap onto more than one line depending on its
        # own length, so the next objective's y has to advance by however
        # many lines this one actually took - a fixed per-objective spacing
        # would let a long one overlap the next.
        loc = self.app.localization
        font = get_font(OBJECTIVE_FONT_SIZE)
        line_height = font.get_linesize() + OBJECTIVE_LINE_SPACING
        y = FIRST_OBJECTIVE_Y
        for objective_key in self.definition.objective_keys:
            text = f"- {loc.t(objective_key)}"
            draw_wrapped_text(surface, text, (OBJECTIVE_LEFT_X, y), OBJECTIVE_MAX_WIDTH, OBJECTIVE_FONT_SIZE, colors.TEXT)
            line_count = len(wrap_text(text, font, OBJECTIVE_MAX_WIDTH))
            y += line_count * line_height + OBJECTIVE_GAP
