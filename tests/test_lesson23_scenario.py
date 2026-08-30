import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l23_time_series_control_room.requests import CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l23_time_series_control_room.scenario import DECISION_FIELDS, build_lesson_twenty_three_runner
from data_science_arcade.lessons.l23_time_series_control_room.scoring import LessonTwentyThreeResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.timeseries_scene import TimeSeriesScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

from lesson_test_helpers import click_through_mission_briefing


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _pick_every_option_correctly(scene: TimeSeriesScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
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
        runner, collected = build_lesson_twenty_three_runner(
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

        assert isinstance(app.scenes.current.inner, TimeSeriesScene)  # guided
        assert app.scenes.current.guided is True
        _pick_every_option_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # independent intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, TimeSeriesScene)  # independent
        assert app.scenes.current.guided is False
        _pick_every_option_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, TwistRevealScene)
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # decision
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwentyThreeResult)
        assert result.completed_thoughtfully() is True
        assert result.guided_choices == CORRECT_OPTION_BY_REQUEST
        assert result.independent_choices == CORRECT_OPTION_BY_REQUEST
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
