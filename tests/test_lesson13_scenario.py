import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l13_join_junction.definition import LESSON_13
from data_science_arcade.lessons.l13_join_junction.orders import generate_active_promotions, generate_customers, generate_orders
from data_science_arcade.lessons.l13_join_junction.scenario import (
    DECISION_FIELDS,
    JOIN1_OPTIONS,
    build_lesson_thirteen_runner,
)
from data_science_arcade.lessons.l13_join_junction.scoring import CRITICAL_EVIDENCE_KEYS, LessonThirteenResult, score_lesson_thirteen
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.join_builder_scene import JoinBuilderScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

GOOD_DECISION = {
    "orders_join_type": "left",
    "orders_join_row_count": "120",
    "promotions_key_cardinality": "many_to_one_from_promotions",
    "promotions_join_needs_preaggregation": "preaggregate_first",
    "promotions_row_count_after_repair": "120",
    "validation_sufficiency": "no_needs_multiple_checks",
}
GOOD_MASTERY_SUPPORTING = ("shipment_has_multiple_real_checkpoints",)
GOOD_MASTERY_ROW_GROWTH_JUDGMENT = "expected_real_grain"


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _leaf_scene(scene):
    while isinstance(scene, OfferThenTaskScene):
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


def _play_comparison_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_join_builder(scene: JoinBuilderScene, choice_key: str) -> None:
    index = _option_index(scene.join_type_options, choice_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _fill_single_select(scene: BriefBuilderScene, field, option_key: str) -> None:
    scene.buttons.buttons[_option_index(field, option_key)].on_activate()
    scene.next_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict, evidence_ids: list[str] | None = None) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            ids = evidence_ids if evidence_ids is not None else list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.max_count]
            for item_id in ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_mastery_select(scene: BriefBuilderScene, supporting_keys: tuple[str, ...], row_growth_key: str) -> None:
    multi_field = scene.fields[0]
    for key in supporting_keys:
        scene.buttons.buttons[_option_index(multi_field, key)].on_activate()
    scene.next_button.on_activate()
    single_field = scene.fields[1]
    scene.buttons.buttons[_option_index(single_field, row_growth_key)].on_activate()
    scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    orders_key_interpretation="customer_id_repeats_in_orders",
    join1_choice="left",
    join1_consequence_interpretation="every_real_order_kept",
    join1_revision_engage: bool = False,
    revised_join1_choice=None,
    promotions_key_interpretation="promotions_key_is_one_to_many",
    fan_out_interpretation="key_matched_more_than_one_row",
    multi_check_interpretation="row_count_alone_insufficient",
    decision=GOOD_DECISION,
    evidence_ids=None,
    mastery_engage: bool = False,
    mastery_supporting=GOOD_MASTERY_SUPPORTING,
    mastery_row_growth_judgment=GOOD_MASTERY_ROW_GROWTH_JUDGMENT,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # orders_key_inspection
    _play_comparison_reveal(app.scenes.current.inner, orders_key_interpretation)

    assert isinstance(app.scenes.current.inner, JoinBuilderScene)  # join1_attempt
    _play_join_builder(app.scenes.current.inner, join1_choice)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # join1_consequence_reveal
    _play_comparison_reveal(app.scenes.current.inner, join1_consequence_interpretation)

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)  # join1_revision_offer
    if join1_revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, JoinBuilderScene)
        assert revised_join1_choice is not None
        _play_join_builder(leaf, revised_join1_choice)
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, DialogueScene)  # finance_promotions_ask
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # promotions_key_inspection
    _play_comparison_reveal(app.scenes.current.inner, promotions_key_interpretation)

    assert isinstance(app.scenes.current.inner, JoinBuilderScene)  # raw_promotions_attempt
    _play_join_builder(app.scenes.current.inner, "left_raw")

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # concrete_fan_out_example
    _play_comparison_reveal(app.scenes.current.inner, fan_out_interpretation)

    assert isinstance(app.scenes.current.inner, JoinBuilderScene)  # validate_reveal
    _play_join_builder(app.scenes.current.inner, "left_validated")

    assert isinstance(app.scenes.current.inner, JoinBuilderScene)  # repair_attempt
    _play_join_builder(app.scenes.current.inner, "left_repaired")

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # multi_check_validation_reveal
    _play_comparison_reveal(app.scenes.current.inner, multi_check_interpretation)

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision, evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()  # Engage
        select_scene = _leaf_scene(mastery_offer)
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_supporting, mastery_row_growth_judgment)
    else:
        mastery_offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_sixteen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_thirteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonThirteenResult)
        assert result.completed_thoughtfully() is True
        assert result.join1_first_choice == "left"
        assert result.join1_choice == "left"
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert set(result.critical_evidence_present) == set(CRITICAL_EVIDENCE_KEYS)
        assert result.mastery_engaged is True
        assert result.mastery_result == {
            "mastery_supporting_evidence": GOOD_MASTERY_SUPPORTING,
            "mastery_row_growth_judgment": GOOD_MASTERY_ROW_GROWTH_JUDGMENT,
        }
        assert collected is not None
    finally:
        pygame.quit()


def test_a_playthrough_that_skips_mastery_still_completes():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_thirteen_runner(app, on_finished=lambda result: finished_results.append(result))
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


def test_join1_revision_recovers_from_an_inner_pick_to_left():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_thirteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(
            app,
            join1_choice="inner",
            join1_consequence_interpretation="some_real_orders_dropped",
            join1_revision_engage=True,
            revised_join1_choice="left",
        )
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.join1_first_choice == "inner"
        assert result.join1_choice == "left"
        assert any(o.text_key == "lesson.l13.feedback.orders_join_type_recovered_via_revision" for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_declining_the_join1_revision_keeps_the_cold_pick():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_thirteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(
            app,
            join1_choice="inner",
            join1_consequence_interpretation="some_real_orders_dropped",
            join1_revision_engage=False,
        )
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.join1_first_choice == "inner"
        assert result.join1_choice == "inner"
        assert not any("recovered_via_revision" in o.text_key for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_evidence_is_available_after_a_wrong_initial_interpretation_at_every_no_revision_reveal():
    # Applying the L11-follow-up lesson proactively: orders_key,
    # promotions_key, fan_out, and multi_check have no revision path of
    # their own, so their evidence must be available regardless of which
    # interpretation was picked - never gated behind the correct one.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_thirteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(
            app,
            orders_key_interpretation="data_is_broken",
            promotions_key_interpretation="each_customer_has_one_promo",
            fan_out_interpretation="duplicate_row_should_be_removed",
            multi_check_interpretation="row_count_alone_sufficient",
        )
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert set(result.critical_evidence_present) == set(CRITICAL_EVIDENCE_KEYS)
    finally:
        pygame.quit()


def test_the_happy_path_python_mirror_executes_top_to_bottom_against_real_tables():
    # Regression for the exact class of bug the L12 follow-up in this same
    # project fixed: a substring check can't catch an unassigned variable
    # or a stale reference - this assembles the real happy-path
    # context.python_mirror() and actually executes it against a real
    # orders/customers/active_promotions namespace.
    app = _init_app()
    try:
        runner, collected = build_lesson_thirteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app)

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        mirror = restored_context.python_mirror()

        assert "join1_result = orders.merge(customers" in mirror
        assert "indicator=True" in mirror
        assert "validate='many_to_one'" in mirror
        assert "promo_per_customer = active_promotions.groupby(" in mirror
        assert "except pd.errors.MergeError" in mirror

        namespace: dict = {
            "orders": generate_orders().frame,
            "customers": generate_customers().frame,
            "active_promotions": generate_active_promotions().frame,
        }
        exec(mirror, namespace)

        assert len(namespace["join1_result"]) == 120
        assert len(namespace["final"]) == 120
        assert namespace["promo_per_customer"]["customer_id"].is_unique
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", DECISION_FIELDS)
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_every_join1_option_has_a_real_pandas_how_value():
    for option in JOIN1_OPTIONS:
        assert option.how in ("inner", "left", "outer")


def test_score_lesson_thirteen_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_thirteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        expected = score_lesson_thirteen(
            LessonThirteenResult(
                join1_first_choice="left",
                join1_choice="left",
                decision=dict(GOOD_DECISION, evidence=CRITICAL_EVIDENCE_KEYS),
                critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
            ),
            LESSON_13,
            hints_used=0,
        )
        assert set(feedback.evaluation.dimension_scores) == set(expected.dimension_scores)
        assert set(feedback.evaluation.dimension_scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE}
    finally:
        pygame.quit()
