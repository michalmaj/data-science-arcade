import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.correlation import CorrelationRequest, VerdictOption
from data_science_arcade.ui.correlation_scene import CorrelationScene

REQUESTS = (
    CorrelationRequest(
        key="request_a",
        prompt_key="app.title",
        hint_key="common.back",
        metric_a_label_key="common.on",
        metric_b_label_key="common.off",
        evidence_key="app.title",
        correlation=0.92,
        sample_size=15,
        options=(
            VerdictOption("mismatched", "common.on", "common.back"),
            VerdictOption("same_month", "common.off", "common.on"),
        ),
    ),
    CorrelationRequest(
        key="request_b",
        prompt_key="app.title",
        metric_a_label_key="common.on",
        metric_b_label_key="common.off",
        evidence_key="app.title",
        correlation=0.4,
        sample_size=8,
        options=(VerdictOption("only_one", "common.on", "app.title"),),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return CorrelationScene(app, "app.title", REQUESTS, on_complete, **kwargs)


def test_starts_on_the_first_request_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.request_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_an_option_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()

        assert scene.choices == {"request_a": "mismatched"}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_selected_option_is_retrievable_for_the_explanation_text():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[1].on_activate()  # "same_month"

        request = scene._current_request()
        assert scene._selected_option(request).key == "same_month"
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
        assert scene.choices["request_a"] == "mismatched"
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

        assert collected == [{"request_a": "same_month", "request_b": "only_one"}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_before_or_after_a_pick():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # before any pick - no explanation shown
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # after a pick - explanation shown
    finally:
        pygame.quit()
