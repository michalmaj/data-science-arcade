import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.findings import Finding
from data_science_arcade.ui.finding_picker_scene import FindingPickerScene

FINDINGS = (
    Finding("a", "common.on"),
    Finding("b", "common.off"),
    Finding("c", "common.back"),
    Finding("d", "app.title"),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return FindingPickerScene(app, "app.title", "app.title", FINDINGS, target_count=3, on_complete=on_complete, **kwargs)


def test_starts_with_the_full_pool_and_no_picks():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.picked == []
        assert len(scene.buttons.buttons) == len(FINDINGS)
    finally:
        pygame.quit()


def test_picking_a_finding_removes_it_from_the_remaining_pool():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # "a"

        assert scene.picked == ["a"]
        assert scene._remaining_findings() == FINDINGS[1:]
        assert len(scene.buttons.buttons) == len(FINDINGS) - 1
    finally:
        pygame.quit()


def test_picking_does_not_call_on_complete_before_the_target_count_is_reached():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[0].on_activate()  # now picks the pool's new index-0 (was index 1)

        assert collected == []
        assert len(scene.picked) == 2
    finally:
        pygame.quit()


def test_on_complete_fires_automatically_once_target_count_is_reached():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()  # "a"
        scene.buttons.buttons[0].on_activate()  # "b" (shifted to index 0)
        scene.buttons.buttons[0].on_activate()  # "c" (shifted to index 0)

        assert collected == [("a", "b", "c")]
    finally:
        pygame.quit()


def test_there_is_no_back_button_since_picks_are_final():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert not hasattr(scene, "back_button")
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_before_or_after_a_pick():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided, hint_key="common.back")
            scene.draw(app.logical_surface)  # no picks yet - no "picked so far" line
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # one pick - "picked so far" line shows
    finally:
        pygame.quit()
