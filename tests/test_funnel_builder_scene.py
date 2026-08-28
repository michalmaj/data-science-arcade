import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.funnel import FunnelDefinition, FunnelRequest, FunnelStep
from data_science_arcade.ui.funnel_builder_scene import FunnelBuilderScene

REQUESTS = (
    FunnelRequest(
        key="request_a",
        prompt_key="app.title",
        hint_key="common.back",
        definitions=(
            FunnelDefinition("flawed", "common.on", steps=(FunnelStep("top", "common.on", 1000), FunnelStep("bottom", "common.off", 100))),
            FunnelDefinition("correct", "common.off", steps=(FunnelStep("top", "common.on", 1000), FunnelStep("bottom", "common.off", 400))),
        ),
    ),
    FunnelRequest(
        key="request_b",
        prompt_key="app.title",
        definitions=(
            FunnelDefinition("only_one", "common.on", steps=(FunnelStep("top", "common.on", 500), FunnelStep("bottom", "common.off", 250))),
        ),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return FunnelBuilderScene(app, "app.title", REQUESTS, on_complete, **kwargs)


def test_starts_on_the_first_request_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.request_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_a_definition_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()

        assert scene.choices == {"request_a": "flawed"}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_next_advances_to_the_next_request_and_back_returns():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene.request_index == 1
        assert scene.back_button.enabled is True

        scene.back_button.on_activate()

        assert scene.request_index == 0
        assert scene.choices["request_a"] == "flawed"
    finally:
        pygame.quit()


def test_finishing_the_last_request_calls_on_complete_with_the_full_choices():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[1].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[0].on_activate()

        scene.next_button.on_activate()

        assert collected == [{"request_a": "correct", "request_b": "only_one"}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_before_or_after_a_choice():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # before any choice - the "pick a definition" placeholder path
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # after a choice - the real funnel chart path
    finally:
        pygame.quit()
