import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l16_metric_forge.scenario import DECISION_FIELDS, build_lesson_sixteen_runner
from data_science_arcade.lessons.l16_metric_forge.scoring import CRITICAL_EVIDENCE_KEYS, LessonSixteenResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.metric_contract_scene import MetricContractScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

GOOD_DECISION = {
    "business_outcome": "durable_not_a_single_number",
    "denominator_choice_rationale": "cant_shrink_by_leaving_open",
    "maturity_window_reasoning": "immature_hasnt_had_its_window",
    "numerator_loophole": "closing_without_finishing",
    "denominator_loophole": "closed_only_denominator_hides_backlog",
    "guardrail_breach_action": "gate_on_guardrails",
}
GOOD_MASTERY_JUDGMENT = "productivity_needs_completeness_guardrail"
GOOD_MASTERY_EVIDENCE = ("completeness_collapsed",)


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


def _play_contract(scene: MetricContractScene, definition_key: str) -> None:
    index = _option_index(scene.definition_options, definition_key)
    scene.buttons.buttons[index].on_activate()
    scene.finish_button.on_activate()


def _play_guardrails(scene: BriefBuilderScene, guardrail_keys: tuple[str, ...]) -> None:
    field = scene.fields[0]
    for key in guardrail_keys:
        scene.buttons.buttons[_option_index(field, key)].on_activate()
    scene.next_button.on_activate()


def _play_prior_verdict(scene: BriefBuilderScene, key: str) -> None:
    scene.buttons.buttons[_option_index(scene.fields[0], key)].on_activate()
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


def _play_mastery_select(scene: BriefBuilderScene, judgment_key: str, evidence_keys: tuple[str, ...]) -> None:
    single_field = scene.fields[0]
    scene.buttons.buttons[_option_index(single_field, judgment_key)].on_activate()
    scene.next_button.on_activate()
    multi_field = scene.fields[1]
    for key in evidence_keys:
        scene.buttons.buttons[_option_index(multi_field, key)].on_activate()
    scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    initial_definition="eligible_population",
    initial_guardrails=("reopen_rate",),
    stress_a_primary_interpretation="impressive_but_need_more_signals",
    prior_success_verdict="ship_it_success",
    stress_a_guardrail_interpretation="reopens_show_work_wasnt_durable",
    stress_b_definition_interpretation="population_denominator_held",
    stress_b_backlog_interpretation="hidden_cost_the_ratio_cant_see",
    revised_definition="durable",
    revised_guardrails=("reopen_rate", "aged_backlog_rate"),
    rerun_interpretation="fully_resists_both",
    decision=GOOD_DECISION,
    evidence_ids=None,
    mastery_engage: bool = False,
    mastery_judgment=GOOD_MASTERY_JUDGMENT,
    mastery_evidence=GOOD_MASTERY_EVIDENCE,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # raw_ticket_inspection
    wb = app.scenes.current.inner
    wb.inspection_buttons["one_row_per_ticket"].on_activate()
    wb.continue_button.on_activate()

    contract = _leaf_scene(app.scenes.current.inner)  # initial_contract
    assert isinstance(contract, MetricContractScene)
    _play_contract(contract, initial_definition)

    guardrails = _leaf_scene(app.scenes.current.inner)
    assert isinstance(guardrails, BriefBuilderScene)
    _play_guardrails(guardrails, initial_guardrails)

    primary_reveal = _leaf_scene(app.scenes.current.inner)  # stress_test_a
    assert isinstance(primary_reveal, ComparisonRevealScene)
    _play_reveal(primary_reveal, stress_a_primary_interpretation)

    verdict = _leaf_scene(app.scenes.current.inner)
    assert isinstance(verdict, BriefBuilderScene)
    _play_prior_verdict(verdict, prior_success_verdict)

    guardrail_reveal = _leaf_scene(app.scenes.current.inner)
    assert isinstance(guardrail_reveal, ComparisonRevealScene)
    _play_reveal(guardrail_reveal, stress_a_guardrail_interpretation)

    definition_reveal = _leaf_scene(app.scenes.current.inner)  # stress_test_b
    assert isinstance(definition_reveal, ComparisonRevealScene)
    _play_reveal(definition_reveal, stress_b_definition_interpretation)

    backlog_reveal = _leaf_scene(app.scenes.current.inner)
    assert isinstance(backlog_reveal, ComparisonRevealScene)
    _play_reveal(backlog_reveal, stress_b_backlog_interpretation)

    revise_contract = _leaf_scene(app.scenes.current.inner)  # revise_contract
    assert isinstance(revise_contract, MetricContractScene)
    assert revise_contract.choice == initial_definition
    _play_contract(revise_contract, revised_definition)

    revise_guardrails = _leaf_scene(app.scenes.current.inner)
    assert isinstance(revise_guardrails, BriefBuilderScene)
    _play_guardrails(revise_guardrails, revised_guardrails)

    rerun = app.scenes.current.inner  # rerun_stress_test
    assert isinstance(rerun, ComparisonRevealScene)
    _play_reveal(rerun, rerun_interpretation)

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_metric_brief
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision, evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()
        select_scene = _leaf_scene(mastery_offer)
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_judgment, mastery_evidence)
    else:
        mastery_offer.buttons.buttons[1].on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_eleven_stages_with_a_real_revision():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_sixteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonSixteenResult)
        assert result.completed_thoughtfully() is True
        assert result.primary_definition == "durable"
        assert set(result.guardrails) == {"reopen_rate", "aged_backlog_rate"}
        assert result.prior_success_verdict == "ship_it_success"
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert set(result.critical_evidence_present) == set(CRITICAL_EVIDENCE_KEYS)
        assert result.mastery_engaged is True
        assert result.mastery_result == {
            "mastery_metric_system_judgment": GOOD_MASTERY_JUDGMENT,
            "mastery_supporting_evidence": GOOD_MASTERY_EVIDENCE,
        }
        assert collected is not None
    finally:
        pygame.quit()


def test_a_correct_initial_pick_needs_no_real_change_at_revision():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_sixteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(
            app,
            initial_definition="durable",
            initial_guardrails=("reopen_rate", "aged_backlog_rate"),
            revised_definition="durable",
            revised_guardrails=("reopen_rate", "aged_backlog_rate"),
        )
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.primary_definition == "durable"
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", DECISION_FIELDS)
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_evidence_is_available_after_a_wrong_interpretation_at_every_reveal():
    app = _init_app()
    try:
        runner, collected = build_lesson_sixteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(
            app,
            stress_a_primary_interpretation="looks_solved_already",
            stress_a_guardrail_interpretation="reopens_are_unrelated_noise",
            stress_b_definition_interpretation="both_denominators_behave_the_same",
            stress_b_backlog_interpretation="backlog_growth_is_expected_here",
            rerun_interpretation="resists_neither",
        )

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        evidence_label_keys = {item.label_key for item in restored_context.evidence}
        assert "lesson.l16.evidence.headline_improved" in evidence_label_keys
        assert "lesson.l16.evidence.guardrail_deteriorated" in evidence_label_keys
        assert "lesson.l16.evidence.definition_stress_result" in evidence_label_keys
        assert "lesson.l16.evidence.aged_backlog" in evidence_label_keys
        assert "lesson.l16.evidence.revised_contract_resists" in evidence_label_keys
    finally:
        pygame.quit()


def test_the_happy_path_python_mirror_executes_top_to_bottom():
    import pandas as pd

    from data_science_arcade.lessons.l16_metric_forge import data as d

    app = _init_app()
    try:
        runner, collected = build_lesson_sixteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app)

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        mirror = restored_context.python_mirror()

        assert "durable_resolution_rate = " in mirror
        assert "reopen_rate_after = " in mirror
        assert "population_denominator_rate = " in mirror
        assert "aged_backlog_after = " in mirror
        assert "revised_stress_a_rate = " in mirror
        assert "revised_stress_b_rate = " in mirror

        tickets = d.honest_tickets()
        namespace: dict = {
            "tickets": tickets,
            "stress_a_tickets": d.apply_stress_test_a(tickets),
            "stress_b_tickets": d.apply_stress_test_b(tickets),
            "pd": pd,
        }
        exec(mirror, namespace)

        assert round(float(namespace["durable_resolution_rate"]) * 100, 1) in (82.0, 84.8)
        assert round(float(namespace["revised_stress_a_rate"]) * 100, 1) == 84.8
        assert round(float(namespace["revised_stress_b_rate"]) * 100, 1) == 82.0
    finally:
        pygame.quit()


def test_score_lesson_sixteen_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_sixteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        assert feedback.evaluation is not None
    finally:
        pygame.quit()
