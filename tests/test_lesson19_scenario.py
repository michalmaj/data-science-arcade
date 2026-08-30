import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l19_power_plant.experiments import SAMPLING_GROUPS, STEP, TOTAL_WEEKS
from data_science_arcade.lessons.l19_power_plant.scenario import DECISION_FIELDS, build_lesson_nineteen_runner
from data_science_arcade.lessons.l19_power_plant.scoring import LessonNineteenResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.sampling_allocator_scene import SamplingAllocatorScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

from lesson_test_helpers import click_through_mission_briefing

EVEN_SPLIT = TOTAL_WEEKS // len(SAMPLING_GROUPS)
assert EVEN_SPLIT % STEP == 0  # otherwise an even split couldn't be reached with whole steps


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _spend_the_whole_budget_evenly(scene: SamplingAllocatorScene) -> None:
    for group in SAMPLING_GROUPS:
        for _ in range(EVEN_SPLIT // STEP):
            scene.plus_buttons[group.key].on_activate()
    scene.confirm_button.on_activate()


def _fill_out_brief(scene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eight_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_nineteen_runner(
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

        assert isinstance(app.scenes.current.inner, SamplingAllocatorScene)  # guided
        assert app.scenes.current.guided is True
        _spend_the_whole_budget_evenly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # independent intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, SamplingAllocatorScene)  # independent
        assert app.scenes.current.guided is False
        _spend_the_whole_budget_evenly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, TwistRevealScene)
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # decision
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonNineteenResult)
        assert result.completed_thoughtfully() is True
        expected_allocation = {group.key: EVEN_SPLIT for group in SAMPLING_GROUPS}
        assert result.guided_allocation == expected_allocation
        assert result.independent_allocation == expected_allocation
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_the_budget_divides_evenly_across_every_experiment_in_whole_steps():
    assert TOTAL_WEEKS % len(SAMPLING_GROUPS) == 0
    assert EVEN_SPLIT % STEP == 0
