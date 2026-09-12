import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pandas as pd
import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l18_randomization_control_room import data as d
from data_science_arcade.lessons.l18_randomization_control_room.scenario import DECISION_FIELDS, build_lesson_eighteen_runner
from data_science_arcade.lessons.l18_randomization_control_room.scoring import (
    ASSIGNMENT_BALANCE_EVIDENCE_KEY,
    ASSIGNMENT_MECHANISM_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    MECHANISM_CONTRAST_EVIDENCE_KEY,
    LessonEighteenResult,
)
from data_science_arcade.ui.assignment_audit_scene import AssignmentAuditScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

_MECHANISM_CLASSIFICATION_BY_DESIGN = {
    d.ID_PARITY: "deterministic_not_randomized",
    d.SIMPLE_RANDOM: "valid_random_fixed_size",
    d.STRATIFIED_RANDOM: "valid_random_within_strata",
}


def _good_decision(final_design: str) -> dict:
    return {
        "mechanism_classification": _MECHANISM_CLASSIFICATION_BY_DESIGN[final_design],
        "what_makes_assignment_randomized": "decided_by_random_mechanism_before_outcome",
        "what_equal_group_sizes_establish": "establishes_nothing_about_mechanism_alone",
        "how_to_interpret_small_realized_imbalance": "does_not_invalidate_valid_randomization",
        "why_stratify_on_platform": "guarantees_balance_on_a_known_covariate_randomness_within_strata",
        "what_must_stay_sealed_during_assignment": "determined_without_outcomes_or_post_treatment_info",
    }


GOOD_MASTERY_MECHANISM = "genuinely_randomly_assigned_per_provenance"
GOOD_MASTERY_IMBALANCE = "real_diagnostic_fact_not_invalidating"
GOOD_MASTERY_EVIDENCE = ("provenance_log_confirms_seeded_random_assignment",)


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


def _pick_design(scene: BriefBuilderScene, design_key: str) -> None:
    field = scene._current_field()
    scene.buttons.buttons[_option_index(field, design_key)].on_activate()
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


def _play_mastery_select(scene: BriefBuilderScene, mechanism_key: str, imbalance_key: str, evidence_keys: tuple[str, ...]) -> None:
    mechanism_field = scene.fields[0]
    scene.buttons.buttons[_option_index(mechanism_field, mechanism_key)].on_activate()
    scene.next_button.on_activate()
    imbalance_field = scene.fields[1]
    scene.buttons.buttons[_option_index(imbalance_field, imbalance_key)].on_activate()
    scene.next_button.on_activate()
    evidence_field = scene.fields[2]
    for key in evidence_keys:
        scene.buttons.buttons[_option_index(evidence_field, key)].on_activate()
    scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    initial_design=d.STRATIFIED_RANDOM,
    revise: bool = False,
    revised_design=d.STRATIFIED_RANDOM,
    decision=None,
    evidence_ids=None,
    mastery_engage: bool = False,
    mastery_mechanism=GOOD_MASTERY_MECHANISM,
    mastery_imbalance=GOOD_MASTERY_IMBALANCE,
    mastery_evidence=GOOD_MASTERY_EVIDENCE,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # roster_inspection
    wb = app.scenes.current.inner
    wb.inspection_buttons["one_row_per_customer"].on_activate()
    wb.continue_button.on_activate()

    pick_scene = _leaf_scene(app.scenes.current.inner)  # design_pick_and_audit: initial pick
    assert isinstance(pick_scene, BriefBuilderScene)
    _pick_design(pick_scene, initial_design)

    initial_audit = _leaf_scene(app.scenes.current.inner)
    assert isinstance(initial_audit, AssignmentAuditScene)
    initial_audit.continue_button.on_activate()

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)
    if revise:
        offer.buttons.buttons[0].on_activate()  # revise
        revision_pick = _leaf_scene(offer)
        assert isinstance(revision_pick, BriefBuilderScene)
        assert revision_pick.choices == {"assignment_design": initial_design}  # seeded with the current final design
        _pick_design(revision_pick, revised_design)
        second_audit = _leaf_scene(offer)
        assert isinstance(second_audit, AssignmentAuditScene)
        second_audit.continue_button.on_activate()
        final_design = revised_design
    else:
        offer.buttons.buttons[1].on_activate()  # keep
        final_design = initial_design

    contrast = app.scenes.current.inner  # mechanism_contrast
    assert isinstance(contrast, AssignmentAuditScene)
    contrast.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, DialogueScene)  # final_design_announcement
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_randomization_brief
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision or _good_decision(final_design), evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()
        select_scene = _leaf_scene(mastery_offer)
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_mechanism, mastery_imbalance, mastery_evidence)
    else:
        mastery_offer.buttons.buttons[1].on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_with_a_stratified_pick_and_no_revision():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_eighteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, initial_design=d.STRATIFIED_RANDOM, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonEighteenResult)
        assert result.completed_thoughtfully() is True
        assert result.initial_design == d.STRATIFIED_RANDOM
        assert result.final_design == d.STRATIFIED_RANDOM
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert set(result.critical_evidence_present) == set(CRITICAL_EVIDENCE_KEYS)
        assert result.mastery_engaged is True
        assert result.mastery_result == {
            "mastery_mechanism_judgment": GOOD_MASTERY_MECHANISM,
            "mastery_imbalance_meaning": GOOD_MASTERY_IMBALANCE,
            "mastery_supporting_evidence": GOOD_MASTERY_EVIDENCE,
        }
        assert collected is not None
    finally:
        pygame.quit()


def test_a_parity_initial_pick_can_be_really_revised_to_stratified():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_eighteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, initial_design=d.ID_PARITY, revise=True, revised_design=d.STRATIFIED_RANDOM)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.initial_design == d.ID_PARITY
        assert result.final_design == d.STRATIFIED_RANDOM
    finally:
        pygame.quit()


def test_skipping_the_revision_keeps_the_initial_design_as_final():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_eighteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, initial_design=d.SIMPLE_RANDOM, revise=False)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.initial_design == d.SIMPLE_RANDOM
        assert result.final_design == d.SIMPLE_RANDOM
    finally:
        pygame.quit()


@pytest.mark.parametrize(
    "final_design,expected_counterexample",
    [(d.ID_PARITY, d.SIMPLE_RANDOM), (d.SIMPLE_RANDOM, d.ID_PARITY), (d.STRATIFIED_RANDOM, d.ID_PARITY)],
)
def test_mechanism_contrast_shows_the_missing_counterexample_for_every_final_design(final_design, expected_counterexample):
    app = _init_app()
    try:
        runner, _ = build_lesson_eighteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        wb = app.scenes.current.inner
        wb.inspection_buttons["one_row_per_customer"].on_activate()
        wb.continue_button.on_activate()

        pick_scene = _leaf_scene(app.scenes.current.inner)
        _pick_design(pick_scene, final_design)
        initial_audit = _leaf_scene(app.scenes.current.inner)
        initial_audit.continue_button.on_activate()
        offer = _leaf_scene(app.scenes.current.inner)
        offer.buttons.buttons[1].on_activate()  # keep

        contrast = app.scenes.current.inner
        assert isinstance(contrast, AssignmentAuditScene)
        expected_group = d.execute_design(expected_counterexample, d.generate_roster().frame)
        expected_audit = d.audit_values(d.generate_roster().frame, expected_group)
        assert contrast.rows[0].treatment_value == expected_audit["n_treatment"]
        assert contrast.rows[0].control_value == expected_audit["n_control"]
    finally:
        pygame.quit()


def test_contrast_evidence_role_is_never_overwritten_by_a_revised_final_audit():
    """The P0 the user flagged: revising away from parity must not erase
    the evidence that parity's own trap was actually seen - the contrast
    beat records a SEPARATE, immutable evidence role from the final
    audit's own current-truth roles."""
    app = _init_app()
    try:
        runner, collected = build_lesson_eighteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, initial_design=d.ID_PARITY, revise=True, revised_design=d.STRATIFIED_RANDOM)

        restored = LessonContext()
        restored.restore_from_dict(collected["analytical_context"])
        evidence_label_keys = {item.label_key for item in restored.evidence}
        assert ASSIGNMENT_MECHANISM_EVIDENCE_KEY in evidence_label_keys
        assert ASSIGNMENT_BALANCE_EVIDENCE_KEY in evidence_label_keys
        assert MECHANISM_CONTRAST_EVIDENCE_KEY in evidence_label_keys
        # Exactly 3 evidence items total - the 2 current-truth roles plus
        # the 1 immutable contrast role, never doubled by the revision.
        assert len(restored.evidence) == 3
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)
    finally:
        pygame.quit()


def test_only_the_finally_executed_designs_code_is_recorded_not_the_abandoned_one():
    app = _init_app()
    try:
        runner, collected = build_lesson_eighteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, initial_design=d.ID_PARITY, revise=True, revised_design=d.STRATIFIED_RANDOM)

        restored = LessonContext()
        restored.restore_from_dict(collected["analytical_context"])
        mirror = restored.python_mirror()
        assert "customer_id_num" in mirror  # parity's own line, but only via the contrast beat's own record
        assignment_audit_action = next(a for a in restored.actions if a.key == "assignment_audit")
        assert "for platform in" in assignment_audit_action.python_code  # stratified's own mirror, the real final design
        assert "np.where" not in assignment_audit_action.python_code  # parity's own mirror must not linger here
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)
    finally:
        pygame.quit()


def test_the_happy_path_python_mirror_executes_top_to_bottom():
    import numpy as np

    app = _init_app()
    try:
        runner, collected = build_lesson_eighteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, initial_design=d.STRATIFIED_RANDOM)

        restored = LessonContext()
        restored.restore_from_dict(collected["analytical_context"])
        mirror = restored.python_mirror()

        namespace: dict = {"roster": d.generate_roster().frame, "pd": pd, "np": np}
        exec(mirror, namespace)

        assert namespace["roster"]["group"].value_counts().to_dict() == {"treatment": 600, "control": 600}
    finally:
        pygame.quit()


@pytest.mark.parametrize(
    "final_design,counterexample_design",
    [(d.ID_PARITY, d.SIMPLE_RANDOM), (d.SIMPLE_RANDOM, d.ID_PARITY), (d.STRATIFIED_RANDOM, d.ID_PARITY)],
)
def test_mirror_top_to_bottom_never_lets_the_contrast_overwrite_the_final_executed_assignment(final_design, counterexample_design):
    """The real bug the user found in PR #87: the mandatory mechanism-
    contrast beat used to reuse DESIGN_MIRROR (the same "roster['group']
    = ..." snippet as the final audit itself), so exec'ing the full
    recorded Mirror top-to-bottom left roster['group'] as whichever
    design was shown LAST (the counterexample) - silently contradicting
    "your final design is locked in." CONTRAST_DESIGN_MIRROR now writes
    to a separate `contrast` frame instead; roster['group'] must still
    reflect the real final executed design after the full mirror runs,
    and `contrast['group']` must independently reflect the
    counterexample - checked on platform COMPOSITION, not just counts,
    since a naive count-only check can't tell parity and stratified
    apart (both give exact 600/600)."""
    import numpy as np

    app = _init_app()
    try:
        runner, collected = build_lesson_eighteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, initial_design=final_design)

        restored = LessonContext()
        restored.restore_from_dict(collected["analytical_context"])
        mirror = restored.python_mirror()

        namespace: dict = {"roster": d.generate_roster().frame, "pd": pd, "np": np}
        exec(mirror, namespace)

        real_roster = d.generate_roster().frame
        expected_final_group = d.execute_design(final_design, real_roster)
        expected_final_audit = d.audit_values(real_roster, expected_final_group)
        expected_contrast_group = d.execute_design(counterexample_design, real_roster)
        expected_contrast_audit = d.audit_values(real_roster, expected_contrast_group)

        final_roster = namespace["roster"]
        final_ios_treatment = (final_roster[final_roster["group"] == "treatment"]["platform"] == "ios").mean()
        assert round(final_ios_treatment, 3) == round(expected_final_audit["ios_share_treatment"], 3)

        assert "contrast" in namespace, "the contrast beat's own code must define its own `contrast` frame"
        contrast = namespace["contrast"]
        contrast_ios_treatment = (contrast[contrast["group"] == "treatment"]["platform"] == "ios").mean()
        assert round(contrast_ios_treatment, 3) == round(expected_contrast_audit["ios_share_treatment"], 3)
    finally:
        pygame.quit()


def test_evidence_is_available_for_the_full_role_set():
    app = _init_app()
    try:
        runner, collected = build_lesson_eighteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(app, initial_design=d.STRATIFIED_RANDOM)

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        evidence_label_keys = {item.label_key for item in restored_context.evidence}
        assert ASSIGNMENT_MECHANISM_EVIDENCE_KEY in evidence_label_keys
        assert ASSIGNMENT_BALANCE_EVIDENCE_KEY in evidence_label_keys
        assert MECHANISM_CONTRAST_EVIDENCE_KEY in evidence_label_keys
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", DECISION_FIELDS)
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_score_lesson_eighteen_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_eighteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        assert feedback.evaluation is not None
    finally:
        pygame.quit()
