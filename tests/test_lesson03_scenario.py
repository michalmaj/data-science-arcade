import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l03_api_courier.scenario import (
    DECISION_FIELDS,
    REQUEST_ATTEMPTS,
    build_lesson_three_runner,
)
from data_science_arcade.lessons.l03_api_courier.scoring import LessonThreeResult
from data_science_arcade.ui.api_console_scene import APIConsoleScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

EXPECTED_TOTAL = sum(a.records_returned for a in REQUEST_ATTEMPTS if a.is_success)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _play_out_the_console(scene) -> None:
    for _ in REQUEST_ATTEMPTS:
        scene.action_button.on_activate()
    scene.action_button.on_activate()  # now showing Finish


def _fill_out_brief(scene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eight_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_three_runner(
            app, on_finished=lambda result: finished_results.append(result)
        )
        runner.start()

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, APIConsoleScene)  # guided
        assert app.scenes.current.guided is True
        _play_out_the_console(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # independent intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, APIConsoleScene)  # independent
        assert app.scenes.current.guided is False
        _play_out_the_console(app.scenes.current)

        assert isinstance(app.scenes.current.inner, TwistRevealScene)
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # decision
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonThreeResult)
        assert result.completed_thoughtfully() is True
        assert result.guided_records_collected == EXPECTED_TOTAL
        assert result.independent_records_collected == EXPECTED_TOTAL
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_request_attempts_add_up_to_a_shortfall_not_a_clean_total():
    assert EXPECTED_TOTAL == 92  # not 100 - that's the whole point
