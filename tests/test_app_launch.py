import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import LOGICAL_SIZE, App


def test_app_initializes_with_the_fixed_logical_resolution():
    app = App()
    app.init()
    try:
        assert app.screen.get_size() == LOGICAL_SIZE
        assert app.running is True
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


def test_escape_key_stops_the_loop():
    app = App()
    app.init()
    try:
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        assert app.running is False
    finally:
        pygame.quit()
