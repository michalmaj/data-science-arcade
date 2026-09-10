import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l14_chart_designer.orders import generate_orders
from data_science_arcade.lessons.l14_chart_designer.scenario import DECISION_FIELDS, build_lesson_fourteen_runner
from data_science_arcade.lessons.l14_chart_designer.scoring import CRITICAL_EVIDENCE_KEYS, LessonFourteenResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.chart_builder_scene import ChartBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

GOOD_DECISION = {
    "chart_form_for_stores": "bar_sorted_desc",
    "rationale_for_stores_form": "bars_compare_magnitude",
    "chart_form_for_dates": "line",
    "rationale_for_dates_form": "real_time_order_shows_change",
    "chart_form_for_distribution": "histogram",
    "communication_principle": "honest_complete_caption",
}
GOOD_MASTERY_SUPPORTING = ("ask_names_a_fixed_threshold",)
GOOD_MASTERY_CHART_JUDGMENT = "needs_target_reference_line"


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


def _play_comparison_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_chart_builder(scene: ChartBuilderScene, choice_key: str) -> None:
    index = _option_index(scene.form_options, choice_key)
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


def _play_mastery_select(scene: BriefBuilderScene, supporting_keys: tuple[str, ...], chart_judgment_key: str) -> None:
    multi_field = scene.fields[0]
    for key in supporting_keys:
        scene.buttons.buttons[_option_index(multi_field, key)].on_activate()
    scene.next_button.on_activate()
    single_field = scene.fields[1]
    scene.buttons.buttons[_option_index(single_field, chart_judgment_key)].on_activate()
    scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    stores_choice="bar_natural_order",
    stores_consequence_interpretation="implies_false_continuity",
    dates_choice="bar_chronological",
    dates_consequence_interpretation="real_chronological_meaning",
    distribution_choice="bar_store_averages",
    distribution_consequence_interpretation="bar_height_is_frequency",
    revision_engage: bool = False,
    revised_stores_choice=None,
    revised_dates_choice=None,
    revised_distribution_choice=None,
    decision=GOOD_DECISION,
    evidence_ids=None,
    mastery_engage: bool = False,
    mastery_supporting=GOOD_MASTERY_SUPPORTING,
    mastery_chart_judgment=GOOD_MASTERY_CHART_JUDGMENT,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, ChartBuilderScene)  # store_attempt
    _play_chart_builder(app.scenes.current.inner, stores_choice)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # store_consequence_reveal
    _play_comparison_reveal(app.scenes.current.inner, stores_consequence_interpretation)

    assert isinstance(app.scenes.current.inner, ChartBuilderScene)  # dates_attempt
    _play_chart_builder(app.scenes.current.inner, dates_choice)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # dates_consequence_reveal
    _play_comparison_reveal(app.scenes.current.inner, dates_consequence_interpretation)

    assert isinstance(app.scenes.current.inner, ChartBuilderScene)  # distribution_attempt
    _play_chart_builder(app.scenes.current.inner, distribution_choice)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # distribution_consequence_reveal
    _play_comparison_reveal(app.scenes.current.inner, distribution_consequence_interpretation)

    offer = app.scenes.current.inner
    assert isinstance(offer, OfferThenTaskScene)  # consolidated_revision_offer
    if revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage

        leaf = _leaf_scene(offer)
        assert isinstance(leaf, ChartBuilderScene)
        assert revised_stores_choice is not None
        _play_chart_builder(leaf, revised_stores_choice)

        leaf = _leaf_scene(offer)
        assert isinstance(leaf, ChartBuilderScene)
        assert revised_dates_choice is not None
        _play_chart_builder(leaf, revised_dates_choice)

        leaf = _leaf_scene(offer)
        assert isinstance(leaf, ChartBuilderScene)
        assert revised_distribution_choice is not None
        _play_chart_builder(leaf, revised_distribution_choice)
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision, evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()  # Engage
        select_scene = _leaf_scene(mastery_offer)
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_supporting, mastery_chart_judgment)
    else:
        mastery_offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_twelve_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_fourteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonFourteenResult)
        assert result.completed_thoughtfully() is True
        assert result.chart_choice_stores_first == "bar_natural_order"
        assert result.chart_choice_stores == "bar_natural_order"
        assert result.chart_choice_dates_first == "bar_chronological"
        assert result.chart_choice_dates == "bar_chronological"
        assert result.chart_choice_distribution_first == "bar_store_averages"
        assert result.chart_choice_distribution == "bar_store_averages"
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert set(result.critical_evidence_present) == set(CRITICAL_EVIDENCE_KEYS)
        assert result.mastery_engaged is True
        assert result.mastery_result == {
            "mastery_supporting_evidence": GOOD_MASTERY_SUPPORTING,
            "mastery_chart_judgment": GOOD_MASTERY_CHART_JUDGMENT,
        }
        assert collected is not None
    finally:
        pygame.quit()


def test_a_playthrough_that_skips_mastery_still_completes():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_fourteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, mastery_engage=False)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.mastery_engaged is False
        assert result.mastery_result == {}
    finally:
        pygame.quit()


def test_the_consolidated_revision_lets_all_three_charts_be_re_edited():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_fourteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(
            app,
            stores_choice="line",
            revision_engage=True,
            revised_stores_choice="bar_sorted_desc",
            revised_dates_choice="line",
            revised_distribution_choice="histogram",
        )
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.chart_choice_stores_first == "line"
        assert result.chart_choice_stores == "bar_sorted_desc"
        assert result.chart_choice_dates_first == "bar_chronological"
        assert result.chart_choice_dates == "line"
        assert result.chart_choice_distribution_first == "bar_store_averages"
        assert result.chart_choice_distribution == "histogram"
    finally:
        pygame.quit()


def test_declining_revision_keeps_the_original_three_picks():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_fourteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, revision_engage=False)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.chart_choice_stores == result.chart_choice_stores_first
        assert result.chart_choice_dates == result.chart_choice_dates_first
        assert result.chart_choice_distribution == result.chart_choice_distribution_first
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", DECISION_FIELDS)
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_evidence_is_available_after_a_wrong_interpretation_at_every_reveal():
    app = _init_app()
    try:
        runner, collected = build_lesson_fourteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(
            app,
            stores_consequence_interpretation="doesnt_matter",
            dates_consequence_interpretation="order_doesnt_matter",
            distribution_consequence_interpretation="bar_height_is_a_value",
        )

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        evidence_label_keys = {item.label_key for item in restored_context.evidence}
        assert "lesson.l14.evidence.store_categories" in evidence_label_keys
        assert "lesson.l14.evidence.date_order" in evidence_label_keys
        assert "lesson.l14.evidence.histogram_binning" in evidence_label_keys
    finally:
        pygame.quit()


def test_the_happy_path_python_mirror_executes_top_to_bottom_against_real_orders():
    app = _init_app()
    try:
        runner, collected = build_lesson_fourteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app)

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        mirror = restored_context.python_mirror()

        assert "returns_by_store = " in mirror
        assert "daily_orders = " in mirror
        assert "import numpy as np" in mirror
        assert "hist_counts, hist_edges = np.histogram(" in mirror
        assert "# Visualization intent:" in mirror

        namespace: dict = {"orders": generate_orders().frame}
        exec(mirror, namespace)

        assert round(float(namespace["returns_by_store"]["S01"]), 1) == 15.0
        assert len(namespace["daily_orders"]) == 14
        assert namespace["hist_counts"].sum() == 260
    finally:
        pygame.quit()


def test_score_lesson_fourteen_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_fourteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        assert feedback.evaluation is not None
    finally:
        pygame.quit()
