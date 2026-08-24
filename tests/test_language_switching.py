import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.ui.settings_scene import SettingsScene


def test_switching_language_in_settings_updates_the_main_menu_on_return():
    app = App()
    app.init()
    try:
        main_menu = app.scenes.current
        assert main_menu.buttons.buttons[0].label == "Continue"

        settings = SettingsScene(app)
        app.scenes.push(settings)
        settings._toggle_language()
        assert app.localization.locale == "pl"

        app.scenes.pop()

        assert app.scenes.current is main_menu
        assert main_menu.buttons.buttons[0].label == "Kontynuuj"
    finally:
        pygame.quit()


def test_settings_labels_update_immediately_after_toggling_language():
    app = App()
    app.init()
    try:
        settings = SettingsScene(app)
        app.scenes.push(settings)

        settings._toggle_language()

        assert settings.back_button.label == "Wstecz"
        assert "Język" in settings.language_button.label
    finally:
        pygame.quit()
