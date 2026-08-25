import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l04_event_log_factory.scenario import (
    CORRECT_EVENT_BY_STEP,
    DECISION_FIELDS,
    FLOW_STEPS,
    build_lesson_four_runner,
)
from data_science_arcade.lessons.l04_event_log_factory.scoring import LessonFourResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.flow_builder_scene import FlowBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _click_correct_option(scene: FlowBuilderScene) -> None:
    step = scene._current_step()
    correct_key = CORRECT_EVENT_BY_STEP[step.key]
    index = next(i for i, option in enumerate(step.options) if option.key == correct_key)
    scene.buttons.buttons[index].on_activate()


def _place_every_step_correctly(scene: FlowBuilderScene) -> None:
    for _ in FLOW_STEPS:
        _click_correct_option(scene)
        scene.next_button.on_activate()


def _fill_out_brief(scene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eight_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_four_runner(
            app, on_finished=lambda result: finished_results.append(result)
        )
        runner.start()

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, FlowBuilderScene)  # guided
        assert app.scenes.current.guided is True
        _place_every_step_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # independent intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, FlowBuilderScene)  # independent
        assert app.scenes.current.guided is False
        _place_every_step_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, TwistRevealScene)
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # decision
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonFourResult)
        assert result.completed_thoughtfully() is True
        assert result.guided_placement == CORRECT_EVENT_BY_STEP
        assert result.independent_placement == CORRECT_EVENT_BY_STEP
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


@pytest.mark.parametrize("step", list(FLOW_STEPS))
def test_every_flow_step_has_at_least_two_options(step):
    assert len(step.options) >= 2


def test_every_flow_step_has_a_unique_key():
    keys = [step.key for step in FLOW_STEPS]
    assert len(keys) == len(set(keys))
