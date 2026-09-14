import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l22_cohort_observatory.requests import CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l22_cohort_observatory.scenario import DECISION_FIELDS, build_lesson_twenty_two_runner
from data_science_arcade.lessons.l22_cohort_observatory.scoring import LessonTwentyTwoResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.cohort_matrix_scene import CohortMatrixScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

from lesson_test_helpers import click_through_mission_briefing


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _pick_option(scene: CohortMatrixScene, option_key: str) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        key = option_key if option_key is not None else CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def _pick_every_option_correctly(scene: CohortMatrixScene) -> None:
    _pick_option(scene, None)


def _confirm_reveal(scene: ComparisonRevealScene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.continue_button.on_activate()


def _fill_out_decision(scene: DecisionBuilderScene) -> None:
    for step in scene._steps:
        if scene._is_evidence_step(step):
            evidence_ids = list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.min_count]
            for item_id in evidence_ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eleven_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_two_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, CohortMatrixScene)  # initial_matrix_pass
        assert app.scenes.current.inner.guided is False
        _pick_every_option_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # horizon_reveal
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # reversal_reveal
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # revision_intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, CohortMatrixScene)  # revision_matrix_pass
        _pick_every_option_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision_brief
        _fill_out_decision(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge - skipped
        app.scenes.current.inner.buttons.buttons[1].on_activate()

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)  # feedback
        app.scenes.current.inner.buttons.buttons[0].on_activate()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwentyTwoResult)
        assert result.completed_thoughtfully() is True
        assert result.initial_cohort_choices == CORRECT_OPTION_BY_REQUEST
        assert result.cohort_choices == CORRECT_OPTION_BY_REQUEST
        assert set(result.decision) >= {field.key for field in DECISION_FIELDS}
        assert collected["decision"] == result.decision
    finally:
        pygame.quit()


def test_the_revision_pass_is_seeded_with_the_initial_passs_own_pick():
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_two_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        initial = app.scenes.current.inner
        _pick_option(initial, "mismatched_month_comparison")

        _confirm_reveal(app.scenes.current.inner)  # horizon_reveal
        _confirm_reveal(app.scenes.current.inner)  # reversal_reveal
        _play_dialogue_to_the_end(app.scenes.current)  # revision_intro

        revision = app.scenes.current.inner
        assert isinstance(revision, CohortMatrixScene)
        assert revision.choices == {"may_retention_comparison": "mismatched_month_comparison"}
    finally:
        pygame.quit()


def test_a_real_revision_can_correct_a_motivated_initial_pick_to_a_fully_defensible_final_one():
    """A student's own first-pass motivated pick becomes something they
    can act on after the two mandatory reveals, never something that
    permanently caps the final result."""
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_two_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        _pick_option(app.scenes.current.inner, "mismatched_month_comparison")  # initial_matrix_pass

        _confirm_reveal(app.scenes.current.inner)  # horizon_reveal
        _confirm_reveal(app.scenes.current.inner)  # reversal_reveal
        _play_dialogue_to_the_end(app.scenes.current)  # revision_intro

        _pick_every_option_correctly(app.scenes.current)  # revision_matrix_pass, corrected this time

        _fill_out_decision(app.scenes.current.inner)  # final_decision_brief

        app.scenes.current.inner.buttons.buttons[1].on_activate()  # mastery_challenge - skipped

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
        app.scenes.current.inner.buttons.buttons[0].on_activate()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        result = finished_results[0]
        assert result.initial_cohort_choices == {"may_retention_comparison": "mismatched_month_comparison"}
        assert result.cohort_choices == CORRECT_OPTION_BY_REQUEST
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
