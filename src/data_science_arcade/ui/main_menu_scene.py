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
        labels_and_actions = [
            ("Continue", lambda: self._open_placeholder("Continue")),
            ("New Course", lambda: self._open_placeholder("New Course")),
            ("Course Map", lambda: self._open_placeholder("Course Map")),
            ("Settings", self._open_settings),
            ("Credits", lambda: self._open_placeholder("Credits")),
            ("Quit", self._quit),
        ]
        buttons = []
        for index, (label, action) in enumerate(labels_and_actions):
            rect = pygame.Rect(0, 0, *BUTTON_SIZE)
            rect.center = (CENTER_X, FIRST_BUTTON_Y + index * BUTTON_SPACING)
            buttons.append(Button(rect, label, action))
        self.buttons = ButtonGroup(buttons)

    def _open_placeholder(self, title: str) -> None:
        self.app.scenes.push(PlaceholderScene(self.app, title))

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
        draw_centered_text(surface, "Data Science Arcade", (CENTER_X, 120), 40, colors.TEXT)
        self.buttons.draw(surface)
