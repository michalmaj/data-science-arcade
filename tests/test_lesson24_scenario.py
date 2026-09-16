import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l24_survey_bureau.requests import CORRECT_COMBO_BY_REQUEST
from data_science_arcade.lessons.l24_survey_bureau.scenario import DECISION_FIELDS, build_lesson_twenty_four_runner
from data_science_arcade.lessons.l24_survey_bureau.scoring import LessonTwentyFourResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.survey_builder_scene import SurveyBuilderScene

from lesson_test_helpers import click_through_mission_briefing


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _pick_combo(scene: SurveyBuilderScene, wording_key: str | None, channel_key: str | None) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_wording, correct_channel = CORRECT_COMBO_BY_REQUEST[request.key]
        use_wording = wording_key if wording_key is not None else correct_wording
        use_channel = channel_key if channel_key is not None else correct_channel
        wording_index = next(i for i, option in enumerate(request.wording_options) if option.key == use_wording)
        channel_index = next(i for i, option in enumerate(request.channel_options) if option.key == use_channel)
        scene.buttons.buttons[wording_index].on_activate()
        scene.buttons.buttons[len(request.wording_options) + channel_index].on_activate()
        scene.next_button.on_activate()


def _pick_every_combo_correctly(scene: SurveyBuilderScene) -> None:
    _pick_combo(scene, None, None)


def _confirm_reveal(scene: ComparisonRevealScene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.continue_button.on_activate()


def _fill_out_decision(scene: DecisionBuilderScene) -> None:
    for step in scene._steps:
        if scene._is_evidence_step(step):
            evidence_ids = list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.min_count]
            for item_id in evidence_ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_twelve_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_four_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, SurveyBuilderScene)  # initial_survey_pass
        assert app.scenes.current.inner.guided is False
        _pick_every_combo_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # coverage_bias_reveal
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # sampling_frame_reveal
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # nonresponse_bias_reveal
        _confirm_reveal(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # revision_intro
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, SurveyBuilderScene)  # revision_survey_pass
        _pick_every_combo_correctly(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision_brief
        _fill_out_decision(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge - skipped
        app.scenes.current.inner.buttons.buttons[1].on_activate()

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)  # feedback
        app.scenes.current.inner.buttons.buttons[0].on_activate()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwentyFourResult)
        assert result.completed_thoughtfully() is True
        assert result.initial_survey_choices == CORRECT_COMBO_BY_REQUEST
        assert result.survey_choices == CORRECT_COMBO_BY_REQUEST
        assert set(result.decision) >= {field.key for field in DECISION_FIELDS}
        assert collected["decision"] == result.decision
    finally:
        pygame.quit()


def test_the_revision_pass_is_seeded_with_the_initial_passs_own_pick():
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_four_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        initial = app.scenes.current.inner
        _pick_combo(initial, "neutral", "power_user_panel")

        _confirm_reveal(app.scenes.current.inner)  # coverage_bias_reveal
        _confirm_reveal(app.scenes.current.inner)  # sampling_frame_reveal
        _confirm_reveal(app.scenes.current.inner)  # nonresponse_bias_reveal
        _play_dialogue_to_the_end(app.scenes.current)  # revision_intro

        revision = app.scenes.current.inner
        assert isinstance(revision, SurveyBuilderScene)
        assert revision.choices == {"general_satisfaction_check": ("neutral", "power_user_panel")}
    finally:
        pygame.quit()


def test_a_real_revision_can_correct_a_motivated_initial_pick_to_a_fully_defensible_final_one():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_four_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        _pick_combo(app.scenes.current.inner, "neutral", "power_user_panel")  # initial_survey_pass

        _confirm_reveal(app.scenes.current.inner)  # coverage_bias_reveal
        _confirm_reveal(app.scenes.current.inner)  # sampling_frame_reveal
        _confirm_reveal(app.scenes.current.inner)  # nonresponse_bias_reveal
        _play_dialogue_to_the_end(app.scenes.current)  # revision_intro

        _pick_every_combo_correctly(app.scenes.current)  # revision_survey_pass, corrected this time

        _fill_out_decision(app.scenes.current.inner)  # final_decision_brief

        app.scenes.current.inner.buttons.buttons[1].on_activate()  # mastery_challenge - skipped

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
        app.scenes.current.inner.buttons.buttons[0].on_activate()
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        result = finished_results[0]
        assert result.initial_survey_choices == {"general_satisfaction_check": ("neutral", "power_user_panel")}
        assert result.survey_choices == CORRECT_COMBO_BY_REQUEST
    finally:
        pygame.quit()


def test_reveal_computations_never_mutate_the_final_survey_choice_mirror_state():
    """The interactive pick's own action key (survey_pick_*) must reflect
    only the real final choice - the three reveals record entirely
    separate keys and must never touch it."""
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_four_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        _pick_every_combo_correctly(app.scenes.current)  # initial_survey_pass

        pick_actions = [a for a in collected["analytical_context"]["actions"] if a["key"] == "survey_pick_general_satisfaction_check"]
        assert len(pick_actions) == 1
        code_after_initial = pick_actions[0]["python_code"]

        _confirm_reveal(app.scenes.current.inner)  # coverage_bias_reveal
        _confirm_reveal(app.scenes.current.inner)  # sampling_frame_reveal
        _confirm_reveal(app.scenes.current.inner)  # nonresponse_bias_reveal

        pick_actions_after_reveals = [a for a in collected["analytical_context"]["actions"] if a["key"] == "survey_pick_general_satisfaction_check"]
        assert len(pick_actions_after_reveals) == 1
        assert pick_actions_after_reveals[0]["python_code"] == code_after_initial
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
