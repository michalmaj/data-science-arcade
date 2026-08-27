import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l12_groupby_kitchen.requests import AGGREGATION_REQUESTS, CORRECT_PIPELINE_BY_REQUEST
from data_science_arcade.lessons.l12_groupby_kitchen.scenario import DECISION_FIELDS, build_lesson_twelve_runner
from data_science_arcade.lessons.l12_groupby_kitchen.scoring import LessonTwelveResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _build_every_pipeline_correctly(scene: PipelineBuilderScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_group_by, correct_aggregate = CORRECT_PIPELINE_BY_REQUEST[request.key]
        group_by_index = next(i for i, option in enumerate(request.group_by_options) if option.key == correct_group_by)
        aggregate_index = next(i for i, option in enumerate(request.aggregate_options) if option.key == correct_aggregate)
        scene.buttons.buttons[group_by_index].on_activate()
        aggregate_button_index = len(request.group_by_options) + aggregate_index
        scene.buttons.buttons[aggregate_button_index].on_activate()
        scene.next_button.on_activate()


def _fill_out_brief(scene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eight_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twelve_runner(
            app, on_finished=lambda result: finished_results.append(result)
        )
        runner.start()

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, PipelineBuilderScene)  # guided
        assert app.scenes.current.guided is True
        _build_every_pipeline_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # independent intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, PipelineBuilderScene)  # independent
        assert app.scenes.current.guided is False
        _build_every_pipeline_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, TwistRevealScene)
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # decision
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwelveResult)
        assert result.completed_thoughtfully() is True
        assert result.guided_choices == CORRECT_PIPELINE_BY_REQUEST
        assert result.independent_choices == CORRECT_PIPELINE_BY_REQUEST
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_every_aggregation_request_is_used_in_the_scenario():
    assert {request.key for request in AGGREGATION_REQUESTS} == set(CORRECT_PIPELINE_BY_REQUEST)
