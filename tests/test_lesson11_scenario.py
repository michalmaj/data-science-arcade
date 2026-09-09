import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l11_distribution_observatory.definition import LESSON_11
from data_science_arcade.lessons.l11_distribution_observatory.scenario import (
    BUSINESS_ASKS_FIELDS,
    DECISION_FIELDS,
    MASTERY_INTERPRETATION_FIELD,
    MASTERY_SUPPORTING_EVIDENCE_FIELD,
    build_lesson_eleven_runner,
)
from data_science_arcade.lessons.l11_distribution_observatory.scoring import CRITICAL_EVIDENCE_KEYS, LessonElevenResult, score_lesson_eleven
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.distribution_explorer_scene import DistributionExplorerScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

from lesson_test_helpers import click_through_mission_briefing

GOOD_PRIOR = {"finance_prior_pick": "mean", "product_prior_pick": "median", "ops_prior_pick": "p90"}
GOOD_DECISION = {
    "finance_summary_choice": "mean",
    "product_typical_order_claim": "median_with_limitation",
    "ops_capacity_summary": "p90",
    "shape_interpretation": "two_separate_populations",
    "communication_recommendation": "differentiated_summaries_per_audience",
}
GOOD_MASTERY_SUPPORTING = ("different_spread_or_std",)
GOOD_MASTERY_INTERPRETATION = "no_practically_different"
DECISION_FIELDS_IN_ORDER = DECISION_FIELDS
MASTERY_FIELDS_IN_ORDER = (MASTERY_SUPPORTING_EVIDENCE_FIELD, MASTERY_INTERPRETATION_FIELD)


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


def _play_mastery_select(scene: BriefBuilderScene, supporting_keys: tuple[str, ...], interpretation_key: str) -> None:
    multi_field = scene.fields[0]
    for key in supporting_keys:
        scene.buttons.buttons[_option_index(multi_field, key)].on_activate()
    scene.next_button.on_activate()
    single_field = scene.fields[1]
    scene.buttons.buttons[_option_index(single_field, interpretation_key)].on_activate()
    scene.next_button.on_activate()


def _play_comparison_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_distribution_explorer(scene: DistributionExplorerScene, *, marker_keys: tuple[str, ...] = (), interpret_key: str | None = None) -> None:
    for key in marker_keys:
        scene.marker_buttons[key].on_activate()
    if interpret_key is not None:
        scene.interpret_buttons[interpret_key].on_activate()
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


def _play_lesson_to_feedback(
    app,
    *,
    explore_interpretation="mean_falls_in_gap",
    capacity_interpretation="p90_is_the_boundary",
    prior=GOOD_PRIOR,
    shape_interpretation_choice="looks_like_two_populations",
    segment_interpretation_choice="segments_explain_mixture",
    revision_engage: bool = False,
    revised_prior=None,
    decision=GOOD_DECISION,
    evidence_ids=None,
    mastery_engage: bool = False,
    mastery_supporting=GOOD_MASTERY_SUPPORTING,
    mastery_interpretation=GOOD_MASTERY_INTERPRETATION,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, DistributionExplorerScene)  # distribution_explore
    _play_distribution_explorer(app.scenes.current.inner, marker_keys=("mean", "median"), interpret_key=explore_interpretation)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # capacity_check
    _play_comparison_reveal(app.scenes.current.inner, capacity_interpretation)

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # business_asks (prior)
    _play_brief_builder(app.scenes.current.inner, prior)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # shape_investigation
    _play_comparison_reveal(app.scenes.current.inner, shape_interpretation_choice)

    assert isinstance(app.scenes.current.inner, DistributionExplorerScene)  # segment_reveal
    _play_distribution_explorer(
        app.scenes.current.inner, marker_keys=("consumer_mean", "business_mean"), interpret_key=segment_interpretation_choice
    )

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)  # revision_offer
    if revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, BriefBuilderScene)
        assert revised_prior is not None
        _play_brief_builder(leaf, revised_prior)
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision, evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()  # Engage
        assert isinstance(mastery_offer._active, SequenceScene)
        mastery_offer._active.continue_button.on_activate()  # DistributionExplorerScene (no interpret gate) -> advance_to_second
        select_scene = mastery_offer._active._active
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_supporting, mastery_interpretation)
    else:
        mastery_offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_eleven_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_eleven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonElevenResult)
        assert result.completed_thoughtfully() is True
        assert result.business_asks_prior == GOOD_PRIOR
        assert set(result.decision) == {field.key for field in DECISION_FIELDS_IN_ORDER} | {"evidence"}
        assert result.segment_interpretation_seen == "segments_explain_mixture"
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
        runner, _ = build_lesson_eleven_runner(app, on_finished=lambda result: finished_results.append(result))
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


def test_declining_the_revision_offer_leaves_no_revised_picks_recorded():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_eleven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app, revision_engage=False)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        assert finished_results[0].business_asks_revised_picks is None
    finally:
        pygame.quit()


def test_engaging_the_revision_offer_records_the_real_picks_not_just_a_flag():
    # The revision offer's own real picks are what get recorded - never
    # just an engaged=True flag standing in for them (the P1 the user
    # reported: trajectory feedback was inferring "recovered via revision"
    # from prior vs. Final Decision alone, which could misattribute credit
    # to a revision that never actually fixed anything). The original
    # unscored prior pass stays untouched either way.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_eleven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        wrong_prior = {"finance_prior_pick": "median", "product_prior_pick": "mean", "ops_prior_pick": "mean"}
        feedback = _play_lesson_to_feedback(app, prior=wrong_prior, revision_engage=True, revised_prior=GOOD_PRIOR)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.business_asks_revised_picks == GOOD_PRIOR
        assert result.business_asks_prior == wrong_prior
    finally:
        pygame.quit()


def test_revision_offer_records_the_real_revised_picks_even_when_they_stay_wrong():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_eleven_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        wrong_prior = {"finance_prior_pick": "median", "product_prior_pick": "mean", "ops_prior_pick": "mean"}
        still_wrong_revision = {"finance_prior_pick": "p90", "product_prior_pick": "p90", "ops_prior_pick": "median"}
        feedback = _play_lesson_to_feedback(app, prior=wrong_prior, revision_engage=True, revised_prior=still_wrong_revision)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.business_asks_revised_picks == still_wrong_revision
        assert not any("recovered_via_revision" in o.text_key for o in feedback.evaluation.observations)
    finally:
        pygame.quit()


def test_a_wrong_prior_recovered_via_the_final_decision_produces_a_real_trajectory_observation():
    app = _init_app()
    try:
        runner, _ = build_lesson_eleven_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        wrong_prior = {"finance_prior_pick": "median", "product_prior_pick": "mean", "ops_prior_pick": "mean"}
        feedback = _play_lesson_to_feedback(app, prior=wrong_prior, revision_engage=True, revised_prior=GOOD_PRIOR)

        assert any(o.text_key == "lesson.l11.feedback.finance_recovered_via_revision" for o in feedback.evaluation.observations)
        assert feedback.evaluation.dimension_scores[ScoreDimension.METHOD] == 94.0
    finally:
        pygame.quit()


def test_the_player_facing_frame_never_leaks_the_segment_before_the_reveal():
    # Belt-and-suspenders on top of order_values.py's own construction
    # guarantee (no `segment` column exists anywhere): no AnalyticalAction
    # recorded before segment_reveal ever mentions the word "segment" in
    # its own python_code.
    app = _init_app()
    try:
        runner, collected = build_lesson_eleven_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_distribution_explorer(app.scenes.current.inner, marker_keys=("mean", "median"), interpret_key="mean_falls_in_gap")
        _play_comparison_reveal(app.scenes.current.inner, "p90_is_the_boundary")
        _play_brief_builder(app.scenes.current.inner, GOOD_PRIOR)
        _play_comparison_reveal(app.scenes.current.inner, "looks_like_two_populations")

        context_data = collected["analytical_context"]
        for action in context_data["actions"]:
            code = action.get("python_code") or ""
            assert "segment" not in code
    finally:
        pygame.quit()


def test_segment_reveal_records_a_real_join_before_any_segment_filtering():
    # P0: the player-facing `orders` frame never carries a `segment`
    # column before this stage - the recorded Python Mirror action must
    # show the real join/validate that brings one into scope, in order,
    # before any orders['segment'] filtering line, so the mirror stays
    # executable/logically readable top to bottom instead of jumping
    # straight to a column nothing ever created.
    app = _init_app()
    try:
        runner, collected = build_lesson_eleven_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_distribution_explorer(app.scenes.current.inner, marker_keys=("mean", "median"), interpret_key="mean_falls_in_gap")
        _play_comparison_reveal(app.scenes.current.inner, "p90_is_the_boundary")
        _play_brief_builder(app.scenes.current.inner, GOOD_PRIOR)
        _play_comparison_reveal(app.scenes.current.inner, "looks_like_two_populations")

        assert isinstance(app.scenes.current.inner, DistributionExplorerScene)  # segment_reveal
        _play_distribution_explorer(
            app.scenes.current.inner, marker_keys=("consumer_mean", "business_mean"), interpret_key="segments_explain_mixture"
        )

        actions = collected["analytical_context"]["actions"]
        segment_reveal_action = next(a for a in actions if a["python_code"] and "segment" in a["python_code"])
        code = segment_reveal_action["python_code"]
        merge_index = code.index("merge")
        validate_index = code.index("validate")
        filter_index = code.index("orders['segment']")
        assert merge_index < filter_index
        assert validate_index < filter_index
    finally:
        pygame.quit()


def test_a_wrong_initial_interpretation_still_leaves_its_fact_available_as_evidence():
    # P0: seeing a real, computed fact (the mean's position, the p90
    # boundary, the IQR width, the segment split) must not require having
    # correctly interpreted it on the spot - there's no revision path for
    # these four reveals (only business_asks gets one), so gating Evidence
    # on the correct interpretation would permanently punish a wrong first
    # read. Every interpretation picked here is deliberately the WRONG one
    # at its own stage.
    app = _init_app()
    try:
        runner, collected = build_lesson_eleven_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            explore_interpretation="mean_looks_representative",
            capacity_interpretation="use_the_maximum_instead",
            shape_interpretation_choice="one_population_with_outliers",
            segment_interpretation_choice="segments_dont_matter",
        )
        assert isinstance(feedback, LessonFeedbackScene)
        assert feedback.evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 97.0
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", [*BUSINESS_ASKS_FIELDS, *DECISION_FIELDS_IN_ORDER, *MASTERY_FIELDS_IN_ORDER])
def test_every_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_score_lesson_eleven_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_eleven_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        expected = score_lesson_eleven(
            LessonElevenResult(
                business_asks_prior=GOOD_PRIOR,
                decision=dict(GOOD_DECISION, evidence=CRITICAL_EVIDENCE_KEYS),
                segment_interpretation_seen="segments_explain_mixture",
                critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
            ),
            LESSON_11,
            hints_used=0,
        )
        assert set(feedback.evaluation.dimension_scores) == set(expected.dimension_scores)
    finally:
        pygame.quit()
