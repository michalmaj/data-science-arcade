from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.source import DataSource
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text, wrap_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
COLUMN_SPACING = 300
COLUMN_WIDTH = 260
HEADER_SIZE = (240, 44)
HEADER_Y = 150
# Lesson 02 never has more than 3 sources, where the numbers above fit the
# 960px canvas comfortably. Lesson 07 needs 5 - narrower spacing/columns
# past that count, verified to still leave a clear gap between columns.
WIDE_COLUMN_SPACING = 170
WIDE_COLUMN_WIDTH = 150
WIDE_HEADER_WIDTH = 150
MANY_COLUMNS_THRESHOLD = 3
ATTRIBUTE_FIRST_Y = 200
ATTRIBUTE_TEXT_SIZE = 14
ATTRIBUTE_LINE_SPACING = 3
ATTRIBUTE_ROW_GAP = 10
"""Real fact text (e.g. "'Active' means: opened the app in 30 days") runs
far longer than the High/Medium/Low tags this board originally showed,
and can wrap past one line at WIDE_COLUMN_WIDTH - a fixed row height
would silently truncate it (caught only by a real screenshot, not by any
button-width test, since this is drawn via wrap-and-blit, not a Button).
Row height is computed per row from the tallest source's real wrapped
line count instead, matching WorkbenchScene._draw_schema's own "advance
by however many lines it actually wrapped to" principle - and shared
across the whole row (not per-column) so every source's Nth row still
starts at the same y, which a comparison board needs to stay scannable."""
HINT_Y = 360
CONFIRM_BUTTON_Y = 470


class SourceBoardScene(Scene):
    """A side-by-side comparison board (spec §25 Lesson 02 'Source Scout'):
    each DataSource is a column showing its trade-off attributes; pick one
    (doesn't auto-confirm, matching the brief builder's Confirm-not-click
    pattern) and confirm. guided=True also shows a general hint about how
    to weigh the trade-offs; guided=False hides it.

    `context`, when given, records the confirmed pick as a real
    AnalyticalAction (source.name_key, no python_code - this isn't a
    pandas operation, the same "record the choice even when it isn't
    code" precedent WorkbenchScene's own inspection_prompt already
    established) - never evidence, and never graded: an ungated read of
    "which source would you check first," useful later only as an
    observation of where the student started, not as part of any
    argument. Defaults to a fresh throwaway LessonContext, matching every
    other scene's `context: LessonContext | None = None` precedent, so
    every existing caller (which never passed one) is unaffected."""

    def __init__(
        self,
        app,
        title_key: str,
        prompt_key: str,
        sources: tuple[DataSource, ...],
        on_complete: Callable[[str], None],
        guided: bool = True,
        hint_key: str | None = None,
        context: LessonContext | None = None,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.prompt_key = prompt_key
        self.sources = sources
        self.on_complete = on_complete
        self.guided = guided
        self.hint_key = hint_key
        self.context = context if context is not None else LessonContext()
        self.selected_key: str | None = None
        self.source_buttons: dict[str, Button] = {}
        self._rebuild_buttons()

    def _column_spacing(self) -> int:
        return COLUMN_SPACING if len(self.sources) <= MANY_COLUMNS_THRESHOLD else WIDE_COLUMN_SPACING

    def _column_width(self) -> int:
        return COLUMN_WIDTH if len(self.sources) <= MANY_COLUMNS_THRESHOLD else WIDE_COLUMN_WIDTH

    def _header_width(self) -> int:
        return HEADER_SIZE[0] if len(self.sources) <= MANY_COLUMNS_THRESHOLD else WIDE_HEADER_WIDTH

    def _first_column_x(self) -> int:
        return CENTER_X - (len(self.sources) - 1) * self._column_spacing() // 2

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []
        self.source_buttons = {}
        first_x = self._first_column_x()
        spacing = self._column_spacing()
        for index, source in enumerate(self.sources):
            rect = pygame.Rect(0, 0, self._header_width(), HEADER_SIZE[1])
            rect.center = (first_x + index * spacing, HEADER_Y)
            button = Button(rect, loc.t(source.name_key), self._make_select(source.key))
            self.source_buttons[source.key] = button
            buttons.append(button)

        confirm_rect = pygame.Rect(0, 0, 220, 44)
        confirm_rect.center = (CENTER_X, CONFIRM_BUTTON_Y)
        self.confirm_button = Button(
            confirm_rect, loc.t("source_board.confirm"), self._confirm, enabled=self.selected_key is not None
        )
        buttons.append(self.confirm_button)

        self.buttons = ButtonGroup(buttons)

    def _make_select(self, key: str) -> Callable[[], None]:
        def select() -> None:
            self.selected_key = key
            self._rebuild_buttons()

        return select

    def _confirm(self) -> None:
        if self.selected_key is None:
            return
        source = next(s for s in self.sources if s.key == self.selected_key)
        self.context.record_action(label_key=source.name_key, key="source_board_pick")
        self.on_complete(self.selected_key)

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 50), 28, colors.TEXT)
        draw_centered_text(surface, loc.t(self.prompt_key), (CENTER_X, 90), 18, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface)
        self._draw_attributes(surface)

        if self.guided and self.hint_key:
            draw_wrapped_text(
                surface, loc.t(self.hint_key), (CENTER_X - 400, HINT_Y), 800, 15, colors.BUTTON_TEXT_DISABLED
            )

    def _draw_selected_indicator(self, surface: pygame.Surface) -> None:
        if self.selected_key is None:
            return
        rect = self.source_buttons[self.selected_key].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_attributes(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        first_x = self._first_column_x()
        spacing = self._column_spacing()
        column_width = self._column_width()
        font = get_font(ATTRIBUTE_TEXT_SIZE)
        line_height = font.get_linesize() + ATTRIBUTE_LINE_SPACING
        row_count = len(self.sources[0].attributes) if self.sources else 0

        y = ATTRIBUTE_FIRST_Y
        for row in range(row_count):
            texts = [
                f"{loc.t(source.attributes[row].label_key)}: {loc.t(source.attributes[row].rating_key)}"
                for source in self.sources
            ]
            max_lines = max((len(wrap_text(text, font, column_width)) for text in texts), default=1)
            for index, text in enumerate(texts):
                column_left = first_x + index * spacing - column_width // 2
                draw_wrapped_text(
                    surface, text, (column_left, y), column_width, ATTRIBUTE_TEXT_SIZE, colors.TEXT,
                    line_spacing=ATTRIBUTE_LINE_SPACING,
                )
            y += max_lines * line_height + ATTRIBUTE_ROW_GAP
