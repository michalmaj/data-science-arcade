import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l01_question_first.scenario import (
    BRIEF_FIELDS,
    CLAIM_FIELD,
    COVERAGE_INTERPRET_FIELD,
    DECISION_CONFIDENCE_FIELD,
    DECISION_FOLLOW_UP_FIELD,
    DECISION_LIMITATION_FIELD,
    DECISION_RECOMMENDATION_FIELD,
    ENTITY_INTERPRET_OPTIONS,
    ENTITY_REVISION_FIELD,
    GRAIN_REQUESTS,
    INSPECTION_PROMPT,
    MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS,
    WINDOW_CONFIDENCE_BEFORE_FIELD,
    WINDOW_INTERPRET_OPTIONS,
    WINDOW_PREDICTION_FIELD,
    build_lesson_one_runner,
)
from data_science_arcade.lessons.l01_question_first.scoring import LessonOneResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene: DialogueScene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _click(app) -> None:
    app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _fill_out(scene: BriefBuilderScene, field_count: int) -> None:
    for _ in range(field_count):
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def _play_pipeline(scene: PipelineBuilderScene, request_count: int) -> None:
    for _ in range(request_count):
        scene.buttons.buttons[0].on_activate()  # first group-by option
        scene.buttons.buttons[2].on_activate()  # the one aggregate option (both GRAIN_REQUESTS have 2 group-bys)
        scene.next_button.on_activate()


def _play_comparison_reveal(scene: ComparisonRevealScene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.continue_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene) -> None:
    scene.buttons.buttons[0].on_activate()  # claim
    scene.next_button.on_activate()
    evidence_ids = list(scene._evidence_toggle_buttons.keys())
    scene._evidence_toggle_buttons[evidence_ids[0]].on_activate()
    scene._evidence_toggle_buttons[evidence_ids[1]].on_activate()
    scene.next_button.on_activate()
    for _ in range(4):  # limitation, confidence, recommendation, follow_up
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def _play_lesson_to_completion(app, *, skip_mastery: bool = True) -> None:
    runner_scene = app.scenes.current

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # investigation

    assert isinstance(app.scenes.current.inner, WorkbenchScene)
    workbench = app.scenes.current.inner
    next(iter(workbench.inspection_buttons.values())).on_activate()
    workbench.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, PipelineBuilderScene)
    _play_pipeline(app.scenes.current.inner, len(GRAIN_REQUESTS))

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _fill_out(app.scenes.current.inner, len(BRIEF_FIELDS))

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _fill_out(app.scenes.current.inner, 2)  # window prediction + confidence

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner)

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # household reveal

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _fill_out(app.scenes.current.inner, 1)  # entity revision

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner)

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # coverage reveal

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _fill_out(app.scenes.current.inner, 1)  # coverage interpretation

    assert isinstance(app.scenes.current.inner, TwistRevealScene)
    _click(app)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)
    app.scenes.current.inner.continue_button.on_activate()  # evidence review

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)
    _play_decision_builder(app.scenes.current.inner)

    assert isinstance(app.scenes.current.inner, MasteryChallengeScene)
    if skip_mastery:
        app.scenes.current.inner.buttons.buttons[1].on_activate()  # Skip
    else:
        app.scenes.current.inner.buttons.buttons[0].on_activate()  # Engage
        app.scenes.current.inner.buttons.buttons[0].on_activate()  # pick a metric
        app.scenes.current.inner.buttons.buttons[0].on_activate()  # pick an interpretation
        app.scenes.current.inner.finish_button.on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    app.scenes.current.inner.buttons.buttons[0].on_activate()

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

    assert app.scenes.current is not runner_scene


def test_the_full_lesson_plays_through_all_eighteen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_one_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_completion(app)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonOneResult)
        assert result.completed_thoughtfully() is True
        assert set(result.guided_brief) == {field.key for field in BRIEF_FIELDS}
        assert result.mastery_engaged is False
        assert "analytical_context" in collected  # threaded through every analytical stage
    finally:
        pygame.quit()


def test_engaging_the_optional_mastery_challenge_is_reflected_in_the_result():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_one_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_completion(app, skip_mastery=False)

        assert finished_results[0].mastery_engaged is True
    finally:
        pygame.quit()


def test_next_is_disabled_until_a_choice_is_made_on_each_field():
    app = _init_app()
    try:
        runner, _ = build_lesson_one_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        workbench = app.scenes.current.inner
        next(iter(workbench.inspection_buttons.values())).on_activate()
        workbench.continue_button.on_activate()
        _play_pipeline(app.scenes.current.inner, len(GRAIN_REQUESTS))

        brief_scene = app.scenes.current
        assert isinstance(brief_scene.inner, BriefBuilderScene)
        assert brief_scene.next_button.enabled is False

        brief_scene.inner.buttons.buttons[0].on_activate()

        assert brief_scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_the_inspection_prompt_gates_continue_on_the_data_tab():
    app = _init_app()
    try:
        runner, _ = build_lesson_one_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)
        _play_dialogue_to_the_end(app.scenes.current)

        workbench = app.scenes.current.inner
        assert isinstance(workbench, WorkbenchScene)
        assert workbench.continue_button.enabled is False

        next(iter(workbench.inspection_buttons.values())).on_activate()

        assert workbench.continue_button.enabled is True
    finally:
        pygame.quit()


def test_the_evidence_step_only_enables_next_within_its_real_min_max_range():
    app = _init_app()
    try:
        runner, _ = build_lesson_one_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)
        _play_dialogue_to_the_end(app.scenes.current)
        workbench = app.scenes.current.inner
        next(iter(workbench.inspection_buttons.values())).on_activate()
        workbench.continue_button.on_activate()
        _play_pipeline(app.scenes.current.inner, len(GRAIN_REQUESTS))
        _fill_out(app.scenes.current.inner, len(BRIEF_FIELDS))
        _fill_out(app.scenes.current.inner, 2)
        _play_comparison_reveal(app.scenes.current.inner)
        _play_dialogue_to_the_end(app.scenes.current)
        _fill_out(app.scenes.current.inner, 1)
        _play_comparison_reveal(app.scenes.current.inner)
        _play_dialogue_to_the_end(app.scenes.current)
        _fill_out(app.scenes.current.inner, 1)
        _click(app)
        app.scenes.current.inner.continue_button.on_activate()  # evidence review

        decision = app.scenes.current.inner
        assert isinstance(decision, DecisionBuilderScene)
        decision.buttons.buttons[0].on_activate()  # claim
        decision.next_button.on_activate()

        assert decision.next_button.enabled is False  # nothing picked yet

        evidence_ids = list(decision._evidence_toggle_buttons.keys())
        assert len(evidence_ids) >= 4  # grain(2) + window(2) + entity(2) + coverage(1), at least
        decision._evidence_toggle_buttons[evidence_ids[0]].on_activate()

        assert decision.next_button.enabled is False  # 1 selected, min_count=2

        decision._evidence_toggle_buttons[evidence_ids[1]].on_activate()

        assert decision.next_button.enabled is True
    finally:
        pygame.quit()


def test_analytical_context_survives_a_checkpoint_new_app_and_resume():
    # Real cross-process resume, not just a second LessonRunner against the
    # same in-memory App - a fresh App() picks up whatever DEFAULT_SAVE_PATH
    # holds on disk (tests/conftest.py's autouse fixture isolates it to one
    # tmp_path for this whole test), matching test_lesson06_scenario.py's
    # own precedent. Before LessonRunner.on_resume existed, this exact
    # scenario silently lost the whole LessonContext on resume: the only
    # place context.restore_from_dict() was ever called was inside the
    # `briefing` stage factory, which a mid-lesson resume never re-enters.
    app1 = _init_app()
    try:
        runner1, _ = build_lesson_one_runner(app1, on_finished=lambda result: None)
        runner1.start()
        click_through_mission_briefing(app1)
        _play_dialogue_to_the_end(app1.scenes.current)  # briefing
        _play_dialogue_to_the_end(app1.scenes.current)  # investigation

        workbench = app1.scenes.current.inner
        next(iter(workbench.inspection_buttons.values())).on_activate()
        workbench.continue_button.on_activate()

        _play_pipeline(app1.scenes.current.inner, len(GRAIN_REQUESTS))
        _fill_out(app1.scenes.current.inner, len(BRIEF_FIELDS))
        _fill_out(app1.scenes.current.inner, 2)  # window prediction + confidence

        compute_window = app1.scenes.current.inner
        assert isinstance(compute_window, ComparisonRevealScene)
        compute_window.buttons.buttons[0].on_activate()
        compute_window.continue_button.on_activate()  # advances + checkpoints; quit right here
    finally:
        pygame.quit()

    app2 = _init_app()  # a brand new App(), same on-disk save - simulates relaunching
    try:
        runner2, _ = build_lesson_one_runner(app2, on_finished=lambda result: None)
        runner2.start()  # resumes straight into household_reveal, skipping briefing/investigation

        assert isinstance(app2.scenes.current.inner, DialogueScene)  # household_reveal
        _play_dialogue_to_the_end(app2.scenes.current)

        _fill_out(app2.scenes.current.inner, 1)  # revise_entity

        compute_entity = app2.scenes.current.inner
        assert isinstance(compute_entity, ComparisonRevealScene)
        resumed_context = compute_entity.context
        assert len(resumed_context.actions) == 6  # inspection(1) + grain(2) + compute_window(3)
        assert len(resumed_context.evidence) == 2  # compute_window's own 2 real comparisons
        assert "orders.groupby(" in resumed_context.python_mirror()  # grain's real lines survived

        compute_entity.buttons.buttons[0].on_activate()
        compute_entity.continue_button.on_activate()

        _play_dialogue_to_the_end(app2.scenes.current)  # coverage_reveal
        _fill_out(app2.scenes.current.inner, 1)  # coverage_interpret
        _click(app2)  # the_twist
        app2.scenes.current.inner.continue_button.on_activate()  # evidence_review

        decision = app2.scenes.current.inner
        assert isinstance(decision, DecisionBuilderScene)
        pre_resume_labels = {item.label_key for item in resumed_context.evidence}
        post_resume_labels = {item.label_key for item in decision.context.evidence}
        assert pre_resume_labels <= post_resume_labels  # nothing recorded before resume was lost

        decision.buttons.buttons[0].on_activate()  # claim
        decision.next_button.on_activate()  # -> evidence step
        assert len(decision._evidence_toggle_buttons) == 5  # window(2) + entity(2) + coverage(1)
    finally:
        pygame.quit()


@pytest.mark.parametrize(
    "field",
    [
        *BRIEF_FIELDS,
        WINDOW_PREDICTION_FIELD,
        WINDOW_CONFIDENCE_BEFORE_FIELD,
        ENTITY_REVISION_FIELD,
        COVERAGE_INTERPRET_FIELD,
        CLAIM_FIELD,
        DECISION_LIMITATION_FIELD,
        DECISION_CONFIDENCE_FIELD,
        DECISION_RECOMMENDATION_FIELD,
        DECISION_FOLLOW_UP_FIELD,
    ],
)
def test_every_single_select_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


@pytest.mark.parametrize("options", [WINDOW_INTERPRET_OPTIONS, ENTITY_INTERPRET_OPTIONS, MASTERY_METRIC_OPTIONS, MASTERY_INTERPRET_OPTIONS])
def test_every_interpret_or_mastery_option_set_has_at_least_two_options(options):
    assert len(options) >= 2


def test_inspection_prompt_has_at_least_two_options():
    assert len(INSPECTION_PROMPT.options) >= 2


def test_every_grain_request_has_at_least_two_group_by_options():
    for request in GRAIN_REQUESTS:
        assert len(request.group_by_options) >= 2
        assert len(request.aggregate_options) >= 1
