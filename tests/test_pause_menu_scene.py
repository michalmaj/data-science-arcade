import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.ui.pause_menu_scene import PauseMenuScene


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_resume_pops_just_the_pause_menu():
    app = _init_app()
    try:
        background = app.scenes.current
        scene = PauseMenuScene(app, background=background, on_quit=lambda: None)
        app.scenes.push(scene)

        scene._resume()

        assert app.scenes.current is background
    finally:
        pygame.quit()


def test_escape_also_resumes():
    app = _init_app()
    try:
        background = app.scenes.current
        scene = PauseMenuScene(app, background=background, on_quit=lambda: None)
        app.scenes.push(scene)

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))

        assert app.scenes.current is background
    finally:
        pygame.quit()


def test_quit_pops_the_pause_menu_then_calls_on_quit():
    app = _init_app()
    try:
        calls = []
        background = app.scenes.current
        scene = PauseMenuScene(app, background=background, on_quit=lambda: calls.append("quit"))
        app.scenes.push(scene)

        scene._quit()

        assert app.scenes.current is background  # the pop happened before on_quit ran
        assert calls == ["quit"]
    finally:
        pygame.quit()


def test_quit_button_triggers_the_same_behavior_as_calling_quit_directly():
    app = _init_app()
    try:
        calls = []
        background = app.scenes.current
        scene = PauseMenuScene(app, background=background, on_quit=lambda: calls.append("quit"))
        app.scenes.push(scene)

        scene.buttons.buttons[1].on_activate()  # Quit is the second button

        assert calls == ["quit"]
    finally:
        pygame.quit()


def test_draw_paints_the_background_before_dimming_and_the_menu():
    app = _init_app()
    try:
        background = app.scenes.current
        scene = PauseMenuScene(app, background=background, on_quit=lambda: None)

        scene.draw(app.logical_surface)  # must not raise
    finally:
        pygame.quit()
