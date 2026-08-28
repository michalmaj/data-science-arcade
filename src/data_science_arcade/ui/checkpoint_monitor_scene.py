from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.monitoring import MonitoringCheckpoint
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
RUNTIME_Y = 78
TABLE_TOP = 140
ROW_HEIGHT = 42
LABEL_X = 60
LABEL_MAX_WIDTH = 420
TREATMENT_COLUMN_X = 640
CONTROL_COLUMN_X = 820
HEADER_Y_OFFSET = -30
HINT_Y = 380
NAV_BUTTON_SIZE = (220, 44)
NAV_BUTTON_Y = 460
NAV_BUTTON_GAP = 130


class CheckpointMonitorScene(Scene):
    """A single experiment monitored at a fixed sequence of checkpoints
    (spec §25 Lesson 20 'A/B Test Commander'): each checkpoint shows a
    real dashboard (primary metric, guardrails, a segment check) for
    however many days have elapsed so far. At every checkpoint but the
    last, the player explicitly chooses to stop and decide now (acting on
    whatever the dashboard shows at that point, however early) or keep
    running to the next, more reliable checkpoint - the "peeking" decision
    is something the player does, not just narration. on_complete receives
    the 1-indexed checkpoint the player stopped at, whether by choice or
    by reaching the end.

    guided=True also shows a hint about what an early read doesn't
    guarantee; guided=False hides it."""

    def __init__(
        self,
        app,
        title_key: str,
        checkpoints: tuple[MonitoringCheckpoint, ...],
        total_runtime_days: int,
        on_complete: Callable[[int], None],
        guided: bool = True,
        hint_key: str | None = None,
        treatment_label_key: str = "checkpoint.treatment_label",
        control_label_key: str = "checkpoint.control_label",
        value_format: Callable[[float], str] = lambda value: f"{value:.1%}",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.checkpoints = checkpoints
        self.total_runtime_days = total_runtime_days
        self.on_complete = on_complete
        self.guided = guided
        self.hint_key = hint_key
        self.treatment_label_key = treatment_label_key
        self.control_label_key = control_label_key
        self.value_format = value_format
        self.checkpoint_index = 0
        self._rebuild_buttons()

    def _current_checkpoint(self) -> MonitoringCheckpoint:
        return self.checkpoints[self.checkpoint_index]

    def _is_last_checkpoint(self) -> bool:
        return self.checkpoint_index == len(self.checkpoints) - 1

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []

        if self._is_last_checkpoint():
            finish_rect = pygame.Rect(0, 0, *NAV_BUTTON_SIZE)
            finish_rect.center = (CENTER_X, NAV_BUTTON_Y)
            self.stop_button = Button(finish_rect, loc.t("brief.finish"), self._stop)
            self.continue_button = None
            buttons.append(self.stop_button)
        else:
            stop_rect = pygame.Rect(0, 0, *NAV_BUTTON_SIZE)
            stop_rect.center = (CENTER_X - NAV_BUTTON_GAP, NAV_BUTTON_Y)
            self.stop_button = Button(stop_rect, loc.t("checkpoint.stop_button"), self._stop)
            buttons.append(self.stop_button)

            continue_rect = pygame.Rect(0, 0, *NAV_BUTTON_SIZE)
            continue_rect.center = (CENTER_X + NAV_BUTTON_GAP, NAV_BUTTON_Y)
            self.continue_button = Button(continue_rect, loc.t("checkpoint.continue_button"), self._continue)
            buttons.append(self.continue_button)

        self.buttons = ButtonGroup(buttons)

    def _stop(self) -> None:
        self.on_complete(self.checkpoint_index + 1)

    def _continue(self) -> None:
        if self._is_last_checkpoint():
            return
        self.checkpoint_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        checkpoint = self._current_checkpoint()

        progress = f"{self.checkpoint_index + 1} / {len(self.checkpoints)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)

        runtime_text = f"{loc.t('checkpoint.day_label')} {checkpoint.day} / {self.total_runtime_days}"
        draw_centered_text(surface, runtime_text, (CENTER_X, RUNTIME_Y), 16, colors.BUTTON_FOCUS_BORDER)

        header_y = TABLE_TOP + HEADER_Y_OFFSET
        draw_centered_text(surface, loc.t(self.treatment_label_key), (TREATMENT_COLUMN_X, header_y), 14, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.control_label_key), (CONTROL_COLUMN_X, header_y), 14, colors.BUTTON_TEXT_DISABLED)

        for index, row in enumerate(checkpoint.rows):
            y = TABLE_TOP + index * ROW_HEIGHT
            value_color = colors.BUTTON_FOCUS_BORDER if row.flagged else colors.TEXT
            draw_wrapped_text(surface, loc.t(row.label_key), (LABEL_X, y - 8), LABEL_MAX_WIDTH, 16, colors.TEXT)
            draw_centered_text(surface, self.value_format(row.treatment_value), (TREATMENT_COLUMN_X, y), 16, value_color)
            draw_centered_text(surface, self.value_format(row.control_value), (CONTROL_COLUMN_X, y), 16, value_color)

        self.buttons.draw(surface)

        if self.guided and self.hint_key:
            draw_wrapped_text(surface, loc.t(self.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)
