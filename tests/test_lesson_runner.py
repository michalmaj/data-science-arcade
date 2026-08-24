import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.core.scenes import Scene
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

        assert isinstance(app.scenes.current, RecordingStageScene)
        assert app.scenes.current.name == "one"
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
