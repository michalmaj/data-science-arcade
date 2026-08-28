from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.funnel import FunnelChoices, FunnelDefinition, FunnelRequest
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.funnel_chart import draw_funnel_bar, step_percent, step_percent_of_top
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 74
PROMPT_MAX_WIDTH = 820
DEFINITION_OPTION_SIZE = (360, 40)
DEFINITION_OPTION_Y = 128
CHART_TOP = 178
ROW_HEIGHT = 45
LABEL_X = 50
LABEL_MAX_WIDTH = 210
BAR_RECT = pygame.Rect(270, 0, 380, 30)
VALUE_X = 830
HINT_Y = 400
NAV_BUTTON_Y = 460


class FunnelBuilderScene(Scene):
    """A fixed sequence of requests, each a specific complaint about
    checkout conversion; picking one of a few candidate funnel
    *definitions* (spec §25 Lesson 21 'Funnel Factory') shows a real
    funnel chart for that definition - same underlying event counts,
    different choices about which events count, in what order, or
    against which denominator. Different defensible-looking definitions
    can make different steps look like the worst bottleneck, which is the
    whole point: the chart is real either way, but which one you pick
    still shapes the story it tells.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        requests: tuple[FunnelRequest, ...],
        on_complete: Callable[[FunnelChoices], None],
        guided: bool = True,
        pick_hint_key: str = "funnel.pick_a_definition_hint",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.pick_hint_key = pick_hint_key
        self.request_index = 0
        self.choices: FunnelChoices = {}
        self._rebuild_buttons()

    def _current_request(self) -> FunnelRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _selected_definition(self, request: FunnelRequest) -> FunnelDefinition | None:
        definition_key = self.choices.get(request.key)
        if definition_key is None:
            return None
        return next(definition for definition in request.definitions if definition.key == definition_key)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        request = self._current_request()
        buttons = []
        count = len(request.definitions)
        for index, definition in enumerate(request.definitions):
            rect = pygame.Rect(0, 0, *DEFINITION_OPTION_SIZE)
            spacing = DEFINITION_OPTION_SIZE[0] + 20
            rect.center = (CENTER_X + (index - (count - 1) / 2) * spacing, DEFINITION_OPTION_Y)
            buttons.append(Button(rect, loc.t(definition.label_key), self._make_choose(definition.key)))

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

    def _make_choose(self, definition_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choices[self._current_request().key] = definition_key
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

        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, 16, colors.TEXT)
        self._draw_chart(surface, request)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, request)

        if self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_chart(self, surface: pygame.Surface, request: FunnelRequest) -> None:
        loc = self.app.localization
        definition = self._selected_definition(request)
        if definition is None:
            draw_centered_text(surface, loc.t(self.pick_hint_key), (CENTER_X, CHART_TOP + 20), 15, colors.BUTTON_TEXT_DISABLED)
            return

        for index, step in enumerate(definition.steps):
            y = CHART_TOP + index * ROW_HEIGHT
            row_rect = BAR_RECT.copy()
            row_rect.centery = y

            draw_wrapped_text(surface, loc.t(step.label_key), (LABEL_X, y - 14), LABEL_MAX_WIDTH, 15, colors.TEXT)
            fraction_of_top = step_percent_of_top(definition.steps, index)
            draw_funnel_bar(surface, row_rect, fraction_of_top, colors.BUTTON_FOCUS_BORDER)

            shown_percent = step_percent(definition.steps, index, definition.percent_basis)
            value_text = f"{step.count:,} ({shown_percent:.0%})"
            draw_centered_text(surface, value_text, (VALUE_X, y), 15, colors.TEXT)

    def _draw_selected_indicator(self, surface: pygame.Surface, request: FunnelRequest) -> None:
        selected_key = self.choices.get(request.key)
        if selected_key is None:
            return
        selected_index = next(i for i, definition in enumerate(request.definitions) if definition.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)
