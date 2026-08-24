import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.progress.model import TOTAL_LESSONS, LessonState
from data_science_arcade.ui.course_map_scene import CourseMapScene
from data_science_arcade.ui.placeholder_scene import PlaceholderScene


def test_only_the_first_lesson_starts_enabled():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        assert course_map._lesson_buttons[1].enabled is True
        assert course_map._lesson_buttons[2].enabled is False
        assert course_map._lesson_buttons[TOTAL_LESSONS].enabled is False
    finally:
        pygame.quit()


def test_unlocking_a_lesson_in_progress_is_reflected_after_on_enter():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.progress.unlock(2)

        course_map.on_enter()

        assert course_map._lesson_buttons[2].enabled is True
    finally:
        pygame.quit()


def test_clicking_an_unlocked_lesson_opens_a_placeholder_with_the_lesson_number():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(1)

        assert isinstance(app.scenes.current, PlaceholderScene)
        assert "01" in app.scenes.current.title
    finally:
        pygame.quit()


def test_dev_mode_shows_every_lesson_as_enabled_without_touching_the_save(monkeypatch):
    monkeypatch.setenv("DSA_DEV_MODE", "1")
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        assert course_map._lesson_buttons[TOTAL_LESSONS].enabled is True
        # the underlying save is untouched - only the *effective* state is unlocked
        assert app.progress.state_of(TOTAL_LESSONS) == LessonState.LOCKED
    finally:
        pygame.quit()


def test_dev_mode_click_marks_the_lesson_complete_and_unlocks_the_next(monkeypatch):
    monkeypatch.setenv("DSA_DEV_MODE", "1")
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(1)

        assert app.progress.state_of(1) == LessonState.COMPLETED
        assert app.progress.state_of(2) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def test_completed_lesson_stays_enabled_for_replay():
    app = App()
    app.init()
    try:
        app.progress.complete(1)
        course_map = CourseMapScene(app)
        assert course_map._lesson_buttons[1].enabled is True
    finally:
        pygame.quit()


def test_escape_goes_back():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        previous = app.scenes._stack[-2]

        course_map.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        assert app.scenes.current is previous
    finally:
        pygame.quit()


def test_draw_does_not_crash_headless():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        course_map.draw(app.logical_surface)
    finally:
        pygame.quit()
