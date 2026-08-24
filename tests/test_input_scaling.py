import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App

SETTINGS_BUTTON_INDEX = 3  # Continue, New Course, Course Map, Settings, ...


def test_mouse_hover_targets_the_right_button_at_an_exact_2x_scale():
    app = App()
    app.init()
    try:
        # Stand in for a 1920x1080 fullscreen window: an exact 2x scale of
        # the 960x540 canvas, no letterbox. window_surface only needs to
        # report the right size here - handle_event() never draws to it.
        app.window_surface = pygame.Surface((1920, 1080))
        settings_button = app.scenes.current.buttons.buttons[SETTINGS_BUTTON_INDEX]
        window_space_point = tuple(component * 2 for component in settings_button.rect.center)

        app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=window_space_point))

        assert app.scenes.current.buttons.focus_index == SETTINGS_BUTTON_INDEX
    finally:
        pygame.quit()


def test_mouse_click_targets_the_right_button_through_a_pillarbox_offset():
    app = App()
    app.init()
    try:
        # 2000x540: wider than 16:9, so compute_scaled_rect adds a pillarbox
        # (scale=1, x-offset=520) instead of scaling up.
        app.window_surface = pygame.Surface((2000, 540))
        activated = []
        app.scenes.current.buttons.buttons[SETTINGS_BUTTON_INDEX].on_activate = lambda: activated.append(True)
        button_center = app.scenes.current.buttons.buttons[SETTINGS_BUTTON_INDEX].rect.center
        window_space_point = (button_center[0] + 520, button_center[1])

        app.handle_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=window_space_point, button=1)
        )

        assert activated == [True]
    finally:
        pygame.quit()


def test_a_click_inside_the_pillarbox_bar_hits_nothing():
    app = App()
    app.init()
    try:
        app.window_surface = pygame.Surface((2000, 540))
        for button in app.scenes.current.buttons.buttons:
            button.on_activate = lambda: (_ for _ in ()).throw(AssertionError("should not activate"))

        app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 270), button=1))
    finally:
        pygame.quit()
