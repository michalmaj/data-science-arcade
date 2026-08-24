from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.placeholder_scene import PlaceholderScene
from data_science_arcade.ui.settings_scene import SettingsScene
from data_science_arcade.ui.text import draw_centered_text

CENTER_X = LOGICAL_SIZE[0] // 2
FIRST_BUTTON_Y = 210
BUTTON_SPACING = 56
BUTTON_SIZE = (260, 48)


class MainMenuScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._items: list[tuple[str, Callable[[], None]]] = [
            ("menu.continue", lambda: self._open_placeholder("menu.continue")),
            ("menu.new_course", lambda: self._open_placeholder("menu.new_course")),
            ("menu.course_map", lambda: self._open_placeholder("menu.course_map")),
            ("menu.settings", self._open_settings),
            ("menu.credits", lambda: self._open_placeholder("menu.credits")),
            ("menu.quit", self._quit),
        ]
        buttons = []
        for index, (key, action) in enumerate(self._items):
            rect = pygame.Rect(0, 0, *BUTTON_SIZE)
            rect.center = (CENTER_X, FIRST_BUTTON_Y + index * BUTTON_SPACING)
            buttons.append(Button(rect, self.app.localization.t(key), action))
        self.buttons = ButtonGroup(buttons)

    def on_enter(self) -> None:
        # Re-resolve labels: the player may have changed language while this
        # scene was underneath Settings on the stack.
        for button, (key, _action) in zip(self.buttons.buttons, self._items):
            button.label = self.app.localization.t(key)

    def _open_placeholder(self, title_key: str) -> None:
        self.app.scenes.push(PlaceholderScene(self.app, title_key))

    def _open_settings(self) -> None:
        self.app.scenes.push(SettingsScene(self.app))

    def _quit(self) -> None:
        self.app.running = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._quit()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        draw_centered_text(surface, self.app.localization.t("app.title"), (CENTER_X, 120), 40, colors.TEXT)
        self.buttons.draw(surface)
