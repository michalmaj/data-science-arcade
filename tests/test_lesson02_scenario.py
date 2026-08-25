import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l02_source_scout.scenario import DECISION_FIELDS, SOURCES, build_lesson_two_runner
from data_science_arcade.lessons.l02_source_scout.scoring import LessonTwoResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.source_board_scene import SourceBoardScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _pick_a_source(scene) -> None:
    first_source_key = SOURCES[0].key
    scene.source_buttons[first_source_key].on_activate()
    scene.confirm_button.on_activate()


def _fill_out_brief(scene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eight_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_two_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        # Stage 1: briefing dialogue
        assert isinstance(app.scenes.current.inner, DialogueScene)
        _play_dialogue_to_the_end(app.scenes.current)

        # Stage 2: investigation dialogue
        assert isinstance(app.scenes.current.inner, DialogueScene)
        _play_dialogue_to_the_end(app.scenes.current)

        # Stage 3: guided source board
        assert isinstance(app.scenes.current.inner, SourceBoardScene)
        assert app.scenes.current.guided is True
        _pick_a_source(app.scenes.current)

        # Stage 4: independent-challenge intro dialogue
        assert isinstance(app.scenes.current.inner, DialogueScene)
        _play_dialogue_to_the_end(app.scenes.current)

        # Stage 5: independent source board (less guidance)
        assert isinstance(app.scenes.current.inner, SourceBoardScene)
        assert app.scenes.current.guided is False
        _pick_a_source(app.scenes.current)

        # Stage 6: twist reveal
        assert isinstance(app.scenes.current.inner, TwistRevealScene)
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        # Stage 7: decision brief
        assert isinstance(app.scenes.current.inner, BriefBuilderScene)
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)

        # Stage 8: debrief dialogue
        assert isinstance(app.scenes.current.inner, DialogueScene)
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwoResult)
        assert result.completed_thoughtfully() is True
        assert result.guided_source_choice == SOURCES[0].key
        assert result.independent_source_choice == SOURCES[0].key
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


def test_confirm_is_disabled_until_a_source_is_selected():
    app = _init_app()
    try:
        runner, _ = build_lesson_two_runner(app, on_finished=lambda result: None)
        runner.start()
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        board_scene = app.scenes.current
        assert isinstance(board_scene.inner, SourceBoardScene)
        assert board_scene.confirm_button.enabled is False

        board_scene.source_buttons[SOURCES[0].key].on_activate()

        assert board_scene.confirm_button.enabled is True
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_every_source_has_five_attributes():
    for source in SOURCES:
        assert len(source.attributes) == 5
