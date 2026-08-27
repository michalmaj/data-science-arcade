from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.chart import ChartChoices, ChartOption, ChartRequest
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.category_chart import category_x, draw_bar_chart, draw_line_chart, value_to_y
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
CHART_RECT = pygame.Rect(150, 68, 660, 168)
CATEGORY_LABEL_Y = CHART_RECT.bottom + 8
PROMPT_Y = CATEGORY_LABEL_Y + 30
PROMPT_SIZE = 18
PROMPT_MAX_WIDTH = 820
OPTION_SIZE = (420, 40)
FIRST_OPTION_Y = PROMPT_Y + 40
OPTION_SPACING = 44
HINT_Y = 452
NAV_BUTTON_Y = 495


class ChartDesignerScene(Scene):
    """Build a chart for a stakeholder's question (spec §25 Lesson 14
    'Chart Designer'): a fixed sequence of requests, each with its own
    small category series, offers a few complete chart 'recipes' (chart
    type + axis scale) as one combined pick - not five independent
    sliders - and redraws the actual chart from real data the moment one
    is chosen, rather than describing the effect in text alone. A zoomed
    bar-chart scale visibly exaggerates the same real gap a zero-based
    one shows honestly.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        requests: tuple[ChartRequest, ...],
        on_complete: Callable[[ChartChoices], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.request_index = 0
        self.choices: ChartChoices = {}
        self._rebuild_buttons()

    def _current_request(self) -> ChartRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _selected_option(self, request: ChartRequest) -> ChartOption | None:
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

        self._draw_chart(surface, request)
        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, request)

        if self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _chart_range(self, option: ChartOption, values: tuple[float, ...]) -> tuple[float, float]:
        if option.chart_type == "bar" and option.scale == "zoomed":
            return min(values) * 0.9, max(values) * 1.05
        return 0.0, max(values) * 1.15

    def _draw_chart(self, surface: pygame.Surface, request: ChartRequest) -> None:
        loc = self.app.localization
        option = self._selected_option(request)
        if option is None:
            draw_centered_text(surface, loc.t("lesson.l14.pick_a_chart_hint"), (CENTER_X, CHART_RECT.centery), 15, colors.BUTTON_TEXT_DISABLED)
            return

        min_value, max_value = self._chart_range(option, request.values)
        values = list(request.values)
        if option.chart_type == "line":
            draw_line_chart(surface, CHART_RECT, values, min_value, max_value, colors.BUTTON_FOCUS_BORDER)
        else:
            draw_bar_chart(surface, CHART_RECT, values, min_value, max_value, colors.TEXT)

        for index, (category, value) in enumerate(zip(request.categories, request.values)):
            x = category_x(index, len(request.categories), CHART_RECT)
            draw_centered_text(surface, category, (x, CATEGORY_LABEL_Y), 13, colors.BUTTON_TEXT_DISABLED)
            label_y = value_to_y(value, min_value, max_value, CHART_RECT) - 12
            draw_centered_text(surface, f"{value:,.0f}", (x, label_y), 12, colors.BUTTON_TEXT_DISABLED)

        draw_centered_text(surface, f"{min_value:,.0f}", (CHART_RECT.left - 8, CHART_RECT.bottom), 12, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, f"{max_value:,.0f}", (CHART_RECT.left - 8, CHART_RECT.top), 12, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicator(self, surface: pygame.Surface, request: ChartRequest) -> None:
        selected_key = self.choices.get(request.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(request.options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)
