import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l17_hypothesis_detective.scenario import DECISION_FIELDS, build_lesson_seventeen_runner
from data_science_arcade.lessons.l17_hypothesis_detective.scoring import CRITICAL_EVIDENCE_KEYS, LessonSeventeenResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

GOOD_PLAN = {
    "target_population": "all_eligible_returning_customers",
    "primary_outcome": "repeat_purchase_14d",
    "observation_window": "fourteen_days",
    "predicted_direction": "increase",
}
BAD_PLAN = {
    "target_population": "app_users_only",
    "primary_outcome": "average_order_value",
    "observation_window": "thirty_days",
    "predicted_direction": "decrease",
}
GOOD_DECISION = {
    "device_finding_status": "exploratory_discovered_after_reveal",
    "why_device_status_differs": "introduced_only_after_primary_result_visible",
    "primary_result_claim": "observed_plus_one_pp_in_predicted_direction",
    "strongest_defensible_device_claim": "real_pattern_worth_a_new_pre_specified_test",
    "next_step": "form_new_hypothesis_prespecify_test_on_new_data",
}
GOOD_MASTERY_JUDGMENT = "not_borne_out_overall_late_rate_increased"
GOOD_MASTERY_URBAN_STATUS = "post_hoc_exploratory_worth_new_test"
GOOD_MASTERY_EVIDENCE = ("overall_late_rate_increased",)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _leaf_scene(scene):
    while True:
        if isinstance(scene, OfferThenTaskScene):
            active = getattr(scene, "_active", None)
            if active is None:
                break
            scene = active
        elif isinstance(scene, SequenceScene):
            scene = scene._active
        else:
            break
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


def _play_plan(scene: BriefBuilderScene, plan: dict) -> None:
    for field in scene.fields:
        current = scene._current_field()
        scene.buttons.buttons[_option_index(current, plan[current.key])].on_activate()
        scene.next_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict, evidence_ids: list[str] | None = None) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            ids = evidence_ids if evidence_ids is not None else list(scene._evidence_toggle_buttons.keys())
            for item_id in ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_mastery_select(scene: BriefBuilderScene, judgment_key: str, urban_status_key: str, evidence_keys: tuple[str, ...]) -> None:
    judgment_field = scene.fields[0]
    scene.buttons.buttons[_option_index(judgment_field, judgment_key)].on_activate()
    scene.next_button.on_activate()
    urban_status_field = scene.fields[1]
    scene.buttons.buttons[_option_index(urban_status_field, urban_status_key)].on_activate()
    scene.next_button.on_activate()
    multi_field = scene.fields[2]
    for key in evidence_keys:
        scene.buttons.buttons[_option_index(multi_field, key)].on_activate()
    scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    initial_plan=GOOD_PLAN,
    revise: bool = False,
    revised_plan=GOOD_PLAN,
    primary_interpretation="observed_in_predicted_direction",
    device_interpretation="a_real_pattern_worth_a_closer_look",
    decision=GOOD_DECISION,
    evidence_ids=None,
    mastery_engage: bool = False,
    mastery_judgment=GOOD_MASTERY_JUDGMENT,
    mastery_urban_status=GOOD_MASTERY_URBAN_STATUS,
    mastery_evidence=GOOD_MASTERY_EVIDENCE,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # blinded_roster_inspection
    wb = app.scenes.current.inner
    assert "repeat_purchase_14d" not in wb.dataset.frame.columns
    wb.inspection_buttons["one_row_per_customer"].on_activate()
    wb.continue_button.on_activate()

    plan_scene = _leaf_scene(app.scenes.current.inner)  # hypothesis_plan_and_check
    assert isinstance(plan_scene, BriefBuilderScene)
    _play_plan(plan_scene, initial_plan)

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)
    if revise:
        offer.buttons.buttons[0].on_activate()
        revision_scene = _leaf_scene(offer)
        assert isinstance(revision_scene, BriefBuilderScene)
        assert revision_scene.choices == initial_plan  # seeded with the prior draft
        _play_plan(revision_scene, revised_plan)
    else:
        offer.buttons.buttons[1].on_activate()

    assert isinstance(app.scenes.current.inner, DialogueScene)  # plan_locked_confirmation
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # full_pilot_reveal
    full_wb = app.scenes.current.inner
    assert "repeat_purchase_14d" in full_wb.dataset.frame.columns
    full_wb.continue_button.on_activate()

    primary = app.scenes.current.inner  # primary_reveal
    assert isinstance(primary, ComparisonRevealScene)
    _play_reveal(primary, primary_interpretation)

    device_pattern = app.scenes.current.inner  # device_pattern_reveal
    assert isinstance(device_pattern, ComparisonRevealScene)
    _play_reveal(device_pattern, device_interpretation)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # device_provenance_reveal
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_hypothesis_brief
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision, evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()
        select_scene = _leaf_scene(mastery_offer)
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_judgment, mastery_urban_status, mastery_evidence)
    else:
        mastery_offer.buttons.buttons[1].on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_twelve_stages_with_a_correct_plan():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_seventeen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonSeventeenResult)
        assert result.completed_thoughtfully() is True
        assert result.hypothesis_plan == GOOD_PLAN
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert set(result.critical_evidence_present) == set(CRITICAL_EVIDENCE_KEYS)
        assert result.mastery_engaged is True
        assert result.mastery_result == {
            "mastery_route_judgment": GOOD_MASTERY_JUDGMENT,
            "mastery_urban_status": GOOD_MASTERY_URBAN_STATUS,
            "mastery_supporting_evidence": GOOD_MASTERY_EVIDENCE,
        }
        assert collected is not None
    finally:
        pygame.quit()


def test_a_wrong_initial_plan_can_be_really_revised_before_lock():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_seventeen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, initial_plan=BAD_PLAN, revise=True, revised_plan=GOOD_PLAN)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.hypothesis_plan == GOOD_PLAN
    finally:
        pygame.quit()


def test_no_locked_action_exists_before_lock_and_exactly_one_after_that_never_changes():
    app = _init_app()
    try:
        runner, collected = build_lesson_seventeen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        wb = app.scenes.current.inner
        wb.inspection_buttons["one_row_per_customer"].on_activate()
        wb.continue_button.on_activate()

        plan_scene = _leaf_scene(app.scenes.current.inner)
        _play_plan(plan_scene, BAD_PLAN)

        # Drafting alone never records a locked action.
        pre_lock_context = LessonContext()
        pre_lock_context.restore_from_dict(collected.get("analytical_context") or {"version": 1, "actions": [], "evidence": [], "decision": None, "next_id": 1})
        assert [a for a in pre_lock_context.actions if a.key == "hypothesis_plan_locked"] == []

        offer = _leaf_scene(app.scenes.current.inner)
        offer.buttons.buttons[0].on_activate()  # revise
        revision_scene = _leaf_scene(offer)
        _play_plan(revision_scene, GOOD_PLAN)

        post_lock_context = LessonContext()
        post_lock_context.restore_from_dict(collected["analytical_context"])
        locked_actions = [a for a in post_lock_context.actions if a.key == "hypothesis_plan_locked"]
        assert len(locked_actions) == 1
        locked_id = locked_actions[0].id
        locked_code = locked_actions[0].python_code
        assert "all_eligible_returning_customers" in locked_code
        assert "app_users_only" not in locked_code  # the revised plan, not the discarded draft

        # Play the rest of the lesson - the locked action must never change again.
        _play_dialogue_to_the_end(app.scenes.current)  # plan_locked_confirmation
        app.scenes.current.inner.continue_button.on_activate()  # full_pilot_reveal
        _play_reveal(app.scenes.current.inner, "observed_in_predicted_direction")
        _play_reveal(app.scenes.current.inner, "a_real_pattern_worth_a_closer_look")
        _play_dialogue_to_the_end(app.scenes.current)  # provenance
        _play_decision_builder(app.scenes.current.inner, decision_keys=GOOD_DECISION)
        app.scenes.current.inner.buttons.buttons[1].on_activate()  # skip mastery

        final_context = LessonContext()
        final_context.restore_from_dict(collected["analytical_context"])
        final_locked_actions = [a for a in final_context.actions if a.key == "hypothesis_plan_locked"]
        assert len(final_locked_actions) == 1
        assert final_locked_actions[0].id == locked_id
        assert final_locked_actions[0].python_code == locked_code
    finally:
        pygame.quit()


def test_no_outcome_values_or_aggregates_exist_anywhere_before_the_lock():
    app = _init_app()
    try:
        runner, collected = build_lesson_seventeen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        wb = app.scenes.current.inner
        assert isinstance(wb, WorkbenchScene)
        assert "repeat_purchase_14d" not in wb.dataset.frame.columns
        wb.inspection_buttons["one_row_per_customer"].on_activate()
        wb.continue_button.on_activate()

        plan_scene = _leaf_scene(app.scenes.current.inner)
        _play_plan(plan_scene, GOOD_PLAN)
        offer = _leaf_scene(app.scenes.current.inner)
        offer.buttons.buttons[1].on_activate()  # skip revision, lock as-is

        # Right after lock: the locked action's own Python Mirror is
        # provenance-only - no outcome computation exists anywhere yet.
        restored = LessonContext()
        restored.restore_from_dict(collected["analytical_context"])
        mirror_at_lock_time = restored.python_mirror()
        assert "mean()" not in mirror_at_lock_time
        assert "groupby" not in mirror_at_lock_time
    finally:
        pygame.quit()


def test_protocol_check_names_every_wrong_field_and_affirms_when_all_correct():
    app = _init_app()
    try:
        runner, _ = build_lesson_seventeen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)
        wb = app.scenes.current.inner
        wb.inspection_buttons["one_row_per_customer"].on_activate()
        wb.continue_button.on_activate()

        plan_scene = _leaf_scene(app.scenes.current.inner)
        _play_plan(plan_scene, BAD_PLAN)
        offer = _leaf_scene(app.scenes.current.inner)
        assert offer._line_keys == (
            "lesson.l17.protocol_check.issue.population_app_only",
            "lesson.l17.protocol_check.issue.outcome_aov",
            "lesson.l17.protocol_check.issue.window_thirty",
            "lesson.l17.protocol_check.issue.direction_mismatch",
        )
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", DECISION_FIELDS)
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_evidence_is_available_after_a_wrong_interpretation_at_every_reveal():
    app = _init_app()
    try:
        runner, collected = build_lesson_seventeen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(
            app,
            primary_interpretation="too_small_to_count_as_evidence",
            device_interpretation="means_nothing_probably_noise",
        )

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        evidence_label_keys = {item.label_key for item in restored_context.evidence}
        assert "lesson.l17.evidence.plan_locked_before_results" in evidence_label_keys
        assert "lesson.l17.evidence.primary_observed_plus_one_pp" in evidence_label_keys
        assert "lesson.l17.evidence.device_pattern_diverges" in evidence_label_keys
        assert "lesson.l17.evidence.device_split_added_after_reveal" in evidence_label_keys
    finally:
        pygame.quit()


def test_the_happy_path_python_mirror_executes_top_to_bottom():
    import pandas as pd

    from data_science_arcade.lessons.l17_hypothesis_detective import data as d

    app = _init_app()
    try:
        runner, collected = build_lesson_seventeen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app)

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        mirror = restored_context.python_mirror()

        assert "PRE-SPECIFIED BEFORE RESULTS" in mirror
        assert "device_rates = " in mirror

        # The lock action itself carries no computation - "primary =" and
        # "groupby" first appear only in primary_reveal's own action, which
        # must come after the plan block and before the exploratory device
        # computation: PLAN -> primary computation -> EXPLORATORY device
        # computation.
        plan_index = mirror.index("PRE-SPECIFIED BEFORE RESULTS")
        primary_index = mirror.index("primary = pilot.groupby")
        device_index = mirror.index("device_rates = ")
        assert plan_index < primary_index < device_index
        plan_block = mirror[plan_index:primary_index]
        assert "groupby" not in plan_block
        assert "mean()" not in plan_block

        namespace: dict = {"pilot": d.generate_pilot().frame, "pd": pd}
        exec(mirror, namespace)

        assert round(float(namespace["primary"]["control"]) * 100, 1) == 25.0
        assert round(float(namespace["primary"]["one_click"]) * 100, 1) == 26.0
        assert round(float(namespace["device_rates"].loc["app", "one_click"]) * 100, 1) == 40.0
    finally:
        pygame.quit()


def test_score_lesson_seventeen_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_seventeen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        assert feedback.evaluation is not None
    finally:
        pygame.quit()
