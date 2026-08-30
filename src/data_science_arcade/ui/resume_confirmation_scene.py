from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text

CENTER_X = LOGICAL_SIZE[0] // 2
CENTER_Y = LOGICAL_SIZE[1] // 2


class ResumeConfirmationScene(Scene):
    """Shown from the course map when a lesson has a saved mid-lesson
    checkpoint - resume where you left off, or start over. Deliberately
    minimal, mirroring PauseMenuScene's own two-button style rather than
    inventing a new visual language for one more confirmation screen."""

    def __init__(self, app, on_resume: Callable[[], None], on_start_over: Callable[[], None]) -> None:
        super().__init__(app)
        self.on_resume = on_resume
        self.on_start_over = on_start_over

        loc = app.localization
        resume_rect = pygame.Rect(0, 0, 260, 48)
        resume_rect.center = (CENTER_X, CENTER_Y - 10)
        start_over_rect = pygame.Rect(0, 0, 260, 48)
        start_over_rect.center = (CENTER_X, CENTER_Y + 50)
        self.buttons = ButtonGroup(
            [
                Button(resume_rect, loc.t("runtime.resume_button"), self._resume),
                Button(start_over_rect, loc.t("runtime.start_over_button"), self._start_over),
            ]
        )

    def _resume(self) -> None:
        self.app.scenes.pop()
        self.on_resume()

    def _start_over(self) -> None:
        self.app.scenes.pop()
        self.on_start_over()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        loc = self.app.localization
        draw_centered_text(surface, loc.t("runtime.resume_prompt_title"), (CENTER_X, CENTER_Y - 80), 24, colors.TEXT)
        self.buttons.draw(surface)
