import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text

CENTER_X = LOGICAL_SIZE[0] // 2


class SettingsScene(Scene):
    """Minimal settings screen. Only display mode exists this early; audio/
    language/accessibility options land with their respective systems."""

    def __init__(self, app) -> None:
        super().__init__(app)
        fullscreen_rect = pygame.Rect(0, 0, 260, 48)
        fullscreen_rect.center = (CENTER_X, 250)
        back_rect = pygame.Rect(0, 0, 200, 48)
        back_rect.center = (CENTER_X, 320)
        self.fullscreen_button = Button(fullscreen_rect, "", self._toggle_fullscreen)
        self.buttons = ButtonGroup([self.fullscreen_button, Button(back_rect, "Back", self._back)])
        self._sync_fullscreen_label()

    def _sync_fullscreen_label(self) -> None:
        state = "On" if self.app.fullscreen else "Off"
        self.fullscreen_button.label = f"Fullscreen: {state}"

    def _toggle_fullscreen(self) -> None:
        self.app.toggle_fullscreen()
        self._sync_fullscreen_label()

    def _back(self) -> None:
        self.app.scenes.pop()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        draw_centered_text(surface, "Settings", (CENTER_X, 160), 36, colors.TEXT)
        self.buttons.draw(surface)
