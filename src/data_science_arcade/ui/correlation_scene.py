from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.correlation import CorrelationChoices, CorrelationRequest, VerdictOption
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 72
PROMPT_MAX_WIDTH = 820
EVIDENCE_RECT = pygame.Rect(60, 96, 840, 92)
OPTION_SIZE = (760, 40)
FIRST_OPTION_Y = 224
OPTION_SPACING = 46
EXPLANATION_Y = 358
EXPLANATION_MAX_WIDTH = 820
HINT_Y = 420
NAV_BUTTON_Y = 470


class CorrelationScene(Scene):
    """Weigh a real correlation against candidate causal stories (spec §25
    Lesson 26 'Correlation Crime Scene'): a persistent evidence panel shows
    the actual computed correlation, sample size, and one additional fact
    that rules some explanations out - then the player picks one of a
    small set of complete verdicts (which explanations survive, which
    don't), rather than checking each explanation individually. Every pick
    shows its own real consequence text, right or wrong, same as every
    other stage scene's "see what actually follows" discipline.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        requests: tuple[CorrelationRequest, ...],
        on_complete: Callable[[CorrelationChoices], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.request_index = 0
        self.choices: CorrelationChoices = {}
        self._rebuild_buttons()

    def _current_request(self) -> CorrelationRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _selected_option(self, request: CorrelationRequest) -> VerdictOption | None:
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
        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, 16, colors.TEXT)

        self._draw_evidence_panel(surface, request)
        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, request)
        self._draw_explanation(surface, request)

        if self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_evidence_panel(self, surface: pygame.Surface, request: CorrelationRequest) -> None:
        loc = self.app.localization
        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, EVIDENCE_RECT, border_radius=8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, EVIDENCE_RECT, width=1, border_radius=8)

        metrics_line = f"{loc.t(request.metric_a_label_key)}  vs.  {loc.t(request.metric_b_label_key)}"
        stats_line = f"{loc.t('correlation.correlation_label')}: {request.correlation:.2f}   {loc.t('correlation.sample_size_label')}: {request.sample_size}"
        draw_centered_text(surface, metrics_line, (CENTER_X, EVIDENCE_RECT.top + 16), 16, colors.TEXT)
        draw_centered_text(surface, stats_line, (CENTER_X, EVIDENCE_RECT.top + 38), 15, colors.BUTTON_FOCUS_BORDER)
        draw_centered_wrapped_text(surface, loc.t(request.evidence_key), (CENTER_X, EVIDENCE_RECT.top + 64), EVIDENCE_RECT.width - 40, 14, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicator(self, surface: pygame.Surface, request: CorrelationRequest) -> None:
        selected_key = self.choices.get(request.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(request.options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_explanation(self, surface: pygame.Surface, request: CorrelationRequest) -> None:
        loc = self.app.localization
        option = self._selected_option(request)
        if option is None:
            return
        draw_centered_wrapped_text(surface, loc.t(option.explanation_key), (CENTER_X, EXPLANATION_Y), EXPLANATION_MAX_WIDTH, 15, colors.TEXT)
