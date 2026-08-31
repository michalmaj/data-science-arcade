import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.ui.course_map_scene import CourseMapScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.handbook_scene import HandbookScene
from data_science_arcade.world.hub_scene import HubScene


def test_opening_the_handbook_pushes_a_handbook_scene():
    app = App()
    app.init()
    try:
        hub = HubScene(app)
        app.scenes.push(hub)

        hub._open_handbook()

        assert isinstance(app.scenes.current, HandbookScene)
    finally:
        pygame.quit()


def test_the_three_hotspots_and_back_button_do_not_overlap():
    app = App()
    app.init()
    try:
        hub = HubScene(app)
        rects = [hub.terminal_button.rect, hub.mentor_button.rect, hub.handbook_button.rect, hub.back_button.rect]
        for i, a in enumerate(rects):
            for b in rects[i + 1 :]:
                assert not a.colliderect(b), (a, b)
    finally:
        pygame.quit()


def test_mission_terminal_opens_the_course_map():
    app = App()
    app.init()
    try:
        hub = HubScene(app)
        app.scenes.push(hub)

        hub._open_terminal()

        assert isinstance(app.scenes.current, CourseMapScene)
    finally:
        pygame.quit()


def test_talking_to_the_mentor_opens_a_dialogue_with_the_hub_as_background():
    app = App()
    app.init()
    try:
        hub = HubScene(app)
        app.scenes.push(hub)

        hub._talk_to_mentor()

        assert isinstance(app.scenes.current, DialogueScene)
        assert app.scenes.current.background is hub
    finally:
        pygame.quit()


def test_escape_returns_to_whatever_opened_the_hub():
    app = App()
    app.init()
    try:
        main_menu = app.scenes.current
        hub = HubScene(app)
        app.scenes.push(hub)

        hub.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        assert app.scenes.current is main_menu
    finally:
        pygame.quit()


def test_draw_does_not_crash_headless():
    app = App()
    app.init()
    try:
        hub = HubScene(app)
        hub.draw(app.logical_surface)
    finally:
        pygame.quit()
