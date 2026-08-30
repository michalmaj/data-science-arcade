import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l09_outlier_patrol.scenario import DECISION_FIELDS, build_lesson_nine_runner
from data_science_arcade.lessons.l09_outlier_patrol.scoring import LessonNineResult
from data_science_arcade.lessons.l09_outlier_patrol.transactions import CORRECT_ACTION_BY_CASE, OUTLIER_CASES
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.flow_builder_scene import FlowBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

from lesson_test_helpers import click_through_mission_briefing


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _decide_every_case_correctly(scene: FlowBuilderScene) -> None:
    for _ in OUTLIER_CASES:
        step = scene._current_step()
        correct_key = CORRECT_ACTION_BY_CASE[step.key]
        index = next(i for i, option in enumerate(step.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def _fill_out_brief(scene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eight_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_nine_runner(
            app, on_finished=lambda result: finished_results.append(result)
        )
        runner.start()
        click_through_mission_briefing(app)

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, FlowBuilderScene)  # guided
        assert app.scenes.current.guided is True
        _decide_every_case_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # independent intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, FlowBuilderScene)  # independent
        assert app.scenes.current.guided is False
        _decide_every_case_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, TwistRevealScene)
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # decision
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonNineResult)
        assert result.completed_thoughtfully() is True
        assert result.guided_actions == CORRECT_ACTION_BY_CASE
        assert result.independent_actions == CORRECT_ACTION_BY_CASE
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
