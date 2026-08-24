import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.ui.main_menu_scene import MainMenuScene


def test_app_initializes_with_the_fixed_logical_resolution_and_the_main_menu():
    app = App()
    app.init()
    try:
        assert app.window_surface.get_size() == LOGICAL_SIZE
        assert app.running is True
        assert isinstance(app.scenes.current, MainMenuScene)
    finally:
        pygame.quit()


def test_quit_event_stops_the_loop():
    app = App()
    app.init()
    try:
        app.handle_event(pygame.event.Event(pygame.QUIT))
        assert app.running is False
    finally:
        pygame.quit()


def test_escape_on_the_main_menu_stops_the_loop():
    app = App()
    app.init()
    try:
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        assert app.running is False
    finally:
        pygame.quit()


def test_f11_toggles_fullscreen_without_crashing():
    app = App()
    app.init()
    try:
        assert app.fullscreen is False
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11))
        assert app.fullscreen is True
    finally:
        pygame.quit()


def test_draw_does_not_crash_after_init():
    app = App()
    app.init()
    try:
        app.draw()
    finally:
        pygame.quit()
