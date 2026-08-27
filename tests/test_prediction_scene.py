import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.prediction import DECREASE, INCREASE, HypothesisRequest
from data_science_arcade.ui.prediction_scene import PredictionScene

REQUESTS = (
    HypothesisRequest(
        key="request_a",
        prompt_key="app.title",
        metric_label_key="common.on",
        hint_key="common.back",
        before_value=0.20,
        after_value=0.30,
    ),
    HypothesisRequest(
        key="request_b",
        prompt_key="app.title",
        metric_label_key="common.off",
        before_value=0.50,
        after_value=0.40,
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return PredictionScene(app, "app.title", REQUESTS, on_complete, **kwargs)


def test_starts_on_the_first_request_with_reveal_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.request_index == 0
        assert scene.action_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_picking_a_direction_enables_reveal_but_does_not_commit_it():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # "increase"

        assert scene.action_button.enabled is True
        assert scene.choices == {}  # not committed until Reveal
        assert scene._pending == INCREASE
    finally:
        pygame.quit()


def test_reveal_commits_the_prediction_and_freezes_the_direction_buttons():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.action_button.on_activate()  # Reveal

        assert scene.choices == {"request_a": INCREASE}
        assert all(button.enabled is False for button in scene.buttons.buttons[:3])
    finally:
        pygame.quit()


def test_reveal_is_a_noop_with_no_pending_direction():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._reveal()

        assert scene.choices == {}
    finally:
        pygame.quit()


def test_after_reveal_the_action_button_advances_instead_of_revealing():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.action_button.on_activate()  # Reveal
        scene.action_button.on_activate()  # Next

        assert scene.request_index == 1
        assert scene.back_button.enabled is True
    finally:
        pygame.quit()


def test_back_returns_to_an_already_revealed_request_still_revealed():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.action_button.on_activate()  # reveal request_a
        scene.action_button.on_activate()  # advance to request_b

        scene.back_button.on_activate()

        assert scene.request_index == 0
        assert scene._is_revealed() is True
        assert scene.choices["request_a"] == INCREASE
    finally:
        pygame.quit()


def test_finishing_the_last_request_calls_on_complete_with_the_full_choices():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()  # request_a: increase
        scene.action_button.on_activate()  # reveal
        scene.action_button.on_activate()  # advance

        scene.buttons.buttons[1].on_activate()  # request_b: decrease
        scene.action_button.on_activate()  # reveal
        scene.action_button.on_activate()  # finish

        assert collected == [{"request_a": INCREASE, "request_b": DECREASE}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_before_or_after_reveal():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # before any pick
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # pending, not yet revealed
            scene.action_button.on_activate()
            scene.draw(app.logical_surface)  # revealed
    finally:
        pygame.quit()
