import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l05_sampling_mission.definition import LESSON_05
from data_science_arcade.lessons.l05_sampling_mission.scenario import (
    CLAIM_SCOPE_FIELD,
    DECISION_EVIDENCE_FIELD,
    ESTIMATE_TO_REPORT_FIELD,
    FRAME_FIELD,
    LIMITATION_FIELD,
    MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS,
    MECHANISM_INTERPRET_OPTIONS,
    NEXT_IMPROVEMENT_FIELD,
    PREDICTION_1_FIELD,
    PREDICTION_2_FIELD,
    SAMPLING_DESIGN_FIELD,
    STRATEGY_FIELD,
    TARGET_POPULATION_FIELD,
    VARIABILITY_INTERPRET_OPTIONS,
    _DesignThenAllocateScene,
    build_lesson_five_runner,
)
from data_science_arcade.lessons.l05_sampling_mission.scoring import LessonFiveResult, round_quality, score_lesson_five
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene
from data_science_arcade.ui.sampling_allocator_scene import SamplingAllocatorScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing

DECISION_FIELDS_IN_ORDER = (
    TARGET_POPULATION_FIELD,
    SAMPLING_DESIGN_FIELD,
    ESTIMATE_TO_REPORT_FIELD,
    DECISION_EVIDENCE_FIELD,
    LIMITATION_FIELD,
    CLAIM_SCOPE_FIELD,
    NEXT_IMPROVEMENT_FIELD,
)

GOOD_DECISION = {
    "target_population": "all_deliveries",
    "sampling_design": "stratified_export",
    "estimate_to_report": "best_design_scoped",
    "limitation": "rural_quickship_gap",
    "claim_scope": "carrierco_regions_scoped",
    "next_improvement": "sync_quickship_log",
}


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _option_index(field_or_options, option_key: str) -> int:
    options = field_or_options.options if hasattr(field_or_options, "options") else field_or_options
    return next(i for i, option in enumerate(options) if option.key == option_key)


def _spend_allocator_evenly(scene: SamplingAllocatorScene) -> None:
    """Round-robins the budget across whatever groups/caps are actually
    shown - respects each group's own real `available` ceiling rather than
    assuming a naive equal split always fits (it doesn't, for the smaller
    convenience frames)."""
    groups = scene.groups
    index = 0
    guard = 0
    while scene._remaining() > 0 and guard < 10_000:
        group = groups[index % len(groups)]
        if scene._headroom(group) >= scene.step:
            scene.plus_buttons[group.key].on_activate()
        index += 1
        guard += 1
    scene.confirm_button.on_activate()


def _play_design_round(app, choices: dict[str, str]) -> None:
    """choices: field.key -> option.key. `{"frame": ..., "strategy": ...}`
    for Round 1, `{"strategy": ...}` alone for Round 4. Drives the
    allocator sub-phase automatically (see _spend_allocator_evenly) if the
    resulting strategy is "stratified"."""
    scene = app.scenes.current.inner
    fields = (FRAME_FIELD, STRATEGY_FIELD) if "frame" in choices else (STRATEGY_FIELD,)
    for field in fields:
        scene.buttons.buttons[_option_index(field, choices[field.key])].on_activate()
        scene.next_button.on_activate()
    active = app.scenes.current.inner
    if hasattr(active, "plus_buttons"):
        _spend_allocator_evenly(active)


def _play_prediction(app, field, option_key: str) -> None:
    scene = app.scenes.current.inner
    scene.buttons.buttons[_option_index(field, option_key)].on_activate()
    scene.next_button.on_activate()


def _play_comparison_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict[str, str]) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            evidence_ids = list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.max_count]
            for item_id in evidence_ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    round1: dict[str, str],
    prediction1_key: str,
    reveal1_key: str,
    reveal2_key: str,
    reveal3_key: str,
    round4: dict[str, str],
    prediction2_key: str,
    reveal4_key: str,
    decision: dict[str, str],
    skip_mastery: bool = True,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # framing

    assert isinstance(app.scenes.current.inner, _DesignThenAllocateScene)
    _play_design_round(app, round1)  # round1_design

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _play_prediction(app, PREDICTION_1_FIELD, prediction1_key)  # prediction1

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner, reveal1_key)  # reveal1

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # root_cause

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner, reveal2_key)  # reveal2

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner, reveal3_key)  # reveal3

    assert isinstance(app.scenes.current.inner, _DesignThenAllocateScene)
    _play_design_round(app, round4)  # round4_design

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _play_prediction(app, PREDICTION_2_FIELD, prediction2_key)  # prediction2

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner, reveal4_key)  # reveal4

    assert isinstance(app.scenes.current.inner, WorkbenchScene)
    app.scenes.current.inner.continue_button.on_activate()  # evidence_review

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision)  # final_decision

    assert isinstance(app.scenes.current.inner, MasteryChallengeScene)
    mastery = app.scenes.current.inner
    if skip_mastery:
        mastery.buttons.buttons[1].on_activate()  # Skip
    else:
        mastery.buttons.buttons[0].on_activate()  # Engage
        mastery.buttons.buttons[0].on_activate()  # first metric
        interpret_index = _option_index(MASTERY_INTERPRET_OPTIONS, "needs_own_stratification")
        mastery.buttons.buttons[interpret_index].on_activate()
        mastery.finish_button.on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def _finish_from_feedback(app) -> None:
    app.scenes.current.inner.buttons.buttons[0].on_activate()
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes


GOOD_ROUND1 = {"frame": "tracking_export", "strategy": "stratified"}
GOOD_ROUND4 = {"strategy": "stratified"}


def test_the_full_lesson_plays_through_all_sixteen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_five_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(
            app,
            round1=GOOD_ROUND1,
            prediction1_key="frame_coverage_gap",
            reveal1_key="frame_coverage_gap",
            reveal2_key="frame_coverage_gap",
            reveal3_key="consistent_with_chance",
            round4=GOOD_ROUND4,
            prediction2_key="frame_ceiling_remains",
            reveal4_key="frame_coverage_gap",
            decision=GOOD_DECISION,
        )
        _finish_from_feedback(app)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonFiveResult)
        assert result.completed_thoughtfully() is True
        assert result.round1_frame == "tracking_export"
        assert result.round1_strategy == "stratified"
        assert result.round4_strategy == "stratified"
        assert result.round1_quality == 1.0
        assert result.round4_quality == 1.0
        assert len(result.critical_evidence_present) >= 1
        assert "analytical_context" in collected
    finally:
        pygame.quit()


def test_a_convenience_on_a_self_selected_frame_playthrough_still_completes():
    """Productive failure: the tempting, free, badly-biased path - still a
    real, playable, completable path, never a dead end."""
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_five_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(
            app,
            round1={"frame": "support_tickets", "strategy": "convenience"},
            prediction1_key="self_selection",
            reveal1_key="self_selection",
            reveal2_key="frame_coverage_gap",
            reveal3_key="consistent_with_chance",
            round4={"strategy": "convenience"},
            prediction2_key="frame_ceiling_remains",
            reveal4_key="draw_order_bias",
            decision=GOOD_DECISION,
        )
        _finish_from_feedback(app)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert result.completed_thoughtfully() is True
        assert result.round1_quality == 0.0  # self-selected frame, convenience - the worst combination
        assert result.round4_quality == 0.7  # tracking_export+convenience - right frame, wrong method
    finally:
        pygame.quit()


def test_analytical_context_survives_a_checkpoint_new_app_and_resume():
    app1 = _init_app()
    try:
        runner1, _ = build_lesson_five_runner(app1, on_finished=lambda result: None)
        runner1.start()
        click_through_mission_briefing(app1)
        _play_dialogue_to_the_end(app1.scenes.current)  # briefing
        _play_dialogue_to_the_end(app1.scenes.current)  # framing
        _play_design_round(app1, GOOD_ROUND1)  # round1_design (+ allocator)
        _play_prediction(app1, PREDICTION_1_FIELD, "frame_coverage_gap")  # prediction1

        reveal = app1.scenes.current.inner
        assert isinstance(reveal, ComparisonRevealScene)
        _play_comparison_reveal(reveal, "frame_coverage_gap")  # advances + checkpoints; quit right here
    finally:
        pygame.quit()

    app2 = _init_app()  # a brand new App(), same on-disk save - simulates relaunching
    try:
        runner2, _ = build_lesson_five_runner(app2, on_finished=lambda result: None)
        runner2.start()  # resumes straight into root_cause, skipping everything before it

        root_cause = app2.scenes.current.inner
        assert isinstance(root_cause, DialogueScene)
        resumed_context = root_cause.context
        assert len(resumed_context.actions) >= 1
        assert len(resumed_context.evidence) >= 2  # reveal1's own 2 real values
    finally:
        pygame.quit()


def test_a_stratified_pick_shows_the_allocator_with_real_per_region_caps():
    app = _init_app()
    try:
        runner, _ = build_lesson_five_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing

        scene = app.scenes.current.inner
        scene.buttons.buttons[_option_index(FRAME_FIELD, "tracking_export")].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[_option_index(STRATEGY_FIELD, "stratified")].on_activate()
        scene.next_button.on_activate()

        allocator = app.scenes.current.inner
        assert isinstance(allocator, _DesignThenAllocateScene)
        assert isinstance(allocator._active, SamplingAllocatorScene)
        caps = {group.key: group.available for group in allocator.groups}
        assert caps == {"metro": 400, "suburban": 300, "coastal": 180, "rural": 15}
    finally:
        pygame.quit()


def test_a_convenience_pick_never_shows_an_allocator():
    app = _init_app()
    try:
        runner, _ = build_lesson_five_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing

        _play_design_round(app, {"frame": "tracking_export", "strategy": "convenience"})

        # Straight through to prediction1 - never an allocator in between.
        assert isinstance(app.scenes.current.inner, BriefBuilderScene)
        assert app.scenes.current.inner.fields == (PREDICTION_1_FIELD,)
    finally:
        pygame.quit()


@pytest.mark.parametrize(
    "field",
    [
        FRAME_FIELD,
        STRATEGY_FIELD,
        PREDICTION_1_FIELD,
        PREDICTION_2_FIELD,
        TARGET_POPULATION_FIELD,
        SAMPLING_DESIGN_FIELD,
        ESTIMATE_TO_REPORT_FIELD,
        LIMITATION_FIELD,
        CLAIM_SCOPE_FIELD,
        NEXT_IMPROVEMENT_FIELD,
    ],
)
def test_every_single_select_field_has_at_least_three_options(field):
    assert len(field.options) >= 3


def test_mechanism_interpret_options_cover_all_real_mechanisms_plus_a_decoy():
    keys = {option.key for option in MECHANISM_INTERPRET_OPTIONS}
    assert keys == {"self_selection", "frame_coverage_gap", "draw_order_bias", "looks_solid"}


def test_variability_interpret_options_are_four_real_choices():
    keys = {option.key for option in VARIABILITY_INTERPRET_OPTIONS}
    assert keys == {"consistent_with_chance", "one_must_be_wrong", "design_must_be_flawed", "bigger_sample_would_match"}


def test_mastery_metric_and_interpret_options_are_both_real_choices():
    assert len(MASTERY_METRIC_OPTIONS) == 2
    assert len(MASTERY_INTERPRET_OPTIONS) == 4


# --- Scoring, exercised directly against hand-built results ---------------


def _result(**overrides) -> LessonFiveResult:
    base = dict(
        round1_frame="tracking_export",
        round1_strategy="stratified",
        round4_strategy="stratified",
        prediction1="frame_coverage_gap",
        prediction2="frame_ceiling_remains",
        decision=dict(GOOD_DECISION, evidence=("e1", "e2")),
        round1_quality=round_quality("tracking_export", "stratified"),
        round4_quality=round_quality("tracking_export", "stratified"),
        critical_evidence_present=("reveal1.rural_share_label", "reveal3.draw_a_label", "reveal3.draw_b_label"),
    )
    base.update(overrides)
    return LessonFiveResult(**base)


def test_data_quality_rewards_tracking_export_stratified_over_self_selected_frames():
    good = score_lesson_five(_result(), LESSON_05, hints_used=0)
    bad = score_lesson_five(
        _result(round1_frame="support_tickets", round1_strategy="convenience", round1_quality=0.0, round4_quality=0.0),
        LESSON_05,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.DATA_QUALITY] > bad.dimension_scores[ScoreDimension.DATA_QUALITY]
    assert bad.dimension_scores[ScoreDimension.DATA_QUALITY] < 30.0


def test_method_rewards_the_stratified_recommendation_and_scoped_estimate():
    good = score_lesson_five(_result(), LESSON_05, hints_used=0)
    size_trap = score_lesson_five(
        _result(decision=dict(GOOD_DECISION, sampling_design="keep_tickets_bigger", estimate_to_report="tickets_biggest", evidence=("e1",))),
        LESSON_05,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.METHOD] > size_trap.dimension_scores[ScoreDimension.METHOD]


def test_evidence_rewards_citing_the_critical_facts():
    good = score_lesson_five(_result(), LESSON_05, hints_used=0)
    empty = score_lesson_five(_result(critical_evidence_present=()), LESSON_05, hints_used=0)
    assert good.dimension_scores[ScoreDimension.EVIDENCE] > empty.dimension_scores[ScoreDimension.EVIDENCE]


def test_uncertainty_rewards_correct_predictions_and_penalizes_overreach():
    good = score_lesson_five(_result(), LESSON_05, hints_used=0)
    overreach = score_lesson_five(
        _result(
            prediction1="looks_solid",
            prediction2="fully_fixed",
            decision=dict(GOOD_DECISION, claim_scope="whole_company_one_rate", evidence=("e1", "e2")),
        ),
        LESSON_05,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.UNCERTAINTY] > overreach.dimension_scores[ScoreDimension.UNCERTAINTY]
    assert overreach.dimension_scores[ScoreDimension.UNCERTAINTY] < 50.0


def test_reasoning_catches_a_design_estimate_mismatch():
    good = score_lesson_five(_result(), LESSON_05, hints_used=0)
    mismatch = score_lesson_five(
        _result(decision=dict(GOOD_DECISION, sampling_design="stratified_export", estimate_to_report="tickets_biggest", evidence=("e1", "e2"))),
        LESSON_05,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.REASONING] > mismatch.dimension_scores[ScoreDimension.REASONING]


def test_reasoning_catches_a_scope_improvement_mismatch():
    good = score_lesson_five(_result(), LESSON_05, hints_used=0)
    mismatch = score_lesson_five(
        _result(decision=dict(GOOD_DECISION, claim_scope="carrierco_regions_scoped", next_improvement="nothing_needed", evidence=("e1", "e2"))),
        LESSON_05,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.REASONING] > mismatch.dimension_scores[ScoreDimension.REASONING]
