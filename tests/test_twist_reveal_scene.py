import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l01_question_first.twist_data import (
    RECENT_WINDOW_START,
    generate_twist_orders,
    repeat_purchase_rate,
)
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete):
    dataset = generate_twist_orders()
    return TwistRevealScene(
        app,
        title_key="dialogue.continue_hint",  # any real key works for these tests
        narrative_keys=("dialogue.continue_hint",),
        dataset=dataset,
        comparisons=(
            ("dialogue.continue_hint", repeat_purchase_rate(dataset, RECENT_WINDOW_START)),
            ("dialogue.continue_hint", repeat_purchase_rate(dataset, None)),
        ),
        on_complete=on_complete,
    )


def test_draw_handles_any_number_of_comparisons():
    app = _init_app()
    try:
        dataset = generate_twist_orders()
        scene = TwistRevealScene(
            app,
            title_key="dialogue.continue_hint",
            narrative_keys=("dialogue.continue_hint",),
            dataset=dataset,
            comparisons=(
                ("dialogue.continue_hint", 0.1),
                ("dialogue.continue_hint", 0.5),
                ("dialogue.continue_hint", 0.9),
            ),
            on_complete=lambda: None,
        )

        scene.draw(app.logical_surface)  # must not raise for 3+ rows
    finally:
        pygame.quit()


def test_enter_triggers_on_complete():
    app = _init_app()
    try:
        calls = []
        scene = _make_scene(app, lambda: calls.append("done"))

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))

        assert calls == ["done"]
    finally:
        pygame.quit()


def test_click_triggers_on_complete():
    app = _init_app()
    try:
        calls = []
        scene = _make_scene(app, lambda: calls.append("done"))

        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 10), button=1))

        assert calls == ["done"]
    finally:
        pygame.quit()


def test_draw_does_not_crash():
    app = _init_app()
    try:
        scene = _make_scene(app, lambda: None)
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()
