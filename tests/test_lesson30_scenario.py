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
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.investigation_hub_scene import InvestigationHubScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _complete_correlation_or_chart_lead(scene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.next_button.on_activate()


def _complete_alert_lead(scene: AlertConfigScene) -> None:
    scene.buttons.buttons[0].on_activate()  # metric
    scene.buttons.buttons[len(scene._current_request().metric_options)].on_activate()  # threshold
    scene.next_button.on_activate()


def _investigate_leads(app, hub: InvestigationHubScene, count: int) -> None:
    # Unlike every other lesson's fixed-shape helper, each of these leads
    # is a different reused scene type - which completion shape applies
    # depends on which lead index was just opened.
    for index in range(count):
        hub.buttons.buttons[index].on_activate()
        lead_scene = app.scenes.current.inner
        if isinstance(lead_scene, AlertConfigScene):
            _complete_alert_lead(lead_scene)
        else:
            _complete_correlation_or_chart_lead(lead_scene)


def _fill_out_brief(scene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_the_full_lesson_plays_through_to_a_result_investigating_exactly_the_minimum():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_thirty_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()

        # Every stage is wrapped in Pausable (Escape opens the pause menu);
        # .inner is the actual stage scene the factory returned.

        assert isinstance(app.scenes.current.inner, DialogueScene)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # investigation intro
        _play_dialogue_to_the_end(app.scenes.current)

        hub = app.scenes.current.inner
        assert isinstance(hub, InvestigationHubScene)
        assert len(hub.leads) == 5

        _investigate_leads(app, hub, MINIMUM_LEADS_REQUIRED)
        assert app.scenes.current.inner is hub
        assert len(hub.investigated) == MINIMUM_LEADS_REQUIRED
        assert hub.conclude_button.enabled
        hub.conclude_button.on_activate()

        assert isinstance(app.scenes.current.inner, TwistRevealScene)
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # decision
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonThirtyResult)
        assert result.completed_thoughtfully() is True
        assert len(result.leads_investigated) == MINIMUM_LEADS_REQUIRED
        assert set(result.decision_brief) == {field.key for field in DECISION_FIELDS}
        assert collected["result"] is result
    finally:
        pygame.quit()


def test_investigating_every_lead_still_completes_thoughtfully():
    app = _init_app()
    try:
        finished_results = []
        runner, _collected = build_lesson_thirty_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()

        _play_dialogue_to_the_end(app.scenes.current)
        _play_dialogue_to_the_end(app.scenes.current)

        hub = app.scenes.current.inner
        _investigate_leads(app, hub, len(hub.leads))
        assert len(hub.investigated) == len(hub.leads)
        hub.conclude_button.on_activate()

        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))
        _fill_out_brief(app.scenes.current, DECISION_FIELDS)
        _play_dialogue_to_the_end(app.scenes.current)

        assert finished_results[0].completed_thoughtfully() is True
        assert len(finished_results[0].leads_investigated) == len(hub.leads)
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", list(DECISION_FIELDS))
def test_every_decision_field_has_at_least_two_options(field):
    assert len(field.options) >= 2
