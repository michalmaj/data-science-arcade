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


def _leaf_scene(scene):
    """Unwraps nested SequenceScene/OfferThenTaskScene composites down to
    the real leaf scene currently on screen. Interaction itself doesn't
    need this - attribute access already proxies through __getattr__ on
    every wrapper - but isinstance checks do, since a wrapper's own type
    never changes as its nested `_active` scene is swapped out."""
    while isinstance(scene, (SequenceScene, OfferThenTaskScene)):
        active = getattr(scene, "_active", None)
        if active is None:
            break
        scene = active
    return scene


def _play_repair_round1(
    app,
    resolution_round1: dict[str, str],
    *,
    population_choice: str | None = None,
    revised_resolution: dict[str, str] | None = None,
) -> None:
    """Drives the repair_round1 composite. A destructive resolution (one
    that shrinks the 400-row population) shows a real population-
    consequence reveal, with a real, un-punished chance to revise before
    the central SLA investigation ever runs against a narrowed
    population - population_choice/revised_resolution only matter on
    that branch. Checked against real stage identity, not scene type
    alone - the very next real stage (first_attempt) is itself a
    ComparisonRevealScene too, and would otherwise be indistinguishable
    from the in-stage consequence reveal by type."""
    stage_scene = app.scenes.current.inner
    assert isinstance(_leaf_scene(stage_scene), WorkbenchScene)
    _repair_issues(stage_scene, resolution_round1)
    app.scenes.current.continue_button.on_activate()

    if app.scenes.current.inner is stage_scene:
        assert population_choice is not None
        assert isinstance(_leaf_scene(stage_scene), ComparisonRevealScene)
        _play_comparison_reveal(stage_scene, population_choice)
        if population_choice == "revise_the_treatment":
            assert isinstance(_leaf_scene(stage_scene), WorkbenchScene)
            assert revised_resolution is not None
            _repair_issues(stage_scene, revised_resolution)
            app.scenes.current.continue_button.on_activate()


def _play_missingness_investigation(app, investigation: dict[str, str]) -> None:
    """Drives the missingness_investigation composite. Whichever real
    signal(s) the first pass didn't land on get forced open here - each
    follow-up request offers only that one real cut (no decoy
    alternative to sidestep it again), so there's never a real "choice"
    left to make; just click through whatever's offered."""
    assert isinstance(_leaf_scene(app.scenes.current.inner), SegmentSlicerScene)
    _play_segment_slicer(app.scenes.current.inner, investigation)

    leaf = _leaf_scene(app.scenes.current.inner)
    if isinstance(leaf, SegmentSlicerScene):
        followup_choices = {request.key: request.options[0].key for request in leaf.requests}
        _play_segment_slicer(app.scenes.current.inner, followup_choices)


def _play_sensitivity_reveal(
    app,
    sensitivity_key: str,
    *,
    revise: bool = False,
    revised_resolution: dict[str, str] | None = None,
    revised_sensitivity_key: str | None = None,
) -> None:
    """Drives the sensitivity_reveal composite: the reveal shows first,
    then a real, un-punished offer to revise pick_minutes' own treatment
    and see the range genuinely recompute.

    OfferThenTaskScene keeps its own real `.buttons` (Engage/Skip)
    attribute alive even once engaged - real gameplay never notices
    since its `handle_event` explicitly routes to the active task scene
    first, but generic attribute proxying (`__getattr__`) finds that
    still-live `.buttons` before ever falling through to the nested task
    scene's own. So once engaged, every further interaction here targets
    the unwrapped leaf scene directly rather than the composite/offer
    wrapper, sidestepping that shadowing."""
    assert isinstance(_leaf_scene(app.scenes.current.inner), ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner, sensitivity_key)

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)
    if revise:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, WorkbenchScene)
        assert revised_resolution is not None
        _repair_issues(leaf, revised_resolution)
        leaf.continue_button.on_activate()

        leaf = _leaf_scene(offer)
        assert isinstance(leaf, ComparisonRevealScene)
        assert revised_sensitivity_key is not None
        _play_comparison_reveal(leaf, revised_sensitivity_key)
    else:
        offer.buttons.buttons[1].on_activate()  # Skip


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
    round1_population_choice=None,
    round1_revised_resolution=None,
    first_attempt_key="worth_checking",
    investigation=GOOD_INVESTIGATION,
    contract_round2=GOOD_CONTRACT_ROUND2,
    resolution_round2=GOOD_RESOLUTION_ROUND2,
    sensitivity_key="range_real_undecided",
    sensitivity_revise: bool = False,
    sensitivity_revised_resolution=None,
    sensitivity_revised_key=None,
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

    _play_repair_round1(
        app,
        resolution_round1,
        population_choice=round1_population_choice,
        revised_resolution=round1_revised_resolution,
    )

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # first attempt
    _play_comparison_reveal(app.scenes.current.inner, first_attempt_key)

    _play_missingness_investigation(app, investigation)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # root cause pivot
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # contract builder round 2
    _fill_single_select(app.scenes.current.inner, PICK_MINUTES_MEANING_FIELD, contract_round2["pick_minutes_meaning"])

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # repair round 2
    _repair_issues(app.scenes.current.inner, resolution_round2)
    app.scenes.current.continue_button.on_activate()

    _play_sensitivity_reveal(
        app,
        sensitivity_key,
        revise=sensitivity_revise,
        revised_resolution=sensitivity_revised_resolution,
        revised_sensitivity_key=sensitivity_revised_key,
    )

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


def test_picking_both_decoy_investigation_options_forces_both_real_signals_via_followup():
    # Both decoys (store, basket_size) show a real, flat table each time -
    # a real finding, not a wasted click - but neither is the pattern the
    # combined diagnosis is about to require, so the follow-up here must
    # force BOTH real signals open before the lesson moves on.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app, investigation={"primary_cut": "store", "secondary_cut": "basket_size"})
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief

        result = finished_results[0]
        assert result.decision.get("missingness_diagnosis") == "legacy_peak_workflow"
    finally:
        pygame.quit()


def test_picking_one_real_signal_and_one_decoy_forces_only_the_missing_real_signal():
    # The exact bug this corrective pass closes: seeing scanner_type
    # alone used to be enough to skip any follow-up at all, so the
    # combined legacy-scanner/peak-hour diagnosis could be required and
    # scored on the strength of a pattern only half-checked. Now the
    # still-missing signal (hour_bucket) gets forced open before the
    # lesson can require or score the combined answer.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app, investigation={"primary_cut": "scanner_type", "secondary_cut": "basket_size"}
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief

        result = finished_results[0]
        assert result.decision.get("missingness_diagnosis") == "legacy_peak_workflow"
    finally:
        pygame.quit()


def _play_investigation_first_pass(app, investigation: dict[str, str]) -> None:
    assert isinstance(_leaf_scene(app.scenes.current.inner), SegmentSlicerScene)
    _play_segment_slicer(app.scenes.current.inner, investigation)


def test_followup_forces_only_the_one_missing_real_signal():
    app = _init_app()
    try:
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _answer_inspection(app.scenes.current.inner, "missingness_needs_diagnosis")
        _fill_single_select(app.scenes.current.inner, COLD_PACK_MEANING_FIELD, GOOD_CONTRACT_ROUND1["cold_pack_meaning"])
        _fill_single_select(app.scenes.current.inner, PROMO_MEANING_FIELD, GOOD_CONTRACT_ROUND1["promo_meaning"])
        _play_repair_round1(app, GOOD_RESOLUTION_ROUND1)
        _play_comparison_reveal(app.scenes.current.inner, "worth_checking")

        _play_investigation_first_pass(app, {"primary_cut": "scanner_type", "secondary_cut": "basket_size"})

        leaf = _leaf_scene(app.scenes.current.inner)
        assert isinstance(leaf, SegmentSlicerScene)
        assert [request.key for request in leaf.requests] == ["followup_hour_bucket"]
    finally:
        pygame.quit()


def test_followup_forces_both_real_signals_when_neither_was_seen():
    app = _init_app()
    try:
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _answer_inspection(app.scenes.current.inner, "missingness_needs_diagnosis")
        _fill_single_select(app.scenes.current.inner, COLD_PACK_MEANING_FIELD, GOOD_CONTRACT_ROUND1["cold_pack_meaning"])
        _fill_single_select(app.scenes.current.inner, PROMO_MEANING_FIELD, GOOD_CONTRACT_ROUND1["promo_meaning"])
        _play_repair_round1(app, GOOD_RESOLUTION_ROUND1)
        _play_comparison_reveal(app.scenes.current.inner, "worth_checking")

        _play_investigation_first_pass(app, {"primary_cut": "store", "secondary_cut": "basket_size"})

        leaf = _leaf_scene(app.scenes.current.inner)
        assert isinstance(leaf, SegmentSlicerScene)
        assert [request.key for request in leaf.requests] == ["followup_scanner_type", "followup_hour_bucket"]
    finally:
        pygame.quit()


def test_no_followup_when_both_real_signals_already_seen():
    app = _init_app()
    try:
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _answer_inspection(app.scenes.current.inner, "missingness_needs_diagnosis")
        _fill_single_select(app.scenes.current.inner, COLD_PACK_MEANING_FIELD, GOOD_CONTRACT_ROUND1["cold_pack_meaning"])
        _fill_single_select(app.scenes.current.inner, PROMO_MEANING_FIELD, GOOD_CONTRACT_ROUND1["promo_meaning"])
        _play_repair_round1(app, GOOD_RESOLUTION_ROUND1)
        _play_comparison_reveal(app.scenes.current.inner, "worth_checking")

        _play_investigation_first_pass(app, GOOD_INVESTIGATION)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # root cause pivot, no followup
    finally:
        pygame.quit()


def test_a_destructive_round1_treatment_can_be_revised_to_recover_the_full_population():
    # drop_missing_promo really does shrink 400 orders to 120 - shown as
    # a real fact immediately, with a real chance to revise before the
    # central SLA investigation ever runs against the narrowed
    # population. A student who recovers here should be able to finish
    # with a high core score, not carry a permanent penalty.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        destructive_resolution = {"cold_pack_temp_c": "leave_as_missing", "promo_code": "drop_missing_promo"}
        feedback = _play_lesson_to_feedback(
            app,
            resolution_round1=destructive_resolution,
            round1_population_choice="revise_the_treatment",
            round1_revised_resolution=GOOD_RESOLUTION_ROUND1,
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief

        result = finished_results[0]
        assert result.round1_revised is True
        assert result.initial_round1_resolution == destructive_resolution
        assert result.round1_resolution == GOOD_RESOLUTION_ROUND1
        assert result.final_row_count() == 400

        assert any(
            o.text_key == "lesson.l07.feedback.round1_population_recovered_via_revision"
            for o in feedback.evaluation.observations
        )
        assert feedback.evaluation.dimension_scores[ScoreDimension.REASONING] == 92.0
    finally:
        pygame.quit()


def test_keeping_a_destructive_round1_treatment_is_caught_by_scope_coherence():
    # A student who sees the population shrink and still keeps the
    # treatment is a legitimate final state, not a forced revision - but
    # a Final Decision that still claims the untouched full population is
    # incoherent with what they actually did, and REASONING must catch
    # it generically rather than needing a dedicated branch.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        destructive_resolution = {"cold_pack_temp_c": "drop_missing_cold_pack", "promo_code": "recode_no_promo"}
        feedback = _play_lesson_to_feedback(
            app,
            resolution_round1=destructive_resolution,
            round1_population_choice="keep_this_population",
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief

        result = finished_results[0]
        assert result.round1_revised is False
        assert result.round1_resolution == destructive_resolution
        assert result.final_row_count() < 400
        assert any(
            o.text_key == "lesson.l07.feedback.target_scope_ignores_dropped_rows" for o in feedback.evaluation.observations
        )
    finally:
        pygame.quit()


def test_a_naive_fill_can_be_revised_to_preserve_and_recover_the_real_range():
    # The target productive-failure chain: impute pick_minutes, see the
    # sensitivity range collapse to a single point, recognize the
    # uncertainty was hidden rather than resolved, revise to preserve
    # and report, and recompute a real range for the final argument. A
    # student who learned from the consequence should be able to finish
    # with a high core score.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_seven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            resolution_round2={"pick_minutes": "fill_global_median"},
            sensitivity_key="range_collapsed_erased",
            sensitivity_revise=True,
            sensitivity_revised_resolution=GOOD_RESOLUTION_ROUND2,
            sensitivity_revised_key="range_real_undecided",
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief

        result = finished_results[0]
        assert result.pick_minutes_revised is True
        assert result.initial_pick_treatment == "fill_global_median"
        assert result.round2_resolution == GOOD_RESOLUTION_ROUND2
        assert result.has_real_sensitivity_range() is True

        assert any(
            o.text_key == "lesson.l07.feedback.pick_minutes_recovered_via_revision" for o in feedback.evaluation.observations
        )
        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.DATA_QUALITY] == 100.0
        assert scores[ScoreDimension.REPRODUCIBILITY] == 100.0
        assert scores[ScoreDimension.REASONING] == 92.0
        assert scores[ScoreDimension.UNCERTAINTY] == 90.0
        assert scores[ScoreDimension.METHOD] == 94.0
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

        assert isinstance(_leaf_scene(app1.scenes.current.inner), WorkbenchScene)  # repair round 1
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


def test_uncertainty_final_field_is_path_aware():
    # A real range's own correct final claim is "bounds_are_real_assumptions";
    # a collapsed range's is "fill_collapsed_the_calculation" - the same
    # answer is never correct on both paths.
    real_range_correct = score_lesson_seven(_result(), LESSON_07, hints_used=0)
    real_range_wrong_claim = score_lesson_seven(
        _result(decision=dict(GOOD_DECISION, sensitivity="fill_collapsed_the_calculation", evidence=("e1", "e2"))),
        LESSON_07,
        hints_used=0,
    )
    assert (
        real_range_correct.dimension_scores[ScoreDimension.UNCERTAINTY]
        > real_range_wrong_claim.dimension_scores[ScoreDimension.UNCERTAINTY]
    )

    collapsed_base = dict(
        GOOD_DECISION, treatment="fill_global_median", kpi_result="complete_case_ship_it", evidence=("e1", "e2")
    )
    collapsed_correct = score_lesson_seven(
        _result(
            round2_resolution={"pick_minutes": "fill_global_median"},
            sensitivity_interpretation="range_collapsed_erased",
            decision=dict(collapsed_base, sensitivity="fill_collapsed_the_calculation"),
        ),
        LESSON_07,
        hints_used=0,
    )
    collapsed_wrong_claim = score_lesson_seven(
        _result(
            round2_resolution={"pick_minutes": "fill_global_median"},
            sensitivity_interpretation="range_collapsed_erased",
            decision=dict(collapsed_base, sensitivity="bounds_are_real_assumptions"),
        ),
        LESSON_07,
        hints_used=0,
    )
    assert (
        collapsed_correct.dimension_scores[ScoreDimension.UNCERTAINTY]
        > collapsed_wrong_claim.dimension_scores[ScoreDimension.UNCERTAINTY]
    )


_ROUND1_UNCHANGED = GOOD_RESOLUTION_ROUND1
_ROUND1_NARROWED_BY_COLD_PACK = {"cold_pack_temp_c": "drop_missing_cold_pack", "promo_code": "recode_no_promo"}
_ROUND1_NARROWED_BY_PROMO = {"cold_pack_temp_c": "leave_as_missing", "promo_code": "drop_missing_promo"}


@pytest.mark.parametrize(
    "round1_resolution,claimed_scope,expected_coherent",
    [
        # Population unchanged (still all 400 orders) - only
        # this_period_go_orders is actually true of it.
        (_ROUND1_UNCHANGED, "this_period_go_orders", True),
        (_ROUND1_UNCHANGED, "remaining_subset_after_filtering", False),
        (_ROUND1_UNCHANGED, "captured_only", False),
        (_ROUND1_UNCHANGED, "all_novamart_orders", False),
        # Population narrowed by a kept destructive Round 1 pick (two
        # different real ways to get there) - only
        # remaining_subset_after_filtering is true of it. Every other
        # option, all_novamart_orders included, stays wrong - it must
        # never become "coherent" just because this_period_go_orders
        # also fails, which was the actual bug (a boolean equivalence
        # against a single option rather than a real mapping).
        (_ROUND1_NARROWED_BY_COLD_PACK, "remaining_subset_after_filtering", True),
        (_ROUND1_NARROWED_BY_COLD_PACK, "this_period_go_orders", False),
        (_ROUND1_NARROWED_BY_COLD_PACK, "captured_only", False),
        (_ROUND1_NARROWED_BY_COLD_PACK, "all_novamart_orders", False),
        (_ROUND1_NARROWED_BY_PROMO, "remaining_subset_after_filtering", True),
        (_ROUND1_NARROWED_BY_PROMO, "this_period_go_orders", False),
        (_ROUND1_NARROWED_BY_PROMO, "captured_only", False),
        (_ROUND1_NARROWED_BY_PROMO, "all_novamart_orders", False),
    ],
)
def test_scope_coherent_maps_final_pipeline_state_to_the_one_defensible_claim(
    round1_resolution, claimed_scope, expected_coherent
):
    result = score_lesson_seven(
        _result(
            round1_resolution=round1_resolution,
            decision=dict(GOOD_DECISION, target_scope=claimed_scope, evidence=("e1", "e2")),
        ),
        LESSON_07,
        hints_used=0,
    )
    scope_feedback_fired = any(o.text_key == "lesson.l07.feedback.target_scope_ignores_dropped_rows" for o in result.observations)
    assert scope_feedback_fired == (not expected_coherent)


def test_method_rewards_the_correct_treatment_and_the_systemic_fix():
    good = score_lesson_seven(_result(), LESSON_07, hints_used=0)
    weak = score_lesson_seven(
        _result(decision=dict(GOOD_DECISION, required_action="nothing_needed", evidence=("e1", "e2"))),
        LESSON_07,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.METHOD] > weak.dimension_scores[ScoreDimension.METHOD]


def test_method_flags_wrong_structural_treatment_for_cold_pack():
    good = score_lesson_seven(_result(), LESSON_07, hints_used=0)
    wrong = score_lesson_seven(
        _result(decision=dict(GOOD_DECISION, structural_treatment="impute_segment_average", evidence=("e1", "e2"))),
        LESSON_07,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.METHOD] > wrong.dimension_scores[ScoreDimension.METHOD]


def test_mastery_requires_the_exact_correct_set_not_a_superset_or_subset():
    assert _mastery_succeeded(_result(mastery_selection=frozenset({"supplier_lead_days"})))
    assert not _mastery_succeeded(_result(mastery_selection=frozenset({"supplier_lead_days", "unit_cost"})))
    assert not _mastery_succeeded(_result(mastery_selection=frozenset()))
