import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.progress.model import LessonCheckpoint
from data_science_arcade.ui.mission_briefing_scene import MissionBriefingScene


class RecordingStageScene(Scene):
    def __init__(self, app, name: str) -> None:
        super().__init__(app)
        self.name = name


def _init_app() -> App:
    app = App()
    app.init()
    return app


DEFINITION = LessonDefinition(
    id="fake",
    chapter=1,
    number=99,
    title_key="app.title",
    objective_keys=("common.back",),
    scoring_dimensions=(ScoreDimension.REASONING,),
    estimated_minutes=15,
)


def _make_stage(app, collected, name):
    # Mirrors the real pattern every one of the 30 lessons' scenario.py
    # files uses: the *factory* just builds the scene; the write into
    # `collected` happens inside a completion callback (triggered by
    # player interaction, exposed here as `.finish()`) that also calls
    # `advance` - not inside the factory itself. Calling `.finish()` is
    # therefore the correct way to simulate "the player finished this
    # stage" in these tests, not calling `runner._advance()` directly,
    # which would skip the write entirely.
    def stage(advance):
        scene = RecordingStageScene(app, name)

        def finish():
            collected[name] = True
            advance()

        scene.finish = finish
        return scene

    return stage


def _three_stages(app, collected):
    return [_make_stage(app, collected, "one"), _make_stage(app, collected, "two"), _make_stage(app, collected, "three")]


def _finish_current_stage(app) -> None:
    app.scenes.current.inner.finish()


def test_a_definition_shows_the_mission_briefing_before_the_first_stage():
    app = _init_app()
    try:
        collected = {}
        runner = LessonRunner(app, _three_stages(app, collected), lesson_number=99, collected=collected, definition=DEFINITION)

        runner.start()

        assert isinstance(app.scenes.current.inner, MissionBriefingScene)
        app.scenes.current.inner.buttons.buttons[0].on_activate()
        assert app.scenes.current.inner.name == "one"
    finally:
        pygame.quit()


def test_no_definition_skips_straight_to_the_first_stage():
    app = _init_app()
    try:
        collected = {}
        runner = LessonRunner(app, _three_stages(app, collected), lesson_number=99, collected=collected)

        runner.start()

        assert app.scenes.current.inner.name == "one"
    finally:
        pygame.quit()


def test_advancing_saves_a_checkpoint_reflecting_only_the_just_finished_stage():
    app = _init_app()
    try:
        collected = {}
        runner = LessonRunner(app, _three_stages(app, collected), lesson_number=99, collected=collected)
        runner.start()

        _finish_current_stage(app)  # finishes "one", lands on "two" (not yet finished)

        checkpoint = app.progress.checkpoint_for(99)
        assert checkpoint is not None
        assert checkpoint.stage_index == 1
        assert checkpoint.collected == {"one": True}
    finally:
        pygame.quit()


def test_no_lesson_number_never_saves_a_checkpoint():
    app = _init_app()
    try:
        collected = {}
        runner = LessonRunner(app, _three_stages(app, collected), collected=collected)
        runner.start()

        _finish_current_stage(app)

        assert app.progress.checkpoints == {}
    finally:
        pygame.quit()


def test_a_fresh_runner_resumes_from_a_saved_checkpoint_skipping_the_briefing():
    app = _init_app()
    try:
        collected = {}
        first_runner = LessonRunner(app, _three_stages(app, collected), lesson_number=99, collected=collected, definition=DEFINITION)
        first_runner.start()
        app.scenes.current.inner.buttons.buttons[0].on_activate()  # Start Mission
        _finish_current_stage(app)  # finishes "one", checkpoint saved at index 1 ("two")

        # Simulate relaunching the lesson: a brand new runner, fresh collected dict.
        new_collected = {}
        second_runner = LessonRunner(app, _three_stages(app, new_collected), lesson_number=99, collected=new_collected, definition=DEFINITION)
        second_runner.start()

        assert not isinstance(app.scenes.current.inner, MissionBriefingScene)
        assert app.scenes.current.inner.name == "two"
        assert second_runner.collected == {"one": True}
    finally:
        pygame.quit()


def test_resume_mutates_collected_in_place_never_rebinding_it():
    app = _init_app()
    try:
        collected = {}
        first_runner = LessonRunner(app, _three_stages(app, collected), lesson_number=99, collected=collected)
        first_runner.start()
        _finish_current_stage(app)  # finishes "one"

        new_collected = {}
        second_runner = LessonRunner(app, _three_stages(app, new_collected), lesson_number=99, collected=new_collected)
        second_runner.start()

        assert second_runner.collected is new_collected  # never rebound to a freshly-deserialized dict
        # continuing to write into it (as the real stage closures do) must
        # actually reach the object LessonRunner is checkpointing from.
        _finish_current_stage(app)  # finishes "two"
        assert app.progress.checkpoint_for(99).collected == {"one": True, "two": True}
    finally:
        pygame.quit()


def test_a_stage_fingerprint_mismatch_discards_the_checkpoint_and_starts_fresh():
    app = _init_app()
    try:
        collected = {}
        first_runner = LessonRunner(app, _three_stages(app, collected), lesson_number=99, collected=collected)
        first_runner.start()
        _finish_current_stage(app)  # checkpoint saved for the 3-stage fingerprint

        def only_stage(advance):
            return RecordingStageScene(app, "only")

        reshaped_collected = {}
        reshaped_runner = LessonRunner(app, [only_stage], lesson_number=99, collected=reshaped_collected)
        reshaped_runner.start()

        assert app.scenes.current.inner.name == "only"  # started fresh, not crashed on an out-of-range index
    finally:
        pygame.quit()


def test_an_out_of_range_checkpoint_index_is_treated_as_no_checkpoint():
    app = _init_app()
    try:
        collected = {}
        stages = _three_stages(app, collected)
        fingerprint = "|".join(stage.__name__ for stage in stages)
        app.progress.save_checkpoint(99, LessonCheckpoint(stage_index=99, stage_fingerprint=fingerprint, collected={}))

        runner = LessonRunner(app, stages, lesson_number=99, collected=collected)
        runner.start()

        assert app.scenes.current.inner.name == "one"
    finally:
        pygame.quit()


def test_finishing_a_lesson_through_the_runner_leaves_the_checkpoint_clearing_to_progress_complete():
    # LessonRunner itself doesn't clear checkpoints - Progress.complete()
    # does, from the one place every real finishing path already calls
    # (see test_progress_migration.py). This just confirms a checkpoint
    # exists mid-lesson so that division of responsibility is meaningful.
    app = _init_app()
    try:
        collected = {}
        runner = LessonRunner(app, _three_stages(app, collected), lesson_number=99, collected=collected)
        runner.start()
        _finish_current_stage(app)

        assert app.progress.checkpoint_for(99) is not None
        app.progress.complete(99)
        assert app.progress.checkpoint_for(99) is None
    finally:
        pygame.quit()
