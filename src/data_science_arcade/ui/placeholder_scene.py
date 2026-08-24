import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text

CENTER_X = LOGICAL_SIZE[0] // 2


class PlaceholderScene(Scene):
    """Stands in for a destination whose real system doesn't exist yet."""

    def __init__(self, app, title: str) -> None:
        super().__init__(app)
        self.title = title
        back_rect = pygame.Rect(0, 0, 200, 48)
        back_rect.center = (CENTER_X, 340)
        self.buttons = ButtonGroup([Button(back_rect, "Back", self._back)])

    def _back(self) -> None:
        self.app.scenes.pop()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        draw_centered_text(surface, self.title, (CENTER_X, 220), 36, colors.TEXT)
        draw_centered_text(surface, "Coming in a later phase.", (CENTER_X, 270), 20, colors.TEXT)
        self.buttons.draw(surface)
