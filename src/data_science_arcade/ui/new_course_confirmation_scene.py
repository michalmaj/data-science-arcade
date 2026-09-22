from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
CENTER_Y = LOGICAL_SIZE[1] // 2


class NewCourseConfirmationScene(Scene):
    """Guards the main menu's own destructive "New Course" action - wiping
    Progress can throw away everything a player has done, unlike Resume
    vs. Start Over (ResumeConfirmationScene) which only ever discards one
    lesson's own mid-lesson checkpoint. Mirrors that scene's own
    constructor shape and pop-then-callback ordering, but with the safe
    option (Cancel) as both the default framing and Escape's own target -
    the destructive option is never the path of least resistance."""

    def __init__(self, app, on_confirm: Callable[[], None], on_cancel: Callable[[], None]) -> None:
        super().__init__(app)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        loc = app.localization
        cancel_rect = pygame.Rect(0, 0, 260, 48)
        cancel_rect.center = (CENTER_X, CENTER_Y + 10)
        confirm_rect = pygame.Rect(0, 0, 260, 48)
        confirm_rect.center = (CENTER_X, CENTER_Y + 70)
        self.buttons = ButtonGroup(
            [
                Button(cancel_rect, loc.t("runtime.new_course_cancel_button"), self._cancel),
                Button(confirm_rect, loc.t("runtime.new_course_confirm_button"), self._confirm),
            ]
        )

    def _cancel(self) -> None:
        self.app.scenes.pop()
        self.on_cancel()

    def _confirm(self) -> None:
        self.app.scenes.pop()
        self.on_confirm()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._cancel()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        loc = self.app.localization
        draw_centered_wrapped_text(
            surface, loc.t("runtime.new_course_confirm_title"), (CENTER_X, CENTER_Y - 90), 700, 22, colors.TEXT
        )
        draw_centered_wrapped_text(
            surface, loc.t("runtime.new_course_confirm_warning"), (CENTER_X, CENTER_Y - 45), 700, 15, colors.BUTTON_TEXT_DISABLED
        )
        self.buttons.draw(surface)
