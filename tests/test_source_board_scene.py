import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.source import DataSource, SourceAttribute
from data_science_arcade.ui.source_board_scene import SourceBoardScene

SOURCES = (
    DataSource(
        key="fast",
        name_key="common.back",  # any real key works - content isn't under test here
        attributes=(SourceAttribute("common.back", "common.on"),),
    ),
    DataSource(
        key="complete",
        name_key="common.back",
        attributes=(SourceAttribute("common.back", "common.off"),),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_starts_with_nothing_selected_and_confirm_disabled():
    app = _init_app()
    try:
        scene = SourceBoardScene(app, "app.title", "app.title", SOURCES, on_complete=lambda key: None)
        assert scene.selected_key is None
        assert scene.confirm_button.enabled is False
    finally:
        pygame.quit()


def test_selecting_a_source_enables_confirm():
    app = _init_app()
    try:
        scene = SourceBoardScene(app, "app.title", "app.title", SOURCES, on_complete=lambda key: None)
        scene.source_buttons["fast"].on_activate()
        assert scene.selected_key == "fast"
        assert scene.confirm_button.enabled is True
    finally:
        pygame.quit()


def test_confirm_does_nothing_until_something_is_selected():
    app = _init_app()
    try:
        scene = SourceBoardScene(app, "app.title", "app.title", SOURCES, on_complete=lambda key: None)
        scene._confirm()  # must not raise, must not call on_complete
    finally:
        pygame.quit()


def test_confirm_calls_on_complete_with_the_selected_key():
    app = _init_app()
    try:
        collected = []
        scene = SourceBoardScene(
            app, "app.title", "app.title", SOURCES, on_complete=lambda key: collected.append(key)
        )
        scene.source_buttons["complete"].on_activate()

        scene.confirm_button.on_activate()

        assert collected == ["complete"]
    finally:
        pygame.quit()


def test_switching_the_selection_before_confirming_keeps_only_the_latest_choice():
    app = _init_app()
    try:
        collected = []
        scene = SourceBoardScene(
            app, "app.title", "app.title", SOURCES, on_complete=lambda key: collected.append(key)
        )
        scene.source_buttons["fast"].on_activate()
        scene.source_buttons["complete"].on_activate()

        scene.confirm_button.on_activate()

        assert collected == ["complete"]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_with_or_without_a_selection():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = SourceBoardScene(
                app,
                "app.title",
                "app.title",
                SOURCES,
                on_complete=lambda key: None,
                guided=guided,
                hint_key="common.back",
            )
            scene.draw(app.logical_surface)
            scene.source_buttons["fast"].on_activate()
            scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_draw_does_not_crash_with_three_sources_and_several_attributes():
    app = _init_app()
    try:
        three_sources = tuple(
            DataSource(
                key=f"source_{i}",
                name_key="common.back",
                attributes=tuple(SourceAttribute("common.back", "common.on") for _ in range(5)),
            )
            for i in range(3)
        )
        scene = SourceBoardScene(app, "app.title", "app.title", three_sources, on_complete=lambda key: None)
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()
