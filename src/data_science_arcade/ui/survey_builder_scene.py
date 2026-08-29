from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.lessons.framework.survey import ChannelOption, SurveyChoices, SurveyRequest, WordingOption
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


class SurveyBuilderScene(Scene):
    """Assemble a survey from two independent choices (spec §25 Lesson 24
    'Survey Bureau'): a question wording and a recruitment channel, picked
    from two independent button columns - the same "two categories of
    choice, live combined consequence" shape GroupBy Kitchen's
    PipelineBuilderScene uses, but the live consequence here is a
    simulated respondent count and recorded average (via the injected
    `simulate` callable) rather than a grouped table, so it's its own
    scene rather than a literal reuse of that one.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        dataset: Dataset,
        requests: tuple[SurveyRequest, ...],
        simulate: Callable[[Dataset, ChannelOption, WordingOption], tuple[int, float]],
        on_complete: Callable[[SurveyChoices], None],
        guided: bool = True,
        wording_label_key: str = "survey.wording_label",
        channel_label_key: str = "survey.channel_label",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.dataset = dataset
        self.requests = requests
        self.simulate = simulate
        self.on_complete = on_complete
        self.guided = guided
        self.wording_label_key = wording_label_key
        self.channel_label_key = channel_label_key
        self.request_index = 0
        self.choices: SurveyChoices = {}
        self._wording_choice: str | None = None
        self._channel_choice: str | None = None
        self._load_pending_choice()
        self._rebuild_buttons()

    def _current_request(self) -> SurveyRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _load_pending_choice(self) -> None:
        # Only called when switching requests (init/back/next) - a lone
        # wording or channel pick isn't committed to self.choices until
        # both sides are chosen, so rebuilding buttons after a single pick
        # must NOT reset that still-pending pick back to None.
        existing = self.choices.get(self._current_request().key)
        self._wording_choice = existing[0] if existing else None
        self._channel_choice = existing[1] if existing else None

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        request = self._current_request()

        buttons = []
        for index, option in enumerate(request.wording_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (LEFT_COLUMN_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose_wording(option.key)))
        for index, option in enumerate(request.channel_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (RIGHT_COLUMN_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose_channel(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.request_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_request() else loc.t("brief.next")
        both_chosen = self._wording_choice is not None and self._channel_choice is not None
        self.next_button = Button(next_rect, next_label, self._next, enabled=both_chosen)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose_wording(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._wording_choice = option_key
            self._commit_if_complete()
            self._rebuild_buttons()

        return choose

    def _make_choose_channel(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._channel_choice = option_key
            self._commit_if_complete()
            self._rebuild_buttons()

        return choose

    def _commit_if_complete(self) -> None:
        if self._wording_choice is not None and self._channel_choice is not None:
            self.choices[self._current_request().key] = (self._wording_choice, self._channel_choice)

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

    def _selected_wording(self, request: SurveyRequest) -> WordingOption | None:
        if self._wording_choice is None:
            return None
        return next(option for option in request.wording_options if option.key == self._wording_choice)

    def _selected_channel(self, request: SurveyRequest) -> ChannelOption | None:
        if self._channel_choice is None:
            return None
        return next(option for option in request.channel_options if option.key == self._channel_choice)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        request = self._current_request()

        progress = f"{self.request_index + 1} / {len(self.requests)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)

        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        draw_centered_text(surface, loc.t(self.wording_label_key), (LEFT_COLUMN_X, COLUMN_LABEL_Y), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.channel_label_key), (RIGHT_COLUMN_X, COLUMN_LABEL_Y), 16, colors.BUTTON_TEXT_DISABLED)

        self.buttons.draw(surface)
        self._draw_selected_indicators(surface, request)
        self._draw_result_preview(surface, request)

        if self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicators(self, surface: pygame.Surface, request: SurveyRequest) -> None:
        for option, choice_key in (
            (self._selected_wording(request), self._wording_choice),
            (self._selected_channel(request), self._channel_choice),
        ):
            if option is None:
                continue
            all_options = request.wording_options if option in request.wording_options else request.channel_options
            index = next(i for i, candidate in enumerate(all_options) if candidate.key == choice_key)
            button_index = index if all_options is request.wording_options else len(request.wording_options) + index
            rect = self.buttons.buttons[button_index].rect
            marker = pygame.Rect(rect.left, rect.top + 4, 4, rect.height - 8)
            pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_result_preview(self, surface: pygame.Surface, request: SurveyRequest) -> None:
        loc = self.app.localization
        wording = self._selected_wording(request)
        channel = self._selected_channel(request)
        if wording is None or channel is None:
            draw_centered_text(surface, loc.t("survey.pick_both_hint"), (CENTER_X, RESULT_RECT.top + 20), 15, colors.BUTTON_TEXT_DISABLED)
            return

        respondent_count, mean_satisfaction = self.simulate(self.dataset, channel, wording)
        count_line = f"{loc.t('survey.respondent_count_label')}: {respondent_count}"
        average_line = f"{loc.t('survey.recorded_average_label')}: {mean_satisfaction:.0%}"
        draw_centered_text(surface, count_line, (CENTER_X, RESULT_RECT.top + 20), 18, colors.TEXT)
        draw_centered_text(surface, average_line, (CENTER_X, RESULT_RECT.top + 52), 18, colors.BUTTON_FOCUS_BORDER)
