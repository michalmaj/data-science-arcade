import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l02_source_scout.scenario import (
    ANSWER_STRATEGY_FIELD,
    BILLING_REQUESTS,
    COMPARISON_1_INTERPRET_OPTIONS,
    COMPARISON_2_INTERPRET_OPTIONS,
    GAP_INTERPRET_OPTIONS,
    KNOWN_GAP_FIELD,
    MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS,
    NOT_SAFE_TO_CLAIM_FIELD,
    RECOMMENDATION_FIELD,
    REVISION_FIELD,
    SAFE_TO_CLAIM_FIELD,
    SOURCES,
    SUPPORT_INTERPRET_OPTIONS,
    build_lesson_two_runner,
)
from data_science_arcade.lessons.l02_source_scout.scoring import LessonTwoResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.ui.source_board_scene import SourceBoardScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing

L02_STAGE_FINGERPRINT = "|".join(
    [
        "briefing",
        "framing",
        "source_map",
        "meet_billing",
        "compute_billing",
        "meet_app_log",
        "comparison_1",
        "comparison_2",
        "gap_discovery",
        "finance_lead_confirms",
        "gut_check",
        "support_list",
        "evidence_review",
        "final_decision",
        "mastery_challenge",
        "feedback",
        "debrief",
    ]
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene: DialogueScene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _pick_a_source(scene: SourceBoardScene) -> None:
    scene.source_buttons[SOURCES[0].key].on_activate()
    scene.confirm_button.on_activate()


def _play_inspection_workbench(scene: WorkbenchScene) -> None:
    next(iter(scene.inspection_buttons.values())).on_activate()
    scene.continue_button.on_activate()


def _play_pipeline(scene: PipelineBuilderScene) -> None:
    scene.buttons.buttons[0].on_activate()  # first group-by option
    scene.buttons.buttons[2].on_activate()  # the one aggregate option
    scene.next_button.on_activate()


def _play_comparison_reveal(scene: ComparisonRevealScene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.continue_button.on_activate()


def _fill_out(scene: BriefBuilderScene, field_count: int) -> None:
    for _ in range(field_count):
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene) -> None:
    scene.buttons.buttons[0].on_activate()  # answer_strategy
    scene.next_button.on_activate()
    evidence_ids = list(scene._evidence_toggle_buttons.keys())
    scene._evidence_toggle_buttons[evidence_ids[0]].on_activate()
    scene._evidence_toggle_buttons[evidence_ids[1]].on_activate()
    scene.next_button.on_activate()
    for _ in range(4):  # known_gap, safe_to_claim, not_safe_to_claim, recommendation
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def _play_lesson_to_completion(app, *, skip_mastery: bool = True) -> None:
    runner_scene = app.scenes.current

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # framing

    assert isinstance(app.scenes.current.inner, SourceBoardScene)
    _pick_a_source(app.scenes.current.inner)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)
    _play_inspection_workbench(app.scenes.current.inner)  # meet billing

    assert isinstance(app.scenes.current.inner, PipelineBuilderScene)
    _play_pipeline(app.scenes.current.inner)  # compute billing

    assert isinstance(app.scenes.current.inner, WorkbenchScene)
    _play_inspection_workbench(app.scenes.current.inner)  # meet app log

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner)  # comparison 1

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner)  # comparison 2

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner)  # gap discovery

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # finance lead confirms

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _fill_out(app.scenes.current.inner, 1)  # gut check

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner)  # support's list

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


def test_the_full_lesson_plays_through_all_seventeen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_two_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_completion(app)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwoResult)
        assert result.completed_thoughtfully() is True
        assert result.initial_inspect_pick == SOURCES[0].key
        assert result.mastery_engaged is False
        assert "analytical_context" in collected
    finally:
        pygame.quit()


def test_engaging_the_optional_mastery_challenge_is_reflected_in_the_result():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_two_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_completion(app, skip_mastery=False)

        assert finished_results[0].mastery_engaged is True
    finally:
        pygame.quit()


def test_picking_the_well_scoped_gap_interpretation_records_the_unresolved_status_evidence():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_two_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)
        _play_dialogue_to_the_end(app.scenes.current)
        _pick_a_source(app.scenes.current.inner)
        _play_inspection_workbench(app.scenes.current.inner)
        _play_pipeline(app.scenes.current.inner)
        _play_inspection_workbench(app.scenes.current.inner)
        _play_comparison_reveal(app.scenes.current.inner)
        _play_comparison_reveal(app.scenes.current.inner)

        gap_scene = app.scenes.current.inner
        assert isinstance(gap_scene, ComparisonRevealScene)
        well_scoped_index = next(
            i for i, option in enumerate(gap_scene.interpret_options) if option.key == "mixed_and_unresolved"
        )
        gap_scene.buttons.buttons[well_scoped_index].on_activate()
        gap_scene.continue_button.on_activate()

        assert any("legacy_status_unresolved" in item.label_key for item in gap_scene.context.evidence)
    finally:
        pygame.quit()


def test_the_evidence_step_only_enables_next_within_its_real_min_max_range():
    app = _init_app()
    try:
        runner, _ = build_lesson_two_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)
        _play_dialogue_to_the_end(app.scenes.current)
        _pick_a_source(app.scenes.current.inner)
        _play_inspection_workbench(app.scenes.current.inner)
        _play_pipeline(app.scenes.current.inner)
        _play_inspection_workbench(app.scenes.current.inner)
        _play_comparison_reveal(app.scenes.current.inner)
        _play_comparison_reveal(app.scenes.current.inner)
        _play_comparison_reveal(app.scenes.current.inner)
        _play_dialogue_to_the_end(app.scenes.current)
        _fill_out(app.scenes.current.inner, 1)
        _play_comparison_reveal(app.scenes.current.inner)
        app.scenes.current.inner.continue_button.on_activate()

        decision = app.scenes.current.inner
        assert isinstance(decision, DecisionBuilderScene)
        decision.buttons.buttons[0].on_activate()  # answer_strategy
        decision.next_button.on_activate()

        assert decision.next_button.enabled is False  # nothing picked yet

        evidence_ids = list(decision._evidence_toggle_buttons.keys())
        assert len(evidence_ids) >= 3  # at least the 3 critical facts
        decision._evidence_toggle_buttons[evidence_ids[0]].on_activate()

        assert decision.next_button.enabled is False  # 1 selected, min_count=2

        decision._evidence_toggle_buttons[evidence_ids[1]].on_activate()

        assert decision.next_button.enabled is True
    finally:
        pygame.quit()


@pytest.mark.parametrize(
    "field",
    [
        ANSWER_STRATEGY_FIELD,
        KNOWN_GAP_FIELD,
        SAFE_TO_CLAIM_FIELD,
        NOT_SAFE_TO_CLAIM_FIELD,
        RECOMMENDATION_FIELD,
        REVISION_FIELD,
    ],
)
def test_every_single_select_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


@pytest.mark.parametrize(
    "options",
    [
        COMPARISON_1_INTERPRET_OPTIONS,
        COMPARISON_2_INTERPRET_OPTIONS,
        GAP_INTERPRET_OPTIONS,
        SUPPORT_INTERPRET_OPTIONS,
        MASTERY_METRIC_OPTIONS,
        MASTERY_INTERPRET_OPTIONS,
    ],
)
def test_every_interpret_or_mastery_option_set_has_at_least_two_options(options):
    assert len(options) >= 2


def test_only_one_gap_interpretation_carries_the_unresolved_status_evidence_key():
    # The whole point of the correction: false-precision/noise/trust-
    # marketing decoys must never leave behind the "unresolved" evidence.
    carriers = [option for option in GAP_INTERPRET_OPTIONS if option.evidence_key is not None]
    assert len(carriers) == 1
    assert carriers[0].key == "mixed_and_unresolved"


def test_billing_compute_offers_at_least_two_group_by_options():
    for request in BILLING_REQUESTS:
        assert len(request.group_by_options) >= 2
        assert len(request.aggregate_options) >= 1


def test_every_source_has_the_same_four_real_fact_attributes():
    for source in SOURCES:
        assert len(source.attributes) == 4
