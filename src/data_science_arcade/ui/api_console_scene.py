from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.api import APIRequestAttempt
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_single_line, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
RESPONSE_RECT = pygame.Rect(60, 110, 380, 160)
LOG_RECT = pygame.Rect(520, 110, 380, 160)
PANEL_HEADER_GAP = 28
RESPONSE_LINE_HEIGHT = 22
LOG_ROW_HEIGHT = 22
LOG_MAX_ROWS = 5
COUNTER_Y = 300
SINGLE_ACTION_BUTTON_Y = 340
SINGLE_ACTION_BUTTON_SIZE = (240, 48)
RETRY_OPTION_SIZE = (420, 44)
RETRY_OPTION_SPACING = 50
RETRY_FIRST_OPTION_Y = 340
HINT_GAP = 20
"""Retry choices (up to 3, see RetryOption) replace the single action
button with a real vertical stack - button/hint y are computed from
whichever state (single button or a real N-choice stack) is actually on
screen rather than a fixed HINT_Y, the same "advance by however much the
real content needs" principle this codebase applies everywhere a
button/option count can genuinely vary (ComparisonRevealScene's own
_continue_button_y, MasteryChallengeScene's _options_layout)."""


class APIConsoleScene(Scene):
    """Steps through a real, hand-scripted pagination pull one click at a
    time: each click sends the next request and shows its real, structured
    response (status, records returned, whether more pages remain, the
    API's own declared total) - not a dialogue line describing what
    happened. Continuation is read off `has_more`, never told in advance;
    Finish only appears once the base `attempts` sequence is exhausted.

    A failed (rate-limited) attempt replaces the single action button with
    a real, caller-scripted choice (see `APIRequestAttempt.retry_options`/
    `RetryOption`) instead of auto-advancing - picking one appends its own
    `result` to the log, and if that result is itself still unresolved
    (`retry_options` set again, e.g. a second rate limit after retrying
    immediately once), the next, real, narrower choice set is offered the
    same way, with no special-casing in this scene for how many times a
    page has already been attempted. None of this is a dead end: every
    path through a failed attempt eventually resolves (successfully or by
    the student choosing to move on with a real, known gap) and the pull
    keeps going regardless of which choice was made - the consequence
    shows up honestly later, in whatever the caller does with the real,
    live `total_records()` this scene ends with, never a Game Over here.

    `context`, `python_code`, `evidence_label_key` are all optional and
    default to recording nothing - only a caller that supplies both
    `context` and `evidence_label_key` gets a real `AnalyticalAction`
    (`python_code`, when given) on Finish. `record_evidence` (default
    True, matching `PipelineBuilderScene`'s own precedent for exactly this
    split) controls whether that action *also* becomes a citable
    `EvidenceItem` - a caller whose real citable number comes from a later
    stage instead (e.g. a reveal that recomputes the same total for its
    own comparison) can pass `record_evidence=False` to keep the Python
    Mirror line without a duplicate evidence entry. `skipped_status_key`,
    if also given, adds a second, distinct `EvidenceItem` (via
    `skipped_evidence_label_key`, independent of `record_evidence`) when
    the log contains an attempt carrying that exact status_key - the
    caller's own way of marking "the student chose to move on without
    recovering this page," since that's real, additional evidence a
    student who took that path has and one who didn't doesn't."""

    def __init__(
        self,
        app,
        title_key: str,
        endpoint_key: str,
        attempts: tuple[APIRequestAttempt, ...],
        on_complete: Callable[[int], None],
        guided: bool = True,
        hint_key: str | None = None,
        context: LessonContext | None = None,
        python_code: str | None = None,
        evidence_label_key: str | None = None,
        record_evidence: bool = True,
        skipped_status_key: str | None = None,
        skipped_evidence_label_key: str | None = None,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.endpoint_key = endpoint_key
        self.attempts = attempts
        self.on_complete = on_complete
        self.guided = guided
        self.hint_key = hint_key
        self.context = context
        self.python_code = python_code
        self.evidence_label_key = evidence_label_key
        self.record_evidence = record_evidence
        self.skipped_status_key = skipped_status_key
        self.skipped_evidence_label_key = skipped_evidence_label_key
        self.log: list[APIRequestAttempt] = []
        self._pointer = 0
        self._pending: APIRequestAttempt | None = None
        self._rebuild_buttons()

    def _base_exhausted(self) -> bool:
        return self._pending is None and self._pointer >= len(self.attempts)

    def total_records(self) -> int:
        return sum(attempt.records_returned for attempt in self.log if attempt.is_success)

    def _buttons_bottom(self) -> int:
        if self._pending is not None:
            count = len(self._pending.retry_options)
            return RETRY_FIRST_OPTION_Y + (count - 1) * RETRY_OPTION_SPACING + RETRY_OPTION_SIZE[1] // 2
        return SINGLE_ACTION_BUTTON_Y + SINGLE_ACTION_BUTTON_SIZE[1] // 2

    def _hint_top(self) -> int:
        return self._buttons_bottom() + HINT_GAP

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []
        if self._pending is not None:
            for index, option in enumerate(self._pending.retry_options):
                rect = pygame.Rect(0, 0, *RETRY_OPTION_SIZE)
                rect.center = (CENTER_X, RETRY_FIRST_OPTION_Y + index * RETRY_OPTION_SPACING)
                buttons.append(Button(rect, loc.t(option.label_key), self._make_choose_retry(option)))
        else:
            rect = pygame.Rect(0, 0, *SINGLE_ACTION_BUTTON_SIZE)
            rect.center = (CENTER_X, SINGLE_ACTION_BUTTON_Y)
            if self._base_exhausted():
                buttons.append(Button(rect, loc.t("api_console.finish"), self._finish))
            else:
                buttons.append(Button(rect, loc.t("api_console.send_request"), self._send_request))
        self.buttons = ButtonGroup(buttons)

    def _send_request(self) -> None:
        if self._pending is not None or self._pointer >= len(self.attempts):
            return
        attempt = self.attempts[self._pointer]
        self.log.append(attempt)
        if attempt.retry_options is not None:
            self._pending = attempt
        else:
            self._pointer += 1
        self._rebuild_buttons()

    def _make_choose_retry(self, option) -> Callable[[], None]:
        def choose() -> None:
            result = option.result
            self.log.append(result)
            if result.retry_options is not None:
                self._pending = result
            else:
                self._pending = None
                self._pointer += 1
            self._rebuild_buttons()

        return choose

    def _finish(self) -> None:
        if not self._base_exhausted():
            return
        if self.context is not None and self.evidence_label_key is not None:
            action = self.context.record_action(label_key=self.evidence_label_key, python_code=self.python_code, key="api_pull")
            if self.record_evidence:
                self.context.record_evidence(
                    label_key=self.evidence_label_key, source_action=action, key="api_pull_total", detail=str(self.total_records())
                )
            if self.skipped_status_key is not None and self.skipped_evidence_label_key is not None:
                if any(attempt.status_key == self.skipped_status_key for attempt in self.log):
                    self.context.record_evidence(
                        label_key=self.skipped_evidence_label_key, source_action=action, key="api_pull_skipped"
                    )
        self.on_complete(self.total_records())

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 50), 28, colors.TEXT)
        draw_centered_text(surface, loc.t(self.endpoint_key), (CENTER_X, 85), 16, colors.BUTTON_TEXT_DISABLED)

        self._draw_response_panel(surface)
        self._draw_log_panel(surface)

        counter_text = f"{loc.t('api_console.records_collected')} {self.total_records()}"
        draw_centered_text(surface, counter_text, (CENTER_X, COUNTER_Y), 18, colors.BUTTON_FOCUS_BORDER)

        self.buttons.draw(surface)

        if self.guided and self.hint_key:
            draw_wrapped_text(surface, loc.t(self.hint_key), (CENTER_X - 380, self._hint_top()), 760, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_response_panel(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, RESPONSE_RECT, border_radius=8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, RESPONSE_RECT, width=1, border_radius=8)
        left = RESPONSE_RECT.left + 16
        width = RESPONSE_RECT.width - 32
        top = RESPONSE_RECT.top + 12
        draw_wrapped_text(surface, loc.t("api_console.response_panel.title"), (left, top), width, 16, colors.BUTTON_FOCUS_BORDER)
        if not self.log:
            return
        latest = self.log[-1]
        has_more_text = loc.t("api_console.value.yes") if latest.has_more else loc.t("api_console.value.no")
        total_text = str(latest.total_count) if latest.total_count is not None else loc.t("api_console.value.unknown")
        lines = (
            f"{loc.t('api_console.response_panel.page')}: {latest.page_number}",
            f"{loc.t('api_console.response_panel.status')}: {loc.t(latest.status_key)}",
            f"{loc.t('api_console.response_panel.records')}: {latest.records_returned}",
            f"{loc.t('api_console.response_panel.has_more')}: {has_more_text}",
            f"{loc.t('api_console.response_panel.total_count')}: {total_text}",
        )
        y = top + PANEL_HEADER_GAP
        for line in lines:
            draw_wrapped_text(surface, line, (left, y), width, 15, colors.TEXT)
            y += RESPONSE_LINE_HEIGHT

    def _draw_log_panel(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, LOG_RECT, border_radius=8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, LOG_RECT, width=1, border_radius=8)
        left = LOG_RECT.left + 16
        width = LOG_RECT.width - 32
        top = LOG_RECT.top + 12
        draw_wrapped_text(surface, loc.t("api_console.log_panel.title"), (left, top), width, 16, colors.BUTTON_FOCUS_BORDER)
        shown = self.log[-LOG_MAX_ROWS:]
        for index, attempt in enumerate(shown):
            y = top + PANEL_HEADER_GAP + index * LOG_ROW_HEIGHT
            page_label = f"{loc.t('api_console.page_label')} {attempt.page_number}"
            status_text = loc.t(attempt.status_key)
            records_text = f"{attempt.records_returned} {loc.t('api_console.records_suffix')}"
            color = colors.TEXT if attempt.is_success else colors.BUTTON_TEXT_DISABLED
            line = f"{page_label} - {status_text} - {records_text}"
            draw_single_line(surface, line, (left, y), width, 14, color)
