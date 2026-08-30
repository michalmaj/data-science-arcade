from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.lessons.framework.alerting import MetricOption, MonitoringChoices, MonitoringRequest, ThresholdOption
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 90
PROMPT_SIZE = 18
PROMPT_MAX_WIDTH = 820
LEFT_COLUMN_X = 260
RIGHT_COLUMN_X = 700
COLUMN_LABEL_Y = 130
OPTION_SIZE = (280, 40)
FIRST_OPTION_Y = 165
OPTION_SPACING = 48
RESULT_RECT = pygame.Rect(230, 300, 500, 90)
HINT_Y = 420
NAV_BUTTON_Y = 470


class AlertConfigScene(Scene):
    """Assemble a monitoring setup from two independent choices (spec §25
    Lesson 25 'KPI Emergency Room'): which metric to treat as the north
    star and how tight its alert threshold should be, picked from two
    independent button columns - the same "two categories of choice, live
    combined consequence" shape Survey Bureau's SurveyBuilderScene uses,
    but the live consequence here is a false-alarm count plus whether the
    scenario's real incident was actually caught (via the injected
    `simulate` callable), not a respondent count and an average - a
    different enough result shape to be its own scene.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split.

    false_alarm_count_label_key defaults to Lesson 25's own "over 14 days"
    wording - baked in as a literal default rather than a true constant,
    since Lesson 25 was this scene's only caller until Lesson 30's own
    8-week dataset needed different wording for the same number."""

    def __init__(
        self,
        app,
        title_key: str,
        dataset: Dataset,
        requests: tuple[MonitoringRequest, ...],
        simulate: Callable[[Dataset, MetricOption, ThresholdOption, int], tuple[int, bool]],
        on_complete: Callable[[MonitoringChoices], None],
        guided: bool = True,
        metric_label_key: str = "alerting.metric_label",
        threshold_label_key: str = "alerting.threshold_label",
        false_alarm_count_label_key: str = "alerting.false_alarm_count_label",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.dataset = dataset
        self.requests = requests
        self.simulate = simulate
        self.on_complete = on_complete
        self.guided = guided
        self.metric_label_key = metric_label_key
        self.threshold_label_key = threshold_label_key
        self.false_alarm_count_label_key = false_alarm_count_label_key
        self.request_index = 0
        self.choices: MonitoringChoices = {}
        self._metric_choice: str | None = None
        self._threshold_choice: str | None = None
        self._load_pending_choice()
        self._rebuild_buttons()

    def _current_request(self) -> MonitoringRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _load_pending_choice(self) -> None:
        # Only called when switching requests (init/back/next) - a lone
        # metric or threshold pick isn't committed to self.choices until
        # both sides are chosen, so rebuilding buttons after a single pick
        # must NOT reset that still-pending pick back to None.
        existing = self.choices.get(self._current_request().key)
        self._metric_choice = existing[0] if existing else None
        self._threshold_choice = existing[1] if existing else None

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        request = self._current_request()

        buttons = []
        for index, option in enumerate(request.metric_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (LEFT_COLUMN_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose_metric(option.key)))
        for index, option in enumerate(request.threshold_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (RIGHT_COLUMN_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose_threshold(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.request_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_request() else loc.t("brief.next")
        both_chosen = self._metric_choice is not None and self._threshold_choice is not None
        self.next_button = Button(next_rect, next_label, self._next, enabled=both_chosen)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose_metric(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._metric_choice = option_key
            self._commit_if_complete()
            self._rebuild_buttons()

        return choose

    def _make_choose_threshold(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._threshold_choice = option_key
            self._commit_if_complete()
            self._rebuild_buttons()

        return choose

    def _commit_if_complete(self) -> None:
        if self._metric_choice is not None and self._threshold_choice is not None:
            self.choices[self._current_request().key] = (self._metric_choice, self._threshold_choice)

    def _back(self) -> None:
        if self.request_index > 0:
            self.request_index -= 1
            self._load_pending_choice()
            self._rebuild_buttons()

    def _next(self) -> None:
        if self._current_request().key not in self.choices:
            return
        if self._is_last_request():
            self.on_complete(dict(self.choices))
            return
        self.request_index += 1
        self._load_pending_choice()
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def _selected_metric(self, request: MonitoringRequest) -> MetricOption | None:
        if self._metric_choice is None:
            return None
        return next(option for option in request.metric_options if option.key == self._metric_choice)

    def _selected_threshold(self, request: MonitoringRequest) -> ThresholdOption | None:
        if self._threshold_choice is None:
            return None
        return next(option for option in request.threshold_options if option.key == self._threshold_choice)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        request = self._current_request()

        progress = f"{self.request_index + 1} / {len(self.requests)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)

        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        draw_centered_text(surface, loc.t(self.metric_label_key), (LEFT_COLUMN_X, COLUMN_LABEL_Y), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.threshold_label_key), (RIGHT_COLUMN_X, COLUMN_LABEL_Y), 16, colors.BUTTON_TEXT_DISABLED)

        self.buttons.draw(surface)
        self._draw_selected_indicators(surface, request)
        self._draw_result_preview(surface, request)

        if self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicators(self, surface: pygame.Surface, request: MonitoringRequest) -> None:
        for option, choice_key in (
            (self._selected_metric(request), self._metric_choice),
            (self._selected_threshold(request), self._threshold_choice),
        ):
            if option is None:
                continue
            all_options = request.metric_options if option in request.metric_options else request.threshold_options
            index = next(i for i, candidate in enumerate(all_options) if candidate.key == choice_key)
            button_index = index if all_options is request.metric_options else len(request.metric_options) + index
            rect = self.buttons.buttons[button_index].rect
            marker = pygame.Rect(rect.left, rect.top + 4, 4, rect.height - 8)
            pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_result_preview(self, surface: pygame.Surface, request: MonitoringRequest) -> None:
        loc = self.app.localization
        metric = self._selected_metric(request)
        threshold = self._selected_threshold(request)
        if metric is None or threshold is None:
            draw_centered_text(surface, loc.t("alerting.pick_both_hint"), (CENTER_X, RESULT_RECT.top + 20), 15, colors.BUTTON_TEXT_DISABLED)
            return

        false_alarm_count, incident_caught = self.simulate(self.dataset, metric, threshold, request.target_incident_day)
        caught_text = loc.t("alerting.yes") if incident_caught else loc.t("alerting.no")
        count_line = f"{loc.t(self.false_alarm_count_label_key)}: {false_alarm_count}"
        caught_line = f"{loc.t('alerting.incident_caught_label')}: {caught_text}"
        draw_centered_text(surface, count_line, (CENTER_X, RESULT_RECT.top + 20), 18, colors.TEXT)
        draw_centered_text(surface, caught_line, (CENTER_X, RESULT_RECT.top + 52), 18, colors.BUTTON_FOCUS_BORDER)
