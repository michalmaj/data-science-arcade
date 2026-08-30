import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.core.scenes import Pausable
from data_science_arcade.lessons.framework.investigation import InvestigationLead
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.investigation_hub_scene import InvestigationHubScene

DUMMY_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="app.title"),))


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_lead(app, key: str) -> InvestigationLead:
    # A DialogueScene stand-in is enough to exercise the hub's own
    # mechanics in isolation - its on_complete takes zero arguments,
    # unlike every real lead scene's one-argument choices dict, which
    # also covers the hub's *_choices tolerance for either shape.
    def build_scene(on_complete):
        return DialogueScene(app, DUMMY_DIALOGUE, on_complete=on_complete)

    return InvestigationLead(key=key, label_key="app.title", build_scene=build_scene)


def _make_hub(app, on_complete=lambda result: None, minimum_leads=3):
    leads = tuple(_make_lead(app, f"lead_{i}") for i in range(5))
    return InvestigationHubScene(app, "app.title", "app.title", leads, minimum_leads, on_complete)


def test_starts_with_no_leads_investigated_and_conclude_disabled():
    app = _init_app()
    try:
        hub = _make_hub(app)
        assert hub.investigated == set()
        assert len(hub.buttons.buttons) == len(hub.leads) + 1  # + the conclude button
        assert not hub.conclude_button.enabled
    finally:
        pygame.quit()


def test_opening_a_lead_pushes_it_wrapped_in_its_own_pausable():
    app = _init_app()
    try:
        hub = _make_hub(app)
        app.scenes.push(Pausable(app, hub, on_escape=lambda: None))

        hub.buttons.buttons[0].on_activate()

        assert isinstance(app.scenes.current, Pausable)
        assert isinstance(app.scenes.current.inner, DialogueScene)
    finally:
        pygame.quit()


def test_escaping_a_lead_returns_to_the_hub_without_marking_it_investigated():
    app = _init_app()
    try:
        hub = _make_hub(app)
        app.scenes.push(Pausable(app, hub, on_escape=lambda: None))

        hub.buttons.buttons[0].on_activate()
        app.scenes.current.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        assert app.scenes.current.inner is hub
        assert hub.investigated == set()
    finally:
        pygame.quit()


def test_completing_a_lead_marks_it_investigated_and_returns_to_the_hub():
    app = _init_app()
    try:
        hub = _make_hub(app)
        app.scenes.push(Pausable(app, hub, on_escape=lambda: None))

        hub.buttons.buttons[0].on_activate()
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert app.scenes.current.inner is hub
        assert hub.investigated == {"lead_0"}
    finally:
        pygame.quit()


def test_conclude_enables_once_the_minimum_is_reached_and_not_before():
    app = _init_app()
    try:
        hub = _make_hub(app, minimum_leads=3)
        app.scenes.push(Pausable(app, hub, on_escape=lambda: None))

        for index in range(2):
            hub.buttons.buttons[index].on_activate()
            app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))
        assert not hub.conclude_button.enabled

        hub.buttons.buttons[2].on_activate()
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))
        assert hub.conclude_button.enabled
    finally:
        pygame.quit()


def test_investigating_more_than_the_minimum_keeps_conclude_enabled():
    app = _init_app()
    try:
        hub = _make_hub(app, minimum_leads=3)
        app.scenes.push(Pausable(app, hub, on_escape=lambda: None))

        for index in range(5):
            hub.buttons.buttons[index].on_activate()
            app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert len(hub.investigated) == 5
        assert hub.conclude_button.enabled
    finally:
        pygame.quit()


def test_reinvestigating_the_same_lead_does_not_duplicate_or_regress_progress():
    app = _init_app()
    try:
        hub = _make_hub(app, minimum_leads=3)
        app.scenes.push(Pausable(app, hub, on_escape=lambda: None))

        for _ in range(2):
            hub.buttons.buttons[0].on_activate()
            app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert hub.investigated == {"lead_0"}
    finally:
        pygame.quit()


def test_conclude_fires_on_complete_with_every_investigated_lead_key():
    app = _init_app()
    try:
        results = []
        hub = _make_hub(app, on_complete=lambda result: results.append(result), minimum_leads=3)
        app.scenes.push(Pausable(app, hub, on_escape=lambda: None))

        for index in range(3):
            hub.buttons.buttons[index].on_activate()
            app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))
        hub.conclude_button.on_activate()

        assert results == [frozenset({"lead_0", "lead_1", "lead_2"})]
    finally:
        pygame.quit()


def test_draw_does_not_crash_before_or_after_investigating():
    app = _init_app()
    try:
        hub = _make_hub(app)
        hub.draw(app.logical_surface)  # nothing investigated yet

        app.scenes.push(Pausable(app, hub, on_escape=lambda: None))
        hub.buttons.buttons[0].on_activate()
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))
        hub.draw(app.logical_surface)  # one lead investigated - marker suffix shows
    finally:
        pygame.quit()
