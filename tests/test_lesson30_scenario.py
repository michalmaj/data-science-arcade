import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l30_the_data_incident.leads import MINIMUM_LEADS_REQUIRED
from data_science_arcade.lessons.l30_the_data_incident.scenario import DECISION_FIELDS, build_lesson_thirty_runner
from data_science_arcade.lessons.l30_the_data_incident.scoring import LessonThirtyResult
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.composite_scene import SequenceScene
from data_science_arcade.ui.correlation_scene import CorrelationScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.investigation_hub_scene import InvestigationHubScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene

from lesson_test_helpers import click_through_mission_briefing

# Lead order matches build_investigation_leads' own return tuple.
_LEAD_KEYS_IN_ORDER = (
    "regional_breakdown",
    "promo_correlation",
    "redesign_correlation",
    "checkout_health_check",
    "monitoring_review",
    "dashboard_chart",
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _complete_correlation_lead(scene: CorrelationScene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.next_button.on_activate()


def _complete_chart_lead(scene: ChartDesignerScene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.next_button.on_activate()


def _complete_segment_lead(scene: SegmentSlicerScene, request_count: int) -> None:
    for _ in range(request_count):
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def _complete_alert_lead(scene: AlertConfigScene) -> None:
    scene.buttons.buttons[0].on_activate()  # metric
    scene.buttons.buttons[len(scene._current_request().metric_options)].on_activate()  # threshold
    scene.next_button.on_activate()


def _complete_promo_lead(scene: SequenceScene) -> None:
    assert isinstance(scene._active, BriefBuilderScene)
    scene.buttons.buttons[0].on_activate()  # dedup choice
    scene.next_button.on_activate()  # advances to the CorrelationScene
    assert isinstance(scene._active, CorrelationScene)
    scene.buttons.buttons[0].on_activate()  # verdict
    scene.next_button.on_activate()


def _investigate_lead(app, hub: InvestigationHubScene, index: int) -> None:
    key = hub.leads[index].key
    hub.buttons.buttons[index].on_activate()
    lead_scene = app.scenes.current.inner
    if key == "regional_breakdown":
        _complete_segment_lead(lead_scene, request_count=2)
    elif key == "promo_correlation":
        _complete_promo_lead(lead_scene)
    elif key == "redesign_correlation":
        _complete_correlation_lead(lead_scene)
    elif key == "checkout_health_check":
        _complete_segment_lead(lead_scene, request_count=1)
    elif key == "monitoring_review":
        _complete_alert_lead(lead_scene)
    elif key == "dashboard_chart":
        _complete_chart_lead(lead_scene)
    else:
        raise AssertionError(f"unhandled lead key: {key}")


def _fill_out_decision(scene: DecisionBuilderScene) -> None:
    # 7 real steps: what_happened, supporting_evidence (EvidenceField),
    # then 5 more BriefField/MultiChoiceField steps - one click each
    # satisfies every one of them (MultiChoiceField's min_count is 1).
    for _ in range(7):
        step = scene._current_step()
        if step.key == "supporting_evidence":
            evidence_ids = list(scene._evidence_toggle_buttons.keys())
            scene._evidence_toggle_buttons[evidence_ids[0]].on_activate()
        else:
            scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_to_a_result_investigating_exactly_the_minimum():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_thirty_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing (merged, single stage)
        _play_dialogue_to_the_end(app.scenes.current)

        hub = app.scenes.current.inner
        assert isinstance(hub, InvestigationHubScene)
        assert len(hub.leads) == 6
        assert {lead.key for lead in hub.leads} == set(_LEAD_KEYS_IN_ORDER)

        for index in range(MINIMUM_LEADS_REQUIRED):
            _investigate_lead(app, hub, index)
            assert app.scenes.current.inner is hub

        assert len(hub.investigated) == MINIMUM_LEADS_REQUIRED
        assert hub.conclude_button.enabled
        hub.conclude_button.on_activate()

        assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # no Twist stage
        _fill_out_decision(app.scenes.current)

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)  # feedback
        app.scenes.current.inner.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonThirtyResult)
        assert result.completed_thoughtfully() is True
        assert len(result.leads_investigated) == MINIMUM_LEADS_REQUIRED
        assert set(result.decision) == {"what_happened", "supporting_evidence", "root_cause_confidence", "remaining_uncertainties", "business_impact", "recommended_action", "follow_up_measurement"}
        assert len(result.gathered_evidence) > 0
        assert collected["result"] is result
    finally:
        pygame.quit()


def test_investigating_every_lead_still_completes_thoughtfully_and_records_evidence_for_each():
    app = _init_app()
    try:
        finished_results = []
        runner, _collected = build_lesson_thirty_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)

        hub = app.scenes.current.inner
        for index in range(len(hub.leads)):
            _investigate_lead(app, hub, index)
        assert len(hub.investigated) == len(hub.leads)
        hub.conclude_button.on_activate()

        _fill_out_decision(app.scenes.current)
        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)  # feedback
        app.scenes.current.inner.continue_button.on_activate()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.completed_thoughtfully() is True
        assert len(result.leads_investigated) == len(hub.leads)
        # Every one of the 6 leads records at least one evidence key.
        assert len(result.gathered_evidence) >= 6
    finally:
        pygame.quit()


def test_reopening_a_lead_with_a_different_choice_replaces_its_evidence_not_duplicates_it():
    # Correction #26: re-running an already-completed lead with a
    # different analytical choice must replace its previous action/
    # evidence, not leave two mutually inconsistent facts both citable.
    app = _init_app()
    try:
        runner, collected = build_lesson_thirty_runner(app, on_finished=lambda _result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)

        hub = app.scenes.current.inner
        checkout_index = next(i for i, lead in enumerate(hub.leads) if lead.key == "checkout_health_check")

        # First pass: pick the cherry-picked (wrong) option.
        hub.buttons.buttons[checkout_index].on_activate()
        scene = app.scenes.current.inner
        scene.buttons.buttons[1].on_activate()  # cherry_picked_low_week is option index 1
        scene.next_button.on_activate()

        # Reopen the same lead and pick the correct option instead.
        hub.buttons.buttons[checkout_index].on_activate()
        scene = app.scenes.current.inner
        scene.buttons.buttons[0].on_activate()  # full_window_avg
        scene.next_button.on_activate()

        checkout_items = [item for item in _context_evidence(collected) if item.key == "checkout_health"]
        assert len(checkout_items) == 1  # updated in place, not appended
        assert checkout_items[0].label_key == "lesson.l30.evidence.checkout_flat"  # the final, correct choice wins
    finally:
        pygame.quit()


def _context_evidence(collected: dict):
    from data_science_arcade.workbench.context import LessonContext

    context = LessonContext()
    context.restore_from_dict(collected["analytical_context"])
    return context.evidence


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
