import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l09_outlier_patrol.definition import LESSON_09
from data_science_arcade.lessons.l09_outlier_patrol.scenario import (
    BULK_POPULATION_BASIS_FIELD,
    CONFIRMED_DATA_ERRORS_FIELD,
    DECISION_FIELDS,
    INCIDENT_TREATMENT_FIELD,
    MASTERY_MUST_NOT_REMOVE_FIELD,
    MASTERY_NEEDS_CORRECTION_FIELD,
    PREVENTION_ACTION_FIELD,
    SAFE_CLAIM_FIELD,
    SEGMENT_TREATMENT_FIELD,
    TOTAL_KPI_DEFENSIBILITY_FIELD,
    TYPICAL_KPI_DEFENSIBILITY_FIELD,
    build_lesson_nine_runner,
)
from data_science_arcade.lessons.l09_outlier_patrol.scoring import CRITICAL_EVIDENCE_KEYS, LessonNineResult, score_lesson_nine
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing

GOOD_ROUND1_RESOLUTION = {"fulfillment_cost": "no_blanket_action"}
GOOD_ROUND2_RESOLUTION = {
    "fulfillment_cost": "correct_via_invoice",
    "order_type": "keep_as_is",
    "incident_reference": "keep_and_flag_as_documented_incident",
}
GOOD_DIAGNOSIS = {
    "decimal_row_diagnosis": "data_entry_error",
    "bulk_row_diagnosis": "rare_but_legitimate",
    "anomaly_row_diagnosis": "documented_anomaly",
}
GOOD_DECISION = {
    "confirmed_data_errors": "decimal_row_only",
    "bulk_order_population_basis": "order_type_metadata",
    "incident_treatment": "keep_and_flag",
    "segment_treatment": "interpret_in_context_no_auto_remove",
    "typical_kpi_defensibility": "report_defensible",
    "total_kpi_defensibility": "report_defensible",
    "prevention_action": "entry_time_sanity_check",
    "safe_claim": "both_numbers_scoped_honestly",
}
DECISION_FIELDS_IN_ORDER = (
    CONFIRMED_DATA_ERRORS_FIELD,
    BULK_POPULATION_BASIS_FIELD,
    INCIDENT_TREATMENT_FIELD,
    SEGMENT_TREATMENT_FIELD,
    TYPICAL_KPI_DEFENSIBILITY_FIELD,
    TOTAL_KPI_DEFENSIBILITY_FIELD,
    PREVENTION_ACTION_FIELD,
    SAFE_CLAIM_FIELD,
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _leaf_scene(scene):
    while isinstance(scene, (SequenceScene, OfferThenTaskScene)):
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


def _answer_inspection(scene: WorkbenchScene, option_key: str) -> None:
    scene.inspection_buttons[option_key].on_activate()
    scene.continue_button.on_activate()


def _fill_single_select(scene: BriefBuilderScene, field, option_key: str) -> None:
    scene.buttons.buttons[_option_index(field, option_key)].on_activate()
    scene.next_button.on_activate()


def _fill_multi_select(scene, field, option_keys) -> None:
    for key in option_keys:
        scene.buttons.buttons[_option_index(field, key)].on_activate()
    scene.next_button.on_activate()


def _first_flagged_cell_button(scene: WorkbenchScene):
    chrome_labels = {scene.app.localization.t(key) for key in ("workbench.data.view_table", "workbench.data.view_schema", "workbench.continue")}
    tab_labels = {scene.app.localization.t(tab.value) for tab in type(scene.active_tab)}
    for button in scene.buttons.buttons:
        if button.label not in chrome_labels and button.label not in tab_labels:
            return button
    raise AssertionError("no flagged cell button found")


def _repair_issues(scene: WorkbenchScene, resolution: dict[str, str]) -> None:
    for _ in scene.issues:
        cell_button = _first_flagged_cell_button(scene)
        cell_button.on_activate()
        assert scene.active_issue is not None
        option_key = resolution[scene.active_issue.column]
        scene.picker_buttons[option_key].on_activate()


def _play_comparison_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_segment_slicer(scene: SegmentSlicerScene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.next_button.on_activate()


def _play_diagnosis_builder(scene: BriefBuilderScene, diagnosis: dict[str, str]) -> None:
    for step in scene.fields:
        _fill_single_select(scene, step, diagnosis[step.key])


def _select_critical_evidence_ids(scene: DecisionBuilderScene) -> list[str]:
    """Every ComparisonRevealScene reveal (detection, consequence, the
    pipeline check) auto-records its own values as evidence too - a
    real, non-critical majority alongside the 4 critical role facts.
    Playthrough tests need the 4 critical ones specifically, not
    whichever items happen to sit first in context.evidence."""
    critical_ids = [
        item.id
        for item in scene.context.evidence
        if item.id in scene._evidence_toggle_buttons and any(critical_key in item.label_key for critical_key in CRITICAL_EVIDENCE_KEYS)
    ]
    other_ids = [item_id for item_id in scene._evidence_toggle_buttons if item_id not in critical_ids]
    return (critical_ids + other_ids)[: scene.evidence_field.max_count]


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            evidence_ids = _select_critical_evidence_ids(scene)
            for item_id in evidence_ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        elif hasattr(step, "min_count"):  # MultiChoiceField
            for key in decision_keys[step.key]:
                index = _option_index(step, key)
                scene.buttons.buttons[index].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    inspection_option="needs_real_investigation",
    detection_interpretation="candidates_not_a_verdict",
    round1_resolution=GOOD_ROUND1_RESOLUTION,
    consequence_interpretation="worth_checking_what_left",
    revision_engage: bool = False,
    revised_round1_resolution=None,
    diagnosis=GOOD_DIAGNOSIS,
    round2_resolution=GOOD_ROUND2_RESOLUTION,
    pipeline_check_interpretation="looks_ready",
    round2_revision_engage: bool = False,
    revised_round2_resolution=None,
    decision=GOOD_DECISION,
    mastery_engage: bool = False,
    mastery_must_not_remove=("escalation_ticket",),
    mastery_needs_correction=("error_ticket",),
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # raw inspection
    _answer_inspection(app.scenes.current.inner, inspection_option)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # detection reveal
    _play_comparison_reveal(app.scenes.current.inner, detection_interpretation)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # repair round 1
    _repair_issues(app.scenes.current.inner, round1_resolution)
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # consequence reveal
    _play_comparison_reveal(app.scenes.current.inner, consequence_interpretation)

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)  # round 1 revision offer
    if revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, WorkbenchScene)
        assert revised_round1_resolution is not None
        _repair_issues(leaf, revised_round1_resolution)
        leaf.continue_button.on_activate()
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, SegmentSlicerScene)  # segment investigation
    _play_segment_slicer(app.scenes.current.inner)

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # diagnosis builder
    _play_diagnosis_builder(app.scenes.current.inner, diagnosis)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # case-by-case treatment
    _repair_issues(app.scenes.current.inner, round2_resolution)
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # pipeline check reveal
    _play_comparison_reveal(app.scenes.current.inner, pipeline_check_interpretation)

    round2_offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(round2_offer, OfferThenTaskScene)  # round 2 revision offer
    if round2_revision_engage:
        round2_offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(round2_offer)
        assert isinstance(leaf, WorkbenchScene)
        assert revised_round2_resolution is not None
        _repair_issues(leaf, revised_round2_resolution)
        leaf.continue_button.on_activate()
    else:
        round2_offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # evidence review
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final decision
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # optional mastery
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()  # Engage
        assert isinstance(mastery_offer._active, SequenceScene)
        mastery_offer._active.continue_button.on_activate()  # inspect the mastery export
        select_scene = mastery_offer._active._active
        _fill_multi_select(select_scene, MASTERY_MUST_NOT_REMOVE_FIELD, mastery_must_not_remove)
        _fill_multi_select(select_scene, MASTERY_NEEDS_CORRECTION_FIELD, mastery_needs_correction)
    else:
        mastery_offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_sixteen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_nine_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(app, mastery_engage=True)
        app.scenes.current.on_complete()  # feedback -> debrief

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonNineResult)
        assert result.completed_thoughtfully() is True
        assert result.round1_resolution == GOOD_ROUND1_RESOLUTION
        assert result.round2_resolution == GOOD_ROUND2_RESOLUTION
        assert set(result.decision) == {field.key for field in DECISION_FIELDS_IN_ORDER} | {"evidence"}
        assert result.mastery_engaged is True
        assert result.mastery_must_not_remove == frozenset({"escalation_ticket"})
        assert result.mastery_needs_correction == frozenset({"error_ticket"})
        assert collected is not None
    finally:
        pygame.quit()


def test_a_playthrough_that_skips_mastery_still_completes():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_nine_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, mastery_engage=False)
        app.scenes.current.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.mastery_engaged is False
        assert result.mastery_must_not_remove == frozenset()
    finally:
        pygame.quit()


def test_a_naive_blanket_drop_can_be_revised_via_the_revision_offer():
    # The central productive-failure chain: pick the naive blanket drop,
    # see its own real consequence, revise via the real, un-punished
    # offer, then correctly investigate every row case-by-case.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_nine_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            round1_resolution={"fulfillment_cost": "drop_outside_fence"},
            revision_engage=True,
            revised_round1_resolution=GOOD_ROUND1_RESOLUTION,
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.round1_revised is True
        assert result.initial_round1_resolution == {"fulfillment_cost": "drop_outside_fence"}
        assert result.round1_resolution == GOOD_ROUND1_RESOLUTION
        n, median = result.final_typical_state()
        assert (n, median) == (88, 47.0)

        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.METHOD] == 94.0
        assert any(o.text_key == "lesson.l09.feedback.round1_recovered_via_revision" for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_a_wrong_case_treatment_can_be_revised_via_the_round2_revision_offer():
    # The same productive-failure chain, one round later: mistreat every
    # flagged row in Round 2, see the real Pipeline Check result, revise
    # via the real, un-punished offer, then correctly treat every row.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_nine_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        bad_round2 = {"fulfillment_cost": "keep_as_is", "order_type": "drop_row", "incident_reference": "drop_row"}
        feedback = _play_lesson_to_feedback(
            app,
            round2_resolution=bad_round2,
            round2_revision_engage=True,
            revised_round2_resolution=GOOD_ROUND2_RESOLUTION,
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.round2_revised is True
        assert result.initial_round2_resolution == bad_round2
        assert result.round2_resolution == GOOD_ROUND2_RESOLUTION

        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.DATA_QUALITY] == 100.0
        assert any(o.text_key == "lesson.l09.feedback.round2_recovered_via_revision" for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_declining_the_revision_offer_keeps_the_naive_blanket_drop():
    app = _init_app()
    try:
        runner, _ = build_lesson_nine_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            round1_resolution={"fulfillment_cost": "drop_outside_fence"},
            revision_engage=False,
            decision=dict(
                GOOD_DECISION,
                typical_kpi_defensibility="report_provisional",
                total_kpi_defensibility="report_provisional",
            ),
        )
        assert isinstance(feedback, LessonFeedbackScene)
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", [*DECISION_FIELDS_IN_ORDER, MASTERY_MUST_NOT_REMOVE_FIELD, MASTERY_NEEDS_CORRECTION_FIELD])
def test_every_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_score_lesson_nine_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_nine_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        expected = score_lesson_nine(
            LessonNineResult(
                round1_resolution=GOOD_ROUND1_RESOLUTION,
                round2_resolution=GOOD_ROUND2_RESOLUTION,
                diagnosis=GOOD_DIAGNOSIS,
                decision=dict(GOOD_DECISION, evidence=()),
            ),
            LESSON_09,
            hints_used=0,
        )
        assert set(feedback.evaluation.dimension_scores) == set(expected.dimension_scores)
    finally:
        pygame.quit()
