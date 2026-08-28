import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.monitoring import MetricRow, MonitoringCheckpoint
from data_science_arcade.ui.checkpoint_monitor_scene import CheckpointMonitorScene

CHECKPOINTS = (
    MonitoringCheckpoint(day=3, rows=(MetricRow("primary", "app.title", 0.265, 0.220),)),
    MonitoringCheckpoint(day=10, rows=(MetricRow("primary", "app.title", 0.238, 0.221),)),
    MonitoringCheckpoint(day=21, rows=(MetricRow("primary", "app.title", 0.223, 0.220),)),
)
TOTAL_RUNTIME_DAYS = 21


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda checkpoint: None, **kwargs):
    return CheckpointMonitorScene(app, "app.title", CHECKPOINTS, TOTAL_RUNTIME_DAYS, on_complete, **kwargs)


def test_starts_on_the_first_checkpoint_with_both_buttons_available():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.checkpoint_index == 0
        assert scene.stop_button.enabled is True
        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


def test_continue_advances_to_the_next_checkpoint():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.continue_button.on_activate()

        assert scene.checkpoint_index == 1
        assert scene._current_checkpoint().day == 10
    finally:
        pygame.quit()


def test_stopping_early_calls_on_complete_with_the_current_checkpoint_number():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda checkpoint: collected.append(checkpoint))
        scene.continue_button.on_activate()  # now on checkpoint 2 (index 1)

        scene.stop_button.on_activate()

        assert collected == [2]
    finally:
        pygame.quit()


def test_the_last_checkpoint_only_offers_one_button_and_it_finishes():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda checkpoint: collected.append(checkpoint))
        scene.continue_button.on_activate()
        scene.continue_button.on_activate()  # now on checkpoint 3 (index 2), the last

        assert scene.continue_button is None
        scene.stop_button.on_activate()

        assert collected == [3]
    finally:
        pygame.quit()


def test_continue_is_a_noop_past_the_last_checkpoint():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.continue_button.on_activate()
        scene.continue_button.on_activate()
        scene._continue()  # no button exists here; call the method directly

        assert scene.checkpoint_index == 2
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_at_any_checkpoint():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided, hint_key="common.back")
            scene.draw(app.logical_surface)
            scene.continue_button.on_activate()
            scene.draw(app.logical_surface)
            scene.continue_button.on_activate()
            scene.draw(app.logical_surface)
    finally:
        pygame.quit()
