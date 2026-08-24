import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.core.scenes import Pausable, Scene
from data_science_arcade.lessons.framework.runner import LessonRunner


class RecordingStageScene(Scene):
    def __init__(self, app, name: str) -> None:
        super().__init__(app)
        self.name = name
        self.entered = False

    def on_enter(self) -> None:
        self.entered = True


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_start_pushes_the_first_stage():
    app = _init_app()
    try:
        runner = LessonRunner(app, [lambda advance: RecordingStageScene(app, "one")])
        runner.start()

        # Every stage is wrapped in Pausable (so Escape opens the pause
        # menu); .inner is the actual stage scene the factory returned.
        assert isinstance(app.scenes.current, Pausable)
        assert isinstance(app.scenes.current.inner, RecordingStageScene)
        assert app.scenes.current.name == "one"  # proxied through via __getattr__
    finally:
        pygame.quit()


def test_advancing_replaces_the_stage_without_growing_the_stack():
    app = _init_app()
    try:
        stack_depth_before = len(app.scenes._stack)
        runner = LessonRunner(
            app,
            [
                lambda advance: RecordingStageScene(app, "one"),
                lambda advance: RecordingStageScene(app, "two"),
            ],
        )
        runner.start()

        runner._advance()

        assert app.scenes.current.name == "two"
        assert len(app.scenes._stack) == stack_depth_before + 1
    finally:
        pygame.quit()


def test_advancing_past_the_last_stage_pops_back_to_whatever_opened_it():
    app = _init_app()
    try:
        previous = app.scenes.current
        runner = LessonRunner(app, [lambda advance: RecordingStageScene(app, "only")])
        runner.start()

        runner._advance()

        assert app.scenes.current is previous
    finally:
        pygame.quit()


def test_on_finished_runs_once_the_lesson_completes():
    app = _init_app()
    try:
        calls = []
        runner = LessonRunner(
            app, [lambda advance: RecordingStageScene(app, "only")], on_finished=lambda: calls.append("done")
        )
        runner.start()

        runner._advance()

        assert calls == ["done"]
    finally:
        pygame.quit()


def test_a_stage_factory_receives_a_working_advance_callback():
    app = _init_app()
    try:
        seen_names = []

        def stage_one(advance):
            scene = RecordingStageScene(app, "one")
            scene.on_activate = advance  # simulate the stage calling advance itself
            return scene

        def stage_two(advance):
            seen_names.append("two")
            return RecordingStageScene(app, "two")

        runner = LessonRunner(app, [stage_one, stage_two])
        runner.start()

        app.scenes.current.on_activate()  # simulates the player finishing stage one

        assert seen_names == ["two"]
        assert app.scenes.current.name == "two"
    finally:
        pygame.quit()


def test_escape_opens_the_pause_menu_instead_of_reaching_the_stage():
    app = _init_app()
    try:
        runner = LessonRunner(app, [lambda advance: RecordingStageScene(app, "one")])
        runner.start()
        stage = app.scenes.current.inner

        app.scenes.current.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))

        from data_science_arcade.ui.pause_menu_scene import PauseMenuScene

        assert isinstance(app.scenes.current, PauseMenuScene)
        assert stage.entered is True  # the stage itself never saw the Escape
    finally:
        pygame.quit()


def test_resuming_from_the_pause_menu_returns_to_the_same_stage():
    app = _init_app()
    try:
        runner = LessonRunner(app, [lambda advance: RecordingStageScene(app, "one")])
        runner.start()
        stage_wrapper = app.scenes.current
        app.scenes.current.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))

        app.scenes.current.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))  # resume

        assert app.scenes.current is stage_wrapper
    finally:
        pygame.quit()


def test_quitting_from_the_pause_menu_abandons_the_lesson_without_finishing_it():
    app = _init_app()
    try:
        previous = app.scenes.current
        finished_calls = []
        runner = LessonRunner(
            app,
            [lambda advance: RecordingStageScene(app, "one")],
            on_finished=lambda: finished_calls.append("done"),
        )
        runner.start()
        app.scenes.current.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))
        quit_button = app.scenes.current.buttons.buttons[1]

        quit_button.on_activate()

        assert app.scenes.current is previous
        assert finished_calls == []  # quitting early must not mark the lesson complete
    finally:
        pygame.quit()
