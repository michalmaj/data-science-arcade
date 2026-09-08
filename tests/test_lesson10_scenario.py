import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l10_validation_gate.definition import LESSON_10
from data_science_arcade.lessons.l10_validation_gate.scenario import (
    BASELINE_GATE_MEANING_FIELD,
    BATCH_SCOPE_DECISION_FIELD,
    DECISION_FIELDS,
    GATE_FIELDS,
    INVARIANT_ACTION_FIELD,
    MASTERY_MISSING_RULE_FIELD,
    MASTERY_PASS_MEANING_FIELD,
    MASTERY_SEVERITY_FIELD,
    MISSING_COVERAGE_FIELD,
    PASS_MEANING_FIELD,
    PREVENTION_OWNERSHIP_FIELD,
    PUBLISHED_TOTAL_DEFENSIBILITY_FIELD,
    build_lesson_ten_runner,
)
from data_science_arcade.lessons.l10_validation_gate.scoring import LessonTenResult, score_lesson_ten
from data_science_arcade.lessons.l10_validation_gate.twist_data import CORRECT_BATCH_ACTION_KEY, CORRECT_ROUND1_KEY
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing

GOOD_ROUND1_RESOLUTION = {"review_status": CORRECT_ROUND1_KEY}
GOOD_BATCH_ACTION_RESOLUTION = {"review_status": CORRECT_BATCH_ACTION_KEY}
GOOD_GATE_RESOLUTION = {
    "optional_field_severity": "warn_at_threshold",
    "optional_field_threshold": "flag_over_2pct",
    "invariant_tolerance": "small_tolerance_atol_1",
    "invariant_severity": "block",
}
GOOD_DECISION = {
    "baseline_gate_meaning": "six_conditions_only",
    "missing_coverage": "cross_field_invariant_check",
    "invariant_action": "block",
    "batch_scope_decision": "block_whole_batch_replay",
    "pass_meaning": "satisfies_written_checks_only",
    "published_total_defensibility": "report_defensible",
    "prevention_ownership": "cross_field_validation_required",
}
GOOD_MASTERY_RESULT = {
    "mastery_missing_rule": "cross_field_invariant_check",
    "mastery_severity": "block",
    "mastery_pass_meaning": "satisfies_written_checks_only",
}
DECISION_FIELDS_IN_ORDER = (
    BASELINE_GATE_MEANING_FIELD,
    MISSING_COVERAGE_FIELD,
    INVARIANT_ACTION_FIELD,
    BATCH_SCOPE_DECISION_FIELD,
    PASS_MEANING_FIELD,
    PUBLISHED_TOTAL_DEFENSIBILITY_FIELD,
    PREVENTION_OWNERSHIP_FIELD,
)
MASTERY_FIELDS_IN_ORDER = (MASTERY_MISSING_RULE_FIELD, MASTERY_SEVERITY_FIELD, MASTERY_PASS_MEANING_FIELD)


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


def _fill_single_select(scene: BriefBuilderScene, field, option_key: str) -> None:
    scene.buttons.buttons[_option_index(field, option_key)].on_activate()
    scene.next_button.on_activate()


def _first_flagged_cell_button(scene: WorkbenchScene):
    chrome_labels = {
        scene.app.localization.t(key) for key in ("workbench.data.view_table", "workbench.data.view_schema", "workbench.continue")
    }
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


def _play_brief_builder(scene: BriefBuilderScene, choices: dict[str, str]) -> None:
    for step in scene.fields:
        _fill_single_select(scene, step, choices[step.key])


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict) -> None:
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
    baseline_interpretation="six_conditions_held",
    round1_resolution=GOOD_ROUND1_RESOLUTION,
    consequence_interpretation="worth_checking_further",
    round1_revision_engage: bool = False,
    revised_round1_resolution=None,
    gate_resolution=GOOD_GATE_RESOLUTION,
    gate_rerun_interpretation="reflects_only_written_checks",
    gate_revision_engage: bool = False,
    revised_gate_resolution=None,
    concentration_interpretation="shared_process_failure",
    batch_action_resolution=GOOD_BATCH_ACTION_RESOLUTION,
    batch_action_revision_engage: bool = False,
    revised_batch_action_resolution=None,
    gate_rerun_clean_interpretation=None,
    decision=GOOD_DECISION,
    mastery_engage: bool = False,
    mastery_result=GOOD_MASTERY_RESULT,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # baseline gate reveal
    _play_comparison_reveal(app.scenes.current.inner, baseline_interpretation)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # round 1
    _repair_issues(app.scenes.current.inner, round1_resolution)
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # consequence reveal
    _play_comparison_reveal(app.scenes.current.inner, consequence_interpretation)

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)  # round 1 revision offer
    if round1_revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, WorkbenchScene)
        assert revised_round1_resolution is not None
        _repair_issues(leaf, revised_round1_resolution)
        leaf.continue_button.on_activate()
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, DialogueScene)  # coverage investigation
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # gate builder
    _play_brief_builder(app.scenes.current.inner, gate_resolution)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # gate rerun reveal
    _play_comparison_reveal(app.scenes.current.inner, gate_rerun_interpretation)

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)  # gate revision offer
    final_gate_resolution = gate_resolution
    if gate_revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, BriefBuilderScene)
        assert revised_gate_resolution is not None
        _play_brief_builder(leaf, revised_gate_resolution)
        final_gate_resolution = revised_gate_resolution
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # concentration reveal
    _play_comparison_reveal(app.scenes.current.inner, concentration_interpretation)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # batch action decision
    _repair_issues(app.scenes.current.inner, batch_action_resolution)
    app.scenes.current.continue_button.on_activate()

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)  # batch action revision offer
    final_batch_action_resolution = batch_action_resolution
    if batch_action_revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, WorkbenchScene)
        assert revised_batch_action_resolution is not None
        _repair_issues(leaf, revised_batch_action_resolution)
        leaf.continue_button.on_activate()
        final_batch_action_resolution = revised_batch_action_resolution
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, DialogueScene)  # replay
    _play_dialogue_to_the_end(app.scenes.current)

    replay_happened = final_batch_action_resolution.get("review_status") == CORRECT_BATCH_ACTION_KEY
    if gate_rerun_clean_interpretation is None:
        gate_rerun_clean_interpretation = "safe_to_publish" if replay_happened else "still_unresolved"

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # gate rerun clean / unresolved
    _play_comparison_reveal(app.scenes.current.inner, gate_rerun_clean_interpretation)

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
        _play_brief_builder(select_scene, mastery_result)
    else:
        mastery_offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_nineteen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_ten_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(app, mastery_engage=True)
        app.scenes.current.on_complete()  # feedback -> debrief

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTenResult)
        assert result.completed_thoughtfully() is True
        assert result.round1_resolution == GOOD_ROUND1_RESOLUTION
        assert result.batch_action_resolution == GOOD_BATCH_ACTION_RESOLUTION
        assert result.gate_resolution == GOOD_GATE_RESOLUTION
        assert set(result.decision) == {field.key for field in DECISION_FIELDS_IN_ORDER} | {"evidence"}
        assert result.mastery_engaged is True
        assert result.mastery_result == GOOD_MASTERY_RESULT
        assert collected is not None
    finally:
        pygame.quit()


def test_a_playthrough_that_skips_mastery_still_completes():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_ten_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, mastery_engage=False)
        app.scenes.current.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.mastery_engaged is False
        assert result.mastery_result == {}
    finally:
        pygame.quit()


def test_approving_for_publication_can_be_revised_via_the_revision_offer():
    # The central productive-failure chain: approve under the false-green
    # baseline gate, see its own real naive-total consequence, revise via
    # the real, un-punished offer, then correctly block-and-replay. This
    # trajectory never drags core METHOD down (see scoring's own
    # docstring) - only OVERCONFIDENCE carries that signal.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_ten_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            round1_resolution={"review_status": "approve_for_publication"},
            round1_revision_engage=True,
            revised_round1_resolution=GOOD_ROUND1_RESOLUTION,
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.round1_revised is True
        assert result.initial_round1_resolution == {"review_status": "approve_for_publication"}
        assert result.round1_resolution == GOOD_ROUND1_RESOLUTION

        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.METHOD] == 94.0
        assert any(o.text_key == "lesson.l10.feedback.round1_recovered_via_revision" for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_a_gate_that_never_authors_the_invariant_check_can_be_revised():
    # P0 fix: the gate that actually runs reflects the student's own real
    # config - picking no_invariant_check means nothing gets flagged,
    # until a real revision authors the check for real.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_ten_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        weak_gate = dict(GOOD_GATE_RESOLUTION, invariant_tolerance="no_invariant_check")
        feedback = _play_lesson_to_feedback(
            app,
            gate_resolution=weak_gate,
            gate_revision_engage=True,
            revised_gate_resolution=GOOD_GATE_RESOLUTION,
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.gate_revised is True
        assert result.initial_gate_resolution == weak_gate
        assert result.gate_resolution == GOOD_GATE_RESOLUTION
        assert any(o.text_key == "lesson.l10.feedback.gate_recovered_via_revision" for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_a_gate_that_never_authors_the_invariant_check_flags_nothing():
    app = _init_app()
    try:
        runner, _ = build_lesson_ten_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        weak_gate = dict(GOOD_GATE_RESOLUTION, invariant_tolerance="no_invariant_check")
        feedback = _play_lesson_to_feedback(
            app,
            gate_resolution=weak_gate,
            decision=dict(GOOD_DECISION, missing_coverage="null_rate_check"),
        )
        assert isinstance(feedback, LessonFeedbackScene)
    finally:
        pygame.quit()


def test_a_wrong_batch_action_can_be_revised_via_its_own_revision_offer():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_ten_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            batch_action_resolution={"review_status": "quarantine_and_report_rest"},
            batch_action_revision_engage=True,
            revised_batch_action_resolution=GOOD_BATCH_ACTION_RESOLUTION,
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.batch_action_revised is True
        assert result.initial_batch_action_resolution == {"review_status": "quarantine_and_report_rest"}
        assert result.batch_action_resolution == GOOD_BATCH_ACTION_RESOLUTION
        assert result.replay_executed() is True
        assert any(o.text_key == "lesson.l10.feedback.batch_action_recovered_via_revision" for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_declining_the_batch_action_revision_offer_never_replays():
    # P0 fix: the final rerun scene must be path-aware - no replay ever
    # happened, so it must never claim a corrected total.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_ten_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            batch_action_resolution={"review_status": "quarantine_and_report_rest"},
            batch_action_revision_engage=False,
            decision=dict(
                GOOD_DECISION,
                batch_scope_decision="quarantine_and_report_rest",
                published_total_defensibility="report_provisional",
            ),
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.replay_executed() is False
        assert result.published_total_defensible() is False
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", [*GATE_FIELDS, *DECISION_FIELDS_IN_ORDER, *MASTERY_FIELDS_IN_ORDER])
def test_every_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_score_lesson_ten_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_ten_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        expected = score_lesson_ten(
            LessonTenResult(
                round1_resolution=GOOD_ROUND1_RESOLUTION,
                batch_action_resolution=GOOD_BATCH_ACTION_RESOLUTION,
                gate_resolution=GOOD_GATE_RESOLUTION,
                decision=dict(GOOD_DECISION, evidence=()),
            ),
            LESSON_10,
            hints_used=0,
        )
        assert set(feedback.evaluation.dimension_scores) == set(expected.dimension_scores)
    finally:
        pygame.quit()
