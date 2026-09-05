import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l07_missing_data_clinic.definition import LESSON_07
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import (
    COLD_PACK_MEANING_FIELD,
    KPI_RESULT_FIELD,
    MASTERY_FIELD,
    MISSINGNESS_DIAGNOSIS_FIELD,
    PICK_MINUTES_MEANING_FIELD,
    PROMO_MEANING_FIELD,
    REQUIRED_ACTION_FIELD,
    SENSITIVITY_FIELD,
    STRUCTURAL_TREATMENT_FIELD,
    TARGET_SCOPE_FIELD,
    TREATMENT_FIELD,
    build_lesson_seven_runner,
)
from data_science_arcade.lessons.l07_missing_data_clinic.scoring import (
    LessonSevenResult,
    _mastery_succeeded,
    score_lesson_seven,
)
from data_science_arcade.lessons.l07_missing_data_clinic.twist_data import ROUND1_ISSUES, ROUND2_ISSUES
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing

GOOD_CONTRACT_ROUND1 = {"cold_pack_meaning": "structural_not_applicable", "promo_meaning": "explicit_category"}
GOOD_CONTRACT_ROUND2 = {"pick_minutes_meaning": "measurement_failure_legacy_peak"}
GOOD_RESOLUTION_ROUND1 = {"cold_pack_temp_c": "leave_as_missing", "promo_code": "recode_no_promo"}
GOOD_RESOLUTION_ROUND2 = {"pick_minutes": "preserve_and_report"}
GOOD_INVESTIGATION = {"primary_cut": "scanner_type", "secondary_cut": "hour_bucket"}
GOOD_DECISION = {
    "target_scope": "this_period_go_orders",
    "missingness_diagnosis": "legacy_peak_workflow",
    "treatment": "preserve_and_report",
    "kpi_result": "range_straddles",
    "sensitivity": "bounds_are_real_assumptions",
    "structural_treatment": "leave_as_missing",
    "required_action": "fix_capture_path",
}
DECISION_FIELDS_IN_ORDER = (
    TARGET_SCOPE_FIELD,
    MISSINGNESS_DIAGNOSIS_FIELD,
    TREATMENT_FIELD,
    KPI_RESULT_FIELD,
    SENSITIVITY_FIELD,
    STRUCTURAL_TREATMENT_FIELD,
    REQUIRED_ACTION_FIELD,
)


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


def _answer_inspection(scene: WorkbenchScene, option_key: str) -> None:
    scene.inspection_buttons[option_key].on_activate()
    scene.continue_button.on_activate()


def _fill_single_select(scene: BriefBuilderScene, field, option_key: str) -> None:
    scene.buttons.buttons[_option_index(field, option_key)].on_activate()
    scene.next_button.on_activate()


def _fill_multi_select(scene: BriefBuilderScene, field, option_keys) -> None:
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


def _play_segment_slicer(scene: SegmentSlicerScene, choices: dict[str, str]) -> None:
    for request in scene.requests:
        option_key = choices[request.key]
        index = _option_index(request, option_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


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
    inspection_option="missingness_needs_diagnosis",
    contract_round1=GOOD_CONTRACT_ROUND1,
    resolution_round1=GOOD_RESOLUTION_ROUND1,
    first_attempt_key="worth_checking",
    investigation=GOOD_INVESTIGATION,
    contract_round2=GOOD_CONTRACT_ROUND2,
    resolution_round2=GOOD_RESOLUTION_ROUND2,
    sensitivity_key="range_real_undecided",
    decision=GOOD_DECISION,
    mastery_engage: bool = False,
    mastery_selection=("supplier_lead_days",),
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # raw inspection
    _answer_inspection(app.scenes.current.inner, inspection_option)

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # contract builder round 1
    scene = app.scenes.current.inner
    _fill_single_select(scene, COLD_PACK_MEANING_FIELD, contract_round1["cold_pack_meaning"])
    _fill_single_select(app.scenes.current.inner, PROMO_MEANING_FIELD, contract_round1["promo_meaning"])

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # repair round 1
    _repair_issues(app.scenes.current.inner, resolution_round1)
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # first attempt
    _play_comparison_reveal(app.scenes.current.inner, first_attempt_key)

    assert isinstance(app.scenes.current.inner, SegmentSlicerScene)  # missingness investigation
    _play_segment_slicer(app.scenes.current.inner, investigation)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # root cause pivot
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # contract builder round 2
    _fill_single_select(app.scenes.current.inner, PICK_MINUTES_MEANING_FIELD, contract_round2["pick_minutes_meaning"])

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # repair round 2
    _repair_issues(app.scenes.current.inner, resolution_round2)
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # sensitivity reveal
    _play_comparison_reveal(app.scenes.current.inner, sensitivity_key)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # evidence review
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final decision
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # optional mastery
    offer = app.scenes.current.inner
    if mastery_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        assert isinstance(offer._active, SequenceScene)
        offer._active.continue_button.on_activate()  # inspect the mastery export
        select_scene = offer._active._active
        _fill_multi_select(select_scene, MASTERY_FIELD, mastery_selection)
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_fifteen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_seven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(app, mastery_engage=True)
        app.scenes.current.on_complete()  # feedback -> debrief

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonSevenResult)
        assert result.completed_thoughtfully() is True
        assert result.round1_resolution == GOOD_RESOLUTION_ROUND1
        assert result.round2_resolution == GOOD_RESOLUTION_ROUND2
        assert set(result.decision) == {field.key for field in DECISION_FIELDS_IN_ORDER} | {"evidence"}
        assert result.mastery_engaged is True
        assert result.mastery_selection == frozenset({"supplier_lead_days"})
        assert collected is not None
    finally:
        pygame.quit()


def test_a_playthrough_that_skips_mastery_still_completes():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, mastery_engage=False)
        app.scenes.current.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.mastery_engaged is False
        assert result.mastery_selection == frozenset()
    finally:
        pygame.quit()


def test_picking_the_decoy_investigation_options_still_completes_with_real_flat_evidence():
    app = _init_app()
    try:
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app, investigation={"primary_cut": "store", "secondary_cut": "basket_size"})
        assert isinstance(feedback, LessonFeedbackScene)
    finally:
        pygame.quit()


def test_analytical_context_survives_a_checkpoint_new_app_and_resume():
    app1 = _init_app()
    try:
        runner1, _ = build_lesson_seven_runner(app1, on_finished=lambda result: None)
        runner1.start()
        click_through_mission_briefing(app1)
        _play_dialogue_to_the_end(app1.scenes.current)  # briefing
        _answer_inspection(app1.scenes.current.inner, "missingness_needs_diagnosis")  # raw inspection
        scene = app1.scenes.current.inner
        _fill_single_select(scene, COLD_PACK_MEANING_FIELD, "structural_not_applicable")
        _fill_single_select(app1.scenes.current.inner, PROMO_MEANING_FIELD, "explicit_category")

        assert isinstance(app1.scenes.current.inner, WorkbenchScene)  # repair round 1
        _repair_issues(app1.scenes.current.inner, GOOD_RESOLUTION_ROUND1)
        app1.scenes.current.continue_button.on_activate()  # advances + checkpoints; quit right here
    finally:
        pygame.quit()

    app2 = _init_app()
    try:
        runner2, _ = build_lesson_seven_runner(app2, on_finished=lambda result: None)
        runner2.start()  # resumes straight into first_attempt

        assert isinstance(app2.scenes.current.inner, ComparisonRevealScene)
        resumed_context = app2.scenes.current.inner.context
        assert len(resumed_context.actions) == 2  # both round-1 issues' evidence already recorded
        assert len(resumed_context.evidence) == 2
    finally:
        pygame.quit()


@pytest.mark.parametrize(
    "field",
    [
        *DECISION_FIELDS_IN_ORDER,
        COLD_PACK_MEANING_FIELD,
        PROMO_MEANING_FIELD,
        PICK_MINUTES_MEANING_FIELD,
        MASTERY_FIELD,
    ],
)
def test_every_field_has_at_least_three_options(field):
    assert len(field.options) >= 3


# --- Scoring, exercised directly against hand-built results ---------------


def _result(**overrides) -> LessonSevenResult:
    base = dict(
        cold_pack_meaning="structural_not_applicable",
        promo_meaning="explicit_category",
        pick_minutes_meaning="measurement_failure_legacy_peak",
        round1_resolution=GOOD_RESOLUTION_ROUND1,
        round2_resolution=GOOD_RESOLUTION_ROUND2,
        sensitivity_interpretation="range_real_undecided",
        decision=dict(GOOD_DECISION, evidence=("e1", "e2")),
        critical_evidence_present=(
            "issue.pick_minutes.evidence",
            "evidence.scanner_type_gap",
            "evidence.hour_bucket_gap",
        ),
    )
    base.update(overrides)
    return LessonSevenResult(**base)


def test_data_quality_rewards_all_three_correct_declarations():
    good = score_lesson_seven(_result(), LESSON_07, hints_used=0)
    bad = score_lesson_seven(
        _result(cold_pack_meaning="measurement_failure", pick_minutes_meaning="random_noise"), LESSON_07, hints_used=0
    )
    assert good.dimension_scores[ScoreDimension.DATA_QUALITY] > bad.dimension_scores[ScoreDimension.DATA_QUALITY]
    assert good.dimension_scores[ScoreDimension.DATA_QUALITY] == 100.0


def test_data_quality_flags_pick_minutes_called_random_noise():
    result = score_lesson_seven(_result(pick_minutes_meaning="random_noise"), LESSON_07, hints_used=0)
    assert any(o.text_key == "lesson.l07.feedback.pick_minutes_called_random_noise" for o in result.observations)


def test_reproducibility_rewards_treatments_that_actually_match_meaning():
    good = score_lesson_seven(_result(), LESSON_07, hints_used=0)
    naive = score_lesson_seven(
        _result(round2_resolution={"pick_minutes": "fill_global_median"}), LESSON_07, hints_used=0
    )
    assert good.dimension_scores[ScoreDimension.REPRODUCIBILITY] > naive.dimension_scores[ScoreDimension.REPRODUCIBILITY]


def test_data_quality_and_reproducibility_are_independent_signals():
    # Correct concept (Contract Builder), wrong execution (repair picker) -
    # the two dimensions must actually diverge, not move together.
    result = score_lesson_seven(
        _result(round2_resolution={"pick_minutes": "fill_global_median"}), LESSON_07, hints_used=0
    )
    assert result.dimension_scores[ScoreDimension.DATA_QUALITY] == 100.0
    assert result.dimension_scores[ScoreDimension.REPRODUCIBILITY] < 100.0


def test_evidence_rewards_citing_the_critical_facts():
    good = score_lesson_seven(_result(), LESSON_07, hints_used=0)
    empty = score_lesson_seven(_result(critical_evidence_present=()), LESSON_07, hints_used=0)
    assert good.dimension_scores[ScoreDimension.EVIDENCE] > empty.dimension_scores[ScoreDimension.EVIDENCE]


def test_reasoning_catches_a_claimed_treatment_that_doesnt_match_execution():
    result = score_lesson_seven(
        _result(decision=dict(GOOD_DECISION, treatment="fill_global_median", evidence=("e1", "e2"))),
        LESSON_07,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l07.feedback.claimed_treatment_doesnt_match_execution" for o in result.observations)


def test_reasoning_catches_a_kpi_claim_that_contradicts_the_real_pipeline():
    # Claims a real range exists ("range_straddles") while having actually
    # filled every gap (round2 = fill_global_median => no real range left).
    result = score_lesson_seven(
        _result(
            round2_resolution={"pick_minutes": "fill_global_median"},
            decision=dict(GOOD_DECISION, treatment="fill_global_median", evidence=("e1", "e2")),
        ),
        LESSON_07,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l07.feedback.kpi_claim_contradicts_own_pipeline" for o in result.observations)


def test_reasoning_catches_a_diagnosis_that_denies_the_pattern():
    result = score_lesson_seven(
        _result(decision=dict(GOOD_DECISION, missingness_diagnosis="random_noise", evidence=("e1", "e2"))),
        LESSON_07,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l07.feedback.diagnosis_denies_the_pattern" for o in result.observations)


def test_uncertainty_rewards_correctly_reading_a_real_range_as_undecided():
    good = score_lesson_seven(_result(), LESSON_07, hints_used=0)
    overclaimed = score_lesson_seven(
        _result(sensitivity_interpretation="clearly_meets"), LESSON_07, hints_used=0
    )
    assert good.dimension_scores[ScoreDimension.UNCERTAINTY] > overclaimed.dimension_scores[ScoreDimension.UNCERTAINTY]
    assert any(
        o.text_key == "lesson.l07.feedback.overclaimed_certainty_on_a_real_range" for o in overclaimed.observations
    )


def test_uncertainty_rewards_correctly_reading_a_collapsed_range_as_erased():
    result = score_lesson_seven(
        _result(
            round2_resolution={"pick_minutes": "fill_global_median"},
            sensitivity_interpretation="range_collapsed_erased",
            decision=dict(GOOD_DECISION, treatment="fill_global_median", kpi_result="complete_case_ship_it", evidence=("e1", "e2")),
        ),
        LESSON_07,
        hints_used=0,
    )
    missed = score_lesson_seven(
        _result(
            round2_resolution={"pick_minutes": "fill_global_median"},
            sensitivity_interpretation="range_real_undecided",
            decision=dict(GOOD_DECISION, treatment="fill_global_median", kpi_result="complete_case_ship_it", evidence=("e1", "e2")),
        ),
        LESSON_07,
        hints_used=0,
    )
    assert result.dimension_scores[ScoreDimension.UNCERTAINTY] > missed.dimension_scores[ScoreDimension.UNCERTAINTY]
    assert any(o.text_key == "lesson.l07.feedback.missed_that_filling_erased_the_range" for o in missed.observations)


def test_uncertainty_flags_claiming_the_exact_truth_is_knowable():
    result = score_lesson_seven(
        _result(decision=dict(GOOD_DECISION, sensitivity="exact_truth_knowable", evidence=("e1", "e2"))),
        LESSON_07,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l07.feedback.claimed_the_exact_truth_is_knowable" for o in result.observations)


def test_method_rewards_the_correct_treatment_and_the_systemic_fix():
    good = score_lesson_seven(_result(), LESSON_07, hints_used=0)
    weak = score_lesson_seven(
        _result(decision=dict(GOOD_DECISION, required_action="nothing_needed", evidence=("e1", "e2"))),
        LESSON_07,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.METHOD] > weak.dimension_scores[ScoreDimension.METHOD]


def test_mastery_requires_the_exact_correct_set_not_a_superset_or_subset():
    assert _mastery_succeeded(_result(mastery_selection=frozenset({"supplier_lead_days"})))
    assert not _mastery_succeeded(_result(mastery_selection=frozenset({"supplier_lead_days", "unit_cost"})))
    assert not _mastery_succeeded(_result(mastery_selection=frozenset()))
