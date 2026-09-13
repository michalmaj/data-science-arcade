import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.power import proportion_difference_ci
from data_science_arcade.lessons.l20_ab_test_commander import data as d
from data_science_arcade.lessons.l20_ab_test_commander.scenario import DECISION_FIELDS, RECOMMENDATION_OPTIONS, build_lesson_twenty_runner
from data_science_arcade.lessons.l20_ab_test_commander.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    DECISION_PROTOCOL_EVIDENCE_KEY,
    LessonTwentyResult,
)
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.experiment_monitor_scene import ExperimentMonitorScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

GOOD_DECISION = {
    "final_verdict": "hold_full_rollout_investigate_support_guardrail",
    "why_not_a_clean_ship": "the_launch_rule_requires_every_guardrail_to_hold_too",
    "week3_stopping_rule_judgment": "no_efficacy_stopping_rule_was_pre_specified",
    "general_stopping_principle": "only_a_pre_specified_rule_efficacy_or_safety_justifies_acting_early",
    "what_explains_week3_vs_week7": "the_cumulative_estimate_moved_as_more_data_arrived_early_estimates_are_noisier",
    "why_guardrail_only_visible_at_week7": "the_support_harm_was_smaller_than_the_primary_lift_and_the_larger_sample_narrowed_its_interval_enough_to_clear_the_threshold",
}
GOOD_MASTERY_STOPPING_JUDGMENT = "stop_now_pre_specified_safety_rule_is_met"
GOOD_MASTERY_CONTRAST = "a_safety_rule_was_pre_specified_here_efficacy_never_was_for_quickpay"
GOOD_MASTERY_EVIDENCE = ("interim_ci_entirely_above_the_prespecified_1pp_threshold", "the_safety_rule_was_pre_specified_before_the_test_started")


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _option_index(field_or_options, option_key: str) -> int:
    options = field_or_options.options if hasattr(field_or_options, "options") else field_or_options
    return next(i for i, option in enumerate(options) if option.key == option_key)


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _play_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict, evidence_ids: list[str] | None = None) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            ids = evidence_ids if evidence_ids is not None else list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.max_count]
            for item_id in ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_mastery_select(scene: BriefBuilderScene, stopping_judgment_key: str, contrast_key: str, evidence_keys: tuple[str, ...]) -> None:
    judgment_field = scene.fields[0]
    scene.buttons.buttons[_option_index(judgment_field, stopping_judgment_key)].on_activate()
    scene.next_button.on_activate()
    contrast_field = scene.fields[1]
    scene.buttons.buttons[_option_index(contrast_field, contrast_key)].on_activate()
    scene.next_button.on_activate()
    evidence_field = scene.fields[2]
    for key in evidence_keys:
        scene.buttons.buttons[_option_index(evidence_field, key)].on_activate()
    scene.next_button.on_activate()


def _play_monitor_checkpoint(scene: ExperimentMonitorScene, recommendation_key: str | None) -> None:
    if recommendation_key is not None:
        index = _option_index(RECOMMENDATION_OPTIONS, recommendation_key)
        scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    week1_recommendation: str = "not_sure_yet",
    week3_recommendation: str = "hold_keep_running",
    interpret_key: str = "the_larger_later_sample_is_more_reliable_not_because_week3_was_fake",
    decision: dict | None = None,
    evidence_ids: list[str] | None = None,
    mastery_engage: bool = False,
    mastery_stopping_judgment: str = GOOD_MASTERY_STOPPING_JUDGMENT,
    mastery_contrast: str = GOOD_MASTERY_CONTRAST,
    mastery_evidence: tuple[str, ...] = GOOD_MASTERY_EVIDENCE,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
    _play_dialogue_to_the_end(app.scenes.current)

    monitor = app.scenes.current.inner  # experiment_monitoring
    assert isinstance(monitor, ExperimentMonitorScene)
    assert monitor._current_checkpoint().week == 1
    _play_monitor_checkpoint(monitor, week1_recommendation)
    assert monitor._current_checkpoint().week == 3
    _play_monitor_checkpoint(monitor, week3_recommendation)
    assert monitor._current_checkpoint().week == 7
    _play_monitor_checkpoint(monitor, None)

    contrast = app.scenes.current.inner  # week3_vs_week7_contrast_reveal
    assert isinstance(contrast, ComparisonRevealScene)
    _play_reveal(contrast, interpret_key)

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision_brief
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision or GOOD_DECISION, evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()
        select_scene = mastery_offer._active
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_stopping_judgment, mastery_contrast, mastery_evidence)
    else:
        mastery_offer.buttons.buttons[1].on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_with_a_correct_final_verdict():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwentyResult)
        assert result.completed_thoughtfully() is True
        assert result.week1_recommendation == "not_sure_yet"
        assert result.week3_recommendation == "hold_keep_running"
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert result.mastery_engaged is True
        assert collected is not None
    finally:
        pygame.quit()


def test_decision_protocol_evidence_is_recorded_before_any_checkpoint_data():
    """The protocol fact (no pre-specified efficacy stop; planned end is
    week 7) is recorded by the investigation stage, structurally before
    the experiment_monitoring stage even starts - not just orderable by
    coincidence."""
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        investigation_scene = app.scenes.current.inner
        assert isinstance(investigation_scene, DialogueScene)
        _play_dialogue_to_the_end(app.scenes.current)

        monitor = app.scenes.current.inner
        assert isinstance(monitor, ExperimentMonitorScene)
        assert any(action.key == "decision_protocol" for action in monitor.context.actions)
        assert any(item.label_key == DECISION_PROTOCOL_EVIDENCE_KEY for item in monitor.context.evidence)
    finally:
        pygame.quit()


def test_evidence_is_available_regardless_of_the_contrast_reveal_interpretation():
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(app, interpret_key="week3_should_be_trusted_because_it_came_first")

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        evidence_label_keys = {item.label_key for item in restored_context.evidence}
        for critical_key in CRITICAL_EVIDENCE_KEYS:
            assert critical_key in evidence_label_keys
    finally:
        pygame.quit()


@pytest.mark.parametrize(
    "week1_recommendation,week3_recommendation",
    [
        ("ship_now", "ship_now"),
        ("not_sure_yet", "hold_keep_running"),
        ("hold_keep_running", "ship_now"),
    ],
)
def test_python_mirror_final_state_never_overwritten_by_interim_checkpoints(week1_recommendation, week3_recommendation):
    """The recurring L18 canonical-substitution bug class, guarded against
    proactively: regardless of what a student recommends at week 1/3, the
    full recorded mirror's own bare canonical variables (primary_diff,
    support_ci_lower, ...) must reflect the real week-7 values, never a
    week1_*/week3_*-prefixed one."""
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(app, week1_recommendation=week1_recommendation, week3_recommendation=week3_recommendation)

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])

        namespace: dict = {"proportion_difference_ci": proportion_difference_ci}
        exec(restored_context.python_mirror(), namespace)

        dataset = d.generate_checkout_experiment()
        for metric_key in d.METRIC_KEYS:
            expected_diff, expected_lo, expected_hi = d.diff_and_ci_at_checkpoint(dataset, d.PLANNED_END_WEEK, metric_key)
            assert namespace[f"{metric_key}_diff"] == pytest.approx(expected_diff)
            assert namespace[f"{metric_key}_ci_lower"] == pytest.approx(expected_lo)
            assert namespace[f"{metric_key}_ci_upper"] == pytest.approx(expected_hi)

        # And the week1_*/week3_* prefixed variables exist separately -
        # proving the bare names above are the real final state, not just
        # the only names ever assigned.
        assert "week1_primary_diff" in namespace
        assert "week3_primary_diff" in namespace
    finally:
        pygame.quit()


def test_mastery_requires_the_correct_judgment_contrast_and_both_evidence_facts():
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(
            app,
            mastery_engage=True,
            mastery_stopping_judgment=GOOD_MASTERY_STOPPING_JUDGMENT,
            mastery_contrast=GOOD_MASTERY_CONTRAST,
            mastery_evidence=GOOD_MASTERY_EVIDENCE,
        )
        assert isinstance(feedback, LessonFeedbackScene)
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
