import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l12_groupby_kitchen.definition import LESSON_12
from data_science_arcade.lessons.l12_groupby_kitchen.scenario import (
    DECISION_FIELDS,
    METRIC_SLOTS,
    NETWORK_ROLLUP_FIELDS,
    build_lesson_twelve_runner,
)
from data_science_arcade.lessons.l12_groupby_kitchen.scoring import CRITICAL_EVIDENCE_KEYS, LessonTwelveResult, score_lesson_twelve
from data_science_arcade.ui.aggregation_builder_scene import AggregationBuilderScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

from lesson_test_helpers import click_through_mission_briefing

GOOD_GROUP_BY = "by_store"
GOOD_METRIC_CHOICES = {
    "orders": "count_order_id",
    "revenue": "sum_revenue",
    "unique_customers": "nunique_customer_id",
    "aov": "mean_revenue",
}
GOOD_ROLLUP = {"network_customer_method": "distinct_network_wide", "network_aov_method": "order_level_or_weighted"}
GOOD_DECISION = {
    "raw_observation_unit": "order",
    "grouped_output_grain": "store",
    "safe_rollup_metrics": ("orders", "revenue"),
    "network_customer_method": "distinct_network_wide",
    "network_aov_method": "order_level_or_weighted",
}
GOOD_MASTERY_SUPPORTING = ("channel_volumes_differ",)
GOOD_MASTERY_INTERPRETATION = "network_avg_needs_weighting"


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


def _play_brief_builder(scene: BriefBuilderScene, choices: dict[str, str]) -> None:
    for step in scene.fields:
        _fill_single_select(scene, step, choices[step.key])


def _play_comparison_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_aggregation_builder(scene: AggregationBuilderScene, *, group_by: str, metric_choices: dict[str, str]) -> None:
    index = _option_index(scene.group_by_options, group_by)
    scene.buttons.buttons[index].on_activate()
    scene.next_button.on_activate()
    for slot in scene.metric_slots:
        index = _option_index(slot.options, metric_choices[slot.key])
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict, evidence_ids: list[str] | None = None) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            ids = evidence_ids if evidence_ids is not None else list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.max_count]
            for item_id in ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        elif step.key == "safe_rollup_metrics":
            for option_key in decision_keys[step.key]:
                scene.buttons.buttons[_option_index(step, option_key)].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_mastery_select(scene: BriefBuilderScene, supporting_keys: tuple[str, ...], interpretation_key: str) -> None:
    multi_field = scene.fields[0]
    for key in supporting_keys:
        scene.buttons.buttons[_option_index(multi_field, key)].on_activate()
    scene.next_button.on_activate()
    single_field = scene.fields[1]
    scene.buttons.buttons[_option_index(single_field, interpretation_key)].on_activate()
    scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    group_by=GOOD_GROUP_BY,
    metric_choices=GOOD_METRIC_CHOICES,
    grain_check_interpretation="one_store",
    customer_count_interpretation="repeats_mean_fewer_real_customers",
    store_summary_revision_engage: bool = False,
    revised_group_by=None,
    revised_metric_choices=None,
    rollup_prior=GOOD_ROLLUP,
    customer_rollup_interpretation="overlap_breaks_the_sum",
    aov_rollup_interpretation="volumes_break_the_unweighted_mean",
    rollup_revision_engage: bool = False,
    revised_rollup=None,
    decision=GOOD_DECISION,
    evidence_ids=None,
    mastery_engage: bool = False,
    mastery_supporting=GOOD_MASTERY_SUPPORTING,
    mastery_interpretation=GOOD_MASTERY_INTERPRETATION,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, AggregationBuilderScene)  # store_summary_build
    _play_aggregation_builder(app.scenes.current.inner, group_by=group_by, metric_choices=metric_choices)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # output_grain_check
    _play_comparison_reveal(app.scenes.current.inner, grain_check_interpretation)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # customer_count_reveal
    _play_comparison_reveal(app.scenes.current.inner, customer_count_interpretation)

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)  # store_summary_revision_offer
    if store_summary_revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, AggregationBuilderScene)
        assert revised_group_by is not None and revised_metric_choices is not None
        _play_aggregation_builder(leaf, group_by=revised_group_by, metric_choices=revised_metric_choices)
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, DialogueScene)  # finance_rollup_ask
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # network_rollup_attempt (prior)
    _play_brief_builder(app.scenes.current.inner, rollup_prior)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # customer_rollup_reveal
    _play_comparison_reveal(app.scenes.current.inner, customer_rollup_interpretation)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # aov_rollup_reveal
    _play_comparison_reveal(app.scenes.current.inner, aov_rollup_interpretation)

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)  # rollup_revision_offer
    if rollup_revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, BriefBuilderScene)
        assert revised_rollup is not None
        _play_brief_builder(leaf, revised_rollup)
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
        _play_mastery_select(select_scene, mastery_supporting, mastery_interpretation)
    else:
        mastery_offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_fourteen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twelve_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwelveResult)
        assert result.completed_thoughtfully() is True
        assert result.group_by == GOOD_GROUP_BY
        assert result.metric_choices == GOOD_METRIC_CHOICES
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert set(result.critical_evidence_present) == set(CRITICAL_EVIDENCE_KEYS)
        assert result.mastery_engaged is True
        assert result.mastery_result == {
            "mastery_supporting_evidence": GOOD_MASTERY_SUPPORTING,
            "mastery_interpretation": GOOD_MASTERY_INTERPRETATION,
        }
        assert collected is not None
    finally:
        pygame.quit()


def test_a_playthrough_that_skips_mastery_still_completes():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_twelve_runner(app, on_finished=lambda result: finished_results.append(result))
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


def test_the_store_summary_revision_offer_can_fix_a_fact_other_than_unique_customers():
    # P0 fix: the revision path must cover ALL 5 pipeline facts (group
    # key, and all 4 metric slots), not just the unique_customers S02
    # trap - here the FIRST pass gets the `aov` slot wrong and the
    # revision fixes only that.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_twelve_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        wrong_metrics = dict(GOOD_METRIC_CHOICES, aov="sum_revenue_as_aov")
        feedback = _play_lesson_to_feedback(
            app,
            metric_choices=wrong_metrics,
            store_summary_revision_engage=True,
            revised_group_by=GOOD_GROUP_BY,
            revised_metric_choices=GOOD_METRIC_CHOICES,
        )
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.metric_choices == GOOD_METRIC_CHOICES
        assert feedback.evaluation.dimension_scores[ScoreDimension.METHOD] == 96.0
    finally:
        pygame.quit()


def test_declining_the_store_summary_revision_keeps_the_first_pass():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_twelve_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        wrong_metrics = dict(GOOD_METRIC_CHOICES, unique_customers="count_order_id_as_customers")
        feedback = _play_lesson_to_feedback(app, metric_choices=wrong_metrics, store_summary_revision_engage=False)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.metric_choices == wrong_metrics
        assert feedback.evaluation.dimension_scores[ScoreDimension.METHOD] < 96.0
    finally:
        pygame.quit()


def test_output_grain_evidence_updates_in_place_after_a_group_by_revision():
    # Guardrail 6: output_grain_role's evidence must update to the FINAL
    # state (never leave two contradictory items) once the revision
    # actually changes the group key.
    app = _init_app()
    try:
        runner, collected = build_lesson_twelve_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(
            app,
            group_by="by_customer",
            grain_check_interpretation="one_customer",
            store_summary_revision_engage=True,
            revised_group_by=GOOD_GROUP_BY,
            revised_metric_choices=GOOD_METRIC_CHOICES,
        )
        context_data = collected["analytical_context"]
        grain_evidence = [e for e in context_data["evidence"] if e["key"] == "output_grain_role"]
        assert len(grain_evidence) == 1
        assert "store_id" in grain_evidence[0]["detail"]
        assert "customer_id" not in grain_evidence[0]["detail"]
    finally:
        pygame.quit()


def test_a_wrong_initial_interpretation_still_leaves_its_fact_available_as_evidence():
    app = _init_app()
    try:
        runner, _ = build_lesson_twelve_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            grain_check_interpretation="one_date",
            customer_count_interpretation="row_count_is_fine",
            customer_rollup_interpretation="sum_is_still_fine",
            aov_rollup_interpretation="unweighted_mean_is_fine",
        )
        assert feedback.evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 97.0
    finally:
        pygame.quit()


def test_declining_the_rollup_revision_leaves_no_revised_picks_recorded():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_twelve_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app, rollup_revision_engage=False)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        assert finished_results[0].rollup_revised_picks is None
    finally:
        pygame.quit()


def test_rollup_revision_records_the_real_revised_picks_not_a_bare_flag():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_twelve_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        wrong_prior = {"network_customer_method": "sum_per_store", "network_aov_method": "mean_of_store_aovs"}
        feedback = _play_lesson_to_feedback(app, rollup_prior=wrong_prior, rollup_revision_engage=True, revised_rollup=GOOD_ROLLUP)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.rollup_prior == wrong_prior
        assert result.rollup_revised_picks == GOOD_ROLLUP
        assert any(o.text_key == "lesson.l12.feedback.customer_method_recovered_via_revision" for o in feedback.evaluation.observations)
        assert any(o.text_key == "lesson.l12.feedback.aov_method_recovered_via_revision" for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_rollup_revision_that_stays_wrong_never_produces_false_trajectory_credit():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_twelve_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        wrong_prior = {"network_customer_method": "sum_per_store", "network_aov_method": "mean_of_store_aovs"}
        still_wrong = {"network_customer_method": "sum_per_store", "network_aov_method": "mean_of_store_aovs"}
        feedback = _play_lesson_to_feedback(
            app,
            rollup_prior=wrong_prior,
            rollup_revision_engage=True,
            revised_rollup=still_wrong,
            decision=dict(GOOD_DECISION, network_customer_method="distinct_network_wide", network_aov_method="order_level_or_weighted"),
        )
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.rollup_revised_picks == still_wrong
        assert not any("recovered_via_revision" in o.text_key for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_a_wrong_pipeline_can_still_earn_reasoning_credit_for_the_normative_grain():
    # Guardrail 5: a student stuck with a wrong (customer-level) pipeline
    # can still honestly claim what the REQUESTED table's grain should
    # have been - METHOD stays low, REASONING's grain check is unaffected.
    app = _init_app()
    try:
        runner, _ = build_lesson_twelve_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app, group_by="by_customer", grain_check_interpretation="one_customer", store_summary_revision_engage=False)

        assert feedback.evaluation.dimension_scores[ScoreDimension.METHOD] < 96.0
        assert feedback.evaluation.dimension_scores[ScoreDimension.REASONING] == 93.0
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", [*DECISION_FIELDS, *NETWORK_ROLLUP_FIELDS])
def test_every_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_every_metric_slot_has_at_least_two_options():
    for slot in METRIC_SLOTS:
        assert len(slot.options) >= 2


def test_score_lesson_twelve_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_twelve_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        expected = score_lesson_twelve(
            LessonTwelveResult(
                group_by=GOOD_GROUP_BY,
                metric_choices=GOOD_METRIC_CHOICES,
                decision=dict(GOOD_DECISION, evidence=CRITICAL_EVIDENCE_KEYS),
                critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
            ),
            LESSON_12,
            hints_used=0,
        )
        assert set(feedback.evaluation.dimension_scores) == set(expected.dimension_scores)
    finally:
        pygame.quit()
