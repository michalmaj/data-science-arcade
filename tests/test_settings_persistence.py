import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.ui.settings_scene import SettingsScene


def test_toggling_fullscreen_survives_a_fresh_app_instance():
    first_run = App()
    first_run.init()
    try:
        settings = SettingsScene(first_run)
        settings._toggle_fullscreen()
        assert first_run.fullscreen is True
    finally:
        pygame.quit()

    second_run = App()  # simulates relaunching the app - reads the same save file
    assert second_run.progress.fullscreen is True


def test_toggling_language_survives_a_fresh_app_instance():
    first_run = App()
    first_run.init()
    try:
        settings = SettingsScene(first_run)
        settings._toggle_language()
        assert first_run.localization.locale == "pl"
    finally:
        pygame.quit()

    second_run = App()
    second_run.init()
    try:
        assert second_run.localization.locale == "pl"
        assert isinstance(second_run.scenes.current.buttons.buttons[0].label, str)
        assert second_run.scenes.current.buttons.buttons[0].label == "Kontynuuj"
    finally:
        pygame.quit()
