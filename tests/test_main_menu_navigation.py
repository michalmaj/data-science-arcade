import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.progress.model import LessonState
from data_science_arcade.ui.course_map_scene import CourseMapScene
from data_science_arcade.ui.credits_scene import CreditsScene
from data_science_arcade.ui.new_course_confirmation_scene import NewCourseConfirmationScene
from data_science_arcade.world.hub_scene import HubScene


def test_continue_opens_the_hub_keeping_existing_progress():
    app = App()
    app.init()
    try:
        app.progress.complete(1)

        app.scenes.current._continue()

        assert isinstance(app.scenes.current, HubScene)
        assert app.progress.state_of(1) == LessonState.COMPLETED
    finally:
        pygame.quit()


def test_new_course_asks_for_confirmation_first():
    app = App()
    app.init()
    try:
        app.progress.complete(1)

        app.scenes.current._new_course()

        assert isinstance(app.scenes.current, NewCourseConfirmationScene)
        assert app.progress.state_of(1) == LessonState.COMPLETED  # untouched until confirmed
    finally:
        pygame.quit()


def test_new_course_cancel_preserves_progress():
    app = App()
    app.init()
    try:
        app.progress.complete(1)
        app.progress.complete(2)
        menu = app.scenes.current

        menu._new_course()
        app.scenes.current._cancel()

        assert app.scenes.current is menu
        assert app.progress.state_of(1) == LessonState.COMPLETED
        assert app.progress.state_of(2) == LessonState.COMPLETED
    finally:
        pygame.quit()


def test_new_course_confirm_resets_progress_and_opens_the_hub():
    app = App()
    app.init()
    try:
        app.progress.complete(1)
        app.progress.complete(2)

        app.scenes.current._new_course()
        app.scenes.current._confirm()

        assert isinstance(app.scenes.current, HubScene)
        assert app.progress.state_of(1) == LessonState.UNLOCKED
        assert app.progress.state_of(2) == LessonState.LOCKED
    finally:
        pygame.quit()


def test_the_hub_s_mission_terminal_reaches_the_course_map():
    app = App()
    app.init()
    try:
        app.scenes.current._continue()
        app.scenes.current._open_terminal()

        assert isinstance(app.scenes.current, CourseMapScene)
    finally:
        pygame.quit()


def test_course_map_button_opens_the_course_map():
    app = App()
    app.init()
    try:
        app.scenes.current._open_course_map()
        assert isinstance(app.scenes.current, CourseMapScene)
    finally:
        pygame.quit()


def test_credits_opens_a_real_credits_screen():
    app = App()
    app.init()
    try:
        app.scenes.current._open_credits()
        assert isinstance(app.scenes.current, CreditsScene)
    finally:
        pygame.quit()
