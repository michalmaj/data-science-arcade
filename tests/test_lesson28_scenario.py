import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.brief import MultiChoiceField
from data_science_arcade.lessons.l28_chart_crime_lab.requests import CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l28_chart_crime_lab.scenario import DECISION_FIELDS, build_lesson_twenty_eight_runner
from data_science_arcade.lessons.l28_chart_crime_lab.scoring import LessonTwentyEightResult
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.dual_axis_reveal_scene import DualAxisRevealScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

from lesson_test_helpers import click_through_mission_briefing


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _pick_picks(scene: ChartDesignerScene, all_correct: bool) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct = CORRECT_OPTION_BY_REQUEST[request.key]
        use_key = correct if all_correct else next(o.key for o in request.options if o.key != correct)
        index = next(i for i, option in enumerate(request.options) if option.key == use_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def _confirm_reveal(scene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.continue_button.on_activate()


def _fill_out_decision(scene: DecisionBuilderScene) -> None:
    for step in scene._steps:
        if scene._is_evidence_step(step):
            evidence_ids = list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.min_count]
            for item_id in evidence_ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        elif isinstance(step, MultiChoiceField):
            for i in range(step.min_count):
                scene.buttons.buttons[i].on_activate()
        else:
            scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_thirteen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_eight_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, ChartDesignerScene)  # initial_pass
        assert app.scenes.current.inner.guided is False
        _pick_picks(app.scenes.current.inner, all_correct=True)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # reveal_axis
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # reveal_window
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # reveal_denominator
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, DualAxisRevealScene)  # reveal_dual_axis
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # revision_intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, ChartDesignerScene)  # revision_pass
        _pick_picks(app.scenes.current.inner, all_correct=True)

        assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision_brief
        _fill_out_decision(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge - skipped
        app.scenes.current.inner.buttons.buttons[1].on_activate()

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)  # feedback
        app.scenes.current.inner.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwentyEightResult)
        assert result.completed_thoughtfully() is True
        assert result.initial_verdict_choices == CORRECT_OPTION_BY_REQUEST
        assert result.verdict_choices == CORRECT_OPTION_BY_REQUEST
        assert set(result.decision) >= {field.key for field in DECISION_FIELDS}
        assert collected["decision"] == result.decision
    finally:
        pygame.quit()


def test_the_revision_pass_is_seeded_with_the_initial_passs_own_pick():
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_eight_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        initial = app.scenes.current.inner
        _pick_picks(initial, all_correct=False)

        _confirm_reveal(app.scenes.current.inner)  # reveal_axis
        _confirm_reveal(app.scenes.current.inner)  # reveal_window
        _confirm_reveal(app.scenes.current.inner)  # reveal_denominator
        _confirm_reveal(app.scenes.current.inner)  # reveal_dual_axis
        _play_dialogue_to_the_end(app.scenes.current)  # revision_intro

        revision = app.scenes.current.inner
        assert isinstance(revision, ChartDesignerScene)
        for key, correct in CORRECT_OPTION_BY_REQUEST.items():
            assert revision.choices[key] != correct
    finally:
        pygame.quit()


def test_a_real_revision_can_correct_a_motivated_initial_pick_to_a_fully_defensible_final_one():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_eight_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        _pick_picks(app.scenes.current.inner, all_correct=False)  # initial_pass

        _confirm_reveal(app.scenes.current.inner)  # reveal_axis
        _confirm_reveal(app.scenes.current.inner)  # reveal_window
        _confirm_reveal(app.scenes.current.inner)  # reveal_denominator
        _confirm_reveal(app.scenes.current.inner)  # reveal_dual_axis
        _play_dialogue_to_the_end(app.scenes.current)  # revision_intro

        _pick_picks(app.scenes.current.inner, all_correct=True)  # revision_pass, corrected this time

        _fill_out_decision(app.scenes.current.inner)  # final_decision_brief

        app.scenes.current.inner.buttons.buttons[1].on_activate()  # mastery_challenge - skipped

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
        app.scenes.current.inner.continue_button.on_activate()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        result = finished_results[0]
        assert result.initial_verdict_choices != CORRECT_OPTION_BY_REQUEST
        assert result.verdict_choices == CORRECT_OPTION_BY_REQUEST
    finally:
        pygame.quit()


def test_reveal_computations_never_mutate_the_final_pick_mirror_state():
    """The interactive pick's own action key (chart_pick_*) must reflect
    only the real final choice - the four reveals record entirely
    separate keys and must never touch it."""
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_eight_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        _pick_picks(app.scenes.current.inner, all_correct=True)  # initial_pass

        pick_actions = [a for a in collected["analytical_context"]["actions"] if a["key"] == "chart_pick_satisfaction_score_claim"]
        assert len(pick_actions) == 1
        code_after_initial = pick_actions[0]["python_code"]

        _confirm_reveal(app.scenes.current.inner)  # reveal_axis
        _confirm_reveal(app.scenes.current.inner)  # reveal_window
        _confirm_reveal(app.scenes.current.inner)  # reveal_denominator
        _confirm_reveal(app.scenes.current.inner)  # reveal_dual_axis

        pick_actions_after_reveals = [
            a for a in collected["analytical_context"]["actions"] if a["key"] == "chart_pick_satisfaction_score_claim"
        ]
        assert len(pick_actions_after_reveals) == 1
        assert pick_actions_after_reveals[0]["python_code"] == code_after_initial
    finally:
        pygame.quit()


def test_no_stale_evidence_survives_a_revision_pass():
    """A student who revises their picks (Back inside ChartDesignerScene,
    or the whole revision_pass stage) must not accumulate duplicate
    Evidence for the same real fact - each reveal's own comparisons are
    recorded exactly once per reveal visit, and reveals are never
    revisited, so the real evidence pool stays exactly 9 items."""
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_eight_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        _pick_picks(app.scenes.current.inner, all_correct=True)  # initial_pass
        _confirm_reveal(app.scenes.current.inner)  # reveal_axis
        _confirm_reveal(app.scenes.current.inner)  # reveal_window
        _confirm_reveal(app.scenes.current.inner)  # reveal_denominator
        _confirm_reveal(app.scenes.current.inner)  # reveal_dual_axis
        _play_dialogue_to_the_end(app.scenes.current)  # revision_intro
        _pick_picks(app.scenes.current.inner, all_correct=True)  # revision_pass

        assert len(collected["analytical_context"]["evidence"]) == 9
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


# --- Regression: the known OVERCLAIM option keys are the only places an
# absolutist claim about one specific design technique ("always
# dishonest", "never legitimate", "automatically suspect") is allowed to
# appear - correction #19's explicit requirement that no OTHER
# student-facing copy states a design technique is inherently deceptive. -

_KNOWN_OVERCLAIM_KEY_FRAGMENTS = (
    "any_non_zero_baseline_chart_is_automatically_dishonest",
    "any_partial_window_is_invalid_only_full_history_is_honest",
    "any_rate_built_on_a_large_denominator_is_automatically_suspect",
    "dual_axis_charts_are_never_a_legitimate_choice",
    "any_chart_using_a_design_choice_like_axis_window_or_dual_axis_is_automatically_suspect",
)
_ABSOLUTIST_PHRASE_MARKERS_EN = ("always dishonest", "never legitimate", "automatically suspect", "automatically dishonest")


def test_no_non_overclaim_copy_calls_a_design_technique_inherently_deceptive():
    from data_science_arcade.localization.service import load_all_locales

    locales = load_all_locales()
    en = locales["en"]
    for key, value in en.items():
        if not key.startswith("lesson.l28."):
            continue
        if any(fragment in key for fragment in _KNOWN_OVERCLAIM_KEY_FRAGMENTS):
            continue
        for marker in _ABSOLUTIST_PHRASE_MARKERS_EN:
            assert marker not in value.lower(), f"{key} uses absolutist phrasing outside its own overclaim option: {value!r}"
