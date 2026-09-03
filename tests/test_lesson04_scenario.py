import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l04_event_log_factory.scenario import (
    EVENT_A_INTERPRET_OPTIONS,
    KNOWN_GAP_FIELD,
    MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS,
    NOT_COLLECTED_FIELD,
    QUESTIONS_ANSWERABLE_FIELD,
    REQUIRED_CHANGE_FIELD,
    SHIP_READINESS_FIELD,
    build_lesson_four_runner,
)
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l04_event_log_factory.scoring import LessonFourResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _play_spec_builder(scene: BriefBuilderScene, *, spec_indices: dict) -> None:
    """spec_indices: field.key -> option index, or a tuple of indices for
    the one MultiChoiceField (payment_b_properties)."""
    for field in scene.fields:
        indices = spec_indices[field.key]
        if isinstance(indices, tuple):
            for index in indices:
                scene.buttons.buttons[index].on_activate()
        else:
            scene.buttons.buttons[indices].on_activate()
        scene.next_button.on_activate()


def _fill_out(scene: BriefBuilderScene, field_count: int, option_index: int = 0) -> None:
    for _ in range(field_count):
        scene.buttons.buttons[option_index].on_activate()
        scene.next_button.on_activate()


def _play_comparison_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = next(i for i, option in enumerate(scene.interpret_options) if option.key == interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_indices: dict) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            evidence_ids = list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.max_count]
            for item_id in evidence_ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[decision_indices[step.key]].on_activate()
        scene.next_button.on_activate()


_DEFAULT_CLEAN_SPEC = {
    "order_a_trigger": 0,
    "order_a_identifiers": 0,
    "payment_b_trigger": 0,
    "payment_b_identifiers": 0,
    "payment_b_properties": (0, 1),
    "data_minimization": 0,
}
_DEFAULT_CLEAN_DECISION = {
    "ship_readiness": 0,
    "questions_answerable": 0,
    "known_gap": 3,
    "required_change": 0,
    "not_collected": 0,
}


def _play_lesson_to_feedback(
    app,
    *,
    spec_indices: dict | None = None,
    gut_check_index: int = 0,
    interpret_key: str = "no_real_gap",
    decision_indices: dict | None = None,
    skip_mastery: bool = True,
    mastery_metric_index: int = 0,
    mastery_interpret_index: int = 0,
) -> LessonFeedbackScene:
    """Plays through every stage up to and including LessonFeedbackScene,
    stopping there (its own evaluation already computed) rather than
    clicking past it - continuing on to debrief would finish the lesson
    and leave nothing but MainMenuScene for a caller to inspect."""
    spec_indices = _DEFAULT_CLEAN_SPEC if spec_indices is None else spec_indices
    decision_indices = _DEFAULT_CLEAN_DECISION if decision_indices is None else decision_indices

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # framing

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _play_spec_builder(app.scenes.current.inner, spec_indices=spec_indices)  # spec builder

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _fill_out(app.scenes.current.inner, 1, gut_check_index)  # gut check

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner, interpret_key)  # event A reveal

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # root cause confirmed

    assert isinstance(app.scenes.current.inner, WorkbenchScene)
    app.scenes.current.inner.continue_button.on_activate()  # evidence review

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)
    _play_decision_builder(app.scenes.current.inner, decision_indices=decision_indices)

    assert isinstance(app.scenes.current.inner, MasteryChallengeScene)
    mastery = app.scenes.current.inner
    if skip_mastery:
        mastery.buttons.buttons[1].on_activate()  # Skip
    else:
        mastery.buttons.buttons[0].on_activate()  # Engage
        mastery.buttons.buttons[mastery_metric_index].on_activate()
        mastery.buttons.buttons[mastery_interpret_index].on_activate()
        mastery.finish_button.on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def _finish_from_feedback(app) -> None:
    app.scenes.current.inner.buttons.buttons[0].on_activate()
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes


def test_the_full_lesson_plays_through_all_eleven_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_four_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(app)
        _finish_from_feedback(app)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonFourResult)
        assert result.completed_thoughtfully() is True
        assert result.event_a_clean is True
        assert result.outcome_captured is True
        assert "analytical_context" in collected
    finally:
        pygame.quit()


def test_analytical_context_survives_a_checkpoint_new_app_and_resume():
    # Real cross-process resume - a fresh App() picks up whatever
    # DEFAULT_SAVE_PATH holds on disk (tests/conftest.py's autouse fixture
    # isolates it to one tmp_path for this whole test).
    app1 = _init_app()
    try:
        runner1, _ = build_lesson_four_runner(app1, on_finished=lambda result: None)
        runner1.start()
        click_through_mission_briefing(app1)
        _play_dialogue_to_the_end(app1.scenes.current)  # briefing
        _play_dialogue_to_the_end(app1.scenes.current)  # framing
        _play_spec_builder(app1.scenes.current.inner, spec_indices=_DEFAULT_CLEAN_SPEC)
        _fill_out(app1.scenes.current.inner, 1)  # gut check

        reveal = app1.scenes.current.inner
        assert isinstance(reveal, ComparisonRevealScene)
        reveal.buttons.buttons[0].on_activate()
        reveal.continue_button.on_activate()  # advances + checkpoints; quit right here
    finally:
        pygame.quit()

    app2 = _init_app()  # a brand new App(), same on-disk save - simulates relaunching
    try:
        runner2, _ = build_lesson_four_runner(app2, on_finished=lambda result: None)
        runner2.start()  # resumes straight into root_cause_confirmed, skipping everything before it

        root_cause = app2.scenes.current.inner
        assert isinstance(root_cause, DialogueScene)
        resumed_context = root_cause.context
        assert len(resumed_context.actions) >= 1  # the reveal's own real actions
        assert len(resumed_context.evidence) >= 2  # the reveal's own 2 real values
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", [SHIP_READINESS_FIELD, QUESTIONS_ANSWERABLE_FIELD, KNOWN_GAP_FIELD, REQUIRED_CHANGE_FIELD, NOT_COLLECTED_FIELD])
def test_every_single_select_decision_field_has_at_least_three_options(field):
    assert len(field.options) >= 3


def test_event_a_interpret_options_cover_all_three_real_states_plus_a_decoy():
    keys = {option.key for option in EVENT_A_INTERPRET_OPTIONS}
    assert keys == {"no_real_gap", "duplicate_trigger", "cannot_verify_orders", "out_of_order_arrival"}


def test_mastery_metric_and_interpret_options_are_both_real_choices():
    assert len(MASTERY_METRIC_OPTIONS) == 2
    assert len(MASTERY_INTERPRET_OPTIONS) == 2


def test_a_fully_correct_playthrough_scores_high_on_every_dimension():
    app = _init_app()
    try:
        runner, _ = build_lesson_four_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app, skip_mastery=False, mastery_metric_index=1, mastery_interpret_index=1)

        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.DATA_QUALITY] >= 85, scores
        assert scores[ScoreDimension.REPRODUCIBILITY] >= 85, scores
        assert scores[ScoreDimension.EVIDENCE] >= 85, scores
        assert scores[ScoreDimension.UNCERTAINTY] >= 80, scores
        assert scores[ScoreDimension.REASONING] >= 85, scores
        assert any(o.text_key == "lesson.l04.feedback.mastery_solved" for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_a_weak_playthrough_scores_low_on_every_dimension():
    app = _init_app()
    try:
        runner, _ = build_lesson_four_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        weak_spec = {
            "order_a_trigger": 1,  # client_click - wrong
            "order_a_identifiers": 1,  # session_only - wrong
            "payment_b_trigger": 2,  # only_approved - wrong
            "payment_b_identifiers": 1,  # session_only - wrong
            "payment_b_properties": (3, 4),  # decline_reason_detail, raw_card_number - misses outcome, includes the privacy decoy
            "data_minimization": 1,  # always_collect_more - wrong
        }
        weak_decision = {
            "ship_readiness": 2,  # monitor_after_launch - never the best choice
            "questions_answerable": 0,  # all_three_clean - overreach, nothing is actually clean here
            "known_gap": 1,  # never_know_failures - overstates permanence
            "required_change": 3,  # redesign_from_scratch - unsupported overreach
            "not_collected": 1,  # capture_everything - the "just in case" overreach
        }
        feedback = _play_lesson_to_feedback(
            app,
            spec_indices=weak_spec,
            gut_check_index=0,
            interpret_key="out_of_order_arrival",
            decision_indices=weak_decision,
        )

        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.DATA_QUALITY] <= 40, scores
        assert scores[ScoreDimension.REPRODUCIBILITY] <= 40, scores
        assert scores[ScoreDimension.UNCERTAINTY] <= 30, scores
    finally:
        pygame.quit()


def test_client_trigger_path_scores_reasoning_dimensions_high_despite_a_lower_data_quality():
    # Productive failure: a real, well-reasoned argument about a worse
    # spec still scores well on everything except DATA_QUALITY, which is
    # the one dimension that actually reflects the spec's own mistakes.
    app = _init_app()
    try:
        runner, _ = build_lesson_four_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        spec = dict(_DEFAULT_CLEAN_SPEC, order_a_trigger=1, payment_b_properties=(1, 2))  # client_click; no outcome
        decision = {
            "ship_readiness": 1,  # ship_with_fix
            "questions_answerable": 1,  # pm_support_once_fixed
            "known_gap": 0,  # decline_reason_unknown
            "required_change": 1,  # fix_trigger_and_identifiers
            "not_collected": 0,
        }
        feedback = _play_lesson_to_feedback(
            app, spec_indices=spec, interpret_key="duplicate_trigger", decision_indices=decision
        )

        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.DATA_QUALITY] < 90, scores  # the spec really was worse
        assert scores[ScoreDimension.REPRODUCIBILITY] >= 85, scores
        assert scores[ScoreDimension.EVIDENCE] >= 85, scores
        assert scores[ScoreDimension.UNCERTAINTY] >= 80, scores
        assert scores[ScoreDimension.REASONING] >= 85, scores
    finally:
        pygame.quit()


def test_identifiers_wrong_path_has_a_real_and_different_critical_evidence_fact():
    app = _init_app()
    try:
        finished = []
        runner, _ = build_lesson_four_runner(app, on_finished=lambda result: finished.append(result))
        runner.start()
        click_through_mission_briefing(app)
        spec = dict(_DEFAULT_CLEAN_SPEC, order_a_identifiers=1, payment_b_properties=(1, 2))  # session_only; no outcome
        decision = {
            "ship_readiness": 1,
            "questions_answerable": 1,
            "known_gap": 0,
            "required_change": 1,
            "not_collected": 0,
        }
        _play_lesson_to_feedback(app, spec_indices=spec, interpret_key="cannot_verify_orders", decision_indices=decision)
        _finish_from_feedback(app)

        result = finished[0]
        assert result.event_a_clean is False
        assert "event_a_gap" in result.critical_evidence_present
        assert "distinct" in result.critical_evidence_present
    finally:
        pygame.quit()


def test_evidence_pool_has_no_event_a_gap_fact_on_the_clean_path():
    app = _init_app()
    try:
        finished = []
        runner, _ = build_lesson_four_runner(app, on_finished=lambda result: finished.append(result))
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app)
        _finish_from_feedback(app)

        result = finished[0]
        assert "event_a_gap" not in result.critical_evidence_present
        assert set(result.critical_evidence_present) == {"distinct", "event_b_outcome"}
    finally:
        pygame.quit()


def test_reasoning_scores_low_for_the_duplication_means_untrustworthy_decoy():
    app = _init_app()
    try:
        runner, _ = build_lesson_four_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        decision = dict(_DEFAULT_CLEAN_DECISION, known_gap=2)  # duplication_means_untrustworthy
        feedback = _play_lesson_to_feedback(app, decision_indices=decision)

        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.REASONING] <= 30, scores
    finally:
        pygame.quit()


def test_reasoning_scores_low_when_questions_answerable_disagrees_with_known_gap():
    app = _init_app()
    try:
        runner, _ = build_lesson_four_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        # all_three_clean implies outcome_captured=True, but known_gap here
        # names the not-captured gap - a real, direct disagreement.
        decision = dict(_DEFAULT_CLEAN_DECISION, questions_answerable=0, known_gap=0)
        feedback = _play_lesson_to_feedback(app, decision_indices=decision)

        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.REASONING] <= 35, scores
    finally:
        pygame.quit()


def test_mastery_solved_requires_the_correct_metric_and_interpretation_together():
    app = _init_app()
    try:
        finished = []
        runner, _ = build_lesson_four_runner(app, on_finished=lambda result: finished.append(result))
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, skip_mastery=False, mastery_metric_index=1, mastery_interpret_index=1)
        _finish_from_feedback(app)

        result = finished[0]
        assert result.mastery_engaged is True
        assert result.mastery_metric == "distinct_user_id_count"
        assert result.mastery_interpretation == "some_signups_double_counted"
    finally:
        pygame.quit()


def test_mastery_attempted_when_the_interpretation_comes_from_the_wrong_metric():
    app = _init_app()
    try:
        runner, _ = build_lesson_four_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        # metric index 0 = raw_account_created_count (wrong), interpret
        # index 1 = some_signups_double_counted (the right-looking answer,
        # but not actually justified by the wrong metric).
        feedback = _play_lesson_to_feedback(app, skip_mastery=False, mastery_metric_index=0, mastery_interpret_index=1)

        observations = feedback.evaluation.observations
        assert any(o.text_key == "lesson.l04.feedback.mastery_attempted" for o in observations)
        assert not any(o.text_key == "lesson.l04.feedback.mastery_solved" for o in observations)
    finally:
        pygame.quit()
