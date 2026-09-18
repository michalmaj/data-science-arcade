import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l29_the_executive_brief.findings import CORRECT_FINDING_KEYS, FINDINGS_POOL, ON_TOPIC_FINDING_KEYS
from data_science_arcade.lessons.l29_the_executive_brief.scenario import (
    DECISION_EVIDENCE_FIELD,
    DECISION_FIELDS,
    build_lesson_twenty_nine_runner,
)
from data_science_arcade.lessons.l29_the_executive_brief.scoring import LessonTwentyNineResult
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.finding_picker_scene import FindingPickerScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

from lesson_test_helpers import click_through_mission_briefing

_CORRECT_DECISION = {
    "lead_finding": "checkout_completion",
    "supporting_chart": "checkout_completion_over_time",
    "confidence_level": "high_sustained_with_consistent_evidence",
    "recommendation": "keep_and_monitor_returns",
    "caveats": "competitor_redesigned_too",
}


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _shortlist_the_on_topic_five(scene: FindingPickerScene) -> None:
    for _ in range(5):
        remaining = scene._remaining_findings()
        index = next(i for i, finding in enumerate(remaining) if finding.key in ON_TOPIC_FINDING_KEYS)
        scene.buttons.buttons[index].on_activate()


def _shortlist_wrong_finding_instead_of(scene: FindingPickerScene, missing_correct_key: str) -> None:
    """Picks 5 findings that include every on-topic finding EXCEPT
    `missing_correct_key`, substituting one dramatic-but-unrelated one -
    used by the independence regression for a wrong shortlist."""
    target = (ON_TOPIC_FINDING_KEYS - {missing_correct_key}) | ({"social_mentions", "stock_price", "employee_satisfaction"} - ON_TOPIC_FINDING_KEYS)
    picked = 0
    while picked < 5:
        remaining = scene._remaining_findings()
        index = next(i for i, finding in enumerate(remaining) if finding.key in target)
        scene.buttons.buttons[index].on_activate()
        picked += 1


def _cite_findings(scene: DecisionBuilderScene, finding_keys: set[str]) -> None:
    label_to_key = {finding.label_key: finding.key for finding in FINDINGS_POOL}
    for item in scene.context.evidence:
        key = label_to_key.get(item.label_key)
        if key in finding_keys:
            scene._evidence_toggle_buttons[item.id].on_activate()


def _cite_the_headline_three(scene: DecisionBuilderScene) -> None:
    _cite_findings(scene, CORRECT_FINDING_KEYS)


def _pick_option(scene: DecisionBuilderScene, option_key: str) -> None:
    step = scene._current_step()
    index = next(i for i, option in enumerate(step.options) if option.key == option_key)
    scene.buttons.buttons[index].on_activate()


def _fill_out_decision(scene: DecisionBuilderScene, decision: dict) -> None:
    for step in scene._steps:
        if scene._is_evidence_step(step):
            _cite_the_headline_three(scene)
        else:
            _pick_option(scene, decision[step.key])
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_all_seven_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_nine_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, FindingPickerScene)  # finding_shortlist
        assert app.scenes.current.inner.guided is False
        _shortlist_the_on_topic_five(app.scenes.current.inner)

        assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision_brief
        _fill_out_decision(app.scenes.current.inner, _CORRECT_DECISION)

        assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # mastery_challenge - skipped
        app.scenes.current.inner.buttons.buttons[1].on_activate()

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)  # feedback
        app.scenes.current.inner.buttons.buttons[0].on_activate()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonTwentyNineResult)
        assert result.completed_thoughtfully() is True
        assert set(result.shortlist_choices) == ON_TOPIC_FINDING_KEYS
        assert result.cited_finding_keys == CORRECT_FINDING_KEYS
        assert set(result.decision) >= {field.key for field in DECISION_FIELDS}
        assert collected["decision"] == result.decision
    finally:
        pygame.quit()


def test_evidence_pool_after_shortlist_is_exactly_the_five_picked_findings():
    """P0 regression: FindingPickerScene has no Back/undo, so exactly
    SHORTLIST_TARGET_COUNT items are ever recorded - context.evidence must
    contain exactly those 5, never more, never a stale/historical set."""
    app = _init_app()
    try:
        runner, collected = build_lesson_twenty_nine_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation

        _shortlist_the_on_topic_five(app.scenes.current.inner)

        assert len(collected["analytical_context"]["evidence"]) == 5
        cited_labels = {item["label_key"] for item in collected["analytical_context"]["evidence"]}
        expected_labels = {finding.label_key for finding in FINDINGS_POOL if finding.key in ON_TOPIC_FINDING_KEYS}
        assert cited_labels == expected_labels
    finally:
        pygame.quit()


def test_supporting_chart_is_scored_against_the_students_own_lead_not_a_fixed_key():
    """Conflict 3's fix: a student who picks a DIFFERENT (wrong) lead but a
    chart that matches THAT lead should still pass the chart-consistency
    check - proven by playing through with payment_step_abandonment as the
    (wrong) lead and its own matching chart, and confirming COMMUNICATION
    reflects a mismatch only against `lead_finding`'s own correctness, not
    the chart pick."""
    from data_science_arcade.lessons.framework.definition import ScoreDimension
    from data_science_arcade.lessons.l29_the_executive_brief.definition import LESSON_29
    from data_science_arcade.lessons.l29_the_executive_brief.scoring import score_lesson_twenty_nine

    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_twenty_nine_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)
        _play_dialogue_to_the_end(app.scenes.current)
        _shortlist_the_on_topic_five(app.scenes.current.inner)

        decision = dict(_CORRECT_DECISION)
        decision["lead_finding"] = "payment_step_abandonment"
        decision["supporting_chart"] = "payment_step_abandonment_over_time"
        _fill_out_decision(app.scenes.current.inner, decision)

        app.scenes.current.inner.buttons.buttons[1].on_activate()  # mastery - skipped
        app.scenes.current.inner.buttons.buttons[0].on_activate()  # feedback ack
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        result = finished_results[0]
        evaluation = score_lesson_twenty_nine(result, LESSON_29, hints_used=0)
        # lead wrong (1 of 3 communication checks fails), chart still matches own lead, caveat correct -> 2 of 3
        assert evaluation.dimension_scores[ScoreDimension.COMMUNICATION] == 65.0
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


def test_evidence_field_requires_exactly_three():
    assert DECISION_EVIDENCE_FIELD.min_count == DECISION_EVIDENCE_FIELD.max_count == 3
