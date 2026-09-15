from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.timeseries import LensOption, TimeSeries, TimeSeriesChoices, TimeSeriesRequest, is_weekend
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.category_chart import draw_line_chart
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 72
PROMPT_MAX_WIDTH = 820
LENS_OPTION_SIZE = (380, 38)
LENS_OPTION_Y = 112
CHART_RECT = pygame.Rect(70, 145, 820, 165)
WEEK_LABEL_Y = CHART_RECT.bottom + 14
SUMMARY_Y = 338
SUMMARY_LINE_SPACING = 20
HINT_Y = 385
NAV_BUTTON_Y = 460
VALUE_PADDING = 0.02


class TimeSeriesScene(Scene):
    """A persistent daily line chart: a fixed current-period series is
    always visible, with weekend columns always shaded so calendar rhythm
    reads at a glance regardless of which claim is active. A fixed
    sequence of requests each poses a claim about specific highlighted
    days; picking "the same days, previous period" overlays a second,
    dimmer line at those same days so a real effect (the line actually
    shifts) looks different from ordinary calendar noise (the lines land
    on top of each other). The full chart is already real and inspectable
    before commit - a motivated-reasoning trap, not a hidden-information
    one, matching FunnelBuilderScene's/CohortMatrixScene's own established
    reasoning.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split.

    `initial_choices`, when given, seeds `self.choices` - the same "seed
    the starting state, let the student freely revise before committing"
    idiom FunnelBuilderScene's/CohortMatrixScene's own `initial_choices`
    already established.

    `context`/`mirror_python_code_for`, when both given, record one real
    `AnalyticalAction` (Python Mirror only, never `EvidenceItem`) per
    request, in `_next()`, right before advancing past it - the identical
    action-only discipline the shared pick scenes already established and
    for the identical reason: evidence recorded conditional on "the
    current pick is correct" would leave a stale correct `EvidenceItem`
    behind after a later Back-revision to a wrong pick. Real Evidence
    should come from a real reveal that fires exactly once, never from
    here. `mirror_python_code_for(request, option, var_name) -> str` is
    injected rather than imported directly, keeping this shared UI scene
    ignorant of any one lesson's own dataset/column names - it takes the
    REQUEST too (not just the option, unlike Funnel's/Cohort's 2-arg
    shape), since `highlight_days` lives on the request here, not the
    option."""

    def __init__(
        self,
        app,
        title_key: str,
        current_period: TimeSeries,
        previous_period: TimeSeries,
        requests: tuple[TimeSeriesRequest, ...],
        on_complete: Callable[[TimeSeriesChoices], None],
        guided: bool = True,
        current_period_label_key: str = "timeseries.current_period_label",
        previous_period_label_key: str = "timeseries.previous_period_label",
        week_label_key: str = "timeseries.week_label",
        context: LessonContext | None = None,
        initial_choices: TimeSeriesChoices | None = None,
        mirror_python_code_for: Callable[[TimeSeriesRequest, LensOption, str], str] | None = None,
        mirror_action_label_key: str = "timeseries.picked_lens_action_label",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.current_period = current_period
        self.previous_period = previous_period
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.current_period_label_key = current_period_label_key
        self.previous_period_label_key = previous_period_label_key
        self.week_label_key = week_label_key
        self.context = context
        self.mirror_python_code_for = mirror_python_code_for
        self.mirror_action_label_key = mirror_action_label_key
        self.request_index = 0
        self.choices: TimeSeriesChoices = dict(initial_choices) if initial_choices is not None else {}

        all_values = [point.value for point in current_period.points] + [point.value for point in previous_period.points]
        self.min_value = max(0.0, min(all_values) - VALUE_PADDING)
        self.max_value = max(all_values) + VALUE_PADDING

        self._rebuild_buttons()

    def _current_request(self) -> TimeSeriesRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _selected_option(self, request: TimeSeriesRequest) -> LensOption | None:
        option_key = self.choices.get(request.key)
        if option_key is None:
            return None
        return next(option for option in request.options if option.key == option_key)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        request = self._current_request()
        buttons = []
        count = len(request.options)
        for index, option in enumerate(request.options):
            rect = pygame.Rect(0, 0, *LENS_OPTION_SIZE)
            spacing = LENS_OPTION_SIZE[0] + 20
            rect.center = (CENTER_X + (index - (count - 1) / 2) * spacing, LENS_OPTION_Y)
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
        request = self._current_request()
        if request.key not in self.choices:
            return
        if self.context is not None and self.mirror_python_code_for is not None:
            option = self._selected_option(request)
            var_name = f"{request.key}_lens"
            self.context.record_action(
                label_key=self.mirror_action_label_key,
                python_code=self.mirror_python_code_for(request, option, var_name),
                key=f"timeseries_pick_{request.key}",
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

    def _day_rect(self, index: int) -> pygame.Rect:
        count = len(self.current_period.points)
        slice_width = CHART_RECT.width / count
        left = CHART_RECT.left + round(slice_width * index)
        right = CHART_RECT.left + round(slice_width * (index + 1))
        return pygame.Rect(left, CHART_RECT.top, right - left, CHART_RECT.height)

    def _draw_chart(self, surface: pygame.Surface, request: TimeSeriesRequest) -> None:
        loc = self.app.localization
        option = self._selected_option(request)
        show_previous = option.show_previous_period if option is not None else False

        for index, point in enumerate(self.current_period.points):
            if is_weekend(point.day):
                pygame.draw.rect(surface, colors.PANEL_BACKGROUND, self._day_rect(index))

        highlighted_indexes = [index for index, point in enumerate(self.current_period.points) if point.day in request.highlight_days]
        if highlighted_indexes:
            left = min(self._day_rect(index).left for index in highlighted_indexes)
            right = max(self._day_rect(index).right for index in highlighted_indexes)
            band = pygame.Rect(left, CHART_RECT.top, right - left, CHART_RECT.height)
            pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, band, width=2, border_radius=4)

        current_values = [point.value for point in self.current_period.points]
        draw_line_chart(surface, CHART_RECT, current_values, self.min_value, self.max_value, colors.TEXT)
        if show_previous:
            previous_values = [point.value for point in self.previous_period.points]
            draw_line_chart(surface, CHART_RECT, previous_values, self.min_value, self.max_value, colors.BUTTON_TEXT_DISABLED)

        week_count = len(self.current_period.points) // 7
        for week_index in range(week_count):
            start = week_index * 7
            end = min(start + 6, len(self.current_period.points) - 1)
            x = (self._day_rect(start).centerx + self._day_rect(end).centerx) // 2
            label = f"{loc.t(self.week_label_key)} {week_index + 1}"
            draw_centered_text(surface, label, (x, WEEK_LABEL_Y), 13, colors.BUTTON_TEXT_DISABLED)

        self._draw_summary(surface, request, show_previous)

    def _average(self, series: TimeSeries, days: tuple[int, ...]) -> float:
        values = [point.value for point in series.points if point.day in days]
        return sum(values) / len(values)

    def _draw_summary(self, surface: pygame.Surface, request: TimeSeriesRequest, show_previous: bool) -> None:
        loc = self.app.localization
        current_avg = self._average(self.current_period, request.highlight_days)
        text = f"{loc.t(self.current_period_label_key)}: {current_avg:.0%}"
        draw_centered_text(surface, text, (CENTER_X, SUMMARY_Y), 16, colors.TEXT)
        if show_previous:
            previous_avg = self._average(self.previous_period, request.highlight_days)
            text = f"{loc.t(self.previous_period_label_key)}: {previous_avg:.0%}"
            draw_centered_text(surface, text, (CENTER_X, SUMMARY_Y + SUMMARY_LINE_SPACING), 16, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicator(self, surface: pygame.Surface, request: TimeSeriesRequest) -> None:
        selected_key = self.choices.get(request.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(request.options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)
