from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.segment import SegmentChoices, SegmentRequest, SliceOption
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 78
PROMPT_SIZE = 18
PROMPT_MAX_WIDTH = 820
TABLE_TOP = 130
TABLE_ROW_HEIGHT = 26
SEGMENT_COLUMN_X = CENTER_X - 140
BEFORE_COLUMN_X = CENTER_X + 40
AFTER_COLUMN_X = CENTER_X + 160
OPTION_SIZE = (420, 40)
FIRST_OPTION_Y = 260
OPTION_SPACING = 44
HINT_Y = 400
NAV_BUTTON_Y = 460


class SegmentSlicerScene(Scene):
    """A fixed sequence of requests, each offering a few options; picking
    one shows a real before/after table for that option's own rows -
    originally built to slice a company-wide metric by a chosen dimension
    (spec §25 Lesson 15 'Segment Detective', where each row is a
    demographic segment like device or region), and reused as-is for
    Lesson 16 'Metric Forge' (where each row is a tracked metric - primary
    or guardrail - instead of a segment). "Segment" in the framework
    dataclasses (`lessons/framework/segment.py`) means "a row this table
    compares," not specifically a demographic slice.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        requests: tuple[SegmentRequest, ...],
        on_complete: Callable[[SegmentChoices], None],
        guided: bool = True,
        row_column_label_key: str = "lesson.l15.segment_column_label",
        before_column_label_key: str = "lesson.l15.before_column_label",
        after_column_label_key: str = "lesson.l15.after_column_label",
        pick_hint_key: str = "lesson.l15.pick_a_slice_hint",
        value_format: Callable[[float], str] = lambda value: f"{value:.0%}",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.row_column_label_key = row_column_label_key
        self.before_column_label_key = before_column_label_key
        self.after_column_label_key = after_column_label_key
        self.pick_hint_key = pick_hint_key
        self.value_format = value_format
        self.request_index = 0
        self.choices: SegmentChoices = {}
        self._rebuild_buttons()

    def _current_request(self) -> SegmentRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _selected_option(self, request: SegmentRequest) -> SliceOption | None:
        option_key = self.choices.get(request.key)
        if option_key is None:
            return None
        return next(option for option in request.options if option.key == option_key)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        request = self._current_request()
        buttons = []
        for index, option in enumerate(request.options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.request_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_request() else loc.t("brief.next")
        self.next_button = Button(next_rect, next_label, self._next, enabled=request.key in self.choices)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choices[self._current_request().key] = option_key
            self._rebuild_buttons()

        return choose

    def _back(self) -> None:
        if self.request_index > 0:
            self.request_index -= 1
            self._rebuild_buttons()

    def _next(self) -> None:
        if self._current_request().key not in self.choices:
            return
        if self._is_last_request():
            self.on_complete(dict(self.choices))
            return
        self.request_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        request = self._current_request()

        progress = f"{self.request_index + 1} / {len(self.requests)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)

        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)
        self._draw_table(surface, request)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, request)

        if self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_table(self, surface: pygame.Surface, request: SegmentRequest) -> None:
        loc = self.app.localization
        option = self._selected_option(request)
        if option is None:
            draw_centered_text(surface, loc.t(self.pick_hint_key), (CENTER_X, TABLE_TOP + 20), 15, colors.BUTTON_TEXT_DISABLED)
            return

        header_y = TABLE_TOP
        draw_centered_text(surface, loc.t(self.row_column_label_key), (SEGMENT_COLUMN_X, header_y), 14, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.before_column_label_key), (BEFORE_COLUMN_X, header_y), 14, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.after_column_label_key), (AFTER_COLUMN_X, header_y), 14, colors.BUTTON_TEXT_DISABLED)

        for index, segment in enumerate(option.segments):
            y = header_y + (index + 1) * TABLE_ROW_HEIGHT
            declined = segment.after_rate < segment.before_rate
            value_color = colors.BUTTON_FOCUS_BORDER if declined else colors.TEXT
            draw_centered_text(surface, loc.t(segment.label_key), (SEGMENT_COLUMN_X, y), 15, colors.TEXT)
            draw_centered_text(surface, self.value_format(segment.before_rate), (BEFORE_COLUMN_X, y), 15, value_color)
            draw_centered_text(surface, self.value_format(segment.after_rate), (AFTER_COLUMN_X, y), 15, value_color)

    def _draw_selected_indicator(self, surface: pygame.Surface, request: SegmentRequest) -> None:
        selected_key = self.choices.get(request.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(request.options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)
