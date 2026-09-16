import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l25_kpi_emergency_room.requests import CORRECT_METRIC_BY_REQUEST
from data_science_arcade.lessons.l25_kpi_emergency_room.scenario import DECISION_FIELDS, build_lesson_twenty_five_runner
from data_science_arcade.lessons.l25_kpi_emergency_room.scoring import LessonTwentyFiveResult
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
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


def _pick_requests(scene: AlertConfigScene, all_correct: bool) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_metric = CORRECT_METRIC_BY_REQUEST[request.key]
        use_metric = correct_metric if all_correct else next(o.key for o in request.metric_options if o.key != correct_metric)
        metric_index = next(i for i, option in enumerate(request.metric_options) if option.key == use_metric)
        scene.buttons.buttons[metric_index].on_activate()
        scene.buttons.buttons[len(request.metric_options)].on_activate()  # threshold - either is fine, METHOD ignores it
        scene.next_button.on_activate()


def _confirm_reveal(scene: ComparisonRevealScene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.continue_button.on_activate()


def _fill_out_decision(scene: DecisionBuilderScene) -> None:
    from data_science_arcade.lessons.framework.brief import MultiChoiceField

    for step in scene._steps:
        if scene._is_evidence_step(step):
            evidence_ids = list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.min_count]
            for item_id in evidence_ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        elif isinstance(step, MultiChoiceField):
            for i in range(step.min_count):
                scene.buttons.buttons[i].on_activate()
        else:
            scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_eleven_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_five_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, AlertConfigScene)  # initial_monitoring_pass
        assert app.scenes.current.inner.guided is False
        _pick_requests(app.scenes.current.inner, all_correct=True)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # threshold_tradeoff_reveal
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # incident_coverage_reveal
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # revision_intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, AlertConfigScene)  # revision_monitoring_pass
        _pick_requests(app.scenes.current.inner, all_correct=True)

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
        assert isinstance(result, LessonTwentyFiveResult)
        assert result.completed_thoughtfully() is True
        for key, correct_metric in CORRECT_METRIC_BY_REQUEST.items():
            assert result.initial_monitoring_choices[key][0] == correct_metric
            assert result.monitoring_choices[key][0] == correct_metric
        assert set(result.decision) >= {field.key for field in DECISION_FIELDS}
        assert collected["decision"] == result.decision
    finally:
        pygame.quit()


def test_the_revision_pass_is_seeded_with_the_initial_passs_own_pick():
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_five_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        initial = app.scenes.current.inner
        _pick_requests(initial, all_correct=False)

        _confirm_reveal(app.scenes.current.inner)  # threshold_tradeoff_reveal
        _confirm_reveal(app.scenes.current.inner)  # incident_coverage_reveal
        _play_dialogue_to_the_end(app.scenes.current)  # revision_intro

        revision = app.scenes.current.inner
        assert isinstance(revision, AlertConfigScene)
        for key, correct_metric in CORRECT_METRIC_BY_REQUEST.items():
            assert revision.choices[key][0] != correct_metric
    finally:
        pygame.quit()


def test_a_real_revision_can_correct_a_motivated_initial_pick_to_a_fully_defensible_final_one():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_five_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        _pick_requests(app.scenes.current.inner, all_correct=False)  # initial_monitoring_pass

        _confirm_reveal(app.scenes.current.inner)  # threshold_tradeoff_reveal
        _confirm_reveal(app.scenes.current.inner)  # incident_coverage_reveal
        _play_dialogue_to_the_end(app.scenes.current)  # revision_intro

        _pick_requests(app.scenes.current.inner, all_correct=True)  # revision_monitoring_pass, corrected this time

        _fill_out_decision(app.scenes.current.inner)  # final_decision_brief

        app.scenes.current.inner.buttons.buttons[1].on_activate()  # mastery_challenge - skipped

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
        app.scenes.current.inner.buttons.buttons[0].on_activate()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        result = finished_results[0]
        for key, correct_metric in CORRECT_METRIC_BY_REQUEST.items():
            assert result.initial_monitoring_choices[key][0] != correct_metric
            assert result.monitoring_choices[key][0] == correct_metric
    finally:
        pygame.quit()


def test_reveal_computations_never_mutate_the_final_monitoring_choice_mirror_state():
    """The interactive pick's own action key (alert_pick_*) must reflect
    only the real final choice - the two reveals record entirely
    separate keys and must never touch it."""
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_five_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        _pick_requests(app.scenes.current.inner, all_correct=True)  # initial_monitoring_pass

        pick_actions = [a for a in collected["analytical_context"]["actions"] if a["key"] == "alert_pick_checkout_incident_focus"]
        assert len(pick_actions) == 1
        code_after_initial = pick_actions[0]["python_code"]

        _confirm_reveal(app.scenes.current.inner)  # threshold_tradeoff_reveal
        _confirm_reveal(app.scenes.current.inner)  # incident_coverage_reveal

        pick_actions_after_reveals = [a for a in collected["analytical_context"]["actions"] if a["key"] == "alert_pick_checkout_incident_focus"]
        assert len(pick_actions_after_reveals) == 1
        assert pick_actions_after_reveals[0]["python_code"] == code_after_initial
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
