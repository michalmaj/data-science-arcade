from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.api import APIRequestAttempt
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_single_line, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
LOG_RECT = pygame.Rect(80, 140, 800, 190)
LOG_ROW_HEIGHT = 24
LOG_MAX_ROWS = 7
COUNTER_Y = 350
ACTION_BUTTON_Y = 420
HINT_Y = 460


class APIConsoleScene(Scene):
    """Steps through a pre-scripted request log one click at a time (spec
    §25 Lesson 03 'API Courier'): each click plays the next APIRequestAttempt
    - success or failure, full or partial - into a running log and updates
    the collected-records count. Finish (Confirm) only appears once every
    attempt has played. guided=True shows a general hint about what to
    watch for in each response; guided=False hides it."""

    def __init__(
        self,
        app,
        title_key: str,
        endpoint_key: str,
        attempts: tuple[APIRequestAttempt, ...],
        on_complete: Callable[[int], None],
        guided: bool = True,
        hint_key: str | None = None,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.endpoint_key = endpoint_key
        self.attempts = attempts
        self.on_complete = on_complete
        self.guided = guided
        self.hint_key = hint_key
        self.log: list[APIRequestAttempt] = []
        self._rebuild_buttons()

    def _all_sent(self) -> bool:
        return len(self.log) >= len(self.attempts)

    def total_records(self) -> int:
        return sum(attempt.records_returned for attempt in self.log if attempt.is_success)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        rect = pygame.Rect(0, 0, 240, 48)
        rect.center = (CENTER_X, ACTION_BUTTON_Y)
        if self._all_sent():
            self.action_button = Button(rect, loc.t("api_console.finish"), self._finish)
        else:
            self.action_button = Button(rect, loc.t("api_console.send_request"), self._send_request)
        self.buttons = ButtonGroup([self.action_button])

    def _send_request(self) -> None:
        if self._all_sent():
            return
        self.log.append(self.attempts[len(self.log)])
        self._rebuild_buttons()

    def _finish(self) -> None:
        if not self._all_sent():
            return
        self.on_complete(self.total_records())

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 50), 28, colors.TEXT)
        draw_centered_text(surface, loc.t(self.endpoint_key), (CENTER_X, 90), 16, colors.BUTTON_TEXT_DISABLED)

        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, LOG_RECT, border_radius=8)
        self._draw_log(surface)

        counter_text = f"{loc.t('api_console.records_collected')} {self.total_records()}"
        draw_centered_text(surface, counter_text, (CENTER_X, COUNTER_Y), 18, colors.BUTTON_FOCUS_BORDER)

        self.buttons.draw(surface)

        if self.guided and self.hint_key:
            draw_wrapped_text(surface, loc.t(self.hint_key), (CENTER_X - 380, HINT_Y), 760, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_log(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        left = LOG_RECT.left + 20
        width = LOG_RECT.width - 40
        shown = self.log[-LOG_MAX_ROWS:]
        for index, attempt in enumerate(shown):
            y = LOG_RECT.top + 12 + index * LOG_ROW_HEIGHT
            page_label = f"{loc.t('api_console.page_label')} {attempt.page_number}"
            status_text = loc.t(attempt.status_key)
            records_text = f"{attempt.records_returned} {loc.t('api_console.records_suffix')}"
            color = colors.TEXT if attempt.is_success else colors.BUTTON_TEXT_DISABLED
            line = f"{page_label} - {status_text} - {records_text}"
            draw_single_line(surface, line, (left, y), width, 15, color)
