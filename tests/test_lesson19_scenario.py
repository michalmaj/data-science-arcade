import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pandas as pd
import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l19_power_plant import data as d
from data_science_arcade.lessons.l19_power_plant.scenario import DECISION_FIELDS, build_lesson_nineteen_runner
from data_science_arcade.lessons.l19_power_plant.scoring import (
    FINAL_PLAN_SENSITIVITY_EVIDENCE_KEY,
    PRECISE_TINY_EFFECT_EVIDENCE_KEY,
    REFERENCE_INADEQUATE_DESIGN_EVIDENCE_KEY,
    UNDERPOWERED_CALIBRATION_EVIDENCE_KEY,
    LessonNineteenResult,
)
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.power_planner_scene import PowerPlannerScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

GOOD_MASTERY_DESIGN_JUDGMENT = "inadequate_for_the_2pp_target"
GOOD_MASTERY_RESULT_INTERPRETATION = "inconclusive_neither_zero_nor_worthwhile_ruled_out"
GOOD_MASTERY_EVIDENCE = ("design_inadequate_for_2pp_target", "wide_ci_crosses_zero_and_target")


def _good_decision(final_weeks: int) -> dict:
    classification = "meets_sensitivity_target" if d.meets_sensitivity_target(final_weeks) else "does_not_meet_sensitivity_target"
    return {
        "final_design_meets_sensitivity_target": classification,
        "what_more_sample_size_changes": "narrows_uncertainty_improves_sensitivity_not_effect_size",
        "what_mde_represents": "design_stage_probability_not_post_hoc_cutoff",
        "business_vs_statistical_detectability": "answer_different_questions_not_interchangeable",
        "underpowered_result_interpretation": "inconclusive_neither_zero_nor_worthwhile_ruled_out",
        "precise_small_effect_interpretation": "precisely_estimated_small_effect_below_threshold",
    }


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _leaf_scene(scene):
    while isinstance(scene, OfferThenTaskScene):
        active = getattr(scene, "_active", None)
        if active is None:
            break
        scene = active
    return scene


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _option_index(field_or_options, option_key: str) -> int:
    options = field_or_options.options if hasattr(field_or_options, "options") else field_or_options
    return next(i for i, option in enumerate(options) if option.key == option_key)


def _play_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict, evidence_ids: list[str] | None = None) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            ids = evidence_ids if evidence_ids is not None else list(scene._evidence_toggle_buttons.keys())
            for item_id in ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_mastery_select(scene: BriefBuilderScene, design_judgment_key: str, result_interpretation_key: str, evidence_keys: tuple[str, ...]) -> None:
    judgment_field = scene.fields[0]
    scene.buttons.buttons[_option_index(judgment_field, design_judgment_key)].on_activate()
    scene.next_button.on_activate()
    interpretation_field = scene.fields[1]
    scene.buttons.buttons[_option_index(interpretation_field, result_interpretation_key)].on_activate()
    scene.next_button.on_activate()
    evidence_field = scene.fields[2]
    for key in evidence_keys:
        scene.buttons.buttons[_option_index(evidence_field, key)].on_activate()
    scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    cold_weeks: int = 7,
    final_weeks: int | None = None,
    primary_interpretation: str = "detection_probability_across_repeated_samples",
    underpowered_interpretation: str = "inconclusive_substantial_uncertainty_remains",
    high_n_interpretation: str = "statistically_distinguishable_but_below_threshold",
    decision: dict | None = None,
    evidence_ids: list[str] | None = None,
    mastery_engage: bool = False,
    mastery_design_judgment: str = GOOD_MASTERY_DESIGN_JUDGMENT,
    mastery_result_interpretation: str = GOOD_MASTERY_RESULT_INTERPRETATION,
    mastery_evidence: tuple[str, ...] = GOOD_MASTERY_EVIDENCE,
) -> LessonFeedbackScene:
    if final_weeks is None:
        final_weeks = cold_weeks

    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
    _play_dialogue_to_the_end(app.scenes.current)

    pick_scene = app.scenes.current.inner  # cold_duration_pick
    assert isinstance(pick_scene, BriefBuilderScene)
    field = pick_scene.fields[0]
    pick_scene.buttons.buttons[_option_index(field, str(cold_weeks))].on_activate()
    pick_scene.next_button.on_activate()

    planner = app.scenes.current.inner  # power_planning
    assert isinstance(planner, PowerPlannerScene)
    assert planner.weeks == cold_weeks
    delta = final_weeks - cold_weeks
    for _ in range(abs(delta)):
        planner.buttons.buttons[1 if delta > 0 else 0].on_activate()
    assert planner.weeks == final_weeks
    planner.confirm_button.on_activate()

    power_reveal = app.scenes.current.inner  # power_as_probability_reveal
    assert isinstance(power_reveal, ComparisonRevealScene)
    _play_reveal(power_reveal, primary_interpretation)

    underpowered_reveal = app.scenes.current.inner
    assert isinstance(underpowered_reveal, ComparisonRevealScene)
    _play_reveal(underpowered_reveal, underpowered_interpretation)

    high_n_reveal = app.scenes.current.inner
    assert isinstance(high_n_reveal, ComparisonRevealScene)
    _play_reveal(high_n_reveal, high_n_interpretation)

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_power_brief
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision or _good_decision(final_weeks), evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()
        select_scene = _leaf_scene(mastery_offer)
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_design_judgment, mastery_result_interpretation, mastery_evidence)
    else:
        mastery_offer.buttons.buttons[1].on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_with_a_correct_7week_plan():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_nineteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, cold_weeks=7, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonNineteenResult)
        assert result.completed_thoughtfully() is True
        assert result.cold_duration_pick == 7
        assert result.final_weeks == 7
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert result.mastery_engaged is True
        assert result.mastery_result == {
            "mastery_design_judgment": GOOD_MASTERY_DESIGN_JUDGMENT,
            "mastery_result_interpretation": GOOD_MASTERY_RESULT_INTERPRETATION,
            "mastery_supporting_evidence": GOOD_MASTERY_EVIDENCE,
        }
        assert collected is not None
    finally:
        pygame.quit()


def test_cold_pick_can_be_really_revised_via_the_planner_stepper():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_nineteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, cold_weeks=4, final_weeks=7)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.cold_duration_pick == 4
        assert result.final_weeks == 7
    finally:
        pygame.quit()


def test_keeping_the_cold_pick_without_touching_the_stepper():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_nineteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, cold_weeks=4, final_weeks=4, decision=_good_decision(4))
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.cold_duration_pick == 4
        assert result.final_weeks == 4
    finally:
        pygame.quit()


def test_evidence_is_available_after_a_wrong_interpretation_at_every_reveal():
    app = _init_app()
    try:
        runner, collected = build_lesson_nineteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(
            app,
            primary_interpretation="four_week_caught_it_sometimes_so_its_fine",
            underpowered_interpretation="not_significant_so_no_real_effect",
            high_n_interpretation="narrow_interval_means_effect_is_zero",
        )

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        evidence_label_keys = {item.label_key for item in restored_context.evidence}
        assert FINAL_PLAN_SENSITIVITY_EVIDENCE_KEY in evidence_label_keys
        assert REFERENCE_INADEQUATE_DESIGN_EVIDENCE_KEY in evidence_label_keys
        assert UNDERPOWERED_CALIBRATION_EVIDENCE_KEY in evidence_label_keys
        assert PRECISE_TINY_EFFECT_EVIDENCE_KEY in evidence_label_keys
    finally:
        pygame.quit()


@pytest.mark.parametrize("final_weeks", [2, 4, 6, 8, 12])
def test_python_mirror_reflects_the_real_final_weeks_never_a_canonical_seven(final_weeks):
    app = _init_app()
    try:
        runner, collected = build_lesson_nineteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        # cold_weeks stays one of the real blind-pick options {2,4,7,12};
        # the stepper (a real revision) reaches any final_weeks 1-12.
        _play_lesson_to_feedback(app, cold_weeks=7, final_weeks=final_weeks, decision=_good_decision(final_weeks))

        restored = LessonContext()
        restored.restore_from_dict(collected["analytical_context"])
        plan_action = next(a for a in restored.actions if a.key == "power_plan")
        assert f"weeks = {final_weeks}" in plan_action.python_code
        assert "weeks = 7" not in plan_action.python_code or final_weeks == 7

        from data_science_arcade.lessons.framework.power import minimum_detectable_effect

        namespace: dict = {"pd": pd, "minimum_detectable_effect": minimum_detectable_effect}
        exec(plan_action.python_code, namespace)
        assert namespace["weeks"] == final_weeks
        assert namespace["mde"] == pytest.approx(d.mde_for_weeks(final_weeks))
    finally:
        pygame.quit()


def test_the_happy_path_python_mirror_executes_top_to_bottom():
    import numpy as np

    from data_science_arcade.lessons.framework.power import Z_ALPHA_2, minimum_detectable_effect, proportion_difference_ci, two_proportion_z_statistic

    app = _init_app()
    try:
        runner, collected = build_lesson_nineteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, cold_weeks=7)

        restored = LessonContext()
        restored.restore_from_dict(collected["analytical_context"])
        mirror = restored.python_mirror()

        assert "weeks = 7" in mirror
        assert "empirical_detection_rate_a" in mirror or "reference_design_a_detections" in mirror

        namespace: dict = {
            "pd": pd,
            "np": np,
            "minimum_detectable_effect": minimum_detectable_effect,
            "proportion_difference_ci": proportion_difference_ci,
            "two_proportion_z_statistic": two_proportion_z_statistic,
            "Z_ALPHA_2": Z_ALPHA_2,
            # The two calibration datasets are legitimate external
            # dependencies (real, given facts) - pre-seeded directly,
            # matching L17/L18's own "base dataset is never re-derived
            # mid-mirror" discipline, never a literal pd.read_csv call.
            "underpowered_calibration": d.generate_underpowered_calibration().frame,
            "high_n_calibration": d.generate_high_n_calibration().frame,
        }
        exec(mirror, namespace)

        assert namespace["weeks"] == 7
        assert round(namespace["mde"] * 100, 2) == 1.43
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", DECISION_FIELDS)
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_score_lesson_nineteen_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_nineteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        assert feedback.evaluation is not None
    finally:
        pygame.quit()
