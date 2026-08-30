import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l06_schema_repair_shop.sales_export import REPAIR_ISSUES
from data_science_arcade.lessons.l06_schema_repair_shop.scenario import DECISION_FIELDS, build_lesson_six_runner
from data_science_arcade.lessons.l06_schema_repair_shop.scoring import LessonSixResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing

CORRECT_RESOLUTION = {issue.column: issue.options[0].key for issue in REPAIR_ISSUES}


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _repair_every_issue_correctly(scene: WorkbenchScene) -> None:
    for _ in REPAIR_ISSUES:
        # Any still-flagged cell button opens that column's picker; which
        # issue it turns out to be doesn't matter here since every issue's
        # own first option is the correct one.
        flagged_cell = _first_flagged_cell_button(scene)
        flagged_cell.on_activate()
        assert scene.active_issue is not None
        correct_key = scene.active_issue.options[0].key
        scene.picker_buttons[correct_key].on_activate()


def _first_flagged_cell_button(scene: WorkbenchScene):
    chrome_labels = {scene.app.localization.t(key) for key in ("workbench.data.view_table", "workbench.data.view_schema", "workbench.continue")}
    tab_labels = {scene.app.localization.t(tab.value) for tab in type(scene.active_tab)}
    for button in scene.buttons.buttons:
        if button.label not in chrome_labels and button.label not in tab_labels:
            return button
    raise AssertionError("no flagged cell button found")


def _fill_out_brief(scene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eight_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_six_runner(
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

        assert isinstance(app.scenes.current.inner, WorkbenchScene)  # guided
        guided_scene = app.scenes.current.inner
        assert guided_scene.guided is True
        _repair_every_issue_correctly(guided_scene)
        assert len(guided_scene.context.actions) == len(REPAIR_ISSUES)
        assert len(guided_scene.context.evidence) == len(REPAIR_ISSUES)
        app.scenes.current.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # independent intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, WorkbenchScene)  # independent
        independent_scene = app.scenes.current.inner
        assert independent_scene.guided is False
        # Persistence proof: the independent round's context already holds
        # the guided round's actions/evidence before the player has done
        # anything independently - same shared LessonContext, not a fresh
        # one per stage.
        assert independent_scene.context is guided_scene.context
        assert len(independent_scene.context.actions) == len(REPAIR_ISSUES)
        _repair_every_issue_correctly(independent_scene)
        # Dedup proof: both rounds resolved every issue with the same
        # (correct, options[0]) pick, so the shared context must not have
        # doubled - same count as after the guided round alone.
        assert len(independent_scene.context.actions) == len(REPAIR_ISSUES)
        assert len(independent_scene.context.evidence) == len(REPAIR_ISSUES)
        app.scenes.current.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, TwistRevealScene)
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # decision
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonSixResult)
        assert result.completed_thoughtfully() is True
        assert result.guided_resolution == CORRECT_RESOLUTION
        assert result.independent_resolution == CORRECT_RESOLUTION
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_analytical_context_survives_a_checkpoint_new_app_and_resume():
    # Real cross-process resume, not just a second LessonRunner against the
    # same in-memory App: a fresh App() picks up whatever the redirected
    # DEFAULT_SAVE_PATH holds on disk (tests/conftest.py's autouse fixture
    # points it at one tmp_path for this whole test), matching how PR A's
    # own manual end-to-end verification simulated a real relaunch.
    app1 = _init_app()
    try:
        runner1, _ = build_lesson_six_runner(app1, on_finished=lambda result: None)
        runner1.start()
        click_through_mission_briefing(app1)
        _play_dialogue_to_the_end(app1.scenes.current)  # briefing
        _play_dialogue_to_the_end(app1.scenes.current)  # investigation

        assert isinstance(app1.scenes.current.inner, WorkbenchScene)  # guided
        _repair_every_issue_correctly(app1.scenes.current)
        app1.scenes.current.continue_button.on_activate()  # advances + checkpoints; quit right here
    finally:
        pygame.quit()

    app2 = _init_app()  # a brand new App(), same on-disk save - simulates relaunching
    try:
        runner2, _ = build_lesson_six_runner(app2, on_finished=lambda result: None)
        runner2.start()  # resumes straight into independent_intro, skipping the briefing

        assert isinstance(app2.scenes.current.inner, DialogueScene)  # independent intro
        _play_dialogue_to_the_end(app2.scenes.current)

        assert isinstance(app2.scenes.current.inner, WorkbenchScene)  # independent
        resumed_context = app2.scenes.current.inner.context
        assert len(resumed_context.actions) == len(REPAIR_ISSUES)
        assert len(resumed_context.evidence) == len(REPAIR_ISSUES)
    finally:
        pygame.quit()
