import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l06_schema_repair_shop.definition import LESSON_06
from data_science_arcade.lessons.l06_schema_repair_shop.scenario import (
    DELIVERED_AT_CONTRACT_FIELD,
    DURATION_CONTRACT_FIELD,
    KPI_RESULT_FIELD,
    MASTERY_FIELD,
    READINESS_FIELD,
    REMAINING_AMBIGUITY_FIELD,
    REQUIRED_CHANGE_FIELD,
    SAFE_COLUMNS_FIELD,
    SAFE_USE_FIELD,
    SHIPMENT_ID_CONTRACT_FIELD,
    _format_rate,
    build_lesson_six_runner,
)
from data_science_arcade.lessons.l06_schema_repair_shop.scoring import (
    LessonSixResult,
    _mastery_succeeded,
    score_lesson_six,
)
from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import ROUND1_ISSUES, ROUND2_ISSUES
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing

GOOD_CONTRACT_ROUND1 = {"shipment_id_contract": "identifier", "delivered_at_contract": "timestamp"}
GOOD_CONTRACT_ROUND2 = {"duration_contract": "per_store_unit_drift"}
GOOD_RESOLUTION = {"shipment_id": "cast_to_text", "delivered_at": "coerce_keep_nat", "duration_minutes": "fix_store_d_only"}
GOOD_DECISION = {
    "readiness": "conditionally_ready",
    "kpi_result": "corrected_12",
    "remaining_ambiguity": "malformed_rows_pattern",
    "safe_use": "this_month_sla",
    "required_change": "update_contract_and_validate",
}
DECISION_FIELDS_IN_ORDER = (
    READINESS_FIELD,
    KPI_RESULT_FIELD,
    REMAINING_AMBIGUITY_FIELD,
    SAFE_USE_FIELD,
    REQUIRED_CHANGE_FIELD,
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
    safe_columns=("item_count",),
    inspection_option="dtypes_are_a_starting_point",
    contract_round1=GOOD_CONTRACT_ROUND1,
    resolution_round1=None,
    reveal1_key="worth_checking",
    contract_round2=GOOD_CONTRACT_ROUND2,
    resolution_round2=None,
    reveal2_key="unit_drift",
    decision=GOOD_DECISION,
    mastery_engage: bool = False,
    mastery_selection=("store_id", "revenue"),
) -> LessonFeedbackScene:
    resolution_round1 = resolution_round1 or {"shipment_id": GOOD_RESOLUTION["shipment_id"], "delivered_at": GOOD_RESOLUTION["delivered_at"]}
    resolution_round2 = resolution_round2 or {"duration_minutes": GOOD_RESOLUTION["duration_minutes"]}

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # raw inspection
    _answer_inspection(app.scenes.current.inner, inspection_option)

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # safe columns prediction
    _fill_multi_select(app.scenes.current.inner, SAFE_COLUMNS_FIELD, safe_columns)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # first KPI attempt
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # contract builder round 1
    scene = app.scenes.current.inner
    _fill_single_select(scene, SHIPMENT_ID_CONTRACT_FIELD, contract_round1["shipment_id_contract"])
    _fill_single_select(app.scenes.current.inner, DELIVERED_AT_CONTRACT_FIELD, contract_round1["delivered_at_contract"])

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # repair round 1
    _repair_issues(app.scenes.current.inner, resolution_round1)
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # kpi reveal 1
    _play_comparison_reveal(app.scenes.current.inner, reveal1_key)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # root cause pivot
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # duration schema check
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # contract builder round 2
    _fill_single_select(app.scenes.current.inner, DURATION_CONTRACT_FIELD, contract_round2["duration_contract"])

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # repair round 2
    _repair_issues(app.scenes.current.inner, resolution_round2)
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # kpi reveal 2
    _play_comparison_reveal(app.scenes.current.inner, reveal2_key)

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


def test_the_full_lesson_plays_through_all_seventeen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_six_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(app, mastery_engage=True)
        app.scenes.current.on_complete()  # feedback -> debrief

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonSixResult)
        assert result.completed_thoughtfully() is True
        assert result.round1_resolution == {"shipment_id": "cast_to_text", "delivered_at": "coerce_keep_nat"}
        assert result.round2_resolution == {"duration_minutes": "fix_store_d_only"}
        assert result.malformed_count_reported == 2
        assert set(result.decision) == {field.key for field in DECISION_FIELDS_IN_ORDER} | {"evidence"}
        assert result.mastery_engaged is True
        assert result.mastery_selection == frozenset({"store_id", "revenue"})
        assert collected is not None  # the same dict passed to LessonRunner throughout
    finally:
        pygame.quit()


def test_a_playthrough_that_skips_mastery_still_completes():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_six_runner(app, on_finished=lambda result: finished_results.append(result))
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


def test_analytical_context_survives_a_checkpoint_new_app_and_resume():
    app1 = _init_app()
    try:
        runner1, _ = build_lesson_six_runner(app1, on_finished=lambda result: None)
        runner1.start()
        click_through_mission_briefing(app1)
        _play_dialogue_to_the_end(app1.scenes.current)  # briefing
        _answer_inspection(app1.scenes.current.inner, "dtypes_are_a_starting_point")  # raw inspection
        _fill_multi_select(app1.scenes.current.inner, SAFE_COLUMNS_FIELD, ("item_count",))  # prediction
        _play_dialogue_to_the_end(app1.scenes.current)  # first attempt
        scene = app1.scenes.current.inner
        _fill_single_select(scene, SHIPMENT_ID_CONTRACT_FIELD, "identifier")
        _fill_single_select(app1.scenes.current.inner, DELIVERED_AT_CONTRACT_FIELD, "timestamp")

        assert isinstance(app1.scenes.current.inner, WorkbenchScene)  # repair round 1
        _repair_issues(app1.scenes.current.inner, {"shipment_id": "cast_to_text", "delivered_at": "coerce_keep_nat"})
        app1.scenes.current.continue_button.on_activate()  # advances + checkpoints; quit right here
    finally:
        pygame.quit()

    app2 = _init_app()
    try:
        runner2, _ = build_lesson_six_runner(app2, on_finished=lambda result: None)
        runner2.start()  # resumes straight into kpi_reveal1

        assert isinstance(app2.scenes.current.inner, ComparisonRevealScene)
        resumed_context = app2.scenes.current.inner.context
        assert len(resumed_context.actions) == 2  # both round-1 issues' evidence already recorded
        assert len(resumed_context.evidence) == 2
    finally:
        pygame.quit()


def test_a_round1_mistake_gets_a_real_second_chance_in_round2_and_the_final_result_reflects_the_fix():
    # cast_category is a real wrong pick for shipment_id (see
    # CORRECT_REPAIR) - Round 2's own WorkbenchScene must re-offer it
    # alongside duration_minutes, and the corrected pick there must be
    # what the final, checkpointed round1_resolution actually shows -
    # never a silently-preserved first mistake.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_six_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(
            app,
            resolution_round1={"shipment_id": "cast_category", "delivered_at": "coerce_keep_nat"},
            resolution_round2={"shipment_id": "cast_to_text", "duration_minutes": "fix_store_d_only"},
        )
        app.scenes.current.on_complete()  # feedback -> debrief
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.round1_resolution == {"shipment_id": "cast_to_text", "delivered_at": "coerce_keep_nat"}
        assert result.round2_resolution == {"duration_minutes": "fix_store_d_only"}
    finally:
        pygame.quit()


def test_a_round1_issue_resolved_correctly_the_first_time_is_not_re_offered():
    app = _init_app()
    try:
        runner, _ = build_lesson_six_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _answer_inspection(app.scenes.current.inner, "dtypes_are_a_starting_point")
        _fill_multi_select(app.scenes.current.inner, SAFE_COLUMNS_FIELD, ("item_count",))
        _play_dialogue_to_the_end(app.scenes.current)  # first attempt
        scene = app.scenes.current.inner
        _fill_single_select(scene, SHIPMENT_ID_CONTRACT_FIELD, "identifier")
        _fill_single_select(app.scenes.current.inner, DELIVERED_AT_CONTRACT_FIELD, "timestamp")
        _repair_issues(app.scenes.current.inner, GOOD_RESOLUTION)  # both correct the first time
        app.scenes.current.continue_button.on_activate()
        _play_comparison_reveal(app.scenes.current.inner, "worth_checking")
        _play_dialogue_to_the_end(app.scenes.current)  # root cause pivot
        app.scenes.current.continue_button.on_activate()  # duration schema check
        _fill_single_select(app.scenes.current.inner, DURATION_CONTRACT_FIELD, "per_store_unit_drift")

        repair_round2_scene = app.scenes.current.inner
        assert isinstance(repair_round2_scene, WorkbenchScene)
        assert [issue.column for issue in repair_round2_scene.issues] == ["duration_minutes"]
    finally:
        pygame.quit()


def test_format_rate_handles_nan_without_crashing():
    assert _format_rate(float("nan")) == "n/a"
    assert _format_rate(0.294) == "29%"


@pytest.mark.parametrize("field", [*DECISION_FIELDS_IN_ORDER, SAFE_COLUMNS_FIELD, SHIPMENT_ID_CONTRACT_FIELD, DELIVERED_AT_CONTRACT_FIELD, DURATION_CONTRACT_FIELD, MASTERY_FIELD])
def test_every_field_has_at_least_three_options(field):
    assert len(field.options) >= 3


# --- Scoring, exercised directly against hand-built results ---------------


def _result(**overrides) -> LessonSixResult:
    base = dict(
        safe_columns=frozenset({"item_count"}),
        shipment_id_contract="identifier",
        delivered_at_contract="timestamp",
        duration_contract="per_store_unit_drift",
        round1_resolution={"shipment_id": "cast_to_text", "delivered_at": "coerce_keep_nat"},
        round2_resolution={"duration_minutes": "fix_store_d_only"},
        malformed_count_reported=2,
        decision=dict(GOOD_DECISION, evidence=("e1", "e2")),
        critical_evidence_present=(
            "issue.shipment_id.evidence",
            "issue.delivered_at.evidence",
            "reveal2.corrected_label",
        ),
    )
    base.update(overrides)
    return LessonSixResult(**base)


def test_data_quality_rewards_all_four_correct_declarations():
    good = score_lesson_six(_result(), LESSON_06, hints_used=0)
    bad = score_lesson_six(
        _result(safe_columns=frozenset(), shipment_id_contract="numeric_measure", duration_contract="uniform_minutes"),
        LESSON_06,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.DATA_QUALITY] > bad.dimension_scores[ScoreDimension.DATA_QUALITY]
    assert good.dimension_scores[ScoreDimension.DATA_QUALITY] == 100.0


def test_data_quality_flags_duration_declared_uniform_after_the_twist():
    result = score_lesson_six(_result(duration_contract="uniform_minutes"), LESSON_06, hints_used=0)
    assert any(o.text_key == "lesson.l06.feedback.duration_declared_uniform_after_twist" for o in result.observations)


def test_reproducibility_rewards_repairs_that_actually_generalize():
    good = score_lesson_six(_result(), LESSON_06, hints_used=0)
    over_corrected = score_lesson_six(
        _result(round2_resolution={"duration_minutes": "fix_every_row"}), LESSON_06, hints_used=0
    )
    assert good.dimension_scores[ScoreDimension.REPRODUCIBILITY] > over_corrected.dimension_scores[ScoreDimension.REPRODUCIBILITY]


def test_data_quality_and_reproducibility_are_independent_signals():
    # Correct concept (Contract Builder), wrong execution (repair picker) -
    # the two dimensions must actually diverge, not move together.
    result = score_lesson_six(
        _result(round2_resolution={"duration_minutes": "fix_every_row"}), LESSON_06, hints_used=0
    )
    assert result.dimension_scores[ScoreDimension.DATA_QUALITY] == 100.0
    assert result.dimension_scores[ScoreDimension.REPRODUCIBILITY] < 100.0


def test_evidence_rewards_citing_the_critical_facts():
    good = score_lesson_six(_result(), LESSON_06, hints_used=0)
    empty = score_lesson_six(_result(critical_evidence_present=()), LESSON_06, hints_used=0)
    assert good.dimension_scores[ScoreDimension.EVIDENCE] > empty.dimension_scores[ScoreDimension.EVIDENCE]


def test_reasoning_catches_reporting_the_naive_number():
    good = score_lesson_six(_result(), LESSON_06, hints_used=0)
    naive = score_lesson_six(
        _result(decision=dict(GOOD_DECISION, kpi_result="naive_29", evidence=("e1", "e2"))), LESSON_06, hints_used=0
    )
    assert good.dimension_scores[ScoreDimension.REASONING] > naive.dimension_scores[ScoreDimension.REASONING]


def test_reasoning_catches_readiness_contradicting_ambiguity():
    result = score_lesson_six(
        _result(decision=dict(GOOD_DECISION, readiness="ready", evidence=("e1", "e2"))), LESSON_06, hints_used=0
    )
    assert any(o.text_key == "lesson.l06.feedback.readiness_contradicts_ambiguity" for o in result.observations)


def test_method_rewards_conditionally_ready_and_the_systemic_fix():
    good = score_lesson_six(_result(), LESSON_06, hints_used=0)
    weak = score_lesson_six(
        _result(decision=dict(GOOD_DECISION, required_change="nothing_needed", evidence=("e1", "e2"))),
        LESSON_06,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.METHOD] > weak.dimension_scores[ScoreDimension.METHOD]


def test_mastery_requires_the_exact_correct_set_not_a_superset_or_subset():
    assert _mastery_succeeded(_result(mastery_selection=frozenset({"store_id", "revenue"})))
    assert not _mastery_succeeded(_result(mastery_selection=frozenset({"store_id", "revenue", "quantity"})))
    assert not _mastery_succeeded(_result(mastery_selection=frozenset({"store_id"})))


def test_data_quality_is_not_capped_by_a_wrong_early_safe_columns_guess():
    # The safe-columns prediction is a prior, made before any real
    # evidence - a wrong guess there must never permanently cap a
    # student whose real, final contract declarations are all correct.
    result = score_lesson_six(_result(safe_columns=frozenset()), LESSON_06, hints_used=0)
    assert result.dimension_scores[ScoreDimension.DATA_QUALITY] == 100.0
    assert any(o.text_key == "lesson.l06.feedback.contract_recovered_after_early_miss" for o in result.observations)


def test_reproducibility_accepts_either_valid_shipment_id_representation():
    # An identifier's own physical representation doesn't need to change
    # just because its semantic type is "identifier" - keeping it int64
    # is just as reproducibility-correct as casting it to text.
    cast_to_text = score_lesson_six(_result(), LESSON_06, hints_used=0)
    kept_int = score_lesson_six(
        _result(round1_resolution={"shipment_id": "recast_int", "delivered_at": "coerce_keep_nat"}),
        LESSON_06,
        hints_used=0,
    )
    assert cast_to_text.dimension_scores[ScoreDimension.REPRODUCIBILITY] == 100.0
    assert kept_int.dimension_scores[ScoreDimension.REPRODUCIBILITY] == 100.0


def test_reasoning_catches_citing_malformed_pattern_when_the_pipeline_shows_zero():
    # A repair that silently dropped the 2 malformed rows (coerce_then_drop)
    # leaves nothing for "whether the pattern recurs" to have been noticed
    # from - citing it anyway is a real, checkable incoherence.
    result = score_lesson_six(_result(malformed_count_reported=0), LESSON_06, hints_used=0)
    assert any(o.text_key == "lesson.l06.feedback.ambiguity_contradicts_own_pipeline" for o in result.observations)


def test_reasoning_catches_overclaiming_exactness_for_the_whole_month():
    result = score_lesson_six(
        _result(decision=dict(GOOD_DECISION, kpi_result="corrected_12_all_month", evidence=("e1", "e2"))),
        LESSON_06,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l06.feedback.kpi_overclaimed_exactness" for o in result.observations)
    good = score_lesson_six(_result(), LESSON_06, hints_used=0)
    assert result.dimension_scores[ScoreDimension.REASONING] < good.dimension_scores[ScoreDimension.REASONING]


def test_trajectory_feedback_notes_recovering_the_read_by_reveal_two():
    result = score_lesson_six(
        _result(reveal1_interpretation="ship_as_is", reveal2_interpretation="unit_drift"), LESSON_06, hints_used=0
    )
    assert any(o.text_key == "lesson.l06.feedback.recovered_the_read_by_reveal_two" for o in result.observations)

    flagged_early = score_lesson_six(
        _result(reveal1_interpretation="worth_checking", reveal2_interpretation="unit_drift"), LESSON_06, hints_used=0
    )
    assert not any(
        o.text_key == "lesson.l06.feedback.recovered_the_read_by_reveal_two" for o in flagged_early.observations
    )
