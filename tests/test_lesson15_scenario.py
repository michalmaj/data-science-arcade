import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l15_segment_detective.scenario import DECISION_FIELDS, build_lesson_fifteen_runner
from data_science_arcade.lessons.l15_segment_detective.scoring import CRITICAL_EVIDENCE_KEYS, LessonFifteenResult
from data_science_arcade.lessons.l15_segment_detective.sessions import generate_sessions
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.segment_mix_scene import SegmentMixScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

GOOD_DECISION = {
    "observed_overall_result": "rose_28_4_to_33_2",
    "within_device_result": "both_declined",
    "statements_relationship": "both_true_different_comparisons",
    "what_explains_the_reversal": "mix_shifted_toward_higher_converting_group",
    "standardized_interpretation": "no_within_device_gain_at_fixed_mix",
    "strongest_defensible_claim": "names_both_facts_respects_causal_boundary",
}
GOOD_MASTERY_SUPPORTING = ("both_carriers_improved",)
GOOD_MASTERY_JUDGMENT = "no_reversal_real_improvement"


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


def _play_segment_mix(scene: SegmentMixScene, dimension_key: str | None = None) -> None:
    if dimension_key is not None:
        index = _option_index(scene.dimension_options, dimension_key)
        scene.buttons.buttons[index].on_activate()
    scene.finish_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict, evidence_ids: list[str] | None = None) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            ids = evidence_ids if evidence_ids is not None else list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.max_count]
            for item_id in ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_mastery_select(scene: BriefBuilderScene, supporting_keys: tuple[str, ...], judgment_key: str) -> None:
    multi_field = scene.fields[0]
    for key in supporting_keys:
        scene.buttons.buttons[_option_index(multi_field, key)].on_activate()
    scene.next_button.on_activate()
    single_field = scene.fields[1]
    scene.buttons.buttons[_option_index(single_field, judgment_key)].on_activate()
    scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    prior_headline_interpretation="need_to_check_composition_first",
    first_dimension="device",
    region_engage: bool = True,
    region_interpretation="region_tracks_aggregate_doesnt_explain",
    device_interpretation="device_explains_the_reversal",
    weighted_interpretation="aggregate_is_weighted_blend",
    standardized_interpretation="q2_rates_at_q1_mix_no_gain",
    revised_headline="overall_up_within_device_down",
    decision=GOOD_DECISION,
    evidence_ids=None,
    mastery_engage: bool = False,
    mastery_supporting=GOOD_MASTERY_SUPPORTING,
    mastery_judgment=GOOD_MASTERY_JUDGMENT,
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # overall_reveal
    _play_comparison_reveal(app.scenes.current.inner, prior_headline_interpretation)

    picker = _leaf_scene(app.scenes.current.inner)
    assert isinstance(picker, SegmentMixScene)  # dimension_investigation picker
    _play_segment_mix(picker, first_dimension)

    if first_dimension == "region":
        null_reveal = _leaf_scene(app.scenes.current.inner)
        assert isinstance(null_reveal, ComparisonRevealScene)
        _play_comparison_reveal(null_reveal, region_interpretation)

        device_mix = _leaf_scene(app.scenes.current.inner)
        assert isinstance(device_mix, SegmentMixScene)  # mandatory device follow-up
        _play_segment_mix(device_mix)

        device_reveal = _leaf_scene(app.scenes.current.inner)
        assert isinstance(device_reveal, ComparisonRevealScene)
        _play_comparison_reveal(device_reveal, device_interpretation)
    else:
        device_reveal = _leaf_scene(app.scenes.current.inner)
        assert isinstance(device_reveal, ComparisonRevealScene)
        _play_comparison_reveal(device_reveal, device_interpretation)

        offer = _leaf_scene(app.scenes.current.inner)
        assert isinstance(offer, OfferThenTaskScene)  # optional region offer
        if region_engage:
            offer.buttons.buttons[0].on_activate()
            region_mix = _leaf_scene(offer)
            assert isinstance(region_mix, SegmentMixScene)
            _play_segment_mix(region_mix)

            null_reveal = _leaf_scene(offer)
            assert isinstance(null_reveal, ComparisonRevealScene)
            _play_comparison_reveal(null_reveal, region_interpretation)
        else:
            offer.buttons.buttons[1].on_activate()

    weighted = app.scenes.current.inner
    assert isinstance(weighted, ComparisonRevealScene)  # weighted_reconstruction_reveal
    _play_comparison_reveal(weighted, weighted_interpretation)

    standardized = app.scenes.current.inner
    assert isinstance(standardized, ComparisonRevealScene)  # standardized_comparison_reveal
    _play_comparison_reveal(standardized, standardized_interpretation)

    revision = app.scenes.current.inner
    assert isinstance(revision, BriefBuilderScene)  # headline_revision
    revision.buttons.buttons[_option_index(revision.fields[0], revised_headline)].on_activate()
    revision.next_button.on_activate()

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision, evidence_ids=evidence_ids)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()
        select_scene = _leaf_scene(mastery_offer)
        assert isinstance(select_scene, BriefBuilderScene)
        _play_mastery_select(select_scene, mastery_supporting, mastery_judgment)
    else:
        mastery_offer.buttons.buttons[1].on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_ten_stages_region_first():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_fifteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, first_dimension="region", mastery_engage=True)
        feedback.on_complete()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonFifteenResult)
        assert result.completed_thoughtfully() is True
        assert result.first_dimension == "region"
        assert result.region_inspected is True
        assert result.prior_headline == "need_to_check_composition_first"
        assert result.revised_headline == "overall_up_within_device_down"
        assert set(result.decision) == {field.key for field in DECISION_FIELDS} | {"evidence"}
        assert set(result.critical_evidence_present) == set(CRITICAL_EVIDENCE_KEYS)
        assert result.mastery_engaged is True
        assert result.mastery_result == {
            "mastery_supporting_evidence": GOOD_MASTERY_SUPPORTING,
            "mastery_reversal_judgment": GOOD_MASTERY_JUDGMENT,
        }
        assert collected is not None
    finally:
        pygame.quit()


def test_the_full_lesson_plays_through_device_first_declining_region():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_fifteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, first_dimension="device", region_engage=False, mastery_engage=False)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.first_dimension == "device"
        assert result.region_inspected is False
        assert result.mastery_engaged is False
        assert result.mastery_result == {}
        # Central roles are all still present even without region - EVIDENCE
        # is never gated on the optional bonus fact.
        assert set(result.critical_evidence_present) == set(CRITICAL_EVIDENCE_KEYS)
    finally:
        pygame.quit()


def test_device_first_with_optional_region_engaged_marks_region_inspected():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_fifteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(app, first_dimension="device", region_engage=True)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.first_dimension == "device"
        assert result.region_inspected is True
    finally:
        pygame.quit()


def test_headline_revision_is_a_real_separate_pick_from_the_prior_one():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_fifteen_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        feedback = _play_lesson_to_feedback(
            app,
            prior_headline_interpretation="conversion_improved",
            revised_headline="overall_up_within_device_down",
        )
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.prior_headline == "conversion_improved"
        assert result.revised_headline == "overall_up_within_device_down"
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", DECISION_FIELDS)
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_evidence_is_available_after_a_wrong_interpretation_at_every_reveal():
    app = _init_app()
    try:
        runner, collected = build_lesson_fifteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(
            app,
            first_dimension="region",
            region_interpretation="region_explains_the_reversal",
            device_interpretation="device_doesnt_explain_anything",
            weighted_interpretation="aggregate_is_a_separate_number",
            standardized_interpretation="proves_product_regressed",
        )

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        evidence_label_keys = {item.label_key for item in restored_context.evidence}
        assert "lesson.l15.evidence.overall_change" in evidence_label_keys
        assert "lesson.l15.evidence.device_rates" in evidence_label_keys
        assert "lesson.l15.evidence.device_share" in evidence_label_keys
        assert "lesson.l15.evidence.standardized_comparison" in evidence_label_keys
        assert "lesson.l15.evidence.region_null" in evidence_label_keys
        assert "lesson.l15.evidence.weighted_reconstruction" in evidence_label_keys
    finally:
        pygame.quit()


def test_the_happy_path_python_mirror_executes_top_to_bottom_against_real_sessions():
    app = _init_app()
    try:
        runner, collected = build_lesson_fifteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, first_dimension="region")

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        mirror = restored_context.python_mirror()

        assert "overall = sessions.groupby('period')['converted'].mean()" in mirror
        assert "region_rates = " in mirror
        assert "device_rates = " in mirror
        assert "device_mix = " in mirror
        assert "reconstructed = " in mirror
        assert "q2_at_q1_mix = " in mirror

        namespace: dict = {"sessions": generate_sessions().frame, "pd": __import__("pandas")}
        exec(mirror, namespace)

        assert round(float(namespace["overall"]["Q1"]) * 100, 1) == 28.4
        assert round(float(namespace["overall"]["Q2"]) * 100, 1) == 33.2
        assert round(float(namespace["q2_at_q1_mix"]) * 100, 1) == 25.2
        assert round(float(namespace["reconstructed"]["Q1"]) * 100, 1) == 28.4
        assert round(float(namespace["reconstructed"]["Q2"]) * 100, 1) == 33.2
    finally:
        pygame.quit()


def test_device_first_mirror_never_references_region_rates_when_region_skipped():
    # Regression: SegmentMixScene used to key its own Mirror action by a
    # fixed, shared string regardless of which dimension it showed - a
    # later dimension's own action would silently overwrite an earlier
    # dimension's real groupby definition in place. Confirms the fix:
    # skipping region means region_rates is never defined at all, and
    # nothing downstream references it.
    app = _init_app()
    try:
        runner, collected = build_lesson_fifteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, first_dimension="device", region_engage=False)

        restored_context = LessonContext()
        restored_context.restore_from_dict(collected["analytical_context"])
        mirror = restored_context.python_mirror()

        assert "region_rates" not in mirror
        assert "device_rates = " in mirror

        namespace: dict = {"sessions": generate_sessions().frame, "pd": __import__("pandas")}
        exec(mirror, namespace)
        assert "device_rates" in namespace
    finally:
        pygame.quit()


def test_score_lesson_fifteen_is_wired_as_the_lessons_own_scorer():
    app = _init_app()
    try:
        runner, _ = build_lesson_fifteen_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(app)
        assert feedback.evaluation is not None
    finally:
        pygame.quit()
