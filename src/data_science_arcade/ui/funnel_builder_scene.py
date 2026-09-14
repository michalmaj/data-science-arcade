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
from data_science_arcade.workbench.context import LessonContext

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
    *definitions* shows a real funnel chart for that definition - same
    underlying counted-event totals, different choices about which
    events count, in what order, or against which denominator. Different
    defensible-looking definitions can make different steps look like the
    worst bottleneck, which is the whole point: the chart is real either
    way, but which one you pick still shapes the story it tells.

    `guided` still exists as a plain hint toggle (matching every other
    stage scene's own `guided` param), but a lesson built around a real
    motivated-reasoning trap - picking whichever definition happens to
    confirm a complaint, rather than the one independently defensible -
    will usually want `guided=False` throughout: a hint naming what to
    check would hand the student the trap's own resolution before they
    fall into it.

    `initial_choices`, when given, seeds `self.choices` - the same "seed
    the starting state, let the student freely revise before committing"
    idiom `PowerPlannerScene.initial_weeks` already established. Lets one
    lesson run this scene twice: once cold, once again seeded with the
    first pass's own picks after a real intervening reveal, so a
    student's own initial motivated-reasoning trap becomes something they
    can actually act on, not something that permanently caps a later
    score.

    `context`/`mirror_python_code_for`, when both given, record one real
    `AnalyticalAction` (Python Mirror only, never `EvidenceItem` - see
    below) per request, in `_next()`, right before advancing past it.
    Deliberately never records Evidence directly: since `_next()` only
    fires when leaving a request forward, evidence recorded conditional
    on "the current pick is correct" would leave a stale correct
    `EvidenceItem` behind after a later Back-revision to a wrong pick
    (`LessonContext` has no evidence-removal path, only update-by-key).
    Real Evidence should come from a real reveal that fires exactly once,
    after all requests are locked in for that pass - never from here.
    `mirror_python_code_for(definition, var_name) -> str` is injected
    rather than imported directly, keeping this shared UI scene ignorant
    of any one lesson's own dataset/column names."""

    def __init__(
        self,
        app,
        title_key: str,
        requests: tuple[FunnelRequest, ...],
        on_complete: Callable[[FunnelChoices], None],
        guided: bool = True,
        pick_hint_key: str = "funnel.pick_a_definition_hint",
        context: LessonContext | None = None,
        initial_choices: FunnelChoices | None = None,
        mirror_python_code_for: Callable[[FunnelDefinition, str], str] | None = None,
        mirror_action_label_key: str = "funnel.picked_definition_action_label",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.pick_hint_key = pick_hint_key
        self.context = context
        self.mirror_python_code_for = mirror_python_code_for
        self.mirror_action_label_key = mirror_action_label_key
        self.request_index = 0
        self.choices: FunnelChoices = dict(initial_choices) if initial_choices is not None else {}
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
        request = self._current_request()
        if request.key not in self.choices:
            return
        if self.context is not None and self.mirror_python_code_for is not None:
            definition = self._selected_definition(request)
            var_name = f"{request.key}_funnel"
            self.context.record_action(
                label_key=self.mirror_action_label_key,
                python_code=self.mirror_python_code_for(definition, var_name),
                key=f"funnel_pick_{request.key}",
            )
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
