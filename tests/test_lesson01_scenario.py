import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l01_question_first.scenario import (
    BRIEF_FIELDS,
    DECISION_FIELDS,
    build_lesson_one_runner,
)
from data_science_arcade.lessons.l01_question_first.scoring import LessonOneResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

from lesson_test_helpers import click_through_mission_briefing


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene: DialogueScene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _fill_out_brief(scene: BriefBuilderScene, fields) -> None:
    for _ in fields:
        first_option_button = scene.buttons.buttons[0]
        first_option_button.on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eight_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_one_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        # Stage 1: briefing dialogue
        assert isinstance(app.scenes.current.inner, DialogueScene)
        _play_dialogue_to_the_end(app.scenes.current)

        # Stage 2: investigation dialogue
        assert isinstance(app.scenes.current.inner, DialogueScene)
        _play_dialogue_to_the_end(app.scenes.current)

        # Stage 3: guided brief builder
        assert isinstance(app.scenes.current.inner, BriefBuilderScene)
        assert app.scenes.current.guided is True
        _fill_out_brief(app.scenes.current, BRIEF_FIELDS)

        # Stage 4: independent-challenge intro dialogue
        assert isinstance(app.scenes.current.inner, DialogueScene)
        _play_dialogue_to_the_end(app.scenes.current)

        # Stage 5: independent brief builder (less guidance)
        assert isinstance(app.scenes.current.inner, BriefBuilderScene)
        assert app.scenes.current.guided is False
        _fill_out_brief(app.scenes.current, BRIEF_FIELDS)

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
        assert isinstance(result, LessonOneResult)
        assert result.completed_thoughtfully() is True
        assert set(result.guided_brief) == {field.key for field in BRIEF_FIELDS}
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


def test_next_is_disabled_until_a_choice_is_made_on_each_field():
    app = _init_app()
    try:
        runner, _ = build_lesson_one_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        brief_scene = app.scenes.current
        assert isinstance(brief_scene.inner, BriefBuilderScene)
        assert brief_scene.next_button.enabled is False

        brief_scene.buttons.buttons[0].on_activate()

        assert brief_scene.next_button.enabled is True
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(BRIEF_FIELDS) + list(DECISION_FIELDS))
def test_every_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
