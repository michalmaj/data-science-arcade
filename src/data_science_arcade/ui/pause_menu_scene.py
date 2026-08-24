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
DIM_ALPHA = 170


class PauseMenuScene(Scene):
    """A minimal pause overlay: Resume or quit back out of the lesson in
    progress without playing it to the end. Deliberately small for now
    (spec §57: smallest reasonable implementation) - settings/help are an
    easy addition here later since this already owns the whole "paused"
    moment, not a reason to build them up front."""

    def __init__(self, app, background: Scene, on_quit: Callable[[], None]) -> None:
        super().__init__(app)
        self.background = background
        self.on_quit = on_quit

        loc = app.localization
        resume_rect = pygame.Rect(0, 0, 260, 48)
        resume_rect.center = (CENTER_X, CENTER_Y - 10)
        quit_rect = pygame.Rect(0, 0, 260, 48)
        quit_rect.center = (CENTER_X, CENTER_Y + 50)
        self.buttons = ButtonGroup(
            [
                Button(resume_rect, loc.t("pause.resume"), self._resume),
                Button(quit_rect, loc.t("pause.quit"), self._quit),
            ]
        )

    def _resume(self) -> None:
        self.app.scenes.pop()

    def _quit(self) -> None:
        self.app.scenes.pop()  # close the pause menu
        self.on_quit()  # then let the caller unwind the paused scene itself

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        self.background.draw(surface)
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, DIM_ALPHA))
        surface.blit(dim, (0, 0))

        draw_centered_text(surface, self.app.localization.t("pause.title"), (CENTER_X, CENTER_Y - 80), 32, colors.TEXT)
        self.buttons.draw(surface)
