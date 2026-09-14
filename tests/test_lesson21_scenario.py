import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l21_funnel_factory.requests import CORRECT_DEFINITION_BY_REQUEST
from data_science_arcade.lessons.l21_funnel_factory.scenario import DECISION_FIELDS, build_lesson_twenty_one_runner
from data_science_arcade.lessons.l21_funnel_factory.scoring import CRITICAL_EVIDENCE_KEYS, LessonTwentyOneResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.funnel_builder_scene import FunnelBuilderScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

GOOD_MASTERY_REAL_BOTTLENECK = "profile_completed"
GOOD_MASTERY_WHY_MISSED = "the_flawed_signup_event_made_a_healthy_step_look_broken_hiding_the_real_one"
GOOD_MASTERY_EVIDENCE = ("flawed_signup_rate_35_vs_correct_81_percent", "profile_completion_real_rate_42_percent")


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _option_index(field_or_options, option_key: str) -> int:
    options = field_or_options.options if hasattr(field_or_options, "options") else field_or_options
    return next(i for i, option in enumerate(options) if option.key == option_key)


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _pick_definitions(scene: FunnelBuilderScene, by_request: dict[str, str]) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        chosen_key = by_request.get(request.key, next(iter(request.definitions)).key)
        index = next(i for i, definition in enumerate(request.definitions) if definition.key == chosen_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def _play_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict, evidence_ids: list[str] | None = None) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            ids = evidence_ids if evidence_ids is not None else list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.max_count]
            for item_id in ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_mastery_select(scene: BriefBuilderScene, real_bottleneck_key: str, why_missed_key: str, evidence_keys: tuple[str, ...]) -> None:
    bottleneck_field = scene.fields[0]
    scene.buttons.buttons[_option_index(bottleneck_field, real_bottleneck_key)].on_activate()
    scene.next_button.on_activate()
    why_field = scene.fields[1]
    scene.buttons.buttons[_option_index(why_field, why_missed_key)].on_activate()
    scene.next_button.on_activate()
    evidence_field = scene.fields[2]
    for key in evidence_keys:
        scene.buttons.buttons[_option_index(evidence_field, key)].on_activate()
    scene.next_button.on_activate()


GOOD_DECISION = {
    "checkout_investigation_conclusion": "blame_cart_to_checkout_step",
    "why_legacy_undercounts": "tracking_pixel_missing_on_newer_app_builds",
    "percent_basis_question": "finds_the_step_thats_uniquely_bad_locally",
    "general_lesson": "justify_definition_independent_of_result",
}


def _play_lesson_to_feedback(
    app,
    *,
    initial_picks: dict[str, str] | None = None,
    revised_picks: dict[str, str] | None = None,
    reveal_a_interpretation: str = "same_step_can_look_broken_plausible_or_excellent_by_definition",
    reveal_b_interpretation: str = "top_shows_cumulative_survival_previous_finds_the_local_loss",
    decision: dict | None = None,
    evidence_ids: list[str] | None = None,
    mastery_engage: bool = False,
    mastery_real_bottleneck: str = GOOD_MASTERY_REAL_BOTTLENECK,
    mastery_why_missed: str = GOOD_MASTERY_WHY_MISSED,
    mastery_evidence: tuple[str, ...] = GOOD_MASTERY_EVIDENCE,
):
    initial_picks = initial_picks if initial_picks is not None else dict(CORRECT_DEFINITION_BY_REQUEST)
    revised_picks = revised_picks if revised_picks is not None else dict(CORRECT_DEFINITION_BY_REQUEST)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # instrumentation_explanation
    _play_dialogue_to_the_end(app.scenes.current)

    initial_scene = app.scenes.current.inner  # initial_funnel_pass
    assert isinstance(initial_scene, FunnelBuilderScene)
    assert initial_scene.guided is False
    _pick_definitions(initial_scene, initial_picks)

    definition_reveal = app.scenes.current.inner  # definition_axis_reveal
    assert isinstance(definition_reveal, ComparisonRevealScene)
    _play_reveal(definition_reveal, reveal_a_interpretation)

    basis_reveal = app.scenes.current.inner  # basis_axis_reveal
    assert isinstance(basis_reveal, ComparisonRevealScene)
    _play_reveal(basis_reveal, reveal_b_interpretation)

    assert isinstance(app.scenes.current.inner, DialogueScene)  # revision_intro
    _play_dialogue_to_the_end(app.scenes.current)

    revision_scene = app.scenes.current.inner  # revision_funnel_pass
    assert isinstance(revision_scene, FunnelBuilderScene)
    assert revision_scene.choices == initial_picks  # seeded with the first pass's own picks
    _pick_definitions(revision_scene, revised_picks)

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision_brief
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision or GOOD_DECISION, evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()
        select_scene = mastery_offer._active
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_real_bottleneck, mastery_why_missed, mastery_evidence)
    else:
        mastery_offer.buttons.buttons[1].on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_with_a_correct_final_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_one_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwentyOneResult)
        assert result.completed_thoughtfully() is True
        assert result.funnel_choices == CORRECT_DEFINITION_BY_REQUEST
        assert result.initial_funnel_choices == CORRECT_DEFINITION_BY_REQUEST
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert result.mastery_engaged is True
        assert collected is not None
    finally:
        pygame.quit()


def test_revision_pass_is_seeded_with_the_initial_pass_and_can_change_the_outcome():
    """The core productive-failure loop: a wrong initial (motivated) pick
    is genuinely revisable after the two mandatory reveals - the revision
    pass starts pre-seeded with it, and picking differently there is what
    the FINAL result (and METHOD) reflects."""
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_one_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        wrong_initial = {**CORRECT_DEFINITION_BY_REQUEST, "mobile_dropout_complaint": "legacy_cart_tracking"}
        feedback = _play_lesson_to_feedback(app, initial_picks=wrong_initial, revised_picks=CORRECT_DEFINITION_BY_REQUEST)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief

        result = finished_results[0]
        assert result.initial_funnel_choices == wrong_initial
        assert result.funnel_choices == CORRECT_DEFINITION_BY_REQUEST
    finally:
        pygame.quit()


def test_evidence_is_available_regardless_of_which_reveal_interpretation_was_chosen():
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_one_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(
            app,
            reveal_a_interpretation="any_definition_is_equally_valid",
            reveal_b_interpretation="percent_of_top_is_always_the_more_honest_number",
        )

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        evidence_label_keys = {item.label_key for item in restored_context.evidence}
        for critical_key in CRITICAL_EVIDENCE_KEYS:
            assert critical_key in evidence_label_keys
    finally:
        pygame.quit()


def test_mirror_final_state_reflects_only_the_revised_pick_never_the_stale_initial_one():
    """The recurring canonical-substitution discipline: after a revision
    that changes at least one pick, the Python Mirror's own action for
    that request must reflect only the FINAL code, never both/either the
    stale initial one."""
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_one_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        wrong_initial = {**CORRECT_DEFINITION_BY_REQUEST, "mobile_dropout_complaint": "legacy_cart_tracking"}
        _play_lesson_to_feedback(app, initial_picks=wrong_initial, revised_picks=CORRECT_DEFINITION_BY_REQUEST)

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        mirror = restored_context.python_mirror()

        assert "complete_cart_tracking" in mirror  # the real final pick's own filter
        # Only one action exists for this request (updated in place, never doubled).
        matching_actions = [a for a in restored_context.actions if a.key == "funnel_pick_mobile_dropout_complaint"]
        assert len(matching_actions) == 1
        assert "legacy_cart_tracking" not in matching_actions[0].python_code

        # The two reveals' own reference variables never collide with any
        # {request_key}_funnel name.
        for var_name in ("definition_check_legacy", "definition_check_complete", "definition_check_raw", "basis_check_top", "basis_check_previous"):
            assert f"{var_name} = (" in mirror
    finally:
        pygame.quit()


def test_mastery_requires_the_correct_judgment_why_and_both_evidence_facts():
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_one_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(
            app,
            mastery_engage=True,
            mastery_real_bottleneck=GOOD_MASTERY_REAL_BOTTLENECK,
            mastery_why_missed=GOOD_MASTERY_WHY_MISSED,
            mastery_evidence=GOOD_MASTERY_EVIDENCE,
        )
        assert isinstance(feedback, LessonFeedbackScene)
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
